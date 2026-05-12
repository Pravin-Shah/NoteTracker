"""
LLM Orchestration Layer for Second Brain (Smart Quota Management).
"""
import os
import json
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

from apps.general.utils.brain_ops import (
    get_unprocessed, mark_processed, upsert_wiki_page, 
    list_wiki_pages, get_wiki_page, add_link, log_llm_op
)
from apps.general.utils.brain_prompts import (
    INGEST_SYSTEM_PROMPT, QUERY_SYSTEM_PROMPT, LINT_SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)

class LLMProvider:
    def __init__(self, provider: str = None):
        self.provider = provider or os.getenv("BRAIN_LLM_PROVIDER", "gemini").lower()
        self.api_key = os.getenv(f"{self.provider.upper()}_API_KEY")
        
        if not self.api_key:
            raise ValueError(f"Missing API key for {self.provider}")

    def complete(self, system_prompt: str, user_prompt: str, images: List[str] = None, use_search: bool = False, force_json: bool = False) -> str:
        """Complete with optional image and search support."""
        # SMART ROUTING: If no images and no search, and we have Groq, use Groq for speed/quota
        groq_key = os.getenv("GROQ_API_KEY")
        if not images and not use_search and groq_key and self.provider != "gemini":
            return self._complete_groq(system_prompt, user_prompt, force_json)

        if self.provider == "gemini":
            return self._complete_gemini(system_prompt, user_prompt, images, use_search, force_json)
        
        return self._complete_groq(system_prompt, user_prompt, force_json)

    def _complete_groq(self, system_prompt: str, user_prompt: str, force_json: bool = False) -> str:
        try:
            from groq import Groq
            api_key = os.getenv("GROQ_API_KEY")
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"} if force_json else None
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return f"API_ERROR: {str(e)}"

    def _complete_gemini(self, system_prompt: str, user_prompt: str, images: List[str] = None, use_search: bool = False, force_json: bool = False) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            contents = [user_prompt]
            
            if images:
                upload_dir = Path(os.getenv("UPLOADS_DIR", "data/uploads"))
                for img_path in images:
                    full_path = upload_dir / img_path
                    if full_path.exists():
                        try:
                            img_data = {
                                "mime_type": "image/jpeg" if img_path.lower().endswith(('.jpg', '.jpeg')) else "image/png",
                                "data": full_path.read_bytes()
                            }
                            contents.append(img_data)
                        except Exception as ie:
                            logger.warning(f"Failed to load image {img_path}: {ie}")

            tools = []
            if use_search:
                tools.append({"google_search_retrieval": {}})

            config = {}
            if force_json:
                config["response_mime_type"] = "application/json"

            model_name = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
            
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
                tools=tools
            )
            response = model.generate_content(contents, generation_config=config)
            return response.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return f"API_ERROR: {str(e)}"

class BrainEngine:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.llm = LLMProvider()

    def _extract_json(self, text: str) -> Optional[Dict]:
        try:
            return json.loads(text)
        except:
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except:
                    pass
        return None

    def ingest(self):
        """Process raw dumps into wiki."""
        unprocessed = get_unprocessed(self.user_id)
        if not unprocessed:
            return "No raw dumps to process."

        wiki_index = list_wiki_pages(self.user_id)
        wiki_index_str = json.dumps(wiki_index, indent=2)

        all_images = []
        needs_search = False
        raw_text_combined = ""

        for r in unprocessed:
            raw_text_combined += f"\nID: {r['id']} - {r['content']}"
            # Check for images
            if r.get('attachments'):
                try:
                    att = json.loads(r['attachments'])
                    if isinstance(att, list):
                        images = [a for a in att if a.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                        all_images.extend(images)
                except:
                    pass
            # Check for explicit research intent
            if "research" in r['content'].lower() or "search" in r['content'].lower():
                needs_search = True

        use_search = (os.getenv("BRAIN_ENABLE_SEARCH", "true").lower() == "true") and needs_search
        search_instruction = ""
        if use_search:
            search_instruction = "\n\nCRITICAL: You have access to Google Search. SEARCH for the concepts mentioned. Use the search results to enrich the wiki pages. Add a '## Web Intelligence' section at the end of the page for external findings."

        user_prompt = f"EXISTING WIKI INDEX:\n{wiki_index_str}\n\nRAW NOTES TO PROCESS:\n{raw_text_combined}{search_instruction}"
        
        # Decide which provider to use based on content
        # If images or search needed, use Gemini. Otherwise, Groq.
        if all_images or use_search:
            provider = "gemini"
        else:
            provider = "groq"

        # Override provider for this call
        temp_llm = LLMProvider(provider=provider)
        response_str = temp_llm.complete(INGEST_SYSTEM_PROMPT, user_prompt, images=all_images, use_search=use_search, force_json=True)
        
        if response_str.startswith("API_ERROR"):
            return response_str

        data = self._extract_json(response_str)
        if not data:
            return "Error: LLM returned invalid JSON structure."

        try:
            for page in data.get("wiki_pages", []):
                upsert_wiki_page(self.user_id, page['title'], page['category'], page['content'], [r['id'] for r in unprocessed])
            
            for link in data.get("links", []):
                p1 = get_wiki_page(self.user_id, link['from'])
                p2 = get_wiki_page(self.user_id, link['to'])
                if p1 and p2:
                    add_link(p1['id'], p2['id'], link['relationship'])

            for r in unprocessed:
                mark_processed(r['id'])

            log_llm_op("ingest", f"{len(unprocessed)} dumps, {len(all_images)} imgs, search={use_search}", data.get("summary", ""), provider)
            return data.get("summary", "Ingestion complete.")

        except Exception as e:
            return f"Error during processing: {str(e)}"

    def query(self, question: str):
        all_pages = list_wiki_pages(self.user_id)
        relevant_titles = [p['title'] for p in all_pages if any(word.lower() in p['title'].lower() for word in question.split())]
        
        context_pages = []
        for title in relevant_titles[:5]:
            page = get_wiki_page(self.user_id, title)
            if page:
                context_pages.append(f"TITLE: {page['title']}\nCONTENT:\n{page['content']}")

        context_str = "\n\n---\n\n".join(context_pages)
        # Only use search if question implies it
        use_search = "search" in question.lower() or "latest" in question.lower() or "news" in question.lower()
        
        user_prompt = f"QUESTION: {question}\n\nCONTEXT FROM BRAIN:\n{context_str}"
        if use_search:
            user_prompt += "\n\nFeel free to use Google Search for up-to-date info."

        provider = "gemini" if use_search else "groq"
        temp_llm = LLMProvider(provider=provider)
        response = temp_llm.complete(QUERY_SYSTEM_PROMPT, user_prompt, use_search=use_search)
        log_llm_op("query", question, response[:500] + "...", provider)
        return response

    def lint(self):
        all_pages = list_wiki_pages(self.user_id)
        full_wiki = [{"title": p['title'], "category": p['category']} for p in all_pages]
        user_prompt = json.dumps(full_wiki)
        # Lint is always Groq (cheap)
        temp_llm = LLMProvider(provider="groq")
        response_str = temp_llm.complete(LINT_SYSTEM_PROMPT, user_prompt, force_json=True)

        data = self._extract_json(response_str)
        if not data: return {"error": "Invalid JSON"}

        try:
            report_content = f"## Health Score: {data.get('health_score', 0)}/100\n\n### Issues Found\n"
            for issue in data.get("issues", []):
                report_content += f"- **{issue['type']}**: {issue['description']}\n"
            upsert_wiki_page(self.user_id, "Brain Health Report", "System", report_content, [])
            return data
        except Exception as e:
            return {"error": str(e)}

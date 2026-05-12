"""
LLM Orchestration Layer for Second Brain (Robust JSON + Search).
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
        if self.provider == "gemini":
            return self._complete_gemini(system_prompt, user_prompt, images, use_search, force_json)
        
        if self.provider == "groq":
            return self._complete_groq(system_prompt, user_prompt, force_json)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _complete_groq(self, system_prompt: str, user_prompt: str, force_json: bool = False) -> str:
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)
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

            # Use Stable 1.5 Flash as default
            model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            
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
        """Extract JSON from LLM response reliably."""
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
        for r in unprocessed:
            if r.get('attachments'):
                try:
                    att = json.loads(r['attachments'])
                    if isinstance(att, list):
                        images = [a for a in att if a.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
                        all_images.extend(images)
                except:
                    pass

        raw_content = "\n---\n".join([f"ID: {r['id']} - {r['content']}" for r in unprocessed])
        
        use_search = os.getenv("BRAIN_ENABLE_SEARCH", "true").lower() == "true"
        search_instruction = ""
        if use_search:
            search_instruction = "\n\nCRITICAL: You have access to Google Search. If a note mentions a project, company, person, or technical concept that you don't fully know about, SEARCH for it. Use the search results to enrich the wiki pages. Add a '## Web Intelligence' section at the end of the page for external findings and links."

        user_prompt = f"EXISTING WIKI INDEX:\n{wiki_index_str}\n\nRAW NOTES TO PROCESS:\n{raw_content}{search_instruction}"
        
        if all_images:
            user_prompt += f"\n\nAttached {len(all_images)} images for visual analysis."

        response_str = self.llm.complete(INGEST_SYSTEM_PROMPT, user_prompt, images=all_images, use_search=use_search, force_json=True)
        
        if response_str.startswith("API_ERROR"):
            return response_str

        data = self._extract_json(response_str)
        if not data:
            logger.error(f"Failed to parse LLM response: {response_str}")
            return "Error: LLM returned invalid JSON structure."

        try:
            for page in data.get("wiki_pages", []):
                upsert_wiki_page(
                    self.user_id, 
                    page['title'], 
                    page['category'], 
                    page['content'], 
                    [r['id'] for r in unprocessed]
                )
            
            for link in data.get("links", []):
                p1 = get_wiki_page(self.user_id, link['from'])
                p2 = get_wiki_page(self.user_id, link['to'])
                if p1 and p2:
                    add_link(p1['id'], p2['id'], link['relationship'])

            for r in unprocessed:
                mark_processed(r['id'])

            log_llm_op("ingest", f"{len(unprocessed)} dumps, {len(all_images)} imgs, search={use_search}", data.get("summary", ""), self.llm.provider)
            return data.get("summary", "Ingestion complete.")

        except Exception as e:
            logger.error(f"Ingest error: {e}")
            return f"Error during processing: {str(e)}"

    def query(self, question: str):
        all_pages = list_wiki_pages(self.user_id)
        relevant_titles = [p['title'] for p in all_pages if any(word.lower() in p['title'].lower() for word in question.split())]
        
        if not relevant_titles:
            relevant_titles = [p['title'] for p in all_pages[:10]]

        context_pages = []
        for title in relevant_titles:
            page = get_wiki_page(self.user_id, title)
            if page:
                context_pages.append(f"TITLE: {page['title']}\nCATEGORY: {page['category']}\nCONTENT:\n{page['content']}")

        context_str = "\n\n---\n\n".join(context_pages)
        use_search = os.getenv("BRAIN_ENABLE_SEARCH_QUERY", "true").lower() == "true"
        
        user_prompt = f"QUESTION: {question}\n\nCONTEXT FROM BRAIN:\n{context_str}"
        if use_search:
            user_prompt += "\n\nIf you need more up-to-date info to answer the question, feel free to use Google Search."

        response = self.llm.complete(QUERY_SYSTEM_PROMPT, user_prompt, use_search=use_search)
        log_llm_op("query", question, response[:500] + "...", self.llm.provider)
        return response

    def lint(self):
        all_pages = list_wiki_pages(self.user_id)
        full_wiki = []
        for p in all_pages:
            page = get_wiki_page(self.user_id, p['title'])
            if page:
                full_wiki.append({"title": page['title'], "category": page['category'], "content": page['content']})

        user_prompt = json.dumps(full_wiki)
        response_str = self.llm.complete(LINT_SYSTEM_PROMPT, user_prompt, force_json=True)

        if response_str.startswith("API_ERROR"):
            return {"error": response_str}

        data = self._extract_json(response_str)
        if not data:
            return {"error": "Invalid JSON report"}

        try:
            report_content = f"## Health Score: {data.get('health_score', 0)}/100\n\n"
            report_content += "### Issues Found\n"
            for issue in data.get("issues", []):
                report_content += f"- **{issue['type']}**: {issue['description']} (Pages: {', '.join(issue['pages'])})\n"
            
            report_content += "\n### Suggestions\n"
            for suggestion in data.get("suggestions", []):
                report_content += f"- {suggestion}\n"

            upsert_wiki_page(self.user_id, "Brain Health Report", "System", report_content, [])
            log_llm_op("lint", f"{len(all_pages)} pages", "Health report generated", self.llm.provider)
            return data
        except Exception as e:
            logger.error(f"Lint error: {e}")
            return {"error": str(e)}

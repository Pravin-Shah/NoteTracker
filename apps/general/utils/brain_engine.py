"""
LLM Orchestration Layer for Second Brain.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional

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
        self.provider = provider or os.getenv("BRAIN_LLM_PROVIDER", "groq").lower()
        self.api_key = os.getenv(f"{self.provider.upper()}_API_KEY")
        
        if not self.api_key:
            raise ValueError(f"Missing API key for {self.provider}")

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "groq":
            return self._complete_groq(system_prompt, user_prompt)
        elif self.provider == "gemini":
            return self._complete_gemini(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _complete_groq(self, system_prompt: str, user_prompt: str) -> str:
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
                response_format={"type": "json_object"} if "JSON" in system_prompt else None
            )
            return completion.choices[0].message.content
        except ImportError:
            return "Error: groq package not installed"
        except Exception as e:
            logger.error(f"Groq error: {e}")
            return f"Error: {str(e)}"

    def _complete_gemini(self, system_prompt: str, user_prompt: str) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                system_instruction=system_prompt
            )
            response = model.generate_content(user_prompt)
            return response.text
        except ImportError:
            return "Error: google-generativeai package not installed"
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return f"Error: {str(e)}"

class BrainEngine:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.llm = LLMProvider()

    def ingest(self):
        """Process raw dumps into wiki."""
        unprocessed = get_unprocessed(self.user_id)
        if not unprocessed:
            return "No raw dumps to process."

        # Build context from existing wiki index
        wiki_index = list_wiki_pages(self.user_id)
        wiki_index_str = json.dumps(wiki_index, indent=2)

        # Build input for LLM
        raw_content = "\n---\n".join([f"ID: {r['id']} - {r['content']}" for r in unprocessed])
        user_prompt = f"EXISTING WIKI INDEX:\n{wiki_index_str}\n\nRAW NOTES TO PROCESS:\n{raw_content}"

        # Get LLM response
        response_str = self.llm.complete(INGEST_SYSTEM_PROMPT, user_prompt)
        
        try:
            # Clean response (Gemini sometimes adds markdown blocks)
            if response_str.startswith("```json"):
                response_str = response_str.split("```json")[1].split("```")[0].strip()
            
            data = json.loads(response_str)
            
            # 1. Update Wiki Pages
            for page in data.get("wiki_pages", []):
                upsert_wiki_page(
                    self.user_id, 
                    page['title'], 
                    page['category'], 
                    page['content'], 
                    [r['id'] for r in unprocessed]
                )
            
            # 2. Update Links
            for link in data.get("links", []):
                p1 = get_wiki_page(self.user_id, link['from'])
                p2 = get_wiki_page(self.user_id, link['to'])
                if p1 and p2:
                    add_link(p1['id'], p2['id'], link['relationship'])

            # 3. Mark Processed
            for r in unprocessed:
                mark_processed(r['id'])

            # 4. Log operation
            log_llm_op("ingest", f"{len(unprocessed)} raw dumps", data.get("summary", ""), self.llm.provider)

            return data.get("summary", "Ingestion complete.")

        except json.JSONDecodeError:
            logger.error(f"Failed to parse LLM response: {response_str}")
            return "Error: LLM returned invalid JSON."
        except Exception as e:
            logger.error(f"Ingest error: {e}")
            return f"Error: {str(e)}"

    def query(self, question: str):
        """Ask your brain a question."""
        # 1. Find relevant pages (Simple keyword match for now, could be vector search)
        all_pages = list_wiki_pages(self.user_id)
        relevant_titles = [p['title'] for p in all_pages if any(word.lower() in p['title'].lower() for word in question.split())]
        
        # If no keywords match, just use recent pages or all pages index
        if not relevant_titles:
            relevant_titles = [p['title'] for p in all_pages[:10]]

        context_pages = []
        for title in relevant_titles:
            page = get_wiki_page(self.user_id, title)
            if page:
                context_pages.append(f"TITLE: {page['title']}\nCATEGORY: {page['category']}\nCONTENT:\n{page['content']}")

        context_str = "\n\n---\n\n".join(context_pages)
        user_prompt = f"QUESTION: {question}\n\nCONTEXT:\n{context_str}"

        response = self.llm.complete(QUERY_SYSTEM_PROMPT, user_prompt)
        
        # Log query
        log_llm_op("query", question, response[:500] + "...", self.llm.provider)
        
        return response

    def lint(self):
        """Run a health check on the wiki."""
        all_pages = list_wiki_pages(self.user_id)
        # Full content for linting (might need to batch if too large)
        full_wiki = []
        for p in all_pages:
            page = get_wiki_page(self.user_id, p['title'])
            full_wiki.append({"title": page['title'], "category": page['category'], "content": page['content']})

        user_prompt = json.dumps(full_wiki)
        response_str = self.llm.complete(LINT_SYSTEM_PROMPT, user_prompt)

        try:
             # Clean response
            if response_str.startswith("```json"):
                response_str = response_str.split("```json")[1].split("```")[0].strip()
                
            data = json.loads(response_str)
            
            # Save report as a wiki page
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
            return f"Error: {str(e)}"

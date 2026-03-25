"""LLM client for Ollama."""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import requests
from src.config import LLMConfig, get_config

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Chat message."""
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}

@dataclass
class ChatCompletion:
    """LLM response."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    raw_response: Optional[Dict] = None

    def extract_json(self) -> Optional[Union[Dict, List]]:
        """Extract JSON from content with high tolerance for errors, supporting both objects and lists."""
        import re
        content = self.content.strip()
        
        # Remove non-printable characters
        content = "".join(c for c in content if c.isprintable() or c in "\n\r\t")

        def clean_internal_quotes(text):
            """Heuristic to clean unescaped quotes within text segments."""
            return re.sub(r'(\w)\s+"(\w+)"\s+(\w)', r'\1 \'\2\' \3', text)
        
        try:
            # Locate JSON boundaries (Object or List)
            # Find first and last occurrence of either { } or [ ]
            start_obj = content.find("{")
            end_obj = content.rfind("}")
            
            start_list = content.find("[")
            end_list = content.rfind("]")
            
            # Determine which structure comes first and ends last
            if start_obj != -1 and (start_list == -1 or start_obj < start_list):
                start, end = start_obj, end_obj
            elif start_list != -1:
                start, end = start_list, end_list
            else:
                return None
                
            if start == -1 or end == -1 or end < start: return None
            
            json_str = content[start : end + 1]
            
            # Standard parsing attempt
            try: return json.loads(json_str)
            except: pass
            
            # Clean internal quotes and retry
            try: return json.loads(clean_internal_quotes(json_str))
            except: pass
            
            # Fallback: Manual regex-based extraction for highly malformed JSON
            if json_str.startswith("{"):
                manual_data = {}
                # ... (keep existing manual extraction for objects)
                if '"needs_rewrite": true' in json_str.lower(): manual_data["needs_rewrite"] = True
                elif '"needs_rewrite": false' in json_str.lower(): manual_data["needs_rewrite"] = False
                
                for sev in ["minor", "moderate", "major"]:
                    if f'"severity": "{sev}"' in json_str.lower():
                        manual_data["severity"] = sev
                        break
                
                for key in ["issues", "suggestions", "consistency_issues", "flow_issues", "redundancies", "recommendations"]:
                    items = re.findall(r'"([^"]*?Issue[^"]*?)"|"[^"]*?Suggestion[^"]*?"|"[^"]*?Rec[^"]*?"', json_str)
                    if items: manual_data[key] = items
                if manual_data: return manual_data

        except: pass
        return None

class LLMClient:
    """Client for Ollama API."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or get_config().llm

    def chat(self, messages: List[Message], temperature: Optional[float] = None, max_tokens: Optional[int] = None, response_format: Optional[Dict] = None) -> ChatCompletion:
        """Execute chat request."""
        if self.config.provider == "ollama": return self._chat_ollama(messages, temperature, max_tokens, response_format)
        elif self.config.provider == "openai": return self._chat_openai(messages, temperature, max_tokens, response_format)
        elif self.config.provider == "google": return self._chat_google(messages, temperature, max_tokens, response_format)
        raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _chat_ollama(self, messages: List[Message], temperature: Optional[float], max_tokens: Optional[int], response_format: Optional[Dict]) -> ChatCompletion:
        """Chat with Ollama with automatic retries."""
        url = f"{self.config.base_url}/api/chat"
        payload = {
            "model": self.config.model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
            "options": {"temperature": temperature or self.config.temperature, "num_predict": max_tokens or self.config.max_tokens}
        }
        
        for attempt in range(3):
            try:
                res = requests.post(url, json=payload, timeout=self.config.timeout)
                res.raise_for_status()
                if not res.text.strip():
                    if attempt < 2: time.sleep(2); continue
                    raise ConnectionError("Empty response")
                
                data = res.json()
                content = data.get("message", {}).get("content") or data.get("response") or data.get("content") or ""
                
                # Robust extraction if standard fields are empty
                if not content:
                    for k, v in data.items():
                        if isinstance(v, str) and v.strip() and k not in ["model", "created_at", "status"]:
                            content = v; break
                
                if not content and attempt < 2: time.sleep(2); continue
                return ChatCompletion(content=content, model=self.config.model, usage={"prompt_tokens": data.get("prompt_eval_count", 0), "completion_tokens": data.get("eval_count", 0)}, raw_response=data)
            except Exception as e:
                if attempt < 2: time.sleep(2); continue
                raise ConnectionError(f"Ollama error: {e}") from e

    def generate_json(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> Dict[str, Any]:
        """Generate JSON response."""
        msgs = [Message(role="system", content=system_prompt), Message(role="user", content=user_prompt)]
        comp = self.chat(messages=msgs, temperature=temperature, response_format={"type": "json_object"})
        data = comp.extract_json()
        if data is None: raise ValueError(f"Failed to extract JSON: {comp.content}")
        return data

    def generate_text(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> str:
        """Generate plain text."""
        msgs = [Message(role="system", content=system_prompt), Message(role="user", content=user_prompt)]
        return self.chat(messages=msgs, temperature=temperature, max_tokens=max_tokens).content

    def is_available(self) -> bool:
        """Check server availability."""
        try: requests.get(f"{self.config.base_url}/api/tags", timeout=2); return True
        except: return False

def get_llm_client(config: Optional[LLMConfig] = None, model_override: Optional[str] = None) -> LLMClient:
    """Get client instance with optional model override."""
    if model_override:
        from dataclasses import replace
        config = config or replace(get_config().llm)
        config.model = model_override
    return LLMClient(config)

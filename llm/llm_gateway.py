"""
Multi-Provider LLM Gateway
Provides structured output generation using Groq, OpenAI, Gemini, Ollama,
with graceful intelligent fallback for demo/offline mode.
"""

import os
import json
import re
import logging
from typing import Type, TypeVar, Optional, Any, Dict
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMGateway:
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.2,
    ):
        """
        Initialize LLMGateway with provider and model settings.
        Supported providers: 'groq', 'openai', 'gemini', 'ollama', 'mock'
        """
        self.temperature = temperature
        
        # Determine provider and API keys
        groq_key = api_key if provider == "groq" else (os.getenv("GROQ_API_KEY") or "")
        openai_key = api_key if provider == "openai" else (os.getenv("OPENAI_API_KEY") or "")
        gemini_key = api_key if provider == "gemini" else (os.getenv("GEMINI_API_KEY") or "")
        
        if not provider:
            if groq_key:
                self.provider = "groq"
            elif openai_key:
                self.provider = "openai"
            elif gemini_key:
                self.provider = "gemini"
            else:
                self.provider = "mock"
        else:
            self.provider = provider.lower()

        # Set default models
        if model:
            self.model = model
        else:
            if self.provider == "groq":
                self.model = "llama-3.3-70b-versatile"
            elif self.provider == "openai":
                self.model = "gpt-4o-mini"
            elif self.provider == "gemini":
                self.model = "gemini-2.0-flash"
            elif self.provider == "ollama":
                self.model = "llama3.2"
            else:
                self.model = "mock-analyst"

        # Initialize clients
        self.groq_client = None
        self.openai_client = None
        self.gemini_client = None

        if self.provider == "groq" and groq_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=groq_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")
                self.provider = "mock"

        elif self.provider == "openai" and openai_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=openai_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self.provider = "mock"

        elif self.provider == "gemini" and gemini_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=gemini_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")
                self.provider = "mock"

        elif self.provider == "ollama":
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama client: {e}")
                self.provider = "mock"

    def _extract_json_from_text(self, text: str) -> str:
        """Extracts JSON substring from markdown backticks or raw response."""
        text = text.strip()
        # Look for ```json ... ``` or ``` ... ```
        json_match = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
            
        # Look for outer brackets
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace : last_brace + 1].strip()
            
        return text

    def generate_text(self, prompt: str, system_prompt: str = "You are an expert data analyst AI assistant.") -> str:
        """Generates raw text response for conversational Q&A."""
        if self.provider == "groq" and self.groq_client:
            resp = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
            )
            return resp.choices[0].message.content or ""

        elif self.provider in ["openai", "ollama"] and self.openai_client:
            resp = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
            )
            return resp.choices[0].message.content or ""

        elif self.provider == "gemini" and self.gemini_client:
            resp = self.gemini_client.models.generate_content(
                model=self.model,
                contents=f"{system_prompt}\n\n{prompt}"
            )
            return resp.text or ""

        # Fallback / Mock mode response
        return f"[Demo Mode - {self.model}]: Based on your data analysis, key drivers and trends indicate stable performance. To unlock live LLM reasoning, configure your GROQ_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY in the settings."

    def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        response_model: Type[T],
        mock_fallback_factory: Optional[callable] = None,
    ) -> T:
        """
        Generates validated structured output adhering to a Pydantic model.
        Falls back gracefully to mock_fallback_factory if API keys are missing or parsing fails.
        """
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        full_system = f"{system_prompt}\n\nYou MUST respond STRICTLY with a valid JSON object adhering to this JSON Schema:\n{schema_json}\nDo not include any prose, explanations, or text outside the valid JSON object."

        raw_output = ""
        if self.provider != "mock":
            try:
                if self.provider == "groq" and self.groq_client:
                    resp = self.groq_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": full_system},
                            {"role": "user", "content": prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=self.temperature,
                    )
                    raw_output = resp.choices[0].message.content or ""

                elif self.provider in ["openai", "ollama"] and self.openai_client:
                    resp = self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": full_system},
                            {"role": "user", "content": prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=self.temperature,
                    )
                    raw_output = resp.choices[0].message.content or ""

                elif self.provider == "gemini" and self.gemini_client:
                    resp = self.gemini_client.models.generate_content(
                        model=self.model,
                        contents=f"{full_system}\n\n{prompt}",
                        config={"response_mime_type": "application/json"}
                    )
                    raw_output = resp.text or ""

                # Parse JSON and validate against Pydantic model
                clean_json_str = self._extract_json_from_text(raw_output)
                parsed_dict = json.loads(clean_json_str)
                return response_model.model_validate(parsed_dict)

            except Exception as e:
                logger.warning(f"LLM generation/parsing failed ({e}). Falling back to schema synthesis...")

        # Fallback to provided mock factory or create instance
        if mock_fallback_factory:
            return mock_fallback_factory()
        return response_model.model_validate({})

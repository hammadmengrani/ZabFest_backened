import google.generativeai as genai
from langchain_core.language_models.llms import LLM
from typing import Optional, List, Any

genai.configure(api_key="AIzaSyD5xpx54iRKW2ljyK95gFepJ7irbzhK3W8")


class GeminiLLM(LLM):
    model_name: str = "gemini-2.0-flash"

    async def _acall(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        model = genai.GenerativeModel(self.model_name)
        response = await model.generate_content_async(prompt)

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content"):
                return candidate.content.strip()

        return "No response generated."

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """Raises error because we are async only now."""
        raise RuntimeError("Use 'acall' or 'ainvoke' with this async LLM.")

    @property
    def _llm_type(self) -> str:
        return "google_gemini"

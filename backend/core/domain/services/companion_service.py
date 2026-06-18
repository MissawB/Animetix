from typing import Optional, List
import re
from .llm_service import LLMService
from .prompt_manager import PromptManager


class CompanionService:
    """
    Service for AI Companions acting as archetypal mentors.
    Wraps user messages with personality prompts and retrieves RAG context.
    """

    MENTORS = {
        "sensei": {"prompt_id": "sensei_personality", "name": "Sensei"},
        "tsundere": {"prompt_id": "tsundere_personality", "name": "Tsundere-chan"},
        "kuudere": {"prompt_id": "kuudere_personality", "name": "Kuudere-san"},
    }

    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def generate_response(
        self,
        mentor_id: str,
        user_msg: str,
        context: str = "",
        history: Optional[List[dict]] = None,
    ) -> str:
        """
        Generates a response from a specific mentor.
        """
        if mentor_id not in self.MENTORS:
            raise ValueError(
                f"Unknown mentor ID: {mentor_id}. Available: {list(self.MENTORS.keys())}"
            )

        mentor_config = self.MENTORS[mentor_id]
        prompt_id = mentor_config["prompt_id"]

        # Format history for the prompt
        history_str = ""
        if history:
            for turn in history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                history_str += f"{role.capitalize()}: {content}\n"

        # Retrieve and format the prompt
        # Task 4: Use delimiters and sanitize user input/context
        prompt, system = self.prompt_manager.get_prompt(
            prompt_id,
            user_msg=self._sanitize_and_delimit(user_msg, "user_input"),
            context=self._sanitize_and_delimit(context, "context"),
            history=history_str,
        )

        # Call LLM
        return self.llm_service.generate(prompt, system_prompt=system)

    def _sanitize_and_delimit(self, text: str, tag: str) -> str:
        """
        Sanitizes input by stripping known prompt injection keywords and wraps it in XML-like tags.
        """
        if not text:
            return ""

        forbidden = [
            r"ignore previous instructions",
            r"ignore all previous",
            r"system prompt",
            r"developer mode",
            r"dan mode",
            r"you are now",
            r"act as",
            r"forget everything",
            r"reset prompt",
        ]

        sanitized = text
        for kw in forbidden:
            pattern = re.escape(kw)
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        return f"<{tag}>{sanitized}</{tag}>"

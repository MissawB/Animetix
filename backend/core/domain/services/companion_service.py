import re
import threading
from typing import List, Optional

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

    def __init__(
        self,
        llm_service: LLMService,
        prompt_manager: PromptManager,
        memory_service=None,
    ):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.memory_service = memory_service

    def generate_response(
        self,
        mentor_id: str,
        user_msg: str,
        context: str = "",
        history: Optional[List[dict]] = None,
        user_id: Optional[str] = None,
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

        # Retrieve memories for the prompt
        memories = ""
        if self.memory_service and user_id:
            memories = self.memory_service.retrieve_relevant_memories(user_id, user_msg)

        # Retrieve and format the prompt
        # Task 4: Use delimiters and sanitize user input/context
        prompt, system = self.prompt_manager.get_prompt(
            prompt_id,
            user_msg=self._sanitize_and_delimit(user_msg, "user_input"),
            context=self._sanitize_and_delimit(context, "context"),
            history=history_str,
            memories=memories,
        )

        # Call LLM
        return self.llm_service.generate(prompt, system_prompt=system)

    def remember(self, user_id, turns) -> None:
        """Persist evicted conversation turns into long-term memory, in the background."""
        if not (self.memory_service and user_id and turns):
            return
        threading.Thread(
            target=self.memory_service.store_memory,
            args=(user_id, turns),
            daemon=True,
        ).start()

    def _sanitize_and_delimit(self, text: str, tag: str) -> str:
        """
        Sanitizes input and wraps it in XML-like delimiters.

        Two layers: a keyword denylist (defense-in-depth, best-effort) and —
        critically — escaping of the ``<`` / ``>`` delimiter characters so user
        content can never close the ``<tag>…</tag>`` wrapper and inject
        instructions outside it (tag-breaking prompt injection). The escaping is
        the structural guarantee; the denylist is not relied upon for safety.
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

        # Neutralize the delimiters so the payload cannot break out of the
        # wrapper (e.g. "</user_input>…<user_input>"). Mirrors the escaping in
        # core.utils.security.sanitize_for_prompt.
        sanitized = sanitized.replace("<", "&lt;").replace(">", "&gt;")

        return f"<{tag}>{sanitized}</{tag}>"

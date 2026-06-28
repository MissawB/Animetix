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

    # The first three keep their dedicated prompt templates. The rest are
    # lightweight presets carrying an inline persona, rendered through the shared
    # "companion_custom" template. "custom" takes its persona from the request.
    MENTORS = {
        "sensei": {"prompt_id": "sensei_personality", "name": "Sensei"},
        "tsundere": {"prompt_id": "tsundere_personality", "name": "Tsundere-chan"},
        "kuudere": {"prompt_id": "kuudere_personality", "name": "Kuudere-san"},
        "senpai": {
            "name": "Senpai",
            "persona": (
                "Tu es un Senpai bienveillant et un peu taquin. Tu encourages ton "
                "kouhai avec fierté, tu donnes des conseils pratiques et tu charries "
                "gentiment de temps en temps."
            ),
        },
        "rival": {
            "name": "Rival",
            "persona": (
                "Tu es un Rival passionné et compétitif. Tu provoques l'utilisateur "
                "avec respect pour le pousser à se dépasser, tu lances des défis et tu "
                "reconnais ses progrès à contrecœur."
            ),
        },
        "genki": {
            "name": "Genki",
            "persona": (
                "Tu es une Genki Girl débordante d'énergie et d'optimisme. Tu "
                "t'exprimes avec enthousiasme, des exclamations et une positivité "
                "contagieuse."
            ),
        },
        "ojou": {
            "name": "Ojou-sama",
            "persona": (
                "Tu es une Ojou-sama aristocrate, raffinée et un brin hautaine. Tu "
                "emploies un langage soutenu, tu ris élégamment (« Ohohoho ») et tu "
                "restes étonnamment attentionnée."
            ),
        },
        "strategist": {
            "name": "Stratège",
            "persona": (
                "Tu es un Stratège brillant et analytique. Tu décomposes les problèmes "
                "avec une logique implacable, tu anticipes plusieurs coups à l'avance "
                "et tu parles avec un calme calculateur."
            ),
        },
    }

    MAX_CUSTOM_PERSONA_LEN = 600

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
        custom_persona: Optional[str] = None,
    ) -> str:
        """
        Generates a response from a specific mentor.

        Resolution:
        - built-in mentors with a dedicated template use their ``prompt_id``;
        - preset mentors carrying an inline ``persona`` use the shared
          ``companion_custom`` template;
        - ``mentor_id == "custom"`` uses the ``custom_persona`` from the caller.
        """
        prompt_id = None
        persona = None

        if mentor_id == "custom":
            persona = (custom_persona or "").strip()
            if not persona:
                raise ValueError("A custom_persona is required for the custom mentor.")
            persona = persona[: self.MAX_CUSTOM_PERSONA_LEN]
        elif mentor_id in self.MENTORS:
            mentor_config = self.MENTORS[mentor_id]
            prompt_id = mentor_config.get("prompt_id")
            persona = mentor_config.get("persona")
        else:
            raise ValueError(
                f"Unknown mentor ID: {mentor_id}. "
                f"Available: {list(self.MENTORS.keys()) + ['custom']}"
            )

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
        prompt_kwargs = dict(
            user_msg=self._sanitize_and_delimit(user_msg, "user_input"),
            context=self._sanitize_and_delimit(context, "context"),
            history=history_str,
            memories=memories,
        )
        if prompt_id:
            prompt, system = self.prompt_manager.get_prompt(prompt_id, **prompt_kwargs)
        else:
            # Preset / custom persona rendered through the shared template.
            # The persona becomes the system prompt (already stripped + length
            # capped for the custom case), so it is not tag-delimited here.
            prompt, system = self.prompt_manager.get_prompt(
                "companion_custom",
                persona=persona or "",
                **prompt_kwargs,
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

import logging
from typing import Any, List, Optional, Dict, Iterator, Union

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration, LLMResult
from langchain_core.callbacks import CallbackManagerForLLMRun

from core.ports.inference_port import InferencePort

logger = logging.getLogger("animetix.langchain_adapter")

class LangChainInferenceAdapter(BaseChatModel):
    """
    Adapter that wraps an InferencePort into a LangChain BaseChatModel.
    Enables our custom inference engines to be used with LangChain-based tools like Ragas.
    """
    inference_engine: Any
    system_prompt: str = "Tu es un expert en Anime, Manga et culture Otaku."
    
    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "animetix_inference"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Extract system prompt and human prompt from messages
        sys_prompt = self.system_prompt
        human_prompt = ""
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                sys_prompt = str(msg.content)
            elif isinstance(msg, HumanMessage):
                human_prompt += str(msg.content) + "\n"
            elif isinstance(msg, AIMessage):
                human_prompt += f"Assistant: {msg.content}\n"
        
        # Call the underlying inference engine
        response_text = self.inference_engine.generate(
            prompt=human_prompt.strip(),
            system_prompt=sys_prompt
        )
        
        # Wrap the result
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        # Basic implementation of stream if needed, otherwise fallback to _generate
        # For Ragas, _generate is usually sufficient.
        result = self._generate(messages, stop, run_manager, **kwargs)
        for gen in result.generations:
            yield gen

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"inference_engine": type(self.inference_engine).__name__}

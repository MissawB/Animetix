from django.utils.translation import gettext as _
from ....ports.inference_port import InferencePort
from ..prompt_manager import PromptManager

class MangaFlowService:
    """
    Manga-OCR & Translation : Pipeline intelligent pour les planches de manga.
    """
    def __init__(self, inference_engine: InferencePort, llm_service, prompt_manager: PromptManager):
        self.inference_engine = inference_engine
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager

    def translate_manga_page(self, image_data: bytes, target_lang: str = "French") -> str:
        # 1. OCR SOTA
        ocr_res = self.inference_engine.process_manga_page(image_data)
        
        # 2. Translation & Inpainting (Conceptual logic)
        # In a real scenario, we would iterate over bubbles. 
        # For now, we simulate the flow:
        prompt, system_prompt = self.prompt_manager.get_prompt(
            "manga_translation",
            target_lang=target_lang,
            original_text=ocr_res.get('text', '')
        )
            
        translated_text = self.llm_service.generate(prompt, system_prompt=system_prompt)
        
        # ... logic to inpaint using ocr_res['layout'] if provided ...
        return self.inference_engine.inpaint_text_bubbles(image_data, [{"text": translated_text, "bbox": [0,0,100,100]}])

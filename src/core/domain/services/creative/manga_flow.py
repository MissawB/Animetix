from django.utils.translation import gettext as _
from ....ports.inference_port import InferencePort

class MangaFlowService:
    """
    Manga-OCR & Translation : Pipeline intelligent pour les planches de manga.
    """
    def __init__(self, inference_engine: InferencePort, llm_service):
        self.inference_engine = inference_engine
        self.llm = llm_service

    def translate_manga_page(self, image_data: bytes, target_lang: str = "Français") -> str:
        page_info = self.inference_engine.process_manga_page(image_data)
        translated_placements = []
        for bubble in page_info.get('bubbles', []):
            original_text = bubble['text']
            prompt = _("Traduis ce texte de manga vers le {target_lang}. Garde le style original. Texte: {original_text}").format(target_lang=target_lang, original_text=original_text)
            translated_text = self.llm.generate(prompt, system_prompt=_("Tu es un traducteur expert de manga."))
            translated_placements.append({"bbox": bubble['bbox'], "text": translated_text})
        return self.inference_engine.inpaint_text_bubbles(image_data, translated_placements)

from adapters.inference.brain_api_adapter import BrainAPIAdapter
from core.ports.inference_port import InferencePort


def verify_adapter():
    adapter = BrainAPIAdapter(brain_api_url="http://localhost:8000")

    # Check if it implements InferencePort
    assert isinstance(adapter, InferencePort)

    methods_to_check = [
        "generate",
        "stream_generate",
        "generate_image",
        "calculate_visual_similarity",
        "get_image_embedding",
        "classify_image",
        "detect_objects",
        "get_video_temporal_embeddings",
        "localize_video_actions",
        "transform_image_to_anime",
        "transform_video_to_anime",
        "generate_soundscape",
        "clone_voice",
        "speech_to_speech",
        "estimate_depth",
        "generate_3d_scene",
        "process_manga_page",
        "translate_manga_page",
        "inpaint_text_bubbles",
        "moderate_content",
        "generate_image_description",
        "get_diagnostics",
        "calculate_uncertainty",
        "health_check",
        "visual_rerank",
        "get_multimodal_late_interaction",
    ]

    for method in methods_to_check:
        assert hasattr(adapter, method), f"Missing method: {method}"
        print(f"✓ Method {method} present")

    print("\nAll methods verified successfully!")


if __name__ == "__main__":
    verify_adapter()

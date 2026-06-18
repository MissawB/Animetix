import time
import logging
import argparse
import sys
import os
import io
import wave
import numpy as np
import psutil
from typing import List
from contextlib import contextmanager

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("benchmark.latency")

try:
    import torch  # noqa: E402

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.warning("torch not found, GPU memory tracking will be disabled.")

# Add src to path to import adapters
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))


@contextmanager
def measure_performance(name: str, results_list: List):
    """Context manager to measure latency and resource usage."""
    start_time = time.perf_counter()
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss / (1024 * 1024)  # MB

    if HAS_TORCH and torch.cuda.is_available():
        try:
            torch.cuda.memory_allocated() / (1024 * 1024)  # MB
        except:
            pass

    metrics = {"name": name, "status": "PASS"}
    try:
        yield metrics
    except Exception as e:
        metrics["status"] = f"FAIL ({str(e)})"
        logger.error(f"Benchmark {name} failed: {e}")
    finally:
        end_time = time.perf_counter()
        end_mem = process.memory_info().rss / (1024 * 1024)
        latency = (end_time - start_time) * 1000  # ms

        end_mem - start_mem
        metrics["latency_ms"] = latency
        metrics["ram_mb"] = end_mem

        if HAS_TORCH and torch.cuda.is_available():
            try:
                end_vram = torch.cuda.memory_allocated() / (1024 * 1024)
                metrics["vram_mb"] = end_vram
                logger.info(
                    f"BENCHMARK [{name}]: {latency:.2f}ms | RAM: {end_mem:.2f}MB | VRAM: {end_vram:.2f}MB"
                )
            except:
                logger.info(
                    f"BENCHMARK [{name}]: {latency:.2f}ms | RAM: {end_mem:.2f}MB"
                )
        else:
            logger.info(f"BENCHMARK [{name}]: {latency:.2f}ms | RAM: {end_mem:.2f}MB")

        results_list.append(metrics)


def create_dummy_video() -> bytes:
    """Creates a tiny valid MP4 buffer for benchmarking."""
    try:
        import imageio  # noqa: E402

        buf = io.BytesIO()
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        with imageio.get_writer(buf, format="mp4", fps=1) as writer:
            writer.append_data(frame)
        return buf.getvalue()
    except Exception as e:
        logger.warning(f"Could not create dummy video: {e}")
        return b"dummy_video_content"


def create_dummy_audio() -> bytes:
    """Creates a 1s silent WAV buffer for benchmarking."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(np.zeros(24000, dtype=np.int16).tobytes())
    return buf.getvalue()


def benchmark_video_style_transfer(results):
    """Benchmarks the Video Style Transfer module."""
    try:
        from adapters.inference.transformers_adapter import TransformersAdapter  # noqa: E402

        adapter = TransformersAdapter()
        video_data = create_dummy_video()

        logger.info("Starting Video Style Transfer benchmark...")
        with measure_performance("Video Style Transfer", results):
            adapter.transform_video_to_anime(video_data, "Ghibli", "landscape")

    except Exception as e:
        results.append(
            {
                "name": "Video Style Transfer",
                "status": f"SKIP ({str(e)})",
                "latency_ms": 0,
                "ram_mb": 0,
            }
        )


def benchmark_voice_ai(results):
    """Benchmarks the Voice AI (Speech-to-Speech) module."""
    try:
        from adapters.inference.transformers_adapter import TransformersAdapter  # noqa: E402

        adapter = TransformersAdapter()
        audio_data = create_dummy_audio()

        logger.info("Starting Voice AI (S2S) benchmark...")
        with measure_performance("Voice AI (S2S)", results):
            adapter.speech_to_speech(audio_data)

    except Exception as e:
        results.append(
            {
                "name": "Voice AI (S2S)",
                "status": f"SKIP ({str(e)})",
                "latency_ms": 0,
                "ram_mb": 0,
            }
        )


def benchmark_distillation(results):
    """Benchmarks a single training step of the Distillation loop."""
    try:
        from scripts.distill_draft_model import train_speculative_draft_model  # noqa: E402

        logger.info("Starting Distillation benchmark (1 step)...")
        with measure_performance("Model Distillation (SFT)", results):
            train_speculative_draft_model(
                epochs=0.01, output_dir="checkpoints/benchmark-distill"
            )
    except Exception as e:
        results.append(
            {
                "name": "Model Distillation (SFT)",
                "status": f"SKIP ({str(e)})",
                "latency_ms": 0,
                "ram_mb": 0,
            }
        )


def benchmark_video_rag(results):
    """Benchmarks Video Temporal Reasoning with Qwen2-VL."""
    try:
        from adapters.inference.transformers_adapter import TransformersAdapter  # noqa: E402

        adapter = TransformersAdapter()
        video_data = create_dummy_video()

        logger.info("Starting Video Temporal RAG benchmark...")
        with measure_performance("Video Temporal RAG (Qwen2-VL)", results):
            adapter.get_video_temporal_embeddings(video_data)
            adapter.localize_video_actions(video_data, ["combat"])

    except Exception as e:
        results.append(
            {
                "name": "Video Temporal RAG",
                "status": f"SKIP ({str(e)})",
                "latency_ms": 0,
                "ram_mb": 0,
            }
        )


def print_report(results):
    """Prints a professional ASCII report of the benchmarks."""
    print("\n" + "=" * 80)
    print(" 🎭 ANIMETIX SOTA 2026 PERFORMANCE REPORT")
    print("=" * 80)
    print(f"{'Pipeline':<35} | {'Status':<15} | {'Latency':<10} | {'RAM (MB)':<10}")
    print("-" * 80)
    for r in results:
        lat = f"{r.get('latency_ms', 0):.1f}ms" if r.get("latency_ms") else "N/A"
        ram = f"{r.get('ram_mb', 0):.1f}" if r.get("ram_mb") else "N/A"
        print(f"{r['name']:<35} | {r['status']:<15} | {lat:<10} | {ram:<10}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Latency and Resource Usage Benchmark")
    parser.add_argument("--all", action="store_true", help="Run all benchmarks")
    parser.add_argument(
        "--video", action="store_true", help="Run Video Style Transfer benchmark"
    )
    parser.add_argument("--voice", action="store_true", help="Run Voice AI benchmark")
    parser.add_argument(
        "--distill", action="store_true", help="Run Distillation benchmark"
    )
    parser.add_argument("--rag", action="store_true", help="Run Video RAG benchmark")

    args = parser.parse_args()
    results = []

    if not any(vars(args).values()):
        parser.print_help()
        return

    if args.all or args.video:
        benchmark_video_style_transfer(results)

    if args.all or args.voice:
        benchmark_voice_ai(results)

    if args.all or args.distill:
        benchmark_distillation(results)

    if args.all or args.rag:
        benchmark_video_rag(results)

    print_report(results)


if __name__ == "__main__":
    main()

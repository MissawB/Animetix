import time
import logging
import argparse
import sys
import os
import io
import wave
import numpy as np
import psutil
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("benchmark.latency")

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.warning("torch not found, GPU memory tracking will be disabled.")

# Add src to path to import adapters
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

@contextmanager
def measure_performance(name: str):
    """Context manager to measure latency and resource usage."""
    start_time = time.perf_counter()
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss / (1024 * 1024)  # MB
    
    start_vram = 0
    if HAS_TORCH and torch.cuda.is_available():
        start_vram = torch.cuda.memory_allocated() / (1024 * 1024)  # MB

    metrics = {}
    try:
        yield metrics
    finally:
        end_time = time.perf_counter()
        end_mem = process.memory_info().rss / (1024 * 1024)
        latency = (end_time - start_time) * 1000  # ms
        
        mem_diff = end_mem - start_mem
        
        logger.info(f"BENCHMARK [{name}]: {latency:.2f}ms | RAM: {end_mem:.2f}MB ({mem_diff:+.2f}MB)")
        
        if HAS_TORCH and torch.cuda.is_available():
            end_vram = torch.cuda.memory_allocated() / (1024 * 1024)
            vram_diff = end_vram - start_vram
            logger.info(f"BENCHMARK [{name}]: VRAM: {end_vram:.2f}MB ({vram_diff:+.2f}MB)")
            metrics['vram_mb'] = end_vram
            metrics['vram_diff_mb'] = vram_diff
            
        metrics['latency_ms'] = latency
        metrics['ram_mb'] = end_mem
        metrics['ram_diff_mb'] = mem_diff

def create_dummy_video() -> bytes:
    """Creates a tiny valid MP4 buffer for benchmarking."""
    try:
        import imageio
        buf = io.BytesIO()
        # Create a single black 64x64 frame
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        with imageio.get_writer(buf, format='mp4', fps=1, extension='.mp4') as writer:
            writer.append_data(frame)
        return buf.getvalue()
    except Exception as e:
        logger.warning(f"Could not create dummy video: {e}")
        return b"dummy_video_content"

def create_dummy_audio() -> bytes:
    """Creates a 1s silent WAV buffer for benchmarking."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        # 1 second of silence
        wf.writeframes(np.zeros(24000, dtype=np.int16).tobytes())
    return buf.getvalue()

def benchmark_video_style_transfer():
    """Benchmarks the Video Style Transfer module."""
    try:
        from adapters.inference.transformers_adapter import TransformersAdapter
        adapter = TransformersAdapter()
        video_data = create_dummy_video()
        
        logger.info("Starting Video Style Transfer benchmark...")
        with measure_performance("Video Style Transfer"):
            # Use a tiny strength and few steps if possible to speed up benchmark
            # but here we just call the method as it is.
            # TransformersAdapter.transform_video_to_anime(video_data, studio_style, prompt)
            adapter.transform_video_to_anime(video_data, "Ghibli", "landscape")
            
    except Exception as e:
        logger.error(f"SKIPPED (MISSING DEPS OR ERROR): Video Style Transfer - {e}")

def benchmark_voice_ai():
    """Benchmarks the Voice AI (Speech-to-Speech) module."""
    try:
        from adapters.inference.transformers_adapter import TransformersAdapter
        adapter = TransformersAdapter()
        audio_data = create_dummy_audio()
        
        logger.info("Starting Voice AI (S2S) benchmark...")
        with measure_performance("Voice AI (S2S)"):
            adapter.speech_to_speech(audio_data)
            
    except Exception as e:
        logger.error(f"SKIPPED (MISSING DEPS OR ERROR): Voice AI (S2S) - {e}")

def main():
    parser = argparse.ArgumentParser(description="Latency and Resource Usage Benchmark")
    parser.add_argument("--all", action="store_true", help="Run all benchmarks")
    parser.add_argument("--video", action="store_true", help="Run Video Style Transfer benchmark")
    parser.add_argument("--voice", action="store_true", help="Run Voice AI benchmark")
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
        return

    if args.all or args.video:
        benchmark_video_style_transfer()
        
    if args.all or args.voice:
        benchmark_voice_ai()

if __name__ == "__main__":
    main()

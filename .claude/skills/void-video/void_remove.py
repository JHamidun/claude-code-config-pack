#!/usr/bin/env python3
"""VOID - Remove objects from video via HuggingFace Spaces API.

Netflix's AI model for physics-aware object removal from video.
Uses the free HuggingFace Spaces demo as backend.

Usage:
    python void_remove.py input.mp4 mask.mp4 "Empty scene description" -o result.mp4
    python void_remove.py input.mp4 mask.mp4 "A table" --steps 50 -o hq_result.mp4
"""

import os
import sys
import argparse
import shutil


def remove_object(input_video: str, mask_video: str, prompt: str,
                  steps: int = 30, guidance: float = 1.0, seed: int = 42,
                  output_path: str = None) -> str:
    """Remove object from video using VOID model via HuggingFace Spaces.

    Args:
        input_video: Path to input video (.mp4)
        mask_video: Path to quadmask video (grayscale .mp4: 0=remove, 255=keep)
        prompt: Description of the scene AFTER object removal
        steps: Inference steps (10-50, higher=better but slower)
        guidance: Classifier-free guidance scale (1.0 recommended)
        seed: Random seed for reproducibility
        output_path: Where to save result (optional, returns temp path if None)

    Returns:
        Path to the output video file
    """
    try:
        from gradio_client import Client
    except ImportError:
        print("Installing gradio_client...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gradio_client", "-q"])
        from gradio_client import Client

    token = os.getenv('HUGGINGFACE_API_KEY')

    print(f"Connecting to VOID Space...")
    client = Client("<author>/VOID", hf_token=token)

    print(f"Running inference ({steps} steps)...")
    result = client.predict(
        input_video=input_video,
        mask_video=mask_video,
        prompt=prompt,
        num_steps=steps,
        guidance_scale=guidance,
        seed=seed,
        api_name="/run_inpaint"
    )

    if output_path:
        shutil.copy2(result, output_path)
        print(f"Saved to: {output_path}")
        return output_path

    print(f"Result at: {result}")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="VOID - Netflix Video Object & Interaction Deletion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s video.mp4 mask.mp4 "A table with cups on it" -o clean.mp4
  %(prog)s clip.mp4 quadmask.mp4 "Empty road" --steps 50 --seed 123 -o result.mp4

Quadmask format (grayscale video):
  Pixel 0   (black)     = Object to remove
  Pixel 63  (dark gray) = Overlap/interaction zone
  Pixel 127 (mid gray)  = Affected region (shadows, reflections)
  Pixel 255 (white)     = Background (keep)

Demo: https://huggingface.co/spaces/<author>/VOID
GitHub: https://github.com/Netflix/void-model
        """
    )
    parser.add_argument("input_video", help="Input video path (.mp4)")
    parser.add_argument("mask_video", help="Quadmask video path (.mp4, grayscale)")
    parser.add_argument("prompt", help="Scene description after object removal")
    parser.add_argument("--steps", type=int, default=30, help="Inference steps, 10-50 (default: 30)")
    parser.add_argument("--guidance", type=float, default=1.0, help="Guidance scale (default: 1.0)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output", "-o", help="Output video path")
    args = parser.parse_args()

    for path in [args.input_video, args.mask_video]:
        if not os.path.exists(path):
            print(f"Error: file not found: {path}")
            sys.exit(1)

    result = remove_object(
        args.input_video, args.mask_video, args.prompt,
        steps=args.steps, guidance=args.guidance, seed=args.seed,
        output_path=args.output
    )

    if not args.output:
        print(f"\nOutput: {result}")
        print("Tip: use -o result.mp4 to save to a specific path")


if __name__ == "__main__":
    main()

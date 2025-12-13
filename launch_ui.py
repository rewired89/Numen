#!/usr/bin/env python3
"""
Launch Numen UI (Gradio web interface).

Usage:
    python launch_ui.py [--share] [--port PORT]
"""

import argparse
from numen.ui.gradio_app import launch_ui


def main():
    parser = argparse.ArgumentParser(description="Launch Numen UI")
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create public share link (for remote access)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Server port (default: 7860)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🧮 NUMEN - MATHEMATICAL REASONING ENGINE")
    print("=" * 60)
    print("\nStarting Gradio UI...")
    print(f"URL: http://localhost:{args.port}")
    if args.share:
        print("Share link will be generated...")
    print("\nFeatures:")
    print("  📝 Text input for equations")
    print("  📷 Image upload with OCR")
    print("  📄 PDF/file processing")
    print("  🔐 Cryptanalysis")
    print("  🧠 Neural dynamics")
    print("\n" + "=" * 60 + "\n")

    launch_ui(
        share=args.share,
        server_name=args.host,
        server_port=args.port,
    )


if __name__ == "__main__":
    main()

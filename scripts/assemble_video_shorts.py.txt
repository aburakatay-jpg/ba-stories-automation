#!/usr/bin/env python3
"""
Dikey (9:16, 1080x1920) short videosu üretir - backgrounds/dikey
klasöründen rastgele bir klip seçip sesle birleştirir.

Kullanım:
  python3 assemble_video_shorts.py backgrounds/dikey ses.mp3 cikti.mp4
"""
import os
import random
import subprocess
import sys


def main():
    if len(sys.argv) != 4:
        print("Kullanım: assemble_video_shorts.py <dikey_klasoru> <ses.mp3> <cikti.mp4>", file=sys.stderr)
        sys.exit(1)

    bg_dir, audio_path, output_path = sys.argv[1:4]

    bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith((".mp4", ".mov"))]
    if not bg_files:
        print(f"Hata: {bg_dir} içinde arka plan videosu bulunamadı", file=sys.stderr)
        sys.exit(1)

    background = os.path.join(bg_dir, random.choice(bg_files))

    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", background,
        "-i", audio_path,
        "-vf", vf,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        output_path,
    ]

    subprocess.run(cmd, check=True)
    print(f"OK: {output_path}")


if __name__ == "__main__":
    main()
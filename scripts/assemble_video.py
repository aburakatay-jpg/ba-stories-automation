#!/usr/bin/env python3
"""
Sabit loop arka plan görseli + seslendirme + yakılmış altyazıyı
tek bir mp4'te birleştirir.

Kurulum: sunucuda ffmpeg kurulu olmalı (apt install ffmpeg)

Kullanım:
  python3 assemble_video.py backgrounds/ ses.mp3 altyazi.srt cikti.mp4

backgrounds/ klasöründe birkaç tane 30-60sn'lik atmosferik loop video
(.mp4) bulunur, her üretimde rastgele biri seçilir.
"""
import os
import random
import subprocess
import sys


def main():
    if len(sys.argv) != 5:
        print(
            "Kullanım: assemble_video.py <backgrounds_klasoru> <ses.mp3> <altyazi.srt> <cikti.mp4>",
            file=sys.stderr,
        )
        sys.exit(1)

    bg_dir, audio_path, srt_path, output_path = sys.argv[1:5]

    bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith((".mp4", ".mov"))]
    if not bg_files:
        print(f"Hata: {bg_dir} içinde arka plan videosu bulunamadı", file=sys.stderr)
        sys.exit(1)

    background = os.path.join(bg_dir, random.choice(bg_files))

    # Altyazı stili: beyaz yazı, siyah kontur, alt ortada
    subtitle_style = (
        "FontName=Arial,FontSize=20,PrimaryColour=&HFFFFFF&,"
        "OutlineColour=&H000000&,BorderStyle=1,Outline=2,Shadow=1,"
        "Alignment=2,MarginV=60"
    )

    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", background,
        "-i", audio_path,
        "-vf", f"subtitles={srt_path}:force_style='{subtitle_style}'",
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

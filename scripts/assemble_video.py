#!/usr/bin/env python3
"""
Sabit loop arka plan görseli + seslendirmeyi tek bir mp4'te birleştirir.
Çıktı HER ZAMAN 16:9 yatay formatta zorlanır (dikey arka plan videoları
kullanılsa bile) — bu, YouTube'un videoyu yanlışlıkla "Shorts" olarak
sınıflandırmasını engeller.

Kurulum: sunucuda ffmpeg kurulu olmalı (GitHub Actions runner'da hazır gelir)

Kullanım:
  python3 assemble_video.py backgrounds/ ses.mp3 cikti.mp4
"""
import os
import random
import subprocess
import sys


def main():
    if len(sys.argv) != 4:
        print(
            "Kullanım: assemble_video.py <backgrounds_klasoru> <ses.mp3> <cikti.mp4>",
            file=sys.stderr,
        )
        sys.exit(1)

    bg_dir, audio_path, output_path = sys.argv[1:4]

    bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith((".mp4", ".mov"))]
    if not bg_files:
        print(f"Hata: {bg_dir} içinde arka plan videosu bulunamadı", file=sys.stderr)
        sys.exit(1)

    background = os.path.join(bg_dir, random.choice(bg_files))

    # scale+crop ile HER arka plan videosunu (dikey/kare olsa bile) 1920x1080
    # 16:9 yatay çerçeveye zorluyoruz -> YouTube'un Shorts'a düşürmesini engeller
    vf = (
        "scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080"
    )

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

#!/usr/bin/env python3
"""
Arka plan klasöründeki BİRDEN FAZLA loop videosunu karıştırıp art arda
bağlar (tek bir klip boyunca loop atmak yerine), sesle birleştirir.
Çıktı her zaman 16:9 yatay formata zorlanır (Shorts'a düşmesin diye).

Kurulum: sunucuda ffmpeg + ffprobe kurulu olmalı (GitHub Actions runner'da hazır gelir)

Kullanım:
  python3 assemble_video.py backgrounds/ ses.mp3 cikti.mp4
"""
import json
import os
import random
import subprocess
import sys


def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def build_clip_sequence(bg_dir, target_duration):
    """Hedef süreyi karşılayana kadar karışık sırayla arka plan klipleri seç."""
    bg_files = [os.path.join(bg_dir, f) for f in os.listdir(bg_dir) if f.lower().endswith((".mp4", ".mov"))]
    if not bg_files:
        raise RuntimeError(f"{bg_dir} içinde arka plan videosu bulunamadı")

    random.shuffle(bg_files)
    sequence, total = [], 0.0
    i = 0
    while total < target_duration:
        clip = bg_files[i % len(bg_files)]
        sequence.append(clip)
        total += get_duration(clip)
        i += 1
        # aynı klip art arda 2'den fazla tekrar etmesin diye havuzu her turda yeniden karıştır
        if i % len(bg_files) == 0:
            random.shuffle(bg_files)
    return sequence


def main():
    if len(sys.argv) != 4:
        print("Kullanım: assemble_video.py <backgrounds_klasoru> <ses.mp3> <cikti.mp4>", file=sys.stderr)
        sys.exit(1)

    bg_dir, audio_path, output_path = sys.argv[1:4]
    audio_duration = get_duration(audio_path)
    sequence = build_clip_sequence(bg_dir, audio_duration)

    inputs = []
    for clip in sequence:
        inputs += ["-i", clip]
    inputs += ["-i", audio_path]
    audio_index = len(sequence)

    filter_parts = []
    concat_inputs = ""
    for idx in range(len(sequence)):
        filter_parts.append(
            f"[{idx}:v]scale=1920:1080:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,setsar=1[v{idx}]"
        )
        concat_inputs += f"[v{idx}]"
    filter_parts.append(f"{concat_inputs}concat=n={len(sequence)}:v=1:a=0[outv]")
    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", f"{audio_index}:a:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        output_path,
    ]

    subprocess.run(cmd, check=True)
    print(f"OK: {output_path} ({len(sequence)} klip birleştirildi)")


if __name__ == "__main__":
    main()
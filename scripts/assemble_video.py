#!/usr/bin/env python3
"""
Arka plan klasöründeki BİRDEN FAZLA loop videosunu karıştırıp art arda
bağlar, anlatım sesiyle ve arka plan müziğiyle birleştirir.

Müzik, anlatıcı konuşurken otomatik olarak kısılır ("ducking" - sidechain
compression), sessiz anlarda biraz daha belirginleşir. Bu sayede müzik asla
anlatıcının önüne geçmez.

Çıktı her zaman 16:9 yatay formata zorlanır (Shorts'a düşmesin diye).

Kullanım:
  python3 assemble_video.py backgrounds/yatay ses.mp3 cikti.mp4 music vid_
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
        if i % len(bg_files) == 0:
            random.shuffle(bg_files)
    return sequence


def pick_music(music_dir, prefix):
    files = [f for f in os.listdir(music_dir) if f.startswith(prefix) and f.lower().endswith((".mp3", ".wav", ".m4a"))]
    if not files:
        return None
    return os.path.join(music_dir, random.choice(files))


def main():
    if len(sys.argv) != 6:
        print(
            "Kullanım: assemble_video.py <backgrounds_klasoru> <ses.mp3> <cikti.mp4> <music_klasoru> <music_onek>",
            file=sys.stderr,
        )
        sys.exit(1)

    bg_dir, audio_path, output_path, music_dir, music_prefix = sys.argv[1:6]
    audio_duration = get_duration(audio_path)
    sequence = build_clip_sequence(bg_dir, audio_duration)
    music_path = pick_music(music_dir, music_prefix)

    inputs = []
    for clip in sequence:
        inputs += ["-i", clip]
    narration_idx = len(sequence)
    inputs += ["-i", audio_path]

    filter_parts = []
    concat_inputs = ""
    for idx in range(len(sequence)):
        filter_parts.append(
            f"[{idx}:v]scale=1920:1080:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,setsar=1[v{idx}]"
        )
        concat_inputs += f"[v{idx}]"
    filter_parts.append(f"{concat_inputs}concat=n={len(sequence)}:v=1:a=0[outv]")

    if music_path:
        music_idx = narration_idx + 1
        inputs += ["-stream_loop", "-1", "-i", music_path]
        filter_parts.append(f"[{music_idx}:a]volume=0.15[music_vol]")
        filter_parts.append(
            f"[music_vol][{narration_idx}:a]sidechaincompress="
            f"threshold=0.05:ratio=8:attack=20:release=400:makeup=1[music_duck]"
        )
        filter_parts.append(f"[{narration_idx}:a][music_duck]amix=inputs=2:duration=first:normalize=0[aout]")
        audio_map = "[aout]"
    else:
        audio_map = f"{narration_idx}:a:0"

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", audio_map,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        output_path,
    ]

    subprocess.run(cmd, check=True)
    print(f"OK: {output_path} ({len(sequence)} klip, müzik: {'var' if music_path else 'yok'})")


if __name__ == "__main__":
    main()
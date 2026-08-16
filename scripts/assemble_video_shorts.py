#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import glob
import random

def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])

def main():
    if len(sys.argv) not in (5, 6):
        print("Kullanım: assemble_video_shorts.py <gorsel_prefix> <ses.mp3> <cikti.mp4> <music_dir> [music_prefix]")
        sys.exit(1)

    prefix = sys.argv[1]
    audio_path = sys.argv[2]
    output_path = sys.argv[3]
    music_dir = sys.argv[4]
    
    music_prefix = sys.argv[5] if len(sys.argv) == 6 else ""

    images = sorted(glob.glob(f"{prefix}_*.jpg"))
    
    if not images:
        if os.path.exists(prefix):
            images = [prefix]
        else:
            print("Hiç görsel bulunamadı!")
            sys.exit(1)

    audio_duration = get_duration(audio_path)
    fps = 30
    total_frames = int(audio_duration * fps)
    
    frames_per_image = total_frames // len(images)
    if frames_per_image < 1:
        frames_per_image = 1

    cmd = ["ffmpeg", "-y"]

    for img in images:
        cmd += ["-loop", "1", "-i", img]

    cmd += ["-i", audio_path]

    music_path = None
    if os.path.exists(music_dir):
        music_files = [f for f in os.listdir(music_dir) if f.startswith(music_prefix) and f.endswith(('.mp3','.wav'))]
        if music_files:
            music_path = os.path.join(music_dir, random.choice(music_files))
            cmd += ["-stream_loop", "-1", "-i", music_path]

    filter_parts = []
    video_maps = []
    for i, img in enumerate(images):
        # Ken Burns efekti
        vf = f"zoompan=z='min(zoom+0.0002,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_per_image}:s=1080x1920:fps={fps}"
        # HATALI KISIM DÜZELTİLDİ: Sadece PTS-STARTPTS olmalı, zaman kaydırmasını kaldırdık!
        filter_parts.append(f"[{i}:v]{vf},setpts=PTS-STARTPTS[v{i}]")
        video_maps.append(f"[v{i}]")

    concat_filter = f"concat=n={len(images)}:v=1:a=0[outv]"
    filter_parts.append(f"{''.join(video_maps)}{concat_filter}")

    audio_idx = len(images)
    if music_path:
        music_idx = len(images) + 1
        filter_parts.append(f"[{music_idx}:a]volume=0.15[music_vol]")
        filter_parts.append(f"[music_vol][{audio_idx}:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400:makeup=1[music_duck]")
        filter_parts.append(f"[{audio_idx}:a][music_duck]amix=inputs=2:duration=first:normalize=0[aout]")
        audio_map = "[aout]"
    else:
        audio_map = f"{audio_idx}:a:0"

    filter_complex = ";".join(filter_parts)

    cmd += ["-filter_complex", filter_complex]
    cmd += ["-map", "[outv]", "-map", audio_map]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "23"]
    cmd += ["-c:a", "aac", "-b:a", "128k"]
    cmd += ["-t", str(audio_duration)]
    cmd += [output_path]

    subprocess.run(cmd, check=True)
    print(f"Video oluşturuldu: {output_path}")

if __name__ == "__main__":
    main()

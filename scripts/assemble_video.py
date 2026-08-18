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
        print("Kullanım: assemble_video.py <gorsel_klasoru> <ses.mp3> <cikti.mp4> <music_dir> [music_prefix]")
        sys.exit(1)

    img_dir = sys.argv[1]
    audio_path = sys.argv[2]
    output_path = sys.argv[3]
    music_dir = sys.argv[4]
    music_prefix = sys.argv[5] if len(sys.argv) == 6 else ""

    images = sorted(glob.glob(os.path.join(img_dir, "*.jpg")))
    
    if not images:
        print(f"{img_dir} içinde hiç görsel bulunamadı!")
        sys.exit(1)

    audio_duration = get_duration(audio_path)
    fps = 30
    N = len(images)
    fade_dur = 1.5 # Uzun videolar için daha yavaş, 1.5 saniyelik sinematik geçiş
    
    if N > 1:
        clip_duration = (audio_duration + (N - 1) * fade_dur) / N
    else:
        clip_duration = audio_duration
        
    frames_per_image = int(clip_duration * fps)
    actual_clip_duration = frames_per_image / fps
    
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
        # 1920x1080 Yatay Ken Burns Efekti (Çok daha yavaş ve dengeli bir yakınlaşma)
        vf = f"zoompan=z='min(zoom+0.00015,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_per_image}:s=1920x1080:fps={fps}"
        filter_parts.append(f"[{i}:v]{vf},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
        
    if N == 1:
        filter_parts.append(f"[v0]copy[outv]")
    else:
        current_offset = actual_clip_duration - fade_dur
        last_out = "v0"
        for i in range(1, N):
            next_out = f"f{i}" if i < N - 1 else "outv"
            filter_parts.append(f"[{last_out}][v{i}]xfade=transition=fade:duration={fade_dur}:offset={current_offset:.3f}[{next_out}]")
            last_out = next_out
            current_offset += (actual_clip_duration - fade_dur)

    audio_idx = len(images)
    if music_path:
        music_idx = len(images) + 1
        filter_parts.append(f"[{music_idx}:a]volume=0.10[music_vol]") # Yatay videolarda müzik sesi biraz daha kısık olmalı
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
    print(f"Yatay Video oluşturuldu: {output_path}")

if __name__ == "__main__":
    main()

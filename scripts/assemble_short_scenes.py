#!/usr/bin/env python3
import os
import subprocess
import sys
import random
import json
import re

def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])

def build_zoom_expr(total_frames):
    target = 1.3
    increment = (target - 1.0) / total_frames if total_frames > 0 else 0.001
    return f"z='min(zoom+{increment:.8f},{target})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

def main():
    if len(sys.argv) != 5:
        print("Kullanım: assemble_short_scenes.py <gorsel_klasoru> <ses.mp3> <cikti.mp4> <music_klasoru> <music_onek>")
        sys.exit(1)

    img_dir = sys.argv[1]
    audio_path = sys.argv[2]
    output_path = sys.argv[3]
    music_dir = sys.argv[4]
    music_prefix = sys.argv[5] if len(sys.argv) > 5 else ""

    # Tüm scene_*.jpg dosyalarını al
    images = sorted([f for f in os.listdir(img_dir) if f.startswith("scene_") and f.endswith(".jpg")])
    if not images:
        print("Hiç sahne görseli bulunamadı! output/scenes/ klasörünü kontrol et.")
        sys.exit(1)

    duration = get_duration(audio_path)
    fps = 30
    total_frames = int(duration * fps)
    scenes_count = len(images)
    per_scene = total_frames // scenes_count

    # Müzik seçimi (sadece prefix ile başlayan dosyalar)
    music_files = [f for f in os.listdir(music_dir) if f.startswith(music_prefix) and f.endswith((".mp3", ".wav"))]
    music_path = os.path.join(music_dir, random.choice(music_files)) if music_files else None

    # FFmpeg komutu oluştur
    cmd = ["ffmpeg", "-y"]
    # Görselleri ekle
    for img in images:
        cmd += ["-i", os.path.join(img_dir, img)]
    cmd += ["-i", audio_path]
    if music_path:
        cmd += ["-stream_loop", "-1", "-i", music_path]

    # Filter complex oluştur
    filter_parts = []
    # Her görsel için zoompan + scale/crop
    for i in range(scenes_count):
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan={build_zoom_expr(per_scene)}:d={per_scene}:s=1080x1920:fps={fps},setpts=PTS-STARTPTS"
        filter_parts.append(f"[{i}:v]{vf}[v{i}]")
    # Geçişler (fade) – her sahne arası 0.5 saniye fade
    concat_inputs = []
    for i in range(scenes_count):
        concat_inputs.append(f"[v{i}]")
    concat_filter = f"{''.join(concat_inputs)}concat=n={scenes_count}:v=1:a=0,format=yuv420p[vout]"
    filter_parts.append(concat_filter)

    # Ses işleme
    if music_path:
        music_idx = scenes_count + 2
        filter_parts.append(f"[{music_idx}:a]volume=0.15[music_vol]")
        filter_parts.append(f"[music_vol][{scenes_count}:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400:makeup=1[music_duck]")
        filter_parts.append(f"[{scenes_count}:a][music_duck]amix=inputs=2:duration=first:normalize=0[aout]")
        audio_map = "[aout]"
    else:
        audio_map = f"{scenes_count}:a:0"

    filter_complex = ";".join(filter_parts)
    cmd += ["-filter_complex", filter_complex]
    cmd += ["-map", "[vout]", "-map", audio_map]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "23"]
    cmd += ["-c:a", "aac", "-b:a", "128k"]
    cmd += ["-t", str(duration), output_path]

    print("FFmpeg komutu çalıştırılıyor...")
    subprocess.run(cmd, check=True)
    print(f"Video oluşturuldu: {output_path}")

if __name__ == "__main__":
    main()

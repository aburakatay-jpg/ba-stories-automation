#!/usr/bin/env python3
"""
Birden fazla sahne görselini Ken Burns efekti ile birleştirir, aralara fade geçiş ekler,
ses ve müzik ile harmanlar.
Kullanım: python assemble_video_scenes.py <scene_klasoru> <ses.mp3> <cikti.mp4> <music_klasoru> <music_onek>
"""
import os
import sys
import json
import subprocess
import random
import re

def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])

def pick_music(music_dir, prefix):
    files = [f for f in os.listdir(music_dir) if f.startswith(prefix) and f.lower().endswith((".mp3", ".wav", ".m4a"))]
    if not files:
        return None
    return os.path.join(music_dir, random.choice(files))

def build_zoom_expr(total_frames, target_zoom=1.3):
    increment = (target_zoom - 1.0) / total_frames
    variants = [
        f"z='min(zoom+{increment:.8f},{target_zoom})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
        f"z='if(eq(on,0),{target_zoom},max(zoom-{increment:.8f},1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",
        f"z='min(zoom+{increment:.8f},{target_zoom})':x='(iw-iw/zoom)*on/{total_frames}':y='ih/2-(ih/zoom/2)'",
        f"z='min(zoom+{increment:.8f},{target_zoom})':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*on/{total_frames}'",
    ]
    return random.choice(variants)

def main():
    if len(sys.argv) != 6:
        print("Kullanım: assemble_video_scenes.py <scene_klasoru> <ses.mp3> <cikti.mp4> <music_klasoru> <music_onek>")
        sys.exit(1)
    
    scene_dir, audio_path, output_path, music_dir, music_prefix = sys.argv[1:6]
    
    # Kaç sahne var?
    count_file = os.path.join(scene_dir, "scene_count.txt")
    if not os.path.exists(count_file):
        print("❌ scene_count.txt bulunamadı!")
        sys.exit(1)
    with open(count_file, "r") as f:
        num_scenes = int(f.read().strip())
    
    # Sahne görsellerini sıralı al
    scene_files = []
    for i in range(1, num_scenes+1):
        fname = f"scene_{i:03d}.jpg"
        path = os.path.join(scene_dir, fname)
        if os.path.exists(path):
            scene_files.append(path)
        else:
            print(f"⚠️ {path} bulunamadı, atlanıyor.")
    
    if not scene_files:
        print("❌ Hiç sahne görseli yok!")
        sys.exit(1)
    
    # Ses süresi
    duration = get_duration(audio_path)
    fps = 30
    total_frames = int(duration * fps)
    
    # Her sahneye eşit süre dağıt (son sahne kalan süreyi alır)
    scene_duration = duration / len(scene_files)
    scene_frames = int(scene_duration * fps)
    
    # FFmpeg filter complex oluştur
    inputs = []
    filter_parts = []
    map_parts = []
    concat_inputs = []
    
    for idx, img_path in enumerate(scene_files):
        inputs.extend(["-loop", "1", "-i", img_path])
        # Her görsel için Ken Burns
        zexpr = build_zoom_expr(scene_frames)
        vf = f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan={zexpr}:d={scene_frames}:s=1080x1920:fps={fps}"
        filter_parts.append(f"[{idx}:v]{vf}[v{idx}]")
        concat_inputs.append(f"[v{idx}]")
    
    # Geçiş efekti (fade) – her sahne arasına fade
    # Basitçe concat ile birleştirip sonra fade ekleyelim (veya filter_complex içinde)
    # Daha basit: concat ile birleştir, sonra genel fade
    concat_filter = f"concat=n={len(scene_files)}:v=1:a=0[outv]"
    filter_parts.append(";".join(filter_parts) + ";" + concat_filter)
    
    # Ses ve müzik
    inputs.append("-i")
    inputs.append(audio_path)
    audio_idx = len(scene_files)
    
    music_path = pick_music(music_dir, music_prefix)
    if music_path:
        inputs.extend(["-stream_loop", "-1", "-i", music_path])
        music_idx = len(scene_files) + 1
        filter_parts.append(f"[{music_idx}:a]volume=0.15[music_vol]")
        filter_parts.append(f"[music_vol][{audio_idx}:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400:makeup=1[music_duck]")
        filter_parts.append(f"[{audio_idx}:a][music_duck]amix=inputs=2:duration=first:normalize=0[aout]")
        audio_map = "[aout]"
    else:
        audio_map = f"{audio_idx}:a"
    
    filter_complex = ";".join(filter_parts)
    
    # FFmpeg komutu
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", audio_map,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(duration),
        output_path,
    ]
    
    subprocess.run(cmd, check=True)
    print(f"✅ Video oluşturuldu: {output_path} (müzik: {'var' if music_path else 'yok'})")

if __name__ == "__main__":
    main()

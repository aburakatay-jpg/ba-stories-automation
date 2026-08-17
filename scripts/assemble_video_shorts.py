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
    N = len(images)
    fade_dur = 1.0 # 1 saniyelik yumuşak geçiş (crossfade) süresi
    
    # Geçiş sürelerini hesaba katarak her görselin ekranda kalma süresini hesapla
    # Çünkü görseller birbiri üzerine bindiğinde toplam video süresi kısalır
    if N > 1:
        clip_duration = (audio_duration + (N - 1) * fade_dur) / N
    else:
        clip_duration = audio_duration
        
    frames_per_image = int(clip_duration * fps)
    actual_clip_duration = frames_per_image / fps # Kusursuz offset hesaplama için
    
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
        # xfade (geçiş) filtresinin çalışması için formatın yuv420p olması zorunludur
        filter_parts.append(f"[{i}:v]{vf},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
        
    # --- YENİ EKLENEN YUMUŞAK GEÇİŞ (XFADE) MANTIĞI ---
    if N == 1:
        filter_parts.append(f"[v0]copy[outv]")
    else:
        current_offset = actual_clip_duration - fade_dur
        last_out = "v0"
        for i in range(1, N):
            next_out = f"f{i}" if i < N - 1 else "outv"
            # xfade ile bir önceki görseli bir sonraki görsele yumuşakça bağla
            filter_parts.append(f"[{last_out}][v{i}]xfade=transition=fade:duration={fade_dur}:offset={current_offset:.3f}[{next_out}]")
            last_out = next_out
            current_offset += (actual_clip_duration - fade_dur)

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

    print("Çalıştırılacak komut (xfade ile):")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Video oluşturuldu: {output_path}")

if __name__ == "__main__":
    main()

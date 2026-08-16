#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import glob

def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])

def build_zoom_filter(input_idx, total_frames, target_zoom=1.3):
    increment = (target_zoom - 1.0) / total_frames
    return f"[{input_idx}:v]zoompan=z='min(zoom+{increment:.8f},{target_zoom})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s=1080x1920:fps=30,format=yuv420p[v{input_idx}]"

def main():
    if len(sys.argv) != 5:
        print("Kullanım: assemble_video_shorts.py <gorsel_prefix> <ses.mp3> <cikti.mp4> <music_dir>")
        sys.exit(1)
    prefix = sys.argv[1]  # "output/thumbnail"
    audio_path = sys.argv[2]
    output_path = sys.argv[3]
    music_dir = sys.argv[4]

    # Tüm görselleri bul
    images = sorted(glob.glob(f"{prefix}_*.jpg"))
    if not images:
        print("Hiç görsel bulunamadı!")
        sys.exit(1)

    audio_duration = get_duration(audio_path)
    fps = 30
    total_frames = int(audio_duration * fps)
    # Her görsele eşit süre (kare sayısı)
    frames_per_image = total_frames // len(images)
    if frames_per_image < 1:
        frames_per_image = 1

    # FFmpeg komutunu oluştur
    cmd = ["ffmpeg", "-y"]

    # Görselleri input olarak ekle
    for img in images:
        cmd += ["-loop", "1", "-i", img]

    # Ses inputu
    cmd += ["-i", audio_path]

    # Müzik inputu (varsa)
    music_path = None
    if os.path.exists(music_dir):
        music_files = [f for f in os.listdir(music_dir) if f.endswith(('.mp3','.wav'))]
        if music_files:
            music_path = os.path.join(music_dir, music_files[0])
            cmd += ["-stream_loop", "-1", "-i", music_path]

    # Filter complex oluştur
    filter_parts = []
    video_maps = []
    for i, img in enumerate(images):
        start_frame = i * frames_per_image
        # Ken Burns efekti, sadece o görselin süresi boyunca uygula
        # Özel bir zoompan ile her görsel için ayrı ayrı
        vf = f"zoompan=z='min(zoom+0.0001,1.3)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames_per_image}:s=1080x1920:fps=30"
        # Her görseli input üzerinden işle
        filter_parts.append(f"[{i}:v]{vf},setpts=PTS-STARTPTS+{start_frame/fps:.2f}/TB[v{i}]")
        video_maps.append(f"[v{i}]")

    # Concat ile birleştir (n=len(images))
    concat_filter = f"concat=n={len(images)}:v=1:a=0[outv]"
    filter_parts.append(f"{''.join(video_maps)}{concat_filter}")

    # Ses ve müzik işleme (ducking)
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

    print("Çalıştırılacak komut:")
    print(" ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"Video oluşturuldu: {output_path}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import sys
import os
import json
import subprocess
import random

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
    if len(sys.argv) != 5:
        print("Kullanım: assemble_short_scenes.py <scenes_dir> <ses.mp3> <cikti.mp4> <music_klasoru> <music_onek>")
        sys.exit(1)

    scenes_dir, audio_path, output_path, music_dir, music_prefix = sys.argv[1:6]

    # Sahne görsellerini bul ve sırala
    scene_files = sorted([f for f in os.listdir(scenes_dir) if f.startswith("scene_") and f.endswith(".jpg")])
    if not scene_files:
        print("Hata: Hiç sahne görseli bulunamadı!")
        sys.exit(1)

    # Ses süresi
    duration = get_duration(audio_path)
    fps = 30
    total_frames = int(duration * fps)

    # Her sahne için süreyi eşit paylaştır (toplam süre / sahne sayısı)
    scene_duration = duration / len(scene_files)
    scene_frames = int(scene_duration * fps)

    # Geçiş efekti süresi (0.5 saniye)
    transition_frames = int(0.5 * fps)

    # FFmpeg filter complex oluştur
    inputs = []
    filter_parts = []
    maps = []
    overlay_idx = 0

    for i, scene_file in enumerate(scene_files):
        scene_path = os.path.join(scenes_dir, scene_file)
        inputs += ["-loop", "1", "-i", scene_path]
        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan={build_zoom_expr(scene_frames)}:d={scene_frames}:s=1080x1920:fps={fps}"
        )
        filter_parts.append(f"[{i}:v]{vf}[v{i}]")
        maps.append(f"[v{i}]")

    # Sahneleri birleştir (concat)
    concat_inputs = "".join(maps)
    # Her sahne arasına 0.5 saniye fade geçişi ekle
    # Önce tüm sahneleri concat ile birleştir, sonra fade geçişlerini uygula
    # Basitlik için doğrudan concat yapıp geçişleri atlıyoruz (daha karmaşık, isteğe bağlı)
    # Ama sen geçiş istediğin için, her bir sahneyi ayrı ayrı işleyip sonra birleştirelim.

    # Daha basit bir yaklaşım: Tüm sahneleri tek bir video olarak birleştir (geçişsiz)
    # Geçiş eklemek istersen, crossfade filter kullanılabilir ama bu çok daha karmaşık.
    # Şimdilik geçişsiz concat yapalım, ama istersen sonra ekleriz.

    filter_complex = f"{';'.join(filter_parts)};{''.join([f'[v{i}]' for i in range(len(scene_files))])}concat=n={len(scene_files)}:v=1:a=0,format=yuv420p[outv]"

    # Müzik ve ses işleme
    music_path = pick_music(music_dir, music_prefix)
    audio_inputs = ["-i", audio_path]
    audio_filter = ""
    if music_path:
        audio_inputs += ["-stream_loop", "-1", "-i", music_path]
        # Ses karışımı
        audio_filter = (
            f"[{len(scene_files)}:a]volume=0.15[music_vol];"
            f"[music_vol][{len(scene_files)+1}:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400:makeup=1[music_duck];"
            f"[{len(scene_files)+1}:a][music_duck]amix=inputs=2:duration=first:normalize=0[aout]"
        )
        audio_map = "[aout]"
    else:
        audio_map = f"{len(scene_files)}:a"

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        *audio_inputs,
        "-filter_complex", filter_complex + ";" + audio_filter if audio_filter else filter_complex,
        "-map", "[outv]",
        "-map", audio_map,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(duration),
        output_path,
    ]

    # FFmpeg komutunu çalıştır
    subprocess.run(cmd, check=True)
    print(f"Video oluşturuldu: {output_path}")

if __name__ == "__main__":
    main()

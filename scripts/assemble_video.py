#!/usr/bin/env python3
"""
Arka plan klasöründeki loop videolarını birleştirip anlatım sesi ve
müzikle birleştirir. 16:9 yatay format zorlanır.

Kullanım:
  python3 assemble_video.py backgrounds/yatay ses.mp3 cikti.mp4 music vid_
"""
import json
import os
import random
import subprocess
import sys
import tempfile


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


def main():
    if len(sys.argv) != 6:
        print("Kullanım: assemble_video.py <bg_dir> <ses.mp3> <cikti.mp4> <music_dir> <music_prefix>", file=sys.stderr)
        sys.exit(1)

    bg_dir, audio_path, output_path, music_dir, music_prefix = sys.argv[1:6]
    audio_duration = get_duration(audio_path)
    music_path = pick_music(music_dir, music_prefix)

    # Arka plan videolarını listele
    bg_files = [os.path.join(bg_dir, f) for f in os.listdir(bg_dir) if f.lower().endswith((".mp4", ".mov"))]
    if not bg_files:
        raise RuntimeError(f"{bg_dir} içinde arka plan videosu bulunamadı")

    # Geçici concat listesi dosyası oluştur
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        concat_list = f.name
        total = 0.0
        used = []
        random.shuffle(bg_files)
        i = 0
        while total < audio_duration:
            clip = bg_files[i % len(bg_files)]
            used.append(clip)
            total += get_duration(clip)
            f.write(f"file '{os.path.abspath(clip)}'\n")
            i += 1
            if i % len(bg_files) == 0:
                random.shuffle(bg_files)
            if len(used) >= 6:
                break

    # Adım 1: Videoları birleştir ve scale et
    temp_video = output_path + "_temp_video.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-an", temp_video,
    ], check=True)

    os.unlink(concat_list)

    # Adım 2: Sesi karıştır (anlatım + müzik + loudnorm)
    temp_audio = output_path + "_temp_audio.aac"
    if music_path:
       subprocess.run([
            "ffmpeg", "-y",
            "-i", audio_path,
            "-stream_loop", "-1", "-i", music_path,
            "-filter_complex",
            "[0:a]volume=1.0[narr];"
            "[1:a]volume=0.08[music];"
            "[narr][music]amix=inputs=2:duration=first:normalize=0[premix];"
            "[premix]loudnorm=I=-14:TP=-1.5:LRA=11[aout]",
            "-map", "[aout]",
            "-c:a", "aac", "-b:a", "128k",
            "-t", str(max_duration),

            temp_audio,
        ], check=True)
    else:
            max_duration = min(audio_duration, 660)  # maksimum 11 dakika
    subprocess.run([
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-t", str(max_duration),
        "-an", temp_video,
    ], check=True)


    # Adım 3: Video + ses birleştir
    subprocess.run([
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", temp_audio,
        "-c:v", "copy", "-c:a", "copy",
        "-shortest",
        output_path,
    ], check=True)

    os.unlink(temp_video)
    os.unlink(temp_audio)

    print(f"OK: {output_path} ({len(used)} klip, müzik: {'var' if music_path else 'yok'})")


if __name__ == "__main__":
    main()

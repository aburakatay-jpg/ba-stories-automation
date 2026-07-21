#!/usr/bin/env python3
"""
Tek bir görsele (üretilen thumbnail) Ken Burns efekti uygulayarak dikey
short videosu üretir, arka plan müziğiyle (ducking'li) birleştirir.

Kamera hareketi videonun TAM SÜRESİNE göre hesaplanır - erken durup
donmaz, son kareye kadar sürer.

Kullanım:
  python3 assemble_video_shorts.py thumbnail.jpg ses.mp3 cikti.mp4 music shorts_
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


def pick_music(music_dir, prefix):
    files = [f for f in os.listdir(music_dir) if f.startswith(prefix) and f.lower().endswith((".mp3", ".wav", ".m4a"))]
    if not files:
        return None
    return os.path.join(music_dir, random.choice(files))


def build_zoom_expr(total_frames, target_zoom=1.3):
    """Zoom, tam olarak son kareye kadar süren bir hızda ilerler - erken durup donmaz."""
    increment = (target_zoom - 1.0) / total_frames
    variants = [
        f"z='min(zoom+{increment:.8f},{target_zoom})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",  # zoom-in, merkez
        f"z='if(eq(on,0),{target_zoom},max(zoom-{increment:.8f},1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",  # zoom-out
        f"z='min(zoom+{increment:.8f},{target_zoom})':x='(iw-iw/zoom)*on/{total_frames}':y='ih/2-(ih/zoom/2)'",  # zoom-in + sağa kayma
        f"z='min(zoom+{increment:.8f},{target_zoom})':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*on/{total_frames}'",  # zoom-in + aşağı kayma
    ]
    return random.choice(variants)


def main():
    if len(sys.argv) != 6:
        print(
            "Kullanım: assemble_video_shorts.py <thumbnail.jpg> <ses.mp3> <cikti.mp4> <music_klasoru> <music_onek>",
            file=sys.stderr,
        )
        sys.exit(1)

    image_path, audio_path, output_path, music_dir, music_prefix = sys.argv[1:6]

    duration = get_duration(audio_path)
    fps = 30
    total_frames = int(duration * fps)
    zoom_expr = build_zoom_expr(total_frames)
    music_path = pick_music(music_dir, music_prefix)

    inputs = ["-loop", "1", "-i", image_path, "-i", audio_path]
    narration_idx = 1

    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"zoompan={zoom_expr}:d={total_frames}:s=1080x1920:fps={fps}"
    )

    filter_parts = [f"[0:v]{vf}[outv]"]

    if music_path:
        music_idx = 2
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
        "-t", str(duration),
        output_path,
    ]

    subprocess.run(cmd, check=True)
    print(f"OK: {output_path} (müzik: {'var' if music_path else 'yok'})")


if __name__ == "__main__":
    main()
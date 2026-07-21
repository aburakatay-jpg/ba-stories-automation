#!/usr/bin/env python3
"""
Tek bir görsele (üretilen thumbnail) Ken Burns efekti (yavaş zoom/kaydırma)
uygulayarak dikey (9:16, 1080x1920) short videosu üretir.

Kullanım:
  python3 assemble_video_shorts.py thumbnail.jpg ses.mp3 cikti.mp4
"""
import json
import random
import subprocess
import sys


def get_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


# Birkaç farklı kamera hareketi - her üretimde rastgele biri seçilir, çeşitlilik için
ZOOM_VARIANTS = [
    "z='min(zoom+0.0012,1.4)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",   # yavaş zoom-in, merkez
    "z='if(eq(on,0),1.4,max(zoom-0.0012,1.0))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'",  # yavaş zoom-out
    "z='min(zoom+0.0010,1.3)':x='if(eq(on,0),0,x+0.5)':y='ih/2-(ih/zoom/2)'",  # zoom-in + sağa kayma
    "z='min(zoom+0.0010,1.3)':x='iw/2-(iw/zoom/2)':y='if(eq(on,0),0,y+0.5)'",  # zoom-in + aşağı kayma
]


def main():
    if len(sys.argv) != 4:
        print("Kullanım: assemble_video_shorts.py <thumbnail.jpg> <ses.mp3> <cikti.mp4>", file=sys.stderr)
        sys.exit(1)

    image_path, audio_path, output_path = sys.argv[1:4]

    duration = get_duration(audio_path)
    fps = 30
    total_frames = int(duration * fps)

    zoom_expr = random.choice(ZOOM_VARIANTS)

    vf = (
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,"
        f"zoompan={zoom_expr}:d={total_frames}:s=1080x1920:fps={fps}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-vf", vf,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(duration),
        output_path,
    ]

    subprocess.run(cmd, check=True)
    print(f"OK: {output_path}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import sys
import os
import glob
import random
import subprocess

def get_audio_duration(audio_path):
    """FFprobe kullanarak ses dosyasının tam süresini saniye cinsinden hesaplar."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Uyarı: Ses süresi okunamadı ({e})")
        return 0.0

def main():
    # Sistemin beklediği tam parametre listesi
    if len(sys.argv) < 5:
        print("Kullanım: assemble_video_shorts.py <gorsel_prefix> <ses.mp3> <cikti.mp4> <music_dir> [music_prefix]")
        sys.exit(1)

    gorsel_prefix = sys.argv[1]
    ses_path = sys.argv[2]
    cikti_path = sys.argv[3]
    music_dir = sys.argv[4]
    music_prefix = sys.argv[5] if len(sys.argv) > 5 else ""

    # Üretilen sahne görsellerini bul (örnek: output/scene_1.jpg, output/scene_2.jpg)
    search_pattern = f"{gorsel_prefix}*.jpg"
    images = sorted(glob.glob(search_pattern))
    
    if not images:
        print(f"Hata: {search_pattern} ile eşleşen sahne görseli bulunamadı.")
        sys.exit(1)

    audio_duration = get_audio_duration(ses_path)
    if audio_duration == 0.0:
        print("Hata: Ses dosyasının süresi hesaplanamadı.")
        sys.exit(1)

    # Ses süresini sahne sayısına bölerek her fotoğrafın ekranda kalma süresini belirle
    duration_per_image = audio_duration / len(images)

    # FFmpeg'in görselleri sırayla okuması için geçici bir liste dosyası oluşturuyoruz
    concat_file = "output/concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for img in images:
            safe_path = os.path.abspath(img).replace("\\", "/")
            f.write(f"file '{safe_path}'\n")
            f.write(f"duration {duration_per_image:.3f}\n")
        # FFmpeg'in son görseli atlamaması için son satırı süresiz tekrar yazıyoruz
        safe_last_path = os.path.abspath(images[-1]).replace("\\", "/")
        f.write(f"file '{safe_last_path}'\n")

    # Klasörden rastgele bir arka plan müziği seç (varsa)
    bgm_path = None
    if os.path.isdir(music_dir):
        music_files = [f for f in os.listdir(music_dir) if f.endswith(".mp3") and f.startswith(music_prefix)]
        if music_files:
            bgm_path = os.path.join(music_dir, random.choice(music_files))

    # Temel FFmpeg birleştirme komutunu inşa et
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-i", ses_path
    ]

    # Arka plan müziği varsa %10 ses seviyesine kıs ve ana sesle birleştir
    # Aynı zamanda görselleri YouTube Shorts (9:16) formatına zorla sığdır
    if bgm_path:
        cmd.extend(["-i", bgm_path])
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v];"
            "[1:a]volume=1.0[a1];"
            "[2:a]volume=0.08[a2];"
            "[a1][a2]amix=inputs=2:duration=first:dropout_transition=2[a]"
        )
        cmd.extend(["-filter_complex", filter_complex, "-map", "[v]", "-map", "[a]"])
    else:
        filter_complex = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920[v]"
        cmd.extend(["-filter_complex", filter_complex, "-map", "[v]", "-map", "1:a"])

    # Çıktı ayarları (Hızlı render, H.264 video kodeği, standart AAC ses)
    cmd.extend([
        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", # Ses bitince videoyu tam oradan kes
        cikti_path
    ])

    print("🎥 Video sahneleri, ses ve müzik birleştiriliyor...")
    subprocess.run(cmd, check=True)
    print(f"✅ Video başarıyla oluşturuldu: {cikti_path}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Ses dosyasından otomatik zaman damgalı .srt altyazı üretir.
Kurulum: pip install faster-whisper --break-system-packages

Kullanım:
  python3 generate_subtitles.py ses.mp3 altyazi.srt

Not: İlk çalıştırmada model dosyasını indirir (~500mb, "small" model).
Oracle Cloud Free Tier / Railway gibi düşük RAM'li sunucularda "tiny"
veya "base" modeline düşürmek gerekebilir.
"""
import sys
from faster_whisper import WhisperModel

MODEL_SIZE = "small"  # RAM sıkıntısı olursa: "base" veya "tiny"


def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def main():
    if len(sys.argv) != 3:
        print("Kullanım: generate_subtitles.py <ses.mp3> <cikti.srt>", file=sys.stderr)
        sys.exit(1)

    audio_path, srt_path = sys.argv[1], sys.argv[2]

    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(audio_path, language="tr", vad_filter=True)

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{format_timestamp(seg.start)} --> {format_timestamp(seg.end)}\n")
            f.write(f"{seg.text.strip()}\n\n")

    print(f"OK: {srt_path}")


if __name__ == "__main__":
    main()

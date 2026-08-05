#!/usr/bin/env python3
"""
Google Cloud Text-to-Speech API ile Türkçe WaveNet seslendirme üretir.
Edge-TTS'e göre çok daha doğal ve insan sesine yakın.

Kullanım:
  python3 generate_tts.py senaryo.txt cikti.mp3

Gerekli ortam değişkeni: GOOGLE_TTS_API_KEY
"""
import base64
import json
import os
import sys

import requests


def main():
    if len(sys.argv) != 3:
        print("Kullanım: generate_tts.py <metin_dosyasi> <cikti.mp3>", file=sys.stderr)
        sys.exit(1)

    text_path, output_path = sys.argv[1], sys.argv[2]

    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("Hata: metin dosyası boş", file=sys.stderr)
        sys.exit(1)

    # Google Cloud TTS maksimum 5000 karakter kabul ediyor
    # Uzun metinleri parçalara böl, birleştir
    chunks = []
    while len(text) > 4800:
        # En yakın cümle sonunda böl
        split_at = text[:4800].rfind(". ")
        if split_at == -1:
            split_at = 4800
        chunks.append(text[:split_at + 1])
        text = text[split_at + 1:].strip()
    chunks.append(text)

    api_key = os.environ["GOOGLE_TTS_API_KEY"]
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"

    audio_parts = []
    for chunk in chunks:
        payload = {
            "input": {"text": chunk},
            "voice": {
                "languageCode": "tr-TR",
                "name": "tr-TR-Wavenet-E",  # Kadın ses, en doğal Türkçe WaveNet
                # Alternatifler: tr-TR-Wavenet-D (erkek)
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 0.97,   # hafif yavaşlatılmış, doğal tempo
                "pitch": -1.0,          # hafif derin ton, gerilim atmosferi için
                "volumeGainDb": 1.0,
            },
        }

        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()

        audio_content = resp.json()["audioContent"]
        audio_parts.append(base64.b64decode(audio_content))

    # Parçaları birleştir
    with open(output_path, "wb") as f:
        for part in audio_parts:
            f.write(part)

    print(f"OK: {output_path} ({len(chunks)} parça)")


if __name__ == "__main__":
    main()

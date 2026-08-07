#!/usr/bin/env python3
"""
Azure Cognitive Services Neural TTS ile Türkçe seslendirme üretir.
Anlatıcı cinsiyetine göre otomatik ses seçimi yapar.

Kullanım:
  python3 generate_tts.py senaryo.txt cikti.mp3 [kadin|erkek]

Gerekli ortam değişkenleri: AZURE_TTS_KEY, AZURE_TTS_REGION
"""
import os
import sys
import requests

VOICES = {
    "kadin": {
        "name": "tr-TR-EmelNeural",
        "style": "narrating-story",  # hikaye anlatım tonu
    },
    "erkek": {
        "name": "tr-TR-AhmetNeural",
        "style": "narrating-story",
    },
}

DEFAULT_VOICE = "kadin"


def synthesize(text, voice_name, region, key):
    """Azure TTS API'ye istek atar, MP3 bytes döndürür."""
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-48khz-192kbitrate-mono-mp3",
    }
    ssml = f"""<speak version='1.0' xml:lang='tr-TR'>
  <voice name='{voice_name}'>
    <prosody rate='-5%' pitch='-2%'>
      {text}
    </prosody>
  </voice>
</speak>"""

    resp = requests.post(url, headers=headers, data=ssml.encode("utf-8"), timeout=60)
    resp.raise_for_status()
    return resp.content


def main():
    if len(sys.argv) < 3:
        print("Kullanım: generate_tts.py <metin_dosyasi> <cikti.mp3> [kadin|erkek]", file=sys.stderr)
        sys.exit(1)

    text_path = sys.argv[1]
    output_path = sys.argv[2]
    anlatici = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_VOICE

    if anlatici not in VOICES:
        anlatici = DEFAULT_VOICE

    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("Hata: metin dosyası boş", file=sys.stderr)
        sys.exit(1)

    key = os.environ["AZURE_TTS_KEY"]
    region = os.environ.get("AZURE_TTS_REGION", "westeurope")
    voice_name = VOICES[anlatici]["name"]

    # Azure TTS tek istekte maksimum ~5000 karakter işleyebilir
    # Uzun metinleri paragraflara göre böl
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) > 4500:
            if current:
                chunks.append(current)
            current = para
        else:
            current = (current + "\n\n" + para).strip() if current else para
    if current:
        chunks.append(current)

    audio_parts = []
    for i, chunk in enumerate(chunks):
        print(f"Ses üretiliyor: parça {i+1}/{len(chunks)} ({anlatici}, {voice_name})...")
        audio = synthesize(chunk, voice_name, region, key)
        audio_parts.append(audio)

    with open(output_path, "wb") as f:
        for part in audio_parts:
            f.write(part)

    print(f"OK: {output_path} ({len(chunks)} parça, anlatıcı: {anlatici})")


if __name__ == "__main__":
    main()

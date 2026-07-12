#!/usr/bin/env python3
"""
Ücretsiz Türkçe seslendirme - Microsoft Edge-TTS kullanır.
Kurulum: pip install edge-tts --break-system-packages

Kullanım:
  python3 generate_tts.py senaryo.txt cikti.mp3

n8n'de "Execute Command" node'u ile çağrılır.
"""
import asyncio
import sys
import edge_tts

# Denenebilecek diğer Türkçe sesler: tr-TR-EmelNeural (kadın), tr-TR-AhmetNeural (erkek)
VOICE = "tr-TR-AhmetNeural"
RATE = "-8%"   # korku/gerilim anlatımı için biraz yavaşlatılmış tempo
PITCH = "-2Hz" # hafif daha derin ton


async def main():
    if len(sys.argv) != 3:
        print("Kullanım: generate_tts.py <metin_dosyasi> <cikti.mp3>", file=sys.stderr)
        sys.exit(1)

    text_path, output_path = sys.argv[1], sys.argv[2]
    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("Hata: metin dosyası boş", file=sys.stderr)
        sys.exit(1)

    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(output_path)
    print(f"OK: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())

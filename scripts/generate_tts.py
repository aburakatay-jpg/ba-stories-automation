#!/usr/bin/env python3
import sys
import os
import asyncio
import requests
import xml.etree.ElementTree as ET

def generate_azure_tts(text, output_file, voice_name="tr-TR-AhmetNeural"):
    """GitHub Secrets'taki resmi Azure Speech API'yi kullanır (403 vermez)."""
    key = os.environ.get("AZURE_TTS_KEY")
    region = os.environ.get("AZURE_TTS_REGION", "eastus")

    if not key:
        return False

    print(f"🎙️ Azure Speech ile seslendiriliyor ({voice_name})...")
    url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
        "User-Agent": "BAShortsAutomation"
    }

    # Metni XML güvenli hale getir
    safe_text = (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
    )

    ssml = f"""<speak version='1.0' xml:lang='tr-TR'>
        <voice xml:lang='tr-TR' name='{voice_name}'>
            <prosody rate='0%'>{safe_text}</prosody>
        </voice>
    </speak>"""

    try:
        resp = requests.post(url, headers=headers, data=ssml.encode("utf-8"), timeout=60)
        if resp.ok and len(resp.content) > 5000:
            with open(output_file, "wb") as f:
                f.write(resp.content)
            print(f"✅ Azure TTS başarılı: {output_file}")
            return True
        else:
            print(f"⚠️ Azure TTS yanıt kodu: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"⚠️ Azure TTS hatası: {e}")

    return False

async def generate_edge_tts(text, output_file, voice_name="tr-TR-AhmetNeural"):
    """Yedek: edge-tts"""
    try:
        import edge_tts
        print(f"🗣️ Edge-TTS deneniyor: {voice_name}")
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(output_file)
        if os.path.exists(output_file) and os.path.getsize(output_file) > 5000:
            print(f"✅ Edge-TTS başarılı: {output_file}")
            return True
    except Exception as e:
        print(f"⚠️ Edge-TTS hatası: {e}")
    return False

def main():
    if len(sys.argv) < 3:
        print("Kullanım: generate_tts.py <senaryo.txt> <output.mp3>")
        sys.exit(1)

    input_txt = sys.argv[1]
    output_mp3 = sys.argv[2]

    with open(input_txt, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        print("Hata: Senaryo metni boş!")
        sys.exit(1)

    # 1. Deneme: Resmi Azure TTS (AhmetNeural)
    success = generate_azure_tts(text, output_mp3, "tr-TR-AhmetNeural")

    # 2. Deneme: Alternatif kadın ses (EmelNeural)
    if not success:
        success = generate_azure_tts(text, output_mp3, "tr-TR-EmelNeural")

    # 3. Deneme: edge-tts fallback
    if not success:
        success = asyncio.run(generate_edge_tts(text, output_mp3, "tr-TR-AhmetNeural"))

    if not success:
        print("❌ Hiçbir TTS yöntemiyle ses üretilemedi!")
        sys.exit(1)

if __name__ == "__main__":
    main()

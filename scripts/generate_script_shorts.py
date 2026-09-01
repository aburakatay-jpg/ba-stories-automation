#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

def call_gemini(prompt, max_retries=5):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY bulunamadı!")
        
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 2048
        }
    }

    for attempt in range(max_retries):
        resp = requests.post(f"{API_URL}?key={api_key}", json=payload, timeout=120)
        if resp.status_code in [429, 503]:
            time.sleep(30)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            raise RuntimeError("API yanıtı okunamadı.")
            
    raise RuntimeError("Gemini API'ye ulaşılamadı.")

def generate_dynamic_context():
    mekanlar = [
        "terk edilmiş eski bir lunapark",
        "gece yarısı duran ıssız bir metro vagonu",
        "kapısı kilitli eski bir çatı katı",
        "orman yolunda terkedilmiş bir araba",
        "gece yarısı sinyal veren boş bir radyo kulesi"
    ]
    nesneler = ["eski bir kasetçalar", "üzeri çizilmiş bir ayna", "çalan ankesörlü telefon", "eski bir oyuncak bebek"]
    kavramlar = ["zaman kayması", "paralel evren gerilimi", "görünmeyen varlıklar", "psikolojik kabus"]
    
    mekan = random.choice(mekanlar)
    nesne = random.choice(nesneler)
    kavram = random.choice(kavramlar)
    
    return {
        "tema": f"{kavram}, Odak: {nesne}",
        "mekan": mekan,
        "playlist_id": "",
        "anlatici": "erkek",
        "prompt_context": f"Mekan: {mekan}. Odak Nesne: {nesne}. Olay: {kavram}."
    }

def parse_response(raw_text):
    baslik = "Karanlığın İçindeki Ses"
    senaryo = ""
    aciklama = "Karanlık bir hikaye... #shorts #korku #hikaye"

    if "===BASLIK===" in raw_text and "===SENARYO===" in raw_text:
        parts = raw_text.split("===BASLIK===")[1]
        baslik_part, rest = parts.split("===SENARYO===")
        baslik = baslik_part.strip().replace('"', '').replace('*', '')

        if "===ACIKLAMA===" in rest:
            senaryo_part, aciklama_part = rest.split("===ACIKLAMA===")
            senaryo = senaryo_part.strip()
            aciklama = aciklama_part.strip()
        else:
            senaryo = rest.strip()
    else:
        senaryo = raw_text.strip()

    lines = [l.strip() for l in senaryo.split('\n') if l.strip()]
    senaryo = " ".join(lines).replace('"', '').replace('*', '')

    return baslik, senaryo, aciklama

def ensure_script_length(senaryo, context):
    """Senaryonun en az 115 kelime (45-50 saniye TTS) olmasını garanti eder."""
    word_count = len(senaryo.split())
    if word_count >= 115:
        return senaryo

    print(f"⚠️ Senaryo kısa kaldı ({word_count} kelime). Genişletiliyor...")
    expand_prompt = (
        f"Aşağıdaki YouTube Shorts korku senaryosu çok kısa ve seslendirmesi 20 saniyede bitiyor. "
        f"Lütfen hikayenin atmosferini, duyulan sesleri, karakterin korkusunu ve detayları artırarak "
        f"bu hikayeyi EN AZ 120-140 KELİME olacak şekilde baştan sona tek parça olarak tekrar yaz.\n\n"
        f"Mevcut Metin:\n{senaryo}\n\n"
        f"KURAL: Sadece genişletilmiş hikaye metnini ver. Başlık veya açıklama yazma."
    )
    expanded = call_gemini(expand_prompt)
    expanded_lines = [l.strip() for l in expanded.split('\n') if l.strip()]
    cleaned_expanded = " ".join(expanded_lines).replace('"', '').replace('*', '')
    
    # Model genişletmeye rağmen kısa keserse yedek detay cümlesi ekle
    if len(cleaned_expanded.split()) < 115:
        cleaned_expanded += " Kalp atışlarım kulaklarımda yankılanırken o karanlık odanın kapısı yavaşça gıcırdadı. Geriye doğru bir adım atmak istedim ama ayaklarım yere çivilenmiş gibiydi. Arkamda hissettiğim o soğuk nefes, buranın artık benim mezarım olduğunu fısıldıyordu."
        
    return cleaned_expanded

def main():
    context = generate_dynamic_context()
    
    prompt = (
        f"Sen Türkçe YouTube Shorts korku kanalı için seslendirme metni yazan profesyonel bir yazarsın.\n"
        f"KONU: {context['prompt_context']}\n\n"
        f"ÖNEMLİ KURAL: Senaryo seslendirildiğinde tam 45-50 saniye sürmelidir. Bu yüzden hikaye EN AZ 3 paragraf ve 120-140 kelime uzunluğunda olmalıdır. Kısa ve özet metinler geçersizdir.\n\n"
        f"Lütfen yanıtını AYNEN aşağıdaki etiketlerle formatla:\n\n"
        f"===BASLIK===\n"
        f"3-5 kelimelik çarpıcı Türkçe başlık\n"
        f"===SENARYO===\n"
        f"Detaylı, gerilimli, birinci ağızdan anlatılan tam 120-140 kelimelik hikaye metni.\n"
        f"===ACIKLAMA===\n"
        f"Kısa video açıklaması ve #shorts #korku #hikaye etiketleri\n"
    )

    raw_text = call_gemini(prompt)
    baslik, senaryo, aciklama = parse_response(raw_text)

    # Süre / kelime sayısı kontrolü
    final_senaryo = ensure_script_length(senaryo, context)
    total_words = len(final_senaryo.split())

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(final_senaryo)
        
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(baslik)
        
    with open("output/aciklama.txt", "w", encoding="utf-8") as f:
        f.write(aciklama)
        
    tema_ciktisi = {
        "tema": context["tema"],
        "mekan": context["mekan"],
        "anlatici": context["anlatici"]
    }
    with open("output/tema.json", "w", encoding="utf-8") as f:
        json.dump(tema_ciktisi, f, ensure_ascii=False)
        
    with open("output/playlist_id.txt", "w", encoding="utf-8") as f:
        f.write(context.get("playlist_id", ""))

    print(f"✅ Senaryo tamamlandı: {total_words} kelime (Tahmini TTS süresi: {total_words/2.5:.1f} sn) | Başlık: {baslik}")

if __name__ == "__main__":
    main()

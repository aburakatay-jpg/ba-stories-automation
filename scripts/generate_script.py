#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

def call_gemini(prompt, temperature=0.8, max_tokens=4096, max_retries=5):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY bulunamadı!")
        
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }

    for attempt in range(max_retries):
        resp = requests.post(f"{API_URL}?key={api_key}", json=payload, timeout=180)
        if resp.status_code in [429, 503]:
            time.sleep(30)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            raise RuntimeError("API geçerli bir metin döndürmedi.")
            
    raise RuntimeError("Gemini API'ye ulaşılamadı.")

def generate_dynamic_context():
    mekanlar = [
        "Anadolu'da terk edilmiş dağ köyü",
        "Karadeniz yaylasında sisli bir orman evi",
        "Eski bir Osmanlı hanı kalıntısı",
        "Kapanmış bir linyit madeni ocağı",
        "Gece yarısı tenha bir taşra tren istasyonu"
    ]
    nesneler = ["üzeri mühürlü eski sandık", "kayıp bir günlük", "antika cep saati", "eski aile fotoğrafı"]
    kavramlar = ["eski lanetler", "cin ve doğaüstü varlık rivayetleri", "köye çöken tekinsiz sis", "unutulmuş sırlar"]
    
    mekan = random.choice(mekanlar)
    nesne = random.choice(nesneler)
    kavram = random.choice(kavramlar)
    
    return {
        "tema": f"{kavram}, Odak: {nesne}",
        "mekan": mekan,
        "playlist_id": "",
        "anlatici": "erkek",
        "prompt_context": f"Mekan: {mekan}. Odak Nesne: {nesne}. Olay/Tema: {kavram}."
    }

def parse_long_response(raw_text):
    baslik = ""
    senaryo = ""
    aciklama = ""

    if "===BASLIK===" in raw_text and "===SENARYO===" in raw_text:
        parts = raw_text.split("===BASLIK===")[1]
        baslik_part, rest = parts.split("===SENARYO===")
        baslik = baslik_part.strip()

        if "===ACIKLAMA===" in rest:
            senaryo_part, aciklama_part = rest.split("===ACIKLAMA===")
            senaryo = senaryo_part.strip()
            aciklama = aciklama_part.strip()
        else:
            senaryo = rest.strip()
    else:
        # Etiketler gelmediyse temiz ayıkla
        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        if lines:
            baslik = lines[0]
            senaryo = "\n\n".join(lines[1:])
        else:
            baslik = "Anadolu'da Yaşanan Gizemli Gece"
            senaryo = raw_text.strip()

    # Başlık temizliği (Tırnak, yıldız, parantez artıklarını kaldır)
    baslik = baslik.replace('"', '').replace('*', '').replace('#', '').strip()
    baslik_lines = [l.strip() for l in baslik.split('\n') if l.strip()]
    if baslik_lines:
        baslik = baslik_lines[0]
        
    for prefix in ["Başlık:", "İşte Başlık:", "Video Başlığı:"]:
        if baslik.lower().startswith(prefix.lower()):
            baslik = baslik[len(prefix):].strip()

    # Eğer model yine 'Iss' gibi anlamsız 5 karakterden kısa bir şey verirse kurtar
    if len(baslik) < 8:
        baslik = "Karanlık Köyün Derinliklerinde Yaşanan Korkunç Olay"

    # Senaryo temizliği
    senaryo = senaryo.replace('*', '').strip()

    if not aciklama:
        aciklama = f"{baslik}\n\nBu videoda yaşanan esrarengiz olayları dinleyeceksiniz. İyi seyirler.\n\n#korkuhikayeleri #korku #paranormal"

    return baslik, senaryo, aciklama

def main():
    context = generate_dynamic_context()
    
    prompt = (
        f"Sen Türkçe korku hikayeleri anlatan popüler bir YouTube kanalı için 8-10 dakikalık uzun video içeriği üreten profesyonel bir yazarsın.\n"
        f"KONU VE BAĞLAM: {context['prompt_context']}\n\n"
        f"KURALLAR:\n"
        f"1. Başlık YouTube'da doğrudan merak uyandıran, 6-10 kelimelik eksiksiz bir Türkçe cümle/ifade olmalıdır (Örn: 'Anadolu'da Issız Bir Köyde Gece Nöbetinde Yaşananlar'). ASLA yarım kelime bırakma.\n"
        f"2. Senaryo en az 1100-1400 kelime uzunluğunda, sürükleyici, giriş-gelişme-sonuç yapısına sahip olmalıdır.\n\n"
        f"Lütfen yanıtını AYNEN şu etiketlerle formatla:\n\n"
        f"===BASLIK===\n"
        f"Tam ve eksiksiz video başlığı\n"
        f"===SENARYO===\n"
        f"Hikaye metni\n"
        f"===ACIKLAMA===\n"
        f"Video açıklaması ve etiketler\n"
    )

    raw_text = call_gemini(prompt, temperature=0.85, max_tokens=4096)
    baslik, senaryo, aciklama = parse_long_response(raw_text)

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(senaryo)
        
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

    print(f"✅ Uzun Video Hazır: Başlık -> '{baslik}' | Kelime Sayısı -> {len(senaryo.split())}")

if __name__ == "__main__":
    main()

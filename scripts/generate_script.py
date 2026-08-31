#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent"

def clean_ai_text(text):
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        lower_line = line.lower()
        if lower_line.startswith(("işte", "tabii", "senaryo:", "başlık:", "tamam", "elbette", "uzun senaryo")):
            continue
        if line.startswith("```"):
            continue
        if line:
            cleaned.append(line.replace('*', '').replace('"', '').replace('#', ''))
    return "\n".join(cleaned).strip()

def call_gemini(prompt, temperature=0.9, max_tokens=4000, max_retries=5):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY bulunamadı!")
        
    for attempt in range(max_retries):
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                ]
            },
            timeout=120,
        )
        if resp.status_code in [429, 503]:
            time.sleep(60)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code} - {resp.text}")
        
        data = resp.json()
        if "candidates" not in data or not data["candidates"]:
            print(f"DEBUG: Gelen cevapta candidate yok: {data}")
            raise RuntimeError("API cevabında candidate bulunamadı.")
            
        candidate = data["candidates"][0]
        if "content" not in candidate or "parts" not in candidate["content"]:
            print(f"DEBUG: İçerik yapısı hatalı: {candidate}")
            raise RuntimeError("API cevabında content veya parts bulunamadı.")

        raw_text = candidate["content"]["parts"][0].get("text", "")
        return clean_ai_text(raw_text)
    raise RuntimeError("Gemini API'ye ulaşılamadı")

def get_series_info():
    seri_path = os.path.join(os.path.dirname(__file__), "seri_bilgisi.json")
    if not os.path.exists(seri_path):
        default_series = {
            "karanlik_arsivler": {"ad": "Karanlık Arşivler", "mekan": "Terk Edilmiş Devlet Arşivi", "sayac": 0},
            "deniz_feneri": {"ad": "Yalnız Fener", "mekan": "Okyanus Ortasında Bir Deniz Feneri", "sayac": 0},
            "kayip_kasetler": {"ad": "Kayıp Kasetler", "mekan": "Eski Bir Radyo İstasyonu", "sayac": 0}
        }
        with open(seri_path, "w", encoding="utf-8") as f:
            json.dump(default_series, f, ensure_ascii=False, indent=2)
        return default_series, seri_path
    
    with open(seri_path, "r", encoding="utf-8") as f:
        return json.load(f), seri_path

def generate_dynamic_context():
    series_data, seri_path = get_series_info()
    
    if random.random() < 0.30:
        secilen_seri_key = random.choice(list(series_data.keys()))
        series_data[secilen_seri_key]["sayac"] += 1
        
        with open(seri_path, "w", encoding="utf-8") as f:
            json.dump(series_data, f, ensure_ascii=False, indent=2)
            
        ad = series_data[secilen_seri_key].get("ad", "Gizemli Hikaye")
        bolum = series_data[secilen_seri_key].get("sayac", 1)
        mekan = series_data[secilen_seri_key].get("mekan", "Karanlık ve tekinsiz bir yer")
        playlist_id = series_data[secilen_seri_key].get("playlist_id", "")
        
        return {
            "is_series": True,
            "tema": ad,
            "mekan": mekan,
            "bolum_no": bolum,
            "playlist_id": playlist_id,
            "anlatici": random.choice(["erkek", "kadin"]),
            "prompt_context": f"Bu hikaye '{ad}' isimli korku serisinin {bolum}. bölümüdür. Ana karakterimiz bu serinin odak kişisidir."
        }
    else:
        mekanlar = ["ıssız bir kargo gemisi", "karlar altında kalmış bir dağ oteli", "eski bir akıl hastanesi kalıntısı", "gece yarısı boş bir otoyol dinlenme tesisi", "derin bir orman kulübesi", "terk edilmiş bir lunapark"]
        nesneler = ["isimsiz bir kaset", "gece yarısı çalan ankesörlü telefon", "duvardaki tuhaf çizimler", "eski bir telsizden gelen yardım çağrısı", "kendiliğinden açılan güvenlik kameraları"]
        kavramlar = ["psikolojik çöküş ve izolasyon", "doğaüstü varlıklar", "açıklanamayan zaman kaymaları", "klostrofobik gerilim", "paralel gerçeklik"]
        
        mekan = random.choice(mekanlar)
        nesne = random.choice(nesneler)
        kavram = random.choice(kavramlar)
        
        tema_adi = f"{kavram}, Odak: {nesne}"
        
        return {
            "is_series": False,
            "tema": tema_adi,
            "mekan": mekan,
            "playlist_id": "",
            "anlatici": random.choice(["erkek", "kadin"]),
            "prompt_context": f"Mekan: {mekan}. Odak Nesne: {nesne}. Tema: {kavram}."
        }

def write_script(context):
    prompt = (
        f"Sen Türkçe bir korku YouTube kanalı için senaryo yazarısın. "
        f"Lütfen en az 1000 - 1200 kelime uzunluğunda, atmosferi ilmek ilmek işleyen, "
        f"birinci ağızdan ('ben') anlatılan gerçekçi bir olay yaz.\n\n"
        f"BAĞLAM: {context['prompt_context']}\n\n"
        f"YAPI VE KURALLAR:\n"
        f"1. GİRİŞ: Direkt hikayeye başla. Karakterin yalnızlığını ve mekanı detaylı tasvir et.\n"
        f"2. GELİŞME: Olayları yavaş yavaş tırmandır, gizemi derinleştir.\n"
        f"3. FİNAL (ÇOK ÖNEMLİ): Hikayeyi ASLA yarım veya açık uçlu bırakma. Karakterin başına gelenleri, yüzleştiği dehşeti net ve sarsıcı bir sonla tamamen bağla.\n"
        f"4. Sadece senaryo metnini ver, başka hiçbir açıklama yazma."
    )
    return call_gemini(prompt, temperature=0.9, max_tokens=4000)

def write_title(context):
    prompt = (
        f"Aşağıdaki konsepte uygun, YouTube için 5-8 kelimelik, ilgi çekici bir korku videosu başlığı yaz.\n"
        f"Konsept: {context['prompt_context']}\n"
        f"Lütfen sadece başlığı ver, ekstra hiçbir açıklama veya tırnak işareti ekleme."
    )
    title = call_gemini(prompt, temperature=0.8, max_tokens=150)
    
    clean_title = title.replace('"', '').replace('*', '').replace("'", "").strip()
    if clean_title.lower().startswith("başlık:"):
        clean_title = clean_title[7:].strip()
    
    if context["is_series"]:
        return f"{clean_title} | {context['tema']} #{context['bolum_no']}"
    
    return clean_title

def write_description(context, title):
    prompt = (
        f"YouTube korku videosu için SEO uyumlu bir açıklama yaz. "
        f"İlk paragraf merak uyandıran bir özet olsun. Altına ilgili Türkçe hashtag'ler ekle. "
        f"Sadece açıklamayı döndür.\nBaşlık: {title}\nBağlam: {context['prompt_context']}"
    )
    return call_gemini(prompt, temperature=0.7, max_tokens=400)

def main():
    context = generate_dynamic_context()
    print(f"Senaryo üretiliyor... (Tema: {context['tema']})")
    
    script = write_script(context)
    time.sleep(2)
    title = write_title(context)
    time.sleep(2)
    description = write_description(context, title)

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(script)
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(title)
    with open("output/aciklama.txt", "w", encoding="utf-8") as f:
        f.write(description)
        
    tema_ciktisi = {
        "tema": context["tema"], 
        "mekan": context["mekan"],
        "anlatici": context["anlatici"]
    }
    with open("output/tema.json", "w", encoding="utf-8") as f:
        json.dump(tema_ciktisi, f, ensure_ascii=False)
        
    with open("output/playlist_id.txt", "w", encoding="utf-8") as f:
        f.write(context.get("playlist_id", ""))

    print(f"✅ Üretim tamamlandı (Uzun Video). Uzunluk: {len(script)} karakter. Başlık: '{title}'")

if __name__ == "__main__":
    main()


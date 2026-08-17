#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"

def clean_ai_text(text):
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        line = line.strip()
        lower_line = line.lower()
        if lower_line.startswith(("işte", "tabii", "senaryo:", "başlık:", "tamam", "elbette", "kısa senaryo")):
            continue
        if line.startswith("```"):
            continue
        if line:
            cleaned.append(line.replace('*', '').replace('"', '').replace('#', ''))
    return "\n".join(cleaned).strip()

def call_gemini(prompt, temperature=0.9, max_tokens=500, max_retries=5):
    api_key = os.environ["GEMINI_API_KEY"]
    for attempt in range(max_retries):
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
            },
            timeout=60,
        )
        if resp.status_code == 429:
            time.sleep(30)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code}")
        
        raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return clean_ai_text(raw_text)
    raise RuntimeError("Gemini API'ye ulaşılamadı")

def get_series_info():
    """Mikro serileri yönetir ve sayacı tutar."""
    seri_path = os.path.join(os.path.dirname(__file__), "seri_bilgisi_shorts.json")
    if not os.path.exists(seri_path):
        default_series = {
            "gece_taksicisi": {"ad": "Gece Taksicisi", "mekan": "Taksi İçi / Karanlık Sokaklar", "sayac": 0},
            "morg_bekcisi": {"ad": "Morg Nöbeti", "mekan": "Eski Hastane Morgu", "sayac": 0},
            "kurye": {"ad": "Girilmez Sokaklar", "mekan": "Issız Apartman Koridorları", "sayac": 0}
        }
        with open(seri_path, "w", encoding="utf-8") as f:
            json.dump(default_series, f, ensure_ascii=False, indent=2)
        return default_series, seri_path
    
    with open(seri_path, "r", encoding="utf-8") as f:
        return json.load(f), seri_path

def generate_dynamic_context():
    """%30 ihtimalle Seri, %70 ihtimalle Tam Dinamik Tema üretir."""
    series_data, seri_path = get_series_info()
    
    # %30 ihtimalle bir seriye devam et
    if random.random() < 0.30:
        secilen_seri_key = random.choice(list(series_data.keys()))
        series_data[secilen_seri_key]["sayac"] += 1
        
        # Güncel sayacı kaydet
        with open(seri_path, "w", encoding="utf-8") as f:
            json.dump(series_data, f, ensure_ascii=False, indent=2)
            
        ad = series_data[secilen_seri_key]["ad"]
        bolum = series_data[secilen_seri_key]["sayac"]
        mekan = series_data[secilen_seri_key]["mekan"]
        
        return {
            "is_series": True,
            "tema": ad,
            "mekan": mekan,
            "bolum_no": bolum,
            "prompt_context": f"Bu hikaye '{ad}' isimli mikro korku serisinin {bolum}. bölümüdür. Ana karakterimiz bu serinin odak kişisidir. Sadece bu bölüme ait, tek bir spesifik ve ürkütücü olayı anlat."
        }
    else:
        # %70 ihtimalle tamamen dinamik ve rastgele bir tema üret
        mekanlar = ["eski bir antika dükkanı", "gece yarısı boş bir metrobüs", "akıllı ev sistemi olan modern bir daire", "otoyol kenarı izbe bir benzinlik", "karanlık bir yeraltı otoparkı", "havalandırma boşluğu", "otel odası"]
        nesneler = ["bozuk bir bebek telsizi", "ikinci el bir akıllı telefon", "dikiz aynası", "eski bir polaroid fotoğraf makinesi", "radyo frekansı", "güvenlik kamerası ekranı"]
        kavramlar = ["teknolojik korku (digital horror)", "zaman döngüsü (loop)", "görünmeyen izleyici", "psikolojik gerilim ve paranoya", "doppelgänger (ikiz/kötü kopya)"]
        
        mekan = random.choice(mekanlar)
        nesne = random.choice(nesneler)
        kavram = random.choice(kavramlar)
        
        tema_adi = f"{kavram}, Odak: {nesne}"
        
        return {
            "is_series": False,
            "tema": tema_adi,
            "mekan": mekan,
            "prompt_context": f"Mekan: {mekan}. Odak Nesne/Durum: {nesne}. Hikayenin Alt Türü: {kavram}. Bu unsurları kullanarak tamamen eşsiz ve beklenmedik bir kurgu yarat."
        }

def write_script(context):
    prompt = (
        f"Sen Türkçe bir korku YouTube Shorts kanalı için senaryo yazarısın. "
        f"Sanki forumda birinci ağızdan gerçek yaşanmış gibi anlatılan, çok kısa ve çarpıcı bir korku anısı yaz.\n"
        f"BAĞLAM VE KONU: {context['prompt_context']}\n"
        f"UZUNLUK ZORUNLU: 150-200 kelime.\n"
        f"İlk cümle anında kanca atmalı. KESİNLİKLE 'İşte senaryo' gibi cümlelerle başlama. Direkt hikayeye gir.\n"
        f"Anlatıcı ASLA kendi adını söylemesin, birinci ağızdan ('ben') anlatsın.\n"
        f"DİL KURALI: SADECE düzgün Türkçe olacak. Sadece senaryo metnini döndür."
    )
    return call_gemini(prompt, temperature=0.95, max_tokens=600)

def write_title(context):
    prompt = (
        f"YouTube Shorts korku videosu için en fazla 8 kelimelik, merak uyandıran bir Türkçe başlık yaz.\n"
        f"İçerik Bağlamı: {context['prompt_context']}\n"
        f"Sadece başlığı döndür."
    )
    title = call_gemini(prompt, temperature=0.8, max_tokens=40)
    
    # Eğer seriyse, başlığın sonuna seri adını ve bölümünü ekle
    if context["is_series"]:
        clean_title = title.replace('"', '').replace("'", "").replace('#shorts', '').strip()
        return f"{clean_title} | {context['tema']} #{context['bolum_no']}"
    
    return title

def write_description(context, title):
    prompt = (
        f"YouTube korku videosu için SEO uyumlu bir açıklama yaz. 2-3 cümlelik merak uyandıran bir özet ve "
        f"aşağıya ilgili Türkçe hashtag'ler (en az 8 tane) ekle. Sadece açıklamayı döndür.\n"
        f"Başlık: {title}\nBağlam: {context['prompt_context']}"
    )
    return call_gemini(prompt, temperature=0.7, max_tokens=300)

def write_cta():
    return call_gemini("Türkçe korku Shorts videosu için 2 cümlelik, yoruma ve abone olmaya davet eden doğal bir kapanış metni yaz. Sadece metni döndür.", temperature=0.8, max_tokens=150)

def main():
    context = generate_dynamic_context()
    script = write_script(context)

    time.sleep(2)
    cta = write_cta()
    script = script + "\n\n" + cta

    time.sleep(2)
    title = write_title(context)
    title = title.replace('"', '').replace("'", "")

    time.sleep(2)
    description = write_description(context, title)

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(script)
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(title)
    with open("output/aciklama.txt", "w", encoding="utf-8") as f:
        f.write(description)
        
    # Görüntü üreticinin (generate_scene_images.py) kullanması için temayı JSON olarak kaydet
    tema_ciktisi = {"tema": context["tema"], "mekan": context["mekan"]}
    with open("output/tema.json", "w", encoding="utf-8") as f:
        json.dump(tema_ciktisi, f, ensure_ascii=False)
        
    with open("output/playlist_id.txt", "w", encoding="utf-8") as f:
        f.write("")

    print(f"OK: Üretim tamamlandı. Seri mi?: {context['is_series']} — '{title}'")

if __name__ == "__main__":
    main()

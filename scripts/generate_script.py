#!/usr/bin/env python3
import json
import os
import random
import time
import requests

os.makedirs("output", exist_ok=True)
# Uzun metinler ve hikaye kurgusu için en yetenekli modellerden gemini-1.5-flash kullanıyoruz
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

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
        raise ValueError("GEMINI_API_KEY bulunamadı! Lütfen GitHub workflow dosyasını kontrol et.")
        
    for attempt in range(max_retries):
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
            },
            timeout=120, # Uzun metin üretimi API tarafında zaman alabilir
        )
        if resp.status_code == 429:
            time.sleep(30)
            continue
        if not resp.ok:
            raise RuntimeError(f"Gemini API hatası: {resp.status_code} - {resp.text}")
        
        raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return clean_ai_text(raw_text)
    raise RuntimeError("Gemini API'ye ulaşılamadı")

def get_series_info():
    seri_path = os.path.join(os.path.dirname(__file__), "seri_bilgisi.json")
    if not os.path.exists(seri_path):
        # Uzun formata (Yatay Video) uygun mikro seriler
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
    
    # %30 ihtimalle bir seriye devam et
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
            "prompt_context": f"Bu hikaye '{ad}' isimli korku serisinin {bolum}. bölümüdür. Ana karakterimiz bu serinin odak kişisidir. Yaklaşık 10-12 dakikalık bir okuma süresi için detaylı, sürükleyici ve yavaş yavaş gerilimi tırmandıran bir olay örgüsü yaz."
        }
    else:
        # %70 ihtimalle rastgele uzun metraj korku kurgusu
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
            "prompt_context": f"Mekan: {mekan}. Odak Nesne/Durum: {nesne}. Hikayenin Alt Türü: {kavram}. Bu unsurları kullanarak detaylı tasvirler içeren, karakterin psikolojisini yansıtan ve gerilimi adım adım tırmandıran uzun ve eşsiz bir kurgu yarat."
        }

def write_script(context):
    prompt = (
        f"Sen Türkçe bir korku YouTube kanalı için senaryo yazarısın. "
        f"Bu video UZUN FORMATLI bir videodur (yaklaşık 10-12 dakika seslendirme süresi hedefleniyor). "
        f"Lütfen en az 1000 - 1200 kelime uzunluğunda, çok detaylı, atmosferi ilmek ilmek işleyen, "
        f"sanki bir forumda veya Reddit'te birinci ağızdan ('ben') anlatılan gerçek bir olay gibi yaz.\n\n"
        f"BAĞLAM VE KONU: {context['prompt_context']}\n\n"
        f"KURALLAR:\n"
        f"1. Asla 'İşte senaryo' gibi girişler yapma. Direkt hikayeye, bulunduğun mekanı ve durumu tasvir ederek başla.\n"
        f"2. Olayları hemen oldurma. İlk birkaç paragrafta karakterin rutinini, yalnızlığını ve mekanın ürkütücülüğünü anlat.\n"
        f"3. Gerilimi yavaş yavaş tırmandır, gizemi son anlara kadar koru ve çarpıcı bir final yap.\n"
        f"4. SADECE düzgün Türkçe kullan ve sadece senaryo metnini döndür."
    )
    return call_gemini(prompt, temperature=0.9, max_tokens=4000)

def write_title(context):
    prompt = (
        f"YouTube uzun korku videosu için en fazla 8 kelimelik, merak uyandıran, tıklamaya teşvik eden (CTR yüksek) bir Türkçe başlık yaz.\n"
        f"İçerik Bağlamı: {context['prompt_context']}\n"
        f"Sadece başlığı döndür."
    )
    title = call_gemini(prompt, temperature=0.8, max_tokens=50)
    
    if context["is_series"]:
        clean_title = title.replace('"', '').replace("'", "").strip()
        return f"{clean_title} | {context['tema']} #{context['bolum_no']}"
    
    return title

def write_description(context, title):
    prompt = (
        f"YouTube uzun korku videosu için SEO uyumlu, izleyiciyi içine çekecek detaylı bir açıklama yaz. "
        f"İlk paragraf merak uyandıran bir özet olsun. Altına ilgili Türkçe hashtag'ler (en az 10 tane) ekle. "
        f"Sadece açıklamayı döndür.\nBaşlık: {title}\nBağlam: {context['prompt_context']}"
    )
    return call_gemini(prompt, temperature=0.7, max_tokens=400)

def main():
    context = generate_dynamic_context()
    print(f"Senaryo üretiliyor... (Tema: {context['tema']})")
    
    script = write_script(context)

    time.sleep(2)
    title = write_title(context)
    title = title.replace('"', '').replace("'", "")

    time.sleep(2)
    description = write_description(context, title)

    # BURASI VE ALTINDAKİ HER ŞEY YANLIŞLIKLA SİLİNMİŞTİ
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

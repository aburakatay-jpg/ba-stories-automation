#!/usr/bin/env python3
"""
temalar_shorts.json'dan, SON KULLANILAN TEMALARI HARİÇ TUTARAK rastgele
bir tema seçer, Gemini API ile KISA (150-200 kelime) bir Türkçe short
senaryosu yazdırır. Çıktı: output/senaryo.txt, output/baslik.txt, output/aciklama.txt

Gerekli ortam değişkeni: GEMINI_API_KEY
"""
import json
import os
import random
import time

import requests

os.makedirs("output", exist_ok=True)

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GECMIS_UZUNLUK = 6


def call_gemini(prompt, temperature=0.9, max_tokens=500, max_retries=5):
    api_key = os.environ["GEMINI_API_KEY"]
    for attempt in range(max_retries):
        resp = requests.post(
            f"{API_URL}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                },
            },
            timeout=60,
        )
        if resp.status_code == 429:
            wait = min(float(resp.headers.get("retry-after", 30)), 60)
            print(f"Rate limit'e takıldık, {wait:.0f} saniye bekleniyor...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    raise RuntimeError("Gemini API'ye çok denemeden sonra bile ulaşılamadı")


def pick_theme():
    base_dir = os.path.dirname(__file__)
    temalar_path = os.path.join(base_dir, "temalar_shorts.json")
    gecmis_path = os.path.join(base_dir, "tema_gecmisi_shorts.json")

    with open(temalar_path, "r", encoding="utf-8") as f:
        temalar = json.load(f)

    gecmis = []
    if os.path.exists(gecmis_path):
        with open(gecmis_path, "r", encoding="utf-8") as f:
            gecmis = json.load(f)

    uygun = [t for t in temalar if t["tema"] not in gecmis]
    if not uygun:
        uygun = temalar

    secilen = random.choice(uygun)

    gecmis.append(secilen["tema"])
    gecmis = gecmis[-GECMIS_UZUNLUK:]
    with open(gecmis_path, "w", encoding="utf-8") as f:
        json.dump(gecmis, f, ensure_ascii=False, indent=2)

    return secilen


def write_script(theme):
    prompt = (
        f"Sen Türkçe bir korku YouTube Shorts kanalı için senaryo yazarısın. "
        f"Sanki forumda birinci ağızdan gerçek yaşanmış gibi anlatılan, çok kısa "
        f"ve çarpıcı bir korku anısı yaz. UZUNLUK ZORUNLU: 150-200 kelime — bu "
        f"45-60 saniyelik seslendirmeye denk gelir. İlk cümle anında kanca atmalı. "
        f"Tek bir olay/an etrafında dön, dallanma yapma. Anlatıcı ASLA kendi adını "
        f"söylemesin, sadece birinci ağızdan ('ben') anlatsın. Sonunda ani ve "
        f"rahatsız edici bir final cümlesi olsun, açıklama yapma. DİL KURALI: metin "
        f"SADECE düzgün, standart yazım kurallarına uygun Türkçe olacak. Tek bir "
        f"İngilizce kelime bile kullanma. Uydurma veya hatalı çekimlenmiş kelime "
        f"kullanma. Sadece senaryo metnini döndür.\n\n"
        f"Tema: {theme['tema']}\nMekan: {theme['mekan']}"
    )
    return call_gemini(prompt, temperature=0.95, max_tokens=600)


def proofread_script(script):
    prompt = (
        f"Sen bir Türkçe dil editörüsün. Sana verilen metni dikkatlice gözden "
        f"geçir ve SADECE şu hataları düzelt: (1) yazım/imla hataları, (2) var "
        f"olmayan veya hatalı çekimlenmiş kelimeler, (3) İngilizce veya yabancı "
        f"kelimeleri doğru Türkçe karşılığıyla değiştir. Metnin anlamını, "
        f"uzunluğunu, üslubunu ve cümle yapısını DEĞİŞTİRME - sadece hataları "
        f"düzelt. Sadece düzeltilmiş metni döndür, açıklama ekleme.\n\n{script}"
    )
    return call_gemini(prompt, temperature=0.3, max_tokens=600)


def write_title(theme):
    prompt = (
        f"YouTube Shorts korku videosu için çok kısa (en fazla 8 kelime), merak "
        f"uyandıran bir Türkçe başlık yaz. Soru formatı veya gizem vurgusu iyi "
        f"çalışır. Sonuna #shorts ekle. Sadece başlığı döndür, tırnak kullanma.\n\n"
        f"Tema: {theme['tema']}, Mekan: {theme['mekan']}"
    )
    return call_gemini(prompt, temperature=0.8, max_tokens=40).strip('"')


def write_description(theme, title):
    prompt = (
        f"YouTube korku videosu için SEO uyumlu bir açıklama yaz. 2-3 cümlelik "
        f"merak uyandıran bir özet + aşağıya ilgili Türkçe hashtag'ler (en az 8 "
        f"tane, örn. #korku #paranormal #gerçekhikaye #gizem gibi) ekle. Hikayenin "
        f"sonunu ifşa etme. Sadece açıklama metnini döndür.\n\n"
        f"Başlık: {title}\nTema: {theme['tema']}, Mekan: {theme['mekan']}"
    )
    return call_gemini(prompt, temperature=0.7, max_tokens=300)


def write_cta():
    prompt = (
        f"Türkçe bir korku/paranormal YouTube kanalı için, videonun sonuna "
        f"eklenecek kısa (2-3 cümle) ve doğal bir kapanış metni yaz. Sanki "
        f"anlatıcı hikayeyi bitirdikten sonra izleyiciye dönüyormuş gibi, sohbet "
        f"tarzında olsun. Şu unsurları içersin: (1) hikayenin gerçek mi kurgu mu "
        f"olduğu sorusu, (2) yorumlara davet, (3) abone ol çağrısı. Klişe ve "
        f"yapay gelmesin, samimi ve kısa olsun. Sadece metni döndür."
    )
    return call_gemini(prompt, temperature=0.8, max_tokens=150)


def main():
    theme = pick_theme()
    script = write_script(theme)

    time.sleep(2)
    script = proofread_script(script)

    time.sleep(2)
    cta = write_cta()
    script = script + "\n\n" + cta

    time.sleep(2)
    title = write_title(theme)

    time.sleep(2)
    description = write_description(theme, title)

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(script)
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(title)
    with open("output/aciklama.txt", "w", encoding="utf-8") as f:
        f.write(description)
    with open("output/tema.json", "w", encoding="utf-8") as f:
        json.dump(theme, f, ensure_ascii=False)
    with open("output/playlist_id.txt", "w", encoding="utf-8") as f:
        f.write("")

    print(f"OK: {len(script)} karakterlik short senaryosu üretildi — '{title}'")


if __name__ == "__main__":
    main()

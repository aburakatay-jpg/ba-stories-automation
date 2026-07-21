#!/usr/bin/env python3
"""
temalar_shorts.json'dan, SON KULLANILAN TEMALARI HARİÇ TUTARAK rastgele
bir tema seçer, Groq API ile KISA (150-200 kelime) bir Türkçe short
senaryosu yazdırır. Çıktı: output/senaryo.txt, output/baslik.txt, output/aciklama.txt

Gerekli ortam değişkeni: GROQ_API_KEY
"""
import json
import os
import random
import time

import requests

os.makedirs("output", exist_ok=True)

API_URL = "https://api.groq.com/openai/v1/chat/completions"
GECMIS_UZUNLUK = 6  # son 6 tema hariç tutulur


def call_groq(messages, temperature, max_tokens, timeout=60, max_retries=5):
    api_key = os.environ["GROQ_API_KEY"]
    for attempt in range(max_retries):
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        if resp.status_code == 429:
            wait = float(resp.headers.get("retry-after", 15))
            wait = max(wait, 10) * (attempt + 1)
            print(f"Rate limit'e takıldık, {wait:.0f} saniye bekleniyor...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    raise RuntimeError("Groq API'ye çok denemeden sonra bile ulaşılamadı (rate limit)")


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
    if not uygun:  # hepsi son kullanılanlardaysa (havuz çok küçükse), tüm havuza geri dön
        uygun = temalar

    secilen = random.choice(uygun)

    gecmis.append(secilen["tema"])
    gecmis = gecmis[-GECMIS_UZUNLUK:]
    with open(gecmis_path, "w", encoding="utf-8") as f:
        json.dump(gecmis, f, ensure_ascii=False, indent=2)

    return secilen


def write_script(theme):
    return call_groq(
        [
            {
                "role": "system",
                "content": (
                    "Sen Türkçe bir korku YouTube Shorts kanalı için "
                    "senaryo yazarısın. Sanki forumda birinci ağızdan "
                    "gerçek yaşanmış gibi anlatılan, çok kısa ve çarpıcı "
                    "bir korku anısı yaz. UZUNLUK ZORUNLU: 150-200 kelime "
                    "— bu 45-60 saniyelik seslendirmeye denk gelir. İlk "
                    "cümle anında kanca atmalı (short'larda ilk 2 saniye "
                    "her şey). Tek bir olay/an etrafında dön, dallanma "
                    "yapma. Anlatıcı ASLA kendi adını söylemesin, sadece "
                    "birinci ağızdan ('ben') anlatsın. Sonunda ani ve "
                    "rahatsız edici bir final cümlesi olsun, açıklama "
                    "yapma. Sadece senaryo metnini döndür."
                ),
            },
            {
                "role": "user",
                "content": f"Tema: {theme['tema']}\nMekan: {theme['mekan']}",
            },
        ],
        temperature=0.95,
        max_tokens=500,
    )


def write_title(theme):
    return call_groq(
        [
            {
                "role": "system",
                "content": (
                    "YouTube Shorts korku videosu için çok kısa (en fazla "
                    "8 kelime), merak uyandıran bir Türkçe başlık yaz. "
                    "Sonuna #shorts ekle. Sadece başlığı döndür, tırnak "
                    "kullanma."
                ),
            },
            {"role": "user", "content": f"Tema: {theme['tema']}, Mekan: {theme['mekan']}"},
        ],
        temperature=0.8,
        max_tokens=40,
        timeout=30,
    ).strip('"')


def write_description(theme, title):
    return call_groq(
        [
            {
                "role": "system",
                "content": (
                    "YouTube korku videosu için SEO uyumlu bir açıklama "
                    "yaz. 2-3 cümlelik merak uyandıran bir özet + "
                    "aşağıya ilgili Türkçe hashtag'ler (en az 8 tane, "
                    "örn. #korku #paranormal #gerçekhikaye #gizem gibi) "
                    "ekle. Hikayenin sonunu ifşa etme. Sadece açıklama "
                    "metnini döndür."
                ),
            },
            {
                "role": "user",
                "content": f"Başlık: {title}\nTema: {theme['tema']}, Mekan: {theme['mekan']}",
            },
        ],
        temperature=0.7,
        max_tokens=300,
        timeout=30,
    )


def main():
    theme = pick_theme()
    script = write_script(theme)
    time.sleep(5)
    title = write_title(theme)

    time.sleep(5)
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
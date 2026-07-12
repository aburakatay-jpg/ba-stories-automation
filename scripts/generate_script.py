#!/usr/bin/env python3
"""
temalar.json'dan rastgele bir tema seçer, Groq API ile Türkçe forum-itirafı
tonunda ORİJİNAL bir senaryo yazdırır. Çıktı: output/senaryo.txt, output/baslik.txt

Not: Önceki sürüm Reddit'ten hikaye çekiyordu, ancak GitHub Actions'ın
sunucu IP'leri Reddit tarafından bot olarak engelleniyor (403 Blocked).
Bu yüzden dış kaynağa bağımlı olmayan, tema havuzundan üreten bir yaklaşıma
geçildi — hem daha güvenilir hem de Türk izleyiciye daha uygun.

Gerekli ortam değişkeni: GROQ_API_KEY
"""
import json
import os
import random

import requests

os.makedirs("output", exist_ok=True)


def pick_theme():
    with open(os.path.join(os.path.dirname(__file__), "temalar.json"), "r", encoding="utf-8") as f:
        temalar = json.load(f)
    return random.choice(temalar)


def write_script(theme):
    api_key = os.environ["GROQ_API_KEY"]
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Sen Türkçe bir korku/paranormal YouTube kanalı için "
                        "senaryo yazarısın. Sanki bir forum/itiraf sitesinde "
                        "birinci ağızdan gerçek yaşanmış gibi anlatılan, doğal "
                        "ve akıcı bir Türkçe korku hikayesi yaz. İlk iki "
                        "cümlede güçlü bir kanca (hook) olsun. 400-600 kelime, "
                        "3-5 dakikalık seslendirmeye uygun uzunlukta olsun. "
                        "Klişe jump-scare yerine gerilim ve belirsizlik "
                        "kullan. Sonunda net bir açıklama yapma, esrarını "
                        "koru. Sadece senaryo metnini döndür, başlık veya "
                        "başka açıklama ekleme."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Tema: {theme['tema']}\nMekan: {theme['mekan']}\n\n"
                        "Bu tema ve mekana göre özgün bir hikaye yaz."
                    ),
                },
            ],
            "temperature": 0.9,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def write_title(theme):
    api_key = os.environ["GROQ_API_KEY"]
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "YouTube korku kanalı için merak uyandıran, kısa "
                        "(en fazla 12 kelime) bir Türkçe başlık yaz. Soru "
                        "formatı veya gizem vurgusu iyi çalışır. Sadece "
                        "başlığı döndür, tırnak işareti kullanma."
                    ),
                },
                {"role": "user", "content": f"Tema: {theme['tema']}, Mekan: {theme['mekan']}"},
            ],
            "temperature": 0.8,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip().strip('"')


def main():
    theme = pick_theme()
    script = write_script(theme)
    title = write_title(theme)

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(script)
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(title)

    print(f"OK: {len(script)} karakterlik senaryo üretildi — '{title}'")


if __name__ == "__main__":
    main()

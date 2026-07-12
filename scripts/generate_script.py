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
                        "ve akıcı bir Türkçe korku hikayesi yaz. "
                        "UZUNLUK ZORUNLU: 1800-2200 kelime — bu, 10-11 "
                        "dakikalık bir seslendirmeye denk gelir, kısa "
                        "kesme. Bu uzunluğa doğal ulaşmak için hikayeyi şu "
                        "yapıda kur: (1) güçlü bir kanca ile açılış, "
                        "(2) sıradan bir başlangıç ve karakterlerin/ortamın "
                        "tanıtımı, (3) ilk tuhaflıklar ve artan şüphe, "
                        "(4) olayların yoğunlaşması — en az 2-3 ayrı gerilim "
                        "anı/sahne, her biri bir öncekinden daha rahatsız "
                        "edici, (5) doruk noktası, (6) esrarını koruyan bir "
                        "kapanış (net açıklama yapma). Betimlemelerde "
                        "cömert ol (ortam, sesler, fiziksel tepkiler, iç "
                        "ses), ama tekrar veya doldurma hissi verme — her "
                        "paragraf hikayeyi ileri taşısın. Klişe jump-scare "
                        "yerine yavaş yavaş büyüyen gerilim kullan. Sadece "
                        "senaryo metnini döndür, başlık veya başka açıklama "
                        "ekleme."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Tema: {theme['tema']}\nMekan: {theme['mekan']}\n\n"
                        "Bu tema ve mekana göre, 1800-2200 kelimelik özgün "
                        "ve sürükleyici bir hikaye yaz."
                    ),
                },
            ],
            "temperature": 0.9,
            "max_tokens": 6000,
        },
        timeout=120,
    )
    resp.raise_for_status()
    script = resp.json()["choices"][0]["message"]["content"].strip()

    # Model 1800 kelime talimatına rağmen kısa kesebiliyor - eksikse devamını yazdır
    attempts = 0
    while len(script.split()) < 1600 and attempts < 3:
        api_key = os.environ["GROQ_API_KEY"]
        cont_resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Aşağıdaki Türkçe korku hikayesinin devamını "
                            "yaz. Aynı üslupta, kaldığı yerden akıcı şekilde "
                            "devam et, tekrar etme, gerilimi bir üst "
                            "seviyeye taşı. En az 600 kelime ekle. Sadece "
                            "devam eden metni döndür, önceki kısmı tekrar "
                            "yazma."
                        ),
                    },
                    {"role": "user", "content": script},
                ],
                "temperature": 0.9,
                "max_tokens": 4000,
            },
            timeout=120,
        )
        cont_resp.raise_for_status()
        script += "\n\n" + cont_resp.json()["choices"][0]["message"]["content"].strip()
        attempts += 1

    return script


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
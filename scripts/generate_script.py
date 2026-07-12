#!/usr/bin/env python3
"""
r/nosleep'ten rastgele bir hikaye çeker, Groq API ile Türkçe forum-itirafı
tonunda senaryoya çevirir. Çıktı: output/senaryo.txt, output/baslik.txt

Gerekli ortam değişkeni: GROQ_API_KEY
"""
import os
import random
import requests

os.makedirs("output", exist_ok=True)

HEADERS = {"User-Agent": "ba-stories-bot/1.0"}


def fetch_story():
    url = "https://www.reddit.com/r/nosleep/top.json?limit=10&t=month"
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    posts = resp.json()["data"]["children"]
    pick = random.choice(posts)["data"]
    return pick["title"], pick["selftext"]


def write_script(title, story):
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
                        "senaryo yazarısın. Sana verilen İngilizce hikayeyi, "
                        "sanki bir Türk forum/itiraf sitesinde birinci ağızdan "
                        "yazılmış gibi, doğal ve akıcı Türkçeye uyarla. İlk iki "
                        "cümlede güçlü bir kanca (hook) olsun. 400-600 kelime, "
                        "3-5 dakikalık seslendirmeye uygun uzunlukta olsun. "
                        "Sadece senaryo metnini döndür, başka açıklama ekleme."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Başlık: {title}\n\nHikaye: {story}",
                },
            ],
            "temperature": 0.8,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def main():
    title, story = fetch_story()
    script = write_script(title, story)

    with open("output/senaryo.txt", "w", encoding="utf-8") as f:
        f.write(script)
    with open("output/baslik.txt", "w", encoding="utf-8") as f:
        f.write(title)

    print(f"OK: {len(script)} karakterlik senaryo üretildi — '{title}'")


if __name__ == "__main__":
    main()

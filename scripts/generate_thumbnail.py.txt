#!/usr/bin/env python3
"""
Tema + başlığa göre kanalın sabit görsel tarzında bir thumbnail üretir.
Pollinations.ai kullanılıyor - API key gerektirmiyor, tamamen ücretsiz.

Kullanım:
  python3 generate_thumbnail.py output/tema.json output/baslik.txt output/thumbnail.jpg
"""
import json
import sys
import urllib.parse

import requests

STYLE = (
    "grainy found-footage horror photography, dim moody lighting, "
    "obscured figure or silhouette, no visible face, cinematic horror, "
    "muted desaturated colors, unsettling atmosphere, VHS grain texture, "
    "photorealistic, 16:9"
)


def main():
    if len(sys.argv) != 4:
        print("Kullanım: generate_thumbnail.py <tema.json> <baslik.txt> <cikti.jpg>", file=sys.stderr)
        sys.exit(1)

    tema_path, title_path, output_path = sys.argv[1:4]

    with open(tema_path, "r", encoding="utf-8") as f:
        theme = json.load(f)
    with open(title_path, "r", encoding="utf-8") as f:
        title = f.read().strip()

    prompt = f"{theme['tema']}, {theme['mekan']}, {STYLE}"
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true"

    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(resp.content)

    print(f"OK: {output_path} üretildi ('{title}' için)")


if __name__ == "__main__":
    main()
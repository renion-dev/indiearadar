"""
og_image.py
Генерація OG images через Pollinations.ai (безкоштовно, без ключа)
Викликається з harvest.py для кожного нового дайджесту.
"""

import requests
import os
import urllib.parse
from pathlib import Path

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/"

def generate_og_image(title: str, slug: str, output_dir: str = "assets/images/og") -> str:
    """
    Генерує OG image для поста і повертає відносний шлях.
    Якщо генерація не вдалася — повертає fallback og-default.svg
    """
    os.makedirs(output_dir, exist_ok=True)

    # Покращений промпт (без тексту)
    prompt = (
        f"Minimalist tech blog header image, dark gradient background "
        f"#0f172a to #1e293b, abstract geometric shapes, "
        f"glowing purple and blue accents, futuristic clean design, "
        f"no text, no letters, no words, 16:9 aspect ratio, "
        f"high quality, professional, subtle glow effects"
    )

    # Безпечний seed (невід'ємний)
    seed = abs(hash(slug)) % 10000

    # Формуємо URL з параметрами
    # Додаємо модель flux для кращої якості (або stable-diffusion)
    url = f"{POLLINATIONS_URL}{urllib.parse.quote(prompt)}"
    url += f"?width=1200&height=630&nologo=true&seed={seed}&model=flux"

    output_path = Path(output_dir) / f"{slug}.png"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, timeout=90, headers=headers)
        resp.raise_for_status()

        # Перевіряємо, чи це зображення
        content_type = resp.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            print(f"[OG Image] Warning: unexpected Content-Type '{content_type}' for {slug}")
            return "/assets/images/og-default.svg"

        # Перевіряємо розмір (щоб уникнути порожніх файлів)
        if len(resp.content) < 1000:  # менше 1KB — підозріло
            print(f"[OG Image] Generated image too small ({len(resp.content)} bytes) for {slug}")
            return "/assets/images/og-default.svg"

        with open(output_path, "wb") as f:
            f.write(resp.content)

        print(f"[OG Image] Successfully generated {output_path}")
        return f"/{output_dir}/{slug}.png"

    except requests.exceptions.RequestException as e:
        print(f"[OG Image] Request failed for {slug}: {e}")
        return "/assets/images/og-default.svg"
    except Exception as e:
        print(f"[OG Image] Unexpected error for {slug}: {e}")
        return "/assets/images/og-default.svg"


def generate_tool_og(tool_name: str, category: str, slug: str,
                     output_dir: str = "assets/images/og") -> str:
    """
    Генерує OG image для сторінки інструменту.
    """
    os.makedirs(output_dir, exist_ok=True)

    prompt = (
        f"Modern tech product showcase, dark background #0f172a, "
        f"{category} software concept, abstract UI elements, "
        f"neon purple and cyan highlights, clean minimal design, "
        f"no text, no letters, professional 3D render style, "
        f"1200x630, high quality"
    )

    seed = abs(hash(slug)) % 10000
    url = f"{POLLINATIONS_URL}{urllib.parse.quote(prompt)}"
    url += f"?width=1200&height=630&nologo=true&seed={seed}&model=flux"

    output_path = Path(output_dir) / f"tool-{slug}.png"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, timeout=90, headers=headers)
        resp.raise_for_status()
        content_type = resp.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            print(f"[OG Image] Unexpected Content-Type for tool {slug}: {content_type}")
            return "/assets/images/og-default.svg"
        if len(resp.content) < 1000:
            print(f"[OG Image] Tool image too small for {slug}")
            return "/assets/images/og-default.svg"
        with open(output_path, "wb") as f:
            f.write(resp.content)
        print(f"[OG Image] Successfully generated tool image {output_path}")
        return f"/{output_dir}/tool-{slug}.png"
    except Exception as e:
        print(f"[OG Image] Failed for tool {slug}: {e}")
        return "/assets/images/og-default.svg"
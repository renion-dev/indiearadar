#!/usr/bin/env python3
"""
OG Image Generator for AI tools.
"""

import os
import time
import re
import requests
from pathlib import Path
from utils import logger, RateLimiter

# Лімітер для pollinations.ai: 1 запит на 2 секунди
POLLINATIONS_RATE_LIMIT = RateLimiter(calls=1, period=2)

def generate_tool_og(tool_name, category, slug, output_dir="assets/images/og"):
    """
    Generate OG image for a tool using pollinations.ai.
    Returns relative path to the generated image.
    """
    # Sanitize inputs
    safe_name = re.sub(r'[^a-zA-Z0-9\s-]', '', tool_name)[:60]
    safe_category = re.sub(r'[^a-zA-Z0-9\s-]', '', category)[:30]
    
    # Prompt for image generation
    prompt = f"Modern tech product showcase, dark background #0f172a, {safe_category} software concept, abstract UI elements, neon purple and cyan highlights, clean minimal design, no text, no letters, professional 3D render style, 1200x630, high quality"
    
    # Create output directory
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Output filename
    filename = f"tool-{slug}.png"
    filepath = out_dir / filename
    
    # If file exists, return existing path
    if filepath.exists():
        return str(filepath)
    
    # Rate limit before making request
    POLLINATIONS_RATE_LIMIT.wait()
    
    # Try to generate image with retries on 429
    max_retries = 3
    for attempt in range(max_retries):
        try:
            url = f"https://image.pollinations.ai/prompt/{prompt}?width=1200&height=630&nologo=true&seed={hash(slug) % 10000}&model=flux"
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                logger.info(f"[OG Image] Generated: {filepath}")
                return str(filepath)
            elif response.status_code == 429:
                wait_time = 2 ** attempt * 5  # 5, 10, 20 seconds
                logger.warning(f"[OG Image] Rate limit hit for {tool_name}, waiting {wait_time}s")
                time.sleep(wait_time)
            else:
                logger.warning(f"[OG Image] Failed for {tool_name}: {response.status_code}")
                break
        except Exception as e:
            logger.warning(f"[OG Image] Error for {tool_name}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                break
    
    # Fallback: return a default image path or empty
    logger.warning(f"[OG Image] Using fallback for {tool_name}")
    return "/assets/images/og/default.png"

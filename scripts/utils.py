#!/usr/bin/env python3
"""
utils.py — Shared utilities for Indie AI Radar automation.
Retry, cache, rate limiting, logging, AI filter, file I/O.
"""
import os
import json
import time
import random
import logging
import re
import yaml
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Optional, Callable, Any, List, Dict

# ─── Logging ─────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("indiearadar")

# File handler for persistent logs
os.makedirs("_logs", exist_ok=True)
file_handler = logging.FileHandler("_logs/automation.log")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(file_handler)


# ─── Retry with exponential backoff ────────────────────────────────
def retry(max_retries: int = 3, backoff_factor: float = 2.0,
          exceptions: tuple = (Exception,)):
    """Decorator: retry function on failure with exponential backoff + jitter."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    wait = (backoff_factor ** attempt) + random.uniform(0, 1)
                    if attempt == max_retries:
                        logger.error(f"[retry] {func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    logger.warning(f"[retry] {func.__name__} attempt {attempt}/{max_retries} failed: {e}. Waiting {wait:.1f}s...")
                    time.sleep(wait)
        return wrapper
    return decorator


# ─── JSON Cache ──────────────────────────────────────────────────────
class Cache:
    """Persistent JSON cache with TTL support."""
    def __init__(self, path: str = "_cache/harvest_cache.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"[cache] Corrupted cache, resetting: {e}")
                self.data = {}

    def save(self):
        temp_path = self.path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        temp_path.replace(self.path)

    def get(self, key: str) -> Optional[Any]:
        entry = self.data.get(key)
        if entry:
            expires = datetime.fromisoformat(entry["expires"])
            if datetime.now(timezone.utc) < expires:
                return entry["value"]
        return None

    def set(self, key: str, value: Any, ttl_hours: int = 24):
        self.data[key] = {
            "value": value,
            "expires": (datetime.now(timezone.utc) + timedelta(hours=ttl_hours)).isoformat()
        }
        self.save()

    def is_processed(self, item_id: str) -> bool:
        return bool(self.data.get(f"processed:{item_id}", False))

    def mark_processed(self, item_id: str):
        self.data[f"processed:{item_id}"] = True
        self.save()

    def get_processed_count(self) -> int:
        return sum(1 for k in self.data if k.startswith("processed:"))


# ─── Rate Limiter ──────────────────────────────────────────────────
class RateLimiter:
    """Token bucket style rate limiter."""
    def __init__(self, calls: int, period: int):
        """Allow `calls` requests per `period` seconds."""
        self.calls = calls
        self.period = period
        self.timestamps: List[float] = []

    def wait(self):
        now = time.time()
        # Clean old timestamps
        self.timestamps = [t for t in self.timestamps if now - t < self.period]
        if len(self.timestamps) >= self.calls:
            sleep_time = self.period - (now - self.timestamps[0]) + 0.5
            logger.debug(f"[rate_limit] Bucket full. Sleeping {sleep_time:.1f}s...")
            time.sleep(sleep_time)
        self.timestamps.append(time.time())


# ─── Safe File Writer ──────────────────────────────────────────────
def write_file(path: str, content: str):
    """Write content to file, creating parent dirs if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"[write] {path}")


# ─── AI Keyword Filter ───────────────────────────────────────────
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "ml", "llm",
    "gpt", "openai", "claude", "gemini", "stable diffusion", "midjourney",
    "copilot", "assistant", "automation", "neural", "embeddings",
    "vector", "rag", "agent", "chatbot", "generative", "synthetic",
    "prompt", "fine-tune", "inference", "model", "transformer",
    "diffusion", "latent", "token", "embedding", "dataset", "hugging face",
    "replicate", "langchain", "crewai", "autogpt", "sidekick",
    "workflow", "no-code", "low-code", "indie", "solopreneur", "maker",
    "bootstrap", "saas", "micro-saas", "api", "webhook", "integration",
    "code generation", "text-to-image", "text-to-speech", "voice",
    "computer vision", "nlp", "deep learning"
]

def is_ai_related(text: str, threshold: int = 1) -> bool:
    """Return True if text contains at least `threshold` AI keywords."""
    text_lower = text.lower()
    # Use a set for O(1) lookup of words
    words = set(re.findall(r"\w+", text_lower))
    matches = sum(1 for kw in AI_KEYWORDS if kw.lower() in text_lower) 
    # Note: keeping 'in text_lower' for multi-word keywords, 
    # but for single words set intersection would be faster.
    return matches >= threshold


# ─── Slugify ───────────────────────────────────────────────────────
def slugify(name: str) -> str:
    """Convert tool name to URL-safe slug."""
    s = re.sub(r"[^\w\s-]", "", name.lower())
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    return s[:60]


# ─── Front Matter Parser ───────────────────────────────────────────
def parse_front_matter(filepath: str) -> Dict[str, Any]:
    """Extract Jekyll front matter using PyYAML. Returns empty if no FM."""
    p = Path(filepath)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    try:
        fm = yaml.safe_load(parts[1]) or {}
        fm["__body__"] = parts[2].strip()
        return fm
    except yaml.YAMLError as e:
        logger.error(f"[parse] YAML error in {filepath}: {e}")
        return {}

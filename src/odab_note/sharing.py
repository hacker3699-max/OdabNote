"""OdabNote community sharing module — auto-sync mistakes to Supabase."""

import json
import os
import re
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

CONFIG_PATH = os.path.expanduser("~/.gemini/antigravity/odab_config.json")

DEFAULT_CONFIG = {
    "share_enabled": False,
    "supabase_url": "",
    "supabase_key": "",
    "anonymous_id": ""
}


def _generate_anonymous_id() -> str:
    """Generate a random anonymous ID for this installation."""
    import hashlib
    import uuid
    return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16]


def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            # Merge with defaults for missing keys
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
    return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


def enable_sharing(supabase_url: str, supabase_key: str):
    config = load_config()
    config["share_enabled"] = True
    config["supabase_url"] = supabase_url.rstrip("/")
    config["supabase_key"] = supabase_key
    if not config["anonymous_id"]:
        config["anonymous_id"] = _generate_anonymous_id()
    save_config(config)


def disable_sharing():
    config = load_config()
    config["share_enabled"] = False
    save_config(config)


def _sanitize_for_sharing(keyword: str, error_pattern: str, solution: str) -> Dict[str, str]:
    """Strip file paths, usernames, and project-specific info from the data."""
    def clean(text: str) -> str:
        # Remove absolute file paths
        text = re.sub(r'(/Users/[^\s]+|/home/[^\s]+|C:\\[^\s]+)', '[PATH]', text)
        # Remove common username patterns
        text = re.sub(r'(?i)(user|username|login):\s*\S+', r'\1: [REDACTED]', text)
        return text

    return {
        "keyword": clean(keyword),
        "error_pattern": clean(error_pattern),
        "solution": clean(solution)
    }


def auto_share(keyword: str, error_pattern: str, solution: str, target_model: str = "all") -> Optional[str]:
    """Automatically share a mistake to the community DB if sharing is enabled."""
    config = load_config()
    if not config.get("share_enabled"):
        return None

    url = config.get("supabase_url")
    key = config.get("supabase_key")
    if not url or not key:
        return None

    sanitized = _sanitize_for_sharing(keyword, error_pattern, solution)

    payload = {
        "keyword": sanitized["keyword"],
        "error_pattern": sanitized["error_pattern"],
        "solution": sanitized["solution"],
        "target_model": target_model,
        "shared_by": config.get("anonymous_id", "anonymous")
    }

    try:
        req = urllib.request.Request(
            f"{url}/rest/v1/shared_mistakes",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Prefer": "return=minimal"
            },
            method="POST"
        )
        urllib.request.urlopen(req, timeout=5)
        return "shared"
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        # Silently fail — never block the user's workflow
        return None


def pull_community(target_model: str = "all") -> list:
    """Pull community-shared mistakes from Supabase."""
    config = load_config()
    url = config.get("supabase_url")
    key = config.get("supabase_key")
    if not url or not key:
        return []

    try:
        query = f"{url}/rest/v1/shared_mistakes?select=keyword,error_pattern,solution,target_model&order=created_at.desc&limit=100"
        if target_model != "all":
            query += f"&target_model=eq.{target_model}"

        req = urllib.request.Request(
            query,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, OSError):
        return []

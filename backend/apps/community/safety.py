import re

from django.conf import settings


def configured_sensitive_words():
    words = getattr(settings, "COMMUNITY_SENSITIVE_WORDS", []) or []
    cleaned = []
    seen = set()
    for item in words:
        word = str(item or "").strip()
        if not word:
            continue
        key = word.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(word)
    return sorted(cleaned, key=len, reverse=True)


def mask_sensitive_text(value):
    text = str(value or "")
    if not text:
        return text, []

    filtered = text
    hits = []
    for word in configured_sensitive_words():
        pattern = re.compile(re.escape(word), flags=re.IGNORECASE)
        if not pattern.search(filtered):
            continue
        hits.append(word)
        filtered = pattern.sub(lambda match: "*" * len(match.group(0)), filtered)
    return filtered, hits


def sanitize_sensitive_fields(data, field_names):
    hits = {}
    for field_name in field_names:
        if field_name not in data:
            continue
        masked, matched_words = mask_sensitive_text(data.get(field_name))
        data[field_name] = masked
        if matched_words:
            hits[field_name] = matched_words
    return hits

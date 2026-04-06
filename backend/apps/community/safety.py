import re
from dataclasses import dataclass

from django.apps import apps
from django.conf import settings
from django.db import OperationalError, ProgrammingError


SEPARATOR_PATTERN = r"[\s\-_.,，。!?！？;；:：、~`'\"“”‘’()（）【】\[\]{}<>《》/\\|]*"


@dataclass(frozen=True)
class SensitiveRule:
    word: str
    action: str


def _clean_rule_word(value):
    return str(value or "").strip()


def _normalize_rule_key(word, action):
    return action, word.casefold()


def _env_rules():
    rules = []
    for word in getattr(settings, "COMMUNITY_SENSITIVE_WORDS", []) or []:
        cleaned = _clean_rule_word(word)
        if cleaned:
            rules.append(SensitiveRule(word=cleaned, action="mask"))
    for word in getattr(settings, "COMMUNITY_BLOCKED_WORDS", []) or []:
        cleaned = _clean_rule_word(word)
        if cleaned:
            rules.append(SensitiveRule(word=cleaned, action="block"))
    return rules


def _db_rules():
    try:
        model = apps.get_model("community", "SensitiveWordRule")
    except LookupError:
        return []

    try:
        rows = model.objects.filter(is_active=True).values_list("word", "action")
    except (OperationalError, ProgrammingError):
        return []

    return [SensitiveRule(word=_clean_rule_word(word), action=str(action or "mask").strip() or "mask") for word, action in rows]


def configured_sensitive_rules():
    rules = []
    seen = set()
    for rule in [*_env_rules(), *_db_rules()]:
        if not rule.word:
            continue
        key = _normalize_rule_key(rule.word, rule.action)
        if key in seen:
            continue
        seen.add(key)
        rules.append(rule)
    return sorted(rules, key=lambda item: (item.action != "block", -len(item.word), item.word.casefold()))


def _pattern_for_word(word):
    chars = [re.escape(char) for char in word]
    return re.compile(SEPARATOR_PATTERN.join(chars), flags=re.IGNORECASE)


def _masked_match(match_text):
    return "".join("*" if not re.fullmatch(SEPARATOR_PATTERN, char) and not char.isspace() else char for char in match_text)


def analyze_sensitive_text(value):
    text = str(value or "")
    if not text:
        return {"text": text, "masked_hits": [], "blocked_hits": []}

    masked_text = text
    masked_hits = []
    blocked_hits = []

    for rule in configured_sensitive_rules():
        pattern = _pattern_for_word(rule.word)
        if not pattern.search(masked_text if rule.action == "mask" else text):
            continue

        if rule.action == "block":
            blocked_hits.append(rule.word)
            continue

        masked_hits.append(rule.word)
        masked_text = pattern.sub(lambda match: _masked_match(match.group(0)), masked_text)

    return {
        "text": masked_text,
        "masked_hits": list(dict.fromkeys(masked_hits)),
        "blocked_hits": list(dict.fromkeys(blocked_hits)),
    }


def sanitize_sensitive_fields(data, field_names):
    result = {"masked": {}, "blocked": {}}
    for field_name in field_names:
        if field_name not in data:
            continue
        scanned = analyze_sensitive_text(data.get(field_name))
        data[field_name] = scanned["text"]
        if scanned["masked_hits"]:
            result["masked"][field_name] = scanned["masked_hits"]
        if scanned["blocked_hits"]:
            result["blocked"][field_name] = scanned["blocked_hits"]
    return result

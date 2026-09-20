"""
Suggest a translation for a term, to prefill an empty Translation field.

Uses the free MyMemory API (no key).  Anything that goes wrong, or an
answer that is not a real translation, gives "" and the field stays
empty as before.
"""

import json
import os
import urllib.parse
import urllib.request

# Language names to MyMemory codes, for the predefined languages that
# MyMemory knows.  Other languages get no suggestion.
LANGUAGE_CODES = {
    "english": "en",
    "german": "de",
    "french": "fr",
    "spanish": "es",
    "italian": "it",
    "portuguese": "pt",
    "polish": "pl",
    "czech": "cs",
    "turkish": "tr",
    "dutch": "nl",
    "swedish": "sv",
    "ukrainian": "uk",
    "russian": "ru",
}

MIN_MATCH = 0.5
TIMEOUT_SECONDS = 5


def target_language():
    "The language suggestions are written in, LUTE_TRANSLATE_TO, default ru."
    return os.environ.get("LUTE_TRANSLATE_TO", "ru").strip().lower() or "ru"


def _fetch(text, source, target):
    "Call MyMemory, return its JSON."
    query = urllib.parse.urlencode({"q": text, "langpair": f"{source}|{target}"})
    url = f"https://api.mymemory.translated.net/get?{query}"
    with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def suggest_translation(language_name, text):
    "Suggested translation of text, or '' if there is none."
    source = LANGUAGE_CODES.get((language_name or "").strip().lower())
    target = target_language()
    clean = (text or "").replace("​", "").strip()
    if source is None or source == target or clean == "":
        return ""

    try:
        data = _fetch(clean, source, target)
        translated = (data["responseData"]["translatedText"] or "").strip()
        match = float(data["responseData"].get("match") or 0)
    except Exception:  # pylint: disable=broad-exception-caught
        return ""

    # MyMemory answers its quota warning as the translation itself, and
    # echoes a word back when it has nothing.
    if translated.upper().startswith("MYMEMORY WARNING"):
        return ""
    if translated.casefold() == clean.casefold() or match < MIN_MATCH:
        return ""
    return translated

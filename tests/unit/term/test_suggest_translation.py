"Suggested translations for the term form."

import pytest
from lute.term import suggest_translation as st


def _answer(text, match=1):
    return {"responseData": {"translatedText": text, "match": match}}


@pytest.fixture(name="fake_api")
def fixture_fake_api(monkeypatch):
    "Replace the MyMemory call, recording what was asked."
    calls = []
    answers = {"value": _answer("трагедия")}

    def fake_fetch(text, source, target):
        calls.append((text, source, target))
        if isinstance(answers["value"], Exception):
            raise answers["value"]
        return answers["value"]

    monkeypatch.setattr(st, "_fetch", fake_fetch)
    monkeypatch.delenv("LUTE_TRANSLATE_TO", raising=False)
    return calls, answers


def test_translates_into_russian_by_default(fake_api):
    calls, _ = fake_api
    assert st.suggest_translation("English", "tragedy") == "трагедия"
    assert calls == [("tragedy", "en", "ru")]


def test_target_language_can_be_changed(fake_api, monkeypatch):
    calls, _ = fake_api
    monkeypatch.setenv("LUTE_TRANSLATE_TO", "uk")
    st.suggest_translation("German", "Haus")
    assert calls == [("Haus", "de", "uk")]


def test_zero_width_spaces_are_removed(fake_api):
    calls, _ = fake_api
    st.suggest_translation("English", "a​ ​big​ thing")
    assert calls[0][0] == "a big thing"


@pytest.mark.parametrize(
    "language,text",
    [("Klingon", "qapla"), ("Russian", "дом"), ("English", "  "), (None, "word")],
)
def test_no_call_when_there_is_nothing_to_ask(fake_api, language, text):
    calls, _ = fake_api
    assert st.suggest_translation(language, text) == ""
    assert not calls


def test_word_echoed_back_is_no_suggestion(fake_api):
    _, answers = fake_api
    answers["value"] = _answer("Public")
    assert st.suggest_translation("English", "public") == ""


def test_weak_match_is_no_suggestion(fake_api):
    _, answers = fake_api
    answers["value"] = _answer("что-то", match=0.2)
    assert st.suggest_translation("English", "word") == ""


def test_quota_warning_is_no_suggestion(fake_api):
    _, answers = fake_api
    answers["value"] = _answer("MYMEMORY WARNING: YOU USED ALL AVAILABLE FREE TRANSLATIONS", 1)
    assert st.suggest_translation("English", "word") == ""


def test_network_error_is_no_suggestion(fake_api):
    _, answers = fake_api
    answers["value"] = TimeoutError("timed out")
    assert st.suggest_translation("English", "word") == ""


def test_odd_answer_is_no_suggestion(fake_api):
    _, answers = fake_api
    answers["value"] = {"unexpected": True}
    assert st.suggest_translation("English", "word") == ""

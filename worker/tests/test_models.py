"""Unit tests for model helpers."""

from __future__ import annotations

from datetime import datetime

from opencallnotes_worker.models import new_session_id, slugify


def test_slugify_ascii_and_punctuation() -> None:
    assert slugify("Client Call!! 2026") == "client-call-2026"


def test_slugify_unicode_is_transliterated() -> None:
    # NFKD strips diacritics; the stroked 'ł' has no decomposition and is dropped.
    assert slugify("Rozmowa zażółć") == "rozmowa-zazoc"


def test_slugify_empty_falls_back() -> None:
    assert slugify("***") == "session"


def test_new_session_id_format() -> None:
    now = datetime(2026, 6, 18, 22, 15, 3)
    assert new_session_id("Client call", now) == "2026-06-18_22-15-03_client-call"

"""Testes básicos do classificador de resultados."""
import pytest
from sites.definitions import SiteDefinition
from core.verifiers import _classify


class FakeResponse:
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self.text = text
        self._json = json_data

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


def test_status_code_found():
    site = SiteDefinition(name="T", url_template="x", category="dev", verification="status_code")
    r = {"status": "", "confidence": 0, "detail": ""}
    out = _classify(site, FakeResponse(200, ""), r)
    assert out["status"] == "encontrado"
    assert out["confidence"] > 50


def test_status_code_not_found():
    site = SiteDefinition(name="T", url_template="x", category="dev", verification="status_code")
    r = {"status": "", "confidence": 0, "detail": ""}
    out = _classify(site, FakeResponse(404, ""), r)
    assert out["status"] == "não encontrado"


def test_text_absence():
    site = SiteDefinition(name="T", url_template="x", category="dev",
                          verification="text_absence", absence_strings=["not found"])
    r = {"status": "", "confidence": 0, "detail": ""}
    out = _classify(site, FakeResponse(200, "...Not Found..."), r)
    assert out["status"] == "não encontrado"


def test_json_field():
    site = SiteDefinition(name="T", url_template="x", category="dev",
                          verification="json_field",
                          json_check={"field": "login", "must_exist": True})
    r = {"status": "", "confidence": 0, "detail": ""}
    out = _classify(site, FakeResponse(200, "", {"login": "bob"}), r)
    assert out["status"] == "encontrado"


def test_rate_limited():
    site = SiteDefinition(name="T", url_template="x", category="dev", verification="status_code")
    r = {"status": "", "confidence": 0, "detail": ""}
    out = _classify(site, FakeResponse(429, ""), r)
    assert out["status"] == "rate-limited"

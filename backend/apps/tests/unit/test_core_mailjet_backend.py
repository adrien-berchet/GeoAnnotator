"""
Unit tests for Mailjet email backend (apps/core/mailjet_backend.py).
"""

import pytest
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives

from apps.core.mailjet_backend import MailjetBackend


class FakeResult:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {"Messages": [{"Status": "success"}]}

    def json(self):
        return self._payload


class FakeSendAPI:
    def __init__(self, result: FakeResult | Exception):
        self._result = result

    def create(self, data):  # noqa: ARG002 - we don't use data in fake
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class FakeClient:
    def __init__(self, *args, **kwargs):  # noqa: D401, ANN001, ANN002 - test double
        self.send = FakeSendAPI(FakeResult())


@pytest.fixture
def mailjet_settings(settings):
    settings.MAILJET_API_KEY = "test_key"
    settings.MAILJET_SECRET_KEY = "test_secret"
    settings.DEFAULT_FROM_EMAIL = "no-reply@example.com"
    settings.DEFAULT_FROM_NAME = "GeoAnnotator"
    return settings


def make_backend(monkeypatch, settings, result=FakeResult(200)):
    """Helper to construct backend with a fake client returning given result."""

    class _Client:
        def __init__(self, *args, **kwargs):
            self.send = FakeSendAPI(result)

    monkeypatch.setattr("apps.core.mailjet_backend.Client", _Client)
    return MailjetBackend()


class TestInit:
    def test_init_with_credentials_ok(self, mailjet_settings, monkeypatch):
        backend = make_backend(monkeypatch, mailjet_settings)
        assert isinstance(backend.client.send, FakeSendAPI)

    def test_init_missing_credentials_raises(self, settings, monkeypatch):
        settings.MAILJET_API_KEY = None
        settings.MAILJET_SECRET_KEY = None
        with pytest.raises(ValueError):
            make_backend(monkeypatch, settings)

    def test_init_missing_credentials_fail_silently(self, settings, monkeypatch):
        settings.MAILJET_API_KEY = None
        settings.MAILJET_SECRET_KEY = None

        class _Client:
            def __init__(self, *args, **kwargs):
                self.send = FakeSendAPI(FakeResult())

        monkeypatch.setattr("apps.core.mailjet_backend.Client", _Client)
        backend = MailjetBackend(fail_silently=True)
        assert isinstance(backend.client.send, FakeSendAPI)


class TestSendMessages:
    def test_send_messages_empty(self, mailjet_settings, monkeypatch):
        backend = make_backend(monkeypatch, mailjet_settings)
        assert backend.send_messages([]) == 0

    def test_send_text_email_success(self, mailjet_settings, monkeypatch):
        backend = make_backend(monkeypatch, mailjet_settings, result=FakeResult(200))
        msg = EmailMessage(
            subject="Hello",
            body="Plain text body",
            from_email=None,
            to=["alice@example.com"],
        )
        sent = backend.send_messages([msg])
        assert sent == 1

    def test_send_html_email_via_subtype_success(self, mailjet_settings, monkeypatch):
        backend = make_backend(monkeypatch, mailjet_settings, result=FakeResult(200))
        msg = EmailMessage(
            subject="Hi",
            body="<p>HTML</p>",
            from_email="sender@example.com",
            to=["bob@example.com"],
        )
        msg.content_subtype = "html"
        assert backend.send_messages([msg]) == 1

    def test_send_html_via_alternatives_success(self, mailjet_settings, monkeypatch):
        backend = make_backend(monkeypatch, mailjet_settings, result=FakeResult(200))
        msg = EmailMultiAlternatives(
            subject="Alt",
            body="Plain",
            from_email="sender@example.com",
            to=["bob@example.com"],
        )
        msg.attach_alternative("<p>HTML</p>", "text/html")
        assert backend.send_messages([msg]) == 1

    def test_send_with_cc_bcc_success(self, mailjet_settings, monkeypatch):
        backend = make_backend(monkeypatch, mailjet_settings, result=FakeResult(200))
        msg = EmailMessage(
            subject="CC BCC",
            body="Body",
            to=["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )
        assert backend.send_messages([msg]) == 1

    def test_api_returns_non_200_raises_when_not_silent(self, mailjet_settings, monkeypatch):
        backend = make_backend(
            monkeypatch, mailjet_settings, result=FakeResult(400, {"error": "bad"})
        )
        msg = EmailMessage(
            subject="Bad",
            body="Body",
            to=["to@example.com"],
        )
        with pytest.raises(RuntimeError):
            backend.send_messages([msg])

    def test_api_returns_non_200_silent_returns_zero(self, mailjet_settings, monkeypatch):
        backend = make_backend(
            monkeypatch, mailjet_settings, result=FakeResult(400, {"error": "bad"})
        )
        backend.fail_silently = True
        msg = EmailMessage(
            subject="Bad",
            body="Body",
            to=["to@example.com"],
        )
        assert backend.send_messages([msg]) == 0

    def test_api_exception_raises_when_not_silent(self, mailjet_settings, monkeypatch):
        class _Client:
            def __init__(self, *args, **kwargs):
                self.send = FakeSendAPI(RuntimeError("network"))

        monkeypatch.setattr("apps.core.mailjet_backend.Client", _Client)
        backend = MailjetBackend()

        msg = EmailMessage(subject="Boom", body="X", to=["to@example.com"])
        with pytest.raises(RuntimeError):
            backend.send_messages([msg])

    def test_api_exception_silent_returns_zero(self, mailjet_settings, monkeypatch):
        class _Client:
            def __init__(self, *args, **kwargs):
                self.send = FakeSendAPI(RuntimeError("network"))

        monkeypatch.setattr("apps.core.mailjet_backend.Client", _Client)
        backend = MailjetBackend(fail_silently=True)

        msg = EmailMessage(subject="Boom", body="X", to=["to@example.com"])
        assert backend.send_messages([msg]) == 0

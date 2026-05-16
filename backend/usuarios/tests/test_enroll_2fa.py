"""Tests del flujo de enrolamiento TOTP."""
from __future__ import annotations

import pytest
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice

from .conftest import current_totp


@pytest.mark.django_db
class TestEnroll2FA:

    def test_get_creates_unconfirmed_device_and_shows_qr(self, client_authenticated, user):
        resp = client_authenticated.get(reverse("enroll_2fa"))
        assert resp.status_code == 200
        assert b"data:image/png;base64," in resp.content
        device = TOTPDevice.objects.get(user=user, name="default")
        assert device.confirmed is False

    def test_post_with_valid_token_confirms_device(self, client_authenticated, user):
        # Generar device primero (vía GET)
        client_authenticated.get(reverse("enroll_2fa"))
        device = TOTPDevice.objects.get(user=user, name="default")
        valid_token = current_totp(device)

        resp = client_authenticated.post(
            reverse("enroll_2fa"), data={"token": valid_token}
        )
        assert resp.status_code == 302
        assert resp.url == reverse("backup_codes")

        device.refresh_from_db()
        assert device.confirmed is True
        user.refresh_from_db()
        assert user.is_2fa_enabled is True
        assert user.email_verified_at is not None

    def test_post_with_invalid_token_keeps_device_unconfirmed(self, client_authenticated, user):
        client_authenticated.get(reverse("enroll_2fa"))
        resp = client_authenticated.post(
            reverse("enroll_2fa"), data={"token": "000000"}
        )
        assert resp.status_code == 200
        device = TOTPDevice.objects.get(user=user, name="default")
        assert device.confirmed is False

    def test_token_cannot_be_replayed(self, client_authenticated, user):
        client_authenticated.get(reverse("enroll_2fa"))
        device = TOTPDevice.objects.get(user=user, name="default")
        token = current_totp(device)

        # Primera vez: válido y confirma device.
        resp1 = client_authenticated.post(reverse("enroll_2fa"), data={"token": token})
        assert resp1.status_code == 302

        # Segunda vez con el mismo token: django-otp lo rechaza (anti-replay vía last_t).
        device.refresh_from_db()
        # Ya estaba confirmado; el verify_token interno usa last_t y no acepta repetición.
        assert device.verify_token(token) is False

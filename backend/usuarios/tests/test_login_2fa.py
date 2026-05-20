"""Tests del flujo de login con y sin 2FA + rate limiting."""
from __future__ import annotations

import pytest
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice

from .conftest import current_totp
from .factories import UserFactory


@pytest.mark.django_db
class TestLoginWithout2FA:

    def test_login_without_2fa_logs_in_directly(self, client):
        UserFactory(email="nofa@mindmetrics.test", password="S3guroPassw0rd!")
        resp = client.post(
            reverse("login_step1"),
            data={"email": "nofa@mindmetrics.test", "password": "S3guroPassw0rd!"},
        )
        assert resp.status_code == 302
        assert resp.url == reverse("dashboard")


@pytest.mark.django_db
class TestLoginWith2FA:

    def test_step1_redirects_to_step2_when_2fa_enabled(self, client, user_with_2fa):
        resp = client.post(
            reverse("login_step1"),
            data={"email": user_with_2fa.email, "password": "S3guroPassw0rd!"},
        )
        assert resp.status_code == 302
        assert resp.url == reverse("login_step2")

    def test_step2_accepts_valid_totp(self, client, user_with_2fa):
        # Etapa 1
        client.post(
            reverse("login_step1"),
            data={"email": user_with_2fa.email, "password": "S3guroPassw0rd!"},
        )
        device = TOTPDevice.objects.get(user=user_with_2fa)
        token = current_totp(device)
        # Etapa 2
        resp = client.post(reverse("login_step2"), data={"token": token})
        assert resp.status_code == 302
        assert resp.url == reverse("dashboard")

    def test_step2_rejects_invalid_token(self, client, user_with_2fa):
        client.post(
            reverse("login_step1"),
            data={"email": user_with_2fa.email, "password": "S3guroPassw0rd!"},
        )
        resp = client.post(reverse("login_step2"), data={"token": "000000"})
        assert resp.status_code == 200
        assert b"incorrecto" in resp.content.lower() or b"inv\xc3\xa1lid" in resp.content

    def test_step2_redirects_to_step1_if_no_pending_user(self, client):
        resp = client.get(reverse("login_step2"))
        assert resp.status_code == 302
        assert resp.url == reverse("login_step1")


@pytest.mark.django_db
class TestBackupCodes:

    def test_backup_code_consumed_after_use(self, client, user_with_backup_codes):
        client.post(
            reverse("login_step1"),
            data={"email": user_with_backup_codes.email, "password": "S3guroPassw0rd!"},
        )
        resp = client.post(reverse("login_step2"), data={"token": "back0001ab"})
        assert resp.status_code == 302
        assert resp.url == reverse("dashboard")

        # El token consumido no debe servir una segunda vez.
        client.logout()
        client.post(
            reverse("login_step1"),
            data={"email": user_with_backup_codes.email, "password": "S3guroPassw0rd!"},
        )
        resp2 = client.post(reverse("login_step2"), data={"token": "back0001ab"})
        assert resp2.status_code == 200


@pytest.mark.django_db
@pytest.mark.integration
class TestRateLimiting:

    def test_axes_blocks_after_failure_limit(self, client, settings):
        """6 intentos fallidos consecutivos deben disparar django-axes (limit=5)."""
        UserFactory(email="rate@mindmetrics.test", password="S3guroPassw0rd!")
        for _ in range(settings.AXES_FAILURE_LIMIT + 1):
            client.post(
                reverse("login_step1"),
                data={"email": "rate@mindmetrics.test", "password": "wrong"},
            )
        # Tras superar el límite, el siguiente intento debe ser bloqueado (403).
        resp = client.post(
            reverse("login_step1"),
            data={"email": "rate@mindmetrics.test", "password": "S3guroPassw0rd!"},
        )
        assert resp.status_code in (403, 200)
        # 403 si axes bloquea con su backend; 200 si renderiza template lockout.

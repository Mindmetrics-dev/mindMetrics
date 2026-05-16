"""Fixtures compartidos para los tests de usuarios."""
from __future__ import annotations

import pytest
from django.test import Client
from django_otp.oath import totp
from django_otp.plugins.otp_totp.models import TOTPDevice

from .factories import (
    ConfirmedTOTPDeviceFactory,
    StaticDeviceFactory,
    UserFactory,
    add_static_token,
)


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def user_with_2fa(db):
    """Usuario con 2FA habilitado + TOTPDevice confirmado."""
    u = UserFactory(is_2fa_enabled=True)
    ConfirmedTOTPDeviceFactory(user=u)
    return u


@pytest.fixture
def user_with_backup_codes(db):
    """Usuario con 2FA y backup codes preconfigurados."""
    u = UserFactory(is_2fa_enabled=True)
    ConfirmedTOTPDeviceFactory(user=u)
    sd = StaticDeviceFactory(user=u)
    add_static_token(sd, token="back0001ab")
    add_static_token(sd, token="back0002cd")
    return u


@pytest.fixture
def client_authenticated(client: Client, user):
    client.force_login(user)
    return client


def current_totp(device: TOTPDevice) -> str:
    """Calcula el código TOTP actual a partir del device (para tests)."""
    return f"{totp(device.bin_key, step=device.step, t0=device.t0, digits=device.digits):0{device.digits}d}"


@pytest.fixture
def totp_code_for():
    """Factory que retorna el token TOTP actual de un device dado."""
    return current_totp

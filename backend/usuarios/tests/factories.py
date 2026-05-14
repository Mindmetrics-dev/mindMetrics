"""Factories de pytest para usuarios y dispositivos OTP."""
from __future__ import annotations

import factory
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@mindmetrics.test")
    username = factory.Sequence(lambda n: f"user{n}")
    first_name = "Test"
    last_name = "User"
    is_active = True

    @factory.post_generation
    def password(self, create: bool, extracted: str | None, **kwargs):
        pwd = extracted or "S3guroPassw0rd!"
        self.set_password(pwd)
        if create:
            self.save()


class ConfirmedTOTPDeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TOTPDevice

    user = factory.SubFactory(UserFactory)
    name = "default"
    confirmed = True


class StaticDeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StaticDevice

    user = factory.SubFactory(UserFactory)
    name = "backup-codes"
    confirmed = True


def add_static_token(device: StaticDevice, token: str = "abcdef1234") -> StaticToken:
    return StaticToken.objects.create(device=device, token=token)

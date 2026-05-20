"""Tests del flujo de registro."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from .factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestSignup:

    def test_signup_get_renders_form(self, client):
        resp = client.get(reverse("signup"))
        assert resp.status_code == 200
        assert b"<form" in resp.content

    def test_signup_success_creates_user_and_redirects_to_enroll(self, client):
        data = {
            "email": "newuser@mindmetrics.test",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password1": "S3guroPassw0rd!",
            "password2": "S3guroPassw0rd!",
        }
        resp = client.post(reverse("signup"), data=data)
        assert resp.status_code == 302
        assert resp.url == reverse("enroll_2fa")
        assert User.objects.filter(email="newuser@mindmetrics.test").exists()

    def test_signup_rejects_duplicate_email(self, client):
        UserFactory(email="dup@mindmetrics.test")
        data = {
            "email": "dup@mindmetrics.test",
            "username": "x", "first_name": "X", "last_name": "Y",
            "password1": "S3guroPassw0rd!",
            "password2": "S3guroPassw0rd!",
        }
        resp = client.post(reverse("signup"), data=data)
        assert resp.status_code == 200
        assert b"Ya existe" in resp.content

    def test_signup_rejects_weak_password(self, client):
        data = {
            "email": "weak@mindmetrics.test",
            "username": "weak", "first_name": "W", "last_name": "K",
            "password1": "12345",
            "password2": "12345",
        }
        resp = client.post(reverse("signup"), data=data)
        assert resp.status_code == 200
        # Validator MinimumLength (10 chars) o CommonPassword se dispara.
        assert not User.objects.filter(email="weak@mindmetrics.test").exists()

    def test_signup_rejects_mismatched_passwords(self, client):
        data = {
            "email": "mm@mindmetrics.test",
            "username": "mm", "first_name": "M", "last_name": "M",
            "password1": "S3guroPassw0rd!",
            "password2": "0troPassw0rd!",
        }
        resp = client.post(reverse("signup"), data=data)
        assert resp.status_code == 200
        assert b"no coinciden" in resp.content

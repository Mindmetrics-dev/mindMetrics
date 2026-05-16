/* ============================================================
   Ruta: Frontend/static/js/main.js
   MindMetrics - Interacciones globales del frontend
   ============================================================ */

(function () {
    'use strict';

    /* ---------- 1. Mobile navbar toggle ---------- */
    function initNavbarToggle() {
        const toggle = document.querySelector('[data-navbar-toggle]');
        const nav = document.querySelector('[data-navbar-nav]');
        if (!toggle || !nav) return;

        toggle.addEventListener('click', () => {
            nav.classList.toggle('is-open');
            const expanded = nav.classList.contains('is-open');
            toggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        });
    }

    /* ---------- 2. OTP inputs (verificación 2FA) ---------- */
    function initOtpInputs() {
        const inputs = document.querySelectorAll('[data-otp-input]');
        if (inputs.length === 0) return;

        inputs.forEach((input, index) => {
            input.addEventListener('input', (e) => {
                const value = e.target.value.replace(/\D/g, '');
                e.target.value = value.slice(0, 1);
                if (value && index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }
                syncOtpHidden(inputs);
            });

            input.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace' && !e.target.value && index > 0) {
                    inputs[index - 1].focus();
                }
            });

            input.addEventListener('paste', (e) => {
                e.preventDefault();
                const text = (e.clipboardData || window.clipboardData)
                    .getData('text').replace(/\D/g, '').slice(0, inputs.length);
                [...text].forEach((digit, i) => {
                    if (inputs[i]) inputs[i].value = digit;
                });
                if (inputs[Math.min(text.length, inputs.length - 1)]) {
                    inputs[Math.min(text.length, inputs.length - 1)].focus();
                }
                syncOtpHidden(inputs);
            });
        });
    }

    function syncOtpHidden(inputs) {
        const hidden = document.querySelector('[data-otp-hidden]');
        if (!hidden) return;
        hidden.value = Array.from(inputs).map(i => i.value).join('');
    }

    /* ---------- 3. Form submit con confirmación de password ---------- */
    function initRegisterValidation() {
        const form = document.querySelector('[data-register-form]');
        if (!form) return;

        form.addEventListener('submit', (e) => {
            const pwd = form.querySelector('[name="password"]');
            const confirm = form.querySelector('[name="password_confirm"]');
            if (pwd && confirm && pwd.value !== confirm.value) {
                e.preventDefault();
                alert('Las contraseñas no coinciden.');
                confirm.focus();
            }
        });
    }

    /* ---------- 4. Bootstrap ---------- */
    document.addEventListener('DOMContentLoaded', () => {
        initNavbarToggle();
        initOtpInputs();
        initRegisterValidation();
    });
})();

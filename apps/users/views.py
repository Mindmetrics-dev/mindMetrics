from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'

    def form_valid(self, form):
        # Lógica que se ejecuta cuando el correo y contraseña son correctos
        usuario = form.get_user()
        
        # Validación del Consentimiento Informado antes de dejarlo pasar
        if not usuario.consentimiento_aceptado:
            # Lo redirigimos a la vista para firmar el consentimiento
            return redirect('users:consentimiento')
        return super().form_valid(form)
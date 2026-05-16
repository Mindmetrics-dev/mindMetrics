from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import PerfilForm


@login_required(login_url='login_step1')
def perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Tu perfil se actualizó correctamente.")
            return redirect('perfil')
        else:
            messages.error(request, "❌ Por favor corrige los errores del formulario.")
    else:
        form = PerfilForm(instance=request.user)

    return render(request, 'perfil.html', {'form': form})

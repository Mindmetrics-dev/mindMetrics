from django.urls import path
from .views import CustomLoginView

app_name = 'users'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    # Ruta temporal para que el redirect del view no falle
    path('consentimiento/', lambda r: r.write("Marcar la casilla "), name='consentimiento'),
]
# usuarios/models.py
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Perfil(models.Model):
    usuario = models.OneToOneField( settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    edad = models.IntegerField(null=True, blank=True)
    estado_civil = models.CharField(max_length=50, blank=True, null=True)
    en_tratamiento = models.CharField(max_length=10, blank=True, null=True)
    detalle_tratamiento = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"
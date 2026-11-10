from django.db import models


class Usuario(models.Model):
    """Referencia local de usuarios para trazabilidad y auditoria."""

    usuario_id = models.BigAutoField(primary_key=True)
    entra_object_id = models.CharField(max_length=150, unique=True)
    username = models.CharField(max_length=120, null=True, blank=True)
    nombre = models.CharField(max_length=200)
    correo = models.EmailField(max_length=254)
    estado = models.CharField(max_length=30)
    fecha_creacion = models.DateTimeField()
    fecha_ultimo_acceso = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "usuario"

    def __str__(self):
        return self.nombre

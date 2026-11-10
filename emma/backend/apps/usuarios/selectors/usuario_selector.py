"""Read queries for users."""

from backend.apps.usuarios.models import Usuario


class UsuarioSelector:
    @staticmethod
    def obtener_base():
        return Usuario.objects.order_by("nombre", "usuario_id")

    @staticmethod
    def obtener_detalle(usuario_id: int):
        return UsuarioSelector.obtener_base().filter(usuario_id=usuario_id).first()

    @staticmethod
    def obtener_por_entra_object_id(entra_object_id: str):
        return UsuarioSelector.obtener_base().filter(entra_object_id=entra_object_id).first()

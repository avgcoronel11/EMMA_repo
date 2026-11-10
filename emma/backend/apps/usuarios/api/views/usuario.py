"""Views for user API endpoints."""

from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.compartido.api.filters import apply_ordering, apply_search
from backend.apps.compartido.api.pagination import ContractPaginationMixin
from backend.apps.usuarios.api.serializers import UsuarioSerializer
from backend.apps.usuarios.selectors.usuario_selector import UsuarioSelector


class UsuarioListView(ContractPaginationMixin, APIView):
    serializer_class = UsuarioSerializer

    def get(self, request):
        usuarios = UsuarioSelector.obtener_base()
        estado = request.query_params.get("estado")
        if estado:
            usuarios = usuarios.filter(estado__iexact=estado)

        search = request.query_params.get("search") or request.query_params.get("q")
        usuarios = apply_search(
            usuarios,
            search,
            ["nombre", "correo", "username", "entra_object_id", "estado"],
        )
        usuarios = apply_ordering(
            usuarios,
            request.query_params.get("ordering"),
            {"usuario_id", "nombre", "correo", "username", "estado", "fecha_creacion", "fecha_ultimo_acceso"},
        )
        return self.paginated_response(usuarios, UsuarioSerializer)


class UsuarioDetailView(APIView):
    serializer_class = UsuarioSerializer

    def get(self, request, usuario_id: int):
        usuario = UsuarioSelector.obtener_detalle(usuario_id)
        if usuario is None:
            raise NotFound("Usuario no encontrado.")
        return Response(UsuarioSerializer(usuario).data)

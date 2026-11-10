from django.db.models.deletion import ProtectedError
from django.test import RequestFactory, SimpleTestCase
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from backend.apps.compartido.api.exceptions import api_exception_handler


class ApiExceptionHandlerTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_error_inesperado_oculta_detalle_tecnico(self):
        request = self.factory.get("/api/v1/demo/")

        with self.assertLogs("backend.apps.compartido.api.exceptions", level="ERROR"):
            response = api_exception_handler(
                ValueError("detalle tecnico sensible"),
                {"request": request},
            )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data["error"]["codigo"], "ERROR_INTERNO")
        self.assertEqual(response.data["error"]["mensaje"], "Ocurrio un error inesperado.")
        self.assertEqual(response.data["error"]["detalles"], {})

    def test_protected_error_responde_conflicto(self):
        request = self.factory.delete("/api/v1/adjuntos/1/")
        error = ProtectedError("protegido", [])

        response = api_exception_handler(error, {"request": request})

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["error"]["codigo"], "REGLA_NEGOCIO")
        self.assertIn("detail", response.data["error"]["detalles"])


class AuditoriaApiPermissionTests(APITestCase):
    def test_auditoria_exige_autenticacion_y_es_solo_lectura(self):
        self.assertEqual(self.client.get("/api/v1/auditoria/").status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(User(username="auditoria-pruebas"))
        self.assertEqual(self.client.get("/api/v1/auditoria/").status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get("/api/v1/auditoria/999999/").status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.post("/api/v1/auditoria/", {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

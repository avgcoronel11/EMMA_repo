"""Error-page tests for shared frontend infrastructure."""

from django.test import RequestFactory, SimpleTestCase, override_settings

from core.views import error_500


class ErrorPagesTests(SimpleTestCase):
    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_404_personalizado_sin_detalles_tecnicos(self):
        response = self.client.get("/ruta-que-no-existe/")

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Pagina no encontrada", status_code=404)
        self.assertNotContains(response, "Traceback", status_code=404)

    @override_settings(DEBUG=False)
    def test_500_personalizado_sin_detalles_tecnicos(self):
        request = RequestFactory().get("/error/")

        response = error_500(request)

        self.assertEqual(response.status_code, 500)
        self.assertContains(response, "Ocurrio un error inesperado", status_code=500)
        self.assertNotContains(response, "Traceback", status_code=500)

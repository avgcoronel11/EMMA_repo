"""Unit tests for the frontend HTTP client and its error normalization."""

from io import BytesIO
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from core.api_client import _build_url, _normalize_error_payload, delete_json, patch_json, post_json, request_json
from core.errors import ApiClientError, form_errors_from_api, to_user_message


class ApiClientUnitariosTests(SimpleTestCase):
    @override_settings(API_BASE_URL="https://api.example/v1/", API_BEARER_TOKEN="fallback")
    def test_construye_url_y_token_sin_repetir_contratos(self):
        self.assertEqual(_build_url("/riesgos/", {"search": "fraude", "page": None}), "https://api.example/v1/riesgos/?search=fraude")

        class Respuesta:
            def read(self):
                return b'{"ok": true}'

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        with patch("core.api_client.urlopen", return_value=Respuesta()) as urlopen:
            self.assertEqual(request_json("post", "riesgos", data={"nombre": "R"}), {"ok": True})
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer fallback")
        self.assertEqual(request.data, b'{"nombre": "R"}')

    def test_normaliza_http_error_red_e_invalido_json(self):
        error_http = HTTPError("https://api.example", 400, "Bad", {}, BytesIO(b'{"nombre": ["Requerido"]}'))
        with patch("core.api_client.urlopen", side_effect=error_http):
            with self.assertRaises(ApiClientError) as capturada:
                request_json("GET", "riesgos")
        self.assertEqual(capturada.exception.error["codigo"], "VALIDACION")
        self.assertEqual(capturada.exception.error["detalles"], {"nombre": ["Requerido"]})

        with patch("core.api_client.urlopen", side_effect=URLError("sin red")):
            with self.assertRaises(ApiClientError) as capturada:
                request_json("GET", "riesgos")
        self.assertEqual(capturada.exception.status_code, None)
        self.assertEqual(capturada.exception.error["codigo"], "ERROR_INTERNO")

    def test_mensajes_y_errores_de_formulario_tienen_fallback_seguro(self):
        error = ApiClientError(status_code=403, payload={})
        self.assertEqual(to_user_message(error), "No tienes permisos para realizar esta accion.")
        self.assertEqual(form_errors_from_api(error), {"__all__": ["No tienes permisos para realizar esta accion."]})
        self.assertEqual(_normalize_error_payload(404, "no-json")["error"]["codigo"], "NO_ENCONTRADO")

    def test_fallbacks_de_error_y_wrappers_preservan_el_contrato(self):
        for status, esperado in ((400, "La informacion enviada no es valida."), (401, "La sesion no esta autorizada para consultar esta informacion."), (404, "El recurso solicitado no existe."), (500, "La API no pudo procesar la solicitud."), (None, "No fue posible comunicarse con la API.")):
            with self.subTest(status=status):
                self.assertEqual(to_user_message(ApiClientError(status_code=status)), esperado)

        with patch("core.api_client.request_json", return_value={}) as request:
            post_json("riesgos", {"a": 1})
            patch_json("riesgos/1", {"a": 2})
            delete_json("riesgos/1")
        self.assertEqual([call.args[:2] for call in request.call_args_list], [("POST", "riesgos"), ("PATCH", "riesgos/1"), ("DELETE", "riesgos/1")])

    def test_timeout_e_json_invalido_se_convierten_en_error_de_dominio(self):
        with patch("core.api_client.urlopen", side_effect=TimeoutError):
            with self.assertRaises(ApiClientError) as capturada:
                request_json("GET", "riesgos")
        self.assertEqual(capturada.exception.detail, "Tiempo de espera agotado")

        class RespuestaInvalida:
            def read(self):
                return b"no-json"

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

        with patch("core.api_client.urlopen", return_value=RespuestaInvalida()):
            with self.assertRaises(ApiClientError) as capturada:
                request_json("GET", "riesgos")
        self.assertEqual(capturada.exception.detail, "La API devolvio una respuesta invalida")

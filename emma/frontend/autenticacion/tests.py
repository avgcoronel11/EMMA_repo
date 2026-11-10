from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from django.urls import reverse


class AutenticacionFrontendTests(SimpleTestCase):
    @override_settings(
        ALLOWED_HOSTS=["127.0.0.1", "localhost", "testserver"],
        LOCAL_CANONICAL_HOST="localhost:8000",
        LOCAL_HOST_ALIASES=["127.0.0.1:8000"],
    )
    def test_127_redirige_a_localhost_para_conservar_sesion(self):
        response = self.client.get("/", HTTP_HOST="127.0.0.1:8000")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "http://localhost:8000/")

    def test_inicio_sin_sesion_redirige_al_login(self):
        response = self.client.get("/inicio/")

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])
        self.assertIn("next=%2Finicio%2F", response["Location"])

    def test_login_muestra_boton_de_microsoft(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Iniciar sesion con Microsoft")

    def test_iniciar_sesion_redirige_a_microsoft(self):
        flow = {"auth_uri": "https://login.microsoftonline.com/demo"}

        with patch("autenticacion.views.iniciar_flujo_login", return_value=flow):
            response = self.client.get("/auth/login/?next=/riesgos/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], flow["auth_uri"])
        self.assertEqual(self.client.session["auth_next"], "/riesgos/")
        self.assertEqual(self.client.session["auth_flow"], flow)

    def test_callback_guarda_token_y_usuario(self):
        session = self.client.session
        session["auth_flow"] = {"state": "abc"}
        session.save()

        result = {
            "access_token": "token-prueba",
            "expires_in": 3600,
            "id_token_claims": {
                "name": "Usuario Prueba",
                "preferred_username": "usuario@example.com",
                "oid": "oid-prueba",
            },
        }

        with patch("autenticacion.views.completar_flujo_login", return_value=result):
            response = self.client.get("/auth/callback/?code=123&state=abc")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("inicio"))
        self.assertEqual(self.client.session["access_token"], "token-prueba")
        self.assertEqual(self.client.session["usuario"]["oid"], "oid-prueba")

    def test_callback_sin_slash_guarda_token_y_usuario(self):
        session = self.client.session
        session["auth_flow"] = {"state": "abc"}
        session.save()

        result = {
            "access_token": "token-prueba",
            "expires_in": 3600,
            "id_token_claims": {
                "name": "Usuario Prueba",
                "preferred_username": "usuario@example.com",
                "oid": "oid-prueba",
            },
        }

        with patch("autenticacion.views.completar_flujo_login", return_value=result):
            response = self.client.get("/auth/callback?code=123&state=abc")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("inicio"))
        self.assertEqual(self.client.session["access_token"], "token-prueba")

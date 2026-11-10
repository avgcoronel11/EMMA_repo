"""Unit tests for Matrix rules that do not require PostgreSQL."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from backend.apps.riesgos.services.control_service import _efectividad, recalcular_evaluacion
from backend.apps.riesgos.services.historico_matriz_service import BACKFILL, OPERACION, _next
from backend.apps.riesgos.services.valoracion.impacto import DIMENSIONES_IMPACTO, calcular_impacto_mayor
from backend.apps.riesgos.services.valoracion.probabilidad import _nivel_por_texto, _probabilidad_historica
from backend.apps.riesgos.services.valoracion.residual import _nivel_residual, _promedios_por_tipo
from backend.apps.riesgos.services.valoracion.severidad import calcular_severidad
from backend.apps.riesgos.services.valoracion.utils import extraer_nivel, normalizar_concatenado, normalizar_texto


class ValoracionUnitariaTests(SimpleTestCase):
    def test_historica_rechaza_nulos_y_valores_invalidos(self):
        for eventos, poblacion in ((None, 1), (1, None), (-1, 1), (1, 0)):
            with self.subTest(eventos=eventos, poblacion=poblacion):
                with self.assertRaises(ValidationError):
                    _probabilidad_historica(eventos_riesgo=eventos, poblacion_expuesta=poblacion)

    def test_niveles_textuales_normalizan_y_rechazan_valores_no_aprobados(self):
        self.assertEqual(_nivel_por_texto(" 5 - Diaria ", componente="exposicion"), 5)
        self.assertEqual(_nivel_por_texto("moderada", componente="ocurrencia"), 3)
        with self.assertRaises(ValidationError):
            _nivel_por_texto("desconocido", componente="ocurrencia")

    def test_impacto_mayor_exige_exactamente_las_dimensiones_aprobadas(self):
        impactos = {dimension: "1" for dimension in DIMENSIONES_IMPACTO}
        with patch(
            "backend.apps.riesgos.services.valoracion.impacto.calcular_impacto",
            side_effect=lambda *, tipo_impacto, nivel, **_: {"nivel": 4 if tipo_impacto == "Financiero" else 1, "tipo_impacto": tipo_impacto},
        ):
            self.assertEqual(calcular_impacto_mayor(impactos=impactos)["tipo_impacto"], "Financiero")
        with self.assertRaises(ValidationError):
            calcular_impacto_mayor(impactos={"Financiero": "1"})

    @patch("backend.apps.riesgos.services.valoracion.severidad.reglas_vigentes")
    def test_severidad_usa_concatenado_normalizado(self, reglas_vigentes):
        regla = SimpleNamespace(severidad="Alta", concatenado="MuyAltaMayor", version="v1")
        reglas_vigentes.return_value.filter.return_value.first.return_value = regla
        resultado = calcular_severidad(probabilidad_etiqueta="Muy Alta", impacto_etiqueta="Mayor")
        self.assertEqual(resultado, {"severidad": "Alta", "concatenado": "MuyAltaMayor", "version": "v1"})

    def test_utilidades_de_valoracion_son_deterministas(self):
        self.assertEqual(normalizar_texto("  dato\t de   prueba "), "dato de prueba")
        self.assertIsNone(normalizar_texto("  "))
        self.assertEqual(normalizar_concatenado("Muy Alta", "Mayor"), "MuyAltaMayor")
        self.assertEqual(extraer_nivel("Nivel 4 - Alta"), 4)
        self.assertIsNone(extraer_nivel("sin nivel"))


class ControlEHistoricoUnitarioTests(SimpleTestCase):
    def test_evaluacion_incompleta_no_modifica_resultados(self):
        control = SimpleNamespace(d1="Sí", d2=None, d3="Sí", d4="Sí", o1="No", o2="Sí", o3="Sí", o4="Sí", o5="NA")
        self.assertFalse(recalcular_evaluacion(control))
        self.assertFalse(hasattr(control, "efectividad"))

    def test_efectividad_normaliza_claves_y_mantiene_fallback_debil(self):
        self.assertEqual(_efectividad(" preventivo ", "Automatizado", "No"), "Fuerte")
        self.assertEqual(_efectividad("Preventivo", "Automático", "No"), "Débil")
        self.assertEqual(_efectividad("Preventivo", "Automatizado", "Sí"), "Débil")
        self.assertEqual(_efectividad("otro", "Manual", "No"), "Débil")

    def test_promedios_distinguen_controles_sin_codigo_y_lista_vacia(self):
        controles = [
            SimpleNamespace(codigo_control=None, tipo_control="Preventivo", efectividad="Fuerte", estado="Activo"),
            SimpleNamespace(codigo_control=None, tipo_control="Preventivo", efectividad="Moderado", estado="Activo"),
        ]
        promedios, cantidad = _promedios_por_tipo(controles)
        self.assertEqual(cantidad, 2)
        self.assertEqual(str(promedios["preventivo"]), "1")
        self.assertEqual(_promedios_por_tipo([]), ({}, 0))

    def test_nivel_residual_valida_y_respeta_limites(self):
        self.assertEqual(_nivel_residual(1, 2), 1)
        self.assertEqual(_nivel_residual(5, -2), 5)
        with self.assertRaises(ValidationError):
            _nivel_residual(0, 1)

    def test_siguiente_version_y_origenes_historicos(self):
        queryset = MagicMock()
        queryset.aggregate.return_value = {"max_version": 4}
        self.assertEqual(_next(queryset), 5)
        queryset.aggregate.return_value = {"max_version": None}
        self.assertEqual(_next(queryset), 1)
        self.assertEqual((OPERACION, BACKFILL), ("OPERACION", "BACKFILL"))

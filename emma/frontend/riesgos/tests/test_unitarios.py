"""Pure form and presentation-helper tests for the Risk Matrix frontend."""

from django.test import RequestFactory, SimpleTestCase

from riesgos.forms import RiesgoCreateForm
from riesgos.matriz_severidad import COLOR_MAP_DATA, COLORES, preparar_matriz_severidad
from riesgos.views import _api_todos, _fetch_riesgos, _filter_form_and_params, _inicial_edicion, _page_number


class RiesgosUnitariosFrontendTests(SimpleTestCase):
    def test_payload_de_valoracion_esta_completo_o_no_se_envia(self):
        configuracion = {
            "version": "v1",
            "exposicion": [{"valor": "1 - Anual", "etiqueta": "Anual"}],
            "complejidad": [{"valor": "Baja", "etiqueta": "Baja"}],
            "condiciones_entorno": [{"valor": "Estable", "etiqueta": "Estable"}],
            "grado_ocurrencia": [{"valor": "1 - Baja", "etiqueta": "Baja"}],
            "impactos": [{"nombre": nombre, "opciones": [{"valor": "1", "etiqueta": "Inferior"}]} for nombre in RiesgoCreateForm.CAMPOS_IMPACTO.values()],
        }
        data = {"nombre_riesgo": "Prueba", "valoracion_version": "v1", "exposicion": "1 - Anual", "complejidad": "Baja", "condiciones_entorno": "Estable", "grado_ocurrencia": "1 - Baja", "eventos_riesgo": 0, "poblacion_expuesta": 1}
        data.update({campo: "1" for campo in RiesgoCreateForm.CAMPOS_IMPACTO})
        form = RiesgoCreateForm(data, configuracion=configuracion)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.to_api_payload()["valoracion"]["version"], "v1")

        incompleto = RiesgoCreateForm({"nombre_riesgo": "Prueba", "eventos_riesgo": 1}, configuracion=configuracion)
        self.assertFalse(incompleto.is_valid())
        self.assertIn("exposicion", incompleto.errors)

    def test_filtros_paginacion_y_normalizacion_de_lista_son_aislables(self):
        request = RequestFactory().get("/riesgos/?search=fraude&page=2")
        form, params = _filter_form_and_params(request)
        self.assertTrue(form.is_valid())
        self.assertEqual(params, {"search": "fraude", "page": "2"})
        self.assertEqual(_page_number("https://api.example/riesgos/?search=f&page=3"), "3")
        self.assertIsNone(_page_number(None))

        from unittest.mock import patch
        with patch("riesgos.views.get_json", return_value=[{"riesgo_id": 1}]):
            self.assertEqual(_fetch_riesgos({})["count"], 1)
        with patch("riesgos.views.get_json", return_value=None):
            self.assertEqual(_fetch_riesgos({})["results"], [])

    def test_precarga_solo_ultima_version_historica(self):
        riesgo = {"nombre_riesgo": "Riesgo", "estado": "Activo"}
        valoraciones = [
            {"version": 1, "datos_entrada": {"probabilidad": {"exposicion": "vieja"}}},
            {"version": 2, "datos_entrada": {"version": "v2", "probabilidad": {"exposicion": "nueva"}}},
        ]
        inicial = _inicial_edicion(riesgo, valoraciones)
        self.assertEqual(inicial["exposicion"], "nueva")
        self.assertEqual(inicial["valoracion_version"], "v2")

    def test_matriz_usa_niveles_persistidos_y_colores_originales(self):
        matriz = preparar_matriz_severidad({
            "prob_inherente_nivel": 1, "impacto_inherente_nivel": 5,
            "prob_residual_nivel": 5, "impacto_residual_nivel": 1,
        })
        self.assertTrue(matriz["valida"])
        self.assertEqual(COLOR_MAP_DATA[0], (1, 1, 2, 3, 4))
        self.assertEqual(COLOR_MAP_DATA[4], (1, 2, 3, 4, 4))
        self.assertEqual(COLORES, {1: "#2196F3", 2: "#8BC34A", 3: "#FFEB3B", 4: "#F44336"})
        self.assertEqual(matriz["filas"][0]["celdas"][4]["marcadores"][0]["codigo"], "RI")
        self.assertEqual(matriz["filas"][4]["celdas"][0]["marcadores"][0]["codigo"], "RR")

    def test_matriz_pendiente_no_inventa_niveles(self):
        matriz = preparar_matriz_severidad({
            "prob_inherente_nivel": 3, "impacto_inherente_nivel": 0,
            "prob_residual_nivel": None, "impacto_residual_nivel": 3,
        })
        self.assertTrue(matriz["pendiente"])
        self.assertFalse(any(celda["marcadores"] for fila in matriz["filas"] for celda in fila["celdas"]))

    def test_catalogo_paginado_recupera_todas_las_paginas(self):
        from unittest.mock import patch
        with patch("riesgos.views._api_lista", side_effect=[
            {"results": [{"proceso_id": 1}], "next": "?page=2"},
            {"results": [{"proceso_id": 2}], "next": None},
        ]) as api_lista:
            self.assertEqual([item["proceso_id"] for item in _api_todos("procesos", "token")], [1, 2])
        self.assertEqual(api_lista.call_count, 2)

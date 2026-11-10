"""View and form tests for the Risk Matrix frontend."""

from unittest.mock import patch

from django.test import SimpleTestCase

from core.errors import ApiClientError
from riesgos.forms import CausaForm, ControlForm, EvaluacionControlForm, RiesgoCreateForm


class RiesgosFrontendTests(SimpleTestCase):
    def _iniciar_sesion(self):
        session = self.client.session
        session["access_token"] = "token-prueba"
        session["usuario"] = {
            "nombre": "Usuario Prueba",
            "correo": "usuario@example.com",
            "oid": "oid-prueba",
        }
        session.save()

    def test_listado_envia_search_a_la_api(self):
        self._iniciar_sesion()

        with patch("riesgos.views.get_json", return_value={"results": []}) as get_json:
            response = self.client.get("/riesgos/", {"search": "fraude"})

        self.assertEqual(response.status_code, 200)
        get_json.assert_any_call("riesgos", params={"search": "fraude"}, token="token-prueba")

    def test_matriz_muestra_riesgos_causas_y_controles_en_un_solo_workspace(self):
        self._iniciar_sesion()
        pagina_causas = {"count": 1, "results": [{"causa_id": 3, "codigo_causa": "C3", "descripcion_causa": "Causa de prueba", "estado": "Activo"}], "next": None, "previous": None}
        pagina_controles = {"count": 0, "results": [], "next": None, "previous": None}
        with (
            patch("riesgos.views.get_json", return_value={"results": []}),
            patch("riesgos.views._api_lista", side_effect=[pagina_causas, pagina_controles]),
            patch("riesgos.views._opciones_control", return_value=([], [], [], [], [], [])),
            patch("riesgos.views._opciones_riesgo", return_value={}),
        ):
            response = self.client.get("/riesgos/", {"modulo": "causas"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Matriz de Riesgos")
        self.assertContains(response, "Controles")
        self.assertContains(response, "Causa de prueba")
        self.assertContains(response, 'id="matriz-riesgos"')
        self.assertContains(response, 'id="matriz-causas"')
        self.assertContains(response, 'id="matriz-controles"')
        self.assertContains(response, 'id="matriz-severidad"')
        self.assertContains(response, "4. Matriz de Severidad del Riesgo")
        self.assertContains(response, "Frente de Riesgos asociado")
        self.assertContains(response, "Sistema / Aplicación / Activo de información")

    def test_busqueda_no_promete_codigo_gr(self):
        self._iniciar_sesion()
        with patch("riesgos.views.get_json", return_value={"results": []}):
            response = self.client.get("/riesgos/")
        self.assertNotContains(response, "Codigo, nombre o subfactor")
        self.assertContains(response, "Nombre, referencia, ciclo, subfactor, proceso o dueño")

    def test_crear_riesgo_envia_payload_y_refresca_listado(self):
        self._iniciar_sesion()

        riesgo = {
            "codigo_riesgo": "R-DEMO-001",
            "nombre_riesgo": "Riesgo creado desde frontend",
            "estado": "Activo",
            "riesgo_homologado": "",
            "severidad_inherente": "",
        }
        data = {"nombre_riesgo": riesgo["nombre_riesgo"], "estado": "Activo"}

        with (
            patch("riesgos.views.post_json", return_value=riesgo) as post_json,
            patch("riesgos.views.get_json", return_value={"results": [riesgo]}),
        ):
            response = self.client.post("/riesgos/crear/", data, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        post_json.assert_called_once_with("riesgos", data, token="token-prueba")
        self.assertContains(response, "R-DEMO-001")
        self.assertContains(response, "Riesgo creado correctamente.")

    def test_listado_conserva_filtros_y_paginacion(self):
        self._iniciar_sesion()
        respuesta = {
            "count": 21,
            "previous": None,
            "next": "http://api.test/api/v1/riesgos/?estado=Activo&page=2",
            "results": [],
        }
        with patch("riesgos.views.get_json", return_value=respuesta) as get_json:
            response = self.client.get("/riesgos/", {"estado": "Activo", "page": "1"})

        self.assertEqual(response.status_code, 200)
        get_json.assert_any_call("riesgos", params={"estado": "Activo", "page": "1"}, token="token-prueba")
        self.assertContains(response, "21 resultados")
        self.assertContains(response, "estado=Activo&page=2")

    def test_paginacion_muestra_anterior_si_api_omite_page_uno(self):
        self._iniciar_sesion()
        respuesta = {"count": 21, "previous": "/api/v1/riesgos/?search=riesgo", "next": None, "results": []}
        with patch("riesgos.views.get_json", return_value=respuesta):
            response = self.client.get("/riesgos/", {"search": "riesgo", "page": "2"})
        self.assertContains(response, "search=riesgo&page=1")

    def test_detalle_muestra_valoraciones_historicas(self):
        self._iniciar_sesion()
        riesgo = {"riesgo_id": 7, "codigo_riesgo": "GR7", "nombre_riesgo": "Prueba", "estado": "Activo", "procesos": [], "causas": [], "controles": []}
        historico = [{"version": 1, "fecha_valoracion": "2026-10-22T10:00:00Z", "severidad_residual": "Alta", "controles": []}]
        with patch("riesgos.views.get_json", side_effect=[riesgo, historico, {}]):
            response = self.client.get("/riesgos/7/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GR7")
        self.assertContains(response, "Versión 1")

    def test_panel_matriz_muestra_ri_y_rr_vigentes(self):
        self._iniciar_sesion()
        riesgo = {
            "riesgo_id": 7, "codigo_riesgo": "GR7", "nombre_riesgo": "Prueba", "estado": "Activo",
            "procesos": [], "causas": [], "controles": [],
            "prob_inherente_nivel": 3, "impacto_inherente_nivel": 4, "severidad_inherente": "Alto",
            "prob_residual_nivel": 2, "impacto_residual_nivel": 1, "severidad_residual": "Bajo",
        }
        with patch("riesgos.views.get_json", return_value=riesgo):
            response = self.client.get("/riesgos/matriz-severidad/", {"riesgo_id": 7})
        self.assertContains(response, "Matriz de Severidad del Riesgo")
        self.assertContains(response, "RI")
        self.assertContains(response, "RR")
        self.assertContains(response, "#2196F3")

    def test_panel_matriz_muestra_estado_pendiente_si_faltan_niveles(self):
        self._iniciar_sesion()
        riesgo = {
            "riesgo_id": 7, "codigo_riesgo": "GR7", "nombre_riesgo": "Prueba", "estado": "Activo",
            "procesos": [], "causas": [], "controles": [],
        }
        with patch("riesgos.views.get_json", return_value=riesgo):
            response = self.client.get("/riesgos/matriz-severidad/", {"riesgo_id": 7})
        self.assertContains(response, "Riesgo pendiente de valoración")

    def test_detalle_muestra_procesos_causas_y_controles_del_api(self):
        self._iniciar_sesion()
        riesgo = {
            "riesgo_id": 7, "codigo_riesgo": "GR7", "nombre_riesgo": "Prueba", "estado": "Activo",
            "procesos": [{"vicepresidencia": "VP prueba", "proceso_nivel0": "Proceso", "proceso_nivel1": "Subproceso", "proceso_nivel2": None, "macroproceso": "Macro", "linea": "Línea"}],
            "causas": [{"causa_id": 7, "codigo_causa": "C7", "descripcion_causa": "Causa visible", "subfactor": "SF", "estado": "Activo"}],
            "controles": [{"control_id": 7, "codigo_control": "CT7", "nombre_control": "Control visible", "tipo_control": "Preventivo", "naturaleza": "Manual", "efectividad": "Fuerte"}],
        }
        with patch("riesgos.views.get_json", side_effect=[riesgo, [], [], {"results": []}, {}]):
            response = self.client.get("/riesgos/7/")
        self.assertContains(response, "VP prueba")
        self.assertContains(response, "Causa visible")
        self.assertContains(response, "Control visible")

    def test_edicion_precarga_las_entradas_de_la_ultima_valoracion(self):
        self._iniciar_sesion()
        riesgo = {
            "riesgo_id": 7, "codigo_riesgo": "GR7", "nombre_riesgo": "Prueba", "estado": "Activo",
            "procesos": [], "causas": [], "controles": [],
        }
        historico = [{
            "version": 2,
            "datos_entrada": {
                "version": "2026.1",
                "probabilidad": {
                    "exposicion": "1 - Anualmente", "complejidad": "Baja",
                    "condiciones_entorno": "Entorno estable",
                    "grado_ocurrencia": "1 - Menos del 1 % de los casos",
                    "eventos_riesgo": 0, "poblacion_expuesta": 10,
                },
                "impacto": {"impactos": {"Impacto Legal": "1"}},
            },
        }]
        configuracion = {
            "version": "2026.1",
            "exposicion": [{"valor": "1 - Anualmente", "etiqueta": "Anual"}],
            "complejidad": [{"valor": "Baja", "etiqueta": "Baja"}],
            "condiciones_entorno": [{"valor": "Entorno estable", "etiqueta": "Estable"}],
            "grado_ocurrencia": [{"valor": "1 - Menos del 1 % de los casos", "etiqueta": "Baja"}],
            "impactos": [{"nombre": "Impacto Legal", "opciones": [{"valor": "1", "etiqueta": "Inferior"}]}],
        }
        with patch("riesgos.views.get_json", side_effect=[riesgo, historico, configuracion]):
            response = self.client.get("/riesgos/7/")

        self.assertContains(response, 'value="1 - Anualmente" selected')
        self.assertContains(response, 'value="Entorno estable" selected')
        self.assertContains(response, 'value="1" selected')

    def test_htmx_muestra_indicador_de_carga(self):
        self._iniciar_sesion()
        with patch("riesgos.views.get_json", return_value={"results": []}):
            response = self.client.get("/riesgos/")
        self.assertContains(response, 'id="riesgos-loading"')
        self.assertContains(response, 'hx-indicator="#riesgos-loading"')

    def test_editar_envia_patch_sin_codigo_gr(self):
        self._iniciar_sesion()
        with patch("riesgos.views.patch_json", return_value={}) as patch_json:
            response = self.client.post("/riesgos/7/editar/", {"nombre_riesgo": "Actualizado"})
        self.assertEqual(response.status_code, 302)
        patch_json.assert_called_once_with("riesgos/7", {"nombre_riesgo": "Actualizado"}, token="token-prueba")

    def test_inactivar_envia_justificacion(self):
        self._iniciar_sesion()
        with patch("riesgos.views.post_json", return_value={}) as post_json:
            response = self.client.post(
                "/riesgos/7/inactivar/",
                {"justificacion": "Depuración", "confirmacion_inactivacion": "on"},
            )
        self.assertEqual(response.status_code, 302)
        post_json.assert_called_once_with("riesgos/7/inactivar", {"justificacion": "Depuración"}, token="token-prueba")

    def test_crear_riesgo_muestra_error_de_api_debajo_del_campo(self):
        self._iniciar_sesion()

        error = ApiClientError(
            status_code=400,
            detail="validacion",
            payload={
                "error": {
                    "codigo": "VALIDACION",
                    "mensaje": "Hay errores en los datos enviados.",
                    "detalles": {
                        "codigo_riesgo": ["Ya existe un riesgo con este codigo."],
                    },
                }
            },
        )
        data = {
            "codigo_riesgo": "R-DUP",
            "nombre_riesgo": "Duplicado",
            "estado": "Activo",
        }

        with (
            patch("riesgos.views.post_json", side_effect=error),
            patch("riesgos.views.get_json", return_value={"results": []}),
        ):
            response = self.client.post("/riesgos/crear/", data, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un riesgo con este codigo.")
        self.assertContains(response, "Hay errores en los datos enviados.")

    def test_editar_muestra_error_general_de_api(self):
        self._iniciar_sesion()
        error = ApiClientError(status_code=500, detail="interno", payload={"error": {"codigo": "ERROR_INTERNO", "mensaje": "La API no pudo procesar la solicitud.", "detalles": {}}})
        riesgo = {"riesgo_id": 7, "codigo_riesgo": "GR7", "nombre_riesgo": "Prueba", "estado": "Activo", "procesos": [], "causas": [], "controles": []}
        with patch("riesgos.views.patch_json", side_effect=error), patch("riesgos.views.get_json", return_value=riesgo):
            response = self.client.post("/riesgos/7/editar/", {"nombre_riesgo": "Actualizado"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "La API no pudo procesar la solicitud.")


class CausasControlesFormsTests(SimpleTestCase):
    def test_estructura_filtra_procesos_y_subprocesos_por_jerarquia_completa(self):
        estructura = [
            {"proceso_id": 1, "vicepresidencia": "VP A", "proceso_nivel0": "Proceso común", "proceso_nivel1": "Subproceso A", "linea": "Línea A", "macroproceso": "Macro A"},
            {"proceso_id": 2, "vicepresidencia": "VP B", "proceso_nivel0": "Proceso común", "proceso_nivel1": "Subproceso B", "linea": "Línea B", "macroproceso": "Macro B"},
            {"proceso_id": 3, "vicepresidencia": "VP A", "proceso_nivel0": "Otro proceso", "proceso_nivel1": "Subproceso C", "linea": "Línea A", "macroproceso": "Macro C"},
        ]
        opciones = {"estructura_procesos": estructura}
        form = RiesgoCreateForm(
            {"nombre_riesgo": "Riesgo", "vicepresidencia": "VP A", "proceso_nivel0": "Proceso común", "proceso_ids": "1"},
            opciones_riesgo=opciones,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.fields["proceso_nivel0"].choices, [("", "Seleccione..."), ("Otro proceso", "Otro proceso"), ("Proceso común", "Proceso común")])
        self.assertEqual(form.fields["proceso_ids"].choices, [("", "Seleccione..."), ("1", "Subproceso A")])
        self.assertEqual(form.to_api_payload()["proceso_ids"], [1])

    def test_estructura_rechaza_subproceso_ajeno_a_proceso_o_vicepresidencia(self):
        estructura = [
            {"proceso_id": 1, "vicepresidencia": "VP A", "proceso_nivel0": "Proceso", "proceso_nivel1": "Subproceso A"},
            {"proceso_id": 2, "vicepresidencia": "VP B", "proceso_nivel0": "Proceso", "proceso_nivel1": "Subproceso B"},
        ]
        form = RiesgoCreateForm(
            {"nombre_riesgo": "Riesgo", "vicepresidencia": "VP A", "proceso_nivel0": "Proceso", "proceso_ids": "2"},
            opciones_riesgo={"estructura_procesos": estructura},
        )

        self.assertFalse(form.is_valid())
        self.assertIn("proceso_ids", form.errors)

    def test_riesgo_serializa_sus_selecciones_propias_y_exige_detalle_eventual(self):
        form = RiesgoCreateForm(
            {
                "nombre_riesgo": "Riesgo de prueba",
                "frente_riesgo_asociado": ["SARO", "Operativo"],
                "checklist_riesgo": ["ABAC"],
                "factor_riesgo_tipo_evento": ["Fraude Interno"],
                "control_cambios": "Nuevo",
                "frecuencia": "Eventual",
                "detalle_frecuencia": "Cuando se materialice el evento",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        payload = form.to_api_payload()
        self.assertEqual(payload["frente_riesgo_asociado"], ["SARO", "Operativo"])
        self.assertEqual(payload["checklist_riesgo"], ["ABAC"])
        self.assertEqual(payload["factor_riesgo_tipo_evento"], ["Fraude Interno"])
        self.assertEqual(payload["detalle_frecuencia"], "Cuando se materialice el evento")

    def test_causa_exige_riesgo_solo_en_creacion(self):
        form = CausaForm({"descripcion_causa": "Causa técnica"}, riesgos=[], require_riesgo=True)
        self.assertFalse(form.is_valid())
        self.assertIn("riesgo_id", form.errors)

    def test_control_generico_es_selector_y_serializa_id(self):
        form = ControlForm(
            {"nombre_control": "Control", "descripcion_control": "Descripción", "riesgo_id": "8", "causa_id": "9", "control_generico_valor_id": "3"},
            riesgos=[{"riesgo_id": 8, "codigo_riesgo": "GR8", "nombre_riesgo": "Riesgo"}],
            causas=[{"causa_id": 9, "codigo_causa": "C9", "descripcion_causa": "Causa"}],
            catalogo=[{"valor_id": 3, "codigo": "CG", "descripcion": "Catálogo activo"}],
            require_context=True,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.payload(include_context=True)["control_generico_valor_id"], 3)

    def test_control_serializa_catalogos_cuentas_y_checklists(self):
        form = ControlForm(
            {
                "nombre_control": "Control", "descripcion_control": "Descripción",
                "sistema_valor_ids": ["7"], "principio_coso_valor_ids": ["8"], "cuenta_ids": ["9"],
                "aserciones": ["Integridad"], "atributos": ["Disponibilidad"], "riesgos_control": ["SARO"],
            },
            sistemas=[{"valor_id": 7, "codigo": "SAP", "descripcion": "SAP"}],
            principios_coso=[{"valor_id": 8, "codigo": "P1", "descripcion": "Principio 1"}],
            cuentas=[{"cuenta_id": 9, "codigo": "1105", "descripcion": "Caja"}],
        )
        self.assertTrue(form.is_valid(), form.errors)
        payload = form.payload()
        self.assertEqual(payload["sistema_valor_ids"], [7])
        self.assertEqual(payload["principio_coso_valor_ids"], [8])
        self.assertEqual(payload["cuenta_ids"], [9])
        self.assertEqual(payload["aserciones"], ["Integridad"])

    def test_evaluacion_no_aplica_formulas_locales(self):
        form = EvaluacionControlForm({"d1": "Sí", "o5": "NA"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.payload(), {"d1": "Sí", "o5": "NA"})


class CausasControlesViewsTests(SimpleTestCase):
    def setUp(self):
        session = self.client.session
        session["access_token"] = "token-prueba"
        session.save()
        self.riesgos = [{"riesgo_id": 1, "codigo_riesgo": "GR1", "nombre_riesgo": "Riesgo técnico"}]
        self.causas = [{"causa_id": 2, "codigo_causa": "C2", "descripcion_causa": "Causa técnica", "estado": "Activo"}]
        self.catalogo = [{"valor_id": 3, "codigo": "CG", "descripcion": "Control genérico"}]

    def test_causas_listado_busqueda_paginacion_vacio_y_loading(self):
        pagina = {"count": 21, "results": [], "previous": None, "next": "http://api.test/?page=2"}
        with patch("riesgos.views._api_lista", return_value=pagina) as api:
            response = self.client.get("/riesgos/causas/", {"search": "fraude"})
        self.assertEqual(response.status_code, 200)
        api.assert_called_once_with("riesgos/causas", "token-prueba", search="fraude", page=None)
        self.assertContains(response, "No hay Causas.")
        self.assertContains(response, 'id="causas-loading"')

    def test_causa_crear_y_error_api(self):
        data = {"descripcion_causa": "Nueva causa", "riesgo_id": "1", "estado": "Activo"}
        with patch("riesgos.views._opciones", return_value=(self.riesgos, self.causas, self.catalogo)), patch("riesgos.views.post_json", return_value={"causa_id": 9, "codigo_causa": "C9"}) as post:
            response = self.client.post("/riesgos/causas/crear/", data)
        self.assertEqual(response.status_code, 302)
        post.assert_called_once()
        error = ApiClientError(status_code=400, detail="invalido", payload={"error": {"codigo": "VALIDACION", "mensaje": "Datos inválidos.", "detalles": {"descripcion_causa": ["Requerida"]}}})
        with patch("riesgos.views._opciones", return_value=(self.riesgos, self.causas, self.catalogo)), patch("riesgos.views.post_json", side_effect=error):
            response = self.client.post("/riesgos/causas/crear/", data)
        self.assertContains(response, "Datos inválidos.")

    def test_causa_detalle_reutilizacion_y_retiro_solo_relacion(self):
        causa = self.causas[0]
        asociados = [self.riesgos[0], {"riesgo_id": 4, "codigo_riesgo": "GR4", "nombre_riesgo": "Segundo riesgo"}]
        with patch("riesgos.views.get_json", side_effect=[causa, asociados]), patch("riesgos.views._opciones", return_value=(self.riesgos, self.causas, self.catalogo)):
            response = self.client.get("/riesgos/causas/2/")
        self.assertContains(response, "Segundo riesgo")
        self.assertContains(response, "La Causa continuará disponible")
        with patch("riesgos.views._causa_context", return_value={"causa": causa, "riesgos_asociados": asociados, "riesgos_opciones": self.riesgos, "form": CausaForm(), "alert": None}), patch("riesgos.views.delete_json", return_value=None) as delete:
            response = self.client.post("/riesgos/causas/2/riesgos/1/retirar/")
        self.assertEqual(response.status_code, 302)
        delete.assert_called_once_with("riesgos/1/causas/2", token="token-prueba")

    def test_controles_listado_busqueda_y_loading(self):
        pagina = {"count": 0, "results": [], "previous": None, "next": None}
        with patch("riesgos.views._api_lista", return_value=pagina) as api:
            response = self.client.get("/riesgos/controles/", {"search": "preventivo"})
        self.assertEqual(response.status_code, 200)
        api.assert_called_once_with("riesgos/controles", "token-prueba", search="preventivo", page=None)
        self.assertContains(response, "No hay Controles.")
        self.assertContains(response, 'id="controles-loading"')

    def test_control_crear_catalogo_y_error_api(self):
        data = {"codigo_control": "CT1", "nombre_control": "Control", "descripcion_control": "Descripción", "riesgo_id": "1", "causa_id": "2", "control_generico_valor_id": "3"}
        opciones_control = (self.riesgos, self.causas, self.catalogo, [], [], [])
        with patch("riesgos.views._opciones_control", return_value=opciones_control), patch("riesgos.views.post_json", return_value={"control_id": 8}) as post:
            response = self.client.post("/riesgos/controles/crear/", data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(post.call_args.args[1]["control_generico_valor_id"], 3)
        error = ApiClientError(status_code=400, detail="catalogo", payload={"error": {"codigo": "VALIDACION", "mensaje": "Catálogo inválido.", "detalles": {"control_generico_valor_id": ["No válido"]}}})
        with patch("riesgos.views._opciones_control", return_value=opciones_control), patch("riesgos.views.post_json", side_effect=error):
            response = self.client.post("/riesgos/controles/crear/", data)
        self.assertContains(response, "Catálogo inválido.")

    def test_evaluacion_envia_respuestas_y_muestra_residual(self):
        control = {"control_id": 8, "codigo_control": "CT8", "nombre_control": "Control", "estado": "Activo"}
        contexto = {"control": control, "causas_asociadas": self.causas, "riesgos_asociados": self.riesgos, "riesgos_opciones": self.riesgos, "causas_opciones": self.causas, "catalogo": self.catalogo, "form": ControlForm(), "evaluacion_form": EvaluacionControlForm(), "alert": None}
        data = {"d1": "Sí", "d2": "Sí", "d3": "Sí", "d4": "Sí", "o1": "No", "o2": "Sí", "o3": "Sí", "o4": "Sí", "o5": "NA"}
        with patch("riesgos.views._control_context", return_value=contexto), patch("riesgos.views.patch_json", return_value={"residual": {"probabilidad": {"nivel": 1}}, "control": control}) as patch_json:
            response = self.client.post("/riesgos/controles/8/evaluar/1/", data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "valoración residual fue actualizada")
        self.assertEqual(patch_json.call_args.args[1], data)

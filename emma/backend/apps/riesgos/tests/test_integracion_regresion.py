"""Integration and regression tests for the Risk Matrix backend."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.db import IntegrityError
from django.test import SimpleTestCase, TestCase
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from backend.apps.catalogos.models import (
    Catalogo,
    CatalogoValor,
    CfgNivelImpacto,
    CfgProbabilidad,
    CfgSeveridad,
    RiesgoGenerico,
)
from backend.apps.compartido.models import EntidadCaracteristica
from backend.apps.procesos.models import CatProceso
from backend.apps.riesgos.models import (
    Causa,
    Control,
    ControlEvaluacionHistorico,
    HistorialRiesgoCausa,
    HistorialRiesgoCausaControl,
    Riesgo,
    RiesgoCausa,
    RiesgoCausaControl,
    RiesgoProceso,
)
from backend.apps.riesgos.selectors.riesgo_selector import RiesgoSelector
from backend.apps.riesgos.services.riesgo_service import RiesgoService
from backend.apps.riesgos.services.control_service import _efectividad, recalcular_evaluacion
from backend.apps.riesgos.services.valoracion.probabilidad import _probabilidad_historica, calcular_probabilidad
from backend.apps.riesgos.services.valoracion.residual import _movimiento, _promedios_por_tipo, calcular_residual


class EmmaFlowFixtureMixin:
    def setUp(self):
        super().setUp()
        if hasattr(self.client, "force_authenticate"):
            self.client.force_authenticate(User(username="riesgos-pruebas"))
        self.catalogo = Catalogo.objects.create(
            codigo_catalogo="PRINCIPIO_COSO",
            nombre="Principio COSO",
            activo=True,
        )
        self.valor_activo = CatalogoValor.objects.create(
            catalogo=self.catalogo,
            descripcion="Ambiente de control",
            activo=True,
            nivel=1,
        )
        CatalogoValor.objects.create(
            catalogo=self.catalogo,
            descripcion="Valor inactivo",
            activo=False,
            nivel=1,
        )
        control_catalogo = Catalogo.objects.create(
            codigo_catalogo="CONTROL_GENERICO",
            nombre="Control generico",
            activo=True,
        )
        self.control_generico = CatalogoValor.objects.create(
            catalogo=control_catalogo,
            codigo="CTR-01",
            descripcion="Control homologado",
            activo=True,
            nivel=1,
        )
        self.riesgo_generico = RiesgoGenerico.objects.create(
            codigo="R1",
            nombre="Fraude interno",
            activo=True,
        )
        RiesgoGenerico.objects.create(codigo="R0", nombre="Inactivo", activo=False)
        self.proceso = CatProceso.objects.create(
            vicepresidencia="VP Riesgo",
            proceso_nivel0="Gestion integral",
            proceso_nivel1="Monitoreo",
            macroproceso="Gobierno",
            linea="Corporativa",
            activo=True,
        )
        CatProceso.objects.create(
            vicepresidencia="VP Riesgo",
            proceso_nivel0="Proceso inactivo",
            activo=False,
        )
        self._crear_reglas_valoracion()

    def _crear_reglas_valoracion(self):
        vigencia = date(2020, 1, 1)
        CfgProbabilidad.objects.create(
            complejidad="Alta", condiciones_entorno="4 - Inestabilidad Política, Económica, Legal, etc",
            nivel="5", probabilidad_inherente="Muy Alta", activo=True, version="test", fecha_inicio_vigencia=vigencia,
        )
        CfgProbabilidad.objects.create(
            complejidad="Media", condiciones_entorno="2 - Estabilidad Política, Económica, Legal, etc",
            nivel="4", probabilidad_inherente="Alta", activo=True, version="test", fecha_inicio_vigencia=vigencia,
        )
        CfgProbabilidad.objects.create(
            complejidad="Baja", condiciones_entorno=None,
            nivel="3", probabilidad_inherente="Moderada", activo=True, version="test", fecha_inicio_vigencia=vigencia,
        )
        for tipo_impacto in (
            "Impacto Legal",
            "Impacto Reputacional",
            "Impacto servicio al cliente",
            "Información",
            "Continuidad",
            "Contagio",
            "Financiero",
        ):
            CfgNivelImpacto.objects.create(
                nivel="3",
                tipo_impacto=tipo_impacto,
                criterio="Criterio de prueba",
                impacto_inherente="Importante",
                activo=True,
                version="test",
                fecha_inicio_vigencia=vigencia,
            )
        CfgSeveridad.objects.create(
            concatenado="AltaImportante",
            severidad="Alta",
            activo=True,
            version="test",
            fecha_inicio_vigencia=vigencia,
        )
        CfgSeveridad.objects.create(
            concatenado="BajaImportante",
            severidad="Moderada",
            activo=True,
            version="test",
            fecha_inicio_vigencia=vigencia,
        )
        CfgSeveridad.objects.create(
            concatenado="MuyBajaImportante",
            severidad="Baja",
            activo=True,
            version="test",
            fecha_inicio_vigencia=vigencia,
        )

    def crear_riesgo_existente(self, codigo="R-001"):
        riesgo = Riesgo.objects.create(
            codigo_riesgo=codigo,
            nombre_riesgo="Riesgo existente",
            riesgo_generico=self.riesgo_generico,
            riesgo_homologado=self.riesgo_generico.nombre,
            dueno_proceso="Dueno de prueba",
            estado="Activo",
        )
        RiesgoProceso.objects.create(riesgo=riesgo, proceso=self.proceso, principal=True)
        Causa.objects.create(
            riesgo=riesgo,
            codigo_causa=f"C-{codigo}",
            descripcion_causa="Causa de prueba",
            estado="Activo",
        )
        Control.objects.create(
            riesgo=riesgo,
            codigo_control=f"CT-{codigo}",
            nombre_control="Control de prueba",
            descripcion_control="Descripcion control",
            estado="Activo",
            control_generico_valor=self.control_generico,
        )
        EntidadCaracteristica.objects.create(
            riesgo=riesgo,
            valor_catalogo=self.valor_activo,
            valor_snapshot=self.valor_activo.descripcion,
            activo=True,
        )
        return riesgo

    def riesgo_payload(self):
        return {
            "nombre_riesgo": "Riesgo creado por API",
            "riesgo_generico_id": self.riesgo_generico.riesgo_generico_id,
            "riesgo_homologado": self.riesgo_generico.nombre,
            "estado": "Activo",
            "proceso_ids": [self.proceso.proceso_id],
            "proceso_principal_id": self.proceso.proceso_id,
            "caracteristicas": [
                {
                    "valor_catalogo_id": self.valor_activo.valor_id,
                    "valor_snapshot": self.valor_activo.descripcion,
                }
            ],
            "valoracion": {
                "version": "test",
                "probabilidad": {
                    "exposicion": "4 - Semanal",
                    "complejidad": "Alta",
                    "condiciones_entorno": "2 - Estabilidad Política, Económica, Legal, etc",
                    "grado_ocurrencia": "3-1 el evento puede ocurrir entre el 5 y 9.99% de los casos",
                    "eventos_riesgo": 0,
                    "poblacion_expuesta": 100,
                },
                "impacto": {
                    "impactos": {
                        "Impacto Legal": "3",
                        "Impacto Reputacional": "3",
                        "Impacto servicio al cliente": "3",
                        "Información": "3",
                        "Continuidad": "3",
                        "Contagio": "3",
                        "Financiero": "3",
                    },
                },
            },
        }


class CatalogosProcesosApiTests(EmmaFlowFixtureMixin, APITestCase):
    def test_consultar_catalogo_devuelve_solo_valores_activos(self):
        response = self.client.get("/api/v1/catalogos/PRINCIPIO_COSO/valores/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["descripcion"], "Ambiente de control")

    def test_consultar_procesos_activos_filtrados_por_vicepresidencia(self):
        response = self.client.get("/api/v1/procesos/", {"vicepresidencia": "VP Riesgo"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["proceso_nivel0"], "Gestion integral")

    def test_consultar_riesgos_genericos_activos(self):
        response = self.client.get("/api/v1/riesgos-genericos/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["codigo"], "R1")


class RiesgosApiTests(EmmaFlowFixtureMixin, APITestCase):
    def test_endpoints_sensibles_de_riesgo_exigen_autenticacion(self):
        riesgo = self.crear_riesgo_existente()
        rutas = (
            ("get", "/api/v1/riesgos/", {}),
            ("post", "/api/v1/riesgos/", {}),
            ("get", f"/api/v1/riesgos/{riesgo.riesgo_id}/", {}),
            ("patch", f"/api/v1/riesgos/{riesgo.riesgo_id}/", {}),
            ("post", f"/api/v1/riesgos/{riesgo.riesgo_id}/inactivar/", {}),
            ("get", f"/api/v1/riesgos/{riesgo.riesgo_id}/valoraciones/", {}),
            ("post", "/api/v1/riesgos/calcular-valoracion/", {}),
            ("post", f"/api/v1/riesgos/{riesgo.riesgo_id}/recalcular-residual/", {}),
        )
        self.client.force_authenticate(user=None)
        for metodo, ruta, payload in rutas:
            respuesta = getattr(self.client, metodo)(ruta, payload, format="json")
            self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN, ruta)

    def test_listar_riesgos_incluye_activos_e_inactivos_por_defecto(self):
        riesgo = self.crear_riesgo_existente()
        inactivo = Riesgo.objects.create(codigo_riesgo="R-INACT", nombre_riesgo="Inactivo", estado="Inactivo")

        response = self.client.get("/api/v1/riesgos/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["riesgo_id"], riesgo.riesgo_id)
        self.assertEqual(response.data["results"][1]["riesgo_id"], inactivo.riesgo_id)

    def test_filtra_por_estado_codigo_y_riesgo_homologado(self):
        riesgo = self.crear_riesgo_existente(codigo="GR25")
        Riesgo.objects.create(
            codigo_riesgo="GR26",
            nombre_riesgo="Otro riesgo",
            riesgo_homologado="Otro homologado",
            estado="Inactivo",
        )

        response = self.client.get(
            "/api/v1/riesgos/",
            {
                "estado": "Activo",
                "codigo_riesgo": "gr25",
                "riesgo_homologado": self.riesgo_generico.nombre,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["riesgo_id"], riesgo.riesgo_id)

    def test_busqueda_por_palabras_clave_aprobadas(self):
        self.crear_riesgo_existente(codigo="R-001")
        Riesgo.objects.create(
            codigo_riesgo="R-002",
            nombre_riesgo="Otro riesgo",
            descripcion_proceso="Palabra distintiva de consulta",
            estado="Activo",
        )

        response = self.client.get("/api/v1/riesgos/", {"search": "distintiva"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["codigo_riesgo"], "R-002")

    def test_filtra_por_estructura_y_dueno_proceso(self):
        riesgo = self.crear_riesgo_existente(codigo="R-ESTRUCTURA")
        otro_proceso = CatProceso.objects.create(
            vicepresidencia="VP Diferente",
            proceso_nivel0="Proceso diferente",
            proceso_nivel1="Subproceso diferente",
            activo=True,
        )
        otro_riesgo = Riesgo.objects.create(
            codigo_riesgo="R-OTRO",
            nombre_riesgo="Otro riesgo",
            dueno_proceso="Otro dueno",
            estado="Activo",
        )
        RiesgoProceso.objects.create(riesgo=otro_riesgo, proceso=otro_proceso, principal=True)

        response = self.client.get(
            "/api/v1/riesgos/",
            {
                "vicepresidencia": "vp riesgo",
                "proceso": "gestion integral",
                "subproceso": "monitoreo",
                "dueno_proceso": "dueno de prueba",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["riesgo_id"], riesgo.riesgo_id)

    def test_listado_usa_paginacion_existente(self):
        for indice in range(3):
            Riesgo.objects.create(
                codigo_riesgo=f"R-PAG-{indice}",
                nombre_riesgo=f"Riesgo paginado {indice}",
                estado="Activo",
            )

        response = self.client.get("/api/v1/riesgos/", {"page_size": 2, "page": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 1)

    def test_obtener_detalle_riesgo(self):
        riesgo = self.crear_riesgo_existente()

        response = self.client.get(f"/api/v1/riesgos/{riesgo.riesgo_id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["codigo_riesgo"], riesgo.codigo_riesgo)
        self.assertEqual(len(response.data["procesos"]), 1)
        self.assertEqual(len(response.data["causas"]), 1)
        self.assertEqual(len(response.data["controles"]), 1)

    def test_crear_riesgo_valido(self):
        Riesgo.objects.create(codigo_riesgo="GR25", nombre_riesgo="Historico GR", estado="Inactivo")

        response = self.client.post("/api/v1/riesgos/", self.riesgo_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Riesgo.objects.count(), 2)
        riesgo = Riesgo.objects.get(codigo_riesgo=response.data["codigo_riesgo"])
        self.assertGreater(riesgo.consecutivo_gr, 25)
        self.assertEqual(riesgo.severidad_inherente, "Alta")
        self.assertEqual(riesgo.prob_residual_nivel, 4)
        self.assertEqual(riesgo.impacto_residual_nivel, 3)
        self.assertEqual(riesgo.severidad_residual, "Alta")
        self.assertEqual(riesgo.riesgo_procesos.count(), 1)
        self.assertEqual(riesgo.caracteristicas.count(), 1)

    def test_rechazar_riesgo_con_datos_invalidos(self):
        response = self.client.post("/api/v1/riesgos/", {"codigo_riesgo": ""}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["codigo"], "VALIDACION")
        self.assertIn("nombre_riesgo", response.data["error"]["detalles"])
        self.assertEqual(Riesgo.objects.count(), 0)

    def test_rechazar_asociacion_de_varios_procesos(self):
        otro_proceso = CatProceso.objects.create(
            vicepresidencia="VP Riesgo",
            proceso_nivel0="Gestion alterna",
            proceso_nivel1="Seguimiento",
            activo=True,
        )
        payload = self.riesgo_payload()
        payload["proceso_ids"] = [self.proceso.proceso_id, otro_proceso.proceso_id]

        response = self.client.post("/api/v1/riesgos/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["codigo"], "VALIDACION")
        self.assertEqual(
            response.data["error"]["detalles"]["proceso_ids"][0],
            "Solo se puede asociar un proceso a cada riesgo.",
        )

    def test_rechazar_codigo_gr_enviado_manualmente(self):
        payload = self.riesgo_payload()
        payload["codigo_riesgo"] = "GR999"

        response = self.client.post("/api/v1/riesgos/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["codigo"], "VALIDACION")
        self.assertEqual(
            response.data["error"]["detalles"]["codigo_riesgo"][0],
            "El codigo GR es generado por el sistema y no se recibe manualmente.",
        )

    def test_calcular_valoracion_sin_guardar(self):
        payload = self.riesgo_payload()["valoracion"]

        response = self.client.post("/api/v1/riesgos/calcular-valoracion/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["probabilidad"]["nivel"], 4)
        self.assertEqual(response.data["impacto"]["nivel"], 3)
        self.assertEqual(response.data["severidad"], "Alta")
        self.assertEqual(Riesgo.objects.count(), 0)

    def test_valoracion_endpoint_creacion_y_edicion_usan_maximo_inherente(self):
        CfgSeveridad.objects.create(
            concatenado="MuyAltaImportante",
            severidad="Crítica",
            activo=True,
            version="test",
            fecha_inicio_vigencia=date(2020, 1, 1),
        )
        valoracion = self.riesgo_payload()["valoracion"]
        valoracion["probabilidad"].update(
            {
                "exposicion": "1 - Anualmente",
                "complejidad": "Baja",
                "condiciones_entorno": "2 - Estabilidad Política, Económica, Legal, etc",
                "grado_ocurrencia": "2-1 el evento puede ocurrir entre el 1 y el 4.99% de los casos",
                "eventos_riesgo": 16,
                "poblacion_expuesta": 100,
            }
        )
        calculada = self.client.post("/api/v1/riesgos/calcular-valoracion/", valoracion, format="json")
        self.assertEqual(calculada.status_code, status.HTTP_200_OK)
        self.assertEqual((calculada.data["probabilidad"]["nivel"], calculada.data["severidad"]), (5, "Crítica"))

        payload = self.riesgo_payload()
        payload["valoracion"] = valoracion
        creada = self.client.post("/api/v1/riesgos/", payload, format="json")
        self.assertEqual(creada.status_code, status.HTTP_201_CREATED)
        self.assertEqual((creada.data["prob_inherente_nivel"], creada.data["prob_residual_nivel"]), (5, 5))

        riesgo = self.crear_riesgo_existente("R-MAX-EDIT")
        editada = self.client.patch(
            f"/api/v1/riesgos/{riesgo.riesgo_id}/", {"valoracion": valoracion}, format="json"
        )
        self.assertEqual(editada.status_code, status.HTTP_200_OK)
        self.assertEqual((editada.data["prob_inherente_nivel"], editada.data["prob_residual_nivel"]), (5, 5))

    def test_rechaza_impactos_incompletos(self):
        payload = self.riesgo_payload()["valoracion"]
        payload["impacto"]["impactos"].pop("Financiero")

        response = self.client.post("/api/v1/riesgos/calcular-valoracion/", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("faltantes", response.data["error"]["detalles"]["impactos"])

    def test_evaluacion_control_preserva_historico_hasta_completar_respuestas(self):
        riesgo = self.crear_riesgo_existente()
        control = riesgo.controles.get()
        control.tipo_control = "Preventivo"
        control.naturaleza = "Automatizado"
        control.cumple_diseno = "No"
        control.cumple_oper = "No"
        control.falla_vpr = "Sí"
        control.efectividad = "Débil"
        control.save()

        parcial = self.client.patch(
            f"/api/v1/riesgos/{riesgo.riesgo_id}/controles/{control.control_id}/evaluacion/",
            {"d1": "Sí"},
            format="json",
        )
        self.assertEqual(parcial.status_code, status.HTTP_200_OK)
        self.assertFalse(parcial.data["evaluacion_completa"])
        control.refresh_from_db()
        self.assertEqual(control.efectividad, "Débil")

        completa = self.client.patch(
            f"/api/v1/riesgos/{riesgo.riesgo_id}/controles/{control.control_id}/evaluacion/",
            {
                "d2": "Sí", "d3": "Sí", "d4": "Sí", "o1": "No", "o2": "Sí",
                "o3": "Sí", "o4": "Sí", "o5": "NA",
            },
            format="json",
        )
        self.assertEqual(completa.status_code, status.HTTP_200_OK)
        self.assertTrue(completa.data["evaluacion_completa"])
        control.refresh_from_db()
        self.assertEqual(control.cumple_diseno, "Sí")
        self.assertEqual(control.cumple_oper, "Sí")
        self.assertEqual(control.falla_vpr, "No")
        self.assertEqual(control.efectividad, "Fuerte")

    def test_residual_excluye_controles_inactivos_y_aplica_minimo(self):
        riesgo = Riesgo.objects.create(
            codigo_riesgo="R-RESIDUAL",
            nombre_riesgo="Residual",
            prob_inherente_nivel=2,
            impacto_inherente_nivel=3,
            estado="Activo",
        )
        Control.objects.create(
            riesgo=riesgo,
            codigo_control="CT-PREV",
            nombre_control="Preventivo",
            descripcion_control="Control",
            tipo_control="Preventivo",
            efectividad="Fuerte",
            estado="Activo",
        )
        Control.objects.create(
            riesgo=riesgo,
            codigo_control="CT-INACT",
            nombre_control="Inactivo",
            descripcion_control="Control",
            tipo_control="Preventivo",
            efectividad="Débil",
            estado="Inactivo",
        )

        response = self.client.post(f"/api/v1/riesgos/{riesgo.riesgo_id}/recalcular-residual/", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["residual"]["controles_activos"], 1)
        self.assertEqual(response.data["residual"]["movimientos"]["preventivo"], 2)
        self.assertEqual(response.data["residual"]["probabilidad"]["nivel"], 1)
        self.assertEqual(response.data["residual"]["impacto"]["nivel"], 3)

    def test_inactivar_riesgo_con_justificacion(self):
        riesgo = self.crear_riesgo_existente()

        response = self.client.post(
            f"/api/v1/riesgos/{riesgo.riesgo_id}/inactivar/",
            {"justificacion": "Depuracion funcional"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        riesgo.refresh_from_db()
        self.assertEqual(riesgo.estado, "Inactivo")
        self.assertEqual(riesgo.justificacion_inactivacion, "Depuracion funcional")
        self.assertIsNotNone(riesgo.fecha_inactivacion)

    def test_impedir_inactivacion_sin_justificacion(self):
        riesgo = self.crear_riesgo_existente()

        response = self.client.post(
            f"/api/v1/riesgos/{riesgo.riesgo_id}/inactivar/",
            {"justificacion": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["error"]["codigo"], "REGLA_NEGOCIO")
        riesgo.refresh_from_db()
        self.assertEqual(riesgo.estado, "Activo")


class RiesgoServiceTests(EmmaFlowFixtureMixin, TestCase):
    def test_complejidad_usa_niveles_de_cfg_probabilidad(self):
        casos = {"Alta": 5, "Media": 4, "Baja": 3}
        for complejidad, esperado in casos.items():
            with self.subTest(complejidad=complejidad):
                resultado = calcular_probabilidad(
                    exposicion="4 - Semanal",
                    complejidad=complejidad,
                    condiciones_entorno="2 - Estabilidad Política, Económica, Legal, etc",
                    grado_ocurrencia="1 - Menos del 1 % de los casos",
                    eventos_riesgo=0,
                    poblacion_expuesta=100,
                    version="test",
                )
                self.assertEqual(resultado["componentes"]["cualitativa"]["complejidad"], esperado)
    def test_probabilidad_inherente_toma_el_mayor_de_tres_componentes(self):
        resultado = calcular_probabilidad(
            exposicion="1 - Anualmente",
            complejidad="Baja",
            condiciones_entorno="2 - Estabilidad Política, Económica, Legal, etc",
            grado_ocurrencia="2-1 el evento puede ocurrir entre el 1 y el 4.99% de los casos",
            eventos_riesgo=16,
            poblacion_expuesta=100,
        )

        self.assertEqual(resultado["componentes"]["cualitativa"]["nivel"], 3)
        self.assertEqual(resultado["componentes"]["ocurrencia"]["nivel"], 2)
        self.assertEqual(resultado["componentes"]["historica"]["nivel"], 5)
        self.assertEqual(resultado["nivel"], 5)

    def test_rollback_cuando_falla_operacion_secundaria(self):
        payload = self.riesgo_payload()
        payload.pop("caracteristicas")
        payload.pop("valoracion")

        with patch(
            "backend.apps.riesgos.services.riesgo_service.RiesgoProceso.objects.create",
            side_effect=IntegrityError("fallo secundario"),
        ):
            with self.assertRaises(IntegrityError):
                RiesgoService.crear_riesgo(payload)

        self.assertFalse(Riesgo.objects.filter(codigo_riesgo="GR1").exists())

    def test_selector_detalle_no_genera_n_mas_uno_evidente(self):
        self.crear_riesgo_existente("R-001")
        self.crear_riesgo_existente("R-002")

        with self.assertNumQueries(6):
            riesgos = list(RiesgoSelector.obtener_activos())
            for riesgo in riesgos:
                list(riesgo.riesgo_procesos.all())
                list(riesgo.causas.all())
                list(riesgo.controles.all())
                list(riesgo.caracteristicas.all())


class MotorPuroTests(SimpleTestCase):
    """Algoritmos sin acceso a PostgreSQL: reproducen la lógica de EMMA."""

    def test_historica_respeta_todos_los_umbral_es(self):
        casos = {
            # Tarea 3: fronteras exactas recaen en Muy Baja.
            (0, 10_000): 1,
            (100, 10_000): 1,
            (101, 10_000): 2,
            (500, 10_000): 1,
            (501, 10_000): 3,
            (1_000, 10_000): 1,
            (1_001, 10_000): 4,
            (1_500, 10_000): 1,
            (1_501, 10_000): 5,
            (2_000, 10_000): 5,
        }
        for (eventos, poblacion), esperado in casos.items():
            with self.subTest(eventos=eventos, poblacion=poblacion):
                nivel, _ = _probabilidad_historica(eventos_riesgo=eventos, poblacion_expuesta=poblacion)
                self.assertEqual(nivel, esperado)

    def test_probabilidad_final_toma_el_maximo_de_los_tres_componentes(self):
        casos = (
            # exposición, complejidad, entorno, ocurrencia, histórica, final
            (5, 5, 5, 2, 3, 5),  # cualitativa mayor
            (1, 1, 1, 5, 3, 5),  # ocurrencia mayor
            (1, 2, 2, 3, 5, 5),  # histórica mayor
            (4, 4, 4, 4, 2, 4),  # empate de cualitativa y ocurrencia
            (3, 3, 3, 3, 3, 3),  # empate de los tres
        )
        for exposicion, complejidad, entorno, ocurrencia, historica, esperado in casos:
            with self.subTest(caso=(exposicion, complejidad, entorno, ocurrencia, historica)):
                with patch(
                    "backend.apps.riesgos.services.valoracion.probabilidad._nivel_cfg_probabilidad",
                    side_effect=[complejidad, entorno],
                ), patch(
                    "backend.apps.riesgos.services.valoracion.probabilidad._probabilidad_historica",
                    return_value=(historica, None),
                ):
                    resultado = calcular_probabilidad(
                        exposicion=f"{exposicion} - Prueba",
                        complejidad="Configuración prueba",
                        condiciones_entorno="Entorno prueba",
                        grado_ocurrencia=f"{ocurrencia} - Prueba",
                        eventos_riesgo=0,
                        poblacion_expuesta=1,
                    )
                self.assertEqual(resultado["nivel"], esperado)

    def test_umbrales_de_movimiento(self):
        casos = {
            "0.00": 0,
            "0.09": 0,
            "0.10": 1,
            "0.20": 1,
            "0.21": 2,
            "1.00": 2,
        }
        for promedio, esperado in casos.items():
            with self.subTest(promedio=promedio):
                from decimal import Decimal

                self.assertEqual(_movimiento(Decimal(promedio)), esperado)

    def test_promedios_usan_controles_activos_y_deduplican_codigo(self):
        controles = [
            SimpleNamespace(codigo_control="A", tipo_control="Preventivo", efectividad="Fuerte", estado="Inactivo"),
            SimpleNamespace(codigo_control="B", tipo_control="Detectivo", efectividad="Moderado", estado="Activo"),
            SimpleNamespace(codigo_control="A", tipo_control="Preventivo", efectividad="Fuerte", estado="Activo"),
        ]
        promedios, cantidad = _promedios_por_tipo(controles)
        self.assertEqual(cantidad, 1)
        self.assertEqual(str(promedios["preventivo"]), "0")
        self.assertEqual(str(promedios["detectivo"]), "1")
        self.assertEqual(str(promedios["correctivo"]), "0")

    @patch("backend.apps.riesgos.services.valoracion.residual.calcular_severidad", return_value={"severidad": "Prueba"})
    def test_residual_aplica_minimo_uno_y_prioridad_correctiva(self, _severidad):
        controles = [
            SimpleNamespace(codigo_control="P", tipo_control="Preventivo", efectividad="Fuerte", estado="Activo"),
            SimpleNamespace(codigo_control="C", tipo_control="Correctivo", efectividad="Fuerte", estado="Activo"),
            SimpleNamespace(codigo_control="D", tipo_control="Detectivo", efectividad="Fuerte", estado="Activo"),
        ]
        resultado = calcular_residual(probabilidad_inherente=2, impacto_inherente=2, controles=controles)
        self.assertEqual(resultado["probabilidad"]["nivel"], 1)
        self.assertEqual(resultado["impacto"]["nivel"], 1)
        self.assertEqual(resultado["movimientos"], {"preventivo": 2, "detectivo": 2, "correctivo": 2})

    def test_evaluacion_cubre_diseno_operatividad_y_falla_vpr(self):
        control = Control(
            tipo_control="Preventivo",
            naturaleza="Automatizado",
            d1="Sí", d2="Sí", d3="Sí", d4="Sí",
            o1="No", o2="Sí", o3="Sí", o4="Sí", o5="NA",
        )
        self.assertTrue(recalcular_evaluacion(control))
        self.assertEqual((control.cumple_diseno, control.cumple_oper, control.falla_vpr, control.efectividad), ("Sí", "Sí", "No", "Fuerte"))

    def test_matriz_de_efectividad_y_falla(self):
        esperados = {
            ("Correctivo", "Manual"): "Débil",
            ("Correctivo", "Dependiente de TI"): "Moderado",
            ("Correctivo", "Automatizado"): "Moderado",
            ("Preventivo", "Manual"): "Moderado",
            ("Preventivo", "Dependiente de TI"): "Moderado",
            ("Preventivo", "Automatizado"): "Fuerte",
            ("Detectivo", "Manual"): "Moderado",
            ("Detectivo", "Dependiente de TI"): "Moderado",
            ("Detectivo", "Automatizado"): "Fuerte",
        }
        for (tipo, naturaleza), esperado in esperados.items():
            with self.subTest(tipo=tipo, naturaleza=naturaleza):
                self.assertEqual(_efectividad(tipo, naturaleza, "No"), esperado)
                self.assertEqual(_efectividad(tipo, naturaleza, "Sí"), "Débil")


class Fase4CausasControlesApiTests(EmmaFlowFixtureMixin, APITestCase):
    """Contrato HTTP de Fase 4; requiere PostgreSQL con riesgos.0005."""

    def setUp(self):
        super().setUp()
        # IsAuthenticated se satisface sin crear un usuario persistente. La
        # auditoría se cubre aparte con un Usuario EMMA real.
        self.client.force_authenticate(User(username="fase4-pruebas"))
        self.riesgo = self.crear_riesgo_existente("R-F4-API")

    def _crear_causa(self, descripcion="Causa Fase 4"):
        response = self.client.post(
            "/api/v1/riesgos/causas/",
            {"riesgo_id": self.riesgo.riesgo_id, "descripcion_causa": descripcion, "estado": "Activo"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data["causa_id"]

    def _crear_control(self, causa_id, codigo="CTRL-F4-API"):
        return self.client.post(
            "/api/v1/riesgos/controles/",
            {
                "riesgo_id": self.riesgo.riesgo_id,
                "causa_id": causa_id,
                "codigo_control": codigo,
                "nombre_control": "Control Fase 4",
                "descripcion_control": "Descripción de control Fase 4",
                "tipo_control": "Preventivo",
                "naturaleza": "Automatizado",
                "estado": "Activo",
            },
            format="json",
        )

    def test_causas_listar_detalle_crear_editar_y_errores(self):
        listado = self.client.get("/api/v1/riesgos/causas/")
        self.assertEqual(listado.status_code, status.HTTP_200_OK)
        self.assertIn("results", listado.data)

        invalida = self.client.post("/api/v1/riesgos/causas/", {"riesgo_id": self.riesgo.riesgo_id}, format="json")
        self.assertEqual(invalida.status_code, status.HTTP_400_BAD_REQUEST)

        causa_id = self._crear_causa()
        self.assertEqual(self.client.get(f"/api/v1/riesgos/causas/{causa_id}/").status_code, status.HTTP_200_OK)
        edicion = self.client.patch(
            f"/api/v1/riesgos/causas/{causa_id}/", {"descripcion_causa": "Causa editada"}, format="json"
        )
        self.assertEqual(edicion.status_code, status.HTTP_200_OK)
        self.assertEqual(edicion.data["descripcion_causa"], "Causa editada")
        self.assertEqual(self.client.get("/api/v1/riesgos/causas/999999/").status_code, status.HTTP_404_NOT_FOUND)

    def test_asociacion_riesgo_causa_reutiliza_y_rechaza_duplicado(self):
        causa_id = self._crear_causa()
        otro_riesgo = Riesgo.objects.create(codigo_riesgo="R-F4-OTRO", nombre_riesgo="Otro", estado="Activo")
        ruta = f"/api/v1/riesgos/{otro_riesgo.riesgo_id}/causas/"
        self.assertEqual(self.client.post(ruta, {"causa_id": causa_id}, format="json").status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.post(ruta, {"causa_id": causa_id}, format="json").status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            self.client.delete(f"/api/v1/riesgos/{otro_riesgo.riesgo_id}/causas/{causa_id}/").status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertTrue(RiesgoCausa.objects.filter(riesgo=self.riesgo, causa_id=causa_id).exists())

    def test_controles_crud_relacion_y_evaluacion(self):
        causa_id = self._crear_causa()
        creada = self._crear_control(causa_id)
        self.assertEqual(creada.status_code, status.HTTP_201_CREATED)
        control_id = creada.data["control_id"]
        listado = self.client.get("/api/v1/riesgos/controles/", {"page_size": 1})
        self.assertEqual(listado.status_code, status.HTTP_200_OK)
        self.assertEqual(listado.data["count"], 2)
        self.assertEqual(len(listado.data["results"]), 1)
        self.assertIsNotNone(listado.data["next"])
        siguiente = self.client.get("/api/v1/riesgos/controles/", {"page": 2, "page_size": 1})
        self.assertEqual(siguiente.status_code, status.HTTP_200_OK)
        self.assertEqual(len(siguiente.data["results"]), 1)
        vacia = self.client.get("/api/v1/riesgos/controles/", {"search": "sin-coincidencias", "page_size": 1})
        self.assertEqual((vacia.data["count"], vacia.data["results"]), (0, []))
        self.assertEqual(self.client.get(f"/api/v1/riesgos/controles/{control_id}/").status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.patch(f"/api/v1/riesgos/controles/{control_id}/", {"objetivo": "Objetivo"}, format="json").status_code,
            status.HTTP_200_OK,
        )

        parcial = self.client.patch(
            f"/api/v1/riesgos/{self.riesgo.riesgo_id}/controles/{control_id}/evaluacion/", {"d1": "Sí"}, format="json"
        )
        self.assertEqual(parcial.status_code, status.HTTP_200_OK)
        self.assertFalse(parcial.data["evaluacion_completa"])
        completa = self.client.patch(
            f"/api/v1/riesgos/{self.riesgo.riesgo_id}/controles/{control_id}/evaluacion/",
            {"d2": "Sí", "d3": "Sí", "d4": "Sí", "o1": "No", "o2": "Sí", "o3": "Sí", "o4": "Sí", "o5": "NA"},
            format="json",
        )
        self.assertTrue(completa.data["evaluacion_completa"])
        self.assertEqual(completa.data["control"]["efectividad"], "Fuerte")

    def test_tripleta_rechaza_duplicado_y_consulta_por_riesgo_causa(self):
        causa_1 = self._crear_causa("Causa uno")
        causa_2 = self._crear_causa("Causa dos")
        creada = self._crear_control(causa_1)
        control_id = creada.data["control_id"]
        ruta = f"/api/v1/riesgos/{self.riesgo.riesgo_id}/causas/{causa_2}/controles/"
        self.assertEqual(self.client.post(ruta, {"control_id": control_id}, format="json").status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.post(ruta, {"control_id": control_id}, format="json").status_code, status.HTTP_400_BAD_REQUEST)
        consulta = self.client.get(ruta)
        self.assertEqual(consulta.status_code, status.HTTP_200_OK)
        self.assertEqual(consulta.data[0]["control_id"], control_id)
        self.assertEqual(
            RiesgoCausaControl.objects.filter(riesgo_causa__riesgo=self.riesgo, control_id=control_id).count(), 2
        )
        self.assertEqual(self.client.delete(f"{ruta}{control_id}/").status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.delete(f"{ruta}{control_id}/").status_code, status.HTTP_404_NOT_FOUND)

    def test_consultas_inversas_usan_las_tablas_puente(self):
        causa_id = self._crear_causa()
        control_id = self._crear_control(causa_id).data["control_id"]
        self.assertEqual(
            self.client.get(f"/api/v1/riesgos/causas/{causa_id}/riesgos/").data[0]["riesgo_id"], self.riesgo.riesgo_id
        )
        self.assertEqual(
            self.client.get(f"/api/v1/riesgos/controles/{control_id}/causas/").data[0]["causa_id"], causa_id
        )
        self.assertEqual(
            self.client.get(f"/api/v1/riesgos/controles/{control_id}/riesgos/").data[0]["riesgo_id"], self.riesgo.riesgo_id
        )

    def test_evaluacion_control_reutilizado_por_puente(self):
        causa_id = self._crear_causa()
        control_id = self._crear_control(causa_id).data["control_id"]
        otro = Riesgo.objects.create(codigo_riesgo="R-F4-REUSO", nombre_riesgo="Reuso", estado="Activo")
        RiesgoCausa.objects.create(riesgo=otro, causa_id=causa_id)
        RiesgoCausaControl.objects.create(
            riesgo_causa=RiesgoCausa.objects.get(riesgo=otro, causa_id=causa_id), control_id=control_id
        )
        respuesta = self.client.patch(
            f"/api/v1/riesgos/{otro.riesgo_id}/controles/{control_id}/evaluacion/", {"d1": "Sí"}, format="json"
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertFalse(respuesta.data["evaluacion_completa"])

    def test_control_generico_inexistente_debe_ser_error_de_validacion(self):
        causa_id = self._crear_causa()
        respuesta = self.client.post(
            "/api/v1/riesgos/controles/",
            {
                "riesgo_id": self.riesgo.riesgo_id,
                "causa_id": causa_id,
                "codigo_control": "CTRL-F4-CATALOGO",
                "nombre_control": "Control inválido",
                "descripcion_control": "Catálogo inexistente",
                "estado": "Activo",
                "control_generico_valor_id": 999999999,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_control_generico_inactivo_y_nulo_se_validan(self):
        causa_id = self._crear_causa()
        valido = self.client.post(
            "/api/v1/riesgos/controles/",
            {
                "riesgo_id": self.riesgo.riesgo_id,
                "causa_id": causa_id,
                "codigo_control": "CTRL-F4-ACTIVO",
                "nombre_control": "Control catálogo activo",
                "descripcion_control": "Catálogo activo",
                "estado": "Activo",
                "control_generico_valor_id": self.control_generico.valor_id,
            },
            format="json",
        )
        self.assertEqual(valido.status_code, status.HTTP_201_CREATED)
        inactivo = CatalogoValor.objects.filter(activo=False).first()
        respuesta = self.client.post(
            "/api/v1/riesgos/controles/",
            {
                "riesgo_id": self.riesgo.riesgo_id,
                "causa_id": causa_id,
                "codigo_control": "CTRL-F4-INACTIVO",
                "nombre_control": "Control catálogo inactivo",
                "descripcion_control": "Catálogo inactivo",
                "estado": "Activo",
                "control_generico_valor_id": inactivo.valor_id,
            },
            format="json",
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        nulo = self._crear_control(causa_id, codigo="CTRL-F4-NULO")
        self.assertEqual(nulo.status_code, status.HTTP_201_CREATED)

    def test_recalculo_residual_exige_autenticacion(self):
        self.riesgo.prob_inherente_nivel = 2
        self.riesgo.impacto_inherente_nivel = 2
        self.riesgo.save(update_fields=["prob_inherente_nivel", "impacto_inherente_nivel"])
        ruta = f"/api/v1/riesgos/{self.riesgo.riesgo_id}/recalcular-residual/"
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.post(ruta, {}, format="json").status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(User(username="fase4-pruebas"))
        # La configuración de severidad del fixture puede rechazar el cálculo,
        # pero la autenticación ya no debe ser la causa del rechazo.
        self.assertNotEqual(self.client.post(ruta, {}, format="json").status_code, status.HTTP_403_FORBIDDEN)

    def test_detalle_prioriza_puentes_y_deduplica_reutilizacion(self):
        origen = self.crear_riesgo_existente("R-F4-DETALLE-ORIGEN")
        causa = origen.causas.get()
        control = origen.controles.get()
        destino = Riesgo.objects.create(codigo_riesgo="R-F4-DETALLE-DESTINO", nombre_riesgo="Destino", estado="Activo")
        asociacion_1 = RiesgoCausa.objects.create(riesgo=destino, causa=causa)
        RiesgoCausaControl.objects.create(riesgo_causa=asociacion_1, control=control)
        causa_2 = Causa.objects.create(riesgo=origen, codigo_causa="C-F4-DETALLE-2", descripcion_causa="Segunda", estado="Activo")
        asociacion_2 = RiesgoCausa.objects.create(riesgo=destino, causa=causa_2)
        RiesgoCausaControl.objects.create(riesgo_causa=asociacion_2, control=control)

        respuesta = self.client.get(f"/api/v1/riesgos/{destino.riesgo_id}/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual({item["causa_id"] for item in respuesta.data["causas"]}, {causa.causa_id, causa_2.causa_id})
        self.assertEqual([item["control_id"] for item in respuesta.data["controles"]], [control.control_id])

    def test_configuracion_valoracion_expone_opciones_activas_sin_formulas(self):
        respuesta = self.client.get("/api/v1/riesgos/configuracion-valoracion/")
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data["exposicion"]), 5)
        self.assertEqual(len(respuesta.data["grado_ocurrencia"]), 5)
        self.assertTrue(respuesta.data["complejidad"])
        self.assertEqual({item["nombre"] for item in respuesta.data["impactos"]}, {
            "Impacto Legal", "Impacto Reputacional", "Impacto servicio al cliente", "Información", "Continuidad", "Contagio", "Financiero"
        })

    def test_unauthenticated_causa_returns_403_with_current_authentication_configuration(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/v1/riesgos/causas/").status_code, status.HTTP_403_FORBIDDEN)


class HistoricosMatrizApiTests(EmmaFlowFixtureMixin, APITestCase):
    """Functional, append-only history for the matrix; audit remains separate."""

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(User(username="historicos-matriz"))
        self.riesgo = self.crear_riesgo_existente("R-HIST")

    def _crear_causa(self, descripcion="Causa histórica"):
        response = self.client.post(
            "/api/v1/riesgos/causas/",
            {"riesgo_id": self.riesgo.riesgo_id, "descripcion_causa": descripcion, "estado": "Activo"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data["causa_id"]

    def _crear_control(self, causa_id):
        response = self.client.post(
            "/api/v1/riesgos/controles/",
            {
                "riesgo_id": self.riesgo.riesgo_id,
                "causa_id": causa_id,
                "codigo_control": "CTRL-HIST",
                "nombre_control": "Control histórico",
                "descripcion_control": "Control de prueba histórica",
                "tipo_control": "Preventivo",
                "naturaleza": "Automatizado",
                "estado": "Activo",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data["control_id"]

    def test_evaluacion_crea_versiones_inmutables_y_endpoint_ordenado(self):
        causa_id = self._crear_causa()
        control_id = self._crear_control(causa_id)
        ruta = f"/api/v1/riesgos/{self.riesgo.riesgo_id}/controles/{control_id}/evaluacion/"

        self.assertEqual(self.client.patch(ruta, {"d1": "Sí"}, format="json").status_code, status.HTTP_200_OK)
        primera = ControlEvaluacionHistorico.objects.get(control_id=control_id, version=1)
        self.assertEqual((primera.d1, primera.origen_registro, primera.usuario_id), ("Sí", "OPERACION", None))

        completa = self.client.patch(
            ruta,
            {"d2": "Sí", "d3": "Sí", "d4": "Sí", "o1": "No", "o2": "Sí", "o3": "Sí", "o4": "Sí", "o5": "NA"},
            format="json",
        )
        self.assertEqual(completa.status_code, status.HTTP_200_OK)
        primera.refresh_from_db()
        segunda = ControlEvaluacionHistorico.objects.get(control_id=control_id, version=2)
        self.assertIsNone(primera.efectividad)
        self.assertEqual(
            (segunda.d1, segunda.d2, segunda.d3, segunda.d4, segunda.o1, segunda.o2, segunda.o3, segunda.o4, segunda.o5),
            ("Sí", "Sí", "Sí", "Sí", "No", "Sí", "Sí", "Sí", "NA"),
        )
        self.assertEqual(
            (segunda.cumple_diseno, segunda.cumple_oper, segunda.falla_vpr, segunda.efectividad),
            ("Sí", "Sí", "No", "Fuerte"),
        )

        historial = self.client.get(f"/api/v1/riesgos/controles/{control_id}/evaluaciones-historicas/")
        self.assertEqual(historial.status_code, status.HTTP_200_OK)
        self.assertEqual([item["version"] for item in historial.data], [2, 1])

    def test_historial_riesgo_causa_asociar_retirar_y_reasociar(self):
        causa_id = self._crear_causa()
        otro = Riesgo.objects.create(codigo_riesgo="R-HIST-OTRO", nombre_riesgo="Otro histórico", estado="Activo")
        ruta = f"/api/v1/riesgos/{otro.riesgo_id}/causas/"
        self.assertEqual(self.client.post(ruta, {"causa_id": causa_id}, format="json").status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.delete(f"{ruta}{causa_id}/").status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.post(ruta, {"causa_id": causa_id}, format="json").status_code, status.HTTP_201_CREATED)

        eventos = list(HistorialRiesgoCausa.objects.filter(riesgo=otro, causa_id=causa_id).order_by("version"))
        self.assertEqual([(item.version, item.evento) for item in eventos], [(1, "ASSOCIATE"), (2, "DISASSOCIATE"), (3, "ASSOCIATE")])
        historial = self.client.get(f"/api/v1/riesgos/{otro.riesgo_id}/causas/{causa_id}/historial-asociacion/")
        self.assertEqual([item["version"] for item in historial.data], [3, 2, 1])

    def test_historial_tripleta_asociar_retirar_y_reasociar_sin_borrar_control(self):
        causa_1 = self._crear_causa("Causa uno")
        causa_2 = self._crear_causa("Causa dos")
        control_id = self._crear_control(causa_1)
        ruta = f"/api/v1/riesgos/{self.riesgo.riesgo_id}/causas/{causa_2}/controles/"
        self.assertEqual(self.client.post(ruta, {"control_id": control_id}, format="json").status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.client.delete(f"{ruta}{control_id}/").status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Control.objects.filter(control_id=control_id).exists())
        self.assertEqual(self.client.post(ruta, {"control_id": control_id}, format="json").status_code, status.HTTP_201_CREATED)

        eventos = list(HistorialRiesgoCausaControl.objects.filter(
            riesgo=self.riesgo, causa_id=causa_2, control_id=control_id
        ).order_by("version"))
        self.assertEqual([(item.version, item.evento) for item in eventos], [(1, "ASSOCIATE"), (2, "DISASSOCIATE"), (3, "ASSOCIATE")])
        historial = self.client.get(
            f"/api/v1/riesgos/{self.riesgo.riesgo_id}/causas/{causa_2}/controles/{control_id}/historial-asociacion/"
        )
        self.assertEqual([item["version"] for item in historial.data], [3, 2, 1])

    def test_endpoints_historicos_validan_entidad_y_exigen_autenticacion(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(
            self.client.get("/api/v1/riesgos/controles/999999/evaluaciones-historicas/").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.client.force_authenticate(User(username="historicos-matriz"))
        self.assertEqual(
            self.client.get("/api/v1/riesgos/controles/999999/evaluaciones-historicas/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_endpoint_historico_vacio_es_solo_lectura(self):
        control = self.riesgo.controles.get()
        ruta = f"/api/v1/riesgos/controles/{control.control_id}/evaluaciones-historicas/"
        self.assertEqual(self.client.get(ruta).data, [])
        self.assertEqual(self.client.post(ruta, {}, format="json").status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_error_al_escribir_historico_revierte_asociacion_vigente(self):
        causa_id = self._crear_causa()
        otro = Riesgo.objects.create(codigo_riesgo="R-HIST-ROLLBACK", nombre_riesgo="Rollback", estado="Activo")
        with patch(
            "backend.apps.riesgos.services.causa_service.registrar_riesgo_causa",
            side_effect=IntegrityError("histórico no disponible"),
        ):
            respuesta = self.client.post(
                f"/api/v1/riesgos/{otro.riesgo_id}/causas/", {"causa_id": causa_id}, format="json"
            )
        self.assertEqual(respuesta.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(RiesgoCausa.objects.filter(riesgo=otro, causa_id=causa_id).exists())

    def test_error_historico_revierte_retiro_de_causa(self):
        causa_id = self._crear_causa()
        otro = Riesgo.objects.create(codigo_riesgo="R-HIST-RET-CAUSA", nombre_riesgo="Otro", estado="Activo")
        self.client.post(f"/api/v1/riesgos/{otro.riesgo_id}/causas/", {"causa_id": causa_id}, format="json")
        with patch(
            "backend.apps.riesgos.services.causa_service.registrar_riesgo_causa",
            side_effect=IntegrityError("histórico no disponible"),
        ):
            respuesta = self.client.delete(f"/api/v1/riesgos/{otro.riesgo_id}/causas/{causa_id}/")
        self.assertEqual(respuesta.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertTrue(RiesgoCausa.objects.filter(riesgo=otro, causa_id=causa_id).exists())

    def test_error_historico_revierte_asociacion_de_control(self):
        causa_1 = self._crear_causa("Causa control origen")
        causa_2 = self._crear_causa("Causa control destino")
        control_id = self._crear_control(causa_1)
        ruta = f"/api/v1/riesgos/{self.riesgo.riesgo_id}/causas/{causa_2}/controles/"
        with patch(
            "backend.apps.riesgos.services.control_service.registrar_riesgo_causa_control",
            side_effect=IntegrityError("histórico no disponible"),
        ):
            respuesta = self.client.post(ruta, {"control_id": control_id}, format="json")
        self.assertEqual(respuesta.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(RiesgoCausaControl.objects.filter(
            riesgo_causa__riesgo=self.riesgo, riesgo_causa__causa_id=causa_2, control_id=control_id
        ).exists())

    def test_error_historico_revierte_retiro_de_control(self):
        causa_1 = self._crear_causa("Causa control origen")
        causa_2 = self._crear_causa("Causa control destino")
        control_id = self._crear_control(causa_1)
        ruta = f"/api/v1/riesgos/{self.riesgo.riesgo_id}/causas/{causa_2}/controles/"
        self.client.post(ruta, {"control_id": control_id}, format="json")
        with patch(
            "backend.apps.riesgos.services.control_service.registrar_riesgo_causa_control",
            side_effect=IntegrityError("histórico no disponible"),
        ):
            respuesta = self.client.delete(f"{ruta}{control_id}/")
        self.assertEqual(respuesta.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertTrue(RiesgoCausaControl.objects.filter(
            riesgo_causa__riesgo=self.riesgo, riesgo_causa__causa_id=causa_2, control_id=control_id
        ).exists())

    def test_error_historico_revierte_evaluacion_de_control(self):
        causa_id = self._crear_causa()
        control_id = self._crear_control(causa_id)
        control = Control.objects.get(control_id=control_id)
        with patch(
            "backend.apps.riesgos.services.control_service.registrar_evaluacion",
            side_effect=IntegrityError("histórico no disponible"),
        ):
            respuesta = self.client.patch(
                f"/api/v1/riesgos/{self.riesgo.riesgo_id}/controles/{control_id}/evaluacion/",
                {"d1": "Sí"}, format="json",
            )
        self.assertEqual(respuesta.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        control.refresh_from_db()
        self.assertIsNone(control.d1)
        self.assertFalse(ControlEvaluacionHistorico.objects.filter(control=control).exists())

from datetime import date, datetime, time

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from backend.apps.catalogos.models import Catalogo, CatalogoValor
from backend.apps.eventos.models import EventoRiesgo
from backend.apps.riesgos.models import Causa, Control, Riesgo
from backend.apps.usuarios.models import Usuario


class EventosApiIntegrationTests(APITestCase):
    """Reglas críticas de Eventos que deben persistir en PostgreSQL."""

    def setUp(self):
        self.auth_user = User.objects.create_user(username="eventos-prueba", email="eventos@example.com")
        self.usuario = Usuario.objects.create(
            entra_object_id="oid-eventos-prueba", username="eventos-prueba", nombre="Usuario Eventos",
            correo="eventos@example.com", estado="Activo", fecha_creacion=timezone.now(),
        )
        self.client.force_authenticate(self.auth_user)
        self.riesgo = Riesgo.objects.create(codigo_riesgo="GR-EVENTO-TEST", nombre_riesgo="Riesgo de evento", estado="Activo")
        self.causa = Causa.objects.create(
            riesgo=self.riesgo, codigo_causa="C-EVENTO-TEST", descripcion_causa="Causa válida", estado="Activo"
        )
        self.control = Control.objects.create(
            riesgo=self.riesgo, codigo_control="CT-EVENTO-TEST", nombre_control="Control válido",
            descripcion_control="Descripción válida", estado="Activo",
        )
        self.valores = {}
        for codigo in ("PRODUCTO", "CANAL", "SEGMENTO", "PAIS", "DEPARTAMENTO", "CIUDAD", "LINEA_NEGOCIO", "TIPO_EVENTO", "CLASE_EVENTO", "OFICINA", "GERENCIA_EVENTO"):
            catalogo, _ = Catalogo.objects.get_or_create(codigo_catalogo=codigo, defaults={"nombre": codigo, "activo": True})
            self.valores[codigo] = catalogo

        def valor(codigo, descripcion, nivel=1, padre=None):
            return CatalogoValor.objects.create(catalogo=self.valores[codigo], descripcion=descripcion, nivel=nivel, parent_valor=padre, activo=True)

        pais = valor("PAIS", "Colombia")
        departamento = valor("DEPARTAMENTO", "Bogotá D.C.", 2, pais)
        ciudad = valor("CIUDAD", "Bogotá", 3, departamento)
        linea_n1 = valor("LINEA_NEGOCIO", "N1")
        linea_n2 = valor("LINEA_NEGOCIO", "N2", 2, linea_n1)
        tipo_n1 = valor("TIPO_EVENTO", "T1")
        tipo_n2 = valor("TIPO_EVENTO", "T2", 2, tipo_n1)
        tipo_n3 = valor("TIPO_EVENTO", "T3", 3, tipo_n2)
        self.caracteristicas = [
            valor("PRODUCTO", "Producto"), valor("CANAL", "Canal"), valor("SEGMENTO", "Segmento"),
            pais, departamento, ciudad, linea_n1, linea_n2, tipo_n1, tipo_n2, tipo_n3, valor("CLASE_EVENTO", "Clase"),
        ]
        self.oficina = valor("OFICINA", "Oficina principal")
        self.gerencia = valor("GERENCIA_EVENTO", "Dirección general")

    def _payload(self):
        hoy = timezone.localdate()
        return {
            "riesgo_id": self.riesgo.riesgo_id,
            "fecha_inicio_evento": str(hoy), "hora_inicio_evento": "08:00:00",
            "fecha_descubrimiento_evento": str(hoy), "hora_descubrimiento_evento": "09:00:00",
            "fecha_finalizacion_evento": str(hoy), "hora_finalizacion_evento": "10:00:00",
            "descripcion_evento": "Descripción del evento de prueba",
            "nombre_evento": "Evento de prueba",
            "cuantia_estimada": "1.00", "cantidad_casos": 1,
            "tipo_perdida": "B", "estado_evento": "REPORTADO",
            "cuantia_perdida_bruta": "0.00", "cuantia_recuperada_seguros": "0.00",
            "cuantia_otras_recuperaciones": "0.00",
            "tipo_recuperacion": [],
            "causas": [{"causa_id": self.causa.causa_id}],
            "controles": [{"control_id": self.control.control_id}],
            "caracteristicas": [{"valor_catalogo_id": valor.valor_id} for valor in self.caracteristicas],
            "sitio_ocurrencia_tipo": "OFICINA", "sitio_ocurrencia_valor_id": self.oficina.valor_id,
            "sitio_deteccion_tipo": "DIRECCION_GENERAL", "sitio_deteccion_valor_id": self.gerencia.valor_id,
        }

    def test_crear_evento_deriva_identidad_snapshots_y_asociaciones(self):
        response = self.client.post("/api/v1/eventos/", self._payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        evento = EventoRiesgo.objects.get(evento_id=response.data["evento_id"])
        self.assertTrue(evento.id_ocurrencia)
        self.assertEqual(evento.usuario_registro_id, self.usuario.usuario_id)
        self.assertEqual(evento.codigo_riesgo_snapshot, self.riesgo.codigo_riesgo)
        self.assertEqual(evento.evento_causas.get().codigo_causa_snapshot, self.causa.codigo_causa)
        self.assertEqual(evento.evento_controles.get().codigo_control_snapshot, self.control.codigo_control)
        self.assertEqual(evento.divisa, "N/A")
        self.assertEqual(evento.pais_evento, "Colombia")
        self.assertEqual(evento.sitio_ocurrencia, "Oficina principal")
        self.assertEqual(evento.sitio_deteccion, "Dirección general")

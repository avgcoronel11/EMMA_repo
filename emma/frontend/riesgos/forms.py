import json

from django import forms


class RiesgoFiltroForm(forms.Form):
    search = forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Nombre, referencia, ciclo, subfactor, proceso o dueño",
                "autocomplete": "off",
            }
        ),
    )
    estado = forms.ChoiceField(
        required=False,
        label="Estado",
        choices=(("", "Todos"), ("Activo", "Activos"), ("Inactivo", "Inactivos")),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    codigo_riesgo = forms.CharField(required=False, label="Código GR", widget=forms.TextInput(attrs={"class": "form-control"}))
    riesgo_homologado = forms.ChoiceField(required=False, label="Riesgo homologado", choices=(), widget=forms.Select(attrs={"class": "form-select"}))
    vicepresidencia = forms.ChoiceField(required=False, label="Vicepresidencia", choices=(), widget=forms.Select(attrs={"class": "form-select", "data-estructura-vicepresidencia": "true"}))
    proceso = forms.ChoiceField(required=False, label="Proceso", choices=(), widget=forms.Select(attrs={"class": "form-select", "data-estructura-proceso": "true"}))
    subproceso = forms.ChoiceField(required=False, label="Subproceso", choices=(), widget=forms.Select(attrs={"class": "form-select", "data-estructura-subproceso": "true"}))
    linea = forms.ChoiceField(required=False, label="Línea", choices=(), widget=forms.Select(attrs={"class": "form-select", "data-estructura-linea-select": "true"}))
    macroproceso = forms.ChoiceField(required=False, label="Macroproceso", choices=(), widget=forms.Select(attrs={"class": "form-select", "data-estructura-macroproceso-select": "true"}))
    dueno_proceso = forms.ChoiceField(required=False, label="Dueño del proceso", choices=(), widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, opciones_riesgo=None, **kwargs):
        super().__init__(*args, **kwargs)
        opciones_riesgo = opciones_riesgo or {}
        estructura = opciones_riesgo.get("estructura_procesos", [])
        vicepresidencia = self.data.get("vicepresidencia") if self.is_bound else self.initial.get("vicepresidencia")
        proceso = self.data.get("proceso") if self.is_bound else self.initial.get("proceso")
        estructura_vp = [item for item in estructura if item.get("vicepresidencia") == vicepresidencia]
        procesos = sorted(
            {item.get("proceso_nivel0") for item in estructura_vp if item.get("proceso_nivel0")},
            key=str.casefold,
        )
        subprocesos = sorted(
            {
                item.get("proceso_nivel1")
                for item in estructura_vp
                if item.get("proceso_nivel0") == proceso and item.get("proceso_nivel1")
            },
            key=str.casefold,
        )
        subproceso = self.data.get("subproceso") if self.is_bound else self.initial.get("subproceso")
        estructura_seleccionada = [
            item for item in estructura_vp
            if (not proceso or item.get("proceso_nivel0") == proceso)
            and (not subproceso or item.get("proceso_nivel1") == subproceso)
        ]
        self.fields["vicepresidencia"].choices = [("", "Todos")] + [
            (valor, valor)
            for valor in sorted(
                {item.get("vicepresidencia") for item in estructura if item.get("vicepresidencia")},
                key=str.casefold,
            )
        ]
        self.fields["proceso"].choices = [("", "Todos")] + [(valor, valor) for valor in procesos]
        self.fields["subproceso"].choices = [("", "Todos")] + [(valor, valor) for valor in subprocesos]
        self.fields["linea"].choices = [("", "Todos")] + [
            (valor, valor)
            for valor in sorted({item.get("linea") for item in estructura_seleccionada if item.get("linea")}, key=str.casefold)
        ]
        self.fields["macroproceso"].choices = [("", "Todos")] + [
            (valor, valor)
            for valor in sorted({item.get("macroproceso") for item in estructura_seleccionada if item.get("macroproceso")}, key=str.casefold)
        ]
        self.fields["vicepresidencia"].widget.attrs["data-estructura-procesos"] = json.dumps(estructura, ensure_ascii=False)
        for campo, opciones in (
            ("riesgo_homologado", opciones_riesgo.get("riesgos_homologados", [])),
            ("dueno_proceso", opciones_riesgo.get("duenos", [])),
        ):
            self.fields[campo].choices = [("", "Todos")] + [(valor, etiqueta) for valor, etiqueta in opciones]


class RiesgoCreateForm(forms.Form):
    FRENTES_RIESGO = (
        ("SARO", "SARO"), ("Conductas", "Conductas"), ("ABAC", "ABAC"),
        ("SARLAFT/FPADM", "SARLAFT/FPADM"), ("Compliance", "Compliance"),
        ("Seguridad de la Información y Ciberseguridad", "Seguridad de la Información y Ciberseguridad"),
        ("Mercado", "Mercado"), ("SARAS", "SARAS"), ("SOX", "SOX"),
        ("Liquidez", "Liquidez"), ("Crédito", "Crédito"), ("RTILB", "RTILB"),
        ("Relevante", "Relevante"), ("ELC", "ELC"), ("Operativo", "Operativo"),
    )
    FACTORES_RIESGO = (
        ("Clientes, productos y prácticas empresariales", "Clientes, productos y prácticas empresariales"),
        ("Daños a activos físicos", "Daños a activos físicos"), ("Fallas tecnológicas", "Fallas tecnológicas"),
        ("Ejecución y administración de procesos", "Ejecución y administración de procesos"),
        ("Producto y mercado objetivo", "Producto y mercado objetivo"),
        ("Relacionamiento con el consumidor financiero", "Relacionamiento con el consumidor financiero"),
        ("Estrategias e incentivos", "Estrategias e incentivos"), ("Riesgo emergente", "Riesgo emergente"),
        ("Fraude Interno", "Fraude Interno"), ("Fraude Externo", "Fraude Externo"),
        ("Relaciones Laborales y Seguridad Laboral", "Relaciones Laborales y Seguridad Laboral"),
    )
    FRECUENCIAS = (
        ("", "Seleccione..."), ("Anual", "Anual"), ("Bimestral", "Bimestral"),
        ("Bisemanal", "Bisemanal"), ("Múltiples veces al día", "Múltiples veces al día"),
        ("Diario", "Diario"), ("Eventual", "Eventual"), ("Mensual", "Mensual"),
        ("Quincenal", "Quincenal"), ("Semanal", "Semanal"), ("Semestral", "Semestral"),
        ("Trimestral", "Trimestral"), ("Cuatrimestral", "Cuatrimestral"), ("Permanente", "Permanente"),
    )
    CAMPOS_IMPACTO = {
        "impacto_legal": "Impacto Legal",
        "impacto_reputacional": "Impacto Reputacional",
        "impacto_servicio_cliente": "Impacto servicio al cliente",
        "impacto_informacion": "Información",
        "impacto_continuidad": "Continuidad",
        "impacto_contagio": "Contagio",
        "impacto_financiero": "Financiero",
    }
    nombre_riesgo = forms.CharField(
        label="Nombre del riesgo",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Describe el riesgo operativo",
            }
        ),
    )
    estado = forms.ChoiceField(
        label="Estado",
        required=False,
        choices=(("Activo", "Activo"), ("Inactivo", "Inactivo")),
        initial="Activo",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    riesgo_homologado = forms.ChoiceField(label="Riesgo homologado", required=False, choices=(), widget=forms.Select(attrs={"class": "form-select"}))
    frente_riesgo_asociado = forms.MultipleChoiceField(
        required=False, label="Frente de Riesgos asociado", choices=FRENTES_RIESGO,
        widget=forms.CheckboxSelectMultiple,
    )
    control_cambios = forms.ChoiceField(
        required=False, label="Control de cambios", choices=(("", "Seleccione..."), ("Nuevo", "Nuevo"), ("Antiguo", "Antiguo")),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    checklist_riesgo = forms.MultipleChoiceField(
        required=False, label="Checklist riesgo", choices=FRENTES_RIESGO,
        widget=forms.CheckboxSelectMultiple,
    )
    factor_riesgo_tipo_evento = forms.MultipleChoiceField(
        required=False, label="Factor de riesgo / Tipo de evento", choices=FACTORES_RIESGO,
        widget=forms.CheckboxSelectMultiple,
    )
    frecuencia = forms.ChoiceField(required=False, label="Frecuencia", choices=FRECUENCIAS, widget=forms.Select(attrs={"class": "form-select", "data-frecuencia-riesgo": "true", "onchange": "var detalle=this.form.querySelector('[data-detalle-frecuencia]'); if(detalle){var eventual=this.value==='Eventual'; detalle.disabled=!eventual; detalle.required=eventual; if(!eventual){detalle.value='';}}"}))
    detalle_frecuencia = forms.CharField(required=False, label="Detalle de frecuencia (solo Eventual)", widget=forms.TextInput(attrs={"class": "form-control", "data-detalle-frecuencia": "true", "disabled": "disabled"}))
    subfactor_riesgo = forms.ChoiceField(label="Subfactor", required=False, choices=(), widget=forms.Select(attrs={"class": "form-select"}))
    # Estos dos valores son informativos: se derivan siempre de la fila de
    # cat_proceso elegida como subproceso. El backend los vuelve a calcular
    # antes de persistir el riesgo, por lo que no se pueden alterar desde el
    # navegador.
    linea = forms.CharField(label="Línea", required=False, widget=forms.TextInput(attrs={"class": "form-control", "readonly": "readonly", "data-estructura-linea": "true"}))
    macroproceso = forms.CharField(label="Macroproceso", required=False, widget=forms.TextInput(attrs={"class": "form-control", "readonly": "readonly", "data-estructura-macroproceso": "true"}))
    dueno_proceso = forms.ChoiceField(label="Dueño del proceso", required=False, choices=(), widget=forms.Select(attrs={"class": "form-select"}))
    vicepresidencia = forms.ChoiceField(label="Vicepresidencia", required=False, choices=(), widget=forms.Select(attrs={"class": "form-select", "data-estructura-vicepresidencia": "true"}))
    proceso_nivel0 = forms.ChoiceField(label="Proceso / Proceso nivel 0", required=False, choices=(), widget=forms.Select(attrs={"class": "form-select", "data-estructura-proceso": "true"}))
    proceso_ids = forms.ChoiceField(label="Proceso de nivel 1 / Hito - Subproceso", required=False, choices=(), widget=forms.Select(attrs={"class": "form-select", "data-estructura-subproceso": "true"}))
    comentario_ultima_edicion = forms.CharField(
        label="Comentario",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    exposicion = forms.ChoiceField(required=False, label="Exposición", choices=())
    complejidad = forms.ChoiceField(required=False, label="Complejidad", choices=())
    condiciones_entorno = forms.ChoiceField(required=False, label="Condiciones del entorno", choices=())
    grado_ocurrencia = forms.ChoiceField(required=False, label="Grado de ocurrencia", choices=())
    eventos_riesgo = forms.IntegerField(required=False, min_value=0, label="Eventos de riesgo")
    poblacion_expuesta = forms.IntegerField(required=False, min_value=1, label="Población expuesta")
    valoracion_version = forms.CharField(required=False, widget=forms.HiddenInput())
    impacto_legal = forms.ChoiceField(required=False, label="Impacto Legal", choices=())
    impacto_reputacional = forms.ChoiceField(required=False, label="Impacto Reputacional", choices=())
    impacto_servicio_cliente = forms.ChoiceField(required=False, label="Impacto servicio al cliente", choices=())
    impacto_informacion = forms.ChoiceField(required=False, label="Información", choices=())
    impacto_continuidad = forms.ChoiceField(required=False, label="Continuidad", choices=())
    impacto_contagio = forms.ChoiceField(required=False, label="Contagio", choices=())
    impacto_financiero = forms.ChoiceField(required=False, label="Financiero", choices=())

    def __init__(self, *args, configuracion=None, opciones_riesgo=None, **kwargs):
        super().__init__(*args, **kwargs)
        configuracion = configuracion or {}
        opciones_riesgo = opciones_riesgo or {}
        estructura = opciones_riesgo.get("estructura_procesos", [])
        vicepresidencia = self.data.get("vicepresidencia") if self.is_bound else self.initial.get("vicepresidencia")
        procesos_seleccionados = (self.data.getlist("proceso_nivel0") if hasattr(self.data, "getlist") else self.data.get("proceso_nivel0", [])) if self.is_bound else self.initial.get("proceso_nivel0", [])
        if isinstance(procesos_seleccionados, str):
            procesos_seleccionados = [procesos_seleccionados]
        procesos_seleccionados = set(procesos_seleccionados or [])
        estructura_vp = [x for x in estructura if x.get("vicepresidencia") == vicepresidencia]
        nombres_proceso = sorted(
            {x["proceso_nivel0"] for x in estructura_vp if x.get("proceso_nivel0")},
            key=str.casefold,
        )
        subprocesos = [
            x for x in estructura_vp
            if x.get("proceso_nivel0") in procesos_seleccionados and x.get("proceso_nivel1")
        ]
        self.fields["vicepresidencia"].choices = [("", "Seleccione...")] + [(x, x) for x in sorted({x.get("vicepresidencia") for x in estructura if x.get("vicepresidencia")})]
        self.fields["proceso_nivel0"].choices = [("", "Seleccione...")] + [(x, x) for x in nombres_proceso]
        self.fields["proceso_ids"].choices = [("", "Seleccione...")] + [
            (str(x["proceso_id"]), x["proceso_nivel1"])
            for x in sorted(subprocesos, key=lambda item: (item["proceso_nivel1"].casefold(), item["proceso_id"]))
        ]
        self.fields["vicepresidencia"].widget.attrs["data-estructura-procesos"] = json.dumps(estructura, ensure_ascii=False)
        for campo, opciones in (
            ("riesgo_homologado", opciones_riesgo.get("riesgos_homologados", [])),
            ("subfactor_riesgo", opciones_riesgo.get("subfactores", [])),
            ("dueno_proceso", opciones_riesgo.get("duenos", [])),
        ):
            self.fields[campo].choices = [("", "Seleccione...")] + [(valor, etiqueta) for valor, etiqueta in opciones]
        for campo in ("exposicion", "complejidad", "condiciones_entorno", "grado_ocurrencia"):
            opciones = configuracion.get(campo, [])
            if campo == "grado_ocurrencia":
                choices = [
                    (
                        opcion["valor"],
                        opcion["valor"].split(" - ", 1)[1] if " - " in opcion["valor"] else opcion["etiqueta"],
                    )
                    for opcion in opciones
                ]
            else:
                choices = [(opcion["valor"], opcion["etiqueta"]) for opcion in opciones]
            self.fields[campo].choices = [("", "Seleccione...")] + choices
            self.fields[campo].widget.attrs["class"] = "form-select"
        opciones_impacto = {item["nombre"]: item["opciones"] for item in configuracion.get("impactos", [])}
        for campo, nombre in self.CAMPOS_IMPACTO.items():
            self.fields[campo].choices = [("", "Seleccione...")] + [
                (opcion["valor"], opcion["etiqueta"]) for opcion in opciones_impacto.get(nombre, [])
            ]
            self.fields[campo].widget.attrs["class"] = "form-select"
        self.initial.setdefault("valoracion_version", configuracion.get("version"))

    def clean(self):
        cleaned = super().clean()
        estructura = json.loads(
            self.fields["vicepresidencia"].widget.attrs.get("data-estructura-procesos", "[]")
        )
        vicepresidencia = cleaned.get("vicepresidencia")
        procesos = [valor for valor in self.data.getlist("proceso_nivel0") if valor] if hasattr(self.data, "getlist") else [cleaned.get("proceso_nivel0")] if cleaned.get("proceso_nivel0") else []
        if len(procesos) > 1:
            self.add_error("proceso_nivel0", "Solo puede seleccionar un proceso.")
            return cleaned
        proceso_nivel0 = procesos[0] if procesos else None
        proceso_id = cleaned.get("proceso_ids")
        niveles_estructura = (vicepresidencia, proceso_nivel0, proceso_id)
        if any(niveles_estructura) and not all(niveles_estructura):
            self.add_error(
                "proceso_ids" if proceso_nivel0 else "proceso_nivel0" if vicepresidencia else "vicepresidencia",
                "Seleccione Vicepresidencia, Proceso y Subproceso en ese orden.",
            )
        if proceso_id:
            proceso = next((item for item in estructura if str(item.get("proceso_id")) == str(proceso_id)), None)
            if not proceso or proceso.get("vicepresidencia") != vicepresidencia or proceso.get("proceso_nivel0") != proceso_nivel0:
                self.add_error("proceso_ids", "El subproceso debe pertenecer a la vicepresidencia y al proceso seleccionado.")
        campos = (
            "exposicion", "complejidad", "condiciones_entorno", "grado_ocurrencia",
            "eventos_riesgo", "poblacion_expuesta", *self.CAMPOS_IMPACTO,
        )
        presentes = [campo for campo in campos if cleaned.get(campo) not in (None, "")]
        if presentes:
            for campo in campos:
                if cleaned.get(campo) in (None, ""):
                    self.add_error(campo, "Complete todos los datos de valoración o deje la sección vacía.")
        if cleaned.get("frecuencia") == "Eventual" and not cleaned.get("detalle_frecuencia"):
            self.add_error("detalle_frecuencia", "Indique el detalle cuando la frecuencia es Eventual.")
        if cleaned.get("frecuencia") != "Eventual":
            cleaned["detalle_frecuencia"] = ""
        return cleaned

    def to_api_payload(self):
        payload = {}
        for field_name, value in self.cleaned_data.items():
            if value not in ("", None, []):
                payload[field_name] = value
        campos_valoracion = (
            "exposicion", "complejidad", "condiciones_entorno", "grado_ocurrencia",
            "eventos_riesgo", "poblacion_expuesta", *self.CAMPOS_IMPACTO,
        )
        if all(self.cleaned_data.get(campo) not in (None, "") for campo in campos_valoracion):
            payload["valoracion"] = {
                "version": self.cleaned_data.get("valoracion_version") or None,
                "probabilidad": {campo: self.cleaned_data[campo] for campo in campos_valoracion[:6]},
                "impacto": {
                    "impactos": {
                        nombre: self.cleaned_data[campo] for campo, nombre in self.CAMPOS_IMPACTO.items()
                    }
                },
            }
            payload["valoracion"] = {key: value for key, value in payload["valoracion"].items() if value is not None}
        for campo in (*campos_valoracion, "valoracion_version"):
            payload.pop(campo, None)
        proceso_id = payload.pop("proceso_ids", None)
        payload.pop("vicepresidencia", None)
        payload.pop("proceso_nivel0", None)
        if proceso_id:
            payload["proceso_ids"] = [int(proceso_id)]
            payload["proceso_principal_id"] = int(proceso_id)
        return payload


class RiesgoEditForm(RiesgoCreateForm):
    """Solo campos generales admitidos por PATCH; GR y cálculos son solo lectura."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("estado")


class RiesgoInactivarForm(forms.Form):
    justificacion = forms.CharField(
        label="Justificación de inactivación",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
    confirmacion_inactivacion = forms.BooleanField(
        required=True,
        label="Confirmo que deseo inactivar el riesgo y entiendo que no se eliminarán causas ni controles.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class CausaForm(forms.Form):
    codigo_actual_causa = forms.CharField(required=False, label="Código de referencia", widget=forms.TextInput(attrs={"class": "form-control"}))
    descripcion_causa = forms.CharField(label="Descripción", widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
    subfactor = forms.ChoiceField(required=False, label="Subfactor", choices=(), widget=forms.Select(attrs={"class": "form-select"}))
    linea = forms.CharField(required=False, label="Línea", disabled=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    macroproceso = forms.CharField(required=False, label="Macroproceso", disabled=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    dueno = forms.CharField(required=False, label="Dueño", disabled=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    estado = forms.ChoiceField(required=False, choices=(("Activo", "Activo"), ("Inactivo", "Inactivo")), widget=forms.Select(attrs={"class": "form-select"}))
    riesgo_id = forms.ChoiceField(required=False, label="Riesgo", choices=(), widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, riesgos=None, subfactores=None, require_riesgo=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["riesgo_id"].required = require_riesgo
        self.fields["riesgo_id"].choices = [("", "Seleccione un Riesgo...")] + [
            (str(r["riesgo_id"]), f'{r.get("codigo_riesgo", "")} — {r.get("nombre_riesgo", "")}') for r in (riesgos or [])
        ]
        self.fields["riesgo_id"].widget.attrs["data-contexto-causa"] = json.dumps({
            str(r["riesgo_id"]): {
                "linea": r.get("linea") or "",
                "macroproceso": r.get("macroproceso") or "",
                "dueno": r.get("dueno_proceso") or "",
            }
            for r in (riesgos or [])
        })
        self.fields["subfactor"].choices = [("", "Seleccione...")] + [
            (item.get("descripcion") or item.get("codigo"), item.get("descripcion") or item.get("codigo"))
            for item in (subfactores or []) if item.get("descripcion") or item.get("codigo")
        ]

    def payload(self, include_riesgo=False):
        result = {key: value for key, value in self.cleaned_data.items() if value not in ("", None)}
        if not include_riesgo:
            result.pop("riesgo_id", None)
        elif "riesgo_id" in result:
            result["riesgo_id"] = int(result["riesgo_id"])
        return result


class ControlForm(forms.Form):
    ASERCIONES = (("Integridad", "Integridad"), ("Existencia/Ocurrencia", "Existencia/Ocurrencia"), ("Derechos y Obligaciones", "Derechos y Obligaciones"), ("Valuacion/Asignacion", "Valuacion/Asignacion"), ("Presentacion y Revelacion", "Presentacion y Revelacion"), ("No aplica", "No aplica"))
    ATRIBUTOS = (("Confidencialidad", "Confidencialidad"), ("Disponibilidad", "Disponibilidad"), ("Gobernanza", "Gobernanza"), ("Calidad", "Calidad"), ("Utilidad", "Utilidad"), ("Objetividad", "Objetividad"), ("Integridad", "Integridad"), ("No aplica", "No aplica"))
    RIESGOS_CONTROL = RiesgoCreateForm.FRENTES_RIESGO
    codigo_actual_control = forms.CharField(required=False, label="Código de referencia", widget=forms.TextInput(attrs={"class": "form-control"}))
    nombre_control = forms.CharField(label="Nombre", widget=forms.TextInput(attrs={"class": "form-control"}))
    objetivo = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
    descripcion_control = forms.CharField(label="Descripción", widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
    importancia = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    evidencia = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}))
    ejecutor_texto = forms.CharField(required=False, label="Ejecutor", widget=forms.TextInput(attrs={"class": "form-control"}))
    tipo_control = forms.ChoiceField(required=False, choices=(("", "Seleccione..."), ("Preventivo", "Preventivo"), ("Detectivo", "Detectivo"), ("Correctivo", "Correctivo")), widget=forms.Select(attrs={"class": "form-select"}))
    naturaleza = forms.ChoiceField(required=False, choices=(("", "Seleccione..."), ("Manual", "Manual"), ("Dependiente de TI", "Dependiente de TI"), ("Automatizado", "Automatizado")), widget=forms.Select(attrs={"class": "form-select"}))
    estado = forms.ChoiceField(required=False, choices=(("Activo", "Activo"), ("Inactivo", "Inactivo")), widget=forms.Select(attrs={"class": "form-select"}))
    control_generico_valor_id = forms.ChoiceField(required=False, label="Control genérico", choices=(), widget=forms.Select(attrs={"class": "form-select"}))
    riesgo_id = forms.ChoiceField(required=False, label="Riesgo", choices=(), widget=forms.Select(attrs={"class": "form-select"}))
    causa_id = forms.ChoiceField(required=False, label="Causa", choices=(), widget=forms.Select(attrs={"class": "form-select"}))
    sistema_valor_ids = forms.MultipleChoiceField(required=False, label="Sistema / Aplicación / Activo de información", choices=(), widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 6}))
    principio_coso_valor_ids = forms.MultipleChoiceField(required=False, label="Principio COSO (ELC)", choices=(), widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 5}))
    cuenta_ids = forms.MultipleChoiceField(required=False, label="Cuentas contables relacionadas", choices=(), widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 6}))
    aserciones = forms.MultipleChoiceField(required=False, label="Checklist de aserciones", choices=ASERCIONES, widget=forms.CheckboxSelectMultiple)
    atributos = forms.MultipleChoiceField(required=False, label="Checklist de atributos", choices=ATRIBUTOS, widget=forms.CheckboxSelectMultiple)
    riesgos_control = forms.MultipleChoiceField(required=False, label="Checklist de riesgos", choices=RIESGOS_CONTROL, widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 6}))

    def __init__(self, *args, riesgos=None, causas=None, catalogo=None, sistemas=None, principios_coso=None, cuentas=None, require_context=False, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ("riesgo_id", "causa_id"):
            self.fields[field].required = require_context
        self.fields["riesgo_id"].choices = [("", "Seleccione un Riesgo...")] + [(str(x["riesgo_id"]), f'{x.get("codigo_riesgo", "")} — {x.get("nombre_riesgo", "")}') for x in (riesgos or [])]
        self.fields["causa_id"].choices = [("", "Seleccione una Causa...")] + [(str(x["causa_id"]), f'{x.get("codigo_causa", "")} — {x.get("descripcion_causa", "")}') for x in (causas or [])]
        self.fields["control_generico_valor_id"].choices = [("", "No aplica")] + [(str(x["valor_id"]), x.get("descripcion") or x.get("codigo")) for x in (catalogo or [])]
        self.fields["sistema_valor_ids"].choices = [(str(x["valor_id"]), x.get("descripcion") or x.get("codigo")) for x in (sistemas or [])]
        self.fields["principio_coso_valor_ids"].choices = [(str(x["valor_id"]), x.get("descripcion") or x.get("codigo")) for x in (principios_coso or [])]
        self.fields["cuenta_ids"].choices = [(str(x["cuenta_id"]), f'{x.get("codigo") or ""} — {x.get("descripcion") or ""}') for x in (cuentas or [])]

    def payload(self, include_context=False):
        result = {key: value for key, value in self.cleaned_data.items() if value not in ("", None)}
        for field in ("control_generico_valor_id", "riesgo_id", "causa_id"):
            if field in result:
                result[field] = int(result[field])
        for field in ("sistema_valor_ids", "principio_coso_valor_ids", "cuenta_ids"):
            result[field] = [int(value) for value in result.get(field, [])]
        if not include_context:
            result.pop("riesgo_id", None); result.pop("causa_id", None)
        return result


class EvaluacionControlForm(forms.Form):
    RESPUESTAS_SN = (("", "Sin responder"), ("Sí", "Sí"), ("No", "No"))
    d1 = forms.ChoiceField(required=False, label="D1", choices=RESPUESTAS_SN, widget=forms.Select(attrs={"class": "form-select"}))
    d2 = forms.ChoiceField(required=False, label="D2", choices=RESPUESTAS_SN, widget=forms.Select(attrs={"class": "form-select"}))
    d3 = forms.ChoiceField(required=False, label="D3", choices=RESPUESTAS_SN, widget=forms.Select(attrs={"class": "form-select"}))
    d4 = forms.ChoiceField(required=False, label="D4", choices=RESPUESTAS_SN, widget=forms.Select(attrs={"class": "form-select"}))
    o1 = forms.ChoiceField(required=False, label="O1", choices=RESPUESTAS_SN, widget=forms.Select(attrs={"class": "form-select"}))
    o2 = forms.ChoiceField(required=False, label="O2", choices=RESPUESTAS_SN, widget=forms.Select(attrs={"class": "form-select"}))
    o3 = forms.ChoiceField(required=False, label="O3", choices=RESPUESTAS_SN, widget=forms.Select(attrs={"class": "form-select"}))
    o4 = forms.ChoiceField(required=False, label="O4", choices=RESPUESTAS_SN, widget=forms.Select(attrs={"class": "form-select"}))
    o5 = forms.ChoiceField(required=False, label="O5", choices=(("", "Sin responder"), ("Sí", "Sí"), ("No", "No"), ("NA", "NA")), widget=forms.Select(attrs={"class": "form-select"}))

    def payload(self):
        return {key: value for key, value in self.cleaned_data.items() if value}

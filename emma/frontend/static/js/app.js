document.body.addEventListener("htmx:responseError", function (event) {
  console.error("HTMX request failed", event.detail);
});

document.addEventListener("click", function (event) {
  const link = event.target.closest("[data-riesgos-loading]");
  if (!link) return;
  const indicator = document.getElementById("riesgos-loading");
  if (indicator) indicator.classList.add("htmx-request");
});

document.addEventListener("submit", function (event) {
  if (!event.target.matches("[data-riesgos-loading]")) return;
  const indicator = document.getElementById("riesgos-loading");
  if (indicator) indicator.classList.add("htmx-request");
});

function sincronizarDetalleFrecuencia(root) {
  (root || document).querySelectorAll("[data-frecuencia-riesgo]").forEach(function (frecuencia) {
    var form = frecuencia.closest("form") || document;
    var detalle = form.querySelector("[data-detalle-frecuencia]");
    if (!detalle) return;

    var esEventual = frecuencia.value === "Eventual";
    detalle.disabled = !esEventual;
    detalle.required = esEventual;
    detalle.setAttribute("aria-disabled", String(!esEventual));
    if (!esEventual) detalle.value = "";
  });
}

function sincronizarResumenMultiseleccion(root) {
  var scope = root || document;
  var selectores = Array.from(scope.querySelectorAll("[data-multi-select]"));
  if (scope.matches && scope.matches("[data-multi-select]")) {
    selectores.unshift(scope);
  }
  selectores.forEach(function (selector) {
    var seleccionados = Array.from(selector.querySelectorAll("[data-multi-select-option]:checked"));
    var resumen = selector.querySelector("[data-multi-select-summary]");
    if (!resumen) return;
    if (!seleccionados.length) {
      resumen.textContent = "Seleccione uno o varios";
      return;
    }
    resumen.textContent = seleccionados.length + (seleccionados.length === 1 ? " seleccionado" : " seleccionados");
  });
}

function actualizarResumenMultiseleccion(input) {
  sincronizarResumenMultiseleccion(input.closest("[data-multi-select]"));
}

function sincronizarEstructuraProcesos(form) {
  if (!form) return;
  var vp = form.querySelector("[data-estructura-vicepresidencia]");
  var procesos = form.querySelector("[data-estructura-proceso]");
  var subprocesos = form.querySelector("[data-estructura-subproceso]");
  var linea = form.querySelector("[data-estructura-linea]");
  var macroproceso = form.querySelector("[data-estructura-macroproceso]");
  var lineaSelect = form.querySelector("[data-estructura-linea-select]");
  var macroprocesoSelect = form.querySelector("[data-estructura-macroproceso-select]");
  if (!vp || !procesos || !subprocesos) return;
  var estructura = JSON.parse(vp.getAttribute("data-estructura-procesos") || "[]");
  var opcionesProceso = Array.from(new Set(estructura.filter(function (x) { return x.vicepresidencia === vp.value; }).map(function (x) { return x.proceso_nivel0; }).filter(Boolean))).sort(function (a, b) { return a.localeCompare(b); });
  // Los tres campos representan una única ruta organizacional. Nunca se
  // comparan por nombre aislado: VP + proceso_nivel0 determinan los
  // subprocesos permitidos.
  var procesoAnterior = procesos.value;
  var esFiltro = procesos.name === "proceso";
  var opcionesProcesoSelect = [new Option(esFiltro ? "Todos" : "Seleccione...", "", false, !procesoAnterior)];
  opcionesProceso.forEach(function (nombre) {
    var opcion = new Option(nombre, nombre, false, procesoAnterior === nombre);
    opcionesProcesoSelect.push(opcion);
  });
  procesos.replaceChildren.apply(procesos, opcionesProcesoSelect);
  procesos.disabled = !vp.value;
  var seleccionados = procesos.value ? [procesos.value] : [];
  var opcionesSub = estructura.filter(function (x) { return x.vicepresidencia === vp.value && seleccionados.indexOf(x.proceso_nivel0) !== -1 && x.proceso_nivel1; }).sort(function (a, b) { return a.proceso_nivel1.localeCompare(b.proceso_nivel1) || String(a.proceso_id).localeCompare(String(b.proceso_id)); });
  var subprocesoAnterior = subprocesos.value;
  var opcionesSubproceso = [new Option(esFiltro ? "Todos" : "Seleccione...", "", false, !subprocesoAnterior)];
  var subprocesosAgregados = {};
  opcionesSub.forEach(function (item) {
    var valorSubproceso = esFiltro ? item.proceso_nivel1 : String(item.proceso_id);
    if (!subprocesosAgregados[valorSubproceso]) {
      opcionesSubproceso.push(new Option(item.proceso_nivel1, valorSubproceso, false, valorSubproceso === subprocesoAnterior));
      subprocesosAgregados[valorSubproceso] = true;
    }
  });
  subprocesos.replaceChildren.apply(subprocesos, opcionesSubproceso);
  subprocesos.disabled = !vp.value || !procesos.value;
  var seleccionado = opcionesSub.find(function (x) { return (esFiltro ? x.proceso_nivel1 : String(x.proceso_id)) === subprocesos.value; });
  if (linea) linea.value = seleccionado ? (seleccionado.linea || "") : "";
  if (macroproceso) macroproceso.value = seleccionado ? (seleccionado.macroproceso || "") : "";
  if (esFiltro) {
    var estructuraFiltrada = estructura.filter(function (item) {
      return item.vicepresidencia === vp.value
        && (!procesos.value || item.proceso_nivel0 === procesos.value)
        && (!subprocesos.value || item.proceso_nivel1 === subprocesos.value);
    });
    [[lineaSelect, "linea"], [macroprocesoSelect, "macroproceso"]].forEach(function (configuracion) {
      var selector = configuracion[0];
      if (!selector) return;
      var valorAnterior = selector.value;
      var valores = Array.from(new Set(estructuraFiltrada.map(function (item) { return item[configuracion[1]]; }).filter(Boolean))).sort(function (a, b) { return a.localeCompare(b); });
      var opciones = [new Option("Todos", "", false, !valorAnterior)];
      valores.forEach(function (valor) { opciones.push(new Option(valor, valor, false, valor === valorAnterior)); });
      selector.replaceChildren.apply(selector, opciones);
      selector.disabled = !vp.value;
    });
  }
}

document.addEventListener("DOMContentLoaded", function () {
  sincronizarDetalleFrecuencia(document);
  sincronizarResumenMultiseleccion(document);
  document.querySelectorAll("form").forEach(sincronizarEstructuraProcesos);
});

document.addEventListener("change", function (event) {
  if (event.target.matches("[data-frecuencia-riesgo]")) {
    sincronizarDetalleFrecuencia(event.target.closest("form"));
  }
  if (event.target.matches("[data-contexto-causa]")) {
    var form = event.target.closest("form");
    var contextos = JSON.parse(event.target.getAttribute("data-contexto-causa") || "{}");
    var contexto = contextos[event.target.value] || {};
    ["linea", "macroproceso", "dueno"].forEach(function (campo) {
      var input = form && form.querySelector("[name='" + campo + "']");
      if (input) input.value = contexto[campo] || "";
    });
  }
  if (event.target.matches("[data-multi-select-option]")) {
    sincronizarResumenMultiseleccion(event.target.closest("[data-multi-select]"));
  }
  if (event.target.matches("[data-estructura-vicepresidencia]")) {
    var formEstructura = event.target.closest("form");
    formEstructura.querySelector("[data-estructura-proceso]").value = "";
    formEstructura.querySelector("[data-estructura-subproceso]").selectedIndex = 0;
    var lineaFiltro = formEstructura.querySelector("[data-estructura-linea-select]");
    var macroFiltro = formEstructura.querySelector("[data-estructura-macroproceso-select]");
    if (lineaFiltro) lineaFiltro.value = "";
    if (macroFiltro) macroFiltro.value = "";
    sincronizarEstructuraProcesos(formEstructura);
  }
  if (event.target.matches("[data-estructura-proceso]")) {
    var formProceso = event.target.closest("form");
    formProceso.querySelector("[data-estructura-subproceso]").selectedIndex = 0;
    var lineaPorProceso = formProceso.querySelector("[data-estructura-linea-select]");
    var macroPorProceso = formProceso.querySelector("[data-estructura-macroproceso-select]");
    if (lineaPorProceso) lineaPorProceso.value = "";
    if (macroPorProceso) macroPorProceso.value = "";
    sincronizarEstructuraProcesos(formProceso);
  }
  if (event.target.matches("[data-estructura-subproceso]")) sincronizarEstructuraProcesos(event.target.closest("form"));
});

document.body.addEventListener("htmx:afterSwap", function (event) {
  sincronizarDetalleFrecuencia(event.target);
  sincronizarResumenMultiseleccion(event.target);
  event.target.querySelectorAll && event.target.querySelectorAll("form").forEach(sincronizarEstructuraProcesos);
});


from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone


SOURCE_SPECS = [
    {
        "code": "SARO",
        "filename": "Catálogo riesgos genéricos SARO_V015.xlsx",
        "frequency": "Mensual",
        "sheet": "Catálogo de Riesgo; Controles Genericos",
        "loader": "_load_saro",
    },
    {
        "code": "ARBOL_PROCESOS",
        "filename": "ARBOLDEPROCESOS.xlsx",
        "frequency": "Mensual",
        "sheet": "Hoja1",
        "loader": "_load_arbol_procesos",
    },
    {
        "code": "ESTRUCTURA",
        "filename": "Estructura.xlsx",
        "frequency": "Mensual",
        "sheet": "Hoja1",
        "loader": "_load_estructura",
    },
    {
        "code": "CLASIFICACIONES",
        "filename": "Clasificaciones.xlsx",
        "frequency": "Mensual",
        "sheet": "Listas",
        "loader": "_load_clasificaciones",
    },
    {
        "code": "GERENCIA_DIRECCION",
        "filename": "geren.xlsx",
        "frequency": "Eventual",
        "sheet": "Hoja1",
        "loader": "_load_gerencias",
    },
    {
        "code": "SISTEMA",
        "filename": "df_sistema.xlsx",
        "frequency": "Eventual",
        "sheet": "Hoja1",
        "loader": "_load_sistemas",
    },
    {
        "code": "PRINCIPIO_COSO",
        "filename": "PrincipioCoso.xlsx",
        "frequency": "Eventual",
        "sheet": "Hoja1",
        "loader": "_load_principios_coso",
    },
    {
        "code": "SUBFACTOR_RIESGO",
        "filename": "subfactor_riesgo.xlsx",
        "frequency": "Eventual",
        "sheet": "Hoja1",
        "loader": "_load_subfactores",
    },
    {
        "code": "CUENTAS_GENERAL",
        "filename": "cuentas.XLSX",
        "frequency": "Eventual",
        "sheet": "Sheet1",
        "loader": "_load_cuentas_general",
    },
    {
        "code": "CUENTAS_RO_2026",
        "filename": "cuentas RO 2026.xlsx",
        "frequency": "Eventual",
        "sheet": "ctas SAP",
        "loader": "_load_cuentas_ro",
    },
    {
        "code": "CUENTAS_OPERATIVO",
        "filename": "Cuentas_Contables_Operativo.xlsx",
        "frequency": "Eventual",
        "sheet": "Hoja1",
        "loader": "_load_cuentas_operativo",
    },
    {
        "code": "CFG_PROBABILIDAD",
        "filename": "datos_probabilidad_historica_completo.xlsx",
        "frequency": "Eventual",
        "sheet": "Sheet1",
        "loader": "_load_cfg_probabilidad",
    },
    {
        "code": "CFG_IMPACTO",
        "filename": "Niveles.xlsx",
        "frequency": "Eventual",
        "sheet": "Hoja1",
        "loader": "_load_cfg_impacto",
    },
    {
        "code": "CFG_SEVERIDAD",
        "filename": "Nivel de Severidad Inherente Riesgo.xlsx",
        "frequency": "Eventual",
        "sheet": "Hoja1",
        "loader": "_load_cfg_severidad",
    },
]


REQUIRED_TABLES = {
    "fuente_dato": "FuenteDato",
    "carga_fuente": "CargaFuente",
    "riesgo_generico": "RiesgoGenerico",
    "cat_proceso": "CatProceso",
    "catalogo": "Catalogo",
    "catalogo_valor": "CatalogoValor",
    "estructura_organizacional": "EstructuraOrganizacional",
    "cuenta_contable": "CuentaContable",
    "cfg_probabilidad": "CfgProbabilidad",
    "cfg_nivel_impacto": "CfgNivelImpacto",
    "cfg_severidad": "CfgSeveridad",
}


IMPACT_COLUMNS = [
    "Impacto Legal",
    "Impacto Reputacional",
    "Impacto servicio al cliente",
    "Información",
    "Continuidad",
    "Contagio",
    "Financiero",
]


@dataclass
class Stats:
    read: int = 0
    valid: int = 0
    rejected: int = 0
    created: int = 0
    updated: int = 0
    inactivated: int = 0
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def merge(self, other: "Stats") -> "Stats":
        self.read += other.read
        self.valid += other.valid
        self.rejected += other.rejected
        self.created += other.created
        self.updated += other.updated
        self.inactivated += other.inactivated
        self.warnings.extend(other.warnings)
        self.details.update(other.details)
        return self


def _is_null(value: Any) -> bool:
    try:
        return pd.isna(value)
    except Exception:
        return value is None


def clean_text(value: Any, *, dash_is_null: bool = False) -> str | None:
    if value is None or _is_null(value):
        return None
    txt = str(value).replace("\u00a0", " ").replace("\ufeff", " ")
    txt = " ".join(txt.strip().split())
    if not txt or txt.lower() in {"nan", "none", "null"}:
        return None
    if dash_is_null and txt in {"-", "–", "—"}:
        return None
    return txt


def normalize_key(value: Any) -> str:
    txt = clean_text(value) or ""
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
    txt = txt.casefold()
    txt = re.sub(r"[^a-z0-9]+", " ", txt)
    return " ".join(txt.split())


def clean_number_code(value: Any, length: int | None = None) -> str | None:
    if value is None or _is_null(value):
        return None

    txt = str(value).strip().replace(",", "")
    try:
        if re.fullmatch(r"-?\d+(?:\.0+)?", txt):
            txt = str(int(float(txt)))
    except Exception:
        pass

    digits = re.sub(r"\D", "", txt)
    if not digits:
        return None
    if length:
        digits = digits.zfill(length)
        if len(digits) > length:
            digits = digits[:length]
    return digits


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_excel(path: Path, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet_name, dtype=object)


def find_column(df: pd.DataFrame, *candidates: str) -> str | None:
    normalized = {normalize_key(c): c for c in df.columns}
    for candidate in candidates:
        key = normalize_key(candidate)
        if key in normalized:
            return normalized[key]
    return None


def require_columns(df: pd.DataFrame, mapping: dict[str, tuple[str, ...]]) -> dict[str, str]:
    found = {}
    missing = []
    for logical_name, candidates in mapping.items():
        col = find_column(df, *candidates)
        if col is None:
            missing.append(f"{logical_name}: {candidates}")
        else:
            found[logical_name] = col
    if missing:
        raise CommandError(
            "Faltan columnas requeridas:\n- " + "\n- ".join(missing)
            + f"\nColumnas disponibles: {list(df.columns)}"
        )
    return found


def unique_clean(values: Iterable[Any], *, dash_is_null: bool = False) -> list[str]:
    seen = set()
    result = []
    for value in values:
        txt = clean_text(value, dash_is_null=dash_is_null)
        if not txt:
            continue
        key = normalize_key(txt)
        if key not in seen:
            seen.add(key)
            result.append(txt)
    return result


def account_key(cuenta_10: str | None, cuenta_6: str | None, descripcion: str) -> str:
    if cuenta_10:
        return f"10:{cuenta_10}"
    if cuenta_6:
        return f"6:{cuenta_6}"
    normalized = normalize_key(descripcion).upper().replace(" ", "_")
    return ("TXT:" + normalized)[:120]


class Command(BaseCommand):
    help = (
        "Migra catalogos, maestros y configuracion de los Excel actuales de EMMA "
        "a PostgreSQL usando los models Django ya creados."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--origen",
            required=True,
            help=(
                "Carpeta raiz que contiene los Excel. Puede ser la carpeta Archivos "
                "o una raiz superior; la busqueda es recursiva."
            ),
        )
        parser.add_argument(
            "--version-reglas",
            dest="version_reglas",
            default="2026.1",
            help="Version de CFG_PROBABILIDAD/CFG_NIVEL_IMPACTO/CFG_SEVERIDAD.",
        )
        parser.add_argument(
            "--vigencia",
            default=date.today().isoformat(),
            help="Fecha de inicio de vigencia de la version de reglas (YYYY-MM-DD).",
        )
        parser.add_argument(
            "--solo",
            nargs="*",
            default=[],
            help=(
                "Opcional. Procesa solo codigos concretos, por ejemplo: "
                "--solo SARO ARBOL_PROCESOS CLASIFICACIONES."
            ),
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Reprocesa aunque el mismo hash ya figure como EXITOSA.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ejecuta validaciones y operaciones, pero revierte la transaccion al final.",
        )
        parser.add_argument(
            "--reporte",
            default=None,
            help="Ruta opcional para escribir un JSON con el resultado de la ejecucion.",
        )
        parser.add_argument(
            "--continuar-con-error",
            action="store_true",
            help="Continua con las demas fuentes si una fuente falla.",
        )

    def handle(self, *args, **options):
        self.M = self._resolve_models()

        root = Path(options["origen"])
        if not root.exists():
            raise CommandError(f"No existe la carpeta de origen: {root}")

        try:
            vigencia = date.fromisoformat(options["vigencia"])
        except ValueError as exc:
            raise CommandError("--vigencia debe tener formato YYYY-MM-DD") from exc

        self.version = str(options["version_reglas"]).strip()
        self.vigencia = vigencia
        self.force = bool(options["force"])
        self.dry_run = bool(options["dry_run"])
        self.continue_on_error = bool(options["continuar_con_error"])

        selected = {x.strip().upper() for x in options["solo"] if x.strip()}
        specs = [
            s for s in SOURCE_SPECS
            if not selected or s["code"].upper() in selected
        ]
        if selected:
            known = {s["code"].upper() for s in SOURCE_SPECS}
            unknown = selected - known
            if unknown:
                raise CommandError(
                    f"Codigos --solo desconocidos: {sorted(unknown)}. "
                    f"Validos: {sorted(known)}"
                )

        file_index = self._index_files(root)

        self.stdout.write(self.style.MIGRATE_HEADING("Migracion Excel -> PostgreSQL EMMA"))
        self.stdout.write(f"Origen: {root}")
        self.stdout.write(f"Version reglas: {self.version}")
        self.stdout.write(f"Vigencia: {self.vigencia}")
        if self.dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN: no se persistiran cambios."))

        if self.dry_run:
            with transaction.atomic():
                results = self._run_specs(specs, file_index)
                transaction.set_rollback(True)
        else:
            results = self._run_specs(specs, file_index)

        report = {
            "timestamp": timezone.now().isoformat(),
            "origen": str(root),
            "version": self.version,
            "vigencia": self.vigencia.isoformat(),
            "dry_run": self.dry_run,
            "results": results,
        }

        if options["reporte"]:
            report_path = Path(options["reporte"])
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            self.stdout.write(f"Reporte: {report_path}")

        failed = [r for r in results if r["status"] == "FALLIDA"]
        if failed:
            raise CommandError(
                f"La migracion termino con {len(failed)} fuente(s) fallida(s). "
                "Revise el detalle anterior o el reporte JSON."
            )

        self.stdout.write(self.style.SUCCESS("Migracion finalizada correctamente."))

    def _resolve_models(self):
        by_table = {
            model._meta.db_table: model
            for model in apps.get_models()
        }

        missing = [table for table in REQUIRED_TABLES if table not in by_table]
        if missing:
            raise CommandError(
                "No encontre models Django para estas tablas: "
                + ", ".join(missing)
                + ". Verifique que la app de EMMA este en INSTALLED_APPS y que db_table coincida."
            )

        class Models:
            pass

        models_ref = Models()
        for table, alias in REQUIRED_TABLES.items():
            setattr(models_ref, alias, by_table[table])
        return models_ref

    def _index_files(self, root: Path) -> dict[str, Path]:
        index = {}
        for path in root.rglob("*"):
            if path.is_file():
                index.setdefault(path.name.casefold(), path)
        return index

    def _find_file(self, file_index: dict[str, Path], filename: str) -> Path:
        path = file_index.get(filename.casefold())
        if path is None:
            raise CommandError(f"No se encontro el archivo requerido: {filename}")
        return path

    def _run_specs(self, specs, file_index):
        results = []

        for spec in specs:
            code = spec["code"]
            try:
                path = self._find_file(file_index, spec["filename"])
            except Exception as exc:
                result = {
                    "source": code,
                    "filename": spec["filename"],
                    "status": "FALLIDA",
                    "error": str(exc),
                }
                results.append(result)
                self.stderr.write(self.style.ERROR(f"[{code}] {exc}"))
                if not self.continue_on_error:
                    raise
                continue

            try:
                result = self._process_source(spec, path)
                results.append(result)
            except Exception as exc:
                result = {
                    "source": code,
                    "filename": str(path),
                    "status": "FALLIDA",
                    "error": f"{type(exc).__name__}: {exc}",
                }
                results.append(result)
                self.stderr.write(self.style.ERROR(f"[{code}] {type(exc).__name__}: {exc}"))
                if not self.continue_on_error:
                    raise

        return results

    def _process_source(self, spec, path: Path) -> dict[str, Any]:
        FuenteDato = self.M.FuenteDato
        CargaFuente = self.M.CargaFuente

        fuente, _ = FuenteDato.objects.update_or_create(
            codigo_fuente=spec["code"],
            defaults={
                "nombre_fuente": spec["filename"],
                "frecuencia": spec["frequency"],
                "hoja_principal": spec["sheet"],
                "activo": True,
            },
        )

        file_hash = sha256_file(path)

        if not self.force:
            already_loaded = CargaFuente.objects.filter(
                fuente=fuente,
                hash_archivo=file_hash,
                estado="EXITOSA",
            ).exists()
            if already_loaded:
                self.stdout.write(
                    self.style.WARNING(
                        f"[{spec['code']}] omitido: el mismo hash ya fue cargado exitosamente."
                    )
                )
                return {
                    "source": spec["code"],
                    "filename": str(path),
                    "hash": file_hash,
                    "status": "OMITIDA_MISMO_HASH",
                }

        carga = CargaFuente.objects.create(
            fuente=fuente,
            fecha_carga=timezone.now(),
            hash_archivo=file_hash,
            estado="EN_PROCESO",
            registros_leidos=0,
            registros_validos=0,
            registros_rechazados=0,
        )

        self.stdout.write(self.style.MIGRATE_LABEL(f"[{spec['code']}] {path.name}"))

        try:
            loader = getattr(self, spec["loader"])
            with transaction.atomic():
                stats: Stats = loader(path, fuente)

            carga.estado = "EXITOSA"
            carga.registros_leidos = stats.read
            carga.registros_validos = stats.valid
            carga.registros_rechazados = stats.rejected
            carga.save(
                update_fields=[
                    "estado",
                    "registros_leidos",
                    "registros_validos",
                    "registros_rechazados",
                ]
            )

            for warning in stats.warnings:
                self.stdout.write(self.style.WARNING(f"  AVISO: {warning}"))

            self.stdout.write(
                self.style.SUCCESS(
                    f"  OK | leidos={stats.read} validos={stats.valid} "
                    f"rechazados={stats.rejected} creados={stats.created} "
                    f"actualizados={stats.updated} inactivados={stats.inactivated}"
                )
            )

            return {
                "source": spec["code"],
                "filename": str(path),
                "hash": file_hash,
                "status": "EXITOSA",
                **stats.__dict__,
            }

        except Exception:
            carga.estado = "FALLIDA"
            carga.save(update_fields=["estado"])
            raise

    def _ensure_catalog(self, code: str, name: str, description: str | None = None):
        Catalogo = self.M.Catalogo
        catalog, created = Catalogo.objects.update_or_create(
            codigo_catalogo=code,
            defaults={
                "nombre": name,
                "descripcion": description,
                "activo": True,
            },
        )
        return catalog, created

    def _upsert_catalog_value(
        self,
        *,
        catalog,
        description: str,
        code: str | None = None,
        parent=None,
        level: int | None = None,
        metadata: dict | None = None,
    ):
        CatalogoValor = self.M.CatalogoValor

        if code:
            qs = CatalogoValor.objects.filter(catalogo=catalog, codigo=code)
        else:
            qs = CatalogoValor.objects.filter(
                catalogo=catalog,
                parent_valor=parent,
                nivel=level,
                descripcion=description,
            )

        obj = qs.order_by("pk").first()
        if obj:
            obj.descripcion = description
            obj.parent_valor = parent
            obj.nivel = level
            obj.metadata_jsonb = metadata
            obj.activo = True
            obj.save(
                update_fields=[
                    "descripcion",
                    "parent_valor",
                    "nivel",
                    "metadata_jsonb",
                    "activo",
                ]
            )
            qs.exclude(pk=obj.pk).update(activo=False)
            return obj, False

        obj = CatalogoValor.objects.create(
            catalogo=catalog,
            codigo=code,
            descripcion=description,
            parent_valor=parent,
            nivel=level,
            orden=None,
            activo=True,
            metadata_jsonb=metadata,
        )
        return obj, True

    def _sync_simple_catalog(
        self,
        code: str,
        name: str,
        values: Iterable[Any],
        *,
        description: str | None = None,
    ) -> Stats:
        CatalogoValor = self.M.CatalogoValor
        catalog, catalog_created = self._ensure_catalog(code, name, description)

        stats = Stats()
        stats.created += int(catalog_created)
        stats.inactivated += CatalogoValor.objects.filter(catalogo=catalog, activo=True).update(activo=False)

        cleaned = unique_clean(values)
        stats.read = len(cleaned)
        stats.valid = len(cleaned)

        existing = {}
        for obj in CatalogoValor.objects.filter(
            catalogo=catalog,
            parent_valor__isnull=True,
            nivel=1,
        ):
            existing.setdefault(normalize_key(obj.descripcion), obj)

        to_create = []
        to_update = []
        for value in cleaned:
            key = normalize_key(value)
            obj = existing.get(key)
            if obj:
                obj.descripcion = value
                obj.parent_valor = None
                obj.nivel = 1
                obj.metadata_jsonb = None
                obj.activo = True
                to_update.append(obj)
            else:
                to_create.append(
                    CatalogoValor(
                        catalogo=catalog,
                        descripcion=value,
                        parent_valor=None,
                        nivel=1,
                        orden=None,
                        activo=True,
                        metadata_jsonb=None,
                    )
                )

        if to_create:
            CatalogoValor.objects.bulk_create(to_create, batch_size=1000)
        if to_update:
            CatalogoValor.objects.bulk_update(
                to_update,
                ["descripcion", "parent_valor", "nivel", "metadata_jsonb", "activo"],
                batch_size=1000,
            )

        stats.created += len(to_create)
        stats.updated += len(to_update)

        return stats

    def _sync_hierarchy(
        self,
        code: str,
        name: str,
        paths: Iterable[Iterable[Any]],
        *,
        description: str | None = None,
        dash_is_null: bool = True,
    ) -> Stats:
        CatalogoValor = self.M.CatalogoValor
        catalog, catalog_created = self._ensure_catalog(code, name, description)

        stats = Stats()
        stats.created += int(catalog_created)
        stats.inactivated += CatalogoValor.objects.filter(catalogo=catalog, activo=True).update(activo=False)

        seen_paths = set()
        valid_paths = []

        for raw_path in paths:
            cleaned = []
            for value in raw_path:
                txt = clean_text(value, dash_is_null=dash_is_null)
                cleaned.append(txt)

            while cleaned and cleaned[-1] is None:
                cleaned.pop()
            if not cleaned:
                continue
            if any(v is None for v in cleaned):
                continue

            key = tuple(normalize_key(v) for v in cleaned)
            if key not in seen_paths:
                seen_paths.add(key)
                valid_paths.append(cleaned)

        stats.read = len(valid_paths)
        stats.valid = len(valid_paths)

        node_defs = {}
        max_level = 0
        for path in valid_paths:
            prefix = []
            for level, value in enumerate(path, start=1):
                prefix.append(normalize_key(value))
                prefix_key = tuple(prefix)
                parent_key = tuple(prefix[:-1]) or None
                node_defs.setdefault(
                    prefix_key,
                    {
                        "description": value,
                        "parent_key": parent_key,
                        "level": level,
                    },
                )
                max_level = max(max_level, level)

        existing = {}
        for obj in CatalogoValor.objects.filter(catalogo=catalog).select_related("parent_valor"):
            key = (
                obj.parent_valor_id,
                obj.nivel,
                normalize_key(obj.descripcion),
            )
            existing.setdefault(key, obj)

        node_cache = {}
        for level in range(1, max_level + 1):
            level_items = [
                (prefix_key, data)
                for prefix_key, data in node_defs.items()
                if data["level"] == level
            ]

            to_create = []
            create_prefixes = []
            to_update = []

            for prefix_key, data in level_items:
                parent = node_cache.get(data["parent_key"]) if data["parent_key"] else None
                existing_key = (
                    parent.pk if parent else None,
                    level,
                    normalize_key(data["description"]),
                )
                obj = existing.get(existing_key)
                if obj:
                    obj.descripcion = data["description"]
                    obj.parent_valor = parent
                    obj.nivel = level
                    obj.metadata_jsonb = None
                    obj.activo = True
                    to_update.append(obj)
                    node_cache[prefix_key] = obj
                else:
                    to_create.append(
                        CatalogoValor(
                            catalogo=catalog,
                            descripcion=data["description"],
                            parent_valor=parent,
                            nivel=level,
                            orden=None,
                            activo=True,
                            metadata_jsonb=None,
                        )
                    )
                    create_prefixes.append(prefix_key)

            if to_create:
                created_objects = CatalogoValor.objects.bulk_create(to_create, batch_size=1000)
                for prefix_key, obj in zip(create_prefixes, created_objects, strict=True):
                    node_cache[prefix_key] = obj
                stats.created += len(created_objects)

            if to_update:
                CatalogoValor.objects.bulk_update(
                    to_update,
                    ["descripcion", "parent_valor", "nivel", "metadata_jsonb", "activo"],
                    batch_size=1000,
                )
                stats.updated += len(to_update)

        return stats

    def _upsert_by_filter(self, model, lookup: dict, defaults: dict):
        obj = model.objects.filter(**lookup).order_by("pk").first()
        if obj:
            for field_name, value in defaults.items():
                setattr(obj, field_name, value)
            obj.save(update_fields=list(defaults.keys()))
            model.objects.filter(**lookup).exclude(pk=obj.pk).update(activo=False)
            return obj, False

        data = {**lookup, **defaults}
        return model.objects.create(**data), True

    def _replace_accounts(self, fuente, records: list[dict[str, Any]]) -> Stats:
        CuentaContable = self.M.CuentaContable
        stats = Stats(read=len(records))

        stats.inactivated = CuentaContable.objects.filter(fuente=fuente, activo=True).update(activo=False)

        objects = []
        for rec in records:
            descripcion = clean_text(rec.get("descripcion"))
            cuenta_10 = clean_number_code(rec.get("cuenta_10"), 10) if rec.get("cuenta_10") else None
            cuenta_6 = clean_number_code(rec.get("cuenta_6"), 6) if rec.get("cuenta_6") else None

            if not descripcion:
                stats.rejected += 1
                continue

            objects.append(
                CuentaContable(
                    fuente=fuente,
                    cuenta_10=cuenta_10,
                    cuenta_6=cuenta_6,
                    descripcion=descripcion[:500],
                    clave_homologacion=account_key(cuenta_10, cuenta_6, descripcion),
                    activo=True,
                )
            )

        CuentaContable.objects.bulk_create(objects, batch_size=1000)
        stats.valid = len(objects)
        stats.created = len(objects)
        return stats

    def _prepare_cfg_version(self, model):
        previous_end = self.vigencia - timedelta(days=1)

        model.objects.filter(activo=True).exclude(version=self.version).update(
            activo=False,
            fecha_fin_vigencia=previous_end,
        )

        return model.objects.filter(version=self.version, activo=True).update(activo=False)

    def _load_saro(self, path: Path, fuente) -> Stats:
        RiesgoGenerico = self.M.RiesgoGenerico
        CatalogoValor = self.M.CatalogoValor

        df_risk = read_excel(path, "Catálogo de Riesgo")
        cols = require_columns(
            df_risk,
            {
                "codigo": ("No",),
                "nombre": ("Riesgos Genéricos", "Riesgos Genericos"),
            },
        )

        stats = Stats(read=len(df_risk))
        stats.inactivated += RiesgoGenerico.objects.filter(activo=True).update(activo=False)

        valid_risk = 0
        for _, row in df_risk.iterrows():
            codigo = clean_text(row[cols["codigo"]])
            nombre = clean_text(row[cols["nombre"]])
            if not codigo or not nombre:
                stats.rejected += 1
                continue

            obj = RiesgoGenerico.objects.filter(codigo=codigo).order_by("pk").first()
            if obj:
                obj.nombre = nombre[:500]
                obj.activo = True
                obj.save(update_fields=["nombre", "activo"])
                stats.updated += 1
            else:
                RiesgoGenerico.objects.create(codigo=codigo[:50], nombre=nombre[:500], activo=True)
                stats.created += 1
            valid_risk += 1

        df_control = read_excel(path, "Controles Genericos")
        stats.read += len(df_control)

        control_col = find_column(df_control, "Código control homologado con Grupo Aval")
        if not control_col:
            raise CommandError(
                "No se encontro la columna de controles genericos en la hoja 'Controles Genericos'."
            )

        catalog, catalog_created = self._ensure_catalog(
            "CONTROL_GENERICO",
            "Control generico homologado",
            "Controles genericos/homologados Grupo Aval.",
        )
        stats.created += int(catalog_created)
        stats.inactivated += CatalogoValor.objects.filter(catalogo=catalog, activo=True).update(activo=False)

        valid_control = 0
        pattern = re.compile(r"^\s*(CTR-\d+)\s*-\s*(.+?)\s*$", re.I)

        for value in df_control[control_col].tolist():
            raw = clean_text(value)
            if not raw:
                continue
            match = pattern.match(raw)
            if match:
                code = match.group(1).upper()
                desc = clean_text(match.group(2)) or raw
            else:
                code = None
                desc = raw
                stats.warnings.append(f"Control generico sin patron CTR-xx; se cargo sin codigo: {raw[:80]}")

            _, created = self._upsert_catalog_value(catalog=catalog, code=code, description=desc, level=1)
            if created:
                stats.created += 1
            else:
                stats.updated += 1
            valid_control += 1

        stats.valid = valid_risk + valid_control
        return stats

    def _load_arbol_procesos(self, path: Path, fuente) -> Stats:
        CatProceso = self.M.CatProceso

        df = read_excel(path, "Hoja1")
        cols = require_columns(
            df,
            {
                "linea": ("LINEA",),
                "macroproceso": ("MACROPROCESO",),
                "proceso": ("PROCESO",),
                "subproceso": ("SUBPROCESO",),
                "vicepresidencia": ("VICEPRESIDENCIA",),
            },
        )

        stats = Stats(read=len(df))
        stats.inactivated = CatProceso.objects.filter(activo=True).update(activo=False)

        unique_rows = []
        seen = set()

        for _, row in df.iterrows():
            vp = clean_text(row[cols["vicepresidencia"]])
            proceso = clean_text(row[cols["proceso"]])
            subproceso = clean_text(row[cols["subproceso"]])
            macro = clean_text(row[cols["macroproceso"]])
            linea = clean_text(row[cols["linea"]])

            if not vp or not proceso:
                stats.rejected += 1
                continue

            key = tuple(normalize_key(x) for x in [vp, macro, proceso, subproceso, linea])
            if key in seen:
                continue
            seen.add(key)
            unique_rows.append((vp, macro, proceso, subproceso, linea))

        existing = {}
        for obj in CatProceso.objects.all().only(
            "proceso_id",
            "vicepresidencia",
            "proceso_nivel0",
            "proceso_nivel1",
            "macroproceso",
            "linea",
            "activo",
        ):
            key = tuple(
                normalize_key(x)
                for x in [
                    obj.vicepresidencia,
                    obj.macroproceso,
                    obj.proceso_nivel0,
                    obj.proceso_nivel1,
                    obj.linea,
                ]
            )
            existing.setdefault(key, obj)

        to_create = []
        to_update = []
        for vp, macro, proceso, subproceso, linea in unique_rows:
            values = {
                "vicepresidencia": vp[:250],
                "proceso_nivel0": proceso[:250],
                "proceso_nivel1": subproceso[:250] if subproceso else None,
                "proceso_nivel2": None,
                "descripcion": None,
                "parent_proceso": None,
                "macroproceso": macro[:255] if macro else None,
                "linea": linea[:255] if linea else None,
                "activo": True,
            }
            key = tuple(
                normalize_key(x)
                for x in [
                    values["vicepresidencia"],
                    values["macroproceso"],
                    values["proceso_nivel0"],
                    values["proceso_nivel1"],
                    values["linea"],
                ]
            )
            obj = existing.get(key)
            if obj:
                for field_name, value in values.items():
                    setattr(obj, field_name, value)
                to_update.append(obj)
            else:
                to_create.append(CatProceso(**values))

        if to_create:
            CatProceso.objects.bulk_create(to_create, batch_size=1000)
        if to_update:
            CatProceso.objects.bulk_update(
                to_update,
                [
                    "vicepresidencia",
                    "proceso_nivel0",
                    "proceso_nivel1",
                    "proceso_nivel2",
                    "descripcion",
                    "parent_proceso",
                    "macroproceso",
                    "linea",
                    "activo",
                ],
                batch_size=1000,
            )

        stats.created = len(to_create)
        stats.updated = len(to_update)

        stats.valid = len(unique_rows)
        return stats

    def _load_estructura(self, path: Path, fuente) -> Stats:
        Estructura = self.M.EstructuraOrganizacional

        df = read_excel(path, "Hoja1")
        cols = require_columns(
            df,
            {
                "gerencia": ("Gerencia/Dirección", "Gerencia/Direccion"),
                "cargo": ("Cargo Aprobado por Estructura",),
            },
        )

        stats = Stats(read=len(df))
        stats.inactivated = Estructura.objects.filter(activo=True).update(activo=False)

        seen = set()
        valid_rows = []

        for _, row in df.iterrows():
            gerencia = clean_text(row[cols["gerencia"]])
            cargo = clean_text(row[cols["cargo"]])
            if not gerencia or not cargo:
                stats.rejected += 1
                continue

            key = (normalize_key(gerencia), normalize_key(cargo))
            if key in seen:
                continue
            seen.add(key)
            valid_rows.append((gerencia[:255], cargo[:255]))

        existing = {}
        for obj in Estructura.objects.all().only(
            "estructura_id",
            "gerencia_direccion",
            "cargo_aprobado",
            "activo",
        ):
            key = (
                normalize_key(obj.gerencia_direccion),
                normalize_key(obj.cargo_aprobado),
            )
            existing.setdefault(key, obj)

        to_create = []
        to_update = []
        for gerencia, cargo in valid_rows:
            key = (normalize_key(gerencia), normalize_key(cargo))
            obj = existing.get(key)
            if obj:
                obj.activo = True
                to_update.append(obj)
            else:
                to_create.append(
                    Estructura(
                        gerencia_direccion=gerencia,
                        cargo_aprobado=cargo,
                        activo=True,
                    )
                )

        if to_create:
            Estructura.objects.bulk_create(to_create, batch_size=1000)
        if to_update:
            Estructura.objects.bulk_update(to_update, ["activo"], batch_size=1000)

        stats.created = len(to_create)
        stats.updated = len(to_update)
        stats.valid = len(valid_rows)
        return stats

    def _load_clasificaciones(self, path: Path, fuente) -> Stats:
        df = read_excel(path, "Listas")
        stats = Stats(read=len(df))

        simple_defs = [
            ("SEGMENTO", "Segmento", ("Segmento",)),
            ("TIPO_PERDIDA", "Tipo de perdida", ("Tipo de Pérdida", "Tipo de Perdida")),
            ("DIVISA", "Divisa", ("Divisa",)),
            ("PRODUCTO", "Producto", ("Productos", "Producto")),
            ("SITIO", "Sitio", ("Sitio",)),
            ("CANAL", "Canal", ("Canal",)),
            ("CLASE_EVENTO", "Clases / tipologias generales del evento", ("Clases",)),
        ]

        for cat_code, cat_name, candidates in simple_defs:
            col = find_column(df, *candidates)
            if not col:
                stats.warnings.append(f"Clasificaciones: no se encontro columna para {cat_code}.")
                continue
            stats.merge(self._sync_simple_catalog(cat_code, cat_name, df[col].tolist()))

        c_pais = find_column(df, "Pais", "País")
        c_depto = find_column(df, "DEPARTAMENTO", "Departamento")
        c_ciudad = find_column(df, "CIUDAD", "Ciudad")
        if c_pais and c_depto and c_ciudad:
            stats.merge(
                self._sync_hierarchy(
                    "UBICACION_GEOGRAFICA",
                    "Ubicacion geografica",
                    df[[c_pais, c_depto, c_ciudad]].itertuples(index=False, name=None),
                )
            )

        c_lop1 = find_column(df, "Líneas Operativas (nivel 1)")
        c_lop2 = find_column(df, "Sublínea (nivel 2)", "Sublinea (nivel 2)")
        if c_lop1 and c_lop2:
            stats.merge(
                self._sync_hierarchy(
                    "LINEA_OPERATIVA",
                    "Linea operativa",
                    df[[c_lop1, c_lop2]].itertuples(index=False, name=None),
                )
            )

        c_ln1 = find_column(df, "Línea de negocio N1", "Linea de negocio N1")
        c_ln2 = find_column(df, "Línea de negocio N2", "Linea de negocio N2")
        if c_ln1 and c_ln2:
            stats.merge(
                self._sync_hierarchy(
                    "LINEA_NEGOCIO",
                    "Linea de negocio",
                    df[[c_ln1, c_ln2]].itertuples(index=False, name=None),
                )
            )

        c_t1 = find_column(df, "Clasificación de Riesgos Operacionales(N1)")
        c_t2 = find_column(df, "Evento de riesgo operacional (Nivel 2)")
        c_t3 = find_column(df, "Evento de Riesgo Operacional (Nivel 3)")
        if c_t1 and c_t2 and c_t3:
            stats.merge(
                self._sync_hierarchy(
                    "TIPO_EVENTO",
                    "Tipologia de evento operacional",
                    df[[c_t1, c_t2, c_t3]].itertuples(index=False, name=None),
                )
            )

        c_ger = find_column(df, "Gerencia")
        c_det = find_column(df, "Detalle")
        if c_ger and c_det:
            stats.merge(
                self._sync_hierarchy(
                    "GERENCIA_EVENTO",
                    "Gerencia / detalle de evento",
                    df[[c_ger, c_det]].itertuples(index=False, name=None),
                    dash_is_null=True,
                )
            )

        stats.merge(self._sync_oficinas(df))

        risk_code_col = find_column(df, "Código de riesgo genérico", "Codigo de riesgo generico")
        if risk_code_col:
            source_codes = set(unique_clean(df[risk_code_col].tolist()))
            db_codes = set(
                self.M.RiesgoGenerico.objects.filter(activo=True).values_list("codigo", flat=True)
            )
            unknown = sorted(source_codes - db_codes)
            if unknown:
                stats.warnings.append(
                    "Clasificaciones contiene codigos de riesgo generico no activos en RIESGO_GENERICO: "
                    f"{unknown[:20]}" + (" ..." if len(unknown) > 20 else "")
                )

        c_account = find_column(df, "Codigo de la cuenta", "Código de la cuenta")
        c_account_desc = find_column(df, "Descripción", "Descripcion")
        if c_account and c_account_desc:
            records = []
            for _, row in df.iterrows():
                code6 = clean_number_code(row[c_account], 6)
                desc = clean_text(row[c_account_desc])
                if code6 and desc:
                    records.append({"cuenta_10": None, "cuenta_6": code6, "descripcion": desc})
            account_stats = self._replace_accounts(fuente, records)
            stats.created += account_stats.created
            stats.inactivated += account_stats.inactivated
            stats.details["cuentas_desde_clasificaciones"] = account_stats.valid

        source_used_cols = [
            c for c in [
                find_column(df, "Segmento"),
                find_column(df, "Tipo de Pérdida"),
                find_column(df, "Divisa"),
                find_column(df, "Productos"),
                find_column(df, "Sitio"),
                find_column(df, "Canal"),
                c_pais, c_depto, c_ciudad,
                c_lop1, c_lop2, c_ln1, c_ln2,
                c_t1, c_t2, c_t3,
                c_ger, c_det, c_account,
            ]
            if c
        ]
        if source_used_cols:
            mask = df[source_used_cols].notna().any(axis=1)
            stats.valid = int(mask.sum())
            stats.rejected = int(len(df) - mask.sum())
        stats.read = len(df)

        return stats

    def _sync_oficinas(self, df: pd.DataFrame) -> Stats:
        CatalogoValor = self.M.CatalogoValor

        c_office = find_column(df, "OFICINA")
        if not c_office:
            return Stats()

        c_code = find_column(df, "CÓDIGO DE OFICINA", "CODIGO DE OFICINA")
        c_name = find_column(df, "NOMBRE DE OFICINA")
        c_address = find_column(df, "DIRECCION", "DIRECCIÓN")
        c_city = find_column(df, "CIUDAD")
        c_dept = find_column(df, "DEPARTAMENTO")

        catalog, catalog_created = self._ensure_catalog(
            "OFICINA",
            "Oficina",
            "Oficinas utilizadas por el modulo de eventos.",
        )
        stats = Stats(created=int(catalog_created))
        stats.inactivated = CatalogoValor.objects.filter(catalogo=catalog, activo=True).update(activo=False)

        seen = set()
        rows = []
        for _, row in df.iterrows():
            office = clean_text(row[c_office])
            if not office:
                continue

            code = clean_number_code(row[c_code]) if c_code else None
            metadata = {
                "nombre_oficina": clean_text(row[c_name]) if c_name else None,
                "direccion": clean_text(row[c_address]) if c_address else None,
                "ciudad": clean_text(row[c_city]) if c_city else None,
                "departamento": clean_text(row[c_dept]) if c_dept else None,
            }
            metadata = {k: v for k, v in metadata.items() if v is not None}

            key = code or normalize_key(office)
            if key in seen:
                continue
            seen.add(key)
            rows.append((office, code, metadata))

        existing = {}
        for obj in CatalogoValor.objects.filter(catalogo=catalog, parent_valor__isnull=True, nivel=1):
            if obj.codigo:
                existing.setdefault(("code", obj.codigo), obj)
            existing.setdefault(("desc", normalize_key(obj.descripcion)), obj)

        to_create = []
        to_update = []
        for office, code, metadata in rows:
            obj = existing.get(("code", code)) if code else None
            if obj is None:
                obj = existing.get(("desc", normalize_key(office)))
            if obj:
                obj.codigo = code
                obj.descripcion = office
                obj.parent_valor = None
                obj.nivel = 1
                obj.metadata_jsonb = metadata
                obj.activo = True
                to_update.append(obj)
            else:
                to_create.append(
                    CatalogoValor(
                        catalogo=catalog,
                        codigo=code,
                        descripcion=office,
                        parent_valor=None,
                        nivel=1,
                        orden=None,
                        activo=True,
                        metadata_jsonb=metadata,
                    )
                )

        if to_create:
            CatalogoValor.objects.bulk_create(to_create, batch_size=1000)
        if to_update:
            CatalogoValor.objects.bulk_update(
                to_update,
                ["codigo", "descripcion", "parent_valor", "nivel", "metadata_jsonb", "activo"],
                batch_size=1000,
            )

        stats.created += len(to_create)
        stats.updated += len(to_update)

        stats.read = len(seen)
        stats.valid = len(seen)
        return stats

    def _load_gerencias(self, path: Path, fuente) -> Stats:
        df = read_excel(path, "Hoja1")
        col = find_column(df, "Gerencia/Dirección", "Gerencia/Direccion")
        if not col:
            raise CommandError("geren.xlsx no contiene 'Gerencia/Direccion'.")
        return self._sync_simple_catalog(
            "GERENCIA_DIRECCION",
            "Gerencia / Direccion - Matriz",
            df[col].tolist(),
            description="Dominio usado por Matriz; no se homologa automaticamente con GERENCIA_EVENTO.",
        )

    def _load_sistemas(self, path: Path, fuente) -> Stats:
        df = read_excel(path, "Hoja1")
        col = find_column(df, "Nombre")
        if not col:
            raise CommandError("df_sistema.xlsx no contiene la columna 'Nombre'.")
        return self._sync_simple_catalog("SISTEMA", "Sistema", df[col].tolist())

    def _load_principios_coso(self, path: Path, fuente) -> Stats:
        df = read_excel(path, "Hoja1")
        col = find_column(df, "Principios COSO")
        if not col:
            raise CommandError("PrincipioCoso.xlsx no contiene 'Principios COSO'.")
        return self._sync_simple_catalog("PRINCIPIO_COSO", "Principio COSO", df[col].tolist())

    def _load_subfactores(self, path: Path, fuente) -> Stats:
        df = read_excel(path, "Hoja1")
        col = find_column(df, "Subfactor de riesgo")
        if not col:
            raise CommandError("subfactor_riesgo.xlsx no contiene 'Subfactor de riesgo'.")
        return self._sync_simple_catalog("SUBFACTOR_RIESGO", "Subfactor de riesgo", df[col].tolist())

    def _load_cuentas_general(self, path: Path, fuente) -> Stats:
        df = read_excel(path, "Sheet1")
        col = find_column(df, "Texto p.posición balance/PyG", "Texto p.posicion balance/PyG")
        if not col:
            raise CommandError("cuentas.XLSX no contiene 'Texto p.posicion balance/PyG'.")

        records = []
        for value in df[col].tolist():
            text = clean_text(value)
            if not text:
                continue

            match = re.match(r"^\s*(\d{6,10})\s*(?:-| )?\s*(.*)$", text)
            if match:
                code = match.group(1)
                desc = clean_text(match.group(2)) or text
                cuenta_10 = code.zfill(10) if len(code) > 6 else None
                cuenta_6 = cuenta_10[:6] if cuenta_10 else code.zfill(6)
            else:
                cuenta_10 = None
                cuenta_6 = None
                desc = text

            records.append({"cuenta_10": cuenta_10, "cuenta_6": cuenta_6, "descripcion": desc})

        stats = self._replace_accounts(fuente, records)
        stats.read = len(df)
        stats.rejected = max(0, len(df) - stats.valid)
        return stats

    def _load_cuentas_ro(self, path: Path, fuente) -> Stats:
        df = read_excel(path, "ctas SAP")
        cols = require_columns(
            df,
            {
                "cuenta": ("Cuenta",),
                "nombre": ("Nombre",),
                "cuenta6": ("Cuenta a 6 dígitos", "Cuenta a 6 digitos"),
            },
        )

        records = []
        for _, row in df.iterrows():
            cuenta10 = clean_number_code(row[cols["cuenta"]], 10)
            cuenta6 = clean_number_code(row[cols["cuenta6"]], 6)
            nombre = clean_text(row[cols["nombre"]])
            if cuenta10 and cuenta6 and nombre:
                records.append({"cuenta_10": cuenta10, "cuenta_6": cuenta6, "descripcion": nombre})

        stats = self._replace_accounts(fuente, records)
        stats.read = len(df)
        stats.rejected = max(0, len(df) - stats.valid)
        return stats

    def _load_cuentas_operativo(self, path: Path, fuente) -> Stats:
        df = read_excel(path, "Hoja1")
        cols = require_columns(
            df,
            {
                "label": ("Cuenta y Descripción", "Cuenta y Descripcion"),
                "cuenta6": ("CuentaDigitos",),
            },
        )

        records = []
        for _, row in df.iterrows():
            label = clean_text(row[cols["label"]])
            cuenta6 = clean_number_code(row[cols["cuenta6"]], 6)
            if not label:
                continue

            match = re.match(r"^\s*(\d{6,10})\s*-\s*(.+)$", label)
            if match:
                cuenta10 = clean_number_code(match.group(1), 10)
                desc = clean_text(match.group(2))
            else:
                cuenta10 = None
                desc = label

            if desc:
                records.append({"cuenta_10": cuenta10, "cuenta_6": cuenta6, "descripcion": desc})

        stats = self._replace_accounts(fuente, records)
        stats.read = len(df)
        stats.rejected = max(0, len(df) - stats.valid)
        return stats

    def _load_cfg_probabilidad(self, path: Path, fuente) -> Stats:
        Model = self.M.CfgProbabilidad
        df = read_excel(path, "Sheet1")
        cols = require_columns(
            df,
            {
                "complejidad": ("Complejidad",),
                "entorno": ("Condiciones del entorno",),
                "nivel": ("Nivel",),
                "prob": ("Probabilidad Inherente Riesgo",),
            },
        )

        stats = Stats(read=len(df))
        stats.inactivated = self._prepare_cfg_version(Model)

        valid = 0
        for _, row in df.iterrows():
            nivel = clean_text(row[cols["nivel"]])
            prob = clean_text(row[cols["prob"]])
            if not nivel or not prob:
                stats.rejected += 1
                continue

            lookup = {
                "version": self.version,
                "complejidad": clean_text(row[cols["complejidad"]]),
                "condiciones_entorno": clean_text(row[cols["entorno"]]),
                "nivel": nivel[:100],
            }
            defaults = {
                "probabilidad_inherente": prob[:255],
                "activo": True,
                "fecha_inicio_vigencia": self.vigencia,
                "fecha_fin_vigencia": None,
            }

            _, created = Model.objects.update_or_create(**lookup, defaults=defaults)
            if created:
                stats.created += 1
            else:
                stats.updated += 1
            valid += 1

        stats.valid = valid
        return stats

    def _load_cfg_impacto(self, path: Path, fuente) -> Stats:
        Model = self.M.CfgNivelImpacto
        df = read_excel(path, "Hoja1")
        level_col = find_column(df, "Nivel")
        inherent_col = find_column(df, "Impacto Inherente")
        if not level_col or not inherent_col:
            raise CommandError("Niveles.xlsx debe contener 'Nivel' e 'Impacto Inherente'.")

        impact_cols = {}
        for name in IMPACT_COLUMNS:
            col = find_column(df, name)
            if col:
                impact_cols[name] = col
            else:
                raise CommandError(f"Niveles.xlsx no contiene la columna requerida: {name}")

        stats = Stats(read=len(df))
        stats.inactivated = self._prepare_cfg_version(Model)

        valid = 0
        for _, row in df.iterrows():
            nivel = clean_text(row[level_col])
            if nivel is None:
                continue

            impacto_inherente = clean_text(row[inherent_col])

            for tipo, col in impact_cols.items():
                criterio = clean_text(row[col])
                if criterio is None:
                    continue

                lookup = {
                    "version": self.version,
                    "tipo_impacto": tipo[:100],
                    "nivel": nivel[:100],
                }
                defaults = {
                    "criterio": criterio[:2000],
                    "impacto_inherente": impacto_inherente[:255] if impacto_inherente else None,
                    "activo": True,
                    "fecha_inicio_vigencia": self.vigencia,
                    "fecha_fin_vigencia": None,
                }
                _, created = Model.objects.update_or_create(**lookup, defaults=defaults)
                if created:
                    stats.created += 1
                else:
                    stats.updated += 1
                valid += 1

        stats.valid = valid
        stats.rejected = 0
        return stats

    def _load_cfg_severidad(self, path: Path, fuente) -> Stats:
        Model = self.M.CfgSeveridad
        df = read_excel(path, "Hoja1")
        cols = require_columns(
            df,
            {
                "concat": ("Concatenado",),
                "sev": ("Severidad",),
            },
        )

        stats = Stats(read=len(df))
        stats.inactivated = self._prepare_cfg_version(Model)

        valid = 0
        for _, row in df.iterrows():
            concat = clean_text(row[cols["concat"]])
            sev = clean_text(row[cols["sev"]])
            if not concat or not sev:
                stats.rejected += 1
                continue

            concat = re.sub(r"\s+", "", concat)

            lookup = {
                "version": self.version,
                "concatenado": concat[:100],
            }
            defaults = {
                "severidad": sev[:100],
                "activo": True,
                "fecha_inicio_vigencia": self.vigencia,
                "fecha_fin_vigencia": None,
            }

            _, created = Model.objects.update_or_create(**lookup, defaults=defaults)
            if created:
                stats.created += 1
            else:
                stats.updated += 1
            valid += 1

        stats.valid = valid
        return stats

"""Genera el diccionario real de PostgreSQL en un documento Word (.docx)."""

from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

import os
import sys

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROYECTO))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "emma.settings")

import django

django.setup()

from django.db import connection


def texto(value):
    return escape("" if value is None else str(value))


def parrafo(value, estilo=None):
    propiedades = f'<w:pPr><w:pStyle w:val="{estilo}"/></w:pPr>' if estilo else ""
    return f'<w:p>{propiedades}<w:r><w:t xml:space="preserve">{texto(value)}</w:t></w:r></w:p>'


def celda(value, encabezado=False):
    negrita = "<w:b/>" if encabezado else ""
    sombreado = '<w:shd w:fill="D9EAD3"/>' if encabezado else ""
    return f'<w:tc><w:tcPr>{sombreado}</w:tcPr><w:p><w:r><w:rPr>{negrita}</w:rPr><w:t xml:space="preserve">{texto(value)}</w:t></w:r></w:p></w:tc>'


def tabla(filas):
    ancho = 9000 // len(filas[0])
    grid = "".join(f'<w:gridCol w:w="{ancho}"/>' for _ in filas[0])
    cuerpo = "".join(
        '<w:tr>' + "".join(celda(valor, indice == 0) for valor in fila) + '</w:tr>'
        for indice, fila in enumerate(filas)
    )
    return f'<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders><w:top w:val="single"/><w:left w:val="single"/><w:bottom w:val="single"/><w:right w:val="single"/><w:insideH w:val="single"/><w:insideV w:val="single"/></w:tblBorders></w:tblPr><w:tblGrid>{grid}</w:tblGrid>{cuerpo}</w:tbl>'


def obtener_metadatos():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.table_name, c.ordinal_position, c.column_name,
                   c.data_type, c.udt_name, c.is_nullable, c.column_default,
                   pgd.description
            FROM information_schema.columns c
            LEFT JOIN pg_catalog.pg_statio_all_tables st
              ON st.schemaname = c.table_schema AND st.relname = c.table_name
            LEFT JOIN pg_catalog.pg_description pgd
              ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
            WHERE c.table_schema = 'public'
            ORDER BY c.table_name, c.ordinal_position
        """)
        columnas = cursor.fetchall()
        cursor.execute("""
            SELECT tc.table_name, kcu.column_name, tc.constraint_type,
                   ccu.table_name AS tabla_referenciada, ccu.column_name AS columna_referenciada
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            LEFT JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
            WHERE tc.table_schema = 'public'
              AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE')
            ORDER BY tc.table_name, kcu.column_name, tc.constraint_type
        """)
        restricciones = cursor.fetchall()
    indice = {}
    for tabla, columna, tipo, ref_tabla, ref_columna in restricciones:
        etiqueta = "PK" if tipo == "PRIMARY KEY" else (f"FK → {ref_tabla}.{ref_columna}" if tipo == "FOREIGN KEY" else "UNIQUE")
        indice.setdefault((tabla, columna), []).append(etiqueta)
    return columnas, indice


def generar(destino):
    columnas, restricciones = obtener_metadatos()
    por_tabla = {}
    for registro in columnas:
        por_tabla.setdefault(registro[0], []).append(registro)

    partes = [
        parrafo("Diccionario BD EMMA", "Title"),
        parrafo(f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')} desde la estructura real de PostgreSQL."),
        parrafo("Alcance: esquema public. Incluye tablas de negocio, catálogos, auditoría y tablas técnicas actualmente existentes."),
        parrafo(f"Total de tablas: {len(por_tabla)}."),
    ]
    for nombre_tabla, registros in por_tabla.items():
        partes.append(parrafo(nombre_tabla, "Heading1"))
        filas = [["#", "Columna", "Tipo PostgreSQL", "Nulo", "Predeterminado", "Restricción", "Descripción"]]
        for _, posicion, columna, tipo, udt, nulo, defecto, descripcion in registros:
            tipo_mostrar = tipo if tipo == udt else f"{tipo} ({udt})"
            filas.append([
                posicion, columna, tipo_mostrar, "Sí" if nulo == "YES" else "No",
                defecto or "—", "; ".join(restricciones.get((nombre_tabla, columna), [])) or "—",
                descripcion or "—",
            ])
        partes.append(tabla(filas))

    documento = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{''.join(partes)}<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="720" w:right="720" w:bottom="720" w:left="720"/></w:sectPr></w:body></w:document>'''
    estilos = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="36"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style></w:styles>'''
    tipos = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'''
    doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
    with ZipFile(destino, "w", ZIP_DEFLATED) as archivo:
        archivo.writestr("[Content_Types].xml", tipos)
        archivo.writestr("_rels/.rels", rels)
        archivo.writestr("word/document.xml", documento)
        archivo.writestr("word/styles.xml", estilos)
        archivo.writestr("word/_rels/document.xml.rels", doc_rels)


if __name__ == "__main__":
    salida = Path(__file__).resolve().parents[1] / "Diccionario BD EMMA.docx"
    generar(salida)
    print(salida)

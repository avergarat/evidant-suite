# excel_repo.py
# -*- coding: utf-8 -*-

import pandas as pd
import re

from ocr_utils import normalizar_run, normalizar_nro_doc

def detectar_columna(columnas, nombre_objetivo, palabras_clave):
    if nombre_objetivo in columnas:
        return nombre_objetivo

    candidatos = []
    for c in columnas:
        cl = str(c).lower()
        if all(p.lower() in cl for p in palabras_clave):
            candidatos.append(c)

    if len(candidatos) == 1:
        return candidatos[0]

    raise KeyError(
        f"No se pudo detectar la columna '{nombre_objetivo}'. "
        f"Columnas disponibles: {list(columnas)}. Candidatos: {candidatos}"
    )

def parsear_monto(monto_raw):
    if pd.isna(monto_raw):
        return None
    s = re.sub(r"[^\d]", "", str(monto_raw))
    return int(s) if s else None


def obtener_categorias_excel(ruta_excel: str):
    """
    Devuelve:
    - calidades: list[str]
    - planillas: list[str]
    - programas: list[str]
    """
    df = pd.read_excel(ruta_excel, sheet_name="ETIQUETAS")

    calidades = sorted(
        df["Calidad Juridica"].dropna().astype(str).unique().tolist()
    )

    planillas = sorted(
        df["Planilla de Pago"].dropna().astype(str).unique().tolist()
    )

    programas = sorted(
        df["Programa"].dropna().astype(str).unique().tolist()
    )

    return calidades, planillas, programas




def leer_etiquetas_excel(ruta_excel: str, log_callback=None):
    if log_callback is None:
        log_callback = lambda msg: None

    xls = pd.ExcelFile(ruta_excel)
    hoja_etiquetas = None
    for nombre in xls.sheet_names:
        if nombre.strip().lower() == "etiquetas":
            hoja_etiquetas = nombre
            break
    if hoja_etiquetas is None:
        hoja_etiquetas = xls.sheet_names[0]

    df = pd.read_excel(xls, sheet_name=hoja_etiquetas, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def construir_mappings(
    ruta_excel: str,
    filtro_calidad: str | None,
    filtro_planilla: str | None,
    filtros_programa: list[str] | None,
    filtros_unidad: list[str] | None,
    log_callback=None,
):
    if log_callback is None:
        log_callback = lambda msg: None

    df = leer_etiquetas_excel(ruta_excel, log_callback=log_callback)
    columnas = list(df.columns)

    col_run = detectar_columna(columnas, "RUN", ["run"])
    col_monto = detectar_columna(columnas, "Monto (Total Haberes)", ["monto", "haber"])
    col_planilla = detectar_columna(columnas, "Planilla de Pago", ["planilla"])
    col_nro_doc = detectar_columna(columnas, "Nº de Documento", ["documento"])

    if "Calidad Juridica" in columnas:
        col_calidad = "Calidad Juridica"
    else:
        col_calidad = detectar_columna(columnas, "Calidad Jurídica", ["calidad", "jurid"])

    col_programa = None
    try:
        col_programa = detectar_columna(columnas, "Programa", ["programa"])
    except KeyError:
        col_programa = None

    col_unidad = None
    try:
        col_unidad = detectar_columna(columnas, "Unidad", ["unidad"])
    except KeyError:
        col_unidad = None
        if filtros_unidad:
            log_callback("Advertencia: no se encontró columna 'Unidad'; se ignora el filtro de unidad.")

    if filtro_calidad:
        df = df[df[col_calidad] == filtro_calidad]
        log_callback(f"Filtrado Calidad Jurídica='{filtro_calidad}': {len(df)} filas")

    if filtro_planilla:
        df = df[df[col_planilla] == filtro_planilla]
        log_callback(f"Filtrado Planilla='{filtro_planilla}': {len(df)} filas")

    if filtros_programa and col_programa:
        df = df[df[col_programa].isin(filtros_programa)]
        log_callback(f"Filtrado Programas ({len(filtros_programa)}): {len(df)} filas")

    if filtros_unidad and col_unidad:
        df = df[df[col_unidad].astype(str).isin(filtros_unidad)]
        log_callback(f"Filtrado Unidades ({len(filtros_unidad)}): {len(df)} filas")

    # mapping (RUN, MONTO) normal
       
    mapping_run_monto = {}

    # mapping (RUN, MONTO) -> lista de registros (para consumir y evitar duplicados)
    mapping_run_monto_list = {}

    # mapping HONORARIOS: (RUN, NRO_DOC) -> lista de registros (para consumir y evitar duplicados)
    mapping_run_doc = {}

    
    for _, row in df.iterrows():
        run_cuerpo = normalizar_run(row[col_run])
        monto = parsear_monto(row[col_monto])
        nro_doc_raw = row[col_nro_doc]
        nro_doc = normalizar_nro_doc(nro_doc_raw)
        planilla = str(row[col_planilla]).strip()
        calidad = str(row[col_calidad]).strip()

        if run_cuerpo and monto is not None:
                registro_monto = {
                    "run_cuerpo": run_cuerpo,
                    "monto": monto,
                    "nro_doc": str(nro_doc_raw).strip(),
                    "planilla": planilla,
                    "calidad": calidad,
                }
                # compat: mantiene el “último gana”
                mapping_run_monto[(run_cuerpo, monto)] = registro_monto
                # correcto: lista para poder consumir uno a uno
                mapping_run_monto_list.setdefault((run_cuerpo, monto), []).append(registro_monto)        


        if run_cuerpo and nro_doc:
            key = (run_cuerpo, nro_doc)
            mapping_run_doc.setdefault(key, []).append({
                "run_cuerpo": run_cuerpo,
                "nro_doc": str(nro_doc_raw).strip(),
                "planilla": planilla,
                "calidad": calidad,
            })

    cols_info = {
        "col_run": col_run,
        "col_monto": col_monto,
        "col_planilla": col_planilla,
        "col_calidad": col_calidad,
        "col_nro_doc": col_nro_doc,
        "col_programa": col_programa,
        "col_unidad": col_unidad,
    }
    return mapping_run_monto, mapping_run_doc, mapping_run_monto_list


def docs_disponibles_para_run(mapping_run_doc, run_cuerpo: str):
    docs = []
    for (r, d), lst in mapping_run_doc.items():
        if r == run_cuerpo and lst:
            docs.append(d)
    docs = sorted(set(docs), key=lambda x: (len(x), x))
    return docs

def consumir_registro(mapping_run_doc, run_cuerpo: str, nro_doc_norm: str):
    key = (run_cuerpo, nro_doc_norm)
    lst = mapping_run_doc.get(key, [])
    if not lst:
        return None
    return lst.pop(0)  # consumo real

def montos_disponibles_para_run(mapping_run_monto_list, run_cuerpo: str):
    """Devuelve montos disponibles (sin consumir) para un RUN en mapping_run_monto_list."""
    montos = []
    for (r, m), lst in mapping_run_monto_list.items():
        if r == run_cuerpo and lst:
            montos.append(m)
    return sorted(set(montos))


def consumir_registro_monto(mapping_run_monto_list, run_cuerpo: str, monto: int):
    """Consume (pop) un registro para (RUN, MONTO) desde mapping_run_monto_list."""
    key = (run_cuerpo, monto)
    lst = mapping_run_monto_list.get(key, [])
    if not lst:
        return None
    return lst.pop(0)

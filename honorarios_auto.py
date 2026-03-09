# honorarios_auto.py
# -*- coding: utf-8 -*-

import os
import time
import threading
from typing import List, Dict, Tuple, Any, Optional

import pdfplumber
import pandas as pd
from PyPDF2 import PdfReader, PdfWriter

from ocr_utils import (
    ocr_roi,
    preprocesar_imagen_ocr_suave,
    extraer_run_emisor_desde_texto_v2,
    normalizar_run,
    extraer_nro_doc_anclado,
    normalizar_nro_doc,
    asegurar_tesseract,
)
from excel_repo import docs_disponibles_para_run, consumir_registro


def _forzar_doc(ocr_doc: str, docs_excel: List[str]) -> Tuple[str, str]:
    """
    Forzado pragmático (como tu log):
    - sufijo: 2107 -> 107
    - substring: 9330 contiene 93
    - cercano por distancia numérica si mismo largo o +-1
    """
    if not ocr_doc or not docs_excel:
        return "", ""

    o = str(ocr_doc)

    # 1) sufijo exacto
    for d in docs_excel:
        if o.endswith(d) and o != d:
            return d, f"sufijo OCR='{o}'->'{d}'"

    # 2) substring
    for d in docs_excel:
        if d in o and o != d:
            return d, f"substring OCR='{o}' contiene '{d}'"

    # 3) cercano por distancia numérica
    try:
        oi = int(o)
        best = None
        for d in docs_excel:
            try:
                di = int(d)
            except Exception:
                continue
            dist = abs(oi - di)
            if best is None or dist < best[0]:
                best = (dist, d)

        # umbral conservador (como lo tenías)
        if best and best[0] <= 400 and best[1] != o:
            return best[1], f"cercano OCR='{o}'~'{best[1]}'"
    except Exception:
        pass

    return "", ""


def _exportar_no_reconocidos_excel(
    no_encontrados: List[Dict[str, Any]],
    carpeta_salida: str,
    nombre_archivo: str,
    log_callback,
) -> Optional[str]:
    """
    Exporta el listado de no reconocidos a Excel con el formato requerido por honorarios_manual:
    pag1, pag2, run_ocr, doc_ocr, motivo, dbg

    Devuelve ruta del archivo si se generó, si no None.
    """
    if not no_encontrados:
        return None

    os.makedirs(carpeta_salida, exist_ok=True)
    ruta_xlsx = os.path.join(carpeta_salida, nombre_archivo)

    # Asegura columnas y orden EXACTO
    cols = ["pag1", "pag2", "run_ocr", "doc_ocr", "motivo", "dbg"]
    rows = []
    for x in no_encontrados:
        rows.append({
            "pag1": x.get("pag1", ""),
            "pag2": x.get("pag2", ""),
            "run_ocr": x.get("run_ocr", ""),
            "doc_ocr": x.get("doc_ocr", ""),
            "motivo": x.get("motivo", ""),
            "dbg": x.get("dbg", ""),
        })

    df = pd.DataFrame(rows, columns=cols)

    try:
        df.to_excel(ruta_xlsx, index=False, engine="openpyxl")
        log_callback(f"Se exportó Excel de no reconocidos: {ruta_xlsx}")
        return ruta_xlsx
    except Exception as e:
        log_callback(f"ERROR: No se pudo exportar Excel de no reconocidos: {e}")
        return None


def procesar_pdf_honorarios(
    ruta_pdf: str,
    mapping_run_doc: dict,
    carpeta_salida: str,
    periodo: str,
    paginas_indices: List[int],
    log_callback=None,
    stop_event: threading.Event | None = None,
    pause_event: threading.Event | None = None,
    progress_callback=None,
    forzado: bool = True,
    guardar_excel: bool = True,
    nombre_excel: str = "no_reconocidos_honorarios.xlsx",
):
    """
    Procesa PDF de honorarios en pares de páginas (2 páginas por boleta),
    hace match por (RUN, NºDoc) usando mapping_run_doc y guarda PDFs etiquetados.

    NUEVO (sin tocar lógica): si hay no_encontrados y guardar_excel=True,
    exporta un Excel con columnas:
    pag1, pag2, run_ocr, doc_ocr, motivo, dbg
    """
    if log_callback is None:
        log_callback = print

    # asegura tesseract (como ya lo estabas usando)
    asegurar_tesseract()

    os.makedirs(carpeta_salida, exist_ok=True)
    reader = PdfReader(ruta_pdf)

    if len(paginas_indices) % 2 != 0:
        paginas_indices = paginas_indices[:-1]

    total_pares = len(paginas_indices) // 2
    no_encontrados: List[Dict[str, Any]] = []
    exitosas = 0
    detenido = False

    with pdfplumber.open(ruta_pdf) as pdf:
        for idx_par in range(total_pares):
            if stop_event and stop_event.is_set():
                detenido = True
                break

            if pause_event and pause_event.is_set():
                while pause_event.is_set():
                    if stop_event and stop_event.is_set():
                        detenido = True
                        break
                    time.sleep(0.2)
                if detenido:
                    break

            idx1 = paginas_indices[2 * idx_par]
            idx2 = paginas_indices[2 * idx_par + 1]

            page = pdf.pages[idx1]
            img = page.to_image(resolution=450).original.convert("RGB")
            w, h = img.size

            # RUN (el que funciona)
            box_sup = (int(0.05 * w), int(0.05 * h), int(0.95 * w), int(0.38 * h))
            config_rut = r"--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.kK:-RrUuTt "
            texto_sup = ocr_roi(img, box_sup, preprocess=preprocesar_imagen_ocr_suave, config=config_rut)
            run = normalizar_run(extraer_run_emisor_desde_texto_v2(texto_sup))

            # NºDoc anclado
            doc, dbg = extraer_nro_doc_anclado(img)
            doc = normalizar_nro_doc(doc)

            if not run or not doc:
                no_encontrados.append({
                    "pag1": idx1,
                    "pag2": idx2,
                    "run_ocr": run,
                    "doc_ocr": doc,
                    "motivo": f"NO RUN/NºDOC válido. {dbg}",
                    "dbg": dbg,
                })
                log_callback(f"[Pág {idx1+1}-{idx2+1}] SIN RUN/NºDOC válido. RUN='{run}', NºDoc='{doc}'")
                if progress_callback:
                    progress_callback(idx_par + 1, total_pares)
                continue

            # match directo (consumible)
            info = consumir_registro(mapping_run_doc, run, doc)
            if info is None and forzado:
                docs_excel = docs_disponibles_para_run(mapping_run_doc, run)
                if docs_excel:
                    corr, why = _forzar_doc(doc, docs_excel)
                    if corr:
                        log_callback(f"[Pág {idx1+1}] CORRECCIÓN NºDoc: OCR='{doc}' -> '{corr}' ({why})")
                        info = consumir_registro(mapping_run_doc, run, corr)
                        doc = corr

            if info is None:
                docs_excel = docs_disponibles_para_run(mapping_run_doc, run)
                no_encontrados.append({
                    "pag1": idx1,
                    "pag2": idx2,
                    "run_ocr": run,
                    "doc_ocr": doc,
                    "motivo": f"SIN MATCH (RUN+NºDOC). Docs Excel RUN: {docs_excel}",
                    "dbg": dbg,
                })
                log_callback(f"[Pág {idx1+1}-{idx2+1}] SIN MATCH (RUN+NºDOC). RUN={run}, NºDoc={doc}")
                if progress_callback:
                    progress_callback(idx_par + 1, total_pares)
                continue

            # guardar 2 páginas
            run_cuerpo = info["run_cuerpo"]
            nro_doc_excel = str(info["nro_doc"]).strip()
            planilla = str(info["planilla"]).replace(" ", "")

            etiqueta = f"{periodo}_{run_cuerpo}_{nro_doc_excel}_{planilla}.pdf"
            out_path = os.path.join(carpeta_salida, etiqueta)

            writer = PdfWriter()
            writer.add_page(reader.pages[idx1])
            writer.add_page(reader.pages[idx2])

            base, ext = os.path.splitext(out_path)
            real_out = out_path
            c = 1
            while os.path.exists(real_out):
                real_out = f"{base}_{c}{ext}"
                c += 1

            with open(real_out, "wb") as f:
                writer.write(f)

            exitosas += 1
            log_callback(f"[Pág {idx1+1}-{idx2+1}] OK -> {os.path.basename(real_out)}")

            if progress_callback:
                progress_callback(idx_par + 1, total_pares)

    # ===== Exportación de no reconocidos a Excel (si corresponde) =====
  
    ruta_xlsx = None
    if guardar_excel:
        ruta_xlsx = _exportar_no_reconocidos_excel(
            no_encontrados=no_encontrados,
            carpeta_salida=carpeta_salida,
            nombre_archivo=nombre_excel,
            log_callback=log_callback,
        )

    return exitosas, no_encontrados, detenido, ruta_xlsx

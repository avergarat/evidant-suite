# -*- coding: utf-8 -*-
# evidant Suite — pages/6_Procesamiento_Imagenes.py
# Módulo combinado:
#   A) Etiquetador de Liquidaciones — PDF multi-página → por RUT+Monto → ZIP etiquetado
#   B) Etiquetador de Honorarios    — PDF boletas (2 págs c/u) → OCR auto/manual/RUT

import streamlit as st
import sys
import os
import re
import io
import queue
import threading
import zipfile
import copy
from pathlib import Path
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ev_design

# ── PIL ──────────────────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageOps, ImageFilter, ImageEnhance
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

# ── pytesseract ───────────────────────────────────────────────────────────────
try:
    import pytesseract as _pyt_mod  # noqa: F401
    _TESSERACT_LIB_OK = True
except ImportError:
    _TESSERACT_LIB_OK = False

# ══════════════════════════════════════════════════════════════════════════════
# OCR UTILITIES  (portadas inline de ocr_utils.py)
# ══════════════════════════════════════════════════════════════════════════════

_TESS_DEFAULT = r"C:\Users\DAP\tesseract.exe"


def _cfg_tess(ruta_extra: str = "") -> bool:
    """Configura pytesseract; prueba env-vars → PATH → rutas típicas Windows."""
    if not _TESSERACT_LIB_OK:
        return False
    import shutil
    import pytesseract
    candidatos = []
    for env_var in ("EVIDANT_TESSERACT", "TESSERACT_CMD", "TESSERACT_EXE", "TESSERACT_PATH"):
        v = os.environ.get(env_var, "").strip()
        if v:
            candidatos.append(v)
    if ruta_extra:
        candidatos.append(ruta_extra)
    which = shutil.which("tesseract")
    if which:
        candidatos.append(which)
    candidatos += [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        _TESS_DEFAULT,
    ]
    for c in candidatos:
        try:
            if c and Path(c).exists():
                pytesseract.pytesseract.tesseract_cmd = c
                return True
        except Exception:
            continue
    # last resort: hope it's in PATH
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _preproc_suave(img):
    img = img.convert("RGB")
    img = ImageOps.grayscale(img)
    img = ImageEnhance.Contrast(img).enhance(1.6)
    return img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))


def _preproc_cuadro(img):
    img = img.convert("RGB")
    img = ImageOps.grayscale(img)
    img = ImageEnhance.Contrast(img).enhance(1.8)
    return img.filter(ImageFilter.UnsharpMask(radius=1, percent=140, threshold=3))


def _preproc_ndoc(img):
    img = img.convert("RGB")
    img = ImageOps.grayscale(img)
    img = ImageEnhance.Contrast(img).enhance(2.2)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = img.point(lambda p: 255 if p > 200 else 0)
    return img.filter(ImageFilter.MedianFilter(size=3))


def _ocr_roi(img, box, preprocess=None, config: str = "") -> str:
    if not _TESSERACT_LIB_OK or not _PIL_OK:
        return ""
    import pytesseract
    try:
        roi = img.crop(box)
        if preprocess:
            roi = preprocess(roi)
        return pytesseract.image_to_string(roi, lang="spa", config=config)
    except Exception:
        return ""


def _norm_run_ocr(run_raw: str) -> str:
    if run_raw is None:
        return ""
    digits = re.sub(r"\D", "", str(run_raw))
    if len(digits) > 8:
        return digits[:-1]
    return digits


def _norm_nro_doc(valor) -> str:
    if valor is None:
        return ""
    digs = re.sub(r"\D", "", str(valor))
    if not digs:
        return ""
    try:
        return str(int(digs))
    except Exception:
        return digs.lstrip("0") or digs


def _extraer_run_v2(texto: str) -> str:
    """Extrae RUN/cuerpo desde texto OCR (igual que extraer_run_emisor_desde_texto_v2)."""
    if not texto:
        return ""
    for ln in (l.strip() for l in texto.splitlines() if l.strip()):
        if "rut" not in ln.lower():
            continue
        m = re.search(r"([0-9\.\s]{7,12})\s*-\s*([0-9kK])", ln)
        if not m:
            continue
        c = re.sub(r"\D", "", m.group(1))
        if c != "61608605" and 7 <= len(c) <= 8:
            return c
    for m in re.finditer(r"([0-9\.\s]{7,12})\s*-\s*([0-9kK])", texto):
        c = re.sub(r"\D", "", m.group(1))
        if c != "61608605" and 7 <= len(c) <= 8:
            return c
    return ""


def _extraer_nro_doc_texto(txt: str) -> str:
    t = (txt or "").upper().replace(" ", "").replace("\n", "")
    m = re.search(r"N[O°º]?\D*0*(\d{1,8})", t)
    if m:
        return m.group(1)
    m2 = re.search(r"(\d{1,8})", t)
    return m2.group(1) if m2 else ""


def _encontrar_ancla_doc(img):
    """Busca ancla BOLETA/ELECTRONICA para determinar ROI del N°Doc."""
    if not _TESSERACT_LIB_OK or not _PIL_OK:
        return None, "sin_tesseract"
    import pytesseract
    from pytesseract import Output
    img = img.convert("RGB")
    w, h = img.size
    box_cuadro = (int(0.55 * w), int(0.06 * h), int(0.97 * w), int(0.34 * h))
    roi = img.crop(box_cuadro)
    roi_pp = _preproc_cuadro(roi)
    try:
        data = pytesseract.image_to_data(
            roi_pp, lang="spa", config="--oem 3 --psm 6", output_type=Output.DICT
        )
    except Exception:
        return None, "ocr_error"
    best = None
    for i, t in enumerate(data["text"]):
        t0 = (t or "").strip().upper()
        t1 = re.sub(r"[^A-Z0-9]", "", t0)
        kind = None
        if "BOLETA" in t1 or t1 in ("B0LETA", "BOIETA", "BOLE7A"):
            kind = "BOLETA"
        elif "ELECTRONICA" in t1 or "ELECTRONICA" in t1.replace("0", "O"):
            kind = "ELECTRONICA"
        if kind:
            x, y = data["left"][i], data["top"][i]
            ww, hh = data["width"][i], data["height"][i]
            conf = float(data["conf"][i] or 0)
            score = conf + ww
            if best is None or score > best[0]:
                best = (score, x, y, ww, hh, t0, kind)
    if best is None:
        return None, "ANCLA=NO"
    _, x, y, ww, hh, token, kind = best
    nro_l = max(0, x - int(0.10 * ww))
    nro_t = y + int(1.1 * hh)
    nro_r = min(roi.size[0], x + int(2.6 * ww))
    nro_b = min(roi.size[1], y + int(4.0 * hh))
    box_abs = (
        box_cuadro[0] + nro_l, box_cuadro[1] + nro_t,
        box_cuadro[0] + nro_r, box_cuadro[1] + nro_b,
    )
    return box_abs, f"ANCLA=OK kind={kind} token='{token}'"


def _extraer_nro_doc_anclado(img):
    """Extrae N°Doc con ancla BOLETA/ELECTRONICA + fallback ROI fijo."""
    box_doc, dbg = _encontrar_ancla_doc(img)
    if box_doc is not None:
        cfg = r"--oem 3 --psm 7 -c tessedit_char_whitelist=NO°º0123456789"
        raw = _ocr_roi(img, box_doc, preprocess=_preproc_ndoc, config=cfg)
        nro = _extraer_nro_doc_texto(raw)
        if nro:
            return _norm_nro_doc(nro), f"{dbg} OCR='{raw.strip()[:80]}'"
    w, h = img.size
    box = (int(0.62 * w), int(0.10 * h), int(0.95 * w), int(0.29 * h))
    cfg = r"--oem 3 --psm 6 -c tessedit_char_whitelist=NO°º0123456789"
    raw = _ocr_roi(img, box, preprocess=_preproc_ndoc, config=cfg)
    nro = _extraer_nro_doc_texto(raw)
    if nro:
        return _norm_nro_doc(nro), f"FALLBACK_ROI OK OCR='{raw.strip()[:80]}'"
    return "", f"{dbg} + FALLBACK=NO"


# ══════════════════════════════════════════════════════════════════════════════
# MAPPING & HELPERS — HONORARIOS (portados de excel_repo.py)
# ══════════════════════════════════════════════════════════════════════════════

def _construir_mapping_run_doc(
    df: pd.DataFrame,
    filtro_calidad=None,
    filtro_planilla=None,
    filtros_programa=None,
    filtros_unidad=None,
    log=None,
) -> dict:
    """Construye mapping_run_doc: {(run_cuerpo, nro_doc): [registros...]}"""
    log = log or (lambda _: None)
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    cols = list(df.columns)
    low = {c: c.lower() for c in cols}

    def find_col(*names):
        for n in names:
            if n in cols:
                return n
        for n in names:
            cands = [c for c in cols if n.lower() in low[c]]
            if cands:
                return cands[0]
        return None

    col_run      = find_col("RUN", "RUT")
    col_planilla = find_col("Planilla de Pago", "Planilla")
    col_calidad  = find_col("Calidad Juridica", "Calidad Jurídica", "Calidad")
    col_nro_doc  = find_col("Nº de Documento", "N° de Documento", "N° Documento", "Nro Documento")
    col_programa = find_col("Programa")
    col_unidad   = find_col("Unidad")

    log(f"Columnas honorarios → RUN='{col_run}' | Planilla='{col_planilla}' | N°Doc='{col_nro_doc}'")

    if filtro_calidad and filtro_calidad != "(Todas)" and col_calidad:
        df = df[df[col_calidad].astype(str) == filtro_calidad]
        log(f"Filtro Calidad: {len(df)} filas")
    if filtro_planilla and filtro_planilla != "(Todas)" and col_planilla:
        df = df[df[col_planilla].astype(str) == filtro_planilla]
        log(f"Filtro Planilla: {len(df)} filas")
    if filtros_programa and col_programa:
        df = df[df[col_programa].astype(str).isin(filtros_programa)]
    if filtros_unidad and col_unidad:
        df = df[df[col_unidad].astype(str).isin(filtros_unidad)]

    mapping_run_doc: dict = {}
    for _, row in df.iterrows():
        run_cuerpo  = _norm_run_ocr(str(row[col_run]).strip()) if col_run else ""
        nro_doc_raw = row[col_nro_doc] if col_nro_doc else ""
        nro_doc     = _norm_nro_doc(nro_doc_raw)
        planilla    = str(row[col_planilla]).strip() if col_planilla else ""
        calidad     = str(row[col_calidad]).strip() if col_calidad else ""
        if run_cuerpo and nro_doc:
            mapping_run_doc.setdefault((run_cuerpo, nro_doc), []).append({
                "run_cuerpo": run_cuerpo,
                "nro_doc":    str(nro_doc_raw).strip(),
                "planilla":   planilla,
                "calidad":    calidad,
            })
    log(f"Claves (RUN, N°Doc) honorarios: {len(mapping_run_doc)}")
    return mapping_run_doc


def _docs_disp(mapping_run_doc: dict, run_cuerpo: str) -> list:
    docs = [d for (r, d), lst in mapping_run_doc.items() if r == run_cuerpo and lst]
    return sorted(set(docs), key=lambda x: (len(x), x))


def _consumir(mapping_run_doc: dict, run_cuerpo: str, nro_doc: str):
    lst = mapping_run_doc.get((run_cuerpo, nro_doc), [])
    return lst.pop(0) if lst else None


def _forzar_doc(ocr_doc: str, docs_excel: list):
    if not ocr_doc or not docs_excel:
        return "", ""
    o = str(ocr_doc)
    for d in docs_excel:
        if o.endswith(d) and o != d:
            return d, f"sufijo OCR='{o}'->'{d}'"
    for d in docs_excel:
        if d in o and o != d:
            return d, f"substring OCR='{o}' contiene '{d}'"
    try:
        oi = int(o)
        best = None
        for d in docs_excel:
            try:
                di = int(d)
                dist = abs(oi - di)
                if best is None or dist < best[0]:
                    best = (dist, d)
            except Exception:
                continue
        if best and best[0] <= 400 and best[1] != o:
            return best[1], f"cercano OCR='{o}'~'{best[1]}'"
    except Exception:
        pass
    return "", ""


# ══════════════════════════════════════════════════════════════════════════════
# LÓGICA DE NEGOCIO — LIQUIDACIONES (portada de app.py)
# ══════════════════════════════════════════════════════════════════════════════

def _normalizar_run(x) -> str:
    """RUN con o sin DV → sólo cuerpo numérico (7-8 dígitos)."""
    if x is None:
        return ""
    s = str(x).strip().upper()
    if not s:
        return ""
    m = re.match(r"^(\d{7,8})-([0-9K])$", s)
    if m:
        return m.group(1)
    if re.fullmatch(r"\d{9}", s):
        return s[:-1]
    digits = re.sub(r"\D+", "", s)
    d2 = digits.lstrip("0")
    if 7 <= len(d2) <= 8:
        digits = d2
    return digits if re.fullmatch(r"\d{7,8}", digits) else ""


def _parsear_monto(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    # Fix: "1462453.0" (pandas float→str) → "1462453"
    if re.fullmatch(r"\d+\.0+", s):
        s = s.split(".")[0]
    s = re.sub(r"[^\d]", "", s)
    return int(s) if s else None


def extraer_run(texto_pagina: str) -> str:
    """Extrae el cuerpo del RUT (sin DV) desde texto de página PDF."""
    texto = texto_pagina or ""
    # Patrón 1: dígitos consecutivos 7-8 + guión + DV  (20575635-3 ó 20575635 - 3)
    m = re.search(r"(\d{7,8})\s*-\s*[\dkK]", texto)
    if m:
        return m.group(1)
    # Patrón 2: RUT con puntos en el cuerpo  (20.575.635-3)
    m2 = re.search(r"(\d{1,2}[.]\d{3}[.]\d{3})\s*-\s*[\dkK]", texto)
    if m2:
        body = re.sub(r"\D", "", m2.group(1))
        if 7 <= len(body) <= 8:
            return body
    return ""


def extraer_total_haberes(texto_pagina: str):
    """
    Extrae el monto de Total Haberes desde el texto PDF de una página.

    Maneja dos layouts:
      Layout A: valor en la misma línea que el label (antes o después)
      Layout B: valores en fila SUPERIOR al label (orden pdfplumber invertido)
    También captura typos comunes: "Totel Haberes", "Total Habers", etc.
    """
    texto_pagina = texto_pagina or ""
    UMBRAL_MIN = 1_000  # bajado para liquidaciones pequeñas

    # Acepta 1.234.567 / 1,234,567 / 1234567 (4+ dígitos)
    _NUM_RE = re.compile(
        r"\b\d{1,3}(?:[.,]\d{3})+\b"
        r"|\b\d{4,}\b"
    )
    # Captura typos: total/totel/tot4l + haberes/habers
    _LABEL_RE = re.compile(r"tot[ae0][lt1]\s+h[ae]ber", re.IGNORECASE)

    def _parsear_v(s: str):
        digs = re.sub(r"[^\d]", "", s)
        if not digs:
            return None
        v = int(digs)
        return v if v >= UMBRAL_MIN else None

    def _nums_en(texto: str) -> list:
        result = []
        for m in _NUM_RE.finditer(texto):
            v = _parsear_v(m.group())
            if v is not None:
                result.append(v)
        return result

    lineas = texto_pagina.splitlines()

    for i, ln in enumerate(lineas):
        m_label = _LABEL_RE.search(ln)
        if m_label:
            # Layout A1: número ANTES del label ("21.220 Totel Haberes ...")
            antes = _nums_en(ln[:m_label.start()])
            if antes:
                return antes[-1]
            # Layout A2: número DESPUÉS del label ("Total Haberes 21.220")
            despues = _nums_en(ln[m_label.end():])
            if despues:
                return despues[0]
            # Layout B: valores en líneas ANTERIORES (pdfplumber orden invertido)
            for j in range(1, 4):
                if i - j >= 0:
                    nums = _nums_en(lineas[i - j])
                    if nums:
                        return nums[0]
            # Layout C: valores en líneas SIGUIENTES
            for j in range(1, 4):
                if i + j < len(lineas):
                    nums = _nums_en(lineas[i + j])
                    if nums:
                        return nums[0]
            break

    # Fallback: ventana de texto alrededor de variantes del label
    texto_lower = texto_pagina.lower()
    for label in ("total haberes", "totel haberes", "total habers",
                  "totel habers", "total hab", "totel hab"):
        idx = texto_lower.find(label)
        if idx != -1:
            antes_txt = texto_pagina[max(0, idx - 150): idx]
            n_antes = _nums_en(antes_txt)
            if n_antes:
                return n_antes[-1]
            despues_txt = texto_pagina[idx + len(label): idx + len(label) + 150]
            n_desp = _nums_en(despues_txt)
            if n_desp:
                return n_desp[0]

    # Último recurso: máximo número en la página
    todos = _nums_en(texto_pagina)
    return max(todos) if todos else None


def parsear_rangos_paginas(spec: str, total_paginas: int) -> list:
    spec = (spec or "").strip()
    if not spec:
        return list(range(total_paginas))
    paginas = set()
    for parte in spec.split(","):
        parte = parte.strip()
        if not parte:
            continue
        if "-" in parte:
            ini_str, fin_str = parte.split("-", 1)
            if ini_str.strip().isdigit() and fin_str.strip().isdigit():
                for p in range(int(ini_str), int(fin_str) + 1):
                    if 1 <= p <= total_paginas:
                        paginas.add(p - 1)
        elif parte.isdigit():
            p = int(parte)
            if 1 <= p <= total_paginas:
                paginas.add(p - 1)
    return sorted(paginas) if paginas else list(range(total_paginas))


def construir_mapping_desde_excel(
    df: pd.DataFrame,
    filtro_calidad=None,
    filtro_planilla=None,
    filtros_programa=None,
    filtros_unidad=None,
    log=None,
) -> dict:
    log = log or (lambda _: None)
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    cols = list(df.columns)
    low = {c: c.lower() for c in cols}

    def find_col(*names):
        for n in names:
            if n in cols:
                return n
        for n in names:
            cands = [c for c in cols if n.lower() in low[c]]
            if cands:
                return cands[0]
        return None

    col_run      = find_col("RUN", "RUT")
    col_monto    = find_col("Monto (Total Haberes)", "Monto Total Haberes", "Monto", "monto")
    col_planilla = find_col("Planilla de Pago", "Planilla")
    col_calidad  = find_col("Calidad Juridica", "Calidad Jurídica", "Calidad")
    col_nro_doc  = find_col("Nº de Documento", "N° de Documento", "N° Documento",
                            "Nro Documento", "Numero de Documento")
    col_programa = find_col("Programa")
    col_unidad   = find_col("Unidad")

    missing = [n for n, c in [("RUN", col_run), ("Monto", col_monto),
                               ("Planilla", col_planilla), ("Calidad", col_calidad),
                               ("N°Documento", col_nro_doc)] if not c]
    if missing:
        log(f"⚠️ Columnas no detectadas: {missing}. Columnas disponibles: {cols}")

    log(f"Columnas → RUN='{col_run}' | Monto='{col_monto}' | Planilla='{col_planilla}' "
        f"| Calidad='{col_calidad}' | N°Doc='{col_nro_doc}' | Programa='{col_programa}' | Unidad='{col_unidad}'")

    if filtro_calidad and filtro_calidad != "(Todas)" and col_calidad:
        df = df[df[col_calidad].astype(str) == filtro_calidad]
        log(f"Filtro Calidad '{filtro_calidad}': {len(df)} filas")
    if filtro_planilla and filtro_planilla != "(Todas)" and col_planilla:
        df = df[df[col_planilla].astype(str) == filtro_planilla]
        log(f"Filtro Planilla '{filtro_planilla}': {len(df)} filas")
    if filtros_programa and col_programa:
        df = df[df[col_programa].astype(str).isin(filtros_programa)]
        log(f"Filtro Programas: {len(df)} filas")
    if filtros_unidad and col_unidad:
        df = df[df[col_unidad].astype(str).isin(filtros_unidad)]
        log(f"Filtro Unidades: {len(df)} filas")

    mapping = {}
    mapping_list = {}
    for _, row in df.iterrows():
        run_cuerpo = _normalizar_run(row[col_run]) if col_run else ""
        monto      = _parsear_monto(row[col_monto]) if col_monto else None
        nro_doc    = str(row[col_nro_doc]).strip() if col_nro_doc else ""
        planilla   = str(row[col_planilla]).strip() if col_planilla else ""
        calidad    = str(row[col_calidad]).strip() if col_calidad else ""
        programa   = str(row[col_programa]).strip() if col_programa else ""
        unidad     = str(row[col_unidad]).strip() if col_unidad else ""

        if run_cuerpo and monto is not None:
            registro = {
                "run_cuerpo": run_cuerpo,
                "monto":      monto,
                "nro_doc":    nro_doc,
                "planilla":   planilla,
                "calidad":    calidad,
                "programa":   programa,
                "unidad":     unidad,
            }
            mapping[(run_cuerpo, monto)] = registro
            mapping_list.setdefault((run_cuerpo, monto), []).append(registro)

    log(f"Claves (RUN, Monto) cargadas: {len(mapping)}")
    return mapping, mapping_list


# ══════════════════════════════════════════════════════════════════════════════
# THREAD — LIQUIDACIONES (sin cambios)
# ══════════════════════════════════════════════════════════════════════════════

def etiquetar_pdf_thread(
    pdf_bytes: bytes,
    pdf_nombre: str,
    df_etiquetas: pd.DataFrame,
    periodo: str,
    filtro_calidad,
    filtro_planilla,
    programas_sel,
    unidades_sel,
    paginas_spec: str,
    log_q: queue.Queue,
    stop_ev: threading.Event,
):
    def log(msg):
        log_q.put(msg)

    try:
        import pdfplumber
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            from PyPDF2 import PdfReader, PdfWriter

        log(f"📄 Procesando: {pdf_nombre}")

        mapping_run_monto, _ = construir_mapping_desde_excel(
            df_etiquetas, filtro_calidad, filtro_planilla,
            programas_sel or None, unidades_sel or None, log
        )

        if not mapping_run_monto:
            log("⚠️ El mapping quedó vacío — revisa los filtros o columnas del Excel.")
            return

        pdf_buf = io.BytesIO(pdf_bytes)
        reader  = PdfReader(pdf_buf)
        total_paginas = len(reader.pages)
        log(f"📑 Total páginas en PDF: {total_paginas}")

        paginas_indices = parsear_rangos_paginas(paginas_spec, total_paginas)
        log(f"🔢 Páginas a procesar: {len(paginas_indices)} "
            f"({'todas' if not paginas_spec.strip() else paginas_spec})")

        zip_buf        = io.BytesIO()
        ok             = 0
        no_match       = []
        resumen        = []
        used_zip_paths = set()

        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            pdf_buf_pdfplumber = io.BytesIO(pdf_bytes)
            with pdfplumber.open(pdf_buf_pdfplumber) as pdf_text:
                for i, idx in enumerate(paginas_indices, 1):
                    if stop_ev.is_set():
                        log("⛔ Detenido por el usuario.")
                        break

                    page_pl = pdf_text.pages[idx]
                    texto   = page_pl.extract_text() or ""

                    run   = extraer_run(texto)
                    monto = extraer_total_haberes(texto)

                    if not run or monto is None:
                        no_match.append({
                            "Página": idx + 1,
                            "RUT extraído": run or "—",
                            "Monto extraído": monto,
                            "Motivo": "Sin RUT o sin monto",
                        })
                        log(f"  [Pág {idx+1}] ⚠️ Sin RUT/Monto → RUT='{run}' Monto={monto}")
                    else:
                        info = mapping_run_monto.get((run, monto))
                        if not info:
                            no_match.append({
                                "Página": idx + 1,
                                "RUT extraído": run,
                                "Monto extraído": f"${monto:,}".replace(",", "."),
                                "Motivo": "Sin match en Excel",
                            })
                            log(f"  [Pág {idx+1}] ⚠️ Sin match → RUT={run}, Monto={monto:,}")
                        else:
                            planilla_clean = str(info["planilla"]).replace(" ", "")
                            etiqueta   = f"{periodo}_{info['run_cuerpo']}_{info['nro_doc']}_{planilla_clean}"
                            nombre_pdf = f"{etiqueta}.pdf"

                            writer = PdfWriter()
                            writer.add_page(reader.pages[idx])
                            page_buf = io.BytesIO()
                            writer.write(page_buf)
                            page_buf.seek(0)

                            programa_clean = re.sub(r'[<>:"/\\|?*]', "_", str(info["programa"] or "SIN_PROGRAMA"))
                            programa_clean = programa_clean[:40].rstrip("_").rstrip()
                            zip_path = f"{programa_clean}/{nombre_pdf}" if info["programa"] else nombre_pdf

                            if zip_path in used_zip_paths:
                                stem, ext = zip_path.rsplit(".", 1)
                                c_dup = 1
                                while zip_path in used_zip_paths:
                                    zip_path = f"{stem}_{c_dup}.{ext}"
                                    c_dup += 1
                            used_zip_paths.add(zip_path)

                            zf.writestr(zip_path, page_buf.read())
                            ok += 1
                            nombre_final = zip_path.split("/")[-1]
                            resumen.append({
                                "Página":   idx + 1,
                                "RUT":      info["run_cuerpo"],
                                "N°Doc":    info["nro_doc"],
                                "Planilla": info["planilla"],
                                "Calidad":  info["calidad"],
                                "Programa": info["programa"],
                                "Unidad":   info["unidad"],
                                "Monto":    f"${monto:,}".replace(",", "."),
                                "Archivo":  nombre_final,
                            })
                            log(f"  [Pág {idx+1}] ✅ {nombre_final}")

                    log_q.put(f"__PROGRESS__{i}__{len(paginas_indices)}")

        zip_buf.seek(0)
        log(f"─── RESUMEN: ✅ {ok} etiquetados | ⚠️ {len(no_match)} sin match ───")
        if no_match:
            log(f"Páginas sin match: {[r['Página'] for r in no_match]}")

        log_q.put(("__ZIP__",     zip_buf.read()))
        log_q.put(("__RESUMEN__", resumen))
        log_q.put(("__NOMATCH__", no_match))

    except ImportError as e_imp:
        log_q.put(f"❌ Librería no instalada: {e_imp}. Ejecuta: pip install pdfplumber pypdf")
    except Exception as e:
        import traceback
        log_q.put(f"❌ Error: {e}")
        log_q.put(traceback.format_exc())
    finally:
        log_q.put("__DONE__")


# ══════════════════════════════════════════════════════════════════════════════
# THREAD — HONORARIOS AUTO (portado de honorarios_auto.py)
# ══════════════════════════════════════════════════════════════════════════════

def honorarios_auto_thread(
    pdf_bytes: bytes,
    pdf_nombre: str,
    mapping_run_doc: dict,
    periodo: str,
    paginas_spec: str,
    forzado: bool,
    tess_path: str,
    log_q: queue.Queue,
    stop_ev: threading.Event,
):
    def log(msg):
        log_q.put(msg)

    try:
        import pdfplumber
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            from PyPDF2 import PdfReader, PdfWriter

        if not _TESSERACT_LIB_OK:
            log("❌ pytesseract no está instalado. Ejecuta: pip install pytesseract")
            return
        if not _PIL_OK:
            log("❌ Pillow no está instalado. Ejecuta: pip install Pillow")
            return
        if not _cfg_tess(tess_path):
            log(f"⚠️ Tesseract no encontrado. Verifica la ruta: '{tess_path}'")
            return

        log(f"📄 Procesando honorarios: {pdf_nombre}")

        pdf_buf = io.BytesIO(pdf_bytes)
        reader  = PdfReader(pdf_buf)
        total   = len(reader.pages)

        paginas_indices = parsear_rangos_paginas(paginas_spec, total)
        if len(paginas_indices) % 2 != 0:
            paginas_indices = paginas_indices[:-1]
        total_pares = len(paginas_indices) // 2
        log(f"📑 Total páginas: {total} | Pares a procesar: {total_pares}")

        zip_buf  = io.BytesIO()
        no_rec   = []
        ok       = 0
        used_zip = set()

        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf_pl:
                for idx_par in range(total_pares):
                    if stop_ev.is_set():
                        log("⛔ Detenido por el usuario.")
                        break

                    idx1 = paginas_indices[2 * idx_par]
                    idx2 = paginas_indices[2 * idx_par + 1]

                    page = pdf_pl.pages[idx1]
                    img  = page.to_image(resolution=450).original.convert("RGB")
                    w, h = img.size

                    # OCR: RUN
                    box_sup = (int(0.05 * w), int(0.05 * h), int(0.95 * w), int(0.38 * h))
                    cfg_run = r"--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789.kK:-RrUuTt "
                    texto_sup = _ocr_roi(img, box_sup, preprocess=_preproc_suave, config=cfg_run)
                    run = _norm_run_ocr(_extraer_run_v2(texto_sup))

                    # OCR: N°Doc
                    doc, dbg = _extraer_nro_doc_anclado(img)

                    if not run or not doc:
                        no_rec.append({
                            "pag1": idx1, "pag2": idx2,
                            "run_ocr": run, "doc_ocr": doc,
                            "motivo": f"NO RUN/NºDOC válido. {dbg}", "dbg": dbg,
                        })
                        log(f"  [Par {idx1+1}-{idx2+1}] ⚠️ Sin RUN/NºDOC. RUN='{run}' NºDoc='{doc}'")
                        log_q.put(f"__PROGRESS_HON__{idx_par+1}__{total_pares}")
                        continue

                    # Match directo
                    info = _consumir(mapping_run_doc, run, doc)

                    # Forzado
                    if info is None and forzado:
                        docs_excel = _docs_disp(mapping_run_doc, run)
                        if docs_excel:
                            corr, why = _forzar_doc(doc, docs_excel)
                            if corr:
                                log(f"  [Par {idx1+1}] CORRECCIÓN: OCR='{doc}' → '{corr}' ({why})")
                                info = _consumir(mapping_run_doc, run, corr)
                                doc = corr

                    if info is None:
                        docs_excel = _docs_disp(mapping_run_doc, run)
                        no_rec.append({
                            "pag1": idx1, "pag2": idx2,
                            "run_ocr": run, "doc_ocr": doc,
                            "motivo": f"SIN MATCH (RUN+NºDOC). Docs Excel RUN: {docs_excel}",
                            "dbg": dbg,
                        })
                        log(f"  [Par {idx1+1}-{idx2+1}] ⚠️ Sin match → RUN={run}, NºDoc={doc}")
                        log_q.put(f"__PROGRESS_HON__{idx_par+1}__{total_pares}")
                        continue

                    # Generar PDF de 2 páginas
                    planilla_clean = str(info["planilla"]).replace(" ", "")
                    etiqueta = f"{periodo}_{info['run_cuerpo']}_{info['nro_doc']}_{planilla_clean}.pdf"
                    zip_path = etiqueta
                    if zip_path in used_zip:
                        stem, ext = zip_path.rsplit(".", 1)
                        c_dup = 1
                        while zip_path in used_zip:
                            zip_path = f"{stem}_{c_dup}.{ext}"
                            c_dup += 1
                    used_zip.add(zip_path)

                    writer = PdfWriter()
                    writer.add_page(reader.pages[idx1])
                    writer.add_page(reader.pages[idx2])
                    page_buf = io.BytesIO()
                    writer.write(page_buf)
                    page_buf.seek(0)
                    zf.writestr(zip_path, page_buf.read())
                    ok += 1
                    log(f"  [Par {idx1+1}-{idx2+1}] ✅ {zip_path}")
                    log_q.put(f"__PROGRESS_HON__{idx_par+1}__{total_pares}")

        zip_buf.seek(0)
        log(f"─── RESUMEN HONORARIOS: ✅ {ok} etiquetados | ⚠️ {len(no_rec)} sin match ───")

        log_q.put(("__HON_ZIP__",     zip_buf.read()))
        log_q.put(("__HON_NOREC__",   no_rec))
        log_q.put(("__HON_MAPPING__", mapping_run_doc))   # mapping consumido (resto disponible para Manual)

    except ImportError as e:
        log_q.put(f"❌ Librería no instalada: {e}. Ejecuta: pip install pdfplumber pypdf pytesseract Pillow")
    except Exception as e:
        import traceback
        log_q.put(f"❌ Error: {e}")
        log_q.put(traceback.format_exc())
    finally:
        log_q.put("__HON_DONE__")


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDAD: renderizar página PDF como imagen (para preview)
# ══════════════════════════════════════════════════════════════════════════════

def _render_pagina(pdf_bytes: bytes, page_idx: int, resolution: int = 180) -> bytes | None:
    """Renderiza una página del PDF a JPEG bytes para mostrar en st.image()."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            if 0 <= page_idx < len(pdf.pages):
                img = pdf.pages[page_idx].to_image(resolution=resolution).original.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=82)
                return buf.getvalue()
    except Exception:
        return None
    return None


# ══════════════════════════════════════════════════════════════════════════════
# STREAMLIT PAGE CONFIG + DISEÑO
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Etiquetador PDF · Evidant Suite",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ev_design.render(
    current="imagenes",
    page_title="Etiquetador de Liquidaciones & Honorarios",
    page_sub="Liquidaciones: RUT+Monto por página · Honorarios: OCR boletas 2 páginas c/u",
    breadcrumb="Imágenes",
    icon="🏷️",
)

# ══════════════════════════════════════════════════════════════════════════════
# ESTADO DE SESIÓN
# ══════════════════════════════════════════════════════════════════════════════

def _init():
    defaults = {
        # ── Liquidaciones ──
        "et_df":          None,
        "et_calidades":   [],
        "et_planillas":   [],
        "et_programas":   [],
        "et_unidades":    [],
        "et_log":         [],
        "et_running":     False,
        "et_resumen":     None,
        "et_nomatch":     None,
        "et_zip":         None,
        "et_queue":       None,
        "et_stop":        None,
        "et_progress":    (0, 1),
        # ── Honorarios (compartido: Excel + PDF) ──
        "hon_df":         None,
        "hon_calidades":  [],
        "hon_planillas":  [],
        "hon_programas":  [],
        "hon_unidades":   [],
        "hon_pdf_bytes":  None,
        "hon_pdf_name":   "",
        # ── Honorarios Auto ──
        "hon_log":        [],
        "hon_running":    False,
        "hon_queue":      None,
        "hon_stop":       None,
        "hon_progress":   (0, 1),
        "hon_zip":        None,
        "hon_no_rec":     None,
        "hon_mapping":    None,   # mapping_run_doc remanente después del auto
        # ── Honorarios Manual ──
        "hon_man_pendientes":   [],
        "hon_man_sel_idx":      0,
        "hon_man_prev_idx":     -1,
        "hon_man_zip":          None,
        # ── Honorarios RUT ──
        "hon_rut_items":        [],
        "hon_rut_index":        {},
        "hon_rut_run_cache":    {},
        "hon_rut_indexed":      False,
        "hon_rut_sel_idx":      0,
        "hon_rut_prev_idx":     -1,
        "hon_rut_zip":          None,
        # ── Preview cache ──
        "hon_preview_cache":    {},
        # ── Honorarios Masivo ──
        "hon_mas_df_consol":    None,   # DataFrame hoja CONSOLIDADO
        "hon_mas_df_pasmi":     None,   # DataFrame hoja PASMI
        "hon_mas_pdfs":         {},     # {codigo_unidad_str: pdf_bytes}
        "hon_mas_zip":          None,
        "hon_mas_log":          [],
        "hon_mas_resumen":      None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init()

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
.log-box {
  background:#0d0d0d;border:1px solid rgba(255,255,255,.07);border-radius:10px;
  padding:1rem 1.2rem;font-family:'JetBrains Mono',monospace;font-size:.72rem;
  color:#b3b3b3;max-height:380px;overflow-y:auto;line-height:1.7;white-space:pre-wrap;
}
.estado-chip {
  display:inline-block;padding:.18rem .6rem;border-radius:20px;font-size:.75rem;font-weight:600;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT: TABS PRINCIPALES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="ev-content ev-anim">', unsafe_allow_html=True)

tab_liq, tab_hon = st.tabs(["🗂️ Liquidaciones", "📋 Honorarios"])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — LIQUIDACIONES (código sin cambios)
# ─────────────────────────────────────────────────────────────────────────────
with tab_liq:
    st.markdown(
        '<div style="background:rgba(29,185,84,.05);border:1px solid rgba(29,185,84,.15);'
        'border-radius:10px;padding:.9rem 1.3rem;font-size:.84rem;color:#86a093;margin-bottom:1.5rem;">'
        '🏷️ <strong style="color:#ccc;">Cómo funciona:</strong> '
        'Sube el PDF de liquidaciones (puede ser multi-página) y el Excel ETIQUETAS. '
        'Por cada página se extrae el <strong>RUT</strong> y el <strong>Total Haberes</strong> del texto, '
        'se busca en el Excel la coincidencia <code>(RUT, Monto)</code> y se guarda la página como PDF '
        'nombrado <code>AAAAMM_RUT_NDOC_PLANILLA.pdf</code>. Descarga el ZIP con todos los etiquetados.'
        '</div>',
        unsafe_allow_html=True,
    )

    # 01 — Excel
    st.markdown("""
<div class="ev-section">
  <span class="ev-section-num">01</span>
  <span class="ev-section-title">Excel de Etiquetas</span>
  <span class="ev-section-sub">Hoja "ETIQUETAS" · RUN, Monto (Total Haberes), Planilla, Calidad, N°Doc, Programa, Unidad</span>
</div>
""", unsafe_allow_html=True)

    excel_file = st.file_uploader("Sube el Excel de etiquetas", type=["xlsx", "xls"], key="et_excel_up")

    if excel_file:
        try:
            xls  = pd.ExcelFile(excel_file)
            hoja = next(
                (h for h in xls.sheet_names if h.strip().lower() == "etiquetas"),
                xls.sheet_names[0],
            )
            df_e = pd.read_excel(xls, sheet_name=hoja, dtype=str)
            df_e.columns = [str(c).strip() for c in df_e.columns]
            st.session_state["et_df"] = df_e

            construir_mapping_desde_excel(df_e, log=lambda _: None)

            cols = list(df_e.columns)
            low  = {c: c.lower() for c in cols}

            def find_col_liq(*names):
                for n in names:
                    if n in cols:
                        return n
                for n in names:
                    cands = [c for c in cols if n.lower() in low[c]]
                    if cands:
                        return cands[0]
                return None

            col_cal  = find_col_liq("Calidad Juridica", "Calidad Jurídica", "Calidad")
            col_plan = find_col_liq("Planilla de Pago", "Planilla")
            col_prog = find_col_liq("Programa")
            col_uni  = find_col_liq("Unidad")

            st.session_state["et_calidades"] = ["(Todas)"] + sorted(df_e[col_cal].dropna().astype(str).unique().tolist()) if col_cal else ["(Todas)"]
            st.session_state["et_planillas"] = ["(Todas)"] + sorted(df_e[col_plan].dropna().astype(str).unique().tolist()) if col_plan else ["(Todas)"]
            st.session_state["et_programas"] = sorted(df_e[col_prog].dropna().astype(str).unique().tolist()) if col_prog else []
            st.session_state["et_unidades"]  = sorted(df_e[col_uni].dropna().astype(str).unique().tolist()) if col_uni else []

            st.success(f"✅ **{len(df_e):,}** filas · Hoja: **{hoja}**")
            with st.expander("Vista previa (primeras 8 filas)", expanded=False):
                st.markdown(ev_design.ev_table_html(df_e.head(8)), unsafe_allow_html=True)

        except Exception as e_xl:
            st.error(f"Error al leer el Excel: {e_xl}")

    # 02 — PDF
    st.markdown("""
<div class="ev-section">
  <span class="ev-section-num">02</span>
  <span class="ev-section-title">PDF de Liquidaciones</span>
  <span class="ev-section-sub">Puede ser multi-página — cada página es una liquidación</span>
</div>
""", unsafe_allow_html=True)

    pdf_file = st.file_uploader("Sube el PDF de liquidaciones", type=["pdf"], key="et_pdf_up")
    if pdf_file:
        st.markdown(
            f'<div style="font-size:.83rem;color:#1ed760;margin-top:.4rem;">'
            f'✅ Archivo cargado: <strong>{pdf_file.name}</strong> · '
            f'{pdf_file.size/1024:.1f} KB</div>',
            unsafe_allow_html=True,
        )

    # 03 — Parámetros
    st.markdown("""
<div class="ev-section">
  <span class="ev-section-num">03</span>
  <span class="ev-section-title">Parámetros de Etiquetado</span>
</div>
""", unsafe_allow_html=True)

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        anio_val = st.text_input("Año", value=datetime.now().strftime("%Y"), placeholder="2025", key="et_anio")
        mes_val  = st.text_input("Mes", value=datetime.now().strftime("%m"), placeholder="01", key="et_mes")
        periodo_liq = f"{anio_val.strip()}{mes_val.strip().zfill(2)}"
    with col_p2:
        calidad_sel = st.selectbox("Calidad Jurídica", options=st.session_state.get("et_calidades", ["(Todas)"]), key="et_calidad")
        planilla_sel = st.selectbox("Planilla de Pago", options=st.session_state.get("et_planillas", ["(Todas)"]), key="et_planilla")
    with col_p3:
        paginas_spec_liq = st.text_input("Páginas a procesar", value="", placeholder="Vacío = todas · Ej: 1,4-10,22", key="et_paginas")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        progs_all_liq = st.session_state.get("et_programas", [])
        progs_sel_liq = st.multiselect("Filtrar por Programa", options=progs_all_liq, default=[], key="et_progs_sel")
    with col_f2:
        unis_all_liq = st.session_state.get("et_unidades", [])
        unis_sel_liq = st.multiselect("Filtrar por Unidad", options=unis_all_liq, default=[], key="et_unis_sel")

    # 04 — Ejecución
    st.markdown("""
<div class="ev-section">
  <span class="ev-section-num">04</span>
  <span class="ev-section-title">Ejecución</span>
</div>
""", unsafe_allow_html=True)

    df_etiquetas_liq = st.session_state.get("et_df")
    excel_ok_liq = df_etiquetas_liq is not None
    pdf_ok_liq   = pdf_file is not None
    periodo_ok_liq = bool(re.fullmatch(r"\d{6}", periodo_liq))
    running_liq  = st.session_state["et_running"]

    req_cols_liq = st.columns(3)
    for i, (lbl, ok) in enumerate([
        ("Excel de etiquetas cargado", excel_ok_liq),
        ("PDF de liquidaciones cargado", pdf_ok_liq),
        (f"Período válido ({periodo_liq})", periodo_ok_liq),
    ]):
        with req_cols_liq[i]:
            color  = "#1ed760" if ok else "#f87171"
            bg     = "rgba(29,185,84,.08)" if ok else "rgba(239,68,68,.08)"
            border = "rgba(29,185,84,.2)" if ok else "rgba(239,68,68,.2)"
            st.markdown(
                f'<div style="background:{bg};border:1px solid {border};border-radius:8px;'
                f'padding:.65rem .9rem;font-size:.8rem;color:{color};">{"✓" if ok else "✗"} {lbl}</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 1])
    with btn_c1:
        can_start_liq = excel_ok_liq and pdf_ok_liq and periodo_ok_liq and not running_liq
        if st.button("▶️ Etiquetar PDF", disabled=not can_start_liq, use_container_width=True, key="et_start"):
            pdf_file.seek(0)
            pdf_bytes = pdf_file.read()
            q = queue.Queue()
            stop_ev = threading.Event()
            st.session_state.update({
                "et_queue": q, "et_stop": stop_ev, "et_log": [],
                "et_running": True, "et_resumen": None, "et_nomatch": None,
                "et_zip": None, "et_progress": (0, 1),
            })
            threading.Thread(
                target=etiquetar_pdf_thread,
                args=(pdf_bytes, pdf_file.name, df_etiquetas_liq, periodo_liq,
                      calidad_sel if calidad_sel != "(Todas)" else None,
                      planilla_sel if planilla_sel != "(Todas)" else None,
                      progs_sel_liq or None, unis_sel_liq or None,
                      paginas_spec_liq, q, stop_ev),
                daemon=True,
            ).start()
            st.rerun()
    with btn_c2:
        if st.button("⛔ Detener", disabled=not running_liq, use_container_width=True, key="et_stop_btn"):
            s = st.session_state.get("et_stop")
            if s:
                s.set()
            st.session_state["et_running"] = False
            st.rerun()
    with btn_c3:
        if st.button("🔄 Actualizar", use_container_width=True, key="et_refresh"):
            q = st.session_state.get("et_queue")
            if q:
                while True:
                    try:
                        msg = q.get_nowait()
                        if msg == "__DONE__":
                            st.session_state["et_running"] = False
                        elif isinstance(msg, tuple) and msg[0] == "__ZIP__":
                            st.session_state["et_zip"] = msg[1]
                        elif isinstance(msg, tuple) and msg[0] == "__RESUMEN__":
                            st.session_state["et_resumen"] = msg[1]
                        elif isinstance(msg, tuple) and msg[0] == "__NOMATCH__":
                            st.session_state["et_nomatch"] = msg[1]
                        elif isinstance(msg, str) and msg.startswith("__PROGRESS__"):
                            _, cur, tot = msg.split("__")[1:]
                            st.session_state["et_progress"] = (int(cur), int(tot))
                        else:
                            st.session_state["et_log"].append(msg)
                    except queue.Empty:
                        break
            st.rerun()

    if running_liq:
        q = st.session_state.get("et_queue")
        if q:
            while True:
                try:
                    msg = q.get_nowait()
                    if msg == "__DONE__":
                        st.session_state["et_running"] = False
                    elif isinstance(msg, tuple) and msg[0] == "__ZIP__":
                        st.session_state["et_zip"] = msg[1]
                    elif isinstance(msg, tuple) and msg[0] == "__RESUMEN__":
                        st.session_state["et_resumen"] = msg[1]
                    elif isinstance(msg, tuple) and msg[0] == "__NOMATCH__":
                        st.session_state["et_nomatch"] = msg[1]
                    elif isinstance(msg, str) and msg.startswith("__PROGRESS__"):
                        _, cur, tot = msg.split("__")[1:]
                        st.session_state["et_progress"] = (int(cur), int(tot))
                    else:
                        st.session_state["et_log"].append(msg)
                except queue.Empty:
                    break

    prog_cur, prog_tot = st.session_state.get("et_progress", (0, 1))
    if running_liq or prog_cur > 0:
        _pct = min(prog_cur / max(prog_tot, 1), 1.0)
        _pct_str = f"{_pct*100:.1f}%"
        _restantes = max(prog_tot - prog_cur, 0)
        st.progress(_pct, text=f"⚙️ Procesando página **{prog_cur}** de **{prog_tot}** — {_pct_str} completado")
        _mc1, _mc2, _mc3 = st.columns(3)
        _mc1.metric("Páginas procesadas", prog_cur, delta=None)
        _mc2.metric("Páginas restantes", _restantes, delta=None)
        _mc3.metric("Progreso", _pct_str, delta=None)
        if running_liq:
            st.spinner("Etiquetando, por favor espere…")

    log_lines_liq = st.session_state.get("et_log", [])
    if log_lines_liq:
        st.markdown("""
<div class="ev-section" style="margin-top:1.2rem;">
  <span class="ev-section-num">05</span>
  <span class="ev-section-title">Log</span>
  <span class="ev-section-sub">Presiona Actualizar para ver nuevos mensajes</span>
</div>
""", unsafe_allow_html=True)
        log_html = ""
        for line in log_lines_liq[-300:]:
            if "❌" in line or "Error" in line or "Traceback" in line:
                css = "color:#f87171;"
            elif "✅" in line or "RESUMEN" in line:
                css = "color:#1ed760;"
            elif "⚠️" in line or "⛔" in line or "Sin match" in line:
                css = "color:#fbbf24;"
            elif "📄" in line or "📑" in line or "Columnas" in line:
                css = "color:#60a5fa;"
            else:
                css = "color:#b3b3b3;"
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            log_html += f'<span style="{css}">{escaped}</span>\n'
        st.markdown(f'<div class="log-box">{log_html}</div>', unsafe_allow_html=True)

    zip_bytes_liq = st.session_state.get("et_zip")
    resumen_liq   = st.session_state.get("et_resumen")
    no_match_liq  = st.session_state.get("et_nomatch")

    if zip_bytes_liq or resumen_liq or no_match_liq:
        st.markdown("""
<div class="ev-section" style="margin-top:1.5rem;">
  <span class="ev-section-num">06</span>
  <span class="ev-section-title">Resultados</span>
</div>
""", unsafe_allow_html=True)
    if zip_bytes_liq:
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button(
            label=f"⬇️ Descargar ZIP ({len(zip_bytes_liq)//1024} KB)",
            data=zip_bytes_liq,
            file_name=f"etiquetados_{periodo_liq}_{ts}.zip",
            mime="application/zip",
            use_container_width=True,
        )
    if resumen_liq:
        st.markdown(f"**✅ {len(resumen_liq)} páginas etiquetadas:**")
        df_res = pd.DataFrame(resumen_liq)
        st.markdown(ev_design.ev_table_html(df_res), unsafe_allow_html=True)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as xw:
            df_res.to_excel(xw, index=False, sheet_name="Etiquetados")
            if no_match_liq:
                pd.DataFrame(no_match_liq).to_excel(xw, index=False, sheet_name="Sin_Match")
        buf.seek(0)
        st.download_button(
            label="⬇️ Descargar reporte Excel",
            data=buf,
            file_name=f"reporte_etiquetado_{periodo_liq}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    if no_match_liq:
        st.markdown(f"**⚠️ {len(no_match_liq)} páginas sin match:**")
        st.markdown(ev_design.ev_table_html(pd.DataFrame(no_match_liq)), unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — HONORARIOS
# ─────────────────────────────────────────────────────────────────────────────
with tab_hon:
    st.markdown(
        '<div style="background:rgba(96,165,250,.05);border:1px solid rgba(96,165,250,.15);'
        'border-radius:10px;padding:.9rem 1.3rem;font-size:.84rem;color:#86a093;margin-bottom:1.5rem;">'
        '📋 <strong style="color:#ccc;">Cómo funciona:</strong> '
        'Cada boleta de honorarios ocupa <strong>2 páginas</strong> del PDF. '
        'El modo <em>Auto</em> usa OCR para extraer RUT y N°Boleta y los etiqueta automáticamente. '
        'Los no reconocidos se gestionan en <em>Manual</em> (asignación por lista) o '
        '<em>Buscar por RUT</em> (búsqueda directa).'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Carga compartida: Excel + PDF ────────────────────────────────────────
    st.markdown("""
<div class="ev-section">
  <span class="ev-section-num">01</span>
  <span class="ev-section-title">Excel de Etiquetas (Honorarios)</span>
  <span class="ev-section-sub">Misma hoja ETIQUETAS — usa columnas RUN, N°Documento, Planilla, Calidad</span>
</div>
""", unsafe_allow_html=True)

    hon_excel_file = st.file_uploader(
        "Sube el Excel de etiquetas (honorarios)",
        type=["xlsx", "xls"],
        key="hon_excel_up",
    )

    if hon_excel_file:
        try:
            xls_h = pd.ExcelFile(hon_excel_file)
            hoja_h = next(
                (h for h in xls_h.sheet_names if h.strip().lower() == "etiquetas"),
                xls_h.sheet_names[0],
            )
            df_h = pd.read_excel(xls_h, sheet_name=hoja_h, dtype=str)
            df_h.columns = [str(c).strip() for c in df_h.columns]
            st.session_state["hon_df"] = df_h

            # Categorías
            cols_h = list(df_h.columns)
            low_h  = {c: c.lower() for c in cols_h}

            def find_col_h(*names):
                for n in names:
                    if n in cols_h:
                        return n
                for n in names:
                    cands = [c for c in cols_h if n.lower() in low_h[c]]
                    if cands:
                        return cands[0]
                return None

            col_cal_h  = find_col_h("Calidad Juridica", "Calidad Jurídica", "Calidad")
            col_plan_h = find_col_h("Planilla de Pago", "Planilla")
            col_prog_h = find_col_h("Programa")
            col_uni_h  = find_col_h("Unidad")

            st.session_state["hon_calidades"] = ["(Todas)"] + sorted(df_h[col_cal_h].dropna().astype(str).unique().tolist()) if col_cal_h else ["(Todas)"]
            st.session_state["hon_planillas"] = ["(Todas)"] + sorted(df_h[col_plan_h].dropna().astype(str).unique().tolist()) if col_plan_h else ["(Todas)"]
            st.session_state["hon_programas"] = sorted(df_h[col_prog_h].dropna().astype(str).unique().tolist()) if col_prog_h else []
            st.session_state["hon_unidades"]  = sorted(df_h[col_uni_h].dropna().astype(str).unique().tolist()) if col_uni_h else []

            st.success(f"✅ **{len(df_h):,}** filas · Hoja: **{hoja_h}**")
            with st.expander("Vista previa", expanded=False):
                st.markdown(ev_design.ev_table_html(df_h.head(8)), unsafe_allow_html=True)
        except Exception as e_xh:
            st.error(f"Error al leer el Excel: {e_xh}")

    st.markdown("""
<div class="ev-section">
  <span class="ev-section-num">02</span>
  <span class="ev-section-title">PDF de Boletas de Honorarios</span>
  <span class="ev-section-sub">2 páginas por boleta — se procesan en pares consecutivos</span>
</div>
""", unsafe_allow_html=True)

    hon_pdf_file = st.file_uploader(
        "Sube el PDF de boletas de honorarios",
        type=["pdf"],
        key="hon_pdf_up",
    )
    if hon_pdf_file:
        hon_pdf_file.seek(0)
        st.session_state["hon_pdf_bytes"] = hon_pdf_file.read()
        st.session_state["hon_pdf_name"]  = hon_pdf_file.name
        st.session_state["hon_preview_cache"] = {}  # reset preview cache
        st.markdown(
            f'<div style="font-size:.83rem;color:#60a5fa;margin-top:.4rem;">'
            f'✅ PDF cargado: <strong>{hon_pdf_file.name}</strong> · '
            f'{len(st.session_state["hon_pdf_bytes"])//1024:.0f} KB</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Sub-tabs Honorarios ───────────────────────────────────────────────────
    subtab_auto, subtab_manual, subtab_rut, subtab_masivo = st.tabs([
        "⚡ Auto (OCR)",
        "✏️ Manual (no reconocidos)",
        "🔍 Buscar por RUT",
        "📦 Masivo (Por Unidad)",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # SUB-TAB: AUTO
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_auto:
        df_hon = st.session_state.get("hon_df")
        pdf_hon_bytes = st.session_state.get("hon_pdf_bytes")

        # Parámetros
        st.markdown("""
<div class="ev-section" style="margin-top:.5rem;">
  <span class="ev-section-num">03</span>
  <span class="ev-section-title">Parámetros Auto</span>
</div>
""", unsafe_allow_html=True)

        col_ha1, col_ha2, col_ha3 = st.columns(3)
        with col_ha1:
            anio_hon = st.text_input("Año", value=datetime.now().strftime("%Y"), key="hon_anio")
            mes_hon  = st.text_input("Mes", value=datetime.now().strftime("%m"), key="hon_mes")
            periodo_hon = f"{anio_hon.strip()}{mes_hon.strip().zfill(2)}"
        with col_ha2:
            calidad_hon  = st.selectbox("Calidad Jurídica", options=st.session_state.get("hon_calidades", ["(Todas)"]), key="hon_calidad")
            planilla_hon = st.selectbox("Planilla de Pago", options=st.session_state.get("hon_planillas", ["(Todas)"]), key="hon_planilla")
        with col_ha3:
            paginas_hon = st.text_input("Páginas a procesar", value="", placeholder="Vacío = todas · Ej: 1-20", key="hon_paginas")
            forzado_hon = st.toggle("Corrección automática de N°Doc (forzado)", value=True, key="hon_forzado",
                                    help="Intenta corregir el N°Doc OCR usando sufijos, substrings y proximidad numérica")

        with st.expander("⚙️ Configuración Tesseract", expanded=False):
            tess_path_hon = st.text_input(
                "Ruta de tesseract.exe",
                value=st.session_state.get("hon_tess_path", _TESS_DEFAULT),
                key="hon_tess_path",
                help="Ruta completa al ejecutable tesseract.exe",
            )

        # Estado requerimientos
        excel_ok_hon   = df_hon is not None
        pdf_ok_hon     = pdf_hon_bytes is not None
        periodo_ok_hon = bool(re.fullmatch(r"\d{6}", periodo_hon))
        running_hon    = st.session_state["hon_running"]

        req_h = st.columns(3)
        for i, (lbl, ok) in enumerate([
            ("Excel cargado", excel_ok_hon),
            ("PDF cargado", pdf_ok_hon),
            (f"Período ({periodo_hon})", periodo_ok_hon),
        ]):
            with req_h[i]:
                color  = "#60a5fa" if ok else "#f87171"
                bg     = "rgba(96,165,250,.08)" if ok else "rgba(239,68,68,.08)"
                border = "rgba(96,165,250,.2)" if ok else "rgba(239,68,68,.2)"
                st.markdown(
                    f'<div style="background:{bg};border:1px solid {border};border-radius:8px;'
                    f'padding:.6rem .9rem;font-size:.8rem;color:{color};">{"✓" if ok else "✗"} {lbl}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)
        btn_h1, btn_h2, btn_h3 = st.columns([1, 1, 1])

        with btn_h1:
            can_start_hon = excel_ok_hon and pdf_ok_hon and periodo_ok_hon and not running_hon
            if st.button("▶️ Procesar Honorarios (Auto)", disabled=not can_start_hon,
                         use_container_width=True, key="hon_start"):
                mapping_copy = copy.deepcopy(
                    _construir_mapping_run_doc(
                        df_hon,
                        calidad_hon if calidad_hon != "(Todas)" else None,
                        planilla_hon if planilla_hon != "(Todas)" else None,
                        None, None,
                        log=lambda m: None,
                    )
                )
                q_h = queue.Queue()
                stop_h = threading.Event()
                st.session_state.update({
                    "hon_queue": q_h, "hon_stop": stop_h, "hon_log": [],
                    "hon_running": True, "hon_zip": None, "hon_no_rec": None,
                    "hon_mapping": None, "hon_progress": (0, 1),
                })
                threading.Thread(
                    target=honorarios_auto_thread,
                    args=(
                        pdf_hon_bytes, st.session_state["hon_pdf_name"],
                        mapping_copy, periodo_hon, paginas_hon,
                        forzado_hon, st.session_state.get("hon_tess_path", _TESS_DEFAULT),
                        q_h, stop_h,
                    ),
                    daemon=True,
                ).start()
                st.rerun()

        with btn_h2:
            if st.button("⛔ Detener", disabled=not running_hon,
                         use_container_width=True, key="hon_stop_btn"):
                s = st.session_state.get("hon_stop")
                if s:
                    s.set()
                st.session_state["hon_running"] = False
                st.rerun()

        with btn_h3:
            if st.button("🔄 Actualizar", use_container_width=True, key="hon_refresh"):
                q_h = st.session_state.get("hon_queue")
                if q_h:
                    while True:
                        try:
                            msg = q_h.get_nowait()
                            if msg == "__HON_DONE__":
                                st.session_state["hon_running"] = False
                            elif isinstance(msg, tuple) and msg[0] == "__HON_ZIP__":
                                st.session_state["hon_zip"] = msg[1]
                            elif isinstance(msg, tuple) and msg[0] == "__HON_NOREC__":
                                st.session_state["hon_no_rec"] = msg[1]
                                st.session_state["hon_man_pendientes"] = list(msg[1])
                            elif isinstance(msg, tuple) and msg[0] == "__HON_MAPPING__":
                                st.session_state["hon_mapping"] = msg[1]
                            elif isinstance(msg, str) and msg.startswith("__PROGRESS_HON__"):
                                _, _, cur, tot = msg.split("__")
                                st.session_state["hon_progress"] = (int(cur), int(tot))
                            else:
                                st.session_state["hon_log"].append(msg)
                        except queue.Empty:
                            break
                st.rerun()

        # Auto-poll
        if running_hon:
            q_h = st.session_state.get("hon_queue")
            if q_h:
                while True:
                    try:
                        msg = q_h.get_nowait()
                        if msg == "__HON_DONE__":
                            st.session_state["hon_running"] = False
                        elif isinstance(msg, tuple) and msg[0] == "__HON_ZIP__":
                            st.session_state["hon_zip"] = msg[1]
                        elif isinstance(msg, tuple) and msg[0] == "__HON_NOREC__":
                            st.session_state["hon_no_rec"] = msg[1]
                            st.session_state["hon_man_pendientes"] = list(msg[1])
                        elif isinstance(msg, tuple) and msg[0] == "__HON_MAPPING__":
                            st.session_state["hon_mapping"] = msg[1]
                        elif isinstance(msg, str) and msg.startswith("__PROGRESS_HON__"):
                            _, _, cur, tot = msg.split("__")
                            st.session_state["hon_progress"] = (int(cur), int(tot))
                        else:
                            st.session_state["hon_log"].append(msg)
                    except queue.Empty:
                        break

        prog_h_cur, prog_h_tot = st.session_state.get("hon_progress", (0, 1))
        if running_hon or prog_h_cur > 0:
            _h_pct = min(prog_h_cur / max(prog_h_tot, 1), 1.0)
            _h_pct_str = f"{_h_pct*100:.1f}%"
            _h_rest = max(prog_h_tot - prog_h_cur, 0)
            st.progress(_h_pct, text=f"⚙️ Procesando par **{prog_h_cur}** de **{prog_h_tot}** — {_h_pct_str} completado")
            _hc1, _hc2, _hc3 = st.columns(3)
            _hc1.metric("Pares procesados", prog_h_cur)
            _hc2.metric("Pares restantes", _h_rest)
            _hc3.metric("Progreso", _h_pct_str)
            if running_hon:
                st.spinner("Etiquetando honorarios, por favor espere…")

        # Log honorarios
        log_lines_hon = st.session_state.get("hon_log", [])
        if log_lines_hon:
            log_h_html = ""
            for line in log_lines_hon[-300:]:
                if "❌" in line or "Error" in line or "Traceback" in line:
                    css = "color:#f87171;"
                elif "✅" in line or "RESUMEN" in line:
                    css = "color:#1ed760;"
                elif "⚠️" in line or "CORRECCIÓN" in line or "Sin match" in line:
                    css = "color:#fbbf24;"
                elif "📄" in line or "📑" in line or "Columnas" in line:
                    css = "color:#60a5fa;"
                else:
                    css = "color:#b3b3b3;"
                escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                log_h_html += f'<span style="{css}">{escaped}</span>\n'
            st.markdown(f'<div class="log-box">{log_h_html}</div>', unsafe_allow_html=True)

        # Resultados auto
        hon_zip   = st.session_state.get("hon_zip")
        hon_no_rec = st.session_state.get("hon_no_rec")

        if hon_zip:
            ts_h = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button(
                label=f"⬇️ Descargar ZIP Honorarios ({len(hon_zip)//1024} KB)",
                data=hon_zip,
                file_name=f"honorarios_{periodo_hon}_{ts_h}.zip",
                mime="application/zip",
                use_container_width=True,
            )

        if hon_no_rec is not None:
            st.markdown(f"**⚠️ {len(hon_no_rec)} boletas sin match** → disponibles en la pestaña **Manual**")
            if hon_no_rec:
                df_norec = pd.DataFrame(hon_no_rec)[["pag1", "pag2", "run_ocr", "doc_ocr", "motivo"]]
                df_norec.columns = ["Pág 1", "Pág 2", "RUN OCR", "NºDoc OCR", "Motivo"]
                df_norec["Pág 1"] = df_norec["Pág 1"] + 1
                df_norec["Pág 2"] = df_norec["Pág 2"] + 1
                st.markdown(ev_design.ev_table_html(df_norec), unsafe_allow_html=True)

                # Exportar Excel de no reconocidos
                buf_nr = io.BytesIO()
                df_norec.to_excel(buf_nr, index=False, engine="openpyxl")
                buf_nr.seek(0)
                st.download_button(
                    label="⬇️ Descargar Excel de no reconocidos",
                    data=buf_nr,
                    file_name=f"no_reconocidos_{periodo_hon}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

    # ══════════════════════════════════════════════════════════════════════════
    # SUB-TAB: MANUAL
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_manual:
        pendientes = st.session_state.get("hon_man_pendientes", [])
        pdf_bytes_man = st.session_state.get("hon_pdf_bytes")
        mapping_man   = st.session_state.get("hon_mapping")

        # Permitir también cargar Excel de no-reconocidos guardado
        with st.expander("📂 Cargar Excel de no reconocidos (opcional)", expanded=not bool(pendientes)):
            nr_up = st.file_uploader("Excel de no reconocidos (columnas: pag1, pag2, run_ocr, doc_ocr, motivo)",
                                     type=["xlsx", "xls"], key="hon_man_nr_up")
            if nr_up:
                try:
                    df_nr_up = pd.read_excel(nr_up, dtype=str)
                    df_nr_up.columns = [str(c).strip().lower() for c in df_nr_up.columns]
                    items_up = []
                    for _, row in df_nr_up.iterrows():
                        items_up.append({
                            "pag1":    int(float(row.get("pag1", 0))),
                            "pag2":    int(float(row.get("pag2", 1))),
                            "run_ocr": str(row.get("run_ocr", "")),
                            "doc_ocr": str(row.get("doc_ocr", "")),
                            "motivo":  str(row.get("motivo", "")),
                            "dbg":     str(row.get("dbg", "")),
                        })
                    st.session_state["hon_man_pendientes"] = items_up
                    st.session_state["hon_man_prev_idx"] = -1
                    st.success(f"✅ {len(items_up)} registros cargados.")
                    st.rerun()
                except Exception as e_nr:
                    st.error(f"Error leyendo Excel: {e_nr}")

        pendientes = st.session_state.get("hon_man_pendientes", [])

        if not pendientes:
            st.info("No hay registros pendientes. Primero procesa el PDF en la pestaña **Auto (OCR)**.")
        else:
            # Construir mapping si no existe
            if mapping_man is None and st.session_state.get("hon_df") is not None:
                mapping_man = _construir_mapping_run_doc(
                    st.session_state["hon_df"], log=lambda _: None
                )
                st.session_state["hon_mapping"] = mapping_man

            # ── Lista de pendientes ──────────────────────────────────────────
            asignados_n = sum(1 for p in pendientes if p.get("run_manual") and p.get("doc_manual"))
            st.markdown(
                f'<p style="font-size:.84rem;color:#aaa;">Total: {len(pendientes)} · '
                f'<span style="color:#1ed760;">ASIGNADOS: {asignados_n}</span> · '
                f'PENDIENTES: {len(pendientes)-asignados_n}</p>',
                unsafe_allow_html=True,
            )

            opciones_man = []
            for it in pendientes:
                p1, p2 = it["pag1"] + 1, it["pag2"] + 1
                run_ocr = it.get("run_ocr", "") or "NO RUN"
                doc_ocr = it.get("doc_ocr", "") or "NO DOC"
                estado  = "✅ ASIGNADO" if (it.get("run_manual") and it.get("doc_manual")) else "⏳ PENDIENTE"
                opciones_man.append(f"Pág {p1}-{p2} | {estado} | OCR_RUN={run_ocr} | OCR_DOC={doc_ocr}")

            sel_idx_man = st.selectbox(
                "Selecciona boleta a gestionar:",
                options=list(range(len(pendientes))),
                format_func=lambda i: opciones_man[i],
                key="hon_man_sel_box",
            )
            st.session_state["hon_man_sel_idx"] = sel_idx_man
            item_sel = pendientes[sel_idx_man]

            # Pre-poblar formulario cuando cambia la selección
            if st.session_state.get("hon_man_prev_idx") != sel_idx_man:
                st.session_state["hon_man_run_input"] = item_sel.get("run_manual") or item_sel.get("run_ocr") or ""
                st.session_state["hon_man_doc_input"] = item_sel.get("doc_manual") or item_sel.get("doc_ocr") or ""
                st.session_state["hon_man_prev_idx"] = sel_idx_man

            col_man_prev, col_man_form = st.columns([1, 1])

            # Preview
            with col_man_prev:
                if pdf_bytes_man:
                    cache = st.session_state["hon_preview_cache"]
                    p1_idx = item_sel["pag1"]
                    if p1_idx not in cache:
                        with st.spinner("Renderizando página..."):
                            cache[p1_idx] = _render_pagina(pdf_bytes_man, p1_idx, resolution=160)
                    if cache.get(p1_idx):
                        st.image(cache[p1_idx], caption=f"Pág {p1_idx+1}", use_container_width=True)
                    else:
                        st.warning("No se pudo renderizar la página.")
                else:
                    st.info("Carga el PDF en la sección 02 para ver la vista previa.")

            # Formulario asignación
            with col_man_form:
                st.markdown(f"""
**Motivo OCR:** <span style="color:#fbbf24;font-size:.78rem;">{item_sel.get('motivo','')}</span>
""", unsafe_allow_html=True)

                run_man_val = st.text_input("RUN (sin DV):", key="hon_man_run_input")
                doc_man_val = st.text_input("N°Documento (boleta):", key="hon_man_doc_input")

                # Sugerencias desde mapping
                sugerencias_man = []
                if mapping_man and run_man_val:
                    run_norm_man = _norm_run_ocr(run_man_val.strip())
                    sugerencias_man = _docs_disp(mapping_man, run_norm_man)

                if sugerencias_man:
                    sug_man = st.selectbox(
                        "Sugerencias N°Doc disponibles en Excel:",
                        options=[""] + sugerencias_man,
                        key="hon_man_sug",
                    )
                    if sug_man:
                        doc_man_val = sug_man

                col_btn_man1, col_btn_man2 = st.columns(2)
                with col_btn_man1:
                    if st.button("💾 Asignar este", use_container_width=True, key="hon_man_asignar"):
                        run_n = _norm_run_ocr(run_man_val.strip())
                        doc_n = _norm_nro_doc(doc_man_val.strip())
                        if run_n and doc_n:
                            item_sel["run_manual"] = run_n
                            item_sel["doc_manual"] = doc_n
                            st.session_state["hon_man_pendientes"][sel_idx_man] = item_sel
                            st.success(f"Asignado: RUN={run_n} | N°Doc={doc_n}")
                            st.rerun()
                        else:
                            st.warning("Completa RUN y N°Documento antes de asignar.")

                with col_btn_man2:
                    if st.button("🗑️ Quitar asignación", use_container_width=True, key="hon_man_quitar"):
                        item_sel.pop("run_manual", None)
                        item_sel.pop("doc_manual", None)
                        st.session_state["hon_man_pendientes"][sel_idx_man] = item_sel
                        st.rerun()

            st.divider()

            # Generar todos los ASIGNADOS
            asignados_list = [p for p in pendientes if p.get("run_manual") and p.get("doc_manual")]
            if st.button(
                f"🚀 Generar ZIP con {len(asignados_list)} ASIGNADOS",
                disabled=not asignados_list or not pdf_bytes_man,
                use_container_width=True,
                key="hon_man_generar",
            ):
                if not mapping_man:
                    st.error("No hay mapping disponible. Asegúrate de haber cargado el Excel.")
                else:
                    try:
                        from pypdf import PdfReader, PdfWriter
                    except ImportError:
                        from PyPDF2 import PdfReader, PdfWriter

                    periodo_man = st.session_state.get("hon_anio", datetime.now().strftime("%Y")) + \
                                  st.session_state.get("hon_mes", datetime.now().strftime("%m")).zfill(2)

                    with st.spinner("Generando PDFs..."):
                        ok_m = 0
                        fallos_m = []
                        reader_m = PdfReader(io.BytesIO(pdf_bytes_man))
                        zip_man_buf = io.BytesIO()
                        generados_idx = []

                        with zipfile.ZipFile(zip_man_buf, "w", zipfile.ZIP_DEFLATED) as zf_m:
                            for idx_m, it in enumerate(asignados_list):
                                run_m = _norm_run_ocr(it["run_manual"].strip())
                                doc_m = _norm_nro_doc(it["doc_manual"].strip())
                                p1_m  = int(it["pag1"])
                                p2_m  = int(it["pag2"])

                                info_m = _consumir(mapping_man, run_m, doc_m)
                                if info_m is None:
                                    docs_av = _docs_disp(mapping_man, run_m)
                                    fallos_m.append(f"Pág {p1_m+1}-{p2_m+1}: sin match RUN={run_m} DOC={doc_m} | Disponibles: {docs_av}")
                                    continue

                                planilla_m = str(info_m["planilla"]).replace(" ", "")
                                etiq_m = f"{periodo_man}_{info_m['run_cuerpo']}_{info_m['nro_doc']}_{planilla_m}.pdf"

                                writer_m = PdfWriter()
                                writer_m.add_page(reader_m.pages[p1_m])
                                writer_m.add_page(reader_m.pages[p2_m])
                                buf_m = io.BytesIO()
                                writer_m.write(buf_m)
                                buf_m.seek(0)
                                zf_m.writestr(etiq_m, buf_m.read())
                                ok_m += 1
                                generados_idx.append(idx_m)

                        zip_man_buf.seek(0)
                        st.session_state["hon_man_zip"] = zip_man_buf.read()
                        st.session_state["hon_mapping"] = mapping_man

                    # Eliminar generados de pendientes
                    items_generados = [asignados_list[i] for i in generados_idx]
                    nuevos_pend = [p for p in pendientes if p not in items_generados]
                    st.session_state["hon_man_pendientes"] = nuevos_pend

                    st.success(f"✅ {ok_m} generados | {len(fallos_m)} fallos · {len(nuevos_pend)} pendientes restantes")
                    if fallos_m:
                        with st.expander(f"⚠️ {len(fallos_m)} fallos", expanded=True):
                            for f_m in fallos_m:
                                st.markdown(f"- {f_m}")
                    st.rerun()

            man_zip_dl = st.session_state.get("hon_man_zip")
            if man_zip_dl:
                st.download_button(
                    label=f"⬇️ Descargar ZIP Manual ({len(man_zip_dl)//1024} KB)",
                    data=man_zip_dl,
                    file_name=f"honorarios_manual_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

    # ══════════════════════════════════════════════════════════════════════════
    # SUB-TAB: BUSCAR POR RUT
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_rut:
        pdf_bytes_rut = st.session_state.get("hon_pdf_bytes")
        mapping_rut   = st.session_state.get("hon_mapping")

        if mapping_rut is None and st.session_state.get("hon_df") is not None:
            mapping_rut = _construir_mapping_run_doc(
                st.session_state["hon_df"], log=lambda _: None
            )
            st.session_state["hon_mapping"] = mapping_rut

        if not pdf_bytes_rut:
            st.info("Carga el PDF en la sección 02 para usar esta función.")
        else:
            # Indexación
            col_rut_idx1, col_rut_idx2 = st.columns([2, 1])
            with col_rut_idx1:
                st.markdown(
                    f'<p style="font-size:.82rem;color:#888;">PDF cargado: <strong style="color:#aaa;">'
                    f'{st.session_state.get("hon_pdf_name","")}</strong> · '
                    f'Índice: {"✅ Listo" if st.session_state.get("hon_rut_indexed") else "⏳ No indexado"}</p>',
                    unsafe_allow_html=True,
                )
            with col_rut_idx2:
                if st.button("🗂️ Indexar PDF (extracción de texto)", use_container_width=True, key="hon_rut_indexar"):
                    with st.spinner("Indexando PDF por RUN (puede tomar unos segundos)..."):
                        try:
                            import pdfplumber
                            idx_map: dict = {}
                            run_cache_idx: dict = {}
                            run_re = re.compile(r"([0-9\.\s]{7,12})\s*-\s*([0-9kK])")

                            def _ext_run_texto(texto):
                                if not texto:
                                    return ""
                                for m in run_re.finditer(texto):
                                    c = re.sub(r"\D", "", m.group(1) or "")
                                    if c != "61608605" and 7 <= len(c) <= 8:
                                        return c
                                return ""

                            with pdfplumber.open(io.BytesIO(pdf_bytes_rut)) as pdf_idx:
                                total_rut = len(pdf_idx.pages)
                                for p1 in range(0, total_rut, 2):
                                    p2 = min(p1 + 1, total_rut - 1)
                                    try:
                                        texto_idx = pdf_idx.pages[p1].extract_text() or ""
                                    except Exception:
                                        texto_idx = ""
                                    run_idx = _norm_run_ocr(_ext_run_texto(texto_idx))
                                    run_cache_idx[p1] = run_idx
                                    if run_idx:
                                        idx_map.setdefault(run_idx, []).append((p1, p2))

                            st.session_state["hon_rut_index"]     = idx_map
                            st.session_state["hon_rut_run_cache"] = run_cache_idx
                            st.session_state["hon_rut_indexed"]   = True
                            st.success(f"✅ Indexados {total_rut} páginas · {len(idx_map)} RUNs encontrados")
                            st.rerun()
                        except Exception as e_idx:
                            st.error(f"Error indexando: {e_idx}")

            st.divider()

            # ── Búsqueda y adición de ítems ──────────────────────────────────
            col_srut1, col_srut2, col_srut3, col_srut4 = st.columns([2, 1, 2, 1])
            with col_srut1:
                rut_buscar = st.text_input("RUT a buscar (sin DV):", key="hon_rut_buscar_inp",
                                           placeholder="Ej: 12345678")
            with col_srut2:
                if st.button("🔍 Buscar", use_container_width=True, key="hon_rut_buscar_btn"):
                    run_b = _norm_run_ocr((rut_buscar or "").strip())
                    if not run_b:
                        st.warning("Ingresa un RUT válido.")
                    else:
                        idx_map_b = st.session_state.get("hon_rut_index", {})
                        pares_b = idx_map_b.get(run_b, [])
                        items_b = [
                            {"run": run_b, "pag1": p1, "pag2": p2, "doc_manual": "", "estado": "PENDIENTE"}
                            for (p1, p2) in pares_b
                        ]
                        if items_b:
                            # Agregar sin duplicar
                            existentes = {(it["pag1"], it["pag2"]) for it in st.session_state["hon_rut_items"]}
                            nuevos = [it for it in items_b if (it["pag1"], it["pag2"]) not in existentes]
                            st.session_state["hon_rut_items"].extend(nuevos)
                            st.session_state["hon_rut_prev_idx"] = -1
                            if not st.session_state.get("hon_rut_indexed"):
                                st.info("El PDF no está indexado — usa 'Indexar PDF' primero.")
                            else:
                                st.success(f"Encontrados {len(pares_b)} pares · {len(nuevos)} nuevos agregados.")
                        else:
                            st.info(f"Sin resultados para RUN={run_b}. Verifica que el PDF esté indexado.")
                        st.rerun()

            with col_srut3:
                pag_agregar = st.text_input("Agregar por N° de página:", key="hon_rut_pag_inp",
                                            placeholder="Ej: 5")
            with col_srut4:
                if st.button("➕ Agregar", use_container_width=True, key="hon_rut_pag_btn"):
                    s_pag = (pag_agregar or "").strip()
                    if not s_pag.isdigit():
                        st.warning("Ingresa un número de página válido.")
                    else:
                        import pdfplumber
                        pag_1b = int(s_pag)
                        try:
                            with pdfplumber.open(io.BytesIO(pdf_bytes_rut)) as _pdf_tmp:
                                total_tmp = len(_pdf_tmp.pages)
                        except Exception:
                            total_tmp = 9999
                        if pag_1b < 1 or pag_1b > total_tmp:
                            st.warning(f"Página fuera de rango (PDF tiene {total_tmp} páginas).")
                        else:
                            z = pag_1b - 1
                            p1_a = z if z % 2 == 0 else z - 1
                            p1_a = max(0, min(p1_a, total_tmp - 1))
                            p2_a = min(p1_a + 1, total_tmp - 1)
                            existentes_a = {(it["pag1"], it["pag2"]) for it in st.session_state["hon_rut_items"]}
                            if (p1_a, p2_a) not in existentes_a:
                                run_det = st.session_state["hon_rut_run_cache"].get(p1_a, "")
                                st.session_state["hon_rut_items"].append({
                                    "run": run_det, "pag1": p1_a, "pag2": p2_a,
                                    "doc_manual": "", "estado": "PENDIENTE",
                                })
                                st.session_state["hon_rut_prev_idx"] = -1
                                st.rerun()
                            else:
                                st.info("Ese par de páginas ya está en la lista.")

            # ── Lista de ítems RUT ────────────────────────────────────────────
            items_rut = st.session_state.get("hon_rut_items", [])

            if not items_rut:
                st.info("Busca por RUT o agrega páginas manualmente para comenzar.")
            else:
                opciones_rut = []
                for it in items_rut:
                    p1r, p2r = it["pag1"] + 1, it["pag2"] + 1
                    run_r    = it.get("run", "") or "?"
                    doc_r    = it.get("doc_manual", "")
                    estado_r = it.get("estado", "PENDIENTE")
                    chip = {"ASIGNADO": "✅", "GENERADO": "🟢", "PENDIENTE": "⏳"}.get(estado_r, "⏳")
                    extra_doc = f" | Doc={doc_r}" if doc_r else ""
                    opciones_rut.append(f"Pág {p1r}-{p2r} | {chip} {estado_r} | RUN={run_r}{extra_doc}")

                sel_rut_idx = st.selectbox(
                    "Selecciona par de páginas:",
                    options=list(range(len(items_rut))),
                    format_func=lambda i: opciones_rut[i],
                    key="hon_rut_sel_box",
                )
                st.session_state["hon_rut_sel_idx"] = sel_rut_idx
                item_rut = items_rut[sel_rut_idx]

                # Pre-poblar formulario al cambiar selección
                if st.session_state.get("hon_rut_prev_idx") != sel_rut_idx:
                    st.session_state["hon_rut_run_input"] = item_rut.get("run", "") or ""
                    st.session_state["hon_rut_doc_input"] = item_rut.get("doc_manual", "") or ""
                    st.session_state["hon_rut_prev_idx"]  = sel_rut_idx

                col_rut_prev, col_rut_form = st.columns([1, 1])

                # Preview
                with col_rut_prev:
                    if pdf_bytes_rut:
                        cache_rut = st.session_state["hon_preview_cache"]
                        p1r_idx   = item_rut["pag1"]
                        if p1r_idx not in cache_rut:
                            with st.spinner("Renderizando..."):
                                cache_rut[p1r_idx] = _render_pagina(pdf_bytes_rut, p1r_idx, resolution=160)
                        if cache_rut.get(p1r_idx):
                            st.image(cache_rut[p1r_idx], caption=f"Pág {p1r_idx+1}", use_container_width=True)
                        else:
                            st.warning("No se pudo renderizar la página.")

                # Formulario
                with col_rut_form:
                    run_rut_val = st.text_input("RUN (sin DV):", key="hon_rut_run_input")
                    doc_rut_val = st.text_input("N°Documento (boleta):", key="hon_rut_doc_input")

                    sugs_rut = []
                    if mapping_rut and run_rut_val:
                        sugs_rut = _docs_disp(mapping_rut, _norm_run_ocr(run_rut_val.strip()))
                    if sugs_rut:
                        sug_rut = st.selectbox("Sugerencias N°Doc:", options=[""] + sugs_rut, key="hon_rut_sug")
                        if sug_rut:
                            doc_rut_val = sug_rut

                    col_rut_btn1, col_rut_btn2 = st.columns(2)
                    with col_rut_btn1:
                        if st.button("💾 Marcar ASIGNADO", use_container_width=True, key="hon_rut_asignar"):
                            run_rn = _norm_run_ocr(run_rut_val.strip())
                            doc_rn = _norm_nro_doc(doc_rut_val.strip())
                            if run_rn and doc_rn:
                                item_rut["run"]        = run_rn
                                item_rut["doc_manual"] = doc_rn
                                item_rut["estado"]     = "ASIGNADO"
                                st.session_state["hon_rut_items"][sel_rut_idx] = item_rut
                                st.success(f"Asignado: RUN={run_rn} | N°Doc={doc_rn}")
                                st.rerun()
                            else:
                                st.warning("Completa RUN y N°Documento.")
                    with col_rut_btn2:
                        if st.button("🗑️ Quitar de lista", use_container_width=True, key="hon_rut_quitar"):
                            st.session_state["hon_rut_items"].pop(sel_rut_idx)
                            st.session_state["hon_rut_prev_idx"] = -1
                            st.rerun()

                    # Generar ESTE
                    if st.button("⚡ Generar ESTE par", use_container_width=True, key="hon_rut_gen_uno"):
                        run_go = _norm_run_ocr(run_rut_val.strip())
                        doc_go = _norm_nro_doc(doc_rut_val.strip())
                        if not run_go or not doc_go:
                            st.warning("Completa RUN y N°Documento antes de generar.")
                        else:
                            try:
                                from pypdf import PdfReader, PdfWriter
                            except ImportError:
                                from PyPDF2 import PdfReader, PdfWriter
                            periodo_rut = st.session_state.get("hon_anio", datetime.now().strftime("%Y")) + \
                                          st.session_state.get("hon_mes", datetime.now().strftime("%m")).zfill(2)
                            info_go = _consumir(mapping_rut, run_go, doc_go) if mapping_rut else None
                            if info_go:
                                planilla_go = str(info_go["planilla"]).replace(" ", "")
                                nombre_go = f"{periodo_rut}_{info_go['run_cuerpo']}_{info_go['nro_doc']}_{planilla_go}.pdf"
                            else:
                                nombre_go = f"{periodo_rut}_{run_go}_{doc_go}_H.pdf"

                            try:
                                reader_go = PdfReader(io.BytesIO(pdf_bytes_rut))
                                writer_go = PdfWriter()
                                writer_go.add_page(reader_go.pages[item_rut["pag1"]])
                                writer_go.add_page(reader_go.pages[item_rut["pag2"]])
                                buf_go = io.BytesIO()
                                writer_go.write(buf_go)
                                buf_go.seek(0)
                                item_rut["estado"] = "GENERADO"
                                st.session_state["hon_rut_items"][sel_rut_idx] = item_rut
                                st.download_button(
                                    label=f"⬇️ {nombre_go}",
                                    data=buf_go.read(),
                                    file_name=nombre_go,
                                    mime="application/pdf",
                                    use_container_width=True,
                                )
                                st.success(f"✅ {nombre_go}")
                            except Exception as e_go:
                                st.error(f"Error generando PDF: {e_go}")

                st.divider()

                # Generar TODOS los ASIGNADOS (RUT)
                asig_rut = [it for it in items_rut if it.get("estado") == "ASIGNADO" and it.get("doc_manual")]
                if st.button(
                    f"🚀 Generar ZIP con {len(asig_rut)} ASIGNADOS",
                    disabled=not asig_rut,
                    use_container_width=True,
                    key="hon_rut_gen_todos",
                ):
                    try:
                        from pypdf import PdfReader, PdfWriter
                    except ImportError:
                        from PyPDF2 import PdfReader, PdfWriter
                    periodo_rut2 = st.session_state.get("hon_anio", datetime.now().strftime("%Y")) + \
                                   st.session_state.get("hon_mes", datetime.now().strftime("%m")).zfill(2)
                    with st.spinner("Generando..."):
                        ok_rut = 0
                        fallos_rut = []
                        reader_rut = PdfReader(io.BytesIO(pdf_bytes_rut))
                        zip_rut_buf = io.BytesIO()
                        with zipfile.ZipFile(zip_rut_buf, "w", zipfile.ZIP_DEFLATED) as zf_rut:
                            for it_r in asig_rut:
                                run_r2 = _norm_run_ocr(it_r["run"].strip())
                                doc_r2 = _norm_nro_doc(it_r["doc_manual"].strip())
                                p1_r2, p2_r2 = int(it_r["pag1"]), int(it_r["pag2"])
                                info_r2 = _consumir(mapping_rut, run_r2, doc_r2) if mapping_rut else None
                                if info_r2:
                                    planilla_r2 = str(info_r2["planilla"]).replace(" ", "")
                                    nombre_r2 = f"{periodo_rut2}_{info_r2['run_cuerpo']}_{info_r2['nro_doc']}_{planilla_r2}.pdf"
                                else:
                                    nombre_r2 = f"{periodo_rut2}_{run_r2}_{doc_r2}_H.pdf"
                                writer_r2 = PdfWriter()
                                writer_r2.add_page(reader_rut.pages[p1_r2])
                                writer_r2.add_page(reader_rut.pages[p2_r2])
                                buf_r2 = io.BytesIO()
                                writer_r2.write(buf_r2)
                                buf_r2.seek(0)
                                zf_rut.writestr(nombre_r2, buf_r2.read())
                                ok_rut += 1
                                it_r["estado"] = "GENERADO"
                        zip_rut_buf.seek(0)
                        st.session_state["hon_rut_zip"] = zip_rut_buf.read()
                    st.success(f"✅ {ok_rut} PDFs generados")
                    st.rerun()

                rut_zip_dl = st.session_state.get("hon_rut_zip")
                if rut_zip_dl:
                    st.download_button(
                        label=f"⬇️ Descargar ZIP RUT ({len(rut_zip_dl)//1024} KB)",
                        data=rut_zip_dl,
                        file_name=f"honorarios_rut_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )

    # ══════════════════════════════════════════════════════════════════════════
    # SUB-TAB: MASIVO (POR UNIDAD)
    # Lógica: Excel Consolidado (col NOMBRE ARCHIVO + CODIGO UNIDAD + Boleta)
    #         + PDFs nombrados por código de unidad (103.pdf, 104.pdf, ...)
    #         + PASMI.pdf para la hoja PASMI
    # Asignación posicional: fila N de la unidad → par de páginas (2N-2, 2N-1)
    # ══════════════════════════════════════════════════════════════════════════
    with subtab_masivo:

        def _nombre_archivo_desde_fila(row) -> str:
            """Obtiene el nombre de archivo desde la columna NOMBRE ARCHIVO.
            Si contiene una fórmula (empieza con '='), lo reconstruye desde las otras columnas."""
            val = str(row.get("NOMBRE ARCHIVO", "") or "").strip()
            if val and not val.startswith("=") and len(val) > 4:
                # ya es un valor calculado
                return val if not val.endswith(".pdf") else val[:-4]
            # Reconstruir: ANO_PAGO + MES_PAGO + "_" + RUT + "_" + Boleta + "_H"
            anio = str(row.get("ANO_PAGO", "") or "").strip()
            mes  = str(row.get("MES_PAGO", "") or "").strip()
            rut  = str(row.get("RUT", "") or "").strip()
            bol  = str(row.get("Boleta", "") or "").strip()
            try:
                mes = str(int(float(mes))).zfill(2)
            except Exception:
                mes = mes.zfill(2) if mes.isdigit() else mes
            rut_clean = re.sub(r"\D", "", rut.split("-")[0] if "-" in rut else rut)
            try:
                bol_clean = str(int(float(bol)))
            except Exception:
                bol_clean = bol
            if anio and mes and rut_clean and bol_clean:
                return f"{anio}{mes}_{rut_clean}_{bol_clean}_H"
            return f"SIN_NOMBRE_fila{row.name if hasattr(row, 'name') else ''}"

        st.markdown(
            '<div style="background:rgba(139,92,246,.05);border:1px solid rgba(139,92,246,.2);'
            'border-radius:10px;padding:.9rem 1.3rem;font-size:.84rem;color:#86a093;margin-bottom:1.2rem;">'
            '📦 <strong style="color:#ccc;">Etiquetado masivo sin OCR:</strong> '
            'Carga el Excel Consolidado + los PDFs de cada unidad (103.pdf, 104.pdf, ..., PASMI.pdf). '
            'El sistema asigna posicionalmente cada fila del Excel a un par de páginas del PDF '
            '(<em>fila 1 → págs 1-2, fila 2 → págs 3-4, ...</em>) y nombra cada PDF con '
            'el valor de la columna <code>NOMBRE ARCHIVO</code>.'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── Paso 1: Excel Consolidado ─────────────────────────────────────────
        st.markdown("""
<div class="ev-section" style="margin-top:.4rem;">
  <span class="ev-section-num">A</span>
  <span class="ev-section-title">Excel Consolidado</span>
  <span class="ev-section-sub">Hojas: CONSOLIDADO y PASMI — columnas: NOMBRE ARCHIVO, CODIGO UNIDAD, Boleta</span>
</div>
""", unsafe_allow_html=True)

        mas_excel_up = st.file_uploader(
            "Sube el Excel Consolidado de Honorarios",
            type=["xlsx", "xls"],
            key="hon_mas_excel_up",
        )

        if mas_excel_up:
            try:
                xls_mas = pd.ExcelFile(mas_excel_up)
                # Leer hoja CONSOLIDADO
                hoja_consol = next(
                    (h for h in xls_mas.sheet_names if "consolidado" in h.lower()),
                    xls_mas.sheet_names[0],
                )
                df_consol = pd.read_excel(xls_mas, sheet_name=hoja_consol, dtype=str)
                df_consol.columns = [str(c).strip() for c in df_consol.columns]
                # Eliminar filas completamente vacías
                df_consol = df_consol.dropna(how="all").reset_index(drop=True)
                st.session_state["hon_mas_df_consol"] = df_consol

                # Leer hoja PASMI si existe
                hoja_pasmi = next(
                    (h for h in xls_mas.sheet_names if "pasmi" in h.lower()), None
                )
                if hoja_pasmi:
                    df_pasmi = pd.read_excel(xls_mas, sheet_name=hoja_pasmi, dtype=str)
                    df_pasmi.columns = [str(c).strip() for c in df_pasmi.columns]
                    df_pasmi = df_pasmi.dropna(how="all").reset_index(drop=True)
                    st.session_state["hon_mas_df_pasmi"] = df_pasmi
                else:
                    st.session_state["hon_mas_df_pasmi"] = None

                # Resumen
                unidades = sorted(df_consol["CODIGO UNIDAD"].dropna().unique().tolist()) \
                    if "CODIGO UNIDAD" in df_consol.columns else []
                n_pasmi = len(st.session_state["hon_mas_df_pasmi"]) if st.session_state["hon_mas_df_pasmi"] is not None else 0

                col_xl1, col_xl2, col_xl3 = st.columns(3)
                col_xl1.metric("Filas CONSOLIDADO", f"{len(df_consol):,}")
                col_xl2.metric("Unidades detectadas", len(unidades))
                col_xl3.metric("Filas PASMI", n_pasmi)

                with st.expander("Vista previa CONSOLIDADO (primeras 10 filas)", expanded=False):
                    cols_mostrar = [c for c in ["NOMBRE", "RUT", "CODIGO UNIDAD", "Boleta", "NOMBRE ARCHIVO"]
                                    if c in df_consol.columns]
                    st.markdown(ev_design.ev_table_html(df_consol[cols_mostrar].head(10)), unsafe_allow_html=True)

                if hoja_pasmi and st.session_state["hon_mas_df_pasmi"] is not None:
                    with st.expander("Vista previa PASMI", expanded=False):
                        cols_p = [c for c in ["NOMBRE", "RUT", "CODIGO UNIDAD", "Boleta", "NOMBRE ARCHIVO"]
                                  if c in st.session_state["hon_mas_df_pasmi"].columns]
                        st.markdown(ev_design.ev_table_html(
                            st.session_state["hon_mas_df_pasmi"][cols_p]), unsafe_allow_html=True)

            except Exception as e_mx:
                st.error(f"Error al leer el Excel: {e_mx}")

        # ── Paso 2: PDFs por unidad ───────────────────────────────────────────
        st.markdown("""
<div class="ev-section" style="margin-top:.8rem;">
  <span class="ev-section-num">B</span>
  <span class="ev-section-title">PDFs por Unidad</span>
  <span class="ev-section-sub">Nombra cada archivo como el código de unidad: 103.pdf, 104.pdf, ... y PASMI.pdf</span>
</div>
""", unsafe_allow_html=True)

        mas_pdfs_up = st.file_uploader(
            "Sube todos los PDFs de unidad (selección múltiple)",
            type=["pdf"],
            accept_multiple_files=True,
            key="hon_mas_pdfs_up",
        )

        if mas_pdfs_up:
            pdfs_dict = {}
            for f_up in mas_pdfs_up:
                # Normaliza el nombre: elimina espacios extra ("103 .pdf" -> "103")
                # y recorta sufijos de fecha en PASMI ("PASMI 10-2025.pdf" -> "PASMI")
                raw_stem = Path(f_up.name).stem.strip().upper()
                if raw_stem.startswith("PASMI"):
                    clave = "PASMI"
                else:
                    clave = raw_stem
                f_up.seek(0)
                pdfs_dict[clave] = f_up.read()
            st.session_state["hon_mas_pdfs"] = pdfs_dict
            st.success(f"✅ {len(pdfs_dict)} PDFs cargados: {', '.join(sorted(pdfs_dict.keys()))}")

        # ── Tabla de estado ───────────────────────────────────────────────────
        df_consol_mas = st.session_state.get("hon_mas_df_consol")
        pdfs_mas      = st.session_state.get("hon_mas_pdfs", {})

        if df_consol_mas is not None and "CODIGO UNIDAD" in df_consol_mas.columns:
            st.markdown("""
<div class="ev-section" style="margin-top:.8rem;">
  <span class="ev-section-num">C</span>
  <span class="ev-section-title">Estado por Unidad</span>
  <span class="ev-section-sub">Verifica que el número de boletas del Excel coincida con los pares de páginas del PDF</span>
</div>
""", unsafe_allow_html=True)

            grupos_mas = df_consol_mas.groupby("CODIGO UNIDAD", sort=False)
            filas_estado = []
            todo_ok = True

            for cod_unidad, grp in grupos_mas:
                cod_str = str(cod_unidad).strip()
                n_boletas = len(grp)
                pdf_key = cod_str.upper()
                pdf_cargado = pdf_key in pdfs_mas
                n_paginas = 0
                n_pares   = 0
                if pdf_cargado:
                    try:
                        from pypdf import PdfReader
                    except ImportError:
                        from PyPDF2 import PdfReader
                    try:
                        n_paginas = len(PdfReader(io.BytesIO(pdfs_mas[pdf_key])).pages)
                        n_pares   = n_paginas // 2
                    except Exception:
                        n_paginas = -1
                        n_pares   = -1

                coincide = (n_boletas == n_pares) if pdf_cargado and n_pares >= 0 else None
                if coincide is False:
                    todo_ok = False

                filas_estado.append({
                    "Unidad": cod_str,
                    "Boletas Excel": n_boletas,
                    "PDF cargado": "✅" if pdf_cargado else "❌ falta",
                    "Páginas PDF": n_paginas if pdf_cargado else "—",
                    "Pares PDF": n_pares if pdf_cargado else "—",
                    "Estado": ("✅ OK" if coincide else ("⚠️ No coincide" if coincide is False else "⏳ Sin PDF")),
                })

            # También PASMI
            df_pasmi_mas = st.session_state.get("hon_mas_df_pasmi")
            if df_pasmi_mas is not None and len(df_pasmi_mas) > 0:
                n_pasmi_b = len(df_pasmi_mas)
                pasmi_cargado = "PASMI" in pdfs_mas
                n_pag_pasmi = 0
                n_par_pasmi = 0
                if pasmi_cargado:
                    try:
                        n_pag_pasmi = len(PdfReader(io.BytesIO(pdfs_mas["PASMI"])).pages)
                        n_par_pasmi = n_pag_pasmi // 2
                    except Exception:
                        pass
                coincide_p = (n_pasmi_b == n_par_pasmi) if pasmi_cargado else None
                if coincide_p is False:
                    todo_ok = False
                filas_estado.append({
                    "Unidad": "PASMI",
                    "Boletas Excel": n_pasmi_b,
                    "PDF cargado": "✅" if pasmi_cargado else "❌ falta",
                    "Páginas PDF": n_pag_pasmi if pasmi_cargado else "—",
                    "Pares PDF": n_par_pasmi if pasmi_cargado else "—",
                    "Estado": ("✅ OK" if coincide_p else ("⚠️ No coincide" if coincide_p is False else "⏳ Sin PDF")),
                })

            df_estado = pd.DataFrame(filas_estado)
            st.markdown(ev_design.ev_table_html(df_estado), unsafe_allow_html=True)

            if not todo_ok:
                st.warning("⚠️ Algunas unidades tienen discrepancias entre boletas Excel y pares de páginas PDF. "
                           "Verifica que el PDF correcto fue cargado para cada unidad.")

            # ── Proceso ───────────────────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)

            col_mas_b1, col_mas_b2 = st.columns([2, 1])
            with col_mas_b1:
                ignorar_discrepancias = st.toggle(
                    "Procesar igualmente aunque haya discrepancias (asigna hasta las páginas disponibles)",
                    value=False,
                    key="hon_mas_ignorar",
                )
            with col_mas_b2:
                carpeta_zip = st.text_input(
                    "Carpeta interna del ZIP",
                    value="",
                    placeholder="Vacío = un ZIP plano",
                    key="hon_mas_carpeta",
                    help="Si rellenas este campo, los PDFs se organizan en subcarpetas por unidad dentro del ZIP",
                )

            pdfs_disponibles = [u for u in [str(g) for g in df_consol_mas["CODIGO UNIDAD"].dropna().unique()]
                                 if str(u).upper() in pdfs_mas]
            if df_pasmi_mas is not None and len(df_pasmi_mas) > 0 and "PASMI" in pdfs_mas:
                pdfs_disponibles.append("PASMI")

            puede_procesar = len(pdfs_disponibles) > 0

            if st.button(
                f"🚀 Procesar TODO ({len(pdfs_disponibles)} unidades con PDF)",
                disabled=not puede_procesar,
                use_container_width=True,
                key="hon_mas_procesar",
            ):
                try:
                    from pypdf import PdfReader, PdfWriter
                except ImportError:
                    from PyPDF2 import PdfReader, PdfWriter

                log_mas  = []
                resumen_mas = []
                errores_mas = []
                ok_total    = 0

                zip_mas_buf = io.BytesIO()

                # ── Indicador de progreso masivo ─────────────────────────────
                _total_u = len(pdfs_disponibles)
                _pbar_mas = st.progress(0, text=f"Iniciando procesamiento  ·  0 / {_total_u} unidades")
                _stat_mas = st.empty()
                _mc1, _mc2, _mc3 = st.columns(3)
                _m_etiq = _mc1.empty(); _m_err = _mc2.empty(); _m_cur = _mc3.empty()
                _m_etiq.metric("Etiquetas generadas", 0)
                _m_err.metric("Con discrepancia", 0)
                _m_cur.metric("Unidad en proceso", "—")
                _u_proc = 0

                with zipfile.ZipFile(zip_mas_buf, "w", zipfile.ZIP_DEFLATED) as zf_mas:

                        # ── Procesar CONSOLIDADO ──────────────────────────────
                        for cod_unidad_g, grp_g in df_consol_mas.groupby("CODIGO UNIDAD", sort=False):
                            cod_str_g = str(cod_unidad_g).strip()
                            pdf_key_g = cod_str_g.upper()
                            _u_proc += 1
                            _m_cur.metric("Unidad en proceso", cod_str_g)
                            _stat_mas.info(f"⚙️ Procesando unidad **{cod_str_g}** — {_u_proc}/{_total_u}")
                            _pbar_mas.progress(_u_proc / _total_u,
                                               text=f"Unidad {cod_str_g}  ·  {_u_proc} / {_total_u}")

                            if pdf_key_g not in pdfs_mas:
                                log_mas.append(f"⚠️ Unidad {cod_str_g}: sin PDF cargado, saltada.")
                                continue

                            try:
                                reader_g = PdfReader(io.BytesIO(pdfs_mas[pdf_key_g]))
                                total_pags_g = len(reader_g.pages)
                            except Exception as e_r:
                                log_mas.append(f"❌ Unidad {cod_str_g}: error abriendo PDF: {e_r}")
                                continue

                            rows_g = grp_g.reset_index(drop=True)
                            n_filas_g = len(rows_g)
                            n_pares_g = total_pags_g // 2

                            if n_filas_g != n_pares_g and not ignorar_discrepancias:
                                log_mas.append(f"⚠️ Unidad {cod_str_g}: {n_filas_g} filas vs {n_pares_g} pares "
                                               f"— saltada (activa 'Procesar igualmente' para forzar).")
                                errores_mas.append({
                                    "Unidad": cod_str_g,
                                    "Motivo": f"{n_filas_g} filas ≠ {n_pares_g} pares en PDF",
                                })
                                continue

                            limite_g = min(n_filas_g, n_pares_g)
                            ok_unidad = 0

                            for i_row in range(limite_g):
                                row_g  = rows_g.iloc[i_row]
                                p1_g   = 2 * i_row
                                p2_g   = 2 * i_row + 1
                                nombre = _nombre_archivo_desde_fila(row_g)
                                nombre_pdf = f"{nombre}.pdf"

                                zip_ruta = (
                                    f"{carpeta_zip}/{cod_str_g}/{nombre_pdf}"
                                    if carpeta_zip.strip()
                                    else (f"{cod_str_g}/{nombre_pdf}")
                                )

                                try:
                                    writer_g = PdfWriter()
                                    writer_g.add_page(reader_g.pages[p1_g])
                                    writer_g.add_page(reader_g.pages[p2_g])
                                    buf_g = io.BytesIO()
                                    writer_g.write(buf_g)
                                    buf_g.seek(0)
                                    zf_mas.writestr(zip_ruta, buf_g.read())
                                    ok_unidad += 1
                                    ok_total  += 1
                                    resumen_mas.append({
                                        "Unidad": cod_str_g,
                                        "Fila Excel": i_row + 1,
                                        "Págs PDF": f"{p1_g+1}-{p2_g+1}",
                                        "Nombre archivo": nombre_pdf,
                                        "Nombre": str(row_g.get("NOMBRE", "")),
                                        "Boleta": str(row_g.get("Boleta", "")),
                                    })
                                except Exception as e_pg:
                                    log_mas.append(f"  ❌ {cod_str_g} fila {i_row+1}: {e_pg}")
                                    errores_mas.append({"Unidad": cod_str_g, "Fila": i_row+1, "Motivo": str(e_pg)})

                            log_mas.append(f"✅ Unidad {cod_str_g}: {ok_unidad}/{limite_g} PDFs generados")
                            _m_etiq.metric("Etiquetas generadas", ok_total)
                            _m_err.metric("Con discrepancia", len(errores_mas))

                        # ── Procesar PASMI ─────────────────────────────────────
                        if df_pasmi_mas is not None and len(df_pasmi_mas) > 0:
                            _u_proc += 1
                            _m_cur.metric("Unidad en proceso", "PASMI")
                            _stat_mas.info(f"⚙️ Procesando PASMI  —  {_u_proc}/{_total_u}")
                            _pbar_mas.progress(_u_proc / _total_u, text=f"PASMI  ·  {_u_proc} / {_total_u}")
                            if "PASMI" not in pdfs_mas:
                                log_mas.append("⚠️ PASMI: sin PDF cargado, saltado.")
                            else:
                                try:
                                    reader_p = PdfReader(io.BytesIO(pdfs_mas["PASMI"]))
                                    total_pags_p = len(reader_p.pages)
                                    n_pares_p = total_pags_p // 2
                                    rows_p    = df_pasmi_mas.reset_index(drop=True)
                                    n_filas_p = len(rows_p)
                                    limite_p  = min(n_filas_p, n_pares_p)

                                    if n_filas_p != n_pares_p and not ignorar_discrepancias:
                                        log_mas.append(f"⚠️ PASMI: {n_filas_p} filas vs {n_pares_p} pares — saltado.")
                                    else:
                                        ok_pasmi = 0
                                        for i_p in range(limite_p):
                                            row_p   = rows_p.iloc[i_p]
                                            nombre_p = _nombre_archivo_desde_fila(row_p)
                                            nombre_pdf_p = f"{nombre_p}.pdf"
                                            zip_ruta_p = (
                                                f"{carpeta_zip}/PASMI/{nombre_pdf_p}"
                                                if carpeta_zip.strip()
                                                else f"PASMI/{nombre_pdf_p}"
                                            )
                                            writer_p = PdfWriter()
                                            writer_p.add_page(reader_p.pages[2 * i_p])
                                            writer_p.add_page(reader_p.pages[2 * i_p + 1])
                                            buf_p = io.BytesIO()
                                            writer_p.write(buf_p)
                                            buf_p.seek(0)
                                            zf_mas.writestr(zip_ruta_p, buf_p.read())
                                            ok_pasmi += 1
                                            ok_total += 1
                                            resumen_mas.append({
                                                "Unidad": "PASMI",
                                                "Fila Excel": i_p + 1,
                                                "Págs PDF": f"{2*i_p+1}-{2*i_p+2}",
                                                "Nombre archivo": nombre_pdf_p,
                                                "Nombre": str(row_p.get("NOMBRE", "")),
                                                "Boleta": str(row_p.get("Boleta", "")),
                                            })
                                        log_mas.append(f"✅ PASMI: {ok_pasmi}/{limite_p} PDFs generados")
                                except Exception as e_p:
                                    log_mas.append(f"❌ PASMI error: {e_p}")

                zip_mas_buf.seek(0)
                st.session_state["hon_mas_zip"]    = zip_mas_buf.read()
                st.session_state["hon_mas_log"]    = log_mas
                st.session_state["hon_mas_resumen"] = resumen_mas
                _pbar_mas.progress(1.0, text=f"✅ {ok_total} etiquetas generadas en {_u_proc} unidades")
                _stat_mas.success(f"✅ Proceso finalizado — **{ok_total} etiquetas** creadas")
                _m_cur.metric("Unidad en proceso", "✅ Listo")
                _m_etiq.metric("Etiquetas generadas", ok_total)
                _m_err.metric("Con discrepancia", len(errores_mas))

                st.rerun()

            # ── Resultados Masivo ─────────────────────────────────────────────
            log_mas_ses    = st.session_state.get("hon_mas_log", [])
            resumen_mas_ses = st.session_state.get("hon_mas_resumen")
            zip_mas_ses    = st.session_state.get("hon_mas_zip")

            if log_mas_ses:
                log_mas_html = ""
                for line in log_mas_ses:
                    if "❌" in line:
                        css = "color:#f87171;"
                    elif "✅" in line:
                        css = "color:#1ed760;"
                    elif "⚠️" in line:
                        css = "color:#fbbf24;"
                    else:
                        css = "color:#b3b3b3;"
                    escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    log_mas_html += f'<span style="{css}">{escaped}</span>\n'
                st.markdown(f'<div class="log-box">{log_mas_html}</div>', unsafe_allow_html=True)

            if zip_mas_ses:
                ts_mas = datetime.now().strftime("%Y%m%d_%H%M")
                st.download_button(
                    label=f"⬇️ Descargar ZIP Masivo — {len(resumen_mas_ses or [])} PDFs · {len(zip_mas_ses)//1024:,} KB",
                    data=zip_mas_ses,
                    file_name=f"honorarios_masivo_{ts_mas}.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

            if resumen_mas_ses:
                with st.expander(f"📋 Resumen detallado ({len(resumen_mas_ses)} archivos generados)", expanded=False):
                    df_res_mas = pd.DataFrame(resumen_mas_ses)
                    st.markdown(ev_design.ev_table_html(df_res_mas), unsafe_allow_html=True)
                    buf_res_mas = io.BytesIO()
                    df_res_mas.to_excel(buf_res_mas, index=False, engine="openpyxl")
                    buf_res_mas.seek(0)
                    st.download_button(
                        label="⬇️ Descargar resumen Excel",
                        data=buf_res_mas,
                        file_name=f"resumen_masivo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

        elif df_consol_mas is None:
            st.info("Carga el Excel Consolidado en el paso A para comenzar.")


st.markdown('</div>', unsafe_allow_html=True)

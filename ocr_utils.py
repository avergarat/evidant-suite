# ocr_utils.py
# -*- coding: utf-8 -*-

import re
import os
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import pytesseract
import os


# >>> AJUSTA ESTA RUTA A TU REALIDAD
TESSERACT_EXE = r"C:\Users\DAP\tesseract.exe"



if os.path.exists(TESSERACT_EXE):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_EXE


from pytesseract import Output
from typing import Optional


import os
import shutil
from pathlib import Path

def _configurar_tesseract() -> str:
    """
    Configura pytesseract.pytesseract.tesseract_cmd usando:
    1) Variable de entorno EVIDANT_TESSERACT o TESSERACT_CMD
    2) PATH (shutil.which)
    3) Rutas típicas de Windows
    Retorna la ruta usada o "" si no se encontró.
    """
    candidatos = []

    # 1) Env vars (lo más seguro para TI)
    env1 = os.environ.get("EVIDANT_TESSERACT", "").strip()
    env2 = os.environ.get("TESSERACT_CMD", "").strip()
    if env1:
        candidatos.append(env1)
    if env2:
        candidatos.append(env2)

    # 2) PATH
    which = shutil.which("tesseract")
    if which:
        candidatos.append(which)

    # 3) Rutas típicas
    candidatos += [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\DAP\tesseract.exe",  # dejo tu intento anterior como fallback
    ]

    for c in candidatos:
        try:
            if c and Path(c).exists():
                pytesseract.pytesseract.tesseract_cmd = c
                return c
        except Exception:
            continue

    return ""

TESSERACT_USADO = _configurar_tesseract()

def asegurar_tesseract():
    """
    Llamar antes de hacer OCR. Si no está, levanta error con instrucciones claras.
    """
    if not TESSERACT_USADO:
        raise RuntimeError(
            "Tesseract no está configurado.\n\n"
            "Solución rápida:\n"
            "1) Instala Tesseract-OCR, o\n"
            "2) Define la variable de entorno EVIDANT_TESSERACT apuntando a tesseract.exe\n"
            "   Ejemplo: C:\\Program Files\\Tesseract-OCR\\tesseract.exe\n"
        )


# ----------------- OCR helpers ----------------- #

def preprocesar_imagen_ocr_suave(img: Image.Image) -> Image.Image:
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = ImageOps.grayscale(img)
    img = ImageEnhance.Contrast(img).enhance(1.6)
    img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
    return img

def prepro_cuadro_boleta(im: Image.Image) -> Image.Image:
    im = im.convert("RGB")
    im = ImageOps.grayscale(im)
    im = ImageEnhance.Contrast(im).enhance(1.8)
    im = im.filter(ImageFilter.UnsharpMask(radius=1, percent=140, threshold=3))
    return im

def prepro_nro_doc(im: Image.Image) -> Image.Image:
    im = im.convert("RGB")
    im = ImageOps.grayscale(im)
    im = ImageEnhance.Contrast(im).enhance(2.2)
    im = ImageEnhance.Sharpness(im).enhance(2.0)
    thr = 200
    im = im.point(lambda p: 255 if p > thr else 0)
    im = im.filter(ImageFilter.MedianFilter(size=3))
    return im

def ocr_roi(img: Image.Image, box, lang="spa", preprocess=None, config=""):
    roi = img.crop(box)
    if preprocess:
        roi = preprocess(roi)
    return pytesseract.image_to_string(roi, lang=lang, config=config)

# ----------------- Normalización ----------------- #

def normalizar_run(run_raw: str) -> str:
    if run_raw is None:
        return ""
    digits = re.sub(r"\D", "", str(run_raw))
    if len(digits) > 8:
        return digits[:-1]
    return digits

def normalizar_nro_doc(valor) -> str:
    if valor is None:
        return ""
    s = str(valor).strip()
    digs = re.sub(r"\D", "", s)
    if not digs:
        return ""
    try:
        return str(int(digs))
    except Exception:
        return digs.lstrip("0") or digs

# ----------------- RUN EMISOR (NO TOCAR: vuelve al que funcionaba) ----------------- #

def extraer_run_emisor_desde_texto_v2(texto: str) -> str:
    if not texto:
        return ""

    lineas = [ln.strip() for ln in texto.splitlines() if ln.strip()]
    for ln in lineas:
        if "rut" not in ln.lower():
            continue
        m = re.search(r"([0-9\.\s]{7,12})\s*-\s*([0-9kK])", ln)
        if not m:
            continue
        cuerpo = re.sub(r"\D", "", m.group(1))
        if cuerpo == "61608605":
            continue
        if 7 <= len(cuerpo) <= 8:
            return cuerpo

    matches = re.finditer(r"([0-9\.\s]{7,12})\s*-\s*([0-9kK])", texto)
    for m in matches:
        cuerpo = re.sub(r"\D", "", m.group(1))
        if cuerpo == "61608605":
            continue
        if 7 <= len(cuerpo) <= 8:
            return cuerpo

    return ""

# ----------------- NRO DOC ANCLADO (BOLETA/ELECTRONICA) + fallback ROI fijo ----------------- #

DOC_ROI_FRAC_FALLBACK = (0.62, 0.10, 0.95, 0.29)

def _extraer_nro_doc_desde_texto(txt: str) -> str:
    t = (txt or "").upper().replace(" ", "").replace("\n", "")
    m = re.search(r"N[O°º]?\D*0*(\d{1,8})", t)
    if m:
        return m.group(1)
    m2 = re.search(r"(\d{1,8})", t)
    return (m2.group(1) if m2 else "")

def encontrar_roi_doc_por_ancla(img: Image.Image):
    img = img.convert("RGB")
    w, h = img.size

    box_cuadro = (int(0.55*w), int(0.06*h), int(0.97*w), int(0.34*h))
    roi = img.crop(box_cuadro)
    roi_pp = prepro_cuadro_boleta(roi)

    cfg = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(roi_pp, lang="spa", config=cfg, output_type=Output.DICT)

    best = None  # (score, x,y,w,h, token, kind)
    for i, t in enumerate(data["text"]):
        t0 = (t or "").strip().upper()
        if not t0:
            continue
        t1 = re.sub(r"[^A-Z0-9]", "", t0)

        kind = None
        if ("BOLETA" in t1) or (t1 in ("B0LETA", "BOIETA", "BOLE7A", "B0IETA")):
            kind = "BOLETA"
        elif ("ELECTRONICA" in t1) or ("ELECTRONICA" in t1.replace("0", "O")):
            kind = "ELECTRONICA"

        if kind:
            x = data["left"][i]; y = data["top"][i]
            ww = data["width"][i]; hh = data["height"][i]
            conf = data["conf"][i]
            try:
                conf = float(conf)
            except Exception:
                conf = 0.0
            score = conf + ww
            if best is None or score > best[0]:
                best = (score, x, y, ww, hh, t0, kind)

    if best is None:
        return None, "ANCLA=NO (sin BOLETA/ELECTRONICA)"

    score, x, y, ww, hh, token, kind = best

    nro_left  = max(0, x - int(0.10 * ww))
    nro_top   = y + int(1.1 * hh)
    nro_right = min(roi.size[0], x + int(2.6 * ww))
    nro_bot   = min(roi.size[1], y + int(4.0 * hh))

    box_abs = (
        box_cuadro[0] + nro_left,
        box_cuadro[1] + nro_top,
        box_cuadro[0] + nro_right,
        box_cuadro[1] + nro_bot,
    )
    return box_abs, f"ANCLA=OK kind={kind} token='{token}' score={score:.1f}"

def extraer_nro_doc_anclado(img: Image.Image):
    # 1) ancla
    box_doc, dbg = encontrar_roi_doc_por_ancla(img)
    if box_doc is not None:
        cfg = r'--oem 3 --psm 7 -c tessedit_char_whitelist=NO°º0123456789'
        raw = ocr_roi(img, box_doc, preprocess=prepro_nro_doc, config=cfg)
        nro = _extraer_nro_doc_desde_texto(raw)
        if nro:
            return normalizar_nro_doc(nro), f"{dbg} OCR='{(raw or '').strip()[:80]}'"

    # 2) fallback ROI fijo
    w, h = img.size
    l,t,r,b = DOC_ROI_FRAC_FALLBACK
    box = (int(l*w), int(t*h), int(r*w), int(b*h))
    cfg = r'--oem 3 --psm 6 -c tessedit_char_whitelist=NO°º0123456789'
    raw = ocr_roi(img, box, preprocess=prepro_nro_doc, config=cfg)
    nro = _extraer_nro_doc_desde_texto(raw)
    if nro:
        return normalizar_nro_doc(nro), f"FALLBACK_ROI_FIJO OK OCR='{(raw or '').strip()[:80]}'"

    return "", f"{dbg} + FALLBACK_ROI_FIJO=NO"


# ----------------- Tesseract config (Windows-friendly) ----------------- #

def configurar_tesseract(ruta_exe: str) -> bool:
    """Configura pytesseract para usar un ejecutable específico. Devuelve True si existe."""
    try:
        if ruta_exe and isinstance(ruta_exe, str) and ruta_exe.strip():
            ruta_exe = ruta_exe.strip().strip('"')
            if os.path.exists(ruta_exe):
                pytesseract.pytesseract.tesseract_cmd = ruta_exe
                return True
    except Exception:
        pass
    return False


def asegurar_tesseract(ruta_preferida: Optional[str] = None) -> None:
    """Intenta asegurar que Tesseract está disponible."""
    if ruta_preferida and configurar_tesseract(ruta_preferida):
        return

    env = os.environ.get("TESSERACT_EXE") or os.environ.get("TESSERACT_PATH")
    if env and configurar_tesseract(env):
        return

    for c in [
        r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
    ]:
        if configurar_tesseract(c):
            return

    try:
        _ = pytesseract.get_tesseract_version()
        return
    except Exception as e:
        raise RuntimeError(
            "tesseract no está instalado o no está en PATH. "
            "Instálalo o configura la ruta en TESSERACT_EXE (env) o en la app."
        ) from e

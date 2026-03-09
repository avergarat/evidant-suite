# pdf_utils.py — versión Streamlit (sin ImageTk)
# -*- coding: utf-8 -*-

import os
import time
import shutil
import tempfile
from functools import lru_cache
from typing import Optional, List

import pdfplumber
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image


def guardar_pdf_paginas(ruta_pdf: str, indices_paginas: List[int], ruta_salida: str) -> str:
    """Guarda un nuevo PDF con las páginas indicadas (0-based)."""
    reader = PdfReader(ruta_pdf)
    writer = PdfWriter()
    for idx in indices_paginas:
        writer.add_page(reader.pages[idx])

    os.makedirs(os.path.dirname(ruta_salida) or ".", exist_ok=True)

    base, ext = os.path.splitext(ruta_salida)
    out = ruta_salida
    c = 1
    while os.path.exists(out):
        out = f"{base}_{c}{ext}"
        c += 1

    with open(out, "wb") as f:
        writer.write(f)
    return out


def _es_failed_to_load_page(e: Exception) -> bool:
    msg = str(e).lower()
    return ("failed to load page" in msg) or ("cannot load page" in msg) or ("load page" in msg)


def _copia_trabajo_pdf(ruta_pdf: str) -> str:
    """Crea una copia temporal del PDF para evitar locks de Adobe/Explorer."""
    if not os.path.exists(ruta_pdf):
        raise FileNotFoundError(ruta_pdf)

    tmp_dir = os.path.join(tempfile.gettempdir(), "evidant_pdf_work")
    os.makedirs(tmp_dir, exist_ok=True)

    base = os.path.splitext(os.path.basename(ruta_pdf))[0]
    dst = os.path.join(tmp_dir, f"{base}__workcopy.pdf")

    last_err = None
    for _ in range(6):
        try:
            shutil.copy2(ruta_pdf, dst)
            return dst
        except Exception as e:
            last_err = e
            time.sleep(0.25)

    raise RuntimeError(
        "No se pudo crear copia de trabajo del PDF (posible bloqueo por Adobe/Explorer). "
        "Cierra Adobe Reader y desactiva vista previa del Explorador."
    ) from last_err


@lru_cache(maxsize=64)
def _render_pil_cached(ruta_pdf: str, page_index: int, resolution: int) -> Image.Image:
    """Render robusto con anti-lock Adobe."""
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            page = pdf.pages[page_index]
            im = page.to_image(resolution=resolution).original.convert("RGB")
        return im
    except Exception as e:
        if not _es_failed_to_load_page(e):
            raise
        ruta_copia = _copia_trabajo_pdf(ruta_pdf)
        with pdfplumber.open(ruta_copia) as pdf:
            page = pdf.pages[page_index]
            im = page.to_image(resolution=resolution).original.convert("RGB")
        return im


def renderizar_pagina_a_pil(
    ruta_pdf: str,
    page_index: int,
    resolution: int = 150,
    max_w: Optional[int] = None,
) -> Image.Image:
    """Renderiza una página a PIL.Image (RGB)."""
    im = _render_pil_cached(ruta_pdf, page_index, resolution).copy()
    if max_w is not None:
        w, h = im.size
        if w > max_w:
            scale = max_w / float(w)
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return im


def renderizar_pagina_desde_bytes(
    pdf_bytes: bytes,
    page_index: int,
    resolution: int = 150,
    max_w: Optional[int] = None,
) -> Image.Image:
    """Renderiza una página desde bytes (para Streamlit file_uploader)."""
    import io
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        if page_index >= len(pdf.pages):
            page_index = len(pdf.pages) - 1
        page = pdf.pages[page_index]
        im = page.to_image(resolution=resolution).original.convert("RGB")
    if max_w is not None:
        w, h = im.size
        if w > max_w:
            scale = max_w / float(w)
            im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return im


def num_paginas_desde_bytes(pdf_bytes: bytes) -> int:
    """Retorna el número de páginas de un PDF en bytes."""
    import io
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return len(pdf.pages)

# -*- coding: utf-8 -*-
# evidant Suite — pages/7_Liquidaciones_Accesorias.py
# Módulo: Descarga automática de Liquidaciones Accesorias desde SIRH
# Interfaz Streamlit que controla el script de automatización pywinauto
import streamlit as st
import sys
import os
import queue
import threading
import tempfile
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ev_design

st.set_page_config(
    page_title="Liq. Accesorias · Evidant Suite",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ev_design.render(
    current="liquidaciones",
    page_title="Liquidaciones Accesorias",
    page_sub="Descarga automática desde SIRH · Procesamiento por lote de folios",
    breadcrumb="Imágenes",
    icon="📋",
)

# ══════════════════════════════════════════════════════════════════════════════
# Localizar el script de automatización
# ══════════════════════════════════════════════════════════════════════════════
_SCRIPT_CANDIDATES = [
    Path(__file__).parents[3] / "APP FINALES" / "DESCARGA LIQUIDACIONES ACCESORIAS FINAL V2.PY",
    Path(r"C:\Users\DAP\OneDrive - SUBSECRETARIA DE SALUD PUBLICA\Escritorio 2024\GESTION\APP FINALES\DESCARGA LIQUIDACIONES ACCESORIAS FINAL V2.PY"),
]

_SCRIPT_PATH: Path | None = None
for _c in _SCRIPT_CANDIDATES:
    if _c.exists():
        _SCRIPT_PATH = _c
        break

# ── Importar el módulo de automatización (sin ejecutar su GUI Tkinter) ──────
_auto_mod   = None
_import_err = ""

if _SCRIPT_PATH:
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "liq_accesorias_auto", str(_SCRIPT_PATH)
        )
        _auto_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_auto_mod)  # type: ignore
    except Exception as _e:
        _import_err = str(_e)

# ══════════════════════════════════════════════════════════════════════════════
# Estado de sesión
# ══════════════════════════════════════════════════════════════════════════════
def _init_state():
    defaults = {
        "liq_log":          [],          # lista de strings de log
        "liq_running":      False,
        "liq_thread":       None,
        "liq_queue":        None,
        "liq_folios_df":    None,        # DataFrame con folios cargados
        "liq_excel_path":   "",          # ruta del Excel temporal
        "liq_periodo":      "",
        "liq_carpeta":      "",
        "liq_folio_inicio": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ══════════════════════════════════════════════════════════════════════════════
# CSS adicional
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
.log-box {
  background: #0d0d0d;
  border: 1px solid rgba(255,255,255,.07);
  border-radius: 10px;
  padding: 1rem 1.2rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: .72rem;
  color: #b3b3b3;
  max-height: 380px;
  overflow-y: auto;
  line-height: 1.7;
  white-space: pre-wrap;
}
.log-ok   { color: #1ed760; }
.log-err  { color: #f87171; }
.log-warn { color: #fbbf24; }
.log-info { color: #60a5fa; }
.status-running {
  display:inline-flex;align-items:center;gap:.5rem;
  background:rgba(29,185,84,.1);border:1px solid rgba(29,185,84,.25);
  border-radius:20px;padding:.4rem 1rem;font-size:.8rem;color:#1ed760;
}
.status-idle {
  display:inline-flex;align-items:center;gap:.5rem;
  background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.08);
  border-radius:20px;padding:.4rem 1rem;font-size:.8rem;color:#535353;
}
</style>
""", unsafe_allow_html=True)

# ── Banner estado módulo ───────────────────────────────────────────────────
st.markdown('<div class="ev-content ev-anim">', unsafe_allow_html=True)

if _auto_mod and not _import_err:
    st.markdown(
        '<div style="background:rgba(29,185,84,.06);border:1px solid rgba(29,185,84,.2);'
        'border-radius:10px;padding:.7rem 1.2rem;font-size:.83rem;color:#86a093;margin-bottom:1rem;">'
        '✅ <strong style="color:#1ed760;">Módulo de automatización</strong> cargado · '
        f'Script: <code style="font-size:.75rem;">{_SCRIPT_PATH.name}</code>'
        '</div>',
        unsafe_allow_html=True,
    )
elif _SCRIPT_PATH and _import_err:
    st.markdown(
        '<div style="background:rgba(239,68,68,.06);border:1px solid rgba(239,68,68,.2);'
        'border-radius:10px;padding:.7rem 1.2rem;font-size:.83rem;color:#c07070;margin-bottom:1rem;">'
        f'❌ <strong style="color:#f87171;">Error al cargar el módulo</strong>: {_import_err}'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div style="background:rgba(245,158,11,.06);border:1px solid rgba(245,158,11,.2);'
        'border-radius:10px;padding:.7rem 1.2rem;font-size:.83rem;color:#b09060;margin-bottom:1rem;">'
        '⚠️ <strong style="color:#fbbf24;">Script de automatización no encontrado</strong> — '
        'Verifica que el archivo exista en la carpeta <code>APP FINALES</code>'
        '</div>',
        unsafe_allow_html=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_cfg, tab_run, tab_res = st.tabs([
    "⚙️ Configuración",
    "▶️ Ejecución",
    "📁 Resultados",
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Configuración
# ─────────────────────────────────────────────────────────────────────────────
with tab_cfg:
    st.markdown("""
<div class="ev-section" style="margin-top:1.5rem;">
  <span class="ev-section-num">01</span>
  <span class="ev-section-title">Carga de Folios (Excel)</span>
  <span class="ev-section-sub">Hoja: FOLIOS · Columnas: FOLIO, NUMERO, RUT, CORRELATIVO DE PAGO</span>
</div>
""", unsafe_allow_html=True)

    excel_up = st.file_uploader(
        "Sube el archivo Excel con los folios",
        type=["xlsx", "xls"],
        key="liq_excel_up",
    )

    if excel_up:
        try:
            import pandas as pd
            df_e = pd.read_excel(excel_up, sheet_name="FOLIOS", dtype=str)
            # Guardar en archivo temporal para que el script lo lea
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".xlsx", prefix="liq_folios_"
            ) as tmp:
                tmp.write(excel_up.getvalue())
                st.session_state["liq_excel_path"] = tmp.name

            st.session_state["liq_folios_df"] = df_e
            st.success(f"✅ {len(df_e)} folios cargados desde la hoja **FOLIOS**")
            st.markdown(ev_design.ev_table_html(df_e.head(10)), unsafe_allow_html=True)
            if len(df_e) > 10:
                st.caption(f"… y {len(df_e) - 10} folios más")
        except Exception as e_xl:
            st.error(f"Error al leer el Excel: {e_xl}")

    st.markdown("""
<div class="ev-section" style="margin-top:1.5rem;">
  <span class="ev-section-num">02</span>
  <span class="ev-section-title">Parámetros de procesamiento</span>
</div>
""", unsafe_allow_html=True)

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        periodo_input = st.text_input(
            "Período (AAAAMM)",
            value=st.session_state["liq_periodo"] or datetime.now().strftime("%Y%m"),
            placeholder="202501",
            help="Período del proceso en formato AAAAMM",
        )
        st.session_state["liq_periodo"] = periodo_input.strip()

    with col_p2:
        carpeta_input = st.text_input(
            "Carpeta de salida",
            value=st.session_state["liq_carpeta"] or str(Path.home() / "Downloads" / "Liquidaciones"),
            placeholder=r"C:\Users\DAP\Downloads\Liquidaciones",
            help="Carpeta donde se guardarán los PDFs descargados",
        )
        st.session_state["liq_carpeta"] = carpeta_input.strip()

    with col_p3:
        folio_inicio = st.number_input(
            "Índice de inicio (0 = desde el principio)",
            min_value=0,
            value=int(st.session_state["liq_folio_inicio"]),
            step=1,
            help="Permite retomar un proceso interrumpido desde un folio específico",
        )
        st.session_state["liq_folio_inicio"] = int(folio_inicio)

    # Verificar que la carpeta de salida existe o se puede crear
    if carpeta_input.strip():
        p_carpeta = Path(carpeta_input.strip())
        if p_carpeta.exists():
            st.markdown(
                f'<span style="font-size:.8rem;color:#1ed760;">✓ Carpeta existe</span>',
                unsafe_allow_html=True,
            )
        else:
            if st.button("📁 Crear carpeta de salida", use_container_width=False):
                try:
                    p_carpeta.mkdir(parents=True, exist_ok=True)
                    st.success(f"Carpeta creada: {p_carpeta}")
                except Exception as e_dir:
                    st.error(f"No se pudo crear: {e_dir}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Ejecución
# ─────────────────────────────────────────────────────────────────────────────
with tab_run:
    st.markdown("""
<div class="ev-section" style="margin-top:1.5rem;">
  <span class="ev-section-num">01</span>
  <span class="ev-section-title">Control de Ejecución</span>
  <span class="ev-section-sub">El proceso corre en segundo plano — SIRH debe estar abierto</span>
</div>
""", unsafe_allow_html=True)

    # ── Requisitos previos ──────────────────────────────────────────────────
    folios_ok  = st.session_state["liq_folios_df"] is not None
    periodo_ok = bool(re.match(r"^\d{6}$", st.session_state["liq_periodo"])) if True else False
    carpeta_ok = bool(st.session_state["liq_carpeta"])
    modulo_ok  = _auto_mod is not None

    import re as _re
    periodo_ok = bool(_re.match(r"^\d{6}$", st.session_state.get("liq_periodo", "")))

    req_items = [
        ("Módulo de automatización cargado", modulo_ok),
        ("Folios cargados desde Excel",      folios_ok),
        ("Período definido (AAAAMM)",         periodo_ok),
        ("Carpeta de salida definida",        carpeta_ok),
    ]

    cols_req = st.columns(4)
    for i, (label, ok) in enumerate(req_items):
        with cols_req[i]:
            color   = "#1ed760" if ok else "#f87171"
            icon    = "✓" if ok else "✗"
            bg      = "rgba(29,185,84,.08)" if ok else "rgba(239,68,68,.08)"
            border  = "rgba(29,185,84,.2)" if ok else "rgba(239,68,68,.2)"
            st.markdown(
                f'<div style="background:{bg};border:1px solid {border};border-radius:8px;'
                f'padding:.6rem .8rem;font-size:.75rem;color:{color};">'
                f'{icon} {label}</div>',
                unsafe_allow_html=True,
            )

    all_ok = all(ok for _, ok in req_items)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Estado actual ───────────────────────────────────────────────────────
    running = st.session_state["liq_running"]
    if running:
        st.markdown(
            '<span class="status-running">● En ejecución — no cierres la aplicación</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="status-idle">○ Detenido</span>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    col_start, col_stop, col_refresh = st.columns([1, 1, 1])

    # ── Función que corre en background ────────────────────────────────────
    def _run_automation(log_q: queue.Queue, excel_path: str,
                        periodo: str, carpeta: str, folio_inicio: int):
        """Hilo de fondo: llama a las funciones del script de automatización."""
        def _log(msg: str):
            ts = datetime.now().strftime("%H:%M:%S")
            log_q.put(f"[{ts}] {msg}")

        try:
            _log("🚀 Iniciando proceso de descarga...")

            if not hasattr(_auto_mod, "cargar_folios"):
                _log("❌ El módulo no expone 'cargar_folios'. Verifica el script.")
                return

            # Cargar folios
            _log(f"📂 Cargando folios desde {excel_path}")
            _auto_mod.PERIODO_AAAAMM  = periodo
            _auto_mod.CARPETA_SALIDA  = carpeta
            _auto_mod.STOP_FLAG       = False

            folios = _auto_mod.cargar_folios(excel_path)
            _log(f"✅ {len(folios)} folios cargados")

            # Conectar SIRH
            _log("🔌 Conectando con SIRH...")
            sirh_win = _auto_mod.conectar_sirh()
            if sirh_win is None:
                _log("❌ No se encontró ventana de SIRH. Asegúrate de que esté abierto.")
                return

            _log("✅ Ventana SIRH encontrada")

            # Procesar lote
            total = len(folios)
            for idx, folio in enumerate(folios[folio_inicio:], start=folio_inicio):
                if getattr(_auto_mod, "STOP_FLAG", False):
                    _log("⛔ Proceso detenido por el usuario")
                    break
                _log(f"[{idx+1}/{total}] Procesando folio {folio.get('FOLIO', folio)}")
                try:
                    _auto_mod.procesar_folio(sirh_win, folio, carpeta)
                    _log(f"  ✅ Folio guardado")
                except Exception as e_folio:
                    _log(f"  ❌ Error: {e_folio}")

            _log("🏁 Proceso terminado")

        except Exception as e_global:
            _log(f"❌ Error global: {e_global}")
        finally:
            log_q.put("__DONE__")

    # ── Botón INICIAR ───────────────────────────────────────────────────────
    with col_start:
        if st.button(
            "▶️ Iniciar Proceso",
            disabled=(running or not all_ok),
            use_container_width=True,
        ):
            q = queue.Queue()
            st.session_state["liq_queue"]   = q
            st.session_state["liq_log"]     = []
            st.session_state["liq_running"] = True

            t = threading.Thread(
                target=_run_automation,
                args=(
                    q,
                    st.session_state["liq_excel_path"],
                    st.session_state["liq_periodo"],
                    st.session_state["liq_carpeta"],
                    st.session_state["liq_folio_inicio"],
                ),
                daemon=True,
            )
            t.start()
            st.session_state["liq_thread"] = t
            st.rerun()

    # ── Botón DETENER ───────────────────────────────────────────────────────
    with col_stop:
        if st.button(
            "⛔ Detener",
            disabled=not running,
            use_container_width=True,
        ):
            if _auto_mod:
                _auto_mod.STOP_FLAG = True
            st.session_state["liq_running"] = False
            st.rerun()

    # ── Botón ACTUALIZAR LOG ────────────────────────────────────────────────
    with col_refresh:
        if st.button("🔄 Actualizar Log", use_container_width=True):
            # Leer mensajes pendientes de la cola
            q = st.session_state.get("liq_queue")
            if q:
                while True:
                    try:
                        msg = q.get_nowait()
                        if msg == "__DONE__":
                            st.session_state["liq_running"] = False
                        else:
                            st.session_state["liq_log"].append(msg)
                    except queue.Empty:
                        break
            st.rerun()

    # ── Log de ejecución ─────────────────────────────────────────────────
    st.markdown("""
<div class="ev-section" style="margin-top:1.5rem;">
  <span class="ev-section-num">02</span>
  <span class="ev-section-title">Log de Ejecución</span>
  <span class="ev-section-sub">Presiona "Actualizar Log" para ver nuevos mensajes</span>
</div>
""", unsafe_allow_html=True)

    log_lines = st.session_state.get("liq_log", [])
    if log_lines:
        log_html = ""
        for line in log_lines[-150:]:   # últimas 150 líneas
            if "❌" in line or "Error" in line.lower():
                css = "log-err"
            elif "✅" in line or "✓" in line or "🏁" in line:
                css = "log-ok"
            elif "⚠️" in line or "⛔" in line:
                css = "log-warn"
            else:
                css = "log-info"
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            log_html += f'<span class="{css}">{escaped}</span>\n'

        st.markdown(
            f'<div class="log-box">{log_html}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="log-box" style="color:#2a2a2a;text-align:center;">'
            'Sin mensajes — inicia el proceso y presiona Actualizar Log</div>',
            unsafe_allow_html=True,
        )

    # Auto-leer cola si está corriendo (sin auto-rerun para no reiniciar tabs)
    if running:
        q = st.session_state.get("liq_queue")
        if q:
            changed = False
            while True:
                try:
                    msg = q.get_nowait()
                    if msg == "__DONE__":
                        st.session_state["liq_running"] = False
                        changed = True
                    else:
                        st.session_state["liq_log"].append(msg)
                        changed = True
                except queue.Empty:
                    break

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Resultados
# ─────────────────────────────────────────────────────────────────────────────
with tab_res:
    st.markdown("""
<div class="ev-section" style="margin-top:1.5rem;">
  <span class="ev-section-num">01</span>
  <span class="ev-section-title">PDFs descargados</span>
  <span class="ev-section-sub">Lista de archivos en la carpeta de salida</span>
</div>
""", unsafe_allow_html=True)

    carpeta_out = st.session_state.get("liq_carpeta", "")
    if not carpeta_out:
        st.info("Define la carpeta de salida en la pestaña **Configuración**.")
    else:
        p_out = Path(carpeta_out)
        if not p_out.exists():
            st.warning(f"La carpeta `{carpeta_out}` no existe aún.")
        else:
            pdfs = sorted(p_out.glob("**/*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True)
            if not pdfs:
                st.info("No hay PDFs en la carpeta de salida todavía.")
            else:
                import pandas as pd
                rows_res = []
                for fp in pdfs[:200]:
                    stat = fp.stat()
                    rows_res.append({
                        "Archivo":   fp.name,
                        "Subcarpeta": str(fp.parent.relative_to(p_out)) if fp.parent != p_out else "—",
                        "Tamaño":    f"{stat.st_size / 1024:.1f} KB",
                        "Fecha":     datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    })

                df_res = pd.DataFrame(rows_res)
                st.metric("Total PDFs encontrados", len(pdfs))
                st.markdown(ev_design.ev_table_html(df_res), unsafe_allow_html=True)
                if len(pdfs) > 200:
                    st.caption(f"Mostrando los 200 más recientes de {len(pdfs)} totales")

    if st.button("🔄 Refrescar lista", use_container_width=False):
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

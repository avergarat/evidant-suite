# -*- coding: utf-8 -*-
"""
Página 2 — Programa Financiero CASA
Envuelve la lógica de PF_CASA (Tkinter) en una interfaz Streamlit.
La función process_steps_1_to_4() se importa directamente del módulo original.
"""

import sys
import os
import io
import traceback
import tempfile

import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ev_design

st.set_page_config(
    page_title="Paso 2: Centralización de Gastos · Evidant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


ev_design.render(
    current="financiero",
    page_title="Programa Financiero CASA",
    page_sub="Paso 3 · Generación de planilla PF desde base redistribuida",
    breadcrumb="Procesamiento Financiero › Paso 3",
    icon="📊",
)
# ── ev_design ya inyectó el CSS Spotify maestro y el page header arriba ──

# ── Import logic ──────────────────────────────────────────────────────────────
try:
    # El módulo PF_CASA usa tkinter en su bloque __main__ y en la clase App,
    # pero las funciones de procesamiento son independientes.
    # Importamos únicamente las funciones necesarias.
    _pf_module_name = "PF_CASA_V1_mejorado_v18_6_PF_MES_fix_CC_v20patch"
    import importlib.util

    _spec = importlib.util.spec_from_file_location(
        _pf_module_name,
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), f"{_pf_module_name}.py"),
    )
    _pf_mod = importlib.util.module_from_spec(_spec)
    # Evitar que el bloque __main__ ejecute tkinter al importar
    _pf_mod.__name__ = _pf_module_name  # No "__main__"
    _spec.loader.exec_module(_pf_mod)

    process_steps_1_to_4           = _pf_mod.process_steps_1_to_4
    get_sheetnames_fast_xlsx        = _pf_mod.get_sheetnames_fast_xlsx
    get_centros_costo_from_base_xlsx = _pf_mod.get_centros_costo_from_base_xlsx
    get_procesos_from_base_xlsx     = _pf_mod.get_procesos_from_base_xlsx
    _import_ok = True
except Exception as _e:
    _import_ok = False
    _import_err = str(_e)
    _tb = traceback.format_exc()

if not _import_ok:
    st.error(f"No se pudo importar el módulo PF_CASA: {_import_err}")
    st.code(_tb)
    st.info("Asegúrate de que el archivo PF_CASA_V1_mejorado_v18_6_PF_MES_fix_CC_v20patch.py esté en el directorio raíz de la suite.")
    st.stop()

# ── Step 1: Upload file ───────────────────────────────────────────────────────
st.markdown("### 1. Archivo fuente")
uploaded = st.file_uploader(
    "Sube el archivo Excel (.xlsx)",
    type=["xlsx"],
    key="pf_uploader",
    help="Debe contener las hojas BASE, CONSOLIDACIÓN y opcionalmente PROGRAMA FINANCIERO (modelo)",
)

if not uploaded:
    st.info("⬆️  Sube tu archivo Excel para continuar.")
    st.stop()

# Save to a temp file (process_steps_1_to_4 requiere ruta en disco)
@st.cache_data(show_spinner=False)
def save_to_temp(file_bytes, filename):
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False, prefix="pf_src_")
    tmp.write(file_bytes)
    tmp.close()
    return tmp.name

file_bytes = uploaded.read()
src_path = save_to_temp(file_bytes, uploaded.name)

# Get sheet names
try:
    sheets = get_sheetnames_fast_xlsx(src_path)
except Exception as e:
    st.error(f"No pude leer las hojas del Excel: {e}")
    st.stop()

st.success(f"✅ Archivo cargado · {len(sheets)} hojas detectadas")

# ── Step 2: Configuration ────────────────────────────────────────────────────
st.markdown("### 2. Configuración de hojas")
col1, col2, col3 = st.columns(3)
with col1:
    base_sheet = st.selectbox(
        "Hoja BASE (origen)",
        options=sheets,
        index=next((i for i, s in enumerate(sheets) if "BASE" in s.upper()), 0),
    )
with col2:
    consol_sheet = st.selectbox(
        "Hoja CONSOLIDACIÓN",
        options=sheets,
        index=next((i for i, s in enumerate(sheets) if "CONSOL" in s.upper() or "REPORTE" in s.upper()), 0),
    )
with col3:
    pf_model_sheet = st.selectbox(
        "Hoja PROGRAMA FINANCIERO (modelo)",
        options=["(ninguna)"] + sheets,
        index=next((i+1 for i, s in enumerate(sheets) if "FINANCIERO" in s.upper() or "PROGRAMA" in s.upper()), 0),
    )

# ── Step 3: Filters ───────────────────────────────────────────────────────────
st.markdown("### 3. Filtros")
col_a, col_b = st.columns(2)

with col_a:
    laws = st.multiselect(
        "Leyes (selecciona una o más)",
        options=["18834", "19664", "15076"],
        default=["18834", "19664", "15076"],
    )
    months = st.multiselect(
        "Meses de pago",
        options=[f"{m:02d}" for m in range(1, 13)],
        default=[f"{m:02d}" for m in range(1, 13)],
    )

with col_b:
    generate_pf = st.checkbox(
        '✅  Generar Programa Financiero (PF_MES_xx + PF_ANUAL)',
        value=False,
    )
    st.markdown(" ")
    load_filters = st.button("🔄  Cargar listas de Proceso y Centro de Costo desde la BASE", use_container_width=True)

# Load CC and Proceso from base
if "pf_centros" not in st.session_state:
    st.session_state["pf_centros"] = []
if "pf_procesos" not in st.session_state:
    st.session_state["pf_procesos"] = []

if load_filters:
    with st.spinner("Leyendo valores únicos desde la hoja BASE..."):
        try:
            st.session_state["pf_centros"]  = get_centros_costo_from_base_xlsx(src_path, base_sheet)
            st.session_state["pf_procesos"] = get_procesos_from_base_xlsx(src_path, base_sheet)
            st.success(f"✅ {len(st.session_state['pf_centros'])} centros de costo · {len(st.session_state['pf_procesos'])} procesos cargados")
        except Exception as e:
            st.error(f"Error al cargar listas: {e}")

col_c, col_d = st.columns(2)
with col_c:
    centros_opts = st.session_state["pf_centros"] or []
    centros_sel = st.multiselect(
        f"Centros de Costo ({len(centros_opts)} disponibles — vacío = todos)",
        options=centros_opts,
        default=centros_opts,
    )
with col_d:
    procesos_opts = st.session_state["pf_procesos"] or []
    procesos_sel = st.multiselect(
        f"Procesos ({len(procesos_opts)} disponibles — vacío = todos)",
        options=procesos_opts,
        default=procesos_opts,
    )

# ── Step 4: Execute ───────────────────────────────────────────────────────────
st.divider()

if st.button("⚡  GENERAR PROGRAMA FINANCIERO", type="primary", use_container_width=True):
    if not laws:
        st.warning("⚠️  Selecciona al menos una ley.")
        st.stop()
    if generate_pf and pf_model_sheet == "(ninguna)":
        st.warning("⚠️  Para generar PF, debes seleccionar la hoja modelo de Programa Financiero.")
        st.stop()

    months_int = [int(m) for m in months]

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False, prefix="pf_out_") as tmp_out:
        out_path = tmp_out.name

    try:
        with st.status("⚡ Generando Programa Financiero...", expanded=True) as _pf_status:
          _pbar_pf = st.progress(0.1, text="Procesando programa financiero...")
          with st.spinner("Procesando programa financiero..."):
            result_path = process_steps_1_to_4(
                src_path=src_path,
                base_sheet_name=base_sheet,
                consol_sheet_name=consol_sheet,
                col_range_montos="AUTO",
                law=laws[0] if laws else "18834",
                laws_selected=laws,
                out_path=out_path,
                months_selected=months_int if months_int else None,
                centros_selected=centros_sel if centros_sel else None,
                procesos_selected=procesos_sel if procesos_sel else None,
                generate_pf=generate_pf,
                pf_model_sheet_name=pf_model_sheet if generate_pf and pf_model_sheet != "(ninguna)" else None,
            )

        with open(result_path, "rb") as f:
            out_bytes = f.read()

        try:
            os.remove(result_path)
        except Exception:
            pass

        st.success("✅ Programa Financiero generado exitosamente.")
        st.download_button(
            "📥  Descargar archivo de salida (.xlsx)",
            data=out_bytes,
            file_name="2. CENTRALIZACION DE GASTOS.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    except Exception:
        st.error("❌ El procesamiento falló.")
        st.code(traceback.format_exc())

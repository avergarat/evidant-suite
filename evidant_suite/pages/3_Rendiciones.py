# -*- coding: utf-8 -*-
# PASO CUATRO: Rendiciones
# Motor embebido — no requiere plantilla Excel externa.
# Entrada: 3. REDISTRIBUCION.xlsx + honorarios.xlsx | Salida: 4. RENDICIONES.xlsx
import sys, os, io, re, traceback, unicodedata
import streamlit as st
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ev_design

st.set_page_config(page_title="Paso 4: Rendiciones - Evidant", page_icon="P", layout="wide")

ev_design.render(
    current="rendiciones",
    page_title="Generador de Rendiciones",
    page_sub="Paso 4 · Consolidación de remuneraciones y honorarios con homologación",
    breadcrumb="Procesamiento Financiero › Paso 4",
    icon="📋",
)
# ── Tablas de homologacion embebidas ──────────────────────────────────────────
# Clave: texto normalizado (sin tildes, lower, strip) -> valor oficial
# HONORARIOS: mapeo exacto basado en los 25 programas únicos del archivo real
# Clave: texto normalizado (sin tildes, lower, strip) -> nombre oficial
_HON_RAW = [
    # ACCESO MIGRANTES
    ("acceso a la atencion de salud a personas migrantes - personal medico",        "ACCESO A LA ATENCION DE SALUD A PERSONAS MIGRANTES"),
    ("acceso a la atencion de salud a personas migrantes - personal no medico",     "ACCESO A LA ATENCION DE SALUD A PERSONAS MIGRANTES"),
    # APOYO GESTION (variantes con y sin espacio tras punto)
    ("apoyo a la gest. en el nivel primario de salud en los estab. de los serv.de salud-personal medico",    "APOYO A LA GESTION EN LOS ESTABLECIMIENTOS DEPENDIENTES DE LOS SERVICIOS DE SALUD"),
    ("apoyo a la gest. en el nivel primario de salud en los estab. de los serv.de salud-personal no medico", "APOYO A LA GESTION EN LOS ESTABLECIMIENTOS DEPENDIENTES DE LOS SERVICIOS DE SALUD"),
    ("apoyo a la gest.en el nivel primario de salud en los estab. de los serv.de salud-personal medico",     "APOYO A LA GESTION EN LOS ESTABLECIMIENTOS DEPENDIENTES DE LOS SERVICIOS DE SALUD"),
    ("apoyo a la gest.en el nivel primario de salud en los estab. de los serv.de salud-personal no medico",  "APOYO A LA GESTION EN LOS ESTABLECIMIENTOS DEPENDIENTES DE LOS SERVICIOS DE SALUD"),
    # CECOSF (sin FAMILIAR)
    ("centro comunitarios de salud familia (cecosf)",   "CENTRO COMUNITARIOS DE SALUD FAMILIAR (CECOSF)"),
    # CHILE CRECE CONTIGO
    ("chile crece contigo - personal no medico",        "PROGRAMA DE APOYO AL DESARROLLO BIOPSICOSOCIAL EN LA RED ASISTENCIAL"),
    # ESPACIOS AMIGABLES
    ("espacios amigables para adolescentes - personal no medico", "ESPACIOS AMIGABLES PARA ADOLESCENTES"),
    # MAS ADULTOS MAYORES
    ("mas adultos mayores autovalentes - personal no medico", "MAS ADULTOS MAYORES AUTOVALENTES"),
    # PASMI
    ("programa de apoyo salud mental infantil - personal medico",    "PROGRAMA DE APOYO A LA SALUD MENTAL INFANTIL (PASMI)"),
    ("programa de apoyo salud mental infantil - personal no medico", "PROGRAMA DE APOYO A LA SALUD MENTAL INFANTIL (PASMI)"),
    # SALUD RESPIRATORIA
    ("programa de salud respiratoria personal medico",    "SALUD RESPIRATORIA"),
    ("programa de salud respiratoria personal no medico", "SALUD RESPIRATORIA"),
    # ELIGE VIDA SANA
    ("programa elige vida sana - personal no medico", "ELIGE VIDA SANA"),
    # SALUD BUCAL
    ("programa estrategias de salud bucal - personal medico", "ESTRATEGIA DE SALUD BUCAL/GES"),
    # LISTA DE ESPERA
    ("programa lista de espera no ges - personal medico",    "LISTA DE ESPERA"),
    ("programa lista de espera no ges - personal no medico", "LISTA DE ESPERA"),
    # RESOLUTIVIDAD
    ("resolutividad en atencion primaria - personal medico",    "RESOLUTIVIDAD EN ATENCION PRIMARIA"),
    ("resolutividad en atencion primaria - personal no medico", "RESOLUTIVIDAD EN ATENCION PRIMARIA"),
    # SALUD MENTAL
    ("salud mental en atencion primaria de salud - personal no medico", "SALUD MENTAL EN LA ATENCION PRIMARIA DE SALUD"),
    # SAPU / URGENCIA
    ("servicio de atencion primaria de urgencia - personal medico",    "ESTRATEGIAS DE INTERVENCION DE URGENCIA EN ATENCION PRIMARIA DE SALUD"),
    ("servicio de atencion primaria de urgencia - personal no medico", "ESTRATEGIAS DE INTERVENCION DE URGENCIA EN ATENCION PRIMARIA DE SALUD"),
    # SAR
    ("servicio de atencion primaria de urgencia de alta resolucion - personal medico",    "SERVICIO DE ATENCION PRIMARIA DE URGENCIA DE ALTA RESOLUCION (SAR)"),
    ("servicio de atencion primaria de urgencia de alta resolucion - personal no medico", "SERVICIO DE ATENCION PRIMARIA DE URGENCIA DE ALTA RESOLUCION (SAR)"),
]

# CONSOLIDADO: programas ya vienen con nombres oficiales EXCEPTO estos casos
_CONS_RAW = [
    ("intermedio medico quirurgico", "APOYO A LA GESTION EN LOS ESTABLECIMIENTOS DEPENDIENTES DE LOS SERVICIOS DE SALUD"),
]

_SALIDA_COLS = [
    "ID_RELACION","Mes Rendicion","Establecimiento","Anio Devengo","Mes Devengo",
    "Resolucion","Programa","Unidad","Descripcion Unidad",
    "Documento (Factura, Boleta, Liquidacion, etc.)","FOLIO (Honorarios)",
    "Num de Documento","RUN","Proveedor o Prestador","Planilla de Pago",
    "Horas","Grado","Calidad Juridica","PLANTA","Detalle","Forma de Pago",
    "Subt.","Monto (Total Haberes)","Tipo de Contrato (Honorarios o Remuneraciones)",
    "Especialidad de Funcionario o prestador","Tipo de Movimiento",
    "Descuentos (asignacion familiar bonos u otros).",
    "Total_Haberes_Netos",
]


def _norm(x):
    if x is None or (isinstance(x, float) and pd.isna(x)): return ""
    s = unicodedata.normalize("NFKD", str(x).strip())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).lower().strip()

def _bmap(table): return {k: v for k, v in table}
_MAP_HON  = _bmap(_HON_RAW)
_MAP_CONS = _bmap(_CONS_RAW)

def _hom(val, m): return m.get(_norm(val), str(val).strip() if val is not None else "")
def _sp(x):
    s = str(x).strip() if x is not None and not (isinstance(x, float) and pd.isna(x)) else ""
    return s.split("_",1)[1].strip() if "_" in s else s
def _un(x):
    s = str(x).strip() if x is not None and not (isinstance(x, float) and pd.isna(x)) else ""
    if "_" in s:
        m = re.search(r"\d+", s.split("_",1)[0]); return m.group(0) if m else s.split("_",1)[0].strip()
    m = re.search(r"\d+", s); return m.group(0) if m else ""
def _ud(x):
    s = str(x).strip() if x is not None and not (isinstance(x, float) and pd.isna(x)) else ""
    return s.split("_",1)[1].strip() if "_" in s else s
def _pp(x):
    s = _norm(x)
    if "accesorio" in s: return "A"
    if "pago normal" in s: return "M"
    return "" if s == "" else str(x).strip()
def _fp(x): return "EFECTIVO" if (str(x).strip() if pd.notna(x) else "") == "" else "TRANSFERENCIA"

CSS = (
    "<style>"
    "@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Space+Grotesk:wght@400;500;600&display=swap');"
    ":root{--ev-bg:#050d1a;--ev-card:#0d1e35;--ev-border:#1a3050;--ev-blue-1:#0057ff;"
    "--ev-blue-2:#0098ff;--ev-accent:#00e5ff;--ev-text:#e8f0fe;--ev-muted:#6b8caf;}"
    "html,body,[class*='css']{background-color:var(--ev-bg)!important;color:var(--ev-text)!important;font-family:'Space Grotesk',sans-serif!important;}"
    "[data-testid='stSidebar']{background:linear-gradient(180deg,#060f1e 0%,#081424 100%)!important;border-right:1px solid var(--ev-border)!important;}"
    "[data-testid='stSidebar'] *{color:var(--ev-text)!important;}"
    "#MainMenu,footer,header{visibility:hidden;}"
    ".block-container{padding-top:1.5rem!important;}"
    ".stButton>button{background:linear-gradient(135deg,#0057ff,#0098ff)!important;color:white!important;border:none!important;border-radius:8px!important;font-weight:600!important;}"
    "[data-testid='stFileUploader']{background:var(--ev-card)!important;border:1.5px dashed var(--ev-border)!important;border-radius:12px!important;}"
    "hr{border-color:var(--ev-border)!important;}"
    ".stDataFrame{border-radius:10px!important;overflow:hidden!important;}"
    ".stSuccess{background:rgba(0,230,160,0.1)!important;}"
    ".stWarning{background:rgba(255,184,48,0.1)!important;}"
    ".stError{background:rgba(255,80,80,0.1)!important;}"
    "[data-testid='stMetric']{background:var(--ev-card)!important;border:1px solid var(--ev-border)!important;border-radius:12px!important;padding:1rem!important;}"
    "[data-testid='stMetricValue']{color:#00e5ff!important;}"
    "input,textarea,[data-baseweb='input'] input{color:#e8f0fe!important;background:#0d1e35!important;border-color:#1a3050!important;}"
    "</style>"
)
st.markdown(CSS, unsafe_allow_html=True)


st.markdown('<div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.5rem;"><div style="font-size:2rem;">P</div><div><div style="font-size:1.6rem;font-weight:800;background:linear-gradient(135deg,#e8f0fe,#00c8ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">PASO CUATRO: Rendiciones</div><div style="font-size:0.8rem;color:#6b8caf;">Paso 4 de 4 - Remuneraciones + Honorarios - 4. RENDICIONES.xlsx</div></div></div><hr/>', unsafe_allow_html=True)

st.info("Sube **(1)** 3. REDISTRIBUCION DE GASTOS.xlsx con hoja CONSOLIDADO_REDISTRIBUIDO y **(2)** honorarios.xlsx con hoja HONORARIOS. Las reglas de homologacion estan embebidas.")

col_up1, col_up2 = st.columns(2)
with col_up1:
    st.caption("ARCHIVO PASO 3 (REDISTRIBUCION)")
    uploaded_remu = st.file_uploader("3. REDISTRIBUCION DE GASTOS.xlsx", type=["xlsx"], key="rend_remu")
with col_up2:
    st.caption("ARCHIVO DE HONORARIOS (SIRH)")
    uploaded_hon = st.file_uploader("honorarios.xlsx", type=["xlsx"], key="rend_hon")

if not uploaded_remu:
    st.info("Sube el archivo del Paso 3 para continuar.")
    st.stop()
if not uploaded_hon:
    st.warning("Sube el archivo de honorarios para generar las rendiciones completas.")
    st.stop()

st.divider()

if st.button("GENERAR 4. RENDICIONES", type="primary", use_container_width=True):
    try:
        with st.spinner("Leyendo archivos..."):
            remu_bytes = uploaded_remu.read()
            hon_bytes  = uploaded_hon.read()
            # Encabezado compuesto: fila 1=INDICADOR, fila 2=numeros, fila 3=nombres reales
            # header=2 => pandas usa la fila de indice 2 (3ra fila) como encabezado
            # Todas las columnas — originales del consolidado Y las nuevas agregadas
            # por el motor — tienen su encabezado en fila 3 (header=2).
            cons_usecols = [
                "ID_CONTRATO","MES PAGO","ESTAB","AÑO PAGO","AÑO DEVENGO",
                "MES DEVENGO","CENTRO DE COSTO","PROGRAMA",
                "UNIDAD","FOLIO","RUT-DV","NOMBRE","PROCESO",
                "HORAS / GRADOS","CALIDAD JURIDICA","PLANTA",
                "TIPO PAGO","TOTAL HABER","CARGO",
                "HABER_NETO","MOVIMIENTO","DESCUENTOS_REDISTRIBUIBLES",
            ]
            hon_usecols = [
                "ANO_PAGO","MES_PAGO","MES_DEVENGO","RUT","DV","NOMBRE","FOLIO",
                "ESTABLECIMIENTO","NOMBRE_PROGRAMA","CODIGO_UNIDAD","DESCRIPCION_UNIDAD",
                "NUM_BOLETA","CUENTA_BANCARIA","ESTAMENTO","MONTO_BRUTO_CUOTA",
            ]
            try:
                # Leer primero sin usecols para detectar columnas reales disponibles
                df_all_cols = pd.read_excel(io.BytesIO(remu_bytes),
                    sheet_name="CONSOLIDADO_REDISTRIBUIDO",
                    header=2, nrows=0, engine="openpyxl")
                available = df_all_cols.columns.tolist()
                usecols_ok = [c for c in cons_usecols if c in available]
                df_cons = pd.read_excel(io.BytesIO(remu_bytes),
                    sheet_name="CONSOLIDADO_REDISTRIBUIDO",
                    header=2, usecols=usecols_ok, engine="openpyxl")
            except Exception as e:
                st.error(f"Error leyendo CONSOLIDADO_REDISTRIBUIDO: {e}")
                st.stop()
            try:
                df_hon = pd.read_excel(io.BytesIO(hon_bytes),
                    sheet_name="HONORARIOS", usecols=hon_usecols, engine="openpyxl")
            except Exception as e:
                st.error(f"Error leyendo hoja HONORARIOS: {e}")
                st.stop()

        with st.spinner("Transformando remuneraciones..."):
            # Columnas nuevas (encabezado fila 3, sin prefijos NAN|NAN| ni INDICADOR|X|)
            # MOVIMIENTO y DESCUENTOS_BLOQUE no existen en el nuevo formato -> vacío
            # HABER_NETO -> LIQUIDO PAGO
            # TOTAL_HABER_BRUTO -> TOTAL HABER
            # ID_RELACION -> ID_CONTRATO
            oc = pd.DataFrame()
            oc["ID_RELACION"]       = df_cons.get("ID_CONTRATO", "")
            oc["Mes Rendicion"]     = df_cons.get("MES PAGO", "")
            oc["Establecimiento"]   = df_cons.get("ESTAB", "")
            # Año devengo: preferir AÑO DEVENGO, fallback AÑO PAGO
            anio_dev = df_cons.get("AÑO DEVENGO", df_cons.get("AÑO PAGO", ""))
            oc["Anio Devengo"]      = anio_dev
            oc["Mes Devengo"]       = df_cons.get("MES PAGO", "")  # MES DEVENGO viene vacío — usar MES PAGO
            oc["Resolucion"]        = df_cons.get("CENTRO DE COSTO", "")
            oc["Programa"]          = df_cons["PROGRAMA"].apply(lambda x: _hom(x, _MAP_CONS))
            oc["Unidad"]            = df_cons["UNIDAD"].apply(_un)
            oc["Descripcion Unidad"]= df_cons["UNIDAD"].apply(_ud)
            oc["Documento (Factura, Boleta, Liquidacion, etc.)"] = "LIQUIDACION"
            oc["FOLIO (Honorarios)"]= df_cons.get("FOLIO", "")
            oc["Num de Documento"]  = ""
            oc["RUN"]               = df_cons.get("RUT-DV", "")
            oc["Proveedor o Prestador"] = df_cons.get("NOMBRE", "")
            oc["Planilla de Pago"]  = df_cons["PROCESO"].apply(_pp)
            oc["Horas"]             = ""
            # HORAS / GRADOS viene limpio (ej: 44) — _sp quita prefijo si lo hay
            oc["Grado"]             = df_cons["HORAS / GRADOS"].apply(_sp)
            # CALIDAD JURIDICA viene limpia (ej: CONTRATADOS) — _sp no afecta si no hay _
            oc["Calidad Juridica"]  = df_cons["CALIDAD JURIDICA"].apply(_sp)
            oc["PLANTA"]            = df_cons.get("PLANTA", "")
            oc["Detalle"]           = "REMUNERACIONES TECNICOS DE NIVEL SUPERIOR EN ENFERMERIA 44 HORAS"
            oc["Forma de Pago"]     = df_cons.get("TIPO PAGO", "")
            oc["Subt."]             = "21"
            oc["Monto (Total Haberes)"] = df_cons.get("TOTAL HABER", "")
            oc["Tipo de Contrato (Honorarios o Remuneraciones)"] = "REMUNERACIONES"
            # CARGO viene como "F320_QUIMICO FARMACEUTICO" -> _sp extrae "QUIMICO FARMACEUTICO"
            oc["Especialidad de Funcionario o prestador"] = df_cons["CARGO"].apply(_sp)
            oc["Tipo de Movimiento"]= df_cons.get("MOVIMIENTO", "")  # MOVIMIENTO ahora está en fila 3
            oc["Descuentos (asignacion familiar bonos u otros)."] = df_cons.get("DESCUENTOS_REDISTRIBUIBLES", "")  # fila 3
            oc["Total_Haberes_Netos"]= df_cons.get("HABER_NETO", "")  # HABER_NETO ahora en fila 3

        with st.spinner("Transformando honorarios..."):
            oh = pd.DataFrame()
            oh["ID_RELACION"] = ("H-" + df_hon["RUT"].astype(str).fillna("")
                + "-" + df_hon["DV"].astype(str).fillna("")
                + "-" + df_hon["FOLIO"].astype(str).fillna("")
                + "-" + df_hon["NUM_BOLETA"].astype(str).fillna("")
                + "-" + df_hon["ANO_PAGO"].astype(str).fillna("")
                + "-" + df_hon["MES_PAGO"].astype(str).fillna(""))
            oh["Mes Rendicion"]    = df_hon["MES_PAGO"]
            oh["Establecimiento"]  = df_hon["ESTABLECIMIENTO"]
            oh["Anio Devengo"]     = df_hon["ANO_PAGO"]
            oh["Mes Devengo"]      = df_hon["MES_DEVENGO"]
            oh["Resolucion"]       = ""
            oh["Programa"]         = df_hon["NOMBRE_PROGRAMA"].apply(lambda x: _hom(x, _MAP_HON))
            oh["Unidad"]           = df_hon["CODIGO_UNIDAD"]
            oh["Descripcion Unidad"]= df_hon["DESCRIPCION_UNIDAD"]
            oh["Documento (Factura, Boleta, Liquidacion, etc.)"] = "HONORARIOS"
            oh["FOLIO (Honorarios)"]= df_hon["FOLIO"]
            oh["Num de Documento"]  = df_hon["NUM_BOLETA"]
            oh["RUN"]              = df_hon["RUT"].astype(str).fillna("") + "-" + df_hon["DV"].astype(str).fillna("")
            oh["Proveedor o Prestador"] = df_hon["NOMBRE"]
            oh["Planilla de Pago"] = "H"
            oh["Horas"]            = ""
            oh["Grado"]            = ""
            oh["Calidad Juridica"] = "HONORARIOS"
            oh["PLANTA"]           = df_hon["ESTAMENTO"]
            oh["Detalle"]          = ""
            oh["Forma de Pago"]    = df_hon["CUENTA_BANCARIA"].apply(_fp)
            oh["Subt."]            = "21"
            oh["Monto (Total Haberes)"] = df_hon["MONTO_BRUTO_CUOTA"]
            oh["Tipo de Contrato (Honorarios o Remuneraciones)"] = "HONORARIOS"
            oh["Especialidad de Funcionario o prestador"] = df_hon["ESTAMENTO"]
            oh["Tipo de Movimiento"] = ""
            oh["Descuentos (asignacion familiar bonos u otros)."] = ""
            oh["Total_Haberes_Netos"] = df_hon["MONTO_BRUTO_CUOTA"]

        with st.spinner("Consolidando..."):
            df_out = pd.concat([oc, oh], ignore_index=True)
            for c in _SALIDA_COLS:
                if c not in df_out.columns: df_out[c] = ""
            df_out = df_out[_SALIDA_COLS]
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df_out.to_excel(w, sheet_name="RENDICIONES", index=False)

        n_sm_c = int(df_cons["PROGRAMA"].apply(lambda x: _norm(x) not in _MAP_CONS).sum())
        n_sm_h = int(df_hon["NOMBRE_PROGRAMA"].apply(lambda x: _norm(x) not in _MAP_HON).sum())
        st.success(f"Listo: {len(df_out):,} registros -- {len(oc):,} REMU + {len(oh):,} HON")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total", f"{len(df_out):,}")
        c2.metric("REMU", f"{len(oc):,}")
        c3.metric("HON", f"{len(oh):,}")
        c4.metric("Sin match homologacion", str(n_sm_c+n_sm_h))
        st.download_button("Descargar 4. RENDICIONES.xlsx", data=buf.getvalue(),
            file_name="4. RENDICIONES.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
        if n_sm_c>0 or n_sm_h>0:
            with st.expander(f"Programas sin homologacion ({n_sm_c} REMU - {n_sm_h} HON)"):
                if n_sm_c>0:
                    vals=df_cons.loc[df_cons["PROGRAMA"].apply(lambda x: _norm(x) not in _MAP_CONS),"PROGRAMA"].dropna().unique()
                    st.markdown("**CONSOLIDADO sin match:**")
                    st.dataframe(pd.DataFrame({"PROGRAMA":vals}), use_container_width=True)
                if n_sm_h>0:
                    vals=df_hon.loc[df_hon["NOMBRE_PROGRAMA"].apply(lambda x: _norm(x) not in _MAP_HON),"NOMBRE_PROGRAMA"].dropna().unique()
                    st.markdown("**HONORARIOS sin match:**")
                    st.dataframe(pd.DataFrame({"NOMBRE_PROGRAMA":vals}), use_container_width=True)
        st.subheader("Vista previa -- primeras 50 filas")
        st.dataframe(df_out.head(50), use_container_width=True)
    except Exception:
        st.error("El procesamiento fallo.")
        st.code(traceback.format_exc())

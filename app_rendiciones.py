# app_rendiciones.py
import io
import re
import pandas as pd
import streamlit as st

SHEET_CONS = "CONSOLIDADO_REDISTRIBUIDO"
SHEET_HON = "HONORARIOS 2025"
SHEET_LISTA = "LISTA CONSOLIDACION"
SHEET_HOMOLOG = "HOMOLOGACIONES DE NOMBRES PROG"

OUT_SHEET = "RENDICIONES"
OUT_FILENAME = "Rendiciones.xlsx"

# -----------------------
# Helpers
# -----------------------
def norm_txt(x: str) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return ""
    return re.sub(r"\s+", " ", str(x).strip()).upper()

def split_after_underscore(x):
    """If x like '21_TITULARES' -> 'TITULARES'. If no underscore -> original."""
    s = str(x).strip() if x is not None and not (isinstance(x, float) and pd.isna(x)) else ""
    if "_" in s:
        return s.split("_", 1)[1].strip()
    return s

def unidad_num(x):
    """From '112_CESFAM ...' -> '112' (only digits before underscore)."""
    s = str(x).strip() if x is not None and not (isinstance(x, float) and pd.isna(x)) else ""
    if "_" in s:
        left = s.split("_", 1)[0].strip()
        m = re.search(r"\d+", left)
        return m.group(0) if m else left
    # fallback: first number token
    m = re.search(r"\d+", s)
    return m.group(0) if m else ""

def unidad_desc(x):
    """From '112_CESFAM A.M.' -> 'CESFAM A.M.' (text after underscore)."""
    s = str(x).strip() if x is not None and not (isinstance(x, float) and pd.isna(x)) else ""
    if "_" in s:
        return s.split("_", 1)[1].strip()
    # if no underscore, return whole string as description
    return s

def planilla_pago_from_proceso(x):
    s = norm_txt(x)
    if "ACCESORIO" in s:
        return "A"
    if "PAGO NORMAL" in s:
        return "M"
    # si no calza, no invento: devuelvo el original (sin upper for legibility)
    return "" if s == "" else str(x).strip()

def build_homolog_dict(df_homolog: pd.DataFrame, hoja_procedencia: str) -> dict:
    df = df_homolog.copy()
    df["HOJA PROCEDENCIA"] = df["HOJA PROCEDENCIA"].astype(str)
    df = df[df["HOJA PROCEDENCIA"].str.strip() == hoja_procedencia].copy()

    # Key: "NOMBRES HONORARIOS" (nombre en hoja de origen)
    # Value: "NOMBRE REAL PROGRAMAS..."
    key_col = "NOMBRES HONORARIOS"
    val_col = "NOMBRE REAL PROGRAMAS (A CONSIDERAR EN REPORTES DE SALIDA"

    # A veces Excel recorta el nombre de columna si hay caracteres raros; normalizamos por startswith
    if val_col not in df.columns:
        # fallback: buscar la columna que empieza con "NOMBRE REAL PROGRAMAS"
        candidates = [c for c in df.columns if str(c).upper().startswith("NOMBRE REAL PROGRAMAS")]
        if not candidates:
            raise ValueError("No encontré columna 'NOMBRE REAL PROGRAMAS...' en HOMOLOGACIONES.")
        val_col = candidates[0]

    if key_col not in df.columns:
        raise ValueError("No encontré columna 'NOMBRES HONORARIOS' en HOMOLOGACIONES.")

    mapping = {}
    for _, r in df.iterrows():
        k = norm_txt(r.get(key_col))
        v = str(r.get(val_col)).strip() if pd.notna(r.get(val_col)) else ""
        if k and v:
            mapping[k] = v
    return mapping

def safe_read_excel(file_bytes, sheet_name, usecols=None):
    return pd.read_excel(
        io.BytesIO(file_bytes),
        sheet_name=sheet_name,
        usecols=usecols,
        engine="openpyxl"
    )

# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="Generador de Rendiciones", layout="wide")
st.title("Generador de RENDICIONES (CONSOLIDADO + HONORARIOS)")

uploaded = st.file_uploader("Sube el Excel (SALIDA_REDISTRIBUCION.xlsx)", type=["xlsx"])

if uploaded is None:
    st.info("Sube el archivo para comenzar.")
    st.stop()

file_bytes = uploaded.read()

# Leer LISTA CONSOLIDACION para obtener el orden de columnas de salida
df_lista = safe_read_excel(file_bytes, SHEET_LISTA)
df_lista.columns = ["SALIDA", "SRC_CONS", "RULE_CONS", "SRC_HON", "RULE_HON"]
# Filtrar filas con nombre de columna de salida
salida_cols = [c for c in df_lista["SALIDA"].tolist() if isinstance(c, str) and c.strip() and c.strip() != "BASE DE DATOS DE SALIDA"]

# Leer homologaciones
df_homolog = safe_read_excel(file_bytes, SHEET_HOMOLOG)
map_prog_cons = build_homolog_dict(df_homolog, SHEET_CONS)
map_prog_hon = build_homolog_dict(df_homolog, SHEET_HON)

# Columnas requeridas (solo las que usaremos) para acelerar lectura
cons_usecols = [
    "ID_RELACION",
    "NAN | NAN | MES PAGO",
    "NAN | NAN | ESTAB",
    "NAN | NAN | AÑO PAGO",
    "NAN | NAN | MES DEVENGO",
    "NAN | NAN | CENTRO DE COSTO",
    "NAN | NAN | PROGRAMA",
    "INDICADOR | 5 | UNIDAD",
    "NAN | NAN | FOLIO",
    "NAN | NAN | RUT-DV",
    "NAN | NAN | NOMBRE",
    "NAN | NAN | PROCESO",
    "INDICADOR | 2 | HORAS / GRADOS",
    "INDICADOR | 1 | CALIDAD JURIDICA",
    "INDICADOR | 4 | PLANTA",
    "INDICADOR | 9 | TIPO PAGO",
    "TOTAL_HABER_BRUTO",
    "INDICADOR | 6 | CARGO",
    "MOVIMIENTO",
    "DESCUENTOS_BLOQUE",
    "HABER_NETO",
]

hon_usecols = [
    "ANO_PAGO",
    "MES_PAGO",
    "MES_DEVENGO",
    "RUT",
    "DV",
    "NOMBRE",
    "FOLIO",
    "ESTABLECIMIENTO",
    "NOMBRE_PROGRAMA",
    "CODIGO_UNIDAD",
    "DESCRIPCION_UNIDAD",
    "NUM_BOLETA",
    "CUENTA_BANCARIA",
    "ESTAMENTO",
    "MONTO_BRUTO_CUOTA",
]

# Lectura
df_cons = safe_read_excel(file_bytes, SHEET_CONS, usecols=cons_usecols)
df_hon = safe_read_excel(file_bytes, SHEET_HON, usecols=hon_usecols)

# -----------------------
# Transform CONSOLIDADO -> salida
# -----------------------
out_cons = pd.DataFrame()
out_cons["ID_RELACION"] = df_cons["ID_RELACION"]
out_cons["Mes Rendicion"] = df_cons["NAN | NAN | MES PAGO"]
out_cons["Establecimiento"] = df_cons["NAN | NAN | ESTAB"]
out_cons["Año Devengo"] = df_cons["NAN | NAN | AÑO PAGO"]
out_cons["Mes Devengo"] = df_cons["NAN | NAN | MES DEVENGO"]
out_cons["Resolución"] = df_cons["NAN | NAN | CENTRO DE COSTO"]

# Programa homologado
prog_src = df_cons["NAN | NAN | PROGRAMA"].apply(norm_txt)
out_cons["Programa"] = prog_src.map(map_prog_cons).fillna(df_cons["NAN | NAN | PROGRAMA"])

# Unidad / Descripción Unidad
out_cons["Unidad"] = df_cons["INDICADOR | 5 | UNIDAD"].apply(unidad_num)
out_cons["Descripcion Unidad"] = df_cons["INDICADOR | 5 | UNIDAD"].apply(unidad_desc)

# Documento fijo para CONSOLIDADO
out_cons["Documento (Factura, Boleta, Liquidacion, etc.)"] = "LIQUIDACION"

out_cons["FOLIO (Honorarios)"] = df_cons["NAN | NAN | FOLIO"]
out_cons["Nº de Documento"] = ""  # no definido en la matriz para CONSOLIDADO
out_cons["RUN"] = df_cons["NAN | NAN | RUT-DV"]
out_cons["Proveedor o Prestador"] = df_cons["NAN | NAN | NOMBRE"]

# Planilla de pago por regla
out_cons["Planilla de Pago"] = df_cons["NAN | NAN | PROCESO"].apply(planilla_pago_from_proceso)

out_cons["Horas"] = ""  # no definido en matriz
out_cons["Grado"] = df_cons["INDICADOR | 2 | HORAS / GRADOS"].apply(split_after_underscore)

out_cons["Calidad Juridica"] = df_cons["INDICADOR | 1 | CALIDAD JURIDICA"].apply(split_after_underscore)
out_cons["PLANTA"] = df_cons["INDICADOR | 4 | PLANTA"]

out_cons["Detalle"] = "REMUNERACIONES TECNICOS DE NIVEL SUPERIOR EN ENFERMERIA 44 HORAS"
out_cons["Forma de Pago"] = df_cons["INDICADOR | 9 | TIPO PAGO"]

out_cons["Subt."] = "21"
out_cons["Monto (Total Haberes)"] = df_cons["TOTAL_HABER_BRUTO"]

out_cons["Tipo de Contrato (Honorarios o Remuneraciones)"] = "REMUNERACIONES"

out_cons["Especialidad de Funcionario o prestador"] = df_cons["INDICADOR | 6 | CARGO"].apply(split_after_underscore)
out_cons["Tipo de Movimiento"] = df_cons["MOVIMIENTO"]
out_cons["Descuentos (Ejemplo, asignación familiar, bono u otros financiados por otra vía)"] = df_cons["DESCUENTOS_BLOQUE"]
out_cons["Total_Haberes_Netos"] = df_cons["HABER_NETO"]

# -----------------------
# Transform HONORARIOS -> salida
# -----------------------
out_hon = pd.DataFrame()

# ID_RELACION creado
out_hon["ID_RELACION"] = (
    "H-"
    + df_hon["RUT"].astype(str).fillna("")
    + "-"
    + df_hon["DV"].astype(str).fillna("")
    + "-"
    + df_hon["FOLIO"].astype(str).fillna("")
    + "-"
    + df_hon["NUM_BOLETA"].astype(str).fillna("")
    + "-"
    + df_hon["ANO_PAGO"].astype(str).fillna("")
    + "-"
    + df_hon["MES_PAGO"].astype(str).fillna("")
)

out_hon["Mes Rendicion"] = df_hon["MES_PAGO"]
out_hon["Establecimiento"] = df_hon["ESTABLECIMIENTO"]
out_hon["Año Devengo"] = df_hon["ANO_PAGO"]
out_hon["Mes Devengo"] = df_hon["MES_DEVENGO"]
out_hon["Resolución"] = ""  # no definido para HON

# Programa homologado
prog_h_src = df_hon["NOMBRE_PROGRAMA"].apply(norm_txt)
out_hon["Programa"] = prog_h_src.map(map_prog_hon).fillna(df_hon["NOMBRE_PROGRAMA"])

out_hon["Unidad"] = df_hon["CODIGO_UNIDAD"]
out_hon["Descripcion Unidad"] = df_hon["DESCRIPCION_UNIDAD"]

out_hon["Documento (Factura, Boleta, Liquidacion, etc.)"] = "HONORARIOS"
out_hon["FOLIO (Honorarios)"] = df_hon["FOLIO"]
out_hon["Nº de Documento"] = df_hon["NUM_BOLETA"]

# RUN: RUT-DV
out_hon["RUN"] = df_hon["RUT"].astype(str).fillna("") + "-" + df_hon["DV"].astype(str).fillna("")
out_hon["Proveedor o Prestador"] = df_hon["NOMBRE"]

out_hon["Planilla de Pago"] = "H"
out_hon["Horas"] = ""
out_hon["Grado"] = ""

out_hon["Calidad Juridica"] = "HONORARIOS"
out_hon["PLANTA"] = df_hon.get("ESTAMENTO", "")  # tu tabla pone ESTAMENTO en PLANTA

out_hon["Detalle"] = ""

# Forma de pago por CUENTA_BANCARIA
def forma_pago_hon(x):
    s = str(x).strip() if pd.notna(x) else ""
    return "EFECTIVO" if s == "" else "TRANSFERENCIA"

out_hon["Forma de Pago"] = df_hon["CUENTA_BANCARIA"].apply(forma_pago_hon)

out_hon["Subt."] = "21"

out_hon["Monto (Total Haberes)"] = ""  # no definido en tu matriz para HON
out_hon["Tipo de Contrato (Honorarios o Remuneraciones)"] = "HONORARIOS"

# Especialidad... según tu matriz: ESTAMENTO
out_hon["Especialidad de Funcionario o prestador"] = df_hon["ESTAMENTO"]

out_hon["Tipo de Movimiento"] = ""
out_hon["Descuentos (Ejemplo, asignación familiar, bono u otros financiados por otra vía)"] = ""

out_hon["Total_Haberes_Netos"] = df_hon["MONTO_BRUTO_CUOTA"]

# -----------------------
# Unir y reordenar columnas según LISTA CONSOLIDACION
# -----------------------
df_out = pd.concat([out_cons, out_hon], ignore_index=True)

# Asegurar que estén todas las columnas del orden esperado
for c in salida_cols:
    if c not in df_out.columns:
        df_out[c] = ""

df_out = df_out[salida_cols]

# Preview
st.subheader("Vista previa (primeras 50 filas)")
st.dataframe(df_out.head(50), use_container_width=True)

# Exportar a Excel en memoria
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df_out.to_excel(writer, sheet_name=OUT_SHEET, index=False)

st.download_button(
    label="Descargar Rendiciones.xlsx",
    data=buffer.getvalue(),
    file_name=OUT_FILENAME,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

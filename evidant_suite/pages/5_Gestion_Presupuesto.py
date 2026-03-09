# -*- coding: utf-8 -*-
# MÓDULO: GESTIÓN DE PRESUPUESTO — evidant Suite v3
# Mejoras: tipografía grande, homologación semántica, nombre programa en tablas,
#           pivot centrado legible, descomposición orden Resolución→Programa, gráficos con títulos

import sys, os, io, traceback, sqlite3, hashlib
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ev_design

st.set_page_config(page_title="Gestión Presupuesto · Evidant", page_icon="💰", layout="wide")

ev_design.render(
    current="presupuesto",
    page_title="Gestión Presupuestaria",
    page_sub="Control de ejecución mensual · Marcos por CC · Dotación y análisis de costo",
    breadcrumb="Gestión Presupuestaria",
    icon="💰",
)
# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=DM+Mono:wght@300;400;500&display=swap');
:root{
  --bg:#050d1a;--card:#0d1e35;--border:#1a3050;
  --blue1:#0057ff;--blue2:#0098ff;--accent:#00e5ff;
  --text:#e8f0fe;--muted:#6b8caf;
  --ok:#00e6a0;--warn:#ffb830;--danger:#ff4d6d;
  --font:'Plus Jakarta Sans',sans-serif;--mono:'DM Mono',monospace;
}
html,body,[class*="css"]{background:var(--bg)!important;color:var(--text)!important;font-family:var(--font)!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#060f1e,#081424)!important;border-right:1px solid var(--border)!important;}
[data-testid="stSidebar"] *{color:var(--text)!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.2rem!important;max-width:1400px!important;}
.stButton>button{background:linear-gradient(135deg,var(--blue1),var(--blue2))!important;color:#fff!important;
  border:none!important;border-radius:8px!important;font-weight:700!important;font-size:1rem!important;
  padding:.6rem 1.2rem!important;transition:all .2s!important;}
.stButton>button:hover{box-shadow:0 0 20px rgba(0,152,255,.4)!important;transform:translateY(-1px)!important;}
[data-testid="stMetric"]{background:var(--card)!important;border:1px solid var(--border)!important;
  border-radius:12px!important;padding:1rem 1.2rem!important;}
[data-testid="stMetric"] label{color:var(--muted)!important;font-size:.82rem!important;
  letter-spacing:.8px;font-weight:600!important;text-transform:uppercase;}
[data-testid="stMetricValue"]{color:var(--accent)!important;font-family:var(--mono)!important;
  font-size:1.6rem!important;font-weight:500!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--card)!important;border-radius:10px!important;padding:.25rem!important;}
.stTabs [data-baseweb="tab"]{color:var(--muted)!important;font-size:.95rem!important;font-weight:600!important;padding:.55rem 1.1rem!important;}
.stTabs [aria-selected="true"]{color:var(--accent)!important;}
hr{border-color:var(--border)!important;}
/* ── Pivot table ──────────────────────────────────── */
.ptbl{width:100%;border-collapse:collapse;font-size:.95rem;}
.ptbl th{background:#08192e;color:#90b8d8;padding:.65rem 1rem;border:1px solid #1a3050;
  font-weight:700;text-align:center;font-size:.85rem;letter-spacing:.5px;text-transform:uppercase;}
.ptbl th.tleft{text-align:left;}
.ptbl td{padding:.55rem 1rem;border:1px solid #122035;text-align:center;
  color:#d5e8f8;font-family:var(--mono);font-size:.93rem;}
.ptbl td.tleft{text-align:left;color:#b8d0e8;font-family:var(--font);font-weight:600;}
.ptbl td.tprog{text-align:left;color:#7a9cb8;font-size:.78rem;padding-left:1.4rem;font-style:italic;}
.ptbl tr:nth-child(even){background:rgba(255,255,255,.023);}
.ptbl tr:hover{background:rgba(0,152,255,.08);}
.ptbl .tr-tot td{background:#061525;color:#00e5ff!important;font-weight:800;border-top:2px solid #0057ff;}
.ptbl .tr-tot td.tleft{font-family:var(--font);}
.tc{color:#00e5ff!important;font-weight:800;}
.lth{color:#a0c0d8!important;font-size:.78rem;}
.ltd{color:#ffb830!important;font-size:.82rem;font-weight:600;}
.ltn{color:#00e6a0!important;font-size:.82rem;font-weight:700;}
/* ── Semaforo ── */
.ev-tag{display:inline-block;padding:.25rem .75rem;border-radius:20px;font-size:.8rem;font-weight:700;letter-spacing:.5px;}
.tag-ok{background:rgba(0,230,160,.14);color:#00e6a0;border:1px solid rgba(0,230,160,.3);}
.tag-warn{background:rgba(255,184,48,.14);color:#ffb830;border:1px solid rgba(255,184,48,.3);}
.tag-danger{background:rgba(255,77,109,.14);color:#ff4d6d;border:1px solid rgba(255,77,109,.3);}
.ev-header{font-size:1.75rem;font-weight:800;background:linear-gradient(135deg,#0098ff,#00e5ff);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.ev-sub{font-size:.82rem;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase;margin-top:.2rem;}
</style>
""", unsafe_allow_html=True)

# ── DB ─────────────────────────────────────────────────────────────────────────
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "presupuesto")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "presupuesto.db")

def get_conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL"); return c

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS centros_costo(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL,
        programa TEXT NOT NULL, marco_clp REAL DEFAULT 0,
        activo INTEGER DEFAULT 1, updated_at TEXT DEFAULT (datetime('now','localtime')));
    CREATE TABLE IF NOT EXISTS imputaciones(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        periodo TEXT NOT NULL, resolucion TEXT NOT NULL, programa TEXT NOT NULL,
        unidad TEXT, descripcion_unidad TEXT, tipo_contrato TEXT,
        tipo_movimiento TEXT, calidad_juridica TEXT,
        monto_total_haberes REAL DEFAULT 0, descuentos REAL DEFAULT 0,
        haber_neto REAL DEFAULT 0, n_personas INTEGER DEFAULT 0,
        lote_hash TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now','localtime')));
    CREATE TABLE IF NOT EXISTS lotes_imputados(
        lote_hash TEXT PRIMARY KEY, periodo TEXT NOT NULL,
        n_registros INTEGER, created_at TEXT DEFAULT (datetime('now','localtime')));
    """)
    for col, typ in [("monto_total_haberes","REAL DEFAULT 0"),("descuentos","REAL DEFAULT 0")]:
        try: conn.execute(f"ALTER TABLE imputaciones ADD COLUMN {col} {typ}")
        except: pass
    conn.commit(); conn.close()

init_db()

# ── Helpers ────────────────────────────────────────────────────────────────────
MESES = {1:"ENE",2:"FEB",3:"MAR",4:"ABR",5:"MAY",6:"JUN",
         7:"JUL",8:"AGO",9:"SEP",10:"OCT",11:"NOV",12:"DIC"}

# Homologación semántica: CONTRATOS=CONTRATADOS, TITULAR=TITULARES, etc.
_HOMO_CJ = {
    "CONTRATO":"CONTRATOS","CONTRATADO":"CONTRATOS",
    "CONTRATADOS":"CONTRATOS",
    "TITULAR":"TITULARES","TITULAR HORA":"TITULARES","TITULARES HORA":"TITULARES",
    "HONORARIO":"HONORARIOS","A HONORARIOS":"HONORARIOS",
}
def homo_cj(v):
    s = str(v).strip().upper() if pd.notna(v) and str(v).strip() not in ("","nan","None") else "S/D"
    return _HOMO_CJ.get(s, s)

def fmt_clp(v):
    try: return f"$ {int(round(float(v))):,}".replace(",",".")
    except: return "$ 0"

def fmt_n(v):
    try: return f"{int(round(float(v))):,}".replace(",",".")
    except: return "0"

def pct_bar(pct):
    pct = min(float(pct), 100)
    c = "#1db954" if pct<80 else "#f59e0b" if pct<95 else "#ef4444"
    return (f'<div style="background:#0f2845;border-radius:6px;height:11px;width:100%;margin-top:5px;">'+
            f'<div style="background:{c};width:{pct:.1f}%;height:11px;border-radius:6px;"></div></div>'+
            f'<div style="font-size:.88rem;color:{c};margin-top:3px;font-weight:700;">{pct:.1f}%</div>')

def semaforo(pct):
    if pct<80: return '<span class="ev-tag tag-ok">NORMAL</span>'
    if pct<95: return '<span class="ev-tag tag-warn">ALERTA</span>'
    return '<span class="ev-tag tag-danger">CRÍTICO</span>'

def parse_num(v):
    try:
        if isinstance(v,(int,float)): return float(v)
        return float(str(v).replace(".","").replace(",",".").strip())
    except: return 0.0

def per_label(p):
    try: y,m=p.split("-"); return f"{MESES.get(int(m),m)} {y}"
    except: return str(p)

# Plotly base — design system evidant
PB = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(17,21,32,0.8)",
    font=dict(family="JetBrains Mono, monospace", color="#94a3b8", size=13),
    title_font=dict(size=16, color="#f1f5f9", family="Cabinet Grotesk, sans-serif"),
    margin=dict(l=20, r=20, t=55, b=20),
)
def ax(**kw): return dict(
    gridcolor="rgba(255,255,255,.06)",
    zerolinecolor="rgba(255,255,255,.06)",
    tickfont=dict(size=12, color="#475569"),
    title_font=dict(size=13, color="#94a3b8"),
    **kw)

# ── DB helpers ─────────────────────────────────────────────────────────────────
def load_centros():
    conn=get_conn(); df=pd.read_sql("SELECT * FROM centros_costo WHERE activo=1 ORDER BY CAST(numero AS INTEGER),numero",conn); conn.close(); return df

def save_centro(num,nom,prog,marco):
    conn=get_conn()
    conn.execute("""INSERT INTO centros_costo(numero,nombre,programa,marco_clp) VALUES(?,?,?,?)
        ON CONFLICT(numero) DO UPDATE SET nombre=excluded.nombre,programa=excluded.programa,
        marco_clp=excluded.marco_clp,updated_at=datetime('now','localtime')""",
        (str(num).strip(),str(nom).strip(),str(prog).strip(),float(marco)))
    conn.commit(); conn.close()

def del_centro(num):
    conn=get_conn(); conn.execute("UPDATE centros_costo SET activo=0 WHERE numero=?",(num,)); conn.commit(); conn.close()

def load_imp():
    conn=get_conn(); df=pd.read_sql("SELECT * FROM imputaciones",conn); conn.close()
    if not df.empty and "calidad_juridica" in df.columns:
        df["calidad_juridica"] = df["calidad_juridica"].apply(homo_cj)
    return df

def load_lotes():
    conn=get_conn(); df=pd.read_sql("SELECT * FROM lotes_imputados ORDER BY periodo DESC",conn); conn.close(); return df

def lote_hash(df,periodo):
    k=periodo+str(len(df))+str(df.get("Total_Haberes_Netos",pd.Series()).sum())
    return hashlib.md5(k.encode()).hexdigest()[:16]

def build_prog_map(df_imp, df_cc):
    """Devuelve {resolucion: nombre_programa_formal_canonico}"""
    m = {}
    if not df_imp.empty:
        modal = (df_imp.groupby("resolucion")["programa"]
                 .agg(lambda s: s.mode()[0] if not s.mode().empty else s.iloc[0])
                 .to_dict())
        m.update(modal)
    if not df_cc.empty:
        for _, r in df_cc.iterrows():
            if str(r["numero"]).strip():
                m[str(r["numero"]).strip()] = str(r["programa"]).strip()
    return m

# ── Sidebar ────────────────────────────────────────────────────────────────────

st.markdown('<div class="ev-header">💰 GESTIÓN DE PRESUPUESTO</div>', unsafe_allow_html=True)
st.markdown('<div class="ev-sub">Control de ejecución presupuestaria · Subtítulo 21</div>', unsafe_allow_html=True)
st.markdown("---")

tab_dash, tab_pivot, tab_import, tab_cc, tab_det = st.tabs([
    "📊  Dashboard", "📅  Estado Mensual", "📥  Imputar Rendiciones",
    "⚙️  Centros de Costo", "🔍  Análisis Detallado"])

# ══════════════════════════════════════════════════════════════════════════════
# CENTROS DE COSTO
# ══════════════════════════════════════════════════════════════════════════════
with tab_cc:
    st.markdown("### ⚙️ Configuración de Centros de Costo")
    df_cc  = load_centros(); df_ref = load_imp()
    prog_list = sorted(df_ref["programa"].dropna().unique().tolist()) if not df_ref.empty else []
    res_list  = sorted(df_ref["resolucion"].dropna().unique().tolist()) if not df_ref.empty else []
    cf, ct = st.columns([1, 1.8], gap="large")
    with cf:
        st.markdown("**Agregar / Actualizar Centro de Costo**")
        with st.form("form_cc", clear_on_submit=True):
            if res_list:
                r_opts = ["✏️ Ingresar manualmente..."] + res_list
                r_sel  = st.selectbox("N° Resolución (CC)", r_opts)
                n_num  = st.text_input("Resolución manual", placeholder="ej: 53") if r_sel=="✏️ Ingresar manualmente..." else r_sel
            else:
                n_num = st.text_input("N° Resolución (CC)", placeholder="ej: 53")
                st.caption("Importa rendiciones para cargar resoluciones.")
            n_nombre = st.text_input("Nombre formal", placeholder="ej: CESFAM CHUCHUNCO")
            if prog_list:
                p_opts = ["✏️ Ingresar manualmente..."] + prog_list
                p_sel  = st.selectbox("Programa asociado", p_opts)
                n_prog = st.text_input("Programa manual", placeholder="ej: APOYO A LA GESTION...") if p_sel=="✏️ Ingresar manualmente..." else p_sel
            else:
                n_prog = st.text_input("Programa asociado", placeholder="ej: APOYO A LA GESTION...")
            n_marco = st.number_input("Marco presupuestario anual (CLP)", min_value=0, step=1_000_000, value=0, format="%d")
            ok = st.form_submit_button("💾 Guardar Centro de Costo", use_container_width=True)
        if ok:
            if not str(n_num).strip() or not str(n_nombre).strip() or not str(n_prog).strip():
                st.error("Completa todos los campos.")
            else:
                save_centro(n_num, n_nombre, n_prog, n_marco); st.success(f"✅ CC **{n_num}** guardado."); st.rerun()
        if not df_cc.empty:
            st.markdown("---")
            opts = {f"{r.numero} — {r.nombre}": r.numero for r in df_cc.itertuples()}
            sel_d = st.selectbox("Eliminar CC", list(opts.keys()))
            if st.button("🗑️ Eliminar", use_container_width=True):
                del_centro(opts[sel_d]); st.success("Eliminado."); st.rerun()
    with ct:
        if df_cc.empty: st.info("No hay centros de costo. Agrega el primero.")
        else:
            ds = df_cc[["numero","nombre","programa","marco_clp"]].copy()
            ds.columns = ["N° Res.","Nombre","Programa","Marco CLP"]
            ds["Marco CLP"] = ds["Marco CLP"].apply(fmt_clp)
            st.dataframe(ds, use_container_width=True, hide_index=True)
        if res_list and not df_cc.empty:
            conf = set(df_cc["numero"].astype(str).tolist())
            sin  = [r for r in res_list if r not in conf]
            if sin: st.warning(f"⚠️ {len(sin)} resoluciones sin marco: {', '.join(sin[:10])}")

# ══════════════════════════════════════════════════════════════════════════════
# IMPUTAR RENDICIONES
# ══════════════════════════════════════════════════════════════════════════════
with tab_import:
    st.markdown("### 📥 Imputar Gastos desde Rendiciones")
    cu, ch = st.columns([1.3, 1], gap="large")
    with cu:
        up = st.file_uploader("4. RENDICIONES.xlsx", type=["xlsx"], key="rend_up")
        if up:
            try:
                rb = up.read()
                df_r = pd.read_excel(io.BytesIO(rb), sheet_name="RENDICIONES", engine="openpyxl")
                st.success(f"✅ **{len(df_r):,} registros** leídos.")
                ms = pd.to_numeric(df_r.get("Mes Rendicion", pd.Series(dtype=float)), errors="coerce").dropna()
                ys = pd.to_numeric(df_r.get("Anio Devengo",  pd.Series(dtype=float)), errors="coerce").dropna()
                md = int(ms.mode()[0]) if not ms.empty else datetime.now().month
                yd = int(ys.mode()[0]) if not ys.empty else datetime.now().year
                cm2,ca2 = st.columns(2)
                mes_s = cm2.selectbox("Mes", list(MESES.keys()), index=md-1, format_func=lambda x: f"{x:02d} — {MESES[x]}")
                ano_s = ca2.number_input("Año", min_value=2020, max_value=2035, value=yd)
                periodo = f"{ano_s}-{mes_s:02d}"
                h = lote_hash(df_r, periodo); lts = load_lotes()
                ya = not lts.empty and h in lts["lote_hash"].values
                if ya: st.warning(f"⚠️ **{per_label(periodo)}** ya fue imputado.")
                pc = ["Resolucion","Programa","Tipo de Contrato (Honorarios o Remuneraciones)",
                      "Monto (Total Haberes)","Descuentos (asignacion familiar bonos u otros).","Total_Haberes_Netos"]
                st.dataframe(df_r[[c for c in pc if c in df_r.columns]].head(5), use_container_width=True, hide_index=True)
                if st.button("⚡ IMPUTAR GASTOS", use_container_width=True, disabled=ya, type="primary"):
                    try:
                        df_r["_n"] = df_r.get("Total_Haberes_Netos", pd.Series(0,index=df_r.index)).apply(parse_num)
                        df_r["_t"] = df_r.get("Monto (Total Haberes)", pd.Series(0,index=df_r.index)).apply(parse_num)
                        df_r["_d"] = df_r.get("Descuentos (asignacion familiar bonos u otros).", pd.Series(0,index=df_r.index)).apply(parse_num)
                        df_r["_u"] = df_r.get("RUN", pd.Series("",index=df_r.index)).astype(str)
                        grp = [c for c in ["Resolucion","Programa","Descripcion Unidad","Unidad",
                               "Tipo de Contrato (Honorarios o Remuneraciones)","Tipo de Movimiento","Calidad Juridica"] if c in df_r.columns]
                        agg = (df_r.groupby(grp,dropna=False)
                               .agg(monto_total_haberes=("_t","sum"),descuentos=("_d","sum"),
                                    haber_neto=("_n","sum"),n_personas=("_u",pd.Series.nunique)).reset_index())
                        conn = get_conn()
                        for _,rw in agg.iterrows():
                            conn.execute("""INSERT INTO imputaciones
                                (periodo,resolucion,programa,unidad,descripcion_unidad,tipo_contrato,
                                 tipo_movimiento,calidad_juridica,monto_total_haberes,descuentos,
                                 haber_neto,n_personas,lote_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                                periodo,str(rw.get("Resolucion","")).strip(),str(rw.get("Programa","")).strip(),
                                str(rw.get("Unidad","")).strip(),str(rw.get("Descripcion Unidad","")).strip(),
                                str(rw.get("Tipo de Contrato (Honorarios o Remuneraciones)","")).strip(),
                                str(rw.get("Tipo de Movimiento","")).strip(),str(rw.get("Calidad Juridica","")).strip(),
                                float(rw["monto_total_haberes"]),float(rw["descuentos"]),
                                float(rw["haber_neto"]),int(rw["n_personas"]),h))
                        conn.execute("INSERT INTO lotes_imputados(lote_hash,periodo,n_registros) VALUES(?,?,?)",(h,periodo,len(df_r)))
                        conn.commit(); conn.close()
                        st.success(f"✅ **{per_label(periodo)}** imputado — {len(agg):,} grupos."); st.rerun()
                    except Exception: st.error("Error al imputar."); st.code(traceback.format_exc())
            except Exception: st.error("Error al leer."); st.code(traceback.format_exc())
    with ch:
        st.markdown("**Historial de imputaciones**")
        lts2 = load_lotes()
        if lts2.empty: st.info("Sin imputaciones.")
        else:
            lts2["Período"] = lts2["periodo"].apply(per_label)
            st.dataframe(lts2[["Período","n_registros","created_at"]].rename(columns={"n_registros":"Registros","created_at":"Fecha"}), use_container_width=True, hide_index=True)
            st.markdown("---")
            sb = st.selectbox("Período a eliminar", lts2["periodo"].tolist(), format_func=per_label, key="sb_del")
            if st.button("🗑️ Eliminar período", use_container_width=True):
                row_d = lts2[lts2["periodo"]==sb].iloc[0]; conn=get_conn()
                conn.execute("DELETE FROM imputaciones WHERE lote_hash=?",(row_d["lote_hash"],))
                conn.execute("DELETE FROM lotes_imputados WHERE lote_hash=?",(row_d["lote_hash"],))
                conn.commit(); conn.close(); st.success(f"{per_label(sb)} eliminado."); st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ESTADO MENSUAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_pivot:
    df_imp = load_imp(); df_cc = load_centros()
    if df_imp.empty:
        st.info("📥 Importa rendiciones para ver el estado mensual.")
    else:
        st.markdown("### 📅 Estado Mensual de Ejecución")
        all_res_p = sorted(df_imp["resolucion"].dropna().unique().tolist())
        f_rp = st.multiselect("Resolución(es)", all_res_p, default=all_res_p, key="piv_r")
        df_p = df_imp[df_imp["resolucion"].isin(f_rp)] if f_rp else df_imp.copy()
        pm = build_prog_map(df_p, df_cc)

        periodos_o = sorted(df_p["periodo"].unique().tolist())
        col_lbl = [per_label(p) for p in periodos_o]

        def mk_piv(df_p, col, periodos_o):
            pv = (df_p.groupby(["resolucion","periodo"])[col].sum().reset_index()
                  .pivot(index="resolucion",columns="periodo",values=col).fillna(0))
            for p in periodos_o:
                if p not in pv.columns: pv[p]=0
            pv = pv[periodos_o]; pv["TOTAL"]=pv.sum(axis=1)
            pv.loc["TOTAL GENERAL"]=pv.sum(); return pv

        # Vista 1: Haber Neto
        st.markdown("#### 💵 Haber Neto por Resolución (CLP)")
        pn = mk_piv(df_p,"haber_neto",periodos_o)
        pn_sorted = pn.drop("TOTAL GENERAL").sort_values("TOTAL",ascending=False)
        pn_sorted.loc["TOTAL GENERAL"] = pn.loc["TOTAL GENERAL"]

        hdr = "".join(f"<th>{c}</th>" for c in col_lbl)+"<th class='tc'>TOTAL</th>"
        rows = ""
        for i,r in pn_sorted.iterrows():
            tg = (i=="TOTAL GENERAL"); cls="tr-tot" if tg else ""
            nom = f"<b>{i}</b>" if tg else str(i)
            prog_txt = "" if tg else f"<div class='tprog'>{pm.get(str(i),'')[:70]}</div>"
            cells = "".join(f"<td>$ {fmt_n(r[p])}</td>" for p in periodos_o)
            cells += f"<td class='tc'>$ {fmt_n(r['TOTAL'])}</td>"
            rows += f"<tr class='{cls}'><td class='tleft'>{nom}{prog_txt}</td>{cells}</tr>"

        st.markdown(f'<div style="overflow-x:auto;margin-bottom:1.2rem">'+
            f'<table class="ptbl"><thead><tr><th class="tleft" style="min-width:220px">Resolución · Programa</th>{hdr}</tr></thead>'+
            f'<tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)

        b1=io.BytesIO(); pn_e=pn.copy(); pn_e.columns=col_lbl+["TOTAL"]; pn_e.to_excel(b1,engine="openpyxl")
        st.download_button("📥 Exportar Haber Neto",b1.getvalue(),f"haber_neto_{datetime.now().strftime('%Y%m%d')}.xlsx",use_container_width=True,key="dl1")

        st.markdown("---")

        # Vista 2: Total + Descuentos + Neto
        st.markdown("#### 📋 Vista Completa: Total Haberes · Descuentos · Haber Neto")
        pt  = mk_piv(df_p,"monto_total_haberes",periodos_o)
        pd2 = mk_piv(df_p,"descuentos",periodos_o)
        pn2 = mk_piv(df_p,"haber_neto",periodos_o)
        pn2_sorted = pn2.drop("TOTAL GENERAL").sort_values("TOTAL",ascending=False)
        all_idx = list(pn2_sorted.index) + ["TOTAL GENERAL"]
        hdr2 = "<th>Concepto</th>"+"".join(f"<th>{c}</th>" for c in col_lbl)+"<th class='tc'>TOTAL</th>"

        def rc(pv,res):
            row = pv.loc[res] if res in pv.index else pd.Series(0,index=periodos_o+["TOTAL"])
            return ("".join(f"<td>$ {fmt_n(row.get(p,0))}</td>" for p in periodos_o)+
                    f"<td class='tc'>$ {fmt_n(row.get('TOTAL',0))}</td>")

        rows2=""
        for res in all_idx:
            tg=(res=="TOTAL GENERAL"); cls="tr-tot" if tg else ""
            b_="<b>" if tg else ""; bc="</b>" if tg else ""
            prog_lbl="" if tg else f"<div class='tprog'>{pm.get(str(res),'')[:60]}</div>"
            rows2+=(f"<tr class='{cls}'>"+
                    f"<td rowspan='3' class='tleft' style='vertical-align:middle;border-right:2px solid #1a3050;min-width:150px'>{b_}{res}{bc}{prog_lbl}</td>"+
                    f"<td class='lth'>Suma Monto (Total Haberes)</td>{rc(pt,res)}</tr>"+
                    f"<tr class='{cls}'><td class='ltd'>Suma Descuentos</td>{rc(pd2,res)}</tr>"+
                    f"<tr class='{cls}' style='border-bottom:2px solid #1a3050'><td class='ltn'>Suma Haber Neto</td>{rc(pn2,res)}</tr>")

        st.markdown(f'<div style="overflow-x:auto;margin-bottom:1.2rem">'+
            f'<table class="ptbl"><thead><tr><th class="tleft" style="min-width:150px">Resolución · Programa</th>{hdr2}</tr></thead>'+
            f'<tbody>{rows2}</tbody></table></div>', unsafe_allow_html=True)

        b2=io.BytesIO()
        with pd.ExcelWriter(b2,engine="openpyxl") as wr:
            pt.rename(columns=dict(zip(periodos_o,col_lbl))).to_excel(wr,sheet_name="Total Haberes")
            pd2.rename(columns=dict(zip(periodos_o,col_lbl))).to_excel(wr,sheet_name="Descuentos")
            pn2.rename(columns=dict(zip(periodos_o,col_lbl))).to_excel(wr,sheet_name="Haber Neto")
        st.download_button("📥 Exportar tabla completa",b2.getvalue(),f"estado_mensual_{datetime.now().strftime('%Y%m%d')}.xlsx",use_container_width=True,key="dl2")

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_dash:
    df_imp=load_imp(); df_cc=load_centros()
    if df_imp.empty: st.info("📥 Importa rendiciones para ver el dashboard."); st.stop()
    pd_all=sorted(df_imp["periodo"].unique(),reverse=True)
    td_all=df_imp["tipo_contrato"].dropna().unique().tolist()
    dfc1,dfc2=st.columns([1.5,1.5])
    f_per=dfc1.multiselect("Período(s)",pd_all,default=pd_all,format_func=per_label,key="d_per")
    f_tip=dfc2.multiselect("Tipo contrato",td_all,default=td_all,key="d_tip")
    df_f=df_imp[df_imp["periodo"].isin(f_per)&df_imp["tipo_contrato"].isin(f_tip)]
    if df_f.empty: st.warning("Sin datos."); st.stop()
    pm=build_prog_map(df_f,df_cc)

    tej=df_f["haber_neto"].sum(); thb=df_f["monto_total_haberes"].sum()
    tds=df_f["descuentos"].sum(); tmr=df_cc["marco_clp"].sum() if not df_cc.empty else 0
    pgl=(tej/tmr*100) if tmr>0 else 0
    k1,k2,k3,k4,k5=st.columns(5)
    k1.metric("Haber Neto",fmt_clp(tej)); k2.metric("Total Haberes",fmt_clp(thb))
    k3.metric("Descuentos",fmt_clp(tds)); k4.metric("Marco Presup.",fmt_clp(tmr)); k5.metric("% Ejecución",f"{pgl:.1f}%")
    st.markdown("---")

    st.markdown("### 🏦 Ejecución por Centro de Costo")
    ej=(df_f.groupby("resolucion").agg(ej=("haber_neto","sum"),thb=("monto_total_haberes","sum"),ds=("descuentos","sum")).reset_index().rename(columns={"resolucion":"cc"}))
    ej["cc"]=ej["cc"].astype(str)
    if not df_cc.empty:
        dm=df_cc[["numero","nombre","marco_clp"]].copy(); dm["numero"]=dm["numero"].astype(str)
        ej=ej.merge(dm,left_on="cc",right_on="numero",how="left")
        ej["nombre"]=ej["nombre"].fillna(ej["cc"]); ej["marco_clp"]=ej["marco_clp"].fillna(0)
    else:
        ej["nombre"]=ej["cc"]; ej["marco_clp"]=0
    ej["programa_formal"]=ej["cc"].map(pm).fillna("")
    ej["pct"]=ej.apply(lambda r:r["ej"]/r["marco_clp"]*100 if r["marco_clp"]>0 else 0,axis=1)
    ej=ej.sort_values("ej",ascending=False)

    for _,row in ej.iterrows():
        c=st.columns([.5,1.6,2.5,1.2,1.2,1.5])
        c[0].markdown(f'<div style="font-family:monospace;font-size:.9rem;color:#6b8caf;padding-top:.5rem"><b>{row["cc"]}</b></div>',unsafe_allow_html=True)
        c[1].markdown(f'<div style="font-weight:700;font-size:1rem;padding-top:.4rem">{row.get("nombre",row["cc"])}</div>',unsafe_allow_html=True)
        c[2].markdown(f'<div style="font-size:.8rem;color:#6b8caf;padding-top:.5rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{str(row.get("programa_formal",""))[:70]}</div>',unsafe_allow_html=True)
        c[3].markdown(f'<div style="font-family:monospace;font-size:.95rem;padding-top:.5rem;font-weight:600">{fmt_clp(row["ej"])}</div>',unsafe_allow_html=True)
        c[4].markdown(f'<div style="font-size:.8rem;color:#6b8caf;padding-top:.5rem">Marco:<br>{fmt_clp(row["marco_clp"])}</div>',unsafe_allow_html=True)
        c[5].markdown(semaforo(row["pct"])+pct_bar(row["pct"]),unsafe_allow_html=True)
        st.markdown("<hr style='margin:.3rem 0;opacity:.15'>",unsafe_allow_html=True)

    st.markdown("---")
    cg1,cg2=st.columns(2,gap="medium")
    with cg1:
        top=ej.head(12)
        f1=go.Figure()
        if top["marco_clp"].sum()>0:
            f1.add_bar(name="Marco presupuestario",x=top["cc"],y=top["marco_clp"],
                       marker_color="rgba(0,87,255,0.25)",marker_line_color="#1a73e8",marker_line_width=1.5)
        colors_bar=["#ef4444" if p>=95 else "#f59e0b" if p>=80 else "#1db954" for p in top["pct"]]
        f1.add_bar(name="Haber Neto ejecutado",x=top["cc"],y=top["ej"],marker_color=colors_bar,
                   text=[fmt_clp(v) for v in top["ej"]],textposition="outside",textfont=dict(size=12,color="#f1f5f9"))
        f1.update_layout(**PB,title="Ejecutado vs Marco Presupuestario por Resolución",
                         barmode="overlay",height=400,
                         xaxis=ax(title="Resolución"),yaxis=ax(title="CLP"),
                         legend=dict(orientation="h",y=-0.2,font=dict(size=14)))
        st.plotly_chart(f1,use_container_width=True)
    with cg2:
        ep=(df_f.groupby("programa")["haber_neto"].sum().reset_index().sort_values("haber_neto",ascending=False).head(10))
        pal=["#1a73e8","#1a73e8","#00c8ff","#4a9eff","#1db954","#f59e0b","#004acc","#0077b6","#48cae4","#6b8caf"]
        f2=go.Figure(go.Pie(labels=[str(x)[:52] for x in ep["programa"]],values=ep["haber_neto"],
                            hole=.48,marker_colors=pal[:len(ep)],
                            textinfo="percent+label",textfont=dict(size=12,color="#f1f5f9"),
                            hovertemplate="<b>%{label}</b><br>$ %{value:,.0f}<extra></extra>"))
        f2.update_layout(**PB,title="Distribución Haber Neto por Programa (Top 10)",
                         height=400,legend=dict(font=dict(size=11),orientation="v",x=1.02))
        st.plotly_chart(f2,use_container_width=True)

    st.markdown("### 📈 Evolución Mensual del Gasto")
    ev=(df_f.groupby("periodo").agg(hn=("haber_neto","sum"),thb=("monto_total_haberes","sum"),ds=("descuentos","sum")).reset_index().sort_values("periodo"))
    ev["lbl"]=ev["periodo"].apply(per_label)
    f3=go.Figure()
    f3.add_bar(name="Total Haberes",x=ev["lbl"],y=ev["thb"],marker_color="rgba(0,87,255,0.45)")
    f3.add_bar(name="Descuentos",x=ev["lbl"],y=ev["ds"],marker_color="rgba(255,184,48,0.55)")
    f3.add_scatter(name="Haber Neto",x=ev["lbl"],y=ev["hn"],mode="lines+markers+text",
                   text=[fmt_clp(v) for v in ev["hn"]],textposition="top center",
                   textfont=dict(size=13,color="#4a9eff"),line=dict(color="#4a9eff",width=3),marker=dict(size=12,color="#4a9eff"))
    f3.update_layout(**PB,title="Evolución Mensual: Total Haberes · Descuentos · Haber Neto",
                     barmode="group",height=360,xaxis=ax(title="Período"),yaxis=ax(title="CLP"),
                     legend=dict(orientation="h",y=-0.2,font=dict(size=14)))
    st.plotly_chart(f3,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ANÁLISIS DETALLADO
# ══════════════════════════════════════════════════════════════════════════════
with tab_det:
    df_imp=load_imp(); df_cc=load_centros()
    if df_imp.empty: st.info("Sin datos. Importa rendiciones primero."); st.stop()
    st.markdown("### 🔍 Análisis de Dotación y Costo")
    pd3=sorted(df_imp["periodo"].unique(),reverse=True)
    da1,da2=st.columns(2)
    fp3=da1.multiselect("Período(s)",pd3,default=pd3,format_func=per_label,key="det_p")
    fr3=da2.multiselect("Resolución(es)",sorted(df_imp["resolucion"].dropna().unique()),
                        default=sorted(df_imp["resolucion"].dropna().unique()),key="det_r")
    df_d=df_imp[df_imp["periodo"].isin(fp3)&df_imp["resolucion"].isin(fr3)]
    if df_d.empty: st.warning("Sin datos."); st.stop()
    pm=build_prog_map(df_d,df_cc)

    dd1,dd2=st.columns([1,1.1],gap="medium")
    with dd1:
        st.markdown("##### Personas y Costo: Honorarios vs Remuneraciones")
        ta=(df_d.groupby("tipo_contrato").agg(personas=("n_personas","sum"),costo=("haber_neto","sum")).reset_index())
        ct_c={"HONORARIOS":"#4a9eff","REMUNERACIONES":"#1a73e8"}
        f4=make_subplots(rows=1,cols=2,subplot_titles=["N° Personas por tipo","Haber Neto CLP por tipo"])
        for _,r in ta.iterrows():
            c=ct_c.get(str(r["tipo_contrato"]).upper(),"#6b8caf")
            f4.add_bar(row=1,col=1,x=[r["tipo_contrato"]],y=[r["personas"]],marker_color=c,showlegend=False,
                       text=[fmt_n(r["personas"])],textposition="outside",textfont=dict(size=14,color="#f1f5f9"))
            f4.add_bar(row=1,col=2,x=[r["tipo_contrato"]],y=[r["costo"]],marker_color=c,showlegend=False,
                       text=[fmt_clp(r["costo"])],textposition="outside",textfont=dict(size=12,color="#f1f5f9"))
        f4.update_layout(**PB,height=380,barmode="group",
                         xaxis=ax(),yaxis=ax(title="Personas"),
                         xaxis2=ax(),yaxis2=ax(title="CLP"))
        f4.update_annotations(font_size=15,font_color="#94a3b8")
        st.plotly_chart(f4,use_container_width=True)
        ta["Costo CLP"]=ta["costo"].apply(fmt_clp)
        ta["Prom/persona"]=ta.apply(lambda r:fmt_clp(r["costo"]/r["personas"]) if r["personas"]>0 else "—",axis=1)
        st.dataframe(ta[["tipo_contrato","personas","Costo CLP","Prom/persona"]].rename(columns={"tipo_contrato":"Tipo","personas":"Personas"}),use_container_width=True,hide_index=True)

    with dd2:
        st.markdown("##### Descomposición por Unidad de Desempeño (Top 15)")
        ua=(df_d.groupby(["descripcion_unidad","tipo_contrato"]).agg(costo=("haber_neto","sum")).reset_index().sort_values("costo",ascending=False).head(15))
        f5=px.bar(ua,x="costo",y="descripcion_unidad",color="tipo_contrato",orientation="h",
                  color_discrete_map={"HONORARIOS":"#4a9eff","REMUNERACIONES":"#1a73e8"},
                  labels={"costo":"Haber Neto CLP","descripcion_unidad":"Unidad","tipo_contrato":"Tipo"},
                  barmode="stack")
        f5.update_layout(**PB,title="Haber Neto por Unidad de Desempeño",height=480,
                         xaxis=ax(title="Haber Neto CLP"),yaxis=ax(title=""),
                         legend=dict(orientation="h",y=-0.1,font=dict(size=14),title_text=""))
        f5.update_yaxes(autorange="reversed",tickfont=dict(size=13))
        st.plotly_chart(f5,use_container_width=True)

    st.markdown("---")
    # Tabla descomposición orden: Resolución → Programa → Movimiento → Tipo (igual tabla dinámica imagen 9)
    st.markdown("### 📋 Descomposición: Resolución · Programa · Movimiento · Tipo de Contrato")
    st.caption("Orden equivalente a tabla dinámica Excel. Un nombre formal de programa por resolución.")
    dg=(df_d.groupby(["resolucion","programa","tipo_movimiento","tipo_contrato"])
        .agg(personas=("n_personas","sum"),monto_total_haberes=("monto_total_haberes","sum"),
             descuentos=("descuentos","sum"),haber_neto=("haber_neto","sum"))
        .reset_index())
    # Ordenar numéricamente la resolución
    dg["_res_sort"]=pd.to_numeric(dg["resolucion"],errors="coerce").fillna(9999)
    dg=dg.sort_values(["_res_sort","programa","tipo_movimiento"]).drop(columns=["_res_sort"])
    dg["Suma Monto (Total Haberes)"]=dg["monto_total_haberes"].apply(fmt_clp)
    dg["Suma Descuentos"]=dg["descuentos"].apply(fmt_clp)
    dg["Suma Total Haberes Netos"]=dg["haber_neto"].apply(fmt_clp)
    dg_show=dg[["resolucion","programa","tipo_movimiento","tipo_contrato","personas",
                "Suma Monto (Total Haberes)","Suma Descuentos","Suma Total Haberes Netos"]].rename(columns={
        "resolucion":"Resolución","programa":"Nombre Programa","tipo_movimiento":"Movimiento",
        "tipo_contrato":"Tipo","personas":"Personas"})
    st.dataframe(dg_show,use_container_width=True,hide_index=True,
                 column_config={"Nombre Programa":st.column_config.TextColumn(width="large"),
                                "Resolución":st.column_config.TextColumn(width="small")})

    st.markdown("---")
    st.markdown("### 👥 Costo por Calidad Jurídica (homologado)")
    cj1c,cj2c=st.columns(2,gap="medium")
    with cj1c:
        cj=(df_d.groupby("calidad_juridica").agg(personas=("n_personas","sum"),costo=("haber_neto","sum")).reset_index().sort_values("costo",ascending=False))
        cj["prom"]=cj.apply(lambda r:r["costo"]/r["personas"] if r["personas"]>0 else 0,axis=1)
        f6=make_subplots(specs=[[{"secondary_y":True}]])
        f6.add_bar(x=cj["calidad_juridica"],y=cj["costo"],name="Costo total",marker_color="#1a73e8",secondary_y=False,
                   text=[fmt_clp(v) for v in cj["costo"]],textposition="outside",textfont=dict(size=12,color="#f1f5f9"))
        f6.add_scatter(x=cj["calidad_juridica"],y=cj["prom"],name="Costo prom/persona",
                       mode="lines+markers+text",text=[fmt_clp(v) for v in cj["prom"]],
                       textposition="top center",textfont=dict(size=11,color="#4a9eff"),
                       marker=dict(size=11,color="#4a9eff"),line=dict(color="#4a9eff",dash="dot",width=2.5),secondary_y=True)
        f6.update_layout(**PB,title="Costo total y Promedio por persona según Calidad Jurídica",
                         height=400,legend=dict(orientation="h",y=-0.2,font=dict(size=14)))
        f6.update_xaxes(gridcolor="rgba(255,255,255,.06)",tickfont=dict(size=13,color="#475569"))
        f6.update_yaxes(title_text="Total CLP",gridcolor="rgba(255,255,255,.06)",tickfont=dict(size=13),secondary_y=False)
        f6.update_yaxes(title_text="Promedio CLP/persona",gridcolor="rgba(0,0,0,0)",tickfont=dict(size=13),secondary_y=True)
        st.plotly_chart(f6,use_container_width=True)
    with cj2c:
        cj["Total CLP"]=cj["costo"].apply(fmt_clp); cj["Prom/persona CLP"]=cj["prom"].apply(fmt_clp)
        st.dataframe(cj[["calidad_juridica","personas","Total CLP","Prom/persona CLP"]].rename(columns={"calidad_juridica":"Calidad Jurídica","personas":"Personas"}),use_container_width=True,hide_index=True)

    st.markdown("---")
    if st.button("📥 Exportar análisis detallado",use_container_width=True):
        bd=io.BytesIO()
        with pd.ExcelWriter(bd,engine="openpyxl") as wr:
            dg.to_excel(wr,sheet_name="Descomposición",index=False)
            ta.to_excel(wr,sheet_name="Tipo Contrato",index=False)
            cj[["calidad_juridica","personas","costo","prom"]].to_excel(wr,sheet_name="Calidad Jurídica",index=False)
        st.download_button("⬇️ Descargar Excel",bd.getvalue(),
                           f"analisis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True,key="dl_det")

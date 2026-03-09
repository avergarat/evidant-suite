# -*- coding: utf-8 -*-
"""
Repositorio RR.HH. - Evidant Suite DAP SSMC
MEJORAS v2:
  - Contraste buscadores arreglado (texto visible en inputs oscuros)
  - Edicion de campos en ficha de funcionario (con registro en historial)
  - Dashboard: grafico CC con Total Haberes en CLP, graficos por UNIDAD y PLANTA
"""
import sys, os, io, traceback
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ev_design

st.set_page_config(page_title="Repositorio RR.HH. - Evidant", page_icon="D", layout="wide")

ev_design.render(
    current="rrhh",
    page_title="Repositorio RR.HH.",
    page_sub="Base de datos persistente de contratos · Historial de cambios · Fichas editables",
    breadcrumb="Gestión Recurso Humano",
    icon="🗄️",
)
# ── CSS con fix de contraste en inputs ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Space+Grotesk:wght@400;500;600&display=swap');
:root{
  --ev-bg:#050d1a;--ev-card:#0d1e35;--ev-border:#1a3050;
  --ev-blue-1:#0057ff;--ev-blue-2:#0098ff;--ev-accent:#00e5ff;
  --ev-text:#e8f0fe;--ev-muted:#6b8caf;--ev-success:#00e6a0;
  --font-head:'Plus Jakarta Sans',sans-serif;--font-body:'Space Grotesk',sans-serif;
}
html,body,[class*="css"]{background-color:var(--ev-bg)!important;color:var(--ev-text)!important;font-family:var(--font-body)!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#060f1e 0%,#081424 100%)!important;border-right:1px solid var(--ev-border)!important;}
[data-testid="stSidebar"] *{color:var(--ev-text)!important;font-family:var(--font-body)!important;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding-top:1.5rem!important;}
.stButton>button{background:linear-gradient(135deg,var(--ev-blue-1),var(--ev-blue-2))!important;color:white!important;border:none!important;border-radius:8px!important;font-weight:600!important;}
.stButton>button:hover{background:linear-gradient(135deg,var(--ev-blue-2),var(--ev-accent))!important;box-shadow:0 0 20px rgba(0,152,255,0.4)!important;}
hr{border-color:var(--ev-border)!important;}
.stDataFrame{border-radius:10px!important;overflow:hidden!important;}
.stSuccess{background:rgba(0,230,160,0.1)!important;}
.stWarning{background:rgba(255,184,48,0.1)!important;}
.stError{background:rgba(255,80,80,0.1)!important;}
.stInfo{background:rgba(0,152,255,0.08)!important;border-color:var(--ev-blue-2)!important;}
[data-testid="stMetric"]{background:var(--ev-card)!important;border:1px solid var(--ev-border)!important;border-radius:12px!important;padding:1rem!important;}
[data-testid="stMetricValue"]{color:var(--ev-accent)!important;font-family:var(--font-head)!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--ev-card)!important;border-radius:8px!important;}
.stTabs [data-baseweb="tab"]{color:var(--ev-muted)!important;}
.stTabs [aria-selected="true"]{color:var(--ev-accent)!important;border-bottom:2px solid var(--ev-accent)!important;}

/* FIX CONTRASTE INPUTS - texto blanco visible sobre fondo oscuro */
input[type="text"], input[type="number"], input[type="search"],
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-baseweb="input"] input {
  color: #e8f0fe !important;
  background: #0d1e35 !important;
  border-color: #1a3050 !important;
  caret-color: #00e5ff !important;
}
textarea,
[data-testid="stTextArea"] textarea,
[data-baseweb="textarea"] textarea {
  color: #e8f0fe !important;
  background: #0d1e35 !important;
  border-color: #1a3050 !important;
  caret-color: #00e5ff !important;
}
input::placeholder, textarea::placeholder { color: #3d5a7a !important; }
[data-testid="stSelectbox"] > div > div,
[data-baseweb="select"] > div {
  background: #0d1e35 !important;
  border-color: #1a3050 !important;
  color: #e8f0fe !important;
}
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
[data-baseweb="option"],
[role="option"] { color: #e8f0fe !important; background: #0d1e35 !important; }
[data-baseweb="popover"] { background: #0d1e35 !important; border: 1px solid #1a3050 !important; }

/* Estilo campos editables en ficha */
.campo-edit-row {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.3rem 0; border-bottom: 1px solid #0d1e35;
}
</style>
""", unsafe_allow_html=True)

# ── DB import ────────────────────────────────────────────────────────────────
try:
    from repositorio.db import (
        init_db, get_todos, get_contrato, get_historial,
        update_notas, update_campo, get_stats, get_distinct, DB_PATH
    )
    init_db()
    _db_ok = True
except Exception:
    _db_ok = False
    _db_err = traceback.format_exc()

if not _db_ok:
    st.error("No se pudo inicializar la base de datos.")
    st.code(_db_err)
    st.stop()

# ── Aliases locales a ev_design (punto único de verdad) ──────────────────────
_ev_bar        = ev_design.ev_bar
_ev_table_html = ev_design.ev_table_html


tab_dash, tab_listado, tab_ficha, tab_export = st.tabs([
    "Dashboard", "Listado de Contratos", "Ficha de Funcionario", "Exportar"
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 - DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
with tab_dash:
    stats = get_stats()

    if stats["total_contratos"] == 0:
        st.info("El repositorio esta vacio. Ejecuta el Paso 1: Consolidacion para poblar la base de datos automaticamente.")
    else:
        # KPIs
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Funcionarios unicos",  stats["total_funcionarios"])
        c2.metric("Contratos activos",    stats["total_contratos"])
        c3.metric("Contratos inactivos",  stats["inactivos"])
        c4.metric("Leyes en uso",         len([x for x in stats["por_ley"] if x["LEY_AFECTO"]]))
        st.divider()

        # Helper para parsear montos CLP (pueden venir como texto con puntos)
        def parse_monto(v):
            try:
                s = str(v).replace(".", "").replace(",", ".").strip()
                return float(s)
            except Exception:
                return 0.0

        # ── Graficos calidad y ley ─────────────────────────────────────────
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Distribucion por Calidad Juridica**")
            if stats["por_calidad"]:
                df_cal = pd.DataFrame(stats["por_calidad"]).rename(columns={"CALIDAD_JURIDICA":"Calidad","n":"Contratos"})
                df_cal = df_cal[df_cal["Calidad"] != ""].sort_values("Contratos", ascending=False)
                st.plotly_chart(_ev_bar(df_cal["Calidad"], df_cal["Contratos"]), use_container_width=True)
        with col_b:
            st.markdown("**Distribucion por Ley Afecto**")
            if stats["por_ley"]:
                df_ley = pd.DataFrame(stats["por_ley"]).rename(columns={"LEY_AFECTO":"Ley","n":"Contratos"})
                df_ley = df_ley[df_ley["Ley"] != ""].sort_values("Contratos", ascending=False)
                st.plotly_chart(_ev_bar(df_ley["Ley"], df_ley["Contratos"]), use_container_width=True)

        st.divider()

        # ── Centro de Costo con Total Haberes ─────────────────────────────
        st.markdown("**Total Haberes por Centro de Costo (Top 20, CLP)**")
        todos_activos = get_todos(solo_activos=True)
        if todos_activos:
            df_all = pd.DataFrame(todos_activos)
            df_all["_monto"] = df_all.get("TOTAL_HABER", pd.Series([0]*len(df_all))).apply(parse_monto)

            # Grafico por CC ordenado por monto (str para eje categórico en Plotly)
            df_cc_monto = (df_all[df_all["CENTRO_DE_COSTO"].astype(str).str.strip() != ""]
                           .copy()
                           .assign(_cc=lambda d: d["CENTRO_DE_COSTO"].astype(str).str.strip())
                           .groupby("_cc")["_monto"].sum()
                           .sort_values(ascending=False)
                           .head(20)
                           .reset_index())
            df_cc_monto.columns = ["Centro de Costo", "Total Haberes CLP"]
            df_cc_monto["Total Haberes (formato)"] = df_cc_monto["Total Haberes CLP"].apply(
                lambda x: f"$ {x:,.0f}".replace(",", "."))

            # Mostrar tabla + grafico
            col_g, col_t = st.columns([2, 1])
            with col_g:
                if not df_cc_monto.empty:
                    st.plotly_chart(
                        _ev_bar(df_cc_monto["Centro de Costo"], df_cc_monto["Total Haberes CLP"],
                                fmt_clp=True, height=380),
                        use_container_width=True,
                    )
            with col_t:
                st.markdown(
                    _ev_table_html(
                        df_cc_monto[["Centro de Costo", "Total Haberes CLP"]],
                        fmt_clp_cols=["Total Haberes CLP"],
                    ),
                    unsafe_allow_html=True,
                )

            st.divider()

            # ── Por UNIDAD ─────────────────────────────────────────────────
            st.markdown("**Distribucion por Unidad — Personas y Total Haberes**")
            if "UNIDAD" in df_all.columns:
                df_unidad = (df_all[df_all["UNIDAD"].astype(str).str.strip() != ""]
                             .groupby("UNIDAD")
                             .agg(Personas=("RUT_DV","nunique"), Total_Haberes=("_monto","sum"))
                             .sort_values("Total_Haberes", ascending=False)
                             .head(25)
                             .reset_index())
                df_unidad["Total Haberes (CLP)"] = df_unidad["Total_Haberes"].apply(
                    lambda x: f"$ {x:,.0f}".replace(",", "."))

                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    st.caption("Personas por Unidad")
                    st.plotly_chart(
                        _ev_bar(df_unidad["UNIDAD"], df_unidad["Personas"]),
                        use_container_width=True,
                    )
                with col_u2:
                    st.caption("Total Haberes CLP por Unidad")
                    st.plotly_chart(
                        _ev_bar(df_unidad["UNIDAD"], df_unidad["Total_Haberes"], fmt_clp=True),
                        use_container_width=True,
                    )

                st.markdown(
                    _ev_table_html(
                        df_unidad[["UNIDAD", "Personas", "Total_Haberes"]].rename(
                            columns={"UNIDAD": "Unidad", "Total_Haberes": "Total Haberes CLP"}
                        ),
                        fmt_clp_cols=["Total Haberes CLP"],
                    ),
                    unsafe_allow_html=True,
                )

            st.divider()

            # ── Por PLANTA ─────────────────────────────────────────────────
            st.markdown("**Distribucion por Planta**")
            if "PLANTA" in df_all.columns:
                df_planta = (df_all[df_all["PLANTA"].astype(str).str.strip() != ""]
                             .groupby("PLANTA")
                             .agg(Personas=("RUT_DV","nunique"), Total_Haberes=("_monto","sum"))
                             .sort_values("Total_Haberes", ascending=False)
                             .reset_index())
                df_planta["Total Haberes (CLP)"] = df_planta["Total_Haberes"].apply(
                    lambda x: f"$ {x:,.0f}".replace(",", "."))

                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    st.caption("Personas por Planta")
                    st.plotly_chart(
                        _ev_bar(df_planta["PLANTA"], df_planta["Personas"]),
                        use_container_width=True,
                    )
                with col_p2:
                    st.caption("Total Haberes CLP por Planta")
                    st.plotly_chart(
                        _ev_bar(df_planta["PLANTA"], df_planta["Total_Haberes"], fmt_clp=True),
                        use_container_width=True,
                    )

                st.markdown(
                    _ev_table_html(
                        df_planta[["PLANTA", "Personas", "Total_Haberes"]].rename(
                            columns={"PLANTA": "Planta", "Total_Haberes": "Total Haberes CLP"}
                        ),
                        fmt_clp_cols=["Total Haberes CLP"],
                    ),
                    unsafe_allow_html=True,
                )

        st.caption(f"Base de datos: `{DB_PATH}`")


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 - LISTADO
# ════════════════════════════════════════════════════════════════════════════
with tab_listado:
    st.markdown("### Filtros")
    f1, f2, f3 = st.columns(3)
    with f1:
        f_nombre = st.text_input("Nombre", placeholder="Buscar por nombre...", key="f_nombre")
        f_rut    = st.text_input("RUT-DV",  placeholder="Ej: 12345678-9", key="f_rut")
    with f2:
        leyes_opts   = ["(Todas)"] + get_distinct("LEY_AFECTO")
        calidad_opts = ["(Todas)"] + get_distinct("CALIDAD_JURIDICA")
        f_ley     = st.selectbox("Ley Afecto",       leyes_opts,   key="f_ley")
        f_calidad = st.selectbox("Calidad Juridica", calidad_opts, key="f_calidad")
    with f3:
        cc_opts   = ["(Todos)"] + get_distinct("CENTRO_DE_COSTO")
        f_cc      = st.selectbox("Centro de Costo", cc_opts, key="f_cc")
        f_activos = st.checkbox("Solo activos", value=True, key="f_activos")

    registros = get_todos(
        solo_activos=f_activos,
        filtro_nombre=f_nombre,
        filtro_rut=f_rut,
        filtro_cc=f_cc if f_cc != "(Todos)" else "",
        filtro_ley=f_ley if f_ley != "(Todas)" else "",
        filtro_calidad=f_calidad if f_calidad != "(Todas)" else "",
    )

    st.markdown(f"**{len(registros):,} contratos encontrados**")

    if registros:
        cols_vis = ["ID_CONTRATO","RUT_DV","NOMBRE","CENTRO_DE_COSTO","PROGRAMA",
                    "CALIDAD_JURIDICA","HORAS_GRADOS","LEY_AFECTO","ESTAB",
                    "CARGO","FECHA_ULTIMO_UPDATE","ACTIVO"]
        df_list = pd.DataFrame(registros)[[c for c in cols_vis if c in pd.DataFrame(registros).columns]]
        df_list["ACTIVO"] = df_list["ACTIVO"].map({1:"Activo",0:"Inactivo"})

        st.dataframe(df_list, use_container_width=True, hide_index=True,
            column_config={
                "ID_CONTRATO":        st.column_config.TextColumn("ID Contrato",     width="medium"),
                "RUT_DV":             st.column_config.TextColumn("RUT-DV"),
                "NOMBRE":             st.column_config.TextColumn("Nombre",           width="large"),
                "CENTRO_DE_COSTO":    st.column_config.TextColumn("C. Costo"),
                "PROGRAMA":           st.column_config.TextColumn("Programa",         width="large"),
                "CALIDAD_JURIDICA":   st.column_config.TextColumn("Calidad Juridica"),
                "HORAS_GRADOS":       st.column_config.TextColumn("Horas/Grado"),
                "LEY_AFECTO":         st.column_config.TextColumn("Ley"),
                "ESTAB":              st.column_config.TextColumn("Establecimiento"),
                "CARGO":              st.column_config.TextColumn("Cargo"),
                "FECHA_ULTIMO_UPDATE":st.column_config.TextColumn("Ultimo update"),
                "ACTIVO":             st.column_config.TextColumn("Estado",           width="small"),
            })

        st.markdown("---")
        st.markdown("**Selecciona un contrato para abrir la ficha:**")
        ids_disp = [r["ID_CONTRATO"] for r in registros]
        nom_map  = {r["ID_CONTRATO"]: f"{r['NOMBRE']} - {r['RUT_DV']} ({r['HORAS_GRADOS']}h - {r['LEY_AFECTO']})" for r in registros}
        id_sel   = st.selectbox("Contrato", options=ids_disp, format_func=lambda x: nom_map.get(x,x), key="sel_listado")
        if id_sel:
            st.session_state["ficha_id"] = id_sel
            st.info(f"ID seleccionado: `{id_sel}` - Ve a la pestana **Ficha de Funcionario**.")
    else:
        st.info("No se encontraron contratos con los filtros aplicados.")


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 - FICHA DE FUNCIONARIO (con edicion de campos)
# ════════════════════════════════════════════════════════════════════════════
with tab_ficha:
    st.markdown("### Ficha de Contrato")
    id_input = st.text_input("ID de Contrato", value=st.session_state.get("ficha_id",""),
                              placeholder="EVD-XXXXXXXXXXXX", key="ficha_id_input")

    if id_input:
        datos = get_contrato(id_input.strip())
        if datos is None:
            st.error(f"No se encontro el contrato `{id_input}`")
        else:
            activo_badge = "ACTIVO" if datos.get("ACTIVO")==1 else "INACTIVO"
            color_badge  = "#00e6a0" if datos.get("ACTIVO")==1 else "#ff5050"
            st.markdown(f'''<div style="background:#0d1e35;border:1px solid #1a3050;
border-left:4px solid #00e5ff;border-radius:10px;padding:1rem 1.4rem;margin-bottom:1rem;">
<div style="font-size:1.2rem;font-weight:700;color:#e8f0fe;">{datos.get("NOMBRE","")}</div>
<div style="color:#6b8caf;font-size:0.85rem;margin-top:0.3rem;">
{datos.get("RUT_DV","—")} - {datos.get("LEY_AFECTO","—")} - {datos.get("HORAS_GRADOS","—")} horas -
{datos.get("CALIDAD_JURIDICA","—")} -
<strong style="color:{color_badge};">{activo_badge}</strong>
</div>
<div style="font-size:0.72rem;color:#3d5a7a;margin-top:0.4rem;">
ID: {datos.get("ID_CONTRATO","—")} - Primer registro: {datos.get("FECHA_PRIMER_REGISTRO","—")} -
Ultimo update: {datos.get("FECHA_ULTIMO_UPDATE","—")}
</div></div>''', unsafe_allow_html=True)

            # ── Tabs dentro de la ficha ────────────────────────────────────
            ft_ver, ft_edit, ft_hist = st.tabs(["Ver datos", "Editar campos", "Historial de cambios"])

            # ── Subtab VER ─────────────────────────────────────────────────
            with ft_ver:
                sec1, sec2 = st.columns(2)
                with sec1:
                    st.markdown("**Datos Contractuales**")
                    for label, campo in [
                        ("Centro de Costo","CENTRO_DE_COSTO"),("Programa","PROGRAMA"),
                        ("SIRH (CC origen)","SIRH"),("Calidad Juridica","CALIDAD_JURIDICA"),
                        ("Horas / Grado","HORAS_GRADOS"),("Planta","PLANTA"),("Cargo","CARGO"),
                        ("Unidad","UNIDAD"),("Establecimiento","ESTAB"),("Ley Afecto","LEY_AFECTO"),
                        ("Nivel","NIVEL"),("Contrato Corto","CONTRATO_CORTO"),("Vigencia","VIGENCIA"),
                        ("Tipo Turno","TIPO_TURNO"),("Afecto a Turno","AFECTO_A_TURNO"),
                        ("Derecho Bonif. Turno","DERECHO_BONIF_TURNO"),("Origen archivo","CONSOLIDADO_ORIGEN"),
                    ]:
                        v = datos.get(campo,"")
                        st.markdown(f"**{label}:** {v or chr(8212)}")
                with sec2:
                    st.markdown("**Datos Previsionales y Personales**")
                    for label, campo in [
                        ("AFP","AFP"),("AFP sin Seguro","AFP_SIN_SEGURO"),("ISAPRE","ISAPRE"),
                        ("Banco","BANCO"),("Cuenta Corriente","CUENTA_CORRIENTE"),
                        ("Dias Trabajados","DIAS_TRABAJADOS"),("Cargas Familiares","CARGAS_FAMILIARES"),
                        ("Cargas Fam. Duplo","CARGAS_FAMILIARES_DUPLO"),
                        ("Asig. Familiar","ASIGNACION_FAMILIAR"),
                        ("Fecha Nacimiento","FECHA_NACIMIENTO"),("Sexo","SEXO"),
                        ("Experiencia Calif.","EXPERIENCIA_CALIFICADA"),
                        ("Bienio/Trienio","BIENIO_TRIENIO"),("CORR","CORR"),
                        ("CORR. Pago","CORR_PAGO"),("Num. Corr. Interno","NUM_CORR_INTERNO"),
                        ("Total Haber","TOTAL_HABER"),
                    ]:
                        v = datos.get(campo,"")
                        st.markdown(f"**{label}:** {v or chr(8212)}")

                st.markdown("---")
                st.markdown("**Notas del Referente Tecnico**")
                notas_act = datos.get("NOTAS_REFERENTE","") or ""
                notas_new = st.text_area("Notas (editable)", value=notas_act, height=100,
                                         key=f"notas_{id_input}")
                if st.button("Guardar notas", key=f"save_notas_{id_input}"):
                    update_notas(id_input.strip(), notas_new)
                    st.success("Notas guardadas.")

                obs1 = datos.get("OBSERVACION","") or ""
                obs2 = datos.get("OBS_HOJA_VIDA","") or ""
                if obs1 or obs2:
                    st.markdown("**Observaciones SIRH**")
                    if obs1: st.warning(f"Observacion: {obs1}")
                    if obs2: st.warning(f"Obs. Hoja Vida: {obs2}")

                st.markdown("---")
                st.markdown(f"**Todos los contratos de {datos.get('RUT_DV','')}**")
                mismos_rut = get_todos(solo_activos=False, filtro_rut=datos.get("RUT_DV",""))
                if len(mismos_rut) > 1:
                    df_rut = pd.DataFrame(mismos_rut)[
                        ["ID_CONTRATO","HORAS_GRADOS","CENTRO_DE_COSTO","PROGRAMA",
                         "LEY_AFECTO","CALIDAD_JURIDICA","ACTIVO"]]
                    df_rut["ACTIVO"] = df_rut["ACTIVO"].map({1:"Activo",0:"Inactivo"})
                    st.dataframe(df_rut, use_container_width=True, hide_index=True)
                else:
                    st.caption("Contrato unico para este RUT.")

            # ── Subtab EDITAR ──────────────────────────────────────────────
            with ft_edit:
                st.markdown("Edita los campos contractuales. Cada cambio queda registrado en el historial.")
                st.warning("Los campos previsionales (AFP, ISAPRE, banco, etc.) provienen del SIRH y no deben editarse manualmente.")

                # Campos editables con sus etiquetas
                CAMPOS_EDIT = [
                    ("Centro de Costo",       "CENTRO_DE_COSTO"),
                    ("Programa",              "PROGRAMA"),
                    ("Calidad Juridica",      "CALIDAD_JURIDICA"),
                    ("Horas / Grado",         "HORAS_GRADOS"),
                    ("Planta",                "PLANTA"),
                    ("Cargo",                 "CARGO"),
                    ("Unidad",                "UNIDAD"),
                    ("Establecimiento",       "ESTAB"),
                    ("Ley Afecto",            "LEY_AFECTO"),
                    ("Nivel",                 "NIVEL"),
                    ("Contrato Corto",        "CONTRATO_CORTO"),
                    ("Vigencia",              "VIGENCIA"),
                    ("Tipo Turno",            "TIPO_TURNO"),
                    ("Afecto a Turno",        "AFECTO_A_TURNO"),
                    ("Derecho Bonif. Turno",  "DERECHO_BONIF_TURNO"),
                ]

                edited_vals = {}
                for label, campo in CAMPOS_EDIT:
                    val_actual = str(datos.get(campo,"") or "")
                    col_lbl, col_inp = st.columns([1, 2])
                    with col_lbl:
                        st.markdown(f"**{label}**")
                        st.caption(campo)
                    with col_inp:
                        nuevo = st.text_input(f"__{campo}", value=val_actual,
                                              key=f"edit_{id_input}_{campo}",
                                              label_visibility="collapsed")
                    edited_vals[campo] = (val_actual, nuevo)

                st.markdown("---")
                motivo = st.text_input("Motivo del cambio (opcional)",
                                       placeholder="Ej: Correccion de centro de costo por reasignacion presupuestaria",
                                       key=f"motivo_{id_input}")

                if st.button("Guardar todos los cambios", type="primary", key=f"save_edit_{id_input}"):
                    cambios = [(c, v_ant, v_new) for c,(v_ant,v_new) in edited_vals.items() if v_ant.strip() != v_new.strip()]
                    if not cambios:
                        st.info("No hay cambios para guardar.")
                    else:
                        ok_count = 0
                        for campo, v_ant, v_new in cambios:
                            try:
                                update_campo(id_input.strip(), campo, v_new, motivo or "Edicion manual desde ficha")
                                ok_count += 1
                            except Exception as e:
                                st.error(f"Error guardando {campo}: {e}")
                        if ok_count > 0:
                            st.success(f"{ok_count} campo(s) actualizados correctamente. Recarga la pagina para ver los cambios reflejados.")
                            # Limpiar cache session para forzar recarga
                            if "ficha_id" in st.session_state:
                                st.session_state["ficha_id"] = id_input.strip()

            # ── Subtab HISTORIAL ───────────────────────────────────────────
            with ft_hist:
                historial = get_historial(id_input.strip())
                if historial:
                    df_hist = pd.DataFrame(historial)
                    cols_h = [c for c in ["fecha","campo","valor_anterior","valor_nuevo","consolidado","motivo"] if c in df_hist.columns]
                    df_hist = df_hist[cols_h]
                    rename_h = {"fecha":"Fecha","campo":"Campo","valor_anterior":"Valor anterior",
                                "valor_nuevo":"Valor nuevo","consolidado":"Consolidado origen","motivo":"Motivo"}
                    df_hist.rename(columns={k:v for k,v in rename_h.items() if k in df_hist.columns}, inplace=True)
                    st.dataframe(df_hist, use_container_width=True, hide_index=True)
                else:
                    st.caption("Sin cambios registrados - este contrato no ha variado entre consolidados.")
    else:
        st.info("Ingresa un ID de contrato, o selecciona uno desde la pestana Listado de Contratos.")


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 - EXPORTAR
# ════════════════════════════════════════════════════════════════════════════
with tab_export:
    st.markdown("### Exportar Repositorio")
    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.markdown("**Exportar a Excel**")
        solo_act = st.checkbox("Solo contratos activos", value=True, key="exp_activos")
        if st.button("Generar Excel del Repositorio", use_container_width=True):
            registros_exp = get_todos(solo_activos=solo_act)
            if registros_exp:
                df_exp = pd.DataFrame(registros_exp)
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                    df_exp.to_excel(writer, sheet_name="REPOSITORIO_RRHH", index=False)
                st.download_button("Descargar REPOSITORIO_RRHH.xlsx", data=buf.getvalue(),
                    file_name="REPOSITORIO_RRHH.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
                st.success(f"{len(registros_exp):,} contratos listos para descargar.")
            else:
                st.warning("No hay contratos en el repositorio.")

    with col_e2:
        st.markdown("**Resumen por Funcionario (multi-contrato)**")
        st.caption("Agrupa todos los contratos por RUT - muestra horas totales y distribucion.")
        if st.button("Generar Resumen por Funcionario", use_container_width=True):
            registros_res = get_todos(solo_activos=True)
            if registros_res:
                df_res = pd.DataFrame(registros_res)
                def parse_h(v):
                    try: return float(str(v).replace(",",".").strip())
                    except Exception: return 0.0
                df_res["_horas"] = df_res["HORAS_GRADOS"].apply(parse_h)
                resumen = df_res.groupby("RUT_DV").agg(
                    NOMBRE=("NOMBRE","first"),
                    N_CONTRATOS=("ID_CONTRATO","count"),
                    HORAS_TOTALES=("_horas","sum"),
                    LEYES=("LEY_AFECTO", lambda x: " / ".join(sorted(set(x)))),
                    CALIDADES=("CALIDAD_JURIDICA", lambda x: " / ".join(sorted(set(x)))),
                    CENTROS=("CENTRO_DE_COSTO", lambda x: " / ".join(sorted(set(x)))),
                    PROGRAMAS=("PROGRAMA", lambda x: " / ".join(sorted(set(x)))),
                ).reset_index()
                buf2 = io.BytesIO()
                with pd.ExcelWriter(buf2, engine="openpyxl") as writer:
                    resumen.to_excel(writer, sheet_name="RESUMEN_FUNCIONARIOS", index=False)
                st.download_button("Descargar RESUMEN_FUNCIONARIOS.xlsx", data=buf2.getvalue(),
                    file_name="RESUMEN_FUNCIONARIOS.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
                st.success(f"{len(resumen):,} funcionarios unicos.")
            else:
                st.warning("No hay contratos activos.")

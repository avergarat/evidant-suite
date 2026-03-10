# -*- coding: utf-8 -*-
"""
Página — Gestión de Dotación
Repositorio persistente de contratos vigentes · Alertas SIRH · Filtros y descarga
"""

import sys, os, io, re, json
import streamlit as st
import pandas as pd
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ev_design

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES — nombres de columnas SIRH
# ══════════════════════════════════════════════════════════════════════════════
COL_RUT     = "Rut"
COL_DV      = "Dv"
COL_NOMBRE  = "Nombre Funcionario"
COL_CORREL  = "Correlativo"
COL_CALIDAD = "Descripción Calidad Jurídica"
COL_INICIO  = "Fecha Inicio Contrato"
COL_TERMINO = "Fecha Término Contrato"
COL_ALEJ    = "Fecha Alejamiento"
COL_HORAS   = "Número horas"
COL_TITULO  = "Título"
COL_PLANTA  = "Correl. Planta"
COL_LEY     = "Ley"
COL_CC      = "C. Costo"

_NULL_STRS  = {"00/00/0000", "", "nan", "nat", "none", "s/d", "sd", "NaT"}
_MAX_DATE   = pd.Timestamp("2999-12-31")
_AÑO_VIG   = 2026                                 # año de vigencia objetivo
_VIG_DESDE = pd.Timestamp(f"{_AÑO_VIG}-01-01")
_VIG_HASTA = pd.Timestamp(f"{_AÑO_VIG}-12-31")

ev_design.render(
    current   = "dotacion",
    page_title= "Gestión de Dotación",
    page_sub  = f"Repositorio persistente · Contratos vigentes {_AÑO_VIG} · Alertas SIRH",
    icon      = "👥",
)

# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DATOS — SQLite persistente
# ══════════════════════════════════════════════════════════════════════════════
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB   = os.path.join(_ROOT, "dotacion.db")


def _get_conn():
    c = sqlite3.connect(_DB, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL")
    return c


def _norm(col: str) -> str:
    """Normaliza nombre de columna para SQLite."""
    return re.sub(r"[^a-z0-9]", "_", str(col).lower()).strip("_")


def _save(df: pd.DataFrame, filas_originales: int = 0):
    orig_cols  = list(df.columns)
    norm_cols  = [_norm(c) for c in orig_cols]
    col_map    = dict(zip(norm_cols, orig_cols))

    conn = _get_conn()
    # Mapa de columnas
    conn.execute("CREATE TABLE IF NOT EXISTS _colmap (norm TEXT PRIMARY KEY, original TEXT)")
    conn.execute("DELETE FROM _colmap")
    conn.executemany("INSERT INTO _colmap VALUES (?,?)", col_map.items())

    # Metadatos: timestamp y conteo
    import datetime as _dt
    conn.execute(
        "CREATE TABLE IF NOT EXISTS _meta (key TEXT PRIMARY KEY, value TEXT)"
    )
    conn.execute("INSERT OR REPLACE INTO _meta VALUES ('updated_at', ?)",
                 (_dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),))
    conn.execute("INSERT OR REPLACE INTO _meta VALUES ('filas_orig', ?)",
                 (str(filas_originales),))
    conn.execute("INSERT OR REPLACE INTO _meta VALUES ('contratos_vig', ?)",
                 (str(len(df)),))
    conn.execute("INSERT OR REPLACE INTO _meta VALUES ('anio_vig', ?)",
                 (str(_AÑO_VIG),))

    # Datos
    df_save          = df.copy().astype(str)
    df_save.columns  = norm_cols
    df_save.to_sql("dotacion", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()


def _load() -> pd.DataFrame:
    try:
        conn = _get_conn()
        df   = pd.read_sql("SELECT * FROM dotacion", conn)
        try:
            col_map = dict(pd.read_sql("SELECT norm, original FROM _colmap", conn).values)
            df.columns = [col_map.get(c, c) for c in df.columns]
        except Exception:
            pass
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def _meta() -> dict:
    """Lee la tabla _meta y devuelve un dict key→value."""
    try:
        conn = _get_conn()
        rows = conn.execute("SELECT key, value FROM _meta").fetchall()
        conn.close()
        return {k: v for k, v in rows}
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# LÓGICA DE PROCESAMIENTO
# ══════════════════════════════════════════════════════════════════════════════

def _parse_termino(v):
    """Fecha Término: '00/00/0000' → MAX_DATE (activo). NaT → MAX_DATE."""
    s = str(v).strip()
    if s in _NULL_STRS:
        return _MAX_DATE
    try:
        return pd.to_datetime(v)
    except Exception:
        return _MAX_DATE


def _parse_inicio(v):
    try:
        return pd.to_datetime(v)
    except Exception:
        return pd.NaT


def procesar_dotacion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Obtiene el contrato vigente en el año {_AÑO_VIG} por persona desde el histórico SIRH.

    Clave de agrupación: (Rut, Correlativo)
    Cada (Rut, Correlativo) es una línea contractual única.
    Un funcionario puede tener más de una línea si trabaja en distintos
    bloques horarios (ej. 22+22 = 44 hrs).

    Criterio de vigencia al año {_AÑO_VIG}:
      · Fecha Inicio Contrato  ≤ 31-12-{_AÑO_VIG}
      · Fecha Término Contrato ≥ 01-01-{_AÑO_VIG}  (o '00/00/0000' = sin término)

    Regla de selección del registro representativo dentro del grupo vigente:
      · TITULAR  → fila con mayor Fecha Inicio Contrato
      · Otros    → fila con mayor Fecha Término Contrato
    """
    df = df.copy()

    # Verificar columnas mínimas
    for col in [COL_RUT, COL_CORREL, COL_CALIDAD, COL_INICIO, COL_TERMINO]:
        if col not in df.columns:
            raise ValueError(f"Columna requerida no encontrada: '{col}'")

    df["_t_sort"] = df[COL_TERMINO].apply(_parse_termino)
    df["_i_sort"] = df[COL_INICIO].apply(_parse_inicio)
    df["_titular"] = df[COL_CALIDAD].astype(str).str.upper().str.contains("TITULAR", na=False)

    # ── Filtro de vigencia en el año _AÑO_VIG ─────────────────────────────
    # inicio ≤ 31-dic-2026  Y  término ≥ 01-ene-2026
    mask_vig = (
        (df["_i_sort"].notna()) &
        (df["_i_sort"] <= _VIG_HASTA) &
        (df["_t_sort"] >= _VIG_DESDE)
    )
    df_vig = df[mask_vig].copy()

    if df_vig.empty:
        return pd.DataFrame(columns=df.columns)

    # ── Selección del registro representativo por (Rut, Correlativo) ──────
    resultados = []
    for (rut, correl), grp in df_vig.groupby([COL_RUT, COL_CORREL], sort=False):
        if grp["_titular"].any():
            idx = grp["_i_sort"].idxmax()
        else:
            idx = grp["_t_sort"].idxmax()
        resultados.append(grp.loc[idx])

    result = pd.DataFrame(resultados).reset_index(drop=True)
    result = result.drop(columns=["_t_sort", "_i_sort", "_titular"], errors="ignore")
    return result


def detectar_alertas_titulo(df: pd.DataFrame) -> pd.DataFrame:
    """RUTs con más de un Título distinto → error SIRH."""
    if COL_TITULO not in df.columns or COL_RUT not in df.columns:
        return pd.DataFrame()
    titulos = (
        df.groupby(COL_RUT)[COL_TITULO]
        .apply(lambda s: [v for v in s.astype(str).str.strip().unique()
                          if v not in _NULL_STRS])
    )
    ruts_err = titulos[titulos.apply(len) > 1].index
    if len(ruts_err) == 0:
        return pd.DataFrame()
    cols_show = [c for c in [COL_RUT, COL_DV, COL_NOMBRE, COL_CALIDAD,
                              COL_TITULO, COL_HORAS, COL_LEY,
                              COL_INICIO, COL_TERMINO] if c in df.columns]
    return (df[df[COL_RUT].isin(ruts_err)][cols_show]
            .sort_values([COL_RUT, COL_TITULO])
            .reset_index(drop=True))


def detectar_alertas_horas(df: pd.DataFrame) -> pd.DataFrame:
    """RUTs cuya suma de horas > 44."""
    if COL_HORAS not in df.columns or COL_RUT not in df.columns:
        return pd.DataFrame()
    df2 = df.copy()
    df2["_h"] = pd.to_numeric(df2[COL_HORAS], errors="coerce").fillna(0)
    suma = df2.groupby(COL_RUT)["_h"].sum()
    ruts_err = suma[suma > 44].index
    if len(ruts_err) == 0:
        return pd.DataFrame()
    nombres = df2.groupby(COL_RUT)[COL_NOMBRE].first() if COL_NOMBRE in df2.columns else None
    res = suma[suma > 44].reset_index()
    res.columns = [COL_RUT, "Total Horas"]
    if nombres is not None:
        res = res.merge(nombres.reset_index(), on=COL_RUT)
    return res.sort_values("Total Horas", ascending=False).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# UI — TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_dash, tab_repo, tab_alertas, tab_upload = st.tabs([
    "📊 Dashboard", "📋 Repositorio", "⚠️ Alertas SIRH", "⬆️ Actualizar",
])

# ─── TAB ACTUALIZAR ───────────────────────────────────────────────────────────
with tab_upload:
    st.markdown(f"### ⬆️ Cargar nueva versión de Dotación SIRH — Vigentes {_AÑO_VIG}")
    st.info(
        f"Sube el archivo Excel exportado desde SIRH (**DOTACION**). "
        f"El sistema filtrará los contratos **vigentes en el año {_AÑO_VIG}** "
        f"(inicio ≤ 31-12-{_AÑO_VIG} y término ≥ 01-01-{_AÑO_VIG}) "
        f"y guardará el repositorio en SQLite de forma persistente."
    )
    up = st.file_uploader("Archivo DOTACION (.xlsx / .xls)", type=["xlsx", "xls"], key="dot_up")

    if up:
        with st.status("⚙️ Procesando dotación...", expanded=True) as _st:
            _pb = st.progress(0, text="Leyendo archivo...")
            try:
                df_raw = pd.read_excel(up)
                _pb.progress(0.3, text=f"Leídas {len(df_raw):,} filas · {len(df_raw.columns)} columnas")

                df_proc = procesar_dotacion(df_raw)
                _pb.progress(0.7, text=f"Contratos vigentes {_AÑO_VIG} detectados: {len(df_proc):,}")

                _save(df_proc, filas_originales=len(df_raw))
                _pb.progress(1.0, text="Repositorio guardado en SQLite ✅")
                _st.update(label="✅ Dotación actualizada correctamente", state="complete", expanded=False)

                n_ruts  = df_proc[COL_RUT].nunique() if COL_RUT in df_proc.columns else "?"
                c1, c2, c3 = st.columns(3)
                c1.metric("Filas originales",    f"{len(df_raw):,}")
                c2.metric("Contratos vigentes",  f"{len(df_proc):,}")
                c3.metric("RUTs únicos",         f"{n_ruts:,}")
                st.rerun()
            except Exception as e:
                import traceback
                _st.update(label="❌ Error al procesar", state="error")
                st.error(str(e))
                st.code(traceback.format_exc())

# ─── Cargar datos ─────────────────────────────────────────────────────────────
df_dot = _load()

if df_dot.empty:
    for _t in [tab_dash, tab_repo, tab_alertas]:
        with _t:
            st.info("Sin datos. Ve a **⬆️ Actualizar** para cargar la dotación SIRH.")
    st.stop()

# ─── TAB DASHBOARD ────────────────────────────────────────────────────────────
with tab_dash:
    st.markdown(f"### 📊 Resumen Dotación — Contratos Vigentes {_AÑO_VIG}")

    # Metadatos del repositorio SQLite
    _meta_data = _meta()
    if _meta_data:
        _upd = _meta_data.get("updated_at", "—")
        _orig = _meta_data.get("filas_orig", "—")
        _anio = _meta_data.get("anio_vig", str(_AÑO_VIG))
        st.caption(
            f"🗄️ Repositorio SQLite — Última actualización: **{_upd}** · "
            f"Filas originales SIRH: **{int(_orig):,}**  · "
            f"Año de vigencia: **{_anio}**"
        )

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total contratos", f"{len(df_dot):,}")
    k2.metric("RUTs únicos", f"{df_dot[COL_RUT].nunique():,}" if COL_RUT in df_dot.columns else "—")

    if COL_CALIDAD in df_dot.columns:
        n_tit = df_dot[COL_CALIDAD].str.upper().str.contains("TITULAR", na=False).sum()
        k3.metric("Titulares",      f"{n_tit:,}")
        k4.metric("Otras calidades",f"{len(df_dot) - n_tit:,}")

    st.divider()

    # Distribución por calidad jurídica
    if COL_CALIDAD in df_dot.columns:
        import plotly.graph_objects as go
        dist_cal = df_dot[COL_CALIDAD].value_counts().reset_index()
        dist_cal.columns = ["Calidad Jurídica", "Contratos"]

        col_tbl, col_bar = st.columns([1, 2])
        with col_tbl:
            st.markdown("**Por Calidad Jurídica**")
            st.markdown(ev_design.ev_table_html(dist_cal), unsafe_allow_html=True)
        with col_bar:
            _labels = dist_cal["Calidad Jurídica"].tolist()
            _vals   = dist_cal["Contratos"].tolist()
            _n      = len(_labels)
            _cols   = [f"rgb({int(74+156*i/max(_n-1,1))},{int(158-101*i/max(_n-1,1))},{int(255-185*i/max(_n-1,1))})"
                       for i in range(_n)]
            fig_cal = go.Figure(go.Bar(
                x=_labels, y=_vals,
                marker=dict(color=_cols, line=dict(width=0)),
                text=[str(v) for v in _vals], textposition="outside",
                textfont=dict(size=11, color="#b3b3b3"),
            ))
            fig_cal.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#b3b3b3", family="Outfit"),
                margin=dict(t=20, b=70, l=10, r=10), height=300,
                xaxis=dict(type="category", tickfont=dict(size=10, color="#b3b3b3"),
                           tickangle=-25, showgrid=False),
                yaxis=dict(tickfont=dict(size=10, color="#6b6b6b"),
                           gridcolor="rgba(255,255,255,0.05)"),
                showlegend=False,
            )
            st.plotly_chart(fig_cal)

    st.divider()

    # Distribución por horas y por ley
    col_h, col_l = st.columns(2)
    with col_h:
        if COL_HORAS in df_dot.columns:
            dist_hrs = (pd.to_numeric(df_dot[COL_HORAS], errors="coerce")
                        .value_counts().sort_index().reset_index())
            dist_hrs.columns = ["Horas", "Contratos"]
            dist_hrs["Horas"] = dist_hrs["Horas"].astype(str)
            st.markdown("**Distribución por N° Horas**")
            st.markdown(ev_design.ev_table_html(dist_hrs), unsafe_allow_html=True)
    with col_l:
        if COL_LEY in df_dot.columns:
            dist_ley = df_dot[COL_LEY].value_counts().reset_index()
            dist_ley.columns = ["Ley", "Contratos"]
            st.markdown("**Distribución por Ley**")
            st.markdown(ev_design.ev_table_html(dist_ley), unsafe_allow_html=True)

# ─── TAB REPOSITORIO ─────────────────────────────────────────────────────────
with tab_repo:
    st.markdown(f"### 📋 Repositorio — Contratos Vigentes {_AÑO_VIG}")

    # Filtros
    f1, f2, f3, f4 = st.columns([1.2, 2, 1.8, 1.5])
    filt_rut = f1.text_input("RUT", placeholder="ej: 12345678", key="dot_frut")
    filt_nom = f2.text_input("Nombre Funcionario", placeholder="Apellido o nombre", key="dot_fnom")

    cal_opts = ["(Todas)"] + (sorted(df_dot[COL_CALIDAD].dropna().unique().tolist())
                               if COL_CALIDAD in df_dot.columns else [])
    filt_cal = f3.selectbox("Calidad Jurídica", cal_opts, key="dot_fcal")

    plt_vals = sorted([v for v in df_dot[COL_PLANTA].unique()
                       if str(v).strip() not in _NULL_STRS]) if COL_PLANTA in df_dot.columns else []
    plt_opts = ["(Todas)"] + plt_vals
    filt_plt = f4.selectbox("Correl. Planta", plt_opts, key="dot_fplt")

    # Aplicar filtros
    df_filt = df_dot.copy()
    if filt_rut.strip():
        df_filt = df_filt[df_filt[COL_RUT].astype(str).str.contains(filt_rut.strip(), na=False)]
    if filt_nom.strip():
        df_filt = df_filt[df_filt[COL_NOMBRE].astype(str).str.upper()
                          .str.contains(filt_nom.strip().upper(), na=False)]
    if filt_cal != "(Todas)":
        df_filt = df_filt[df_filt[COL_CALIDAD] == filt_cal]
    if filt_plt != "(Todas)":
        df_filt = df_filt[df_filt[COL_PLANTA] == filt_plt]

    # Reset página si cambiaron filtros
    _filt_key = f"{filt_rut}|{filt_nom}|{filt_cal}|{filt_plt}"
    if st.session_state.get("_dot_filt_prev") != _filt_key:
        st.session_state["dot_pag"] = 1
        st.session_state["_dot_filt_prev"] = _filt_key

    # Paginación
    p1, p2, p3 = st.columns([3, 1, 1])
    p1.caption(f"{len(df_filt):,} registros encontrados")
    rows_pp   = p2.selectbox("Filas", [10, 20, 50, 100], index=1,
                              key="dot_rpp", label_visibility="collapsed")
    total_pag = max(1, -(-len(df_filt) // rows_pp))
    pag       = st.session_state.get("dot_pag", 1)

    nav1, nav2, nav3 = st.columns([1, 3, 1])
    if nav1.button("◀ Anterior", key="dot_prev", disabled=(pag <= 1)):
        st.session_state["dot_pag"] = pag - 1; st.rerun()
    nav2.markdown(
        f'<div style="text-align:center;padding:6px 0;color:#b3b3b3;font-size:13px;">'
        f'Página <b>{pag}</b> de <b>{total_pag}</b> · {len(df_filt):,} registros</div>',
        unsafe_allow_html=True)
    if nav3.button("Siguiente ▶", key="dot_next", disabled=(pag >= total_pag)):
        st.session_state["dot_pag"] = pag + 1; st.rerun()

    _ini = (pag - 1) * rows_pp
    st.markdown(ev_design.ev_table_html(df_filt.iloc[_ini:_ini + rows_pp]), unsafe_allow_html=True)

    # Descarga
    st.markdown("---")
    dl_buf = io.BytesIO()
    df_filt.to_excel(dl_buf, index=False)
    dl_buf.seek(0)
    st.download_button(
        f"📥 Descargar filtro actual  ({len(df_filt):,} registros)",
        data=dl_buf,
        file_name="dotacion_vigente.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="dot_dl",
    )

# ─── TAB ALERTAS ─────────────────────────────────────────────────────────────
with tab_alertas:
    st.markdown("### ⚠️ Alertas SIRH — Inconsistencias a Corregir")

    # ── Alerta 1: Título inconsistente ────────────────────────────────────────
    st.markdown("#### 📌 Funcionarios con más de un Título diferente")
    st.caption(
        "Un mismo RUT registra distintos valores en la columna **'Título'**. "
        "Esto indica una inconsistencia que debe corregirse directamente en SIRH."
    )
    df_al_tit = detectar_alertas_titulo(df_dot)
    if df_al_tit.empty:
        st.success("✅ Sin inconsistencias en la columna Título.")
    else:
        st.error(f"❌ {df_al_tit[COL_RUT].nunique()} RUT(s) con Título inconsistente — "
                 f"{len(df_al_tit)} filas afectadas")
        st.markdown(ev_design.ev_table_html(df_al_tit), unsafe_allow_html=True)

        al_buf = io.BytesIO()
        df_al_tit.to_excel(al_buf, index=False)
        al_buf.seek(0)
        st.download_button(
            "📥 Descargar listado de alertas Título",
            data=al_buf, file_name="alertas_titulo_sirh.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dot_dl_al_tit",
        )

    st.divider()

    # ── Alerta 2: Horas > 44 ─────────────────────────────────────────────────
    st.markdown("#### 📌 Funcionarios con total de horas superior a 44")
    st.caption(
        "La suma de horas de todos los contratos vigentes del funcionario "
        "supera las **44 horas** máximas permitidas."
    )
    df_al_hrs = detectar_alertas_horas(df_dot)
    if df_al_hrs.empty:
        st.success("✅ Sin exceso de horas detectado.")
    else:
        st.warning(f"⚠️ {len(df_al_hrs)} RUT(s) con total de horas > 44")
        st.markdown(ev_design.ev_table_html(df_al_hrs), unsafe_allow_html=True)

        hrs_buf = io.BytesIO()
        df_al_hrs.to_excel(hrs_buf, index=False)
        hrs_buf.seek(0)
        st.download_button(
            "📥 Descargar listado de alertas Horas",
            data=hrs_buf, file_name="alertas_horas_sirh.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dot_dl_al_hrs",
        )

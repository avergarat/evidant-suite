# -*- coding: utf-8 -*-
"""
Página 8 — Revisión de Dotación por Centro de Salud
Repositorio mensual · Asignación de horas indirectas · Cálculo de horas clínicas · Brecha vs ideal
"""

import sys, os, io, re, sqlite3, datetime
from typing import Optional
import streamlit as st
import pandas as pd

# ── paths ──────────────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
import ev_design
from revision_dotacion import db_rev

# ── Init DB ────────────────────────────────────────────────────────────────────
db_rev.init_db()

# ── Render design ──────────────────────────────────────────────────────────────
ev_design.render(
    current    = "dotacion",
    page_title = "Revisión Dotación por Centro",
    page_sub   = "Asignación horas indirectas · Horas clínicas por funcionario · Repositorio mensual",
    icon       = "🏥",
)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES — columnas posibles en dotacion.db (SIRH)
# ══════════════════════════════════════════════════════════════════════════════
_DOTACION_DB = os.path.join(_ROOT, "dotacion.db")

# Posibles nombres de columna para "centro de salud"
_COL_CESFAM_OPTS  = ["Descripción Unidad", "Descripcion Unidad", "CESFAM",
                     "Centro de Salud", "Descripción Unidad 2", "Descripcion Unidad 2"]
# Columnas SIRH mínimas
_COL_RUT    = "Rut"
_COL_DV     = "Dv"
_COL_NOMBRE = "Nombre Funcionario"
_COL_CALIDAD = "Descripción Calidad Jurídica"
_COL_CARGO  = "Descripción Cargo"
_COL_PLANTA = "Descripción Planta"
_COL_HORAS  = "Número horas"
_COL_UNIDAD = "Descripción Unidad"
_COL_UNIDAD2 = "Descripción Unidad 2"

_NULL_STRS = {"nan", "none", "nat", "s/d", "sd", "", "NaT", "None"}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=120)
def _load_dotacion() -> pd.DataFrame:
    """Carga el repositorio de dotación vigente desde dotacion.db."""
    if not os.path.exists(_DOTACION_DB):
        return pd.DataFrame()
    try:
        con = sqlite3.connect(_DOTACION_DB, check_same_thread=False)
        df = pd.read_sql("SELECT * FROM dotacion", con)
        # Restaurar nombres originales desde _colmap
        try:
            cm = pd.read_sql("SELECT norm, original FROM _colmap", con)
            col_map = dict(zip(cm["norm"], cm["original"]))
            df.columns = [col_map.get(c, c) for c in df.columns]
        except Exception:
            pass
        con.close()
        return df
    except Exception:
        return pd.DataFrame()


def _norm_col(col: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", str(col).lower()).strip("_")


def _find_col(df: pd.DataFrame, candidates: list) -> Optional[str]:
    """Retorna el primer nombre de columna que existe en df."""
    for c in candidates:
        if c in df.columns:
            return c
    # fuzzy: normalizar
    norm_map = {_norm_col(c): c for c in df.columns}
    for c in candidates:
        n = _norm_col(c)
        if n in norm_map:
            return norm_map[n]
    return None


def _safe_float(v) -> float:
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return 0.0


def _clean_str(v) -> str:
    s = str(v).strip()
    return "" if s.lower() in _NULL_STRS else s


def _list_cesfam_values(df: pd.DataFrame, col_cesfam: str) -> list:
    vals = sorted(df[col_cesfam].dropna().unique().tolist())
    return [v for v in vals if _clean_str(v)]


def _mes_anio_str(mes: int, anio: int) -> str:
    return f"{anio}-{mes:02d}"


def _filtrar_por_cesfam(df: pd.DataFrame, col_cesfam: str, cesfam_sel: str) -> pd.DataFrame:
    return df[df[col_cesfam].astype(str).str.strip() == cesfam_sel].copy()


# ══════════════════════════════════════════════════════════════════════════════
# ESTADO DE SESIÓN
# ══════════════════════════════════════════════════════════════════════════════

def _init_session():
    if "rdot_asig" not in st.session_state:
        # {rut: [encargatura, ...]}
        st.session_state["rdot_asig"] = {}
    if "rdot_unidad" not in st.session_state:
        # {rut: unidad_desempeno}
        st.session_state["rdot_unidad"] = {}
    if "rdot_obs" not in st.session_state:
        # {rut: observaciones}
        st.session_state["rdot_obs"] = {}

_init_session()


def _reset_session_centro():
    st.session_state["rdot_asig"] = {}
    st.session_state["rdot_unidad"] = {}
    st.session_state["rdot_obs"] = {}


# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════

tab_vista, tab_unidades, tab_horas, tab_repo, tab_ideal, tab_brecha = st.tabs([
    "🏥 Vista por Centro",
    "🗂️ Unidades de Desempeño",
    "⏱️ Horas Indirectas",
    "📊 Repositorio Mensual",
    "📐 Dotación Ideal",
    "🔍 Brecha vs Ideal",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — VISTA POR CENTRO
# ══════════════════════════════════════════════════════════════════════════════

with tab_vista:
    st.markdown("### 🏥 Revisión de Dotación por Centro de Salud")

    df_dot = _load_dotacion()
    col_cesfam = _find_col(df_dot, _COL_CESFAM_OPTS) if not df_dot.empty else None

    if df_dot.empty:
        st.warning(
            "No hay datos de dotación cargados en esta sesión. "
            "Primero debes cargar el archivo SIRH en el módulo **Dotación**."
        )
        st.page_link("pages/7_Dotacion.py", label="👉 Ir a Dotación → pestaña ⬆️ Actualizar")
    elif col_cesfam is None:
        st.error(
            f"No se encontró columna de Centro de Salud. "
            f"Columnas disponibles: {list(df_dot.columns)}"
        )
    else:
        # ── Selectores de período y CESFAM ────────────────────────────────────
        c1, c2, c3 = st.columns([1, 1, 2])
        anio_sel = c1.number_input("Año", min_value=2020, max_value=2035,
                                   value=datetime.datetime.now().year, step=1, key="rv_anio")
        mes_sel  = c2.selectbox(
            "Mes", list(range(1, 13)),
            format_func=lambda m: ["Ene","Feb","Mar","Abr","May","Jun",
                                    "Jul","Ago","Sep","Oct","Nov","Dic"][m-1],
            index=datetime.datetime.now().month - 1, key="rv_mes",
        )
        mes_anio = _mes_anio_str(int(mes_sel), int(anio_sel))

        cesfam_list = _list_cesfam_values(df_dot, col_cesfam)
        cesfam_sel = c3.selectbox("Centro de Salud (Descripción Unidad)", cesfam_list, key="rv_cesfam")

        if st.button("🔄 Cambiar Centro / Período", key="rv_reset"):
            _reset_session_centro()
            st.rerun()

        st.divider()

        # ── Cargar asignaciones guardadas para este mes/CESFAM ────────────────
        df_asig_guardadas = db_rev.get_asignaciones(mes_anio)
        if not df_asig_guardadas.empty:
            for rut_g, grp in df_asig_guardadas.groupby("rut"):
                rut_g = str(rut_g)
                if rut_g not in st.session_state["rdot_asig"]:
                    st.session_state["rdot_asig"][rut_g] = list(grp["encargatura"])

        df_rev_guardada = db_rev.get_revision_mensual(mes_anio, cesfam_sel)
        if not df_rev_guardada.empty:
            for _, rg in df_rev_guardada.iterrows():
                rut_g = str(rg["rut"])
                if rut_g not in st.session_state["rdot_unidad"]:
                    st.session_state["rdot_unidad"][rut_g] = str(rg.get("unidad_desempeno", ""))
                if rut_g not in st.session_state["rdot_obs"]:
                    st.session_state["rdot_obs"][rut_g] = str(rg.get("observaciones", ""))

        # ── Filtrar dotación para el CESFAM seleccionado ─────────────────────
        df_centro = _filtrar_por_cesfam(df_dot, col_cesfam, cesfam_sel)
        if df_centro.empty:
            st.info(f"No se encontraron funcionarios para **{cesfam_sel}**.")
        else:
            # ── Lista de encargaturas disponibles ──────────────────────────────
            df_hrs_gen   = db_rev.get_horas_general()
            df_hrs_csfm  = db_rev.get_horas_cesfam(cesfam_sel)
            all_encargaturas_gen  = sorted(df_hrs_gen["nombre"].tolist())
            all_encargaturas_csfm = sorted(df_hrs_csfm["encargatura"].tolist()) if not df_hrs_csfm.empty else []
            seen = set()
            all_encargaturas = []
            for e in all_encargaturas_csfm + all_encargaturas_gen:
                if e not in seen:
                    all_encargaturas.append(e)
                    seen.add(e)

            # ── Lista de unidades de desempeño disponibles ─────────────────────
            df_ud = db_rev.get_unidades_desempeno(cesfam_sel)
            ud_options = sorted(df_ud["unidad_desempeno"].unique().tolist()) if not df_ud.empty else []

            st.markdown(f"**{len(df_centro)} funcionarios** encontrados en **{cesfam_sel}** — Período: `{mes_anio}`")

            # ── Construir tabla de trabajo ──────────────────────────────────────
            col_rut    = _find_col(df_centro, [_COL_RUT, "Rut", "RUT", "rut"])
            col_dv     = _find_col(df_centro, [_COL_DV, "DV", "dv"])
            col_nombre = _find_col(df_centro, [_COL_NOMBRE, "Nombre", "NOMBRE"])
            col_calidad= _find_col(df_centro, [_COL_CALIDAD, "Calidad Jurídica", "Descripcion Calidad Juridica"])
            col_cargo  = _find_col(df_centro, [_COL_CARGO, "Cargo", "Descripcion Cargo", "Descripción Cargo"])
            col_planta = _find_col(df_centro, [_COL_PLANTA, "Descripcion Planta", "Descripción Planta"])
            col_horas  = _find_col(df_centro, [_COL_HORAS, "Número horas", "Numero horas", "Horas"])
            col_unidad_sirh = _find_col(df_centro, [_COL_UNIDAD2, _COL_UNIDAD, "Unidad Desempeño"])

            def _get(row, col):
                return _clean_str(row[col]) if col and col in row.index else ""

            rows_tabla = []
            for _, row in df_centro.iterrows():
                rut     = _get(row, col_rut)
                dv      = _get(row, col_dv)
                nombre  = _get(row, col_nombre)
                horas_c = _safe_float(_get(row, col_horas)) if col_horas else 0.0

                ud_actual = st.session_state["rdot_unidad"].get(rut, "")
                if not ud_actual and col_unidad_sirh:
                    ud_actual = _get(row, col_unidad_sirh)

                encargaturas_rut = st.session_state["rdot_asig"].get(rut, [])
                hrs_indir = sum(db_rev.resolver_horas_encargatura(cesfam_sel, e) for e in encargaturas_rut)
                hrs_clinicas = max(0.0, horas_c - hrs_indir)

                rows_tabla.append({
                    "RUT":              rut,
                    "DV":               dv,
                    "Nombre":           nombre,
                    "Calidad Jurídica": _get(row, col_calidad),
                    "Cargo":            _get(row, col_cargo) or _get(row, col_planta),
                    "Unidad Desempeño": ud_actual,
                    "Hrs Contrato":     horas_c,
                    "Encargaturas":     len(encargaturas_rut),
                    "Hrs Indirectas":   round(hrs_indir, 2),
                    "Hrs Clínicas":     round(hrs_clinicas, 2),
                    "Obs":              st.session_state["rdot_obs"].get(rut, ""),
                })

            df_tabla = pd.DataFrame(rows_tabla)

            # ── Tabla con semáforo de colores ───────────────────────────────────
            def _semaforo_html(df):
                pal = {"hbg":"#1a1a1a","rbg":"#181818","ralt":"#1f1f1f",
                       "bdr":"rgba(255,255,255,0.07)","grn":"#1db954",
                       "yel":"#f59e0b","red":"#ef4444","txt":"#ffffff","txt2":"#b3b3b3"}
                cols = list(df.columns)
                th = "".join(
                    f'<th style="padding:8px 10px;text-align:left;font-size:11px;font-weight:600;'
                    f'color:{pal["txt2"]};border-bottom:1px solid {pal["bdr"]};white-space:nowrap;">{c}</th>'
                    for c in cols)
                rows_h = ""
                for i, (_, r) in enumerate(df.iterrows()):
                    bg = pal["ralt"] if i % 2 else pal["rbg"]
                    cells = ""
                    for c in cols:
                        v = r[c]
                        if c == "Hrs Clínicas":
                            try:
                                fv = float(v)
                                clr = pal["grn"] if fv >= 20 else pal["yel"] if fv >= 10 else pal["red"]
                            except Exception:
                                clr = pal["txt2"]
                            cells += (f'<td style="padding:7px 10px;color:{clr};font-weight:700;'
                                      f'font-size:13px;text-align:right;">{v}</td>')
                        elif c == "Hrs Indirectas":
                            cells += (f'<td style="padding:7px 10px;color:{pal["yel"]};'
                                      f'font-size:13px;text-align:right;">{v}</td>')
                        elif c == "Hrs Contrato":
                            cells += (f'<td style="padding:7px 10px;color:{pal["txt2"]};'
                                      f'font-size:13px;text-align:right;">{v}</td>')
                        else:
                            cells += (f'<td style="padding:7px 10px;color:{pal["txt"]};'
                                      f'font-size:12px;white-space:nowrap;">{v}</td>')
                    rows_h += f'<tr style="background:{bg};">{cells}</tr>'
                return (f'<div style="overflow-x:auto;border-radius:8px;border:1px solid {pal["bdr"]};">'
                        f'<table style="width:100%;border-collapse:collapse;font-family:Outfit,sans-serif;">'
                        f'<thead><tr style="background:{pal["hbg"]};">{th}</tr></thead>'
                        f'<tbody>{rows_h}</tbody></table></div>')

            st.markdown(_semaforo_html(df_tabla), unsafe_allow_html=True)
            st.divider()

            # ── Panel de asignación por funcionario ────────────────────────────
            st.markdown("#### ⚙️ Asignar Encargaturas")
            rut_opciones = [f"{r} — {n}" for r, n in zip(df_tabla["RUT"], df_tabla["Nombre"])]
            sel_func_str = st.selectbox("Seleccionar funcionario", rut_opciones, key="rv_func_sel")
            rut_sel = sel_func_str.split(" — ")[0].strip() if sel_func_str else ""

            if rut_sel:
                row_func = df_tabla[df_tabla["RUT"] == rut_sel].iloc[0]
                fa, fb, fc = st.columns([2, 2, 2])

                ud_actual = st.session_state["rdot_unidad"].get(rut_sel, row_func["Unidad Desempeño"])
                ud_idx = ud_options.index(ud_actual) if ud_actual in ud_options else None
                ud_nueva = fa.selectbox(
                    "Unidad de Desempeño",
                    ["— Sin asignar —"] + ud_options + ["[Escribir manualmente]"],
                    index=(ud_idx + 1) if ud_idx is not None else 0,
                    key=f"ud_{rut_sel}",
                )
                if ud_nueva == "[Escribir manualmente]":
                    ud_final = fa.text_input("Escribir unidad:", key=f"ud_manual_{rut_sel}")
                elif ud_nueva == "— Sin asignar —":
                    ud_final = ""
                else:
                    ud_final = ud_nueva
                if ud_final != st.session_state["rdot_unidad"].get(rut_sel, ""):
                    st.session_state["rdot_unidad"][rut_sel] = ud_final

                encargaturas_actuales = st.session_state["rdot_asig"].get(rut_sel, [])

                with fb:
                    st.markdown("**Encargaturas asignadas:**")
                    if encargaturas_actuales:
                        for enc in encargaturas_actuales:
                            hrs_enc = db_rev.resolver_horas_encargatura(cesfam_sel, enc)
                            st.markdown(
                                f'<div style="display:flex;justify-content:space-between;'
                                f'padding:4px 8px;background:#242424;border-radius:4px;margin:2px 0;">'
                                f'<span style="font-size:12px;color:#fff;">{enc}</span>'
                                f'<span style="font-size:12px;color:#f59e0b;font-weight:600;">{hrs_enc:.2f} h</span>'
                                f'</div>', unsafe_allow_html=True)
                    else:
                        st.caption("Sin encargaturas asignadas.")

                with fc:
                    st.markdown("**Agregar encargatura:**")
                    nueva_enc = st.selectbox("", ["— Seleccionar —"] + all_encargaturas,
                                             key=f"nueva_enc_{rut_sel}", label_visibility="collapsed")
                    if st.button("➕ Agregar", key=f"add_enc_{rut_sel}"):
                        if nueva_enc and nueva_enc != "— Seleccionar —":
                            lst = st.session_state["rdot_asig"].get(rut_sel, [])
                            if nueva_enc not in lst:
                                lst.append(nueva_enc)
                                st.session_state["rdot_asig"][rut_sel] = lst
                            st.rerun()
                    if encargaturas_actuales:
                        enc_quitar = st.selectbox("Quitar:", ["— —"] + encargaturas_actuales,
                                                  key=f"quitar_{rut_sel}")
                        if st.button("➖ Quitar", key=f"rm_enc_{rut_sel}"):
                            if enc_quitar != "— —":
                                lst = st.session_state["rdot_asig"].get(rut_sel, [])
                                if enc_quitar in lst:
                                    lst.remove(enc_quitar)
                                    st.session_state["rdot_asig"][rut_sel] = lst
                                st.rerun()

                obs_actual = st.session_state["rdot_obs"].get(rut_sel, "")
                obs_nueva = st.text_input("Observaciones:", value=obs_actual, key=f"obs_{rut_sel}")
                st.session_state["rdot_obs"][rut_sel] = obs_nueva

            st.divider()

            # ── KPIs ───────────────────────────────────────────────────────────
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Funcionarios", len(df_tabla))
            k2.metric("Hrs Contrato total", f"{df_tabla['Hrs Contrato'].sum():.1f}")
            k3.metric("Hrs Indirectas total", f"{df_tabla['Hrs Indirectas'].sum():.1f}")
            k4.metric("Hrs Clínicas total", f"{df_tabla['Hrs Clínicas'].sum():.1f}")
            k5.metric("Sin encargatura", int((df_tabla["Encargaturas"] == 0).sum()))

            st.divider()

            # ── Guardar revisión ───────────────────────────────────────────────
            col_g1, col_g2 = st.columns([3, 1])
            with col_g2:
                if st.button("💾 Guardar Revisión Mensual", type="primary",
                             use_container_width=True, key="rv_guardar"):
                    rows_save = []
                    asig_save_all = []
                    for _, row_t in df_centro.iterrows():
                        rut = _get(row_t, col_rut)
                        horas_c = _safe_float(_get(row_t, col_horas)) if col_horas else 0.0
                        encargaturas_rut = st.session_state["rdot_asig"].get(rut, [])
                        hrs_indir = sum(db_rev.resolver_horas_encargatura(cesfam_sel, e) for e in encargaturas_rut)
                        hrs_clin  = max(0.0, horas_c - hrs_indir)
                        ud  = st.session_state["rdot_unidad"].get(
                            rut, _get(row_t, col_unidad_sirh) if col_unidad_sirh else "")
                        obs = st.session_state["rdot_obs"].get(rut, "")
                        rows_save.append({
                            "rut": rut, "dv": _get(row_t, col_dv),
                            "nombre": _get(row_t, col_nombre), "cesfam": cesfam_sel,
                            "descripcion_unidad": _get(row_t, col_cesfam),
                            "calidad_juridica": _get(row_t, col_calidad),
                            "descripcion_cargo": _get(row_t, col_cargo) or _get(row_t, col_planta),
                            "descripcion_planta": _get(row_t, col_planta),
                            "unidad_desempeno": ud, "horas_contrato": horas_c,
                            "horas_indirectas_total": round(hrs_indir, 2),
                            "horas_clinicas": round(hrs_clin, 2), "observaciones": obs,
                        })
                        for encarg in encargaturas_rut:
                            hrs_e  = db_rev.resolver_horas_encargatura(cesfam_sel, encarg)
                            fuente = "CESFAM" if (not df_hrs_csfm.empty and
                                      encarg in df_hrs_csfm["encargatura"].tolist()) else "GENERAL"
                            asig_save_all.append((rut, _get(row_t, col_nombre), encarg, hrs_e, fuente))
                    try:
                        db_rev.save_revision_mensual(mes_anio, rows_save)
                        from collections import defaultdict
                        asig_by_rut = defaultdict(list)
                        for rut_s, nom_s, encarg_s, hrs_s, fuente_s in asig_save_all:
                            asig_by_rut[(rut_s, nom_s)].append((encarg_s, hrs_s, fuente_s))
                        for (rut_s, nom_s), encs in asig_by_rut.items():
                            db_rev.save_asignaciones_rut(mes_anio, rut_s, nom_s, cesfam_sel, encs)
                        st.success(f"✅ Revisión guardada — {len(rows_save)} funcionarios — {mes_anio}")
                        _load_dotacion.clear()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

            with col_g1:
                buf = io.BytesIO()
                pd.DataFrame(rows_tabla).to_excel(buf, index=False)
                buf.seek(0)
                st.download_button(
                    f"📥 Descargar tabla actual ({cesfam_sel})",
                    data=buf,
                    file_name=f"revision_{cesfam_sel}_{mes_anio}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True, key="rv_dl_tabla",
                )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — UNIDADES DE DESEMPEÑO
# ══════════════════════════════════════════════════════════════════════════════

with tab_unidades:
    st.markdown("### 🗂️ Base de Datos — Unidades de Desempeño")
    st.caption(
        "Define el mapeo entre la nomenclatura SIRH (Unidad SIRH) y la Unidad de Desempeño real "
        "para cada CESFAM. Esta tabla permite estandarizar la vista principal."
    )

    df_ud_all = db_rev.get_unidades_desempeno()

    # Tabla actual
    if not df_ud_all.empty:
        st.markdown("#### Mapeos actuales")
        st.markdown(ev_design.ev_table_html(df_ud_all.drop(columns=["id"])), unsafe_allow_html=True)

        # Eliminar fila
        ud_ids = df_ud_all["id"].tolist()
        ud_etiquetas = [f"{r['cesfam']} | {r['unidad_sirh']} → {r['unidad_desempeno']}"
                        for _, r in df_ud_all.iterrows()]
        del_ud = st.selectbox("Eliminar mapeo:", ["— —"] + ud_etiquetas, key="ud_del_sel")
        if st.button("🗑️ Eliminar seleccionado", key="ud_del_btn"):
            if del_ud != "— —":
                idx = ud_etiquetas.index(del_ud)
                db_rev.delete_unidad_desempeno(ud_ids[idx])
                st.rerun()
    else:
        st.info("No hay mapeos definidos.")

    st.divider()
    st.markdown("#### ➕ Agregar / Actualizar mapeo")

    ua, ub, uc = st.columns(3)
    ud_cesfam_new = ua.text_input("CESFAM", key="ud_new_cesfam",
                                   placeholder="ej: CESFAM Ahues")
    ud_sirh_new   = ub.text_input("Unidad SIRH (tal como aparece en dotación)", key="ud_new_sirh",
                                   placeholder="ej: SECTOR AMARILLO")
    ud_dest_new   = uc.text_input("Unidad de Desempeño real", key="ud_new_dest",
                                   placeholder="ej: Sector Amarillo - CESFAM Ahues")

    if st.button("💾 Guardar mapeo", key="ud_save"):
        if ud_cesfam_new and ud_sirh_new and ud_dest_new:
            db_rev.upsert_unidad_desempeno(ud_cesfam_new.strip(), ud_sirh_new.strip(), ud_dest_new.strip())
            st.success("Mapeo guardado.")
            st.rerun()
        else:
            st.warning("Completa los tres campos.")

    st.divider()
    st.markdown("#### 📥 Importar desde Excel")
    st.caption("El archivo debe tener columnas: `cesfam`, `unidad_sirh`, `unidad_desempeno`")
    up_ud = st.file_uploader("Excel de mapeos", type=["xlsx", "xls"], key="ud_up")
    if up_ud:
        try:
            df_up = pd.read_excel(up_ud)
            req = {"cesfam", "unidad_sirh", "unidad_desempeno"}
            if req.issubset({c.lower().strip() for c in df_up.columns}):
                df_up.columns = [c.lower().strip() for c in df_up.columns]
                for _, rw in df_up.iterrows():
                    db_rev.upsert_unidad_desempeno(
                        str(rw["cesfam"]).strip(),
                        str(rw["unidad_sirh"]).strip(),
                        str(rw["unidad_desempeno"]).strip(),
                    )
                st.success(f"Importados {len(df_up)} mapeos.")
                st.rerun()
            else:
                st.error(f"Columnas requeridas: {req}. Encontradas: {set(df_up.columns)}")
        except Exception as e:
            st.error(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — HORAS INDIRECTAS
# ══════════════════════════════════════════════════════════════════════════════

with tab_horas:
    st.markdown("### ⏱️ Gestión de Horas Indirectas")

    sub_gen, sub_cesfam, sub_import = st.tabs([
        "📋 Lista General",
        "🏥 Matriz por CESFAM",
        "📥 Importar desde Excel",
    ])

    # ── Sub-tab: Lista General ─────────────────────────────────────────────────
    with sub_gen:
        st.markdown("#### Horas indirectas generales (aplica a todos los CESFAM como fallback)")
        df_hg = db_rev.get_horas_general()

        if not df_hg.empty:
            # Editar inline con data_editor
            df_hg_edit = df_hg.copy()
            edited = st.data_editor(
                df_hg_edit.drop(columns=["id"]),
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "tipo": st.column_config.SelectboxColumn("Tipo", options=["GRUPAL", "INDIVIDUAL"]),
                    "nombre": st.column_config.TextColumn("Nombre encargatura"),
                    "horas": st.column_config.NumberColumn("Hrs semanales", format="%.2f", min_value=0),
                },
                key="hg_editor",
            )
            if st.button("💾 Guardar cambios lista general", key="hg_save"):
                for _, rw in edited.iterrows():
                    if rw["nombre"] and str(rw["nombre"]).strip():
                        db_rev.upsert_hora_general(
                            str(rw["nombre"]).strip(),
                            str(rw["tipo"]).strip(),
                            float(rw["horas"] or 0),
                        )
                st.success("Lista general actualizada.")
                st.rerun()

        st.divider()
        st.markdown("#### ➕ Agregar nueva encargatura")
        ha, hb, hc = st.columns([2, 1, 1])
        h_nombre = ha.text_input("Nombre encargatura", key="hg_new_nom")
        h_tipo   = hb.selectbox("Tipo", ["INDIVIDUAL", "GRUPAL"], key="hg_new_tipo")
        h_horas  = hc.number_input("Hrs semanales", min_value=0.0, step=0.25, key="hg_new_hrs")
        if st.button("➕ Agregar", key="hg_add"):
            if h_nombre.strip():
                db_rev.upsert_hora_general(h_nombre.strip(), h_tipo, h_horas)
                st.success("Encargatura agregada.")
                st.rerun()

    # ── Sub-tab: Matriz por CESFAM ─────────────────────────────────────────────
    with sub_cesfam:
        st.markdown("#### Horas indirectas específicas por CESFAM")
        st.caption("Estas horas tienen prioridad sobre la lista general. Celdas vacías usan la lista general.")

        df_hc_all = db_rev.get_horas_cesfam()
        if not df_hc_all.empty:
            pivot = df_hc_all.pivot_table(
                index="encargatura", columns="cesfam", values="horas", aggfunc="first"
            ).reset_index()
            st.dataframe(pivot, use_container_width=True, height=400)
        else:
            st.info("No hay datos en la matriz por CESFAM.")

        st.divider()
        st.markdown("#### ➕ Agregar / Actualizar entrada")
        ca, cb, cc = st.columns(3)
        hc_cesfam  = ca.text_input("CESFAM", key="hc_cesfam", placeholder="ej: CESFAM Ahues")
        hc_encarg  = cb.text_input("Encargatura", key="hc_encarg",
                                    placeholder="ej: Jefe de Sector")
        hc_horas   = cc.number_input("Hrs semanales", min_value=0.0, step=0.25, key="hc_horas")
        if st.button("💾 Guardar", key="hc_save"):
            if hc_cesfam.strip() and hc_encarg.strip():
                db_rev.upsert_hora_cesfam(hc_cesfam.strip(), hc_encarg.strip(), float(hc_horas))
                st.success("Entrada guardada.")
                st.rerun()
            else:
                st.warning("Completa CESFAM y Encargatura.")

        if not df_hc_all.empty:
            st.divider()
            st.markdown("#### 🗑️ Eliminar entrada")
            hc_opts = [f"{r['cesfam']} | {r['encargatura']}" for _, r in df_hc_all.iterrows()]
            hc_del  = st.selectbox("Seleccionar:", ["— —"] + hc_opts, key="hc_del_sel")
            if st.button("Eliminar", key="hc_del_btn"):
                if hc_del != "— —":
                    idx = hc_opts.index(hc_del)
                    db_rev.delete_hora_cesfam(df_hc_all.iloc[idx]["id"])
                    st.rerun()

    # ── Sub-tab: Importar ──────────────────────────────────────────────────────
    with sub_import:
        st.markdown("#### 📥 Importar Horas Indirectas desde Excel")
        st.markdown("""
**Formato aceptado para hoja de horas generales:**
Columnas: `tipo` | `nombre` | `horas`

**Formato aceptado para hoja de matriz CESFAM:**
Columnas: `encargatura` | `CESFAM Nº1` | `CESFAM Ahues` | ... (un CESFAM por columna)
O bien columnas: `cesfam` | `encargatura` | `horas` (formato largo)
        """)

        up_horas = st.file_uploader("Archivo Excel", type=["xlsx", "xls", "xlsm"], key="hrs_up")
        if up_horas:
            try:
                xl = pd.ExcelFile(up_horas)
                st.info(f"Hojas disponibles: {xl.sheet_names}")
                hoja_sel = st.selectbox("Seleccionar hoja", xl.sheet_names, key="hrs_hoja")
                hoja_tipo = st.radio("Tipo de datos:", ["General (tipo|nombre|horas)",
                                                         "Matriz CESFAM (encargatura en filas, CESFAM en columnas)",
                                                         "Largo (cesfam|encargatura|horas)"],
                                     key="hrs_tipo")
                if st.button("📥 Importar hoja", key="hrs_import"):
                    df_imp = pd.read_excel(up_horas, sheet_name=hoja_sel)
                    df_imp.columns = [str(c).strip() for c in df_imp.columns]

                    if "General" in hoja_tipo:
                        cols_l = {c.lower(): c for c in df_imp.columns}
                        for _, rw in df_imp.iterrows():
                            nom = str(rw.get(cols_l.get("nombre", ""), "")).strip()
                            tip = str(rw.get(cols_l.get("tipo", ""), "INDIVIDUAL")).strip()
                            hrs = float(str(rw.get(cols_l.get("horas", ""), 0)).replace(",", ".") or 0)
                            if nom:
                                db_rev.upsert_hora_general(nom, tip, hrs)
                        st.success(f"Importadas {len(df_imp)} filas a lista general.")

                    elif "Matriz" in hoja_tipo:
                        # Primera columna = encargatura, resto = CESFAM
                        col_enc = df_imp.columns[0]
                        cesfam_cols = df_imp.columns[1:].tolist()
                        for _, rw in df_imp.iterrows():
                            encarg = str(rw[col_enc]).strip()
                            if not encarg or encarg.lower() in _NULL_STRS:
                                continue
                            for cf in cesfam_cols:
                                val = str(rw[cf]).strip()
                                if val and val.lower() not in _NULL_STRS and val.lower() != "na":
                                    try:
                                        db_rev.upsert_hora_cesfam(cf.strip(), encarg, float(val.replace(",", ".")))
                                    except Exception:
                                        pass
                        st.success("Importada matriz CESFAM.")

                    else:  # Largo
                        cols_l = {c.lower(): c for c in df_imp.columns}
                        for _, rw in df_imp.iterrows():
                            cf    = str(rw.get(cols_l.get("cesfam", ""), "")).strip()
                            encarg= str(rw.get(cols_l.get("encargatura", ""), "")).strip()
                            hrs   = float(str(rw.get(cols_l.get("horas", ""), 0)).replace(",", ".") or 0)
                            if cf and encarg:
                                db_rev.upsert_hora_cesfam(cf, encarg, hrs)
                        st.success(f"Importadas {len(df_imp)} filas (formato largo).")

                    st.rerun()
            except Exception as e:
                st.error(f"Error importando: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — REPOSITORIO MENSUAL
# ══════════════════════════════════════════════════════════════════════════════

with tab_repo:
    st.markdown("### 📊 Repositorio Mensual de Revisión de Dotación")
    st.caption("Histórico estable. Los registros se actualizan al re-guardar, no se borran automáticamente.")

    meses_disp = db_rev.get_meses_disponibles()
    if not meses_disp:
        st.info("No hay revisiones guardadas. Usa la pestaña **🏥 Vista por Centro** para generar y guardar.")
    else:
        rm_a, rm_b, rm_c = st.columns([2, 2, 2])
        mes_repo  = rm_a.selectbox("Período", meses_disp, key="repo_mes")
        cesfam_disp_repo = ["(Todos)"] + sorted(
            db_rev.get_revision_mensual(mes_repo)["cesfam"].dropna().unique().tolist()
            if mes_repo else []
        )
        cesfam_repo = rm_b.selectbox("Centro", cesfam_disp_repo, key="repo_cesfam")

        df_repo = db_rev.get_revision_mensual(
            mes_repo,
            cesfam_repo if cesfam_repo != "(Todos)" else None,
        )

        if df_repo.empty:
            st.info("Sin registros para este período/centro.")
        else:
            # KPIs del repositorio
            rk1, rk2, rk3, rk4 = st.columns(4)
            rk1.metric("Funcionarios", len(df_repo))
            rk2.metric("Hrs Contrato", f"{pd.to_numeric(df_repo['horas_contrato'], errors='coerce').sum():.1f}")
            rk3.metric("Hrs Indirectas", f"{pd.to_numeric(df_repo['horas_indirectas_total'], errors='coerce').sum():.1f}")
            rk4.metric("Hrs Clínicas", f"{pd.to_numeric(df_repo['horas_clinicas'], errors='coerce').sum():.1f}")

            # Tabla con highlight de horas clínicas
            cols_show = [c for c in [
                "nombre", "cesfam", "calidad_juridica", "descripcion_cargo",
                "unidad_desempeno", "horas_contrato", "horas_indirectas_total",
                "horas_clinicas", "observaciones",
            ] if c in df_repo.columns]
            df_show = df_repo[cols_show].copy()
            df_show.columns = [c.replace("_", " ").title() for c in df_show.columns]

            st.markdown(ev_design.ev_table_html(
                df_show,
                highlight_cols=["Horas Clinicas"],
            ), unsafe_allow_html=True)

            # Descarga
            st.markdown("---")
            dl_repo = io.BytesIO()
            df_repo.to_excel(dl_repo, index=False)
            dl_repo.seek(0)
            st.download_button(
                f"📥 Descargar repositorio — {mes_repo}",
                data=dl_repo,
                file_name=f"revision_dotacion_{mes_repo}_{cesfam_repo}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key="repo_dl",
            )

        # Borrar período
        with rm_c:
            st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
            with st.expander("🗑️ Borrar período"):
                st.warning(f"Esto borrará **todos** los registros de `{mes_repo}` "
                           + (f"para `{cesfam_repo}`" if cesfam_repo != "(Todos)" else ""))
                if st.button("Confirmar borrado", key="repo_del_confirm"):
                    db_rev.delete_revision_mensual(
                        mes_repo,
                        cesfam_repo if cesfam_repo != "(Todos)" else None,
                    )
                    st.success("Registros eliminados.")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — DOTACIÓN IDEAL
# ══════════════════════════════════════════════════════════════════════════════

with tab_ideal:
    st.markdown("### 📐 Dotación Ideal por Centro")
    st.caption(
        "Define la dotación ideal por estamento/cargo para cada CESFAM. "
        "Se usa para calcular la brecha vs dotación real en la pestaña **🔍 Brecha**. "
        "Puedes importar la hoja 'MATRIZ DE EVALUACIÓN CENTRO' del libro REVISIÓN DOTACIONES."
    )

    df_ideal_all = db_rev.get_dotacion_ideal()

    i_cesfam_opts = sorted(df_ideal_all["cesfam"].unique().tolist()) if not df_ideal_all.empty else []
    id_a, id_b = st.columns([2, 3])
    cesfam_ideal = id_a.selectbox("CESFAM", ["(Todos)"] + i_cesfam_opts, key="ideal_cesfam")
    df_ideal_show = db_rev.get_dotacion_ideal(
        cesfam_ideal if cesfam_ideal != "(Todos)" else None
    )

    if not df_ideal_show.empty:
        st.dataframe(
            df_ideal_show.drop(columns=["id"]),
            use_container_width=True, height=350,
        )
        # Pivot por CESFAM
        if cesfam_ideal == "(Todos)":
            pivot_ideal = df_ideal_show.pivot_table(
                index=["estamento", "cargo"],
                columns="cesfam",
                values="horas_ideal",
                aggfunc="first",
            )
            st.markdown("**Vista Matriz:**")
            st.dataframe(pivot_ideal, use_container_width=True)
    else:
        st.info("Sin datos de dotación ideal. Agrega manualmente o importa desde Excel.")

    st.divider()
    st.markdown("#### ➕ Agregar / Actualizar entrada ideal")
    ia, ib, ic, id_, ie = st.columns(5)
    id_cesfam_new  = ia.text_input("CESFAM", key="id_new_cesfam")
    id_estamento   = ib.text_input("Estamento", key="id_new_est", placeholder="ej: MÉDICO")
    id_cargo       = ic.text_input("Cargo", key="id_new_cargo", placeholder="ej: Médico General")
    id_hrs_ideal   = id_.number_input("Hrs ideal", min_value=0.0, step=0.5, key="id_new_hrs")
    id_n_ideal     = ie.number_input("N° ideal", min_value=0.0, step=0.5, key="id_new_n")
    if st.button("💾 Guardar entrada ideal", key="id_save"):
        if id_cesfam_new.strip() and id_estamento.strip():
            db_rev.upsert_dotacion_ideal(
                id_cesfam_new.strip(), id_estamento.strip(),
                id_cargo.strip(), float(id_hrs_ideal), float(id_n_ideal),
            )
            st.success("Entrada guardada.")
            st.rerun()

    st.divider()
    st.markdown("#### 📥 Importar desde Excel")
    st.caption(
        "Formato requerido — columnas: `cesfam` | `estamento` | `cargo` | `horas_ideal` | `n_ideal`  \n"
        "También acepta la hoja 'MATRIZ DE EVALUACIÓN CENTRO' con formato de tabla Excel."
    )
    up_ideal = st.file_uploader("Excel de dotación ideal", type=["xlsx", "xls", "xlsm"], key="ideal_up")
    if up_ideal:
        try:
            xl_i = pd.ExcelFile(up_ideal)
            hoja_i = st.selectbox("Hoja", xl_i.sheet_names, key="ideal_hoja")
            if st.button("📥 Importar", key="ideal_import_btn"):
                df_i = pd.read_excel(up_ideal, sheet_name=hoja_i)
                df_i.columns = [str(c).strip().lower() for c in df_i.columns]
                req_cols = {"cesfam", "estamento", "cargo", "horas_ideal"}
                if req_cols.issubset(set(df_i.columns)):
                    db_rev.import_dotacion_ideal_from_df(df_i.rename(columns={
                        c: c for c in df_i.columns
                    }))
                    st.success(f"Importadas {len(df_i)} filas.")
                    st.rerun()
                else:
                    # Intentar formato ancho: CESFAM en columnas, encargatura en filas
                    st.warning(
                        f"Columnas encontradas: {list(df_i.columns)}. "
                        "Asegúrate de tener: cesfam, estamento, cargo, horas_ideal, n_ideal"
                    )
        except Exception as e:
            st.error(f"Error: {e}")

    if not df_ideal_show.empty:
        dl_ideal = io.BytesIO()
        df_ideal_show.to_excel(dl_ideal, index=False)
        dl_ideal.seek(0)
        st.download_button(
            "📥 Descargar dotación ideal",
            data=dl_ideal,
            file_name="dotacion_ideal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, key="ideal_dl",
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — BRECHA VS IDEAL
# ══════════════════════════════════════════════════════════════════════════════

with tab_brecha:
    st.markdown("### 🔍 Análisis de Brecha — Dotación Real vs Ideal")

    meses_b = db_rev.get_meses_disponibles()
    cesfam_b_opts = []

    if not meses_b:
        st.info("Sin datos en el repositorio. Guarda al menos una revisión mensual para analizar la brecha.")
    else:
        ba, bb = st.columns([2, 3])
        mes_brecha = ba.selectbox("Período", meses_b, key="brecha_mes")
        df_rev_b = db_rev.get_revision_mensual(mes_brecha)
        cesfam_b_opts = ["(Todos)"] + sorted(df_rev_b["cesfam"].dropna().unique().tolist()) if not df_rev_b.empty else ["(Todos)"]
        cesfam_b = bb.selectbox("Centro de Salud", cesfam_b_opts, key="brecha_cesfam")

        if cesfam_b != "(Todos)":
            df_rev_b = df_rev_b[df_rev_b["cesfam"] == cesfam_b]

        df_ideal_b = db_rev.get_dotacion_ideal(
            cesfam_b if cesfam_b != "(Todos)" else None
        )

        if df_rev_b.empty:
            st.info("Sin revisiones guardadas para este período/centro.")
        else:
            st.divider()
            st.markdown("#### 📊 Resumen por cargo/estamento")

            # Agrupar dotación real por cargo
            df_real_grp = df_rev_b.groupby("descripcion_cargo").agg(
                n_real=("rut", "count"),
                hrs_contrato_total=("horas_contrato", lambda x: pd.to_numeric(x, errors="coerce").sum()),
                hrs_indir_total=("horas_indirectas_total", lambda x: pd.to_numeric(x, errors="coerce").sum()),
                hrs_clin_total=("horas_clinicas", lambda x: pd.to_numeric(x, errors="coerce").sum()),
            ).reset_index()
            df_real_grp.columns = ["Cargo", "N Real", "Hrs Contrato", "Hrs Indirectas", "Hrs Clínicas"]

            if not df_ideal_b.empty:
                # Merge con ideal
                df_ideal_grp = df_ideal_b.groupby("cargo").agg(
                    n_ideal=("n_ideal", "sum"),
                    hrs_ideal=("horas_ideal", "sum"),
                ).reset_index()
                df_ideal_grp.columns = ["Cargo", "N Ideal", "Hrs Ideal"]
                df_brecha = df_real_grp.merge(df_ideal_grp, on="Cargo", how="outer").fillna(0)
                df_brecha["Brecha N"]   = (df_brecha["N Real"] - df_brecha["N Ideal"]).round(1)
                df_brecha["Brecha Hrs"] = (df_brecha["Hrs Clínicas"] - df_brecha["Hrs Ideal"]).round(1)
            else:
                df_brecha = df_real_grp
                df_brecha["N Ideal"]   = "—"
                df_brecha["Hrs Ideal"] = "—"
                df_brecha["Brecha N"]  = "—"
                df_brecha["Brecha Hrs"]= "—"

            # Visualización con semáforo de brecha
            def _brecha_html(df: pd.DataFrame) -> str:
                cols = list(df.columns)
                th = "".join(
                    f'<th style="padding:8px 10px;text-align:left;font-size:11px;'
                    f'font-weight:600;color:#b3b3b3;border-bottom:1px solid rgba(255,255,255,.07);">{c}</th>'
                    for c in cols
                )
                rows_h = ""
                for i, (_, r) in enumerate(df.iterrows()):
                    bg = "#1f1f1f" if i % 2 else "#181818"
                    cells = ""
                    for c in cols:
                        v = r[c]
                        if c in ("Brecha N", "Brecha Hrs"):
                            try:
                                fv = float(v)
                                clr = "#1db954" if fv >= 0 else "#ef4444"
                                txt = f"+{fv:.1f}" if fv > 0 else f"{fv:.1f}"
                            except Exception:
                                clr = "#b3b3b3"; txt = str(v)
                            cells += (f'<td style="padding:7px 10px;color:{clr};'
                                      f'font-weight:700;font-size:13px;text-align:right;">{txt}</td>')
                        elif c in ("Hrs Clínicas", "Hrs Ideal"):
                            cells += (f'<td style="padding:7px 10px;color:#4a9eff;'
                                      f'font-size:13px;text-align:right;">{v}</td>')
                        else:
                            cells += (f'<td style="padding:7px 10px;color:#fff;'
                                      f'font-size:12px;white-space:nowrap;">{v}</td>')
                    rows_h += f'<tr style="background:{bg};">{cells}</tr>'
                return (f'<div style="overflow-x:auto;border-radius:8px;'
                        f'border:1px solid rgba(255,255,255,.07);">'
                        f'<table style="width:100%;border-collapse:collapse;font-family:Outfit,sans-serif;">'
                        f'<thead><tr style="background:#1a1a1a;">{th}</tr></thead>'
                        f'<tbody>{rows_h}</tbody></table></div>')

            st.markdown(_brecha_html(df_brecha), unsafe_allow_html=True)

            st.divider()
            st.markdown("#### 📊 Distribución de Horas Clínicas por Unidad de Desempeño")

            if "unidad_desempeno" in df_rev_b.columns:
                df_rev_b["horas_clinicas_num"] = pd.to_numeric(df_rev_b["horas_clinicas"], errors="coerce")
                df_ud_grp = df_rev_b.groupby("unidad_desempeno")["horas_clinicas_num"].sum().reset_index()
                df_ud_grp.columns = ["Unidad de Desempeño", "Hrs Clínicas"]
                df_ud_grp = df_ud_grp.sort_values("Hrs Clínicas", ascending=False)
                st.markdown(ev_design.ev_table_html(df_ud_grp), unsafe_allow_html=True)

            st.divider()

            # Descarga de brecha
            dl_br = io.BytesIO()
            df_brecha.to_excel(dl_br, index=False)
            dl_br.seek(0)
            st.download_button(
                f"📥 Descargar análisis de brecha — {mes_brecha}",
                data=dl_br,
                file_name=f"brecha_dotacion_{mes_brecha}_{cesfam_b}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key="brecha_dl",
            )

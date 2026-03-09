# -*- coding: utf-8 -*-
# evidant Suite — Inicio.py v8 (Spotify Edition)
# Diseño completo estilo Spotify + navbar funcional via ev_design

import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ev_design

st.set_page_config(
    page_title="Evidant Suite · DAP SSMC",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Navbar + CSS Spotify ──────────────────────────────────────────────────────
ev_design.render(current="inicio")

# ── CSS adicional para la home ────────────────────────────────────────────────
st.markdown("""
<style>
/* Hero gradient background */
.home-hero {
  padding: 5rem 2rem 4.5rem;
  text-align: center;
  background:
    radial-gradient(ellipse 80% 60% at 50% 0%,  rgba(29,185,84,.09) 0%, transparent 65%),
    radial-gradient(ellipse 50% 40% at 80% 80%, rgba(74,158,255,.05) 0%, transparent 60%);
  position: relative;
}
.home-hero-eyebrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: .58rem;
  letter-spacing: 3.5px;
  text-transform: uppercase;
  color: #1db954;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: .8rem;
  justify-content: center;
}
.home-hero-line {
  display: block;
  width: 2.5rem;
  height: 1px;
  background: rgba(29,185,84,.4);
}
.home-hero-title {
  font-family: 'Cabinet Grotesk', sans-serif;
  font-size: clamp(3.2rem, 8vw, 6rem);
  font-weight: 900;
  line-height: .9;
  letter-spacing: -4px;
  margin-bottom: 1.5rem;
}
.home-hero-title .t-green {
  background: linear-gradient(135deg, #fff 0%, #a8f0c0 30%, #1db954 60%, #1ed760 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.home-hero-title .t-dim { color: rgba(255,255,255,.06); }
.home-hero-desc {
  font-size: 1.05rem;
  color: #b3b3b3;
  max-width: 540px;
  margin: 0 auto 3rem;
  line-height: 1.78;
}
.home-stats {
  display: inline-flex;
  align-items: center;
  gap: 2.5rem;
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.07);
  border-radius: 50px;
  padding: 1rem 2.5rem;
}
.home-stat-val {
  font-family: 'Cabinet Grotesk', sans-serif;
  font-size: 1.7rem;
  font-weight: 900;
  background: linear-gradient(135deg, #1db954, #1ed760);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
}
.home-stat-lbl {
  font-family: 'JetBrains Mono', monospace;
  font-size: .48rem;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: #333;
  margin-top: .3rem;
}
.home-stat-sep { width:1px; height:2.5rem; background:rgba(255,255,255,.07); }

/* Module cards */
.module-card {
  background: #181818;
  border: 1px solid rgba(255,255,255,.07);
  border-radius: 14px;
  padding: 1.5rem;
  min-height: 290px;
  display: flex;
  flex-direction: column;
  gap: .9rem;
  transition: background .2s, border-color .2s, transform .2s, box-shadow .2s;
  cursor: default;
}
.module-card:hover {
  background: #242424;
  border-color: rgba(255,255,255,.13);
  transform: translateY(-3px);
  box-shadow: 0 8px 32px rgba(0,0,0,.5);
}
.module-card-top { border-top: 2px solid var(--accent, #1db954); }
.step-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: .52rem;
  font-weight: 700;
  padding: .15rem .45rem;
  border-radius: 4px;
  background: rgba(255,255,255,.07);
  color: #535353;
  letter-spacing: .5px;
}
.module-title {
  font-family: 'Cabinet Grotesk', sans-serif;
  font-size: 1rem;
  font-weight: 800;
  color: #fff;
  line-height: 1.25;
}
.module-desc { font-size: .82rem; color: #b3b3b3; line-height: 1.65; flex: 1; }
.module-tag {
  display: inline-flex;
  align-items: center;
  font-size: .55rem;
  text-transform: uppercase;
  font-family: 'JetBrains Mono', monospace;
  padding: .1rem .38rem;
  border-radius: 20px;
  background: rgba(255,255,255,.05);
  color: #535353;
  border: 1px solid rgba(255,255,255,.06);
}

/* Section title */
.section-hdr {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 3rem 2rem 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255,255,255,.07);
}
.sec-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: .58rem;
  letter-spacing: 2px;
  color: #1db954;
  font-weight: 700;
}
.sec-title {
  font-family: 'Cabinet Grotesk', sans-serif;
  font-size: 1.1rem;
  font-weight: 900;
  color: #fff;
}
.sec-sub {
  font-size: .7rem;
  color: #333;
  margin-left: auto;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: .5px;
}

/* Notice / alert box */
.ev-notice {
  display: flex;
  align-items: center;
  gap: .9rem;
  background: rgba(29,185,84,.05);
  border: 1px solid rgba(29,185,84,.15);
  border-radius: 10px;
  padding: .85rem 1.4rem;
  margin-bottom: 1.4rem;
  font-size: .84rem;
  color: #86a093;
}
.ev-notice strong { color: #1db954; }
.ev-notice-gold {
  background: rgba(245,158,11,.05);
  border-color: rgba(245,158,11,.18);
  color: #b09060;
}
.ev-notice-gold strong { color: #f59e0b; }

/* Feature list */
.feat-list { display: flex; flex-direction: column; gap: .55rem; }
.feat-item {
  display: flex;
  align-items: flex-start;
  gap: .6rem;
  font-size: .82rem;
  color: #b3b3b3;
  line-height: 1.5;
}
.feat-dot {
  width: 5px; height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: .48rem;
}

/* Footer */
.ev-footer {
  text-align: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: .52rem;
  color: #1e1e1e;
  padding: 1.8rem 0;
  border-top: 1px solid rgba(255,255,255,.04);
  margin-top: 3rem;
}

/* Padding de contenido */
.ev-main { padding: 0 2rem 2rem; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="home-hero">
  <div class="home-hero-eyebrow">
    <span class="home-hero-line"></span>
    Plataforma de Gestión · Subtítulo 21 · DAP SSMC
    <span class="home-hero-line"></span>
  </div>
  <div class="home-hero-title">
    <span class="t-green">Evidant</span><br>
    <span class="t-dim">Suite</span>
  </div>
  <div class="home-hero-desc">
    Control integral del gasto en remuneraciones y gestión presupuestaria de la
    <strong style="color:#cce0f8;">Dirección de Atención Primaria</strong>
    del Servicio de Salud Metropolitano Central.
  </div>
  <div class="home-stats">
    <div>
      <div class="home-stat-val">5</div>
      <div class="home-stat-lbl">Módulos</div>
    </div>
    <div class="home-stat-sep"></div>
    <div>
      <div class="home-stat-val">4</div>
      <div class="home-stat-lbl">Pasos</div>
    </div>
    <div class="home-stat-sep"></div>
    <div>
      <div class="home-stat-val">21</div>
      <div class="home-stat-lbl">Subtítulo</div>
    </div>
    <div class="home-stat-sep"></div>
    <div>
      <div class="home-stat-val">DAP</div>
      <div class="home-stat-lbl">SSMC</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — PROCESAMIENTO FINANCIERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-hdr">
  <span class="sec-num">01</span>
  <span class="sec-title">Procesamiento Financiero</span>
  <span class="sec-sub">Flujo secuencial · 4 pasos · Ejecución mensual</span>
</div>
""", unsafe_allow_html=True)

PASOS = [
    ("📂", "PASO 1", "Consolidación de Reportes",
     ["Consolidado","Multi-hoja","Triple encabezado"],
     "Une múltiples hojas del Excel preservando el encabezado triple (3 filas). Actualiza automáticamente el Repositorio RR.HH.",
     "pages/4_Consolidacion_Remu.py", "#1db954"),
    ("🔄", "PASO 2", "Redistribución PRAPS vs DAP",
     ["Redistribución","Reintegros","Auditoría"],
     "Elimina pares de reintegros y redistribuye montos entre centros PRAPS y D.A.P. Genera resumen, resultados y auditoría Excel.",
     "pages/1_Redistribucion.py", "#4a9eff"),
    ("📊", "PASO 3", "Programa Financiero CASA",
     ["PF Anual","Multi-ley","Filtros CC"],
     "Genera la planilla de Programa Financiero desde la base redistribuida. Produce hojas PF_MES y PF_ANUAL.",
     "pages/2_Programa_Financiero.py", "#a855f7"),
    ("📋", "PASO 4", "Generador de Rendiciones",
     ["Rendiciones","Honorarios","Homologación"],
     "Consolida remuneraciones y honorarios. Produce el archivo de rendiciones con homologación de programas y trazabilidad.",
     "pages/3_Rendiciones.py", "#00d4ff"),
]

st.markdown('<div class="ev-main">', unsafe_allow_html=True)
cols = st.columns(4, gap="small")
for i, (icon, step, title, tags, desc, page, color) in enumerate(PASOS):
    with cols[i]:
        tag_html = "".join(
            f'<span class="module-tag">{t}</span>' for t in tags
        )
        st.markdown(
            f'<div class="module-card module-card-top" style="--accent:{color};">'
            f'<div style="display:flex;align-items:center;gap:.6rem;">'
            f'<span class="step-badge">{step}</span>'
            f'<span style="font-size:1.25rem;">{icon}</span>'
            f'</div>'
            f'<div class="module-title">{title}</div>'
            f'<div style="display:flex;gap:.2rem;flex-wrap:wrap;">{tag_html}</div>'
            f'<div class="module-desc">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.page_link(page, label=f"Abrir Paso {i+1} →", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — GESTIÓN PRESUPUESTARIA
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-hdr">
  <span class="sec-num">02</span>
  <span class="sec-title">Gestión Presupuestaria</span>
  <span class="sec-sub">Ejecución mensual · Marcos CC · Dotación y costo</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="ev-main">', unsafe_allow_html=True)
cp1, cp2, cp3 = st.columns([1.5, 1, 1], gap="medium")

with cp1:
    st.markdown(
        '<div class="module-card module-card-top" style="--accent:#1db954;min-height:360px;">'
        '<div style="font-size:1.9rem;">💰</div>'
        '<div class="module-title">Gestión de Presupuesto</div>'
        '<div style="display:flex;gap:.2rem;flex-wrap:wrap;">'
        '<span class="module-tag">Marcos Anuales</span>'
        '<span class="module-tag">Imputación Mensual</span>'
        '<span class="module-tag">Dashboard KPI</span>'
        '<span class="module-tag">Pivot Mensual</span>'
        '</div>'
        '<div class="module-desc">Configura centros de costo con marcos anuales. '
        'Imputa rendiciones mes a mes con detección de duplicados. '
        'Dashboard con semáforo presupuestario y tablas pivot tipo Excel.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/5_Gestion_Presupuesto.py", label="Abrir Gestión Presupuestaria →", use_container_width=True)


def feat_block(items, dot_color):
    rows = "".join(
        f'<div class="feat-item">'
        f'<div class="feat-dot" style="background:{dot_color};"></div>'
        f'<span>{x}</span></div>' for x in items
    )
    return rows


with cp2:
    st.markdown(
        '<div class="module-card" style="height:100%;">'
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:.52rem;'
        'font-weight:700;letter-spacing:2px;text-transform:uppercase;'
        'color:#333;margin-bottom:1rem;">Dashboard & KPIs</div>'
        '<div class="feat-list">'
        + feat_block([
            "KPIs: Haber Neto, Total Haberes, Descuentos, Marco",
            "Semáforo presupuestario por CC (Normal/Alerta/Crítico)",
            "Evolución mensual del gasto",
            "Distribución por programa Top 10",
        ], "#1db954") +
        '</div></div>',
        unsafe_allow_html=True,
    )

with cp3:
    st.markdown(
        '<div class="module-card" style="height:100%;">'
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:.52rem;'
        'font-weight:700;letter-spacing:2px;text-transform:uppercase;'
        'color:#333;margin-bottom:1rem;">Estado Mensual & Análisis</div>'
        '<div class="feat-list">'
        + feat_block([
            "Pivot Resolución × Mes × 3 métricas",
            "Imputación con anti-duplicado automático",
            "Análisis Honorarios vs Remuneraciones",
            "Homologación semántica calidad jurídica",
            "Exportación Excel multihoja",
        ], "#1db954") +
        '</div></div>',
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — GESTIÓN RECURSO HUMANO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-hdr">
  <span class="sec-num">03</span>
  <span class="sec-title">Gestión del Recurso Humano</span>
  <span class="sec-sub">Repositorio persistente · Historial · Fichas contractuales</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="ev-main">', unsafe_allow_html=True)

st.markdown(
    '<div class="ev-notice ev-notice-gold">'
    '<span style="font-size:1.1rem;flex-shrink:0;">🔒</span>'
    '<span><strong>Datos permanentes:</strong> El repositorio usa SQLite local — '
    'los contratos e historial <strong>no se borran al reiniciar la aplicación</strong>. '
    'Se actualiza automáticamente al procesar el Paso 1.</span>'
    '</div>',
    unsafe_allow_html=True,
)

rh1, rh2 = st.columns([1, 1], gap="medium")

with rh1:
    st.markdown(
        '<div class="module-card module-card-top" style="--accent:#f59e0b;min-height:340px;">'
        '<div style="font-size:1.9rem;">🗄️</div>'
        '<div class="module-title">Repositorio RR.HH.</div>'
        '<div style="display:flex;gap:.2rem;flex-wrap:wrap;">'
        '<span class="module-tag">Contratos</span>'
        '<span class="module-tag">Historial Cambios</span>'
        '<span class="module-tag">SQLite Persistente</span>'
        '<span class="module-tag">No se borra</span>'
        '</div>'
        '<div class="module-desc">Base de datos persistente de contratos del personal. '
        'Se actualiza desde el Paso 1 conservando historial completo de cambios. '
        'Fichas editables con 15 campos contractuales. '
        'Búsqueda por RUT, nombre o contrato. Dashboard por CC y Planta.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/0_Repositorio_RRHH.py", label="Abrir Repositorio RR.HH. →", use_container_width=True)

with rh2:
    st.markdown(
        '<div class="module-card" style="height:100%;">'
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:.52rem;'
        'font-weight:700;letter-spacing:2px;text-transform:uppercase;'
        'color:#333;margin-bottom:1rem;">Funcionalidades incluidas</div>'
        '<div class="feat-list">'
        + feat_block([
            "Auto-carga desde Paso 1 (Consolidación)",
            "Historial completo de modificaciones por contrato",
            "Ficha editable por contrato — 15 campos",
            "Búsqueda por RUT, nombre o N° contrato",
            "Dashboard con gráficos por CC y Planta",
            "SQLite persistente — no se borra al reiniciar",
            "ID_CONTRATO determinístico por RUT + CC",
            "Exportación Excel del repositorio completo",
        ], "#f59e0b") +
        '</div></div>',
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — PROCESAMIENTO DE IMÁGENES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="section-hdr">
  <span class="sec-num">04</span>
  <span class="sec-title">Procesamiento de Imágenes</span>
  <span class="sec-sub">OCR · Clasificación PDF · Descarga automática SIRH</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="ev-main">', unsafe_allow_html=True)

img1, img2 = st.columns([1, 1], gap="medium")

with img1:
    st.markdown(
        '<div class="module-card module-card-top" style="--accent:#a855f7;min-height:320px;">'
        '<div style="font-size:1.9rem;">🖼</div>'
        '<div class="module-title">Clasificador PDF por Etiquetas</div>'
        '<div style="display:flex;gap:.2rem;flex-wrap:wrap;">'
        '<span class="module-tag">Excel ETIQUETAS</span>'
        '<span class="module-tag">Match RUT + N°Doc</span>'
        '<span class="module-tag">Por Programa/CC</span>'
        '<span class="module-tag">Reporte Excel</span>'
        '</div>'
        '<div class="module-desc">'
        'Clasifica PDFs (ACCESORIAS / HSA / TIT-CONT) usando un Excel de etiquetas. '
        'Hace match por clave (RUT sin DV + N° Documento) y organiza la salida '
        'en carpetas por Programa y Centro de Salud.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/6_Procesamiento_Imagenes.py", label="Abrir Clasificador →", use_container_width=True)

with img2:
    st.markdown(
        '<div class="module-card module-card-top" style="--accent:#1db954;min-height:320px;">'
        '<div style="font-size:1.9rem;">👥</div>'
        '<div class="module-title">Gestión de Dotación</div>'
        '<div style="display:flex;gap:.2rem;flex-wrap:wrap;">'
        '<span class="module-tag">SIRH Export</span>'
        '<span class="module-tag">Contrato Vigente</span>'
        '<span class="module-tag">Alertas SIRH</span>'
        '<span class="module-tag">Repositorio Actualizable</span>'
        '</div>'
        '<div class="module-desc">'
        'Repositorio persistente de dotación vigente. Detecta el último contrato '
        'activo por funcionario, controla bloques de horas y alerta sobre '
        'inconsistencias en Título para corrección en SIRH.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.page_link("pages/7_Dotacion.py", label="Abrir Dotación →", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ev-footer">
  Evidant Suite &nbsp;·&nbsp; Control Subtítulo 21 &nbsp;·&nbsp;
  Dirección de Atención Primaria &nbsp;·&nbsp; SSMC &nbsp;·&nbsp; 2025
</div>
""", unsafe_allow_html=True)

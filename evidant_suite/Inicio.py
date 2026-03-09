# -*- coding: utf-8 -*-
# Evidant Suite — Inicio.py v7 — Streamlit nativo puro, sin iframes
# Navegacion 100% con st.switch_page(), diseno dark con CSS override total

import streamlit as st

st.set_page_config(
    page_title="Evidant Suite · DAP SSMC",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=Inter:wght@300;400;500;600&display=swap');
:root {
  --bg:#050c17;--surface:#0a1522;--card:#0d1b2e;--card2:#101f35;
  --border:rgba(255,255,255,.06);--border2:rgba(0,148,255,.18);
  --blue:#0066ff;--blue2:#0094ff;--cyan:#00ccff;--green:#00e09a;--gold:#f0b340;
  --t1:#eef4ff;--t2:#8daac8;--t3:#445a72;
  --ff:'Inter',sans-serif;--fd:'Syne',sans-serif;--fm:'DM Mono',monospace;
}
html,body,[class*="css"],.stApp,.stAppViewContainer,
[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="block-container"],
.main,.block-container {
  background-color:var(--bg)!important;background:var(--bg)!important;
  color:var(--t1)!important;font-family:var(--ff)!important;
}
#MainMenu,footer,header,[data-testid="stHeader"],[data-testid="stToolbar"],
[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important;visibility:hidden!important;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#060e1c,#081524)!important;border-right:1px solid rgba(255,255,255,.05)!important;}
[data-testid="stSidebar"] *{color:var(--t1)!important;}
.block-container{padding:0!important;max-width:100%!important;}
[data-testid="stMain"] > div{padding:0!important;}
.stButton > button{
  background:linear-gradient(135deg,#0055dd,#0094ff)!important;
  color:#fff!important;border:none!important;border-radius:9px!important;
  font-weight:600!important;font-size:.9rem!important;padding:.62rem 1.2rem!important;
  width:100%!important;transition:all .18s!important;font-family:var(--ff)!important;
}
.stButton > button:hover{box-shadow:0 4px 20px rgba(0,100,255,.4)!important;transform:translateY(-1px)!important;}
hr{border-color:rgba(255,255,255,.06)!important;margin:2.5rem 0!important;}
</style>
""", unsafe_allow_html=True)


with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:.9rem 0 1.4rem">'
        '<div style="font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;'
        'background:linear-gradient(135deg,#0094ff,#00ccff);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">evidant</div>'
        '<div style="font-size:.52rem;color:#3a5570;letter-spacing:3px;'
        'text-transform:uppercase;margin-top:.2rem;font-family:monospace;">Suite · DAP SSMC</div>'
        '</div>',
        unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div style="font-size:.58rem;color:#2a4560;letter-spacing:2px;font-weight:700;'
                'text-transform:uppercase;padding:.2rem .4rem .5rem;font-family:monospace;">'
                '⚙ PROCESAMIENTO FINANCIERO</div>', unsafe_allow_html=True)
    st.page_link("pages/4_Consolidacion_Remu.py", label="📂  Paso 1 · Consolidación")
    st.page_link("pages/1_Redistribucion.py",      label="🔄  Paso 2 · Redistribución")
    st.page_link("pages/2_Programa_Financiero.py", label="📊  Paso 3 · Prog. Financiero")
    st.page_link("pages/3_Rendiciones.py",         label="📋  Paso 4 · Rendiciones")
    st.markdown("---")
    st.markdown('<div style="font-size:.58rem;color:#2a4560;letter-spacing:2px;font-weight:700;'
                'text-transform:uppercase;padding:.2rem .4rem .5rem;font-family:monospace;">'
                '💰 GESTIÓN PRESUPUESTARIA</div>', unsafe_allow_html=True)
    st.page_link("pages/5_Gestion_Presupuesto.py", label="💰  Dashboard & Ejecución")
    st.markdown("---")
    st.markdown('<div style="font-size:.58rem;color:#2a4560;letter-spacing:2px;font-weight:700;'
                'text-transform:uppercase;padding:.2rem .4rem .5rem;font-family:monospace;">'
                '👥 GESTIÓN RECURSO HUMANO</div>', unsafe_allow_html=True)
    st.page_link("pages/0_Repositorio_RRHH.py", label="🗄️  Repositorio RR.HH.")
    st.markdown("---")
    st.page_link("Inicio.py", label="🏠  Inicio")
    st.markdown('<div style="font-size:.55rem;color:#1e3550;text-align:center;'
                'padding:1.2rem 0 .4rem;font-family:monospace;">Subtítulo 21 · SSMC · 2025</div>',
                unsafe_allow_html=True)


# ── TOPBAR visual ─────────────────────────────────────────────────────────────
st.markdown(
    '<div style="display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;'
    'background:rgba(4,10,22,.96);border-bottom:1px solid rgba(255,255,255,.05);'
    'padding:.55rem 1.8rem;position:sticky;top:0;z-index:999;'
    'backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);">'
    # Logo
    '<div style="display:flex;flex-direction:column;padding-right:1.1rem;'
    'border-right:1px solid rgba(255,255,255,.05);margin-right:.7rem;flex-shrink:0;">'
    '<span style="font-family:Syne,sans-serif;font-size:1.1rem;font-weight:800;'
    'background:linear-gradient(135deg,#2aaeff,#00ccff);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.1;">evidant</span>'
    '<span style="font-size:.44rem;letter-spacing:2.5px;color:#334455;text-transform:uppercase;'
    'font-family:monospace;margin-top:.1rem;">Suite · DAP SSMC</span></div>'
    # G1
    '<div style="display:flex;flex-direction:column;gap:.16rem;padding:.18rem .55rem;border-radius:7px;">'
    '<span style="font-size:.47rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#253545;font-family:monospace;">⚙ Procesamiento Financiero</span>'
    '<div style="display:flex;gap:.12rem;flex-wrap:nowrap;">'
    '<span style="display:inline-flex;align-items:center;gap:.28rem;padding:.2rem .48rem;border-radius:5px;font-size:.68rem;color:#6a8aaa;background:rgba(0,100,200,.07);border:1px solid rgba(0,100,200,.12);">'
    '<span style="font-family:monospace;font-size:.48rem;background:rgba(0,100,200,.28);color:#5cc8ff;padding:.02rem .23rem;border-radius:3px;">P1</span>Consolidación</span>'
    '<span style="display:inline-flex;align-items:center;gap:.28rem;padding:.2rem .48rem;border-radius:5px;font-size:.68rem;color:#6a8aaa;background:rgba(0,100,200,.07);border:1px solid rgba(0,100,200,.12);">'
    '<span style="font-family:monospace;font-size:.48rem;background:rgba(0,100,200,.28);color:#5cc8ff;padding:.02rem .23rem;border-radius:3px;">P2</span>Redistribución</span>'
    '<span style="display:inline-flex;align-items:center;gap:.28rem;padding:.2rem .48rem;border-radius:5px;font-size:.68rem;color:#6a8aaa;background:rgba(0,100,200,.07);border:1px solid rgba(0,100,200,.12);">'
    '<span style="font-family:monospace;font-size:.48rem;background:rgba(0,100,200,.28);color:#5cc8ff;padding:.02rem .23rem;border-radius:3px;">P3</span>Prog. Financiero</span>'
    '<span style="display:inline-flex;align-items:center;gap:.28rem;padding:.2rem .48rem;border-radius:5px;font-size:.68rem;color:#6a8aaa;background:rgba(0,100,200,.07);border:1px solid rgba(0,100,200,.12);">'
    '<span style="font-family:monospace;font-size:.48rem;background:rgba(0,100,200,.28);color:#5cc8ff;padding:.02rem .23rem;border-radius:3px;">P4</span>Rendiciones</span>'
    '</div></div>'
    # Sep
    '<div style="width:1px;height:2rem;background:rgba(255,255,255,.05);margin:0 .3rem;flex-shrink:0;"></div>'
    # G2
    '<div style="display:flex;flex-direction:column;gap:.16rem;padding:.18rem .55rem;border-radius:7px;">'
    '<span style="font-size:.47rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#253545;font-family:monospace;">💰 Gestión Presupuestaria</span>'
    '<span style="display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .48rem;border-radius:5px;font-size:.68rem;color:#6a8aaa;background:rgba(0,160,120,.06);border:1px solid rgba(0,160,120,.12);">'
    '<span style="color:#3dffbd;font-size:.5rem;">●</span>Dashboard & Estado</span>'
    '</div>'
    # Sep
    '<div style="width:1px;height:2rem;background:rgba(255,255,255,.05);margin:0 .3rem;flex-shrink:0;"></div>'
    # G3
    '<div style="display:flex;flex-direction:column;gap:.16rem;padding:.18rem .55rem;border-radius:7px;">'
    '<span style="font-size:.47rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#253545;font-family:monospace;">👥 Recurso Humano</span>'
    '<span style="display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .48rem;border-radius:5px;font-size:.68rem;color:#6a8aaa;background:rgba(200,140,0,.06);border:1px solid rgba(200,140,0,.12);">'
    '<span style="color:#ffc955;font-size:.5rem;">●</span>Repositorio RR.HH.</span>'
    '</div>'
    '</div>',
    unsafe_allow_html=True)


# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="text-align:center;padding:5rem 2rem 4rem;'
    'background:radial-gradient(ellipse 80% 60% at 50% 0%,rgba(0,100,255,.07) 0%,transparent 65%);">'
    '<div style="font-family:monospace;font-size:.56rem;letter-spacing:3.5px;text-transform:uppercase;'
    'color:#253545;margin-bottom:1.6rem;display:inline-flex;align-items:center;gap:.8rem;">'
    '<span style="display:block;width:2.5rem;height:1px;background:rgba(0,150,255,.3);"></span>'
    'Plataforma de Gestión &nbsp;·&nbsp; Subtítulo 21 &nbsp;·&nbsp; DAP SSMC'
    '<span style="display:block;width:2.5rem;height:1px;background:rgba(0,150,255,.3);"></span></div>'
    '<div style="font-family:Syne,sans-serif;font-size:clamp(3rem,8vw,5.5rem);font-weight:800;'
    'line-height:.9;letter-spacing:-3px;margin-bottom:1.5rem;">'
    '<span style="background:linear-gradient(135deg,#fff 0%,#80d4ff 35%,#00ccff 65%,#00e09a 100%);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">evidant</span><br>'
    '<span style="color:rgba(255,255,255,.08);">Suite</span></div>'
    '<div style="font-size:1.05rem;color:#8daac8;max-width:550px;margin:0 auto 2.8rem;line-height:1.78;">'
    'Control integral del gasto en remuneraciones y gestión presupuestaria de la '
    '<strong style="color:#cce0f8;">Dirección de Atención Primaria</strong> '
    'del Servicio de Salud Metropolitano Central.</div>'
    '<div style="display:inline-flex;align-items:center;gap:2.5rem;'
    'background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.06);'
    'border-radius:14px;padding:.9rem 2.5rem;">'
    '<div style="display:flex;flex-direction:column;align-items:center;gap:.2rem;">'
    '<span style="font-family:Syne,sans-serif;font-size:1.7rem;font-weight:800;'
    'background:linear-gradient(135deg,#00ccff,#00e09a);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">3</span>'
    '<span style="font-size:.5rem;color:#253545;letter-spacing:1.5px;text-transform:uppercase;font-family:monospace;">Módulos</span></div>'
    '<div style="width:1px;height:2.5rem;background:rgba(255,255,255,.06);"></div>'
    '<div style="display:flex;flex-direction:column;align-items:center;gap:.2rem;">'
    '<span style="font-family:Syne,sans-serif;font-size:1.7rem;font-weight:800;'
    'background:linear-gradient(135deg,#00ccff,#00e09a);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">4</span>'
    '<span style="font-size:.5rem;color:#253545;letter-spacing:1.5px;text-transform:uppercase;font-family:monospace;">Pasos</span></div>'
    '<div style="width:1px;height:2.5rem;background:rgba(255,255,255,.06);"></div>'
    '<div style="display:flex;flex-direction:column;align-items:center;gap:.2rem;">'
    '<span style="font-family:Syne,sans-serif;font-size:1.7rem;font-weight:800;'
    'background:linear-gradient(135deg,#00ccff,#00e09a);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">21</span>'
    '<span style="font-size:.5rem;color:#253545;letter-spacing:1.5px;text-transform:uppercase;font-family:monospace;">Subtítulo</span></div>'
    '<div style="width:1px;height:2.5rem;background:rgba(255,255,255,.06);"></div>'
    '<div style="display:flex;flex-direction:column;align-items:center;gap:.2rem;">'
    '<span style="font-family:Syne,sans-serif;font-size:1.7rem;font-weight:800;'
    'background:linear-gradient(135deg,#00ccff,#00e09a);'
    '-webkit-background-clip:text;-webkit-text-fill-color:transparent;">DAP</span>'
    '<span style="font-size:.5rem;color:#253545;letter-spacing:1.5px;text-transform:uppercase;font-family:monospace;">SSMC</span></div>'
    '</div></div>',
    unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


def sh(num, title, sub, color):
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:1.2rem;margin-bottom:2rem;">'
        f'<div style="font-family:Syne,sans-serif;font-size:4rem;font-weight:800;'
        f'color:rgba(255,255,255,.03);line-height:1;letter-spacing:-3px;flex-shrink:0;">{num}</div>'
        f'<div style="width:3px;height:2.8rem;border-radius:2px;'
        f'background:linear-gradient(180deg,{color},transparent);flex-shrink:0;"></div>'
        f'<div><div style="font-family:Syne,sans-serif;font-size:1.25rem;font-weight:700;color:#eef4ff;">{title}</div>'
        f'<div style="font-size:.64rem;color:#253545;letter-spacing:1.2px;text-transform:uppercase;'
        f'margin-top:.16rem;font-family:monospace;">{sub}</div></div></div>',
        unsafe_allow_html=True)


# ═══════ SEC 1: PROCESAMIENTO ═══════
sh("01","Procesamiento Financiero","flujo secuencial de 4 pasos · ejecución mensual","#0066ff")

PASOS = [
    ("📂","PASO 1","Consolidación de Reportes",
     ["Consolidado","Multi-hoja","Triple encabezado"],
     "Une múltiples hojas del Excel preservando el encabezado triple (3 filas). Actualiza automáticamente el Repositorio RR.HH.",
     "pages/4_Consolidacion_Remu.py","#0066ff"),
    ("🔄","PASO 2","Redistribución PRAPS vs DAP",
     ["Redistribución","Reintegros","Auditoría"],
     "Elimina pares de reintegros y redistribuye montos entre centros PRAPS y D.A.P. Genera resumen, resultados y auditoría Excel.",
     "pages/1_Redistribucion.py","#0094ff"),
    ("📊","PASO 3","Programa Financiero CASA",
     ["PF Anual","Multi-ley","Filtros CC"],
     "Genera la planilla de Programa Financiero desde la base redistribuida. Produce hojas PF_MES y PF_ANUAL.",
     "pages/2_Programa_Financiero.py","#00bbff"),
    ("📋","PASO 4","Generador de Rendiciones",
     ["Rendiciones","Honorarios","Homologación"],
     "Consolida remuneraciones y honorarios. Produce el archivo de rendiciones con homologación de programas y trazabilidad.",
     "pages/3_Rendiciones.py","#00ccff"),
]

cols = st.columns(4, gap="small")
for i,(icon,step,title,tags,desc,page,color) in enumerate(PASOS):
    with cols[i]:
        tag_spans = "".join(
            f'<span style="font-size:.53rem;text-transform:uppercase;font-family:monospace;'
            f'padding:.09rem .38rem;border-radius:20px;background:rgba(255,255,255,.04);'
            f'color:#445a72;border:1px solid rgba(255,255,255,.05);">{t}</span>' for t in tags)
        st.markdown(
            f'<div style="background:#0d1b2e;border:1px solid rgba(255,255,255,.06);'
            f'border-radius:14px;padding:1.5rem;min-height:300px;display:flex;flex-direction:column;'
            f'gap:.85rem;border-top:2px solid {color};">'
            f'<div style="display:flex;align-items:center;gap:.6rem;">'
            f'<span style="font-family:monospace;font-size:.52rem;padding:.18rem .48rem;border-radius:4px;'
            f'background:rgba(0,100,200,.25);color:#5cc8ff;border:1px solid rgba(0,148,255,.2);">{step}</span>'
            f'<span style="font-size:1.3rem;">{icon}</span></div>'
            f'<div style="font-family:Syne,sans-serif;font-size:.95rem;font-weight:700;color:#eef4ff;line-height:1.25;">{title}</div>'
            f'<div style="display:flex;gap:.22rem;flex-wrap:wrap;">{tag_spans}</div>'
            f'<div style="font-size:.8rem;color:#8daac8;line-height:1.65;flex:1;">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True)
        if st.button(f"Abrir Paso {i+1} →", key=f"p{i}", use_container_width=True):
            st.switch_page(page)

st.markdown("<hr>", unsafe_allow_html=True)


# ═══════ SEC 2: PRESUPUESTO ═══════
sh("02","Gestión Presupuestaria","ejecución mensual · marcos CC · dotación y costo","#00e09a")

cp1, cp2, cp3 = st.columns([1.5, 1, 1], gap="medium")
with cp1:
    st.markdown(
        '<div style="background:#0d1b2e;border:1px solid rgba(255,255,255,.06);border-radius:16px;'
        'padding:1.8rem;display:flex;flex-direction:column;gap:1rem;border-top:2px solid #00e09a;min-height:360px;">'
        '<div style="font-size:1.9rem;">💰</div>'
        '<div style="font-family:Syne,sans-serif;font-size:1.15rem;font-weight:700;color:#eef4ff;">Gestión de Presupuesto</div>'
        '<div style="display:flex;gap:.25rem;flex-wrap:wrap;">'
        '<span style="font-size:.56rem;text-transform:uppercase;font-family:monospace;padding:.09rem .42rem;'
        'border-radius:20px;background:rgba(0,200,150,.05);color:#005533;border:1px solid rgba(0,200,150,.1);">Marcos Anuales</span>'
        '<span style="font-size:.56rem;text-transform:uppercase;font-family:monospace;padding:.09rem .42rem;'
        'border-radius:20px;background:rgba(0,200,150,.05);color:#005533;border:1px solid rgba(0,200,150,.1);">Imputación Mensual</span>'
        '<span style="font-size:.56rem;text-transform:uppercase;font-family:monospace;padding:.09rem .42rem;'
        'border-radius:20px;background:rgba(0,200,150,.05);color:#005533;border:1px solid rgba(0,200,150,.1);">Dashboard KPI</span>'
        '<span style="font-size:.56rem;text-transform:uppercase;font-family:monospace;padding:.09rem .42rem;'
        'border-radius:20px;background:rgba(0,200,150,.05);color:#005533;border:1px solid rgba(0,200,150,.1);">Pivot Mensual</span>'
        '</div>'
        '<div style="font-size:.85rem;color:#8daac8;line-height:1.72;flex:1;">'
        'Configura centros de costo con marcos anuales. Imputa rendiciones mes a mes con detección de duplicados. '
        'Dashboard con semáforo presupuestario y tablas pivot tipo Excel. '
        'Análisis de dotación con homologación semántica de calidad jurídica.</div>'
        '</div>',
        unsafe_allow_html=True)
    if st.button("Abrir Gestión Presupuestaria →", key="btn_pres", use_container_width=True):
        st.switch_page("pages/5_Gestion_Presupuesto.py")

def feat(title, items, dot):
    rows = "".join(
        f'<div style="display:flex;align-items:flex-start;gap:.6rem;font-size:.82rem;color:#8daac8;line-height:1.5;">'
        f'<div style="width:5px;height:5px;border-radius:50%;background:{dot};flex-shrink:0;margin-top:.42rem;"></div>'
        f'<span>{x}</span></div>' for x in items)
    return (
        f'<div style="background:#0a1522;border:1px solid rgba(255,255,255,.06);'
        f'border-radius:16px;padding:1.6rem;height:100%;">'
        f'<div style="font-size:.55rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;'
        f'color:#253545;font-family:monospace;margin-bottom:1.1rem;">{title}</div>'
        f'<div style="display:flex;flex-direction:column;gap:.58rem;">{rows}</div></div>')

with cp2:
    st.markdown(feat("Dashboard & KPIs",[
        "KPIs: Haber Neto, Total Haberes, Descuentos, Marco",
        "Semáforo presupuestario por CC (Normal/Alerta/Crítico)",
        "Evolución mensual del gasto",
        "Distribución por programa Top 10",
    ],"#00e09a"), unsafe_allow_html=True)

with cp3:
    st.markdown(feat("Estado Mensual & Análisis",[
        "Pivot Resolución × Mes × 3 métricas",
        "Imputación con anti-duplicado automático",
        "Análisis Honorarios vs Remuneraciones",
        "Homologación semántica calidad jurídica",
        "Exportación Excel multihoja",
    ],"#00e09a"), unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ═══════ SEC 3: RRHH ═══════
sh("03","Gestión del Recurso Humano","repositorio persistente · historial de cambios · fichas contractuales","#f0b340")

st.markdown(
    '<div style="display:flex;align-items:center;gap:.9rem;'
    'background:rgba(240,180,60,.05);border:1px solid rgba(240,180,60,.15);'
    'border-radius:10px;padding:.85rem 1.4rem;margin-bottom:1.4rem;'
    'font-size:.85rem;color:#c8a060;">'
    '<span style="font-size:1.1rem;flex-shrink:0;">🔒</span>'
    '<span><strong style="color:#f0b340;">Datos permanentes:</strong> '
    'El repositorio usa SQLite local — los contratos e historial '
    '<strong style="color:#f0b340;">no se borran al reiniciar la aplicación</strong>. '
    'Se actualiza automáticamente al procesar el Paso 1.</span></div>',
    unsafe_allow_html=True)

rh1, rh2 = st.columns([1, 1], gap="medium")
with rh1:
    st.markdown(
        '<div style="background:#0d1b2e;border:1px solid rgba(255,255,255,.06);border-radius:16px;'
        'padding:1.8rem;display:flex;flex-direction:column;gap:1rem;border-top:2px solid #f0b340;min-height:340px;">'
        '<div style="font-size:1.9rem;">🗄️</div>'
        '<div style="font-family:Syne,sans-serif;font-size:1.15rem;font-weight:700;color:#eef4ff;">Repositorio RR.HH.</div>'
        '<div style="display:flex;gap:.25rem;flex-wrap:wrap;">'
        '<span style="font-size:.56rem;text-transform:uppercase;font-family:monospace;padding:.09rem .42rem;'
        'border-radius:20px;background:rgba(200,140,0,.05);color:#664400;border:1px solid rgba(200,140,0,.12);">Contratos</span>'
        '<span style="font-size:.56rem;text-transform:uppercase;font-family:monospace;padding:.09rem .42rem;'
        'border-radius:20px;background:rgba(200,140,0,.05);color:#664400;border:1px solid rgba(200,140,0,.12);">Historial Cambios</span>'
        '<span style="font-size:.56rem;text-transform:uppercase;font-family:monospace;padding:.09rem .42rem;'
        'border-radius:20px;background:rgba(200,140,0,.05);color:#664400;border:1px solid rgba(200,140,0,.12);">SQLite Persistente</span>'
        '<span style="font-size:.56rem;text-transform:uppercase;font-family:monospace;padding:.09rem .42rem;'
        'border-radius:20px;background:rgba(200,140,0,.05);color:#664400;border:1px solid rgba(200,140,0,.12);">No se borra</span>'
        '</div>'
        '<div style="font-size:.85rem;color:#8daac8;line-height:1.72;flex:1;">'
        'Base de datos persistente de contratos del personal. Se actualiza desde el Paso 1 conservando historial '
        'completo de cambios. Fichas editables con 15 campos contractuales. '
        'Búsqueda por RUT, nombre o contrato. Dashboard por CC y Planta.</div>'
        '</div>',
        unsafe_allow_html=True)
    if st.button("Abrir Repositorio RR.HH. →", key="btn_rrhh", use_container_width=True):
        st.switch_page("pages/0_Repositorio_RRHH.py")

with rh2:
    st.markdown(feat("Funcionalidades incluidas",[
        "Auto-carga desde Paso 1 (Consolidación)",
        "Historial completo de modificaciones por contrato",
        "Ficha editable por contrato — 15 campos",
        "Búsqueda por RUT, nombre o N° contrato",
        "Dashboard con gráficos por CC y Planta",
        "SQLite persistente — no se borra al reiniciar",
        "ID_CONTRATO determinístico por RUT + CC",
        "Exportación Excel del repositorio completo",
    ],"#f0b340"), unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;font-family:monospace;font-size:.55rem;'
    'color:#1e3550;padding:1.5rem 0;">'
    'evidant Suite &nbsp;·&nbsp; Control Subtítulo 21 &nbsp;·&nbsp; '
    'Dirección de Atención Primaria &nbsp;·&nbsp; SSMC &nbsp;·&nbsp; 2025</div>',
    unsafe_allow_html=True)

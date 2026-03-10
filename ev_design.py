# -*- coding: utf-8 -*-
"""
evidant Design System — ev_design.py  v9
Navbar FUNCIONAL: usa st.columns() para layout horizontal real.
Los st.page_link() van DENTRO de columnas, no dentro de divs HTML (no funciona en Streamlit).
"""
import streamlit as st
import plotly.graph_objects as go

# ══════════════════════════════════════════════════════════════════════════════
# ANTI-FLASH JS: fondo oscuro antes del primer render
# ══════════════════════════════════════════════════════════════════════════════
_ANTI_FLASH_JS = """
<script>
(function(){
  var s = document.createElement('style');
  s.textContent =
    'html,body{background:#121212!important;color:#fff!important;}' +
    '[data-testid="stMain"]{overflow-y:auto!important;}' +
    '.stApp,.stAppViewContainer,[data-testid="stAppViewContainer"],' +
    '[data-testid="stMain"],.main,.block-container{background:#121212!important;}';
  document.head.appendChild(s);
})();
</script>
"""

# ══════════════════════════════════════════════════════════════════════════════
# JS: marca el primer stHorizontalBlock como navbar (agrega data-ev-navbar="true")
# Se re-aplica en cada re-render de Streamlit via MutationObserver
# ══════════════════════════════════════════════════════════════════════════════
_NAVBAR_TAG_JS = """
<script>
(function(){
  function tagNav(){
    var nb = document.querySelector('[data-testid="stHorizontalBlock"]');
    if(nb){ nb.setAttribute('data-ev-navbar','true'); }
    else  { setTimeout(tagNav, 60); }
  }
  tagNav();
  new MutationObserver(function(){
    var nb = document.querySelector('[data-testid="stHorizontalBlock"]');
    if(nb) nb.setAttribute('data-ev-navbar','true');
  }).observe(document.documentElement,{subtree:true,childList:true});
})();
</script>
"""

# ══════════════════════════════════════════════════════════════════════════════
# MASTER CSS — Paleta Spotify + Navbar + Page Links
# ══════════════════════════════════════════════════════════════════════════════
MASTER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cabinet+Grotesk:wght@400;700;800;900&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600&display=swap');

/* ── VARIABLES SPOTIFY ── */
:root {
  --bg:       #121212;
  --bg2:      #191414;
  --surface:  #1a1a1a;
  --surface2: #242424;
  --card:     #181818;
  --card-h:   #282828;

  --border:   rgba(255,255,255,.07);
  --border2:  rgba(255,255,255,.13);

  --green:    #1db954;
  --green2:   #1ed760;
  --blue:     #4a9eff;
  --gold:     #f59e0b;

  --text:  #ffffff;
  --text2: #b3b3b3;
  --text3: #535353;
  --text4: #282828;

  --ff: 'Outfit', sans-serif;
  --fd: 'Cabinet Grotesk', sans-serif;
  --fm: 'JetBrains Mono', monospace;

  --radius:    10px;
  --radius-lg: 16px;
  --shadow:    0 4px 32px rgba(0,0,0,.6);
  --glow-g:    0 0 40px rgba(29,185,84,.18);
}

/* ── RESET TOTAL ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[class*="css"],
.stApp,
.stAppViewContainer,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main,
.block-container,
[data-testid="block-container"] {
  background-color: var(--bg) !important;
  background:       var(--bg) !important;
  color:            var(--text) !important;
  font-family:      var(--ff) !important;
}

/* ── OCULTAR CHROME DE STREAMLIT ── */
#MainMenu, footer, header,
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebar"] {
  display: none !important;
  visibility: hidden !important;
}

/* ── LAYOUT ── */
.block-container       { padding: 0 !important; max-width: 100% !important; overflow: visible !important; }
[data-testid="stMain"] > div { padding: 0 !important; overflow: visible !important; }
section[data-testid="stMain"] { padding: 0 !important; }

/* ── SCROLLBAR SPOTIFY ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,.2); }

/* ══════════════════════════════════════════════════════
   NAVBAR — bloque horizontal identificado por JS
   El primer stHorizontalBlock recibe data-ev-navbar="true"
══════════════════════════════════════════════════════ */

/* Bloque sticky del navbar */
[data-ev-navbar="true"] {
  position: sticky !important;
  top: 0 !important;
  z-index: 9999 !important;
  background: rgba(18,18,18,.96) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border-bottom: 1px solid rgba(255,255,255,.07) !important;
  min-height: 58px !important;
  align-items: center !important;
  padding: 0 8px !important;
  flex-wrap: nowrap !important;
  gap: 2px !important;
}

/* Columnas dentro del navbar */
[data-ev-navbar="true"] [data-testid="column"] {
  padding: 0 2px !important;
  align-self: center !important;
  min-width: 0 !important;
  flex: 0 0 auto !important;
}
[data-ev-navbar="true"] [data-testid="stVerticalBlock"] {
  padding: 0 !important;
  gap: 0 !important;
}
[data-ev-navbar="true"] [data-testid="stMarkdownContainer"] {
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
}

/* Logo en el navbar */
.ev-logo-block {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-right: 14px;
  border-right: 1px solid rgba(255,255,255,.07);
  flex-shrink: 0;
  white-space: nowrap;
  user-select: none;
}
.ev-logo-name {
  font-family: 'Cabinet Grotesk', sans-serif;
  font-size: .95rem;
  font-weight: 900;
  background: linear-gradient(135deg, #1db954, #1ed760);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
  letter-spacing: .5px;
}
.ev-logo-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 7px;
  letter-spacing: 2.5px;
  color: #3a3a3a;
  text-transform: uppercase;
  margin-top: 3px;
}

/* Separador vertical */
.ev-vsep {
  width: 1px;
  height: 22px;
  background: rgba(255,255,255,.07);
  display: block;
  margin: 0 auto;
  align-self: center;
}

/* Label de grupo */
.ev-nav-grp-lbl {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #606060;
  white-space: nowrap;
  display: block;
  line-height: 1;
  margin-bottom: 2px;
}

/* ── PAGE_LINK dentro del navbar: pill pequeño gris ── */
[data-ev-navbar="true"] [data-testid="stPageLink"] {
  display: inline-block !important;
  width: auto !important;
  min-width: 0 !important;
  padding: 0 !important;
}
[data-ev-navbar="true"] [data-testid="stPageLink"] p,
[data-ev-navbar="true"] [data-testid="stPageLink"] div {
  display: contents !important;
}
[data-ev-navbar="true"] [data-testid="stPageLink"] a {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: auto !important;
  background: transparent !important;
  color: #e0e0e0 !important;
  border: 1px solid transparent !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  font-family: 'Outfit', sans-serif !important;
  padding: 6px 11px !important;
  letter-spacing: 0 !important;
  transform: none !important;
  box-shadow: none !important;
  text-decoration: none !important;
  white-space: nowrap !important;
  line-height: 1.2 !important;
  transition: all .15s ease !important;
}
[data-ev-navbar="true"] [data-testid="stPageLink"] a:hover {
  background: rgba(255,255,255,.08) !important;
  color: #ffffff !important;
  border-color: rgba(255,255,255,.1) !important;
  transform: none !important;
  box-shadow: none !important;
}
/* Página activa: Streamlit agrega aria-current="page" al link activo */
[data-ev-navbar="true"] [data-testid="stPageLink"] a[aria-current="page"] {
  background: rgba(29,185,84,.12) !important;
  color: #1ed760 !important;
  border-color: rgba(29,185,84,.28) !important;
  font-weight: 700 !important;
}

/* ══════════════════════════════════════════════════════
   PAGE_LINK fuera del navbar = botón Spotify verde
══════════════════════════════════════════════════════ */
[data-testid="stPageLink"] {
  display: block !important;
  width: 100% !important;
}
[data-testid="stPageLink"] a {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  background: var(--green) !important;
  color: #000 !important;
  border: none !important;
  border-radius: 500px !important;
  font-weight: 700 !important;
  font-size: .875rem !important;
  font-family: var(--ff) !important;
  padding: .65rem 1.8rem !important;
  letter-spacing: .5px !important;
  transition: all .18s cubic-bezier(.4,0,.2,1) !important;
  text-decoration: none !important;
  cursor: pointer !important;
  white-space: nowrap !important;
}
[data-testid="stPageLink"] a:hover {
  background: var(--green2) !important;
  transform: scale(1.02) !important;
  box-shadow: 0 4px 24px rgba(29,185,84,.4) !important;
  color: #000 !important;
}

/* ══════════════════════════════════════════════════════
   PAGE HEADER
══════════════════════════════════════════════════════ */
.ev-page-header {
  padding: 2.5rem 2rem 2rem;
  border-bottom: 1px solid var(--border);
  position: relative;
  overflow: hidden;
}
.ev-page-header::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60% 100% at 0% 50%, rgba(29,185,84,.06) 0%, transparent 65%),
    radial-gradient(ellipse 40% 80% at 100% 20%, rgba(74,158,255,.04) 0%, transparent 60%);
  pointer-events: none;
}
.ev-breadcrumb {
  font-family: var(--fm);
  font-size: .62rem;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--text3);
  margin-bottom: .8rem;
}
.ev-page-title {
  font-family: var(--fd);
  font-size: 2rem;
  font-weight: 900;
  color: var(--text);
  letter-spacing: -.5px;
  line-height: 1.15;
  margin-bottom: .4rem;
}
.ev-page-subtitle {
  font-size: .88rem;
  color: var(--text2);
  line-height: 1.6;
}

/* ══════════════════════════════════════════════════════
   CONTENT AREA
══════════════════════════════════════════════════════ */
.ev-content { padding: 1.8rem 2rem; max-width: 1400px; margin: 0 auto; }

/* ══════════════════════════════════════════════════════
   CARDS
══════════════════════════════════════════════════════ */
.ev-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.6rem;
  transition: border-color .2s, box-shadow .2s, transform .2s, background .2s;
  position: relative;
  overflow: hidden;
}
.ev-card:hover {
  background: var(--card-h);
  border-color: var(--border2);
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}
.ev-card-green { border-top: 2px solid var(--green); }
.ev-card-blue  { border-top: 2px solid var(--blue); }
.ev-card-gold  { border-top: 2px solid var(--gold); }

/* ══════════════════════════════════════════════════════
   BUTTONS (Spotify pill)
══════════════════════════════════════════════════════ */
.stButton > button {
  background: var(--green) !important;
  color: #000 !important;
  border: none !important;
  border-radius: 500px !important;
  font-weight: 700 !important;
  font-size: .875rem !important;
  font-family: var(--ff) !important;
  padding: .65rem 1.8rem !important;
  letter-spacing: .5px !important;
  transition: all .18s cubic-bezier(.4,0,.2,1) !important;
  width: 100% !important;
}
.stButton > button:hover {
  background: var(--green2) !important;
  transform: scale(1.02) !important;
  box-shadow: 0 4px 24px rgba(29,185,84,.4) !important;
}
.stButton > button:active { transform: scale(.98) !important; }

/* ══════════════════════════════════════════════════════
   INPUTS / SELECT
══════════════════════════════════════════════════════ */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
}
[data-testid="stSelectbox"] > div > div:hover { border-color: rgba(29,185,84,.4) !important; }
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  font-family: var(--ff) !important;
  caret-color: var(--green) !important;
}
[data-testid="stTextArea"] textarea {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  caret-color: var(--green) !important;
}
input::placeholder, textarea::placeholder { color: var(--text3) !important; }
label, [data-testid="stWidgetLabel"] {
  color: var(--text2) !important;
  font-family: var(--ff) !important;
  font-size: .85rem !important;
  font-weight: 500 !important;
}

/* ══════════════════════════════════════════════════════
   METRICS
══════════════════════════════════════════════════════ */
[data-testid="stMetric"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  padding: 1.3rem 1.5rem !important;
  transition: box-shadow .2s, border-color .2s !important;
}
[data-testid="stMetric"]:hover {
  border-color: rgba(29,185,84,.2) !important;
  box-shadow: var(--glow-g) !important;
}
[data-testid="stMetric"] label {
  color: var(--text3) !important;
  font-family: var(--fm) !important;
  font-size: .62rem !important;
  font-weight: 500 !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
  color: var(--text) !important;
  font-family: var(--fm) !important;
  font-size: 1.7rem !important;
  font-weight: 600 !important;
}

/* ══════════════════════════════════════════════════════
   TABS — underline Spotify
══════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important;
  padding: 0 !important;
  border-radius: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text2) !important;
  font-family: var(--ff) !important;
  font-size: .875rem !important;
  font-weight: 600 !important;
  padding: .85rem 1.5rem !important;
  border-bottom: 2px solid transparent !important;
  border-radius: 0 !important;
  transition: all .18s !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text) !important; background: rgba(255,255,255,.03) !important; }
.stTabs [aria-selected="true"] {
  color: var(--text) !important;
  border-bottom-color: var(--green) !important;
  font-weight: 700 !important;
}

/* ══════════════════════════════════════════════════════
   DATAFRAMES
══════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  overflow: hidden !important;
}

/* ══════════════════════════════════════════════════════
   FILE UPLOADER
══════════════════════════════════════════════════════ */
[data-testid="stFileUploader"] {
  background: var(--surface) !important;
  border: 1.5px dashed rgba(29,185,84,.3) !important;
  border-radius: var(--radius-lg) !important;
  padding: 1.2rem !important;
  transition: border-color .2s, background .2s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: rgba(29,185,84,.6) !important;
  background: rgba(29,185,84,.04) !important;
}

/* ══════════════════════════════════════════════════════
   ALERTS
══════════════════════════════════════════════════════ */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border: 1px solid !important;
  font-family: var(--ff) !important;
  font-size: .875rem !important;
}

/* ══════════════════════════════════════════════════════
   HR
══════════════════════════════════════════════════════ */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 2rem 0 !important;
}

/* ══════════════════════════════════════════════════════
   DOWNLOAD BUTTON
══════════════════════════════════════════════════════ */
[data-testid="stDownloadButton"] > button {
  background: var(--surface) !important;
  color: var(--text) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 500px !important;
  font-weight: 600 !important;
}
[data-testid="stDownloadButton"] > button:hover {
  border-color: var(--green) !important;
  color: var(--green2) !important;
  background: rgba(29,185,84,.06) !important;
}

/* ══════════════════════════════════════════════════════
   PROGRESS BAR
══════════════════════════════════════════════════════ */
[data-testid="stProgressBar"] > div > div { background: var(--green) !important; border-radius: 4px !important; }
[data-testid="stProgressBar"] > div       { background: var(--surface) !important; border-radius: 4px !important; }

/* ══════════════════════════════════════════════════════
   EXPANDER
══════════════════════════════════════════════════════ */
[data-testid="stExpander"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary { font-family: var(--ff) !important; font-weight: 600 !important; color: var(--text) !important; }

/* ══════════════════════════════════════════════════════
   CHIPS
══════════════════════════════════════════════════════ */
.ev-chip {
  display: inline-flex; align-items: center; gap: .3rem;
  padding: .2rem .65rem; border-radius: 500px;
  font-size: .68rem; font-weight: 600;
  font-family: var(--fm); letter-spacing: .5px;
}
.ev-chip-green { background: rgba(29,185,84,.12); color: #1ed760; border: 1px solid rgba(29,185,84,.22); }
.ev-chip-blue  { background: rgba(74,158,255,.12); color: var(--blue); border: 1px solid rgba(74,158,255,.22); }
.ev-chip-gold  { background: rgba(245,158,11,.12); color: var(--gold); border: 1px solid rgba(245,158,11,.22); }
.ev-chip-gray  { background: rgba(255,255,255,.06); color: var(--text2); border: 1px solid var(--border); }

/* KPI card */
.kpi-card {
  background: var(--card); border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 1.4rem 1.5rem;
  position: relative; overflow: hidden; transition: all .2s;
}
.kpi-card:hover { border-color: rgba(29,185,84,.2); box-shadow: var(--glow-g); }
.kpi-card::after { content:''; position:absolute; top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,var(--green),transparent); }
.kpi-label { font-family:var(--fm);font-size:.6rem;letter-spacing:2px;text-transform:uppercase;color:var(--text3);margin-bottom:.6rem; }
.kpi-value { font-family:var(--fm);font-size:1.65rem;font-weight:600;color:var(--text);line-height:1;margin-bottom:.3rem; }
.kpi-value.green { color:var(--green); } .kpi-value.blue { color:var(--blue); } .kpi-value.gold { color:var(--gold); }

/* Section header */
.ev-section { display:flex;align-items:center;gap:1rem;margin:2rem 0 1.4rem;padding-bottom:.9rem;border-bottom:1px solid var(--border); }
.ev-section-num { font-family:var(--fm);font-size:.6rem;letter-spacing:2px;color:var(--green);font-weight:600; }
.ev-section-title { font-family:var(--fd);font-size:1.1rem;font-weight:800;color:var(--text); }
.ev-section-sub { font-size:.72rem;color:var(--text3);margin-left:auto;font-family:var(--fm); }

/* Pulse dot */
.ev-dot { display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);animation:pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1);}50%{opacity:.5;transform:scale(.8);} }

/* Animaciones */
@keyframes fadeUp { from{opacity:0;transform:translateY(16px);}to{opacity:1;transform:translateY(0);} }
.ev-anim  { animation:fadeUp .45s ease both; }
.ev-anim2 { animation:fadeUp .45s ease .1s both; }
.ev-anim3 { animation:fadeUp .45s ease .2s both; }
.ev-anim4 { animation:fadeUp .45s ease .3s both; }

/* ══════════════════════════════════════════════════════
   RESPONSIVE — Mobile & Tablet
══════════════════════════════════════════════════════ */

/* ── Tablet (≤ 1024px) ── */
@media (max-width:1024px){
  .ev-page-title  { font-size:1.6rem; }
  .ev-kpi-grid    { grid-template-columns:repeat(2,1fr) !important; }
  .ev-kpi-value   { font-size:1.2rem !important; }
}

/* ── Mobile (≤ 768px) ── */
@media (max-width:768px){

  /* Layout base */
  .ev-page-header { padding:1rem .8rem !important; }
  .ev-page-title  { font-size:1.25rem !important; line-height:1.3 !important; }
  .ev-page-sub    { font-size:.75rem !important; }
  .ev-content     { padding:.8rem .6rem !important; }
  .section-hdr    { padding:1rem .8rem !important; font-size:1rem !important; }

  /* ── Navbar: scroll horizontal, no overflow ── */
  [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) {
    overflow-x: auto !important;
    overflow-y: hidden !important;
    -webkit-overflow-scrolling: touch !important;
    scrollbar-width: none !important;
    flex-wrap: nowrap !important;
    gap: 2px !important;
    min-height: 50px !important;
    padding: 0 4px !important;
  }
  [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"])::-webkit-scrollbar {
    display: none !important;
  }
  [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) [data-testid="stPageLink"] a {
    font-size: 11px !important;
    padding: 5px 9px !important;
    white-space: nowrap !important;
  }

  /* ── Columnas: stack vertical (excepto navbar) ── */
  [data-testid="stHorizontalBlock"]:not(:has([data-testid="stPageLink"])) {
    flex-direction: column !important;
    flex-wrap: wrap !important;
    gap: 0 !important;
  }
  [data-testid="stHorizontalBlock"]:not(:has([data-testid="stPageLink"])) > [data-testid="column"] {
    width: 100% !important;
    min-width: 100% !important;
    flex: 0 0 100% !important;
  }

  /* ── Métricas ── */
  [data-testid="metric-container"]  { min-width:0 !important; }
  [data-testid="stMetricValue"]     { font-size:1.1rem !important; }
  [data-testid="stMetricLabel"]     { font-size:.7rem !important; }

  /* ── KPI grid ── */
  .ev-kpi-grid  { grid-template-columns:repeat(2,1fr) !important; gap:.5rem !important; }
  .ev-kpi-value { font-size:1rem !important; }
  .ev-kpi-lbl   { font-size:.68rem !important; }

  /* ── Tabs: scroll horizontal ── */
  [data-testid="stTabs"] > div:first-child {
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
    scrollbar-width: none !important;
    flex-wrap: nowrap !important;
  }
  [data-testid="stTabs"] > div:first-child::-webkit-scrollbar { display:none !important; }
  [data-testid="stTabs"] button {
    white-space: nowrap !important;
    font-size: 12px !important;
    padding: 6px 10px !important;
    flex-shrink: 0 !important;
  }

  /* ── Tablas HTML: scroll horizontal ── */
  [data-testid="stMarkdownContainer"] > div[style*="border-radius:12px"],
  [data-testid="stMarkdownContainer"] > div[style*="border-radius: 12px"] {
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
    max-width: 100vw !important;
  }
  [data-testid="stMarkdownContainer"] table { min-width: 480px; }

  /* ── DataFrames ── */
  [data-testid="stDataFrame"] > div { overflow-x:auto !important; -webkit-overflow-scrolling:touch !important; }

  /* ── Plotly: no desborde ── */
  [data-testid="stPlotlyChart"] { overflow-x:auto !important; max-width:100vw !important; }
  [data-testid="stPlotlyChart"] > div { min-width:0 !important; }

  /* ── Botones full-width ── */
  [data-testid="stDownloadButton"] button { width:100% !important; font-size:13px !important; }
  [data-testid="stButton"] > button       { font-size:13px !important; }

  /* ── Inputs — evitar zoom iOS (min 16px) ── */
  [data-testid="stTextInput"]  input  { font-size:16px !important; }
  [data-testid="stSelectbox"]  select { font-size:16px !important; }
  [data-testid="stNumberInput"] input { font-size:16px !important; }

  /* ── Texto general más legible ── */
  [data-testid="stMarkdownContainer"] p  { font-size:.9rem !important; line-height:1.6 !important; }
  [data-testid="stMarkdownContainer"] h3 { font-size:1.1rem !important; }
  [data-testid="stMarkdownContainer"] h4 { font-size:1rem !important; }

  /* ── Status y progress ── */
  [data-testid="stStatus"]       { font-size:13px !important; }
  [data-testid="stProgress"] > div { height:6px !important; }

  /* ── Expander ── */
  [data-testid="stExpander"] summary { font-size:13px !important; }

  /* ── File uploader ── */
  [data-testid="stFileUploader"] { font-size:13px !important; }
  [data-testid="stFileUploader"] section { padding:.6rem !important; }
}

/* ── Small mobile (≤ 480px) ── */
@media (max-width:480px){
  .ev-page-title { font-size:1rem !important; }
  .ev-kpi-grid   { grid-template-columns:1fr !important; }
  [data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) [data-testid="stPageLink"] a {
    font-size: 10px !important;
    padding: 4px 7px !important;
  }
  [data-testid="stTabs"] button { font-size:11px !important; padding:5px 8px !important; }
  [data-testid="stMetricValue"] { font-size:.95rem !important; }
}

/* ══════════════════════════════════════════════════════
   NAVBAR :has() — fallback CSS4 (funciona aunque JS falle)
   Identifica el bloque horizontal que contiene page_links
   Especificidad 0-3-1 > regla global 0-1-1, sin JS
══════════════════════════════════════════════════════ */
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) {
  position: sticky !important;
  top: 0 !important;
  z-index: 9999 !important;
  background: rgba(18,18,18,.97) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border-bottom: 1px solid rgba(255,255,255,.07) !important;
  min-height: 58px !important;
  align-items: center !important;
  padding: 0 8px !important;
  flex-wrap: nowrap !important;
  gap: 2px !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) [data-testid="stPageLink"] a {
  background: var(--green) !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 500px !important;
  font-weight: 700 !important;
  font-size: 14px !important;
  font-family: 'Outfit', sans-serif !important;
  padding: 6px 14px !important;
  white-space: nowrap !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-decoration: none !important;
  transition: all .15s ease !important;
  width: auto !important;
  min-width: 0 !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) [data-testid="stPageLink"] a:hover {
  background: var(--green2) !important;
  color: #ffffff !important;
  transform: scale(1.03) !important;
  box-shadow: 0 4px 20px rgba(29,185,84,.35) !important;
}
[data-testid="stHorizontalBlock"]:has([data-testid="stPageLink"]) [data-testid="stPageLink"] a[aria-current="page"] {
  background: #155d27 !important;
  color: #1ed760 !important;
  box-shadow: none !important;
  transform: none !important;
}
</style>
"""


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS COMPARTIDOS — usables desde cualquier página
# ══════════════════════════════════════════════════════════════════════════════

def ev_bar(x_vals, y_vals, fmt_clp=False, height=340):
    """Bar chart oscuro con gradiente azul→rojo, etiquetas con miles y escala
    logarítmica automática cuando hay outliers (ratio max/min > 20).
    Uso: st.plotly_chart(ev_design.ev_bar(x, y), use_container_width=True)
    """
    n      = len(x_vals)
    y_list = list(y_vals)
    x_list = list(x_vals)

    # Detectar outliers: activar log si max/min > 20
    y_pos   = [v for v in y_list if v > 0]
    use_log = (len(y_pos) >= 2 and max(y_pos) / max(min(y_pos), 1) > 20)

    # Gradiente posicional: azul #4a9eff → rojo #e63946
    colors = [
        f"rgb({int(74  + 156 * i / max(n - 1, 1))},"
        f"{int(158 - 101 * i / max(n - 1, 1))},"
        f"{int(255 - 185 * i / max(n - 1, 1))})"
        for i in range(n)
    ]

    # Etiquetas de valor con separador de miles (formato chileno)
    if fmt_clp:
        text_vals = [f"${v:,.0f}".replace(",", ".") for v in y_list]
    else:
        text_vals = [f"{int(v):,}".replace(",", ".") for v in y_list]

    fig = go.Figure(go.Bar(
        x=x_list, y=y_list,
        marker=dict(color=colors, line=dict(width=0)),
        text=text_vals,
        textposition="outside",
        textfont=dict(size=10, color="#b3b3b3", family="JetBrains Mono"),
        cliponaxis=False,
    ))

    yaxis_cfg = dict(
        tickfont=dict(color="#6b6b6b", size=10),
        gridcolor="rgba(255,255,255,0.05)",
        linecolor="rgba(255,255,255,0.07)",
        showgrid=True,
    )
    if use_log:
        yaxis_cfg["type"] = "log"
        if fmt_clp:
            yaxis_cfg["tickvals"] = [1e4, 1e5, 1e6, 1e7, 1e8, 1e9]
            yaxis_cfg["ticktext"] = ["$10K", "$100K", "$1M", "$10M", "$100M", "$1B"]
        else:
            yaxis_cfg["tickvals"] = [1, 10, 100, 1_000, 10_000]
            yaxis_cfg["ticktext"] = ["1", "10", "100", "1.000", "10.000"]

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#b3b3b3", family="Outfit"),
        margin=dict(t=35, b=90, l=10, r=10),
        height=height,
        xaxis=dict(
            type="category",
            tickfont=dict(color="#6b6b6b", size=10),
            tickangle=-35,
            showgrid=False,
            linecolor="rgba(255,255,255,0.07)",
        ),
        yaxis=yaxis_cfg,
        bargap=0.28,
        showlegend=False,
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )
    if use_log:
        fig.add_annotation(
            text="escala logarítmica",
            xref="paper", yref="paper",
            x=1, y=1.04, xanchor="right", yanchor="bottom",
            font=dict(size=9, color="#333", family="JetBrains Mono"),
            showarrow=False,
        )
    return fig


def ev_table_html(df, fmt_clp_cols=None, highlight_cols=None):
    """Renderiza un DataFrame como tabla HTML con tema oscuro Spotify.
    Uso: st.markdown(ev_design.ev_table_html(df), unsafe_allow_html=True)
    fmt_clp_cols: lista de columnas numéricas a formatear como $ 1.234.567
    highlight_cols: lista de columnas a destacar con fondo amarillo
    """
    fmt_clp_cols  = fmt_clp_cols  or []
    highlight_cols = highlight_cols or []

    def _th_style(col):
        if col in highlight_cols:
            return (
                f'<th style="padding:8px 14px;text-align:left;'
                f'font-family:JetBrains Mono,monospace;font-size:10px;font-weight:700;'
                f'letter-spacing:1.5px;text-transform:uppercase;color:#1a1a1a;'
                f'background:#f5c518;border-bottom:1px solid rgba(255,255,255,.07);'
                f'white-space:nowrap;">{col}</th>'
            )
        return (
            f'<th style="padding:8px 14px;text-align:left;'
            f'font-family:JetBrains Mono,monospace;font-size:10px;font-weight:600;'
            f'letter-spacing:1.5px;text-transform:uppercase;color:#535353;'
            f'border-bottom:1px solid rgba(255,255,255,.07);white-space:nowrap;">'
            f'{col}</th>'
        )

    th = "".join(_th_style(col) for col in df.columns)
    rows = ""
    for i, (_, row) in enumerate(df.iterrows()):
        bg = "rgba(255,255,255,.025)" if i % 2 == 0 else "transparent"
        cells = ""
        for col in df.columns:
            val = row[col]
            if col in fmt_clp_cols and isinstance(val, (int, float)):
                val_str = f"$ {val:,.0f}".replace(",", ".")
            else:
                val_str = str(val) if val is not None else "—"
            if col in highlight_cols:
                cells += (
                    f'<td style="padding:7px 14px;font-size:12px;'
                    f'font-family:Outfit,sans-serif;color:#1a1a1a;font-weight:600;'
                    f'background:rgba(245,197,24,0.15);'
                    f'border-bottom:1px solid rgba(255,255,255,.04);">'
                    f'{val_str}</td>'
                )
            else:
                cells += (
                    f'<td style="padding:7px 14px;font-size:12px;'
                    f'font-family:Outfit,sans-serif;color:#b3b3b3;'
                    f'border-bottom:1px solid rgba(255,255,255,.04);">'
                    f'{val_str}</td>'
                )
        rows += f'<tr style="background:{bg};">{cells}</tr>'

    return (
        f'<div style="background:#181818;border:1px solid rgba(255,255,255,.07);'
        f'border-radius:12px;overflow:auto;margin-top:4px;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr>{th}</tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table></div>'
    )


# ══════════════════════════════════════════════════════════════════════════════
# RENDER — Navbar con st.columns() real + CSS maestro
# ══════════════════════════════════════════════════════════════════════════════
def render(current: str = "", page_title: str = "", page_sub: str = "",
           breadcrumb: str = "", icon: str = ""):
    """
    Inyecta CSS Spotify + navbar FUNCIONAL con st.columns() y st.page_link().
    El primer stHorizontalBlock es marcado por JS y recibe estilos de navbar.

    current: ya no se usa para resaltar (Streamlit lo hace vía aria-current="page"),
             se mantiene por compatibilidad con las páginas existentes.
    """
    _ = current  # reservado para compatibilidad

    # ── 1. Anti-flash + CSS maestro + JS navbar tagger ─────────────────────
    st.markdown(_ANTI_FLASH_JS,    unsafe_allow_html=True)
    st.markdown(MASTER_CSS,        unsafe_allow_html=True)
    st.markdown(_NAVBAR_TAG_JS,    unsafe_allow_html=True)

    # ── 2. Navbar como columnas (renderiza HORIZONTAL de verdad) ────────────
    # Cols: logo | P1 | P2 | P3 | P4 | sep | Presupuesto | sep | RRHH | Inicio | sep | OCR/PDF | Liq. | sep | relleno
    c = st.columns(
        [2.3, 1.4, 1.5, 1.9, 1.3, 0.3, 1.6, 0.3, 1.4, 1.1, 0.2, 1.2, 1.6, 0.2, 0.3],
        gap="small"
    )

    with c[0]:   # Logo
        st.markdown(
            '<div class="ev-logo-block">'
            '<span class="ev-logo-name">EVIDANT S.A.</span>'
            '<span class="ev-logo-tag">Suite · DAP SSMC</span>'
            '</div>',
            unsafe_allow_html=True,
        )

    with c[1]:   # Paso 1
        st.markdown('<span class="ev-nav-grp-lbl">⚙ Proc. Financiero</span>', unsafe_allow_html=True)
        st.page_link("pages/4_Consolidacion_Remu.py", label="P1 · Consolidación")

    with c[2]:   # Paso 2
        st.markdown('<span class="ev-nav-grp-lbl">&nbsp;</span>', unsafe_allow_html=True)
        st.page_link("pages/1_Redistribucion.py", label="P2 · Redistribución")

    with c[3]:   # Paso 3
        st.markdown('<span class="ev-nav-grp-lbl">&nbsp;</span>', unsafe_allow_html=True)
        st.page_link("pages/2_Programa_Financiero.py", label="P3 · Prog. Financiero")

    with c[4]:   # Paso 4
        st.markdown('<span class="ev-nav-grp-lbl">&nbsp;</span>', unsafe_allow_html=True)
        st.page_link("pages/3_Rendiciones.py", label="P4 · Rendiciones")

    with c[5]:   # Separador visual
        st.markdown('<div class="ev-vsep"></div>', unsafe_allow_html=True)

    with c[6]:   # Presupuesto
        st.markdown('<span class="ev-nav-grp-lbl">💰 Presupuesto</span>', unsafe_allow_html=True)
        st.page_link("pages/5_Gestion_Presupuesto.py", label="Dashboard & KPIs")

    with c[7]:   # Separador visual
        st.markdown('<div class="ev-vsep"></div>', unsafe_allow_html=True)

    with c[8]:   # RRHH
        st.markdown('<span class="ev-nav-grp-lbl">👥 RR.HH.</span>', unsafe_allow_html=True)
        st.page_link("pages/0_Repositorio_RRHH.py", label="Repositorio")

    with c[9]:   # Inicio
        st.markdown('<span class="ev-nav-grp-lbl">&nbsp;</span>', unsafe_allow_html=True)
        st.page_link("Inicio.py", label="⌂ Inicio")

    with c[10]:  # Separador visual
        st.markdown('<div class="ev-vsep"></div>', unsafe_allow_html=True)

    with c[11]:  # Imágenes — OCR / PDF
        st.markdown('<span class="ev-nav-grp-lbl">🖼 Imágenes</span>', unsafe_allow_html=True)
        st.page_link("pages/6_Procesamiento_Imagenes.py", label="OCR / PDF")

    with c[12]:  # Imágenes — Liquidaciones Accesorias
        st.markdown('<span class="ev-nav-grp-lbl">&nbsp;</span>', unsafe_allow_html=True)
        st.page_link("pages/7_Dotacion.py", label="Dotación")

    with c[13]:  # Separador final
        st.markdown('<div class="ev-vsep"></div>', unsafe_allow_html=True)

    # c[14] = relleno (vacío)

    # ── 3. Page header (solo si se proporciona título) ───────────────────────
    if page_title:
        bc = (f'<div class="ev-breadcrumb">evidant Suite › {breadcrumb}</div>'
              if breadcrumb else "")
        icon_html = f'<span style="margin-right:.5rem">{icon}</span>' if icon else ""
        st.markdown(
            f'<div class="ev-page-header ev-anim">'
            f'{bc}'
            f'<div class="ev-page-title">{icon_html}{page_title}</div>'
            f'<div class="ev-page-subtitle">{page_sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

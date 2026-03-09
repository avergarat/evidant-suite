# -*- coding: utf-8 -*-
"""
evidant Design System — ev_design.py
CSS maestro + navbar para todas las páginas de evidant Suite
Estética: Spotify/Linear — dark mode, tipografía premium, micro-animaciones, glassmorphism
"""
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# SISTEMA DE DISEÑO MAESTRO
# ══════════════════════════════════════════════════════════════════════════════
MASTER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cabinet+Grotesk:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600&family=Outfit:wght@300;400;500;600;700&display=swap');

/* ── VARIABLES GLOBALES ── */
:root {
  --bg:          #080b12;
  --bg2:         #0c1018;
  --surface:     #111520;
  --surface2:    #161b28;
  --card:        #141926;
  --card-hover:  #1a2035;
  --border:      rgba(255,255,255,.07);
  --border2:     rgba(255,255,255,.12);
  --border-blue: rgba(29,185,84,.2);

  --blue:        #1a73e8;
  --blue2:       #4a9eff;
  --cyan:        #00d4ff;
  --green:       #1db954;
  --green2:      #1ed760;
  --gold:        #f59e0b;
  --red:         #ef4444;
  --purple:      #a855f7;

  --text:        #f1f5f9;
  --text2:       #94a3b8;
  --text3:       #475569;
  --text4:       #1e293b;

  --ff: 'Outfit', sans-serif;
  --fd: 'Cabinet Grotesk', sans-serif;
  --fm: 'JetBrains Mono', monospace;

  --radius:   12px;
  --radius-lg: 18px;
  --shadow:   0 4px 24px rgba(0,0,0,.4);
  --shadow-lg: 0 8px 48px rgba(0,0,0,.6);
  --glow-green: 0 0 40px rgba(29,185,84,.15);
  --glow-blue:  0 0 40px rgba(74,158,255,.15);
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
.block-container {
  padding: 0 !important;
  max-width: 100% !important;
}
[data-testid="stMain"] > div {
  padding: 0 !important;
}
section[data-testid="stMain"] {
  padding: 0 !important;
}

/* ── SCROLLBAR SPOTIFY-STYLE ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,.1);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,.2); }

/* ══════════════════════════════════════════════════════════════════
   NAVBAR
══════════════════════════════════════════════════════════════════ */
.ev-nav {
  position: sticky;
  top: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 0;
  background: rgba(8,11,18,.92);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border-bottom: 1px solid var(--border);
  padding: 0 1.5rem;
  height: 58px;
  width: 100%;
}

.ev-logo {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-right: 1.2rem;
  border-right: 1px solid var(--border);
  margin-right: 1rem;
  flex-shrink: 0;
  text-decoration: none;
  cursor: pointer;
}
.ev-logo-name {
  font-family: var(--fd);
  font-size: 1.15rem;
  font-weight: 900;
  background: linear-gradient(135deg, #1db954, #1ed760);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1;
  letter-spacing: -.3px;
}
.ev-logo-tag {
  font-family: var(--fm);
  font-size: .45rem;
  letter-spacing: 2.5px;
  color: var(--text3);
  text-transform: uppercase;
  margin-top: .12rem;
}

.ev-nav-sep {
  width: 1px;
  height: 2rem;
  background: linear-gradient(180deg, transparent, var(--border), transparent);
  margin: 0 .8rem;
  flex-shrink: 0;
}

.ev-grp {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: .18rem;
  padding: .3rem .55rem;
  border-radius: 10px;
  transition: background .2s;
  cursor: default;
}
.ev-grp:hover { background: rgba(255,255,255,.03); }

.ev-grp-lbl {
  font-family: var(--fm);
  font-size: .48rem;
  font-weight: 600;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--text3);
  white-space: nowrap;
}

.ev-links {
  display: flex;
  align-items: center;
  gap: .1rem;
  flex-wrap: nowrap;
}

.ev-link {
  display: inline-flex;
  align-items: center;
  gap: .28rem;
  padding: .24rem .55rem;
  border-radius: 7px;
  font-size: .75rem;
  font-weight: 500;
  color: var(--text2);
  text-decoration: none;
  border: 1px solid transparent;
  transition: all .18s ease;
  white-space: nowrap;
  font-family: var(--ff);
}
.ev-link:hover {
  background: rgba(255,255,255,.07);
  color: var(--text);
  border-color: var(--border);
}
.ev-link.active {
  background: rgba(29,185,84,.12);
  color: var(--green2);
  border-color: rgba(29,185,84,.25);
  font-weight: 600;
}

.ev-badge {
  font-family: var(--fm);
  font-size: .5rem;
  font-weight: 600;
  padding: .05rem .28rem;
  border-radius: 4px;
  background: rgba(255,255,255,.08);
  color: var(--text3);
  border: 1px solid var(--border);
  letter-spacing: .3px;
}
.ev-link.active .ev-badge {
  background: rgba(29,185,84,.2);
  color: var(--green);
  border-color: rgba(29,185,84,.3);
}

/* ══════════════════════════════════════════════════════════════════
   PAGE HEADER
══════════════════════════════════════════════════════════════════ */
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
  font-size: .65rem;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--text3);
  margin-bottom: .8rem;
  display: flex;
  align-items: center;
  gap: .5rem;
}
.ev-breadcrumb-sep { color: var(--text4); }
.ev-page-title {
  font-family: var(--fd);
  font-size: 2rem;
  font-weight: 900;
  color: var(--text);
  letter-spacing: -.5px;
  line-height: 1.15;
  margin-bottom: .4rem;
}
.ev-page-title span {
  background: linear-gradient(135deg, var(--green), var(--cyan));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.ev-page-subtitle {
  font-size: .88rem;
  color: var(--text2);
  line-height: 1.6;
}

/* ══════════════════════════════════════════════════════════════════
   CONTENT AREA
══════════════════════════════════════════════════════════════════ */
.ev-content {
  padding: 1.8rem 2rem;
  max-width: 1380px;
  margin: 0 auto;
}

/* ══════════════════════════════════════════════════════════════════
   CARDS
══════════════════════════════════════════════════════════════════ */
.ev-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.6rem;
  transition: border-color .2s, box-shadow .2s, transform .2s;
  position: relative;
  overflow: hidden;
}
.ev-card:hover {
  border-color: var(--border2);
  box-shadow: 0 8px 32px rgba(0,0,0,.4);
  transform: translateY(-1px);
}
.ev-card-glass {
  background: rgba(20, 25, 38, .6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: var(--radius-lg);
  padding: 1.6rem;
}
.ev-card-green {
  border-top: 2px solid var(--green);
}
.ev-card-blue {
  border-top: 2px solid var(--blue2);
}
.ev-card-gold {
  border-top: 2px solid var(--gold);
}

/* ══════════════════════════════════════════════════════════════════
   UPLOAD ZONE
══════════════════════════════════════════════════════════════════ */
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
[data-testid="stFileUploaderDropzone"] {
  background: transparent !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
  color: var(--text2) !important;
  font-family: var(--ff) !important;
}

/* ══════════════════════════════════════════════════════════════════
   BUTTONS
══════════════════════════════════════════════════════════════════ */
.stButton > button {
  background: var(--green) !important;
  color: #000 !important;
  border: none !important;
  border-radius: 500px !important;
  font-weight: 700 !important;
  font-size: .9rem !important;
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
.stButton > button:active {
  transform: scale(.98) !important;
}

/* CTA primario grande */
.ev-cta > .stButton > button {
  background: linear-gradient(135deg, var(--green), #17a84a) !important;
  font-size: 1rem !important;
  padding: .8rem 2rem !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  box-shadow: 0 4px 24px rgba(29,185,84,.3) !important;
}

/* ══════════════════════════════════════════════════════════════════
   INPUTS & SELECTS
══════════════════════════════════════════════════════════════════ */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  font-family: var(--ff) !important;
}
[data-testid="stSelectbox"] > div > div:hover,
[data-testid="stMultiSelect"] > div > div:hover {
  border-color: rgba(29,185,84,.4) !important;
}
[data-testid="stNumberInput"] input {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  font-family: var(--fm) !important;
}
[data-testid="stTextInput"] input {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: var(--radius) !important;
  color: var(--text) !important;
  font-family: var(--ff) !important;
}
input::placeholder, textarea::placeholder {
  color: var(--text3) !important;
}
label, [data-testid="stWidgetLabel"] {
  color: var(--text2) !important;
  font-family: var(--ff) !important;
  font-size: .85rem !important;
  font-weight: 500 !important;
}

/* ══════════════════════════════════════════════════════════════════
   METRICS
══════════════════════════════════════════════════════════════════ */
[data-testid="stMetric"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  padding: 1.3rem 1.5rem !important;
  transition: box-shadow .2s, border-color .2s !important;
}
[data-testid="stMetric"]:hover {
  border-color: rgba(29,185,84,.2) !important;
  box-shadow: var(--glow-green) !important;
}
[data-testid="stMetric"] label {
  color: var(--text3) !important;
  font-family: var(--fm) !important;
  font-size: .65rem !important;
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
[data-testid="stMetricDelta"] { font-family: var(--ff) !important; }

/* ══════════════════════════════════════════════════════════════════
   TABS — Spotify style
══════════════════════════════════════════════════════════════════ */
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
  font-size: .88rem !important;
  font-weight: 600 !important;
  padding: .85rem 1.5rem !important;
  border-bottom: 2px solid transparent !important;
  border-radius: 0 !important;
  transition: all .18s !important;
  letter-spacing: .3px !important;
}
.stTabs [data-baseweb="tab"]:hover {
  color: var(--text) !important;
  background: rgba(255,255,255,.03) !important;
}
.stTabs [aria-selected="true"] {
  color: var(--text) !important;
  border-bottom-color: var(--green) !important;
  font-weight: 700 !important;
}

/* ══════════════════════════════════════════════════════════════════
   DATAFRAMES
══════════════════════════════════════════════════════════════════ */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  overflow: hidden !important;
}
.dvn-scroller { background: var(--card) !important; }
.cell-wrap-text { color: var(--text) !important; font-family: var(--fm) !important; }
[data-testid="column-header--name"] {
  background: var(--surface) !important;
  color: var(--text3) !important;
  font-family: var(--fm) !important;
  font-size: .7rem !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  font-weight: 600 !important;
}

/* ══════════════════════════════════════════════════════════════════
   ALERTS / INFO
══════════════════════════════════════════════════════════════════ */
[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border: 1px solid !important;
  font-family: var(--ff) !important;
  font-size: .88rem !important;
}
.st-ae { /* success */
  background: rgba(29,185,84,.08) !important;
  border-color: rgba(29,185,84,.25) !important;
  color: #86efac !important;
}
.st-af { /* info */
  background: rgba(74,158,255,.08) !important;
  border-color: rgba(74,158,255,.25) !important;
  color: #93c5fd !important;
}
.st-ag { /* warning */
  background: rgba(245,158,11,.08) !important;
  border-color: rgba(245,158,11,.25) !important;
  color: #fcd34d !important;
}
.st-ah { /* error */
  background: rgba(239,68,68,.08) !important;
  border-color: rgba(239,68,68,.25) !important;
  color: #fca5a5 !important;
}

/* ══════════════════════════════════════════════════════════════════
   DIVIDER
══════════════════════════════════════════════════════════════════ */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 2rem 0 !important;
}

/* ══════════════════════════════════════════════════════════════════
   SPINNER
══════════════════════════════════════════════════════════════════ */
[data-testid="stSpinner"] > div {
  border-top-color: var(--green) !important;
}

/* ══════════════════════════════════════════════════════════════════
   DOWNLOAD BUTTON
══════════════════════════════════════════════════════════════════ */
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

/* ══════════════════════════════════════════════════════════════════
   FORM
══════════════════════════════════════════════════════════════════ */
[data-testid="stForm"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  padding: 1.5rem !important;
}

/* ══════════════════════════════════════════════════════════════════
   PROGRESS BAR
══════════════════════════════════════════════════════════════════ */
[data-testid="stProgressBar"] > div > div {
  background: var(--green) !important;
  border-radius: 4px !important;
}
[data-testid="stProgressBar"] > div {
  background: var(--surface) !important;
  border-radius: 4px !important;
}

/* ══════════════════════════════════════════════════════════════════
   CUSTOM COMPONENTS
══════════════════════════════════════════════════════════════════ */

/* KPI card */
.kpi-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.4rem 1.5rem;
  position: relative;
  overflow: hidden;
  transition: all .2s;
}
.kpi-card:hover {
  border-color: rgba(29,185,84,.2);
  box-shadow: var(--glow-green);
}
.kpi-card::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, var(--green), transparent);
}
.kpi-label {
  font-family: var(--fm);
  font-size: .6rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--text3);
  margin-bottom: .6rem;
}
.kpi-value {
  font-family: var(--fm);
  font-size: 1.65rem;
  font-weight: 600;
  color: var(--text);
  line-height: 1;
  margin-bottom: .3rem;
}
.kpi-value.green { color: var(--green); }
.kpi-value.blue  { color: var(--blue2); }
.kpi-value.gold  { color: var(--gold); }

/* Section header */
.ev-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 2rem 0 1.4rem;
  padding-bottom: .9rem;
  border-bottom: 1px solid var(--border);
}
.ev-section-num {
  font-family: var(--fm);
  font-size: .62rem;
  letter-spacing: 2px;
  color: var(--green);
  font-weight: 600;
}
.ev-section-title {
  font-family: var(--fd);
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text);
}
.ev-section-sub {
  font-size: .75rem;
  color: var(--text3);
  margin-left: auto;
  font-family: var(--fm);
  letter-spacing: .5px;
}

/* Tag/badge chips */
.ev-chip {
  display: inline-flex;
  align-items: center;
  gap: .3rem;
  padding: .2rem .65rem;
  border-radius: 500px;
  font-size: .68rem;
  font-weight: 600;
  font-family: var(--fm);
  letter-spacing: .5px;
}
.ev-chip-green {
  background: rgba(29,185,84,.12);
  color: var(--green2);
  border: 1px solid rgba(29,185,84,.2);
}
.ev-chip-blue {
  background: rgba(74,158,255,.12);
  color: var(--blue2);
  border: 1px solid rgba(74,158,255,.2);
}
.ev-chip-gold {
  background: rgba(245,158,11,.12);
  color: var(--gold);
  border: 1px solid rgba(245,158,11,.2);
}
.ev-chip-gray {
  background: rgba(255,255,255,.06);
  color: var(--text2);
  border: 1px solid var(--border);
}

/* Pulse dot */
.ev-dot {
  display: inline-block;
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--green);
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: .5; transform: scale(.8); }
}

/* Animaciones de entrada */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.ev-anim  { animation: fadeUp .45s ease both; }
.ev-anim2 { animation: fadeUp .45s ease .1s both; }
.ev-anim3 { animation: fadeUp .45s ease .2s both; }
.ev-anim4 { animation: fadeUp .45s ease .3s both; }

/* ══════════════════════════════════════════════════════════════════
   RADIO / CHECKBOX
══════════════════════════════════════════════════════════════════ */
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label {
  color: var(--text2) !important;
  font-family: var(--ff) !important;
}

/* ══════════════════════════════════════════════════════════════════
   EXPANDER
══════════════════════════════════════════════════════════════════ */
[data-testid="stExpander"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary {
  font-family: var(--ff) !important;
  font-weight: 600 !important;
  color: var(--text) !important;
}

/* ══════════════════════════════════════════════════════════════════
   PLOTLY CHARTS — transparencia para integrar con el fondo
══════════════════════════════════════════════════════════════════ */
.js-plotly-plot .plotly .main-svg {
  border-radius: var(--radius-lg);
}

/* ══════════════════════════════════════════════════════════════════
   RESPONSIVE
══════════════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
  .ev-nav { flex-wrap: wrap; height: auto; padding: .6rem 1rem; }
  .ev-nav-sep { display: none; }
  .ev-page-header { padding: 1.5rem 1rem; }
  .ev-page-title { font-size: 1.5rem; }
  .ev-content { padding: 1.2rem 1rem; }
}
</style>
"""

# ── Función nav link ──────────────────────────────────────────────────────────
def _nl(url: str, label: str, badge: str = "", active: bool = False) -> str:
    cls = "ev-link active" if active else "ev-link"
    b = f'<span class="ev-badge">{badge}</span> ' if badge else ""
    return f'<a class="{cls}" href="/{url}" target="_self">{b}{label}</a>'

# ── Render navbar + CSS maestro ────────────────────────────────────────────────
def render(current: str = "", page_title: str = "", page_sub: str = "",
           breadcrumb: str = "", icon: str = ""):
    """
    Inyecta el CSS maestro + navbar + page header.
    current: 'consolidacion' | 'redistribucion' | 'financiero' |
             'rendiciones' | 'presupuesto' | 'rrhh'
    """
    # CSS maestro
    st.markdown(MASTER_CSS, unsafe_allow_html=True)

    # Navbar HTML
    nav = (
        '<nav class="ev-nav">'
        '<a class="ev-logo" href="/" target="_self">'
        '<span class="ev-logo-name">evidant</span>'
        '<span class="ev-logo-tag">Suite · DAP SSMC</span>'
        '</a>'
        '<div class="ev-nav-sep"></div>'
        '<div class="ev-grp">'
        '<div class="ev-grp-lbl">⚙ Procesamiento Financiero</div>'
        '<div class="ev-links">'
        + _nl("4_Consolidacion_Remu", "Consolidación",  "P1", current=="consolidacion")
        + _nl("1_Redistribucion",     "Redistribución", "P2", current=="redistribucion")
        + _nl("2_Programa_Financiero","Prog. Financiero","P3", current=="financiero")
        + _nl("3_Rendiciones",        "Rendiciones",    "P4", current=="rendiciones")
        + '</div></div>'
        '<div class="ev-nav-sep"></div>'
        '<div class="ev-grp">'
        '<div class="ev-grp-lbl">💰 Gestión Presupuestaria</div>'
        '<div class="ev-links">'
        + _nl("5_Gestion_Presupuesto", "Dashboard & KPIs", "", current=="presupuesto")
        + '</div></div>'
        '<div class="ev-nav-sep"></div>'
        '<div class="ev-grp">'
        '<div class="ev-grp-lbl">👥 Recurso Humano</div>'
        '<div class="ev-links">'
        + _nl("0_Repositorio_RRHH", "Repositorio RR.HH.", "", current=="rrhh")
        + '</div></div>'
        '</nav>'
    )
    st.markdown(nav, unsafe_allow_html=True)

    # Page header
    if page_title:
        bc = f'<div class="ev-breadcrumb">evidant Suite <span class="ev-breadcrumb-sep">›</span> {breadcrumb}</div>' if breadcrumb else ""
        icon_html = f'<span style="margin-right:.5rem">{icon}</span>' if icon else ""
        st.markdown(
            f'<div class="ev-page-header ev-anim">'
            f'{bc}'
            f'<div class="ev-page-title">{icon_html}{page_title}</div>'
            f'<div class="ev-page-subtitle">{page_sub}</div>'
            f'</div>',
            unsafe_allow_html=True)

# evidant Suite · Control Subtítulo 21 · DAP SSMC

Plataforma SaaS para el control del subtítulo 21 de la Dirección de Atención Primaria SSMC.

---

## Estructura del proyecto

```
evidant_suite/
│
├── Inicio.py                                          ← Página principal (landing)
├── requirements.txt                                   ← Dependencias
│
├── pages/
│   ├── 1_Redistribucion.py                            ← Módulo 1: Redistribución PRAPS vs DAP
│   ├── 2_Programa_Financiero.py                       ← Módulo 2: Programa Financiero CASA
│   ├── 3_Rendiciones.py                               ← Módulo 3: Generador de Rendiciones
│   └── 4_Consolidacion_Remu.py                        ← Módulo 4: Consolidación Reportes Remu
│
│  (Motores originales — NO modificar)
├── app_redistribucion_mod2.py
├── PF_CASA_V1_mejorado_v18_6_PF_MES_fix_CC_v20patch.py
├── app_rendiciones.py
└── CONSOLIDACIO_N_REPORTE_REMU.py
```

---

## Instalación y ejecución en VS Code

### 1. Pre-requisitos
- Python 3.10 o superior
- pip actualizado

### 2. Crear entorno virtual (recomendado)

```bash
# En la carpeta del proyecto:
python -m venv .venv

# Activar en Windows:
.venv\Scripts\activate

# Activar en macOS/Linux:
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar la suite

```bash
streamlit run Inicio.py
```

La aplicación se abrirá automáticamente en `http://localhost:8501`

---

## Módulos disponibles

| Módulo | Descripción | Entrada | Salida |
|--------|-------------|---------|--------|
| **Redistribución PRAPS vs DAP** | Redistribuye montos entre CC PRAPS y DAP, elimina reintegros, genera auditoría | Excel con CONSOLIDADO + BLOQUE DESCUENTO | SALIDA_REDISTRIBUCION.xlsx |
| **Programa Financiero CASA** | Genera PF por CC/ley/mes con filtros avanzados | Excel BASE + CONSOLIDACIÓN + PF modelo | _SALIDA.xlsx con PF_MES y PF_ANUAL |
| **Generador de Rendiciones** | Consolida remuneraciones + honorarios para rendición | SALIDA_REDISTRIBUCION.xlsx | Rendiciones.xlsx |
| **Consolidación Reportes Remu** | Une hojas por triplete de encabezados (3 filas) | Cualquier Excel multi-hoja | _CONSOLIDADO_UNION.xlsx |

---

## Notas importantes

- Los **motores originales** (`.py` en la raíz) **no han sido modificados**. Las páginas de Streamlit los importan directamente.
- El módulo **PF_CASA** fue desarrollado originalmente con Tkinter; la página 2 importa solo las funciones de procesamiento, sin levantar la ventana de escritorio.
- El módulo **Consolidación Reportes Remu** también fue desarrollado con Tkinter; la página 4 importa únicamente `consolidate_by_header_triplet`.
- El ícono `.ico` de Evidant está incluido en el directorio para uso en futuras configuraciones de escritorio.

---

*evidant · Plataforma de Control Subtítulo 21 · 2025*

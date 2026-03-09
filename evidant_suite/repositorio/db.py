# -*- coding: utf-8 -*-
"""
repositorio/db.py
Motor SQLite para el Repositorio de Funcionarios DAP SSMC.

Cada registro = un contrato (una fila del consolidado).
Un funcionario puede tener N contratos → N registros con el mismo RUT pero distinto ID_CONTRATO.

ID_CONTRATO: hash SHA256 determinista de (RUT_DV + CORR + LEY_AFECTO + HORAS_GRADOS + CENTRO_DE_COSTO)
             → estable entre consolidados, permite detectar cambios.
"""

import sqlite3
import hashlib
import os
import json
from datetime import datetime
from typing import Optional

# Ruta del archivo SQLite — vive junto a este módulo
_DB_DIR  = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(_DB_DIR, "funcionarios.db")

# Campos del consolidado que se almacenan
CAMPOS_CONTRATO = [
    "ID_CONTRATO",        # PK — hash determinista
    "RUT_DV",
    "CENTRO_DE_COSTO",
    "PROGRAMA",
    "CORR",
    "CORR_PAGO",
    "NOMBRE",
    "ESTAB",
    "CALIDAD_JURIDICA",
    "HORAS_GRADOS",
    "BIENIO_TRIENIO",
    "PLANTA",
    "UNIDAD",
    "CARGO",
    "AFP",
    "ISAPRE",
    "CONTRATO_CORTO",
    "SIRH",
    "BANCO",
    "CUENTA_CORRIENTE",
    "VIGENCIA",
    "AFP_SIN_SEGURO",
    "AFECTO_A_TURNO",
    "DIAS_TRABAJADOS",
    "CARGAS_FAMILIARES",
    "CARGAS_FAMILIARES_DUPLO",
    "ASIGNACION_FAMILIAR",
    "EXPERIENCIA_CALIFICADA",
    "FECHA_NACIMIENTO",
    "SEXO",
    "LEY_AFECTO",
    "OBSERVACION",
    "NUM_CORR_INTERNO",
    "TIPO_TURNO",
    "DERECHO_BONIF_TURNO",
    "OBS_HOJA_VIDA",
    "NIVEL",
    "TOTAL_HABER",
    # Metadatos de trazabilidad
    "FECHA_PRIMER_REGISTRO",  # cuando apareció por primera vez
    "FECHA_ULTIMO_UPDATE",    # último consolidado que lo actualizó
    "CONSOLIDADO_ORIGEN",     # nombre del archivo origen
    "ACTIVO",                 # 1=vigente en último consolidado, 0=ya no aparece
    "NOTAS_REFERENTE",        # campo libre editable por el referente técnico
]

# Mapeo de columna h3 del consolidado → campo de la BD
# (normalizado, sin espacios ni caracteres especiales)
H3_TO_CAMPO = {
    "RUT-DV":                   "RUT_DV",
    "CENTRO DE COSTO":          "CENTRO_DE_COSTO",
    "PROGRAMA":                 "PROGRAMA",
    "CORR":                     "CORR",
    "CORR. PAGO":               "CORR_PAGO",
    "NOMBRE":                   "NOMBRE",
    "ESTAB":                    "ESTAB",
    "CALIDAD JURIDICA":         "CALIDAD_JURIDICA",
    "HORAS / GRADOS":           "HORAS_GRADOS",
    "BIENIO / TRIENIO":         "BIENIO_TRIENIO",
    "PLANTA":                   "PLANTA",
    "UNIDAD":                   "UNIDAD",
    "CARGO":                    "CARGO",
    "AFP":                      "AFP",
    "ISAPRE":                   "ISAPRE",
    "CONTRATO CORTO":           "CONTRATO_CORTO",
    "SIRH":                     "SIRH",
    "BANCO":                    "BANCO",
    "CUENTA CORRIENTE":         "CUENTA_CORRIENTE",
    "VIGENCIA":                 "VIGENCIA",
    "AFP SIN SEGURO":           "AFP_SIN_SEGURO",
    "AFECTO A TURNO":           "AFECTO_A_TURNO",
    "DIAS TRABAJADOS":          "DIAS_TRABAJADOS",
    "CARGAS FAMILIARES":        "CARGAS_FAMILIARES",
    "CARGAS FAMILIARES DUPLO":  "CARGAS_FAMILIARES_DUPLO",
    "ASIGNACION FAMILIAR":      "ASIGNACION_FAMILIAR",
    "EXPERIENCIA CALIFICADA":   "EXPERIENCIA_CALIFICADA",
    "FECHA NACIMIENTO":         "FECHA_NACIMIENTO",
    "SEXO":                     "SEXO",
    "LEY AFECTO":               "LEY_AFECTO",
    "OBSERVACION":              "OBSERVACION",
    "NUM. CORR. INTERNO":       "NUM_CORR_INTERNO",
    "TIPO TURNO":               "TIPO_TURNO",
    "DERECHO A BONIF. TURNO":   "DERECHO_BONIF_TURNO",
    "OBSERVACION DE HOJA DE VIDA": "OBS_HOJA_VIDA",
    "NIVEL":                    "NIVEL",
    "TOTAL HABER":              "TOTAL_HABER",
}


# ══════════════════════════════════════════════════════════════════════════════
# Conexión y esquema
# ══════════════════════════════════════════════════════════════════════════════

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Crea las tablas si no existen."""
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS contratos (
            ID_CONTRATO           TEXT PRIMARY KEY,
            RUT_DV                TEXT,
            CENTRO_DE_COSTO       TEXT,
            PROGRAMA              TEXT,
            CORR                  TEXT,
            CORR_PAGO             TEXT,
            NOMBRE                TEXT,
            ESTAB                 TEXT,
            CALIDAD_JURIDICA      TEXT,
            HORAS_GRADOS          TEXT,
            BIENIO_TRIENIO        TEXT,
            PLANTA                TEXT,
            UNIDAD                TEXT,
            CARGO                 TEXT,
            AFP                   TEXT,
            ISAPRE                TEXT,
            CONTRATO_CORTO        TEXT,
            SIRH                  TEXT,
            BANCO                 TEXT,
            CUENTA_CORRIENTE      TEXT,
            VIGENCIA              TEXT,
            AFP_SIN_SEGURO        TEXT,
            AFECTO_A_TURNO        TEXT,
            DIAS_TRABAJADOS       TEXT,
            CARGAS_FAMILIARES     TEXT,
            CARGAS_FAMILIARES_DUPLO TEXT,
            ASIGNACION_FAMILIAR   TEXT,
            EXPERIENCIA_CALIFICADA TEXT,
            FECHA_NACIMIENTO      TEXT,
            SEXO                  TEXT,
            LEY_AFECTO            TEXT,
            OBSERVACION           TEXT,
            NUM_CORR_INTERNO      TEXT,
            TIPO_TURNO            TEXT,
            DERECHO_BONIF_TURNO   TEXT,
            OBS_HOJA_VIDA         TEXT,
            NIVEL                 TEXT,
            TOTAL_HABER           TEXT,
            FECHA_PRIMER_REGISTRO TEXT,
            FECHA_ULTIMO_UPDATE   TEXT,
            CONSOLIDADO_ORIGEN    TEXT,
            ACTIVO                INTEGER DEFAULT 1,
            NOTAS_REFERENTE       TEXT DEFAULT ''
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS historial_cambios (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_CONTRATO       TEXT,
            campo             TEXT,
            valor_anterior    TEXT,
            valor_nuevo       TEXT,
            fecha             TEXT,
            consolidado       TEXT,
            FOREIGN KEY (ID_CONTRATO) REFERENCES contratos(ID_CONTRATO)
        )
        """)

        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rut ON contratos(RUT_DV)
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_nombre ON contratos(NOMBRE)
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_activo ON contratos(ACTIVO)
        """)


# ══════════════════════════════════════════════════════════════════════════════
# Generación de ID único por contrato
# ══════════════════════════════════════════════════════════════════════════════

def generar_id_contrato(rut_dv: str, corr: str, ley_afecto: str,
                         horas_grados: str, centro_costo: str) -> str:
    """
    ID determinista: SHA256 de los 5 campos clave del contrato.
    Siempre produce el mismo ID para el mismo contrato.
    Si el funcionario cambia de CC → nuevo ID (se detecta el cambio).
    """
    raw = f"{rut_dv}|{corr}|{ley_afecto}|{horas_grados}|{centro_costo}"
    return "EVD-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12].upper()


# ══════════════════════════════════════════════════════════════════════════════
# Upsert masivo desde el consolidado
# ══════════════════════════════════════════════════════════════════════════════

def upsert_desde_consolidado(
    h3_out: list,
    data_out: list,
    nombre_archivo: str,
) -> dict:
    """
    Recibe los encabezados h3 y filas de datos del consolidado post-procesado.
    Hace upsert en la BD:
      - Si el ID no existe → INSERT (nuevo contrato)
      - Si el ID existe → UPDATE campos que cambiaron + log en historial
    Marca como ACTIVO=0 los contratos que ya no aparecen en este consolidado.

    Retorna: {"nuevos": N, "actualizados": N, "sin_cambio": N, "inactivos": N}
    """
    init_db()

    # Mapa h3 → índice de columna
    col_idx = {}
    for i, name in enumerate(h3_out):
        if name in H3_TO_CAMPO:
            col_idx[H3_TO_CAMPO[name]] = i

    def _get(row, campo):
        idx = col_idx.get(campo)
        if idx is None or idx >= len(row):
            return ""
        v = row[idx]
        if v is None:
            return ""
        return str(v).strip()

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stats = {"nuevos": 0, "actualizados": 0, "sin_cambio": 0, "inactivos": 0}

    ids_este_consolidado = set()

    with get_conn() as conn:
        for row in data_out:
            rut    = _get(row, "RUT_DV")
            corr   = _get(row, "CORR")
            ley    = _get(row, "LEY_AFECTO")
            horas  = _get(row, "HORAS_GRADOS")
            cc     = _get(row, "CENTRO_DE_COSTO")

            if not rut:
                continue

            id_c = generar_id_contrato(rut, corr, ley, horas, cc)
            ids_este_consolidado.add(id_c)

            # Construir dict de campos del consolidado
            nuevo = {campo: _get(row, campo) for campo in H3_TO_CAMPO.values()}
            nuevo["ID_CONTRATO"] = id_c

            # Verificar si ya existe
            existing = conn.execute(
                "SELECT * FROM contratos WHERE ID_CONTRATO = ?", (id_c,)
            ).fetchone()

            if existing is None:
                # INSERT
                nuevo["FECHA_PRIMER_REGISTRO"] = ahora
                nuevo["FECHA_ULTIMO_UPDATE"]   = ahora
                nuevo["CONSOLIDADO_ORIGEN"]    = nombre_archivo
                nuevo["ACTIVO"]                = 1
                nuevo["NOTAS_REFERENTE"]       = ""

                cols = ", ".join(nuevo.keys())
                placeholders = ", ".join(["?"] * len(nuevo))
                conn.execute(
                    f"INSERT INTO contratos ({cols}) VALUES ({placeholders})",
                    list(nuevo.values())
                )
                stats["nuevos"] += 1

            else:
                # Detectar cambios en campos actualizables (excluye metadatos y notas)
                campos_comparar = [c for c in H3_TO_CAMPO.values()]
                cambios = []
                for campo in campos_comparar:
                    v_old = str(existing[campo] or "").strip()
                    v_new = nuevo.get(campo, "")
                    if v_old != v_new:
                        cambios.append((campo, v_old, v_new))

                if cambios:
                    # UPDATE campos que cambiaron
                    set_parts = ", ".join(
                        [f"{c} = ?" for c, _, _ in cambios] +
                        ["FECHA_ULTIMO_UPDATE = ?", "CONSOLIDADO_ORIGEN = ?", "ACTIVO = 1"]
                    )
                    vals = [v_new for _, _, v_new in cambios] + [ahora, nombre_archivo, id_c]
                    conn.execute(f"UPDATE contratos SET {set_parts} WHERE ID_CONTRATO = ?", vals)

                    # Log en historial
                    for campo, v_old, v_new in cambios:
                        conn.execute(
                            "INSERT INTO historial_cambios (ID_CONTRATO, campo, valor_anterior, valor_nuevo, fecha, consolidado) VALUES (?,?,?,?,?,?)",
                            (id_c, campo, v_old, v_new, ahora, nombre_archivo)
                        )
                    stats["actualizados"] += 1
                else:
                    # Solo actualizar metadatos
                    conn.execute(
                        "UPDATE contratos SET FECHA_ULTIMO_UPDATE=?, CONSOLIDADO_ORIGEN=?, ACTIVO=1 WHERE ID_CONTRATO=?",
                        (ahora, nombre_archivo, id_c)
                    )
                    stats["sin_cambio"] += 1

        # Marcar como inactivos los que no aparecieron en este consolidado
        if ids_este_consolidado:
            placeholders = ",".join(["?"] * len(ids_este_consolidado))
            result = conn.execute(
                f"UPDATE contratos SET ACTIVO=0 WHERE ID_CONTRATO NOT IN ({placeholders}) AND ACTIVO=1",
                list(ids_este_consolidado)
            )
            stats["inactivos"] = result.rowcount

    return stats


# ══════════════════════════════════════════════════════════════════════════════
# Consultas
# ══════════════════════════════════════════════════════════════════════════════

def get_todos(solo_activos=True, filtro_nombre="", filtro_rut="",
              filtro_cc="", filtro_ley="", filtro_calidad="") -> list:
    init_db()
    query = "SELECT * FROM contratos WHERE 1=1"
    params = []
    if solo_activos:
        query += " AND ACTIVO = 1"
    if filtro_nombre:
        query += " AND NOMBRE LIKE ?"
        params.append(f"%{filtro_nombre}%")
    if filtro_rut:
        query += " AND RUT_DV LIKE ?"
        params.append(f"%{filtro_rut}%")
    if filtro_cc:
        query += " AND CENTRO_DE_COSTO = ?"
        params.append(filtro_cc)
    if filtro_ley:
        query += " AND LEY_AFECTO = ?"
        params.append(filtro_ley)
    if filtro_calidad:
        query += " AND CALIDAD_JURIDICA = ?"
        params.append(filtro_calidad)
    query += " ORDER BY NOMBRE, HORAS_GRADOS"
    with get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_contrato(id_contrato: str) -> Optional[dict]:
    init_db()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM contratos WHERE ID_CONTRATO = ?", (id_contrato,)
        ).fetchone()
    return dict(row) if row else None


def get_historial(id_contrato: str) -> list:
    init_db()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM historial_cambios WHERE ID_CONTRATO = ? ORDER BY fecha DESC",
            (id_contrato,)
        ).fetchall()
    return [dict(r) for r in rows]


def update_notas(id_contrato: str, notas: str):
    init_db()
    with get_conn() as conn:
        conn.execute(
            "UPDATE contratos SET NOTAS_REFERENTE=?, FECHA_ULTIMO_UPDATE=? WHERE ID_CONTRATO=?",
            (notas, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), id_contrato)
        )


def update_campo(id_contrato: str, campo: str, valor: str, consolidado: str = "edición manual"):
    """Edita un campo con registro en historial."""
    init_db()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_conn() as conn:
        old = conn.execute(
            f"SELECT {campo} FROM contratos WHERE ID_CONTRATO=?", (id_contrato,)
        ).fetchone()
        v_old = str(old[0] or "") if old else ""
        conn.execute(
            f"UPDATE contratos SET {campo}=?, FECHA_ULTIMO_UPDATE=? WHERE ID_CONTRATO=?",
            (valor, ahora, id_contrato)
        )
        conn.execute(
            "INSERT INTO historial_cambios (ID_CONTRATO, campo, valor_anterior, valor_nuevo, fecha, consolidado) VALUES (?,?,?,?,?,?)",
            (id_contrato, campo, v_old, valor, ahora, consolidado)
        )


def get_stats() -> dict:
    init_db()
    with get_conn() as conn:
        total       = conn.execute("SELECT COUNT(*) FROM contratos WHERE ACTIVO=1").fetchone()[0]
        funcionarios= conn.execute("SELECT COUNT(DISTINCT RUT_DV) FROM contratos WHERE ACTIVO=1").fetchone()[0]
        por_ley     = conn.execute("SELECT LEY_AFECTO, COUNT(*) as n FROM contratos WHERE ACTIVO=1 GROUP BY LEY_AFECTO ORDER BY n DESC").fetchall()
        por_calidad = conn.execute("SELECT CALIDAD_JURIDICA, COUNT(*) as n FROM contratos WHERE ACTIVO=1 GROUP BY CALIDAD_JURIDICA ORDER BY n DESC").fetchall()
        por_cc      = conn.execute("SELECT CENTRO_DE_COSTO, COUNT(*) as n FROM contratos WHERE ACTIVO=1 GROUP BY CENTRO_DE_COSTO ORDER BY n DESC").fetchall()
        inactivos   = conn.execute("SELECT COUNT(*) FROM contratos WHERE ACTIVO=0").fetchone()[0]
    return {
        "total_contratos": total,
        "total_funcionarios": funcionarios,
        "por_ley": [dict(r) for r in por_ley],
        "por_calidad": [dict(r) for r in por_calidad],
        "por_cc": [dict(r) for r in por_cc],
        "inactivos": inactivos,
    }


def get_distinct(campo: str) -> list:
    init_db()
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT {campo} FROM contratos WHERE ACTIVO=1 AND {campo} != '' ORDER BY {campo}"
        ).fetchall()
    return [r[0] for r in rows]

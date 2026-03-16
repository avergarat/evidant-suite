# -*- coding: utf-8 -*-
"""
revision_dotacion/db_rev.py
Base de datos SQLite persistente para el módulo de Revisión de Dotación por Centro.

Tablas:
  horas_indirectas_general  — lista de horas indirectas por encargatura (común a todos los CESFAM)
  horas_indirectas_cesfam   — matriz de horas por encargatura x CESFAM (específica por centro)
  unidades_desempeno        — mapeo CESFAM + Unidad SIRH → Unidad de Desempeño real
  asignaciones_funcionarios — encargaturas asignadas por funcionario en un mes/año
  revision_mensual          — repositorio histórico de revisión mensual
  dotacion_ideal            — dotación ideal por estamento/cargo/CESFAM
"""

import os
import sqlite3
import datetime
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_ROOT, "revision_dotacion", "rev_dotacion.db")

# ──────────────────────────────────────────────────────────────────────────────
# HORAS INDIRECTAS — datos base (desde imagen de referencia)
# ──────────────────────────────────────────────────────────────────────────────
_HRS_GRUPALES = [
    ("GRUPAL", "Delegados gremiales",                                   0.00),
    ("GRUPAL", "Asociados gremiales",                                   0.00),
    ("GRUPAL", "Dirigente Gremial",                                    44.00),
    ("GRUPAL", "Días administrativos Ley médica",                       2.13),
    ("GRUPAL", "Días Capacitación Extra Ley Médica",                    1.06),
    ("GRUPAL", "Vacaciones extra 5 días",                               0.89),
    ("GRUPAL", "Vacaciones extras 10 días",                             1.77),
    ("GRUPAL", "Fuero Lactancia",                                       5.00),
    ("GRUPAL", "Asamblea General",                                      0.50),
    ("GRUPAL", "Reunión de Autocuidado",                                0.50),
    ("GRUPAL", "Programación",                                          0.53),
    ("GRUPAL", "Reuniones de Sector con análisis de casos",             1.00),
    ("GRUPAL", "Estudios de caso",                                      0.82),
    ("GRUPAL", "Día administrativos Ley N° 18834",                      1.06),
    ("GRUPAL", "Reunión de Programa",                                   0.50),
    ("GRUPAL", "Censo mensual",                                         2.13),
    ("GRUPAL", "Censo semestral",                                       1.06),
    ("GRUPAL", "Consejo Técnico",                                       0.75),
    ("GRUPAL", "Equipo Gestor",                                         2.00),
    ("GRUPAL", "Reunión de Estamento",                                  0.13),
    ("GRUPAL", "Comité paritario",                                      0.25),
    ("GRUPAL", "Comité capacitacion",                                   0.50),
    ("GRUPAL", "Comité OIRS",                                           0.50),
    ("GRUPAL", "Comité de Lactancia Materna",                           0.50),
    ("GRUPAL", "Comité de Calidad",                                     0.50),
    ("GRUPAL", "Comité de farmacia",                                    0.38),
    ("GRUPAL", "Comité de género",                                      0.50),
    ("GRUPAL", "Comité de Cultura Local",                               0.50),
    ("GRUPAL", "Comité de Seguridad",                                   0.25),
    ("GRUPAL", "Comité de Riesgos Psicosociales",                       0.50),
    ("GRUPAL", "Mesa de Género y LGTBQ+Funcionarios",                   0.25),
]

_HRS_INDIVIDUALES = [
    ("INDIVIDUAL", "Contraloría Médica",                                            5.00),
    ("INDIVIDUAL", "Odontólogo Contralor",                                          2.50),
    ("INDIVIDUAL", "Matron/a Contralor",                                            2.50),
    ("INDIVIDUAL", "Coordinador Programa Odontológico",                            11.00),
    ("INDIVIDUAL", "Coordinador Programa Infantil, Adolescente y Ch CC",           11.00),
    ("INDIVIDUAL", "Coordinador Programa Infantil, Adolescente y Ch CC (Espacio Amigable)", 13.00),
    ("INDIVIDUAL", "Encargado Programa Salud Mental",                              11.00),
    ("INDIVIDUAL", "Encargada Programa Salud sexual y reproductiva",                9.00),
    ("INDIVIDUAL", "Encargada Programa Salud sexual y reproductiva (incluye VIH)", 11.00),
    ("INDIVIDUAL", "Jefe de Sector",                                               22.00),
    ("INDIVIDUAL", "Coordinador CECOSF",                                           22.00),
    ("INDIVIDUAL", "Jefe de Farmacia",                                             33.00),
    ("INDIVIDUAL", "Coordinador de SAPU Corto",                                    15.00),
    ("INDIVIDUAL", "Coordinador de SAPU Largo (104,113,107)",                      15.00),
    ("INDIVIDUAL", "Coordinador de SAR",                                           44.00),
    ("INDIVIDUAL", "Encargado MAIS",                                                3.00),
    ("INDIVIDUAL", "Encargado de Calidad",                                         22.00),
    ("INDIVIDUAL", "Encargado de REAS",                                             5.00),
    ("INDIVIDUAL", "Encargado IAAS",                                                5.00),
    ("INDIVIDUAL", "Encargado Programa Adulto",                                    11.00),
    ("INDIVIDUAL", "Encargado Programa Adulto Mayor",                              11.00),
    ("INDIVIDUAL", "Encargado Apoyo Clínico e Inmunizaciones",                     44.00),
    ("INDIVIDUAL", "Delegado Epidemiología < 30.000 PIV",                           5.00),
    ("INDIVIDUAL", "Delegado Epidemiología > 30.000 PIV",                          11.00),
    ("INDIVIDUAL", "Encargado Programa TBC",                                        2.00),
    ("INDIVIDUAL", "Supervisor Programa Alimentario 20.000 a 35.000 PVI",         10.00),
    ("INDIVIDUAL", "Supervisor Programa Alimentario > 35.000 PVI",                 12.50),
    ("INDIVIDUAL", "Encargado de Género",                                           2.00),
    ("INDIVIDUAL", "Encargado Salud Intercultural (PESPI y Migrantes)",             5.00),
    ("INDIVIDUAL", "Encargado Participación y OIRS",                               22.00),
    ("INDIVIDUAL", "Encargado Sala ERA",                                            1.50),
    ("INDIVIDUAL", "Encargado Sala IRA",                                            1.50),
    ("INDIVIDUAL", "Encargado Sala Rehabilitación Comunitaria",                     2.00),
    ("INDIVIDUAL", "Subdirección Técnica",                                         44.00),
    ("INDIVIDUAL", "Subdirector de Gestión Administrativa",                        44.00),
    ("INDIVIDUAL", "Director/a",                                                   44.00),
    ("INDIVIDUAL", "Encargado RAD",                                                 5.00),
    ("INDIVIDUAL", "Encargado tecnovigilancia",                                     2.00),
    ("INDIVIDUAL", "Encargado/a Telesalud o formularios gestión de la demanda",    10.00),
    ("INDIVIDUAL", "Gestor/a Telesalud o formularios gestión de la demanda",        5.00),
]

_HRS_DEFAULT = _HRS_GRUPALES + _HRS_INDIVIDUALES

# Encargaturas y sus horas por CESFAM (visible desde imagen 3)
# Formato: (encargatura, cesfam_nro1, cesfam_nro5, cesfam_pvi, cesfam_mercedes,
#            cesfam_chuchunco, cesfam_maipu, cesfam_ahues, cesfam_juricic,
#            cesfam_voullieme, cesfam_pincheira)
_CESFAM_KEYS = [
    "CESFAM Nº1", "CESFAM Nº5", "CESFAM PVI", "CESFAM Las Mercedes",
    "CESFAM Chuchunco", "CESFAM Maipu", "CESFAM Ahues",
    "CESFAM Juricic", "CESFAM Voullieme", "CESFAM Pincheira",
]

# Matriz de horas por encargatura x CESFAM (extraída de imagen 3)
# None = NA (no aplica en ese CESFAM)
_MATRIZ_CESFAM = [
    # (encargatura, [horas por cada CESFAM en _CESFAM_KEYS order])
    ("Director/a",                      [44, 44, 44, 44, 44, 44, 44, 44, 44, 44]),
    ("Subdirección Técnica",            [44, 44, 44, 44, 44, 44, 44, 44, 44, 44]),
    ("Subdirector de Gestión Administrativa", [44, 44, 44, 44, 44, 44, 44, 44, 44, 44]),
    ("Coordinador CECOSF",              [None, None, None, None, 22, 22, 22, None, 22, None]),
    ("Jefe de Sector",                  [22, 22, 22, 22, 22, 22, 22, None, 22, 22]),
    ("Encargado de Calidad",            [22, 22, 10, 33, 44, 77, 22, 22, 22, 22]),
    ("Encargado Apoyo Clínico e Inmunizaciones", [22, 22, 22, 39, 22, 22, 22, 22, 22, 17]),
    ("Encargado de Reas",               [None, None, None, None, None, None, None, None, None, None]),
    ("Encargado IAAS",                  [11, 11, 11, 10, 11, 6, 11, 11, 11, 11]),
    ("Delegado Epidemiología < 30.000 PIV", [10, 22, 3, 11, 9.5, None, 4.5, 8, 11, 5]),
    ("Encargado Programa TBC",          [22, 5, 8, 5, 5, 2, 5, 3, 10, 5]),
    ("Jefe de Farmacia",                [44, 33, 44, 44, 44, 44, 44, None, 44, 44]),
    ("Encargado Programa Salud Mental", [22, 22, 22, 11, 11, 11, 11, 22, 10, 11]),
    ("Encargada Programa Salud sexual y reproductiva", [None, 6, 9, 6, 6, 11, 11, 11, 8, 6]),
    ("Encargada Programa Salud sexual y reproductiva (incluye VIH)", [None, None, None, None, None, None, None, None, None, None]),
    ("Contraloría Médica",              [10, 5.5, 11, 5, 7.5, 10, 5, 5, None, 5]),
    ("Matron/a Contralor",              [None, 5, None, 5, None, 6, 5, None, 2, 5]),
    ("Odontólogo Contralor",            [5, 5, None, 5, 5, 5, 5, None, 5, 5]),
    ("Coordinador Programa Odontológico", [11, 10, 11, 11, 11, 6, 11, 22, 11, 11]),
    ("Encargado Participación y OIRS",  [22, 22, 11, 22, 22, 22, 22, 5.5, 11, 22]),
    ("Encargado Sala ERA",              [3, 11, 11, 3, 3, 2, 3, 11, 4, 5.5]),
    ("Encargado Sala IRA",              [None, 3, 11, 3, 3, 3, 3, 5.5, 4, 5.5]),
    ("Encargado RAD",                   [11, 7, 11, 2.5, 11, 2, 5, 11, None, 11]),
    ("Encargado Sala RBC",              [None, 8, 3, 7, 4, None, 4, 3, None, 4]),
    ("Encargado OIRS",                  [None, None, 11, None, 22, 22, None, 11, 22, 22]),
    ("Encargado Programa Infantil",     [11, 10, 11, 5, 5.5, 5, 5.5, 11, 5.5, 5.5]),
    ("Coordinador Programa Infantil, Adolescente y Ch CC", [11, 11, 11, 5, 5.5, 5, 5.5, 11, 5.5, 5.5]),
    ("Coordinador Programa Infantil, Adolescente y Ch CC (Espacio Amigable)", [None, None, None, None, None, 5.5, None, None, 4, None]),
    ("Encargado Programa Adulto",       [8, 8, 8, 8, 4, 11, 8, 8, 8, 8]),
    ("Encargado Programa Adulto Mayor", [3, 3, 3, 3, 6, 11, 3, 3, 10, 3]),
    ("Encargado Programa de Salud Mental", [22, 22, 22, 11, 11, 11, 11, 22, 10, 11]),
    ("Encargado MAIS",                  [11, None, 4, None, None, 4, 11, 22, 7, 5]),
    ("Encargado tecnovigilancia",       [None, None, 11, None, None, 2, None, None, None, None]),
    ("Encargado Salud Intercultural (PESPI y Migrantes)", [11, None, 3, None, 4, 2.5, 3, 5, 5.5, 2]),
    ("Supervisor Programa Alimentario 20.000 a 35.000 PVI", [11, 11, 11, 7.5, 7.5, 22, 11, 11, 10, 11]),
    ("Encargado de Género",             [None, None, None, 5, None, 2, 3, 5.5, 3, 3]),
]


# ──────────────────────────────────────────────────────────────────────────────
# CONEXIÓN Y ESQUEMA
# ──────────────────────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


def init_db():
    """Crea las tablas si no existen y pre-pobla los datos base."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = _conn()
    cur = con.cursor()

    # Horas indirectas generales
    cur.execute("""
        CREATE TABLE IF NOT EXISTS horas_indirectas_general (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo   TEXT    NOT NULL,
            nombre TEXT    NOT NULL UNIQUE,
            horas  REAL    NOT NULL DEFAULT 0.0
        )""")

    # Horas indirectas por CESFAM (matriz)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS horas_indirectas_cesfam (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cesfam      TEXT    NOT NULL,
            encargatura TEXT    NOT NULL,
            horas       REAL    NOT NULL DEFAULT 0.0,
            UNIQUE(cesfam, encargatura)
        )""")

    # Mapeo de unidades de desempeño
    cur.execute("""
        CREATE TABLE IF NOT EXISTS unidades_desempeno (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            cesfam          TEXT    NOT NULL,
            unidad_sirh     TEXT    NOT NULL,
            unidad_desempeno TEXT   NOT NULL,
            UNIQUE(cesfam, unidad_sirh)
        )""")

    # Asignaciones de encargatura por funcionario (por mes)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS asignaciones_funcionarios (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            mes_anio         TEXT    NOT NULL,
            rut              TEXT    NOT NULL,
            nombre           TEXT,
            cesfam           TEXT,
            encargatura      TEXT    NOT NULL,
            horas_indirectas REAL    DEFAULT 0.0,
            fuente           TEXT    DEFAULT 'GENERAL',
            UNIQUE(mes_anio, rut, encargatura)
        )""")

    # Repositorio mensual de revisión
    cur.execute("""
        CREATE TABLE IF NOT EXISTS revision_mensual (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            mes_anio              TEXT    NOT NULL,
            rut                   TEXT    NOT NULL,
            dv                    TEXT,
            nombre                TEXT,
            cesfam                TEXT,
            descripcion_unidad    TEXT,
            calidad_juridica      TEXT,
            descripcion_cargo     TEXT,
            descripcion_planta    TEXT,
            unidad_desempeno      TEXT,
            horas_contrato        REAL    DEFAULT 0.0,
            horas_indirectas_total REAL   DEFAULT 0.0,
            horas_clinicas        REAL    DEFAULT 0.0,
            observaciones         TEXT,
            timestamp_creacion    TEXT,
            UNIQUE(mes_anio, rut)
        )""")

    # Dotación ideal por estamento/cargo/CESFAM
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dotacion_ideal (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cesfam      TEXT    NOT NULL,
            estamento   TEXT    NOT NULL,
            cargo       TEXT,
            horas_ideal REAL    DEFAULT 0.0,
            n_ideal     REAL    DEFAULT 0.0,
            UNIQUE(cesfam, estamento, cargo)
        )""")

    con.commit()

    # Pre-poblar horas indirectas generales si está vacía
    n = cur.execute("SELECT COUNT(*) FROM horas_indirectas_general").fetchone()[0]
    if n == 0:
        cur.executemany(
            "INSERT OR IGNORE INTO horas_indirectas_general (tipo, nombre, horas) VALUES (?,?,?)",
            _HRS_DEFAULT,
        )
        con.commit()

    # Pre-poblar horas por CESFAM si está vacía
    n2 = cur.execute("SELECT COUNT(*) FROM horas_indirectas_cesfam").fetchone()[0]
    if n2 == 0:
        rows = []
        for encarg, valores in _MATRIZ_CESFAM:
            for cesfam, hrs in zip(_CESFAM_KEYS, valores):
                if hrs is not None:
                    rows.append((cesfam, encarg, float(hrs)))
        if rows:
            cur.executemany(
                "INSERT OR IGNORE INTO horas_indirectas_cesfam (cesfam, encargatura, horas) VALUES (?,?,?)",
                rows,
            )
            con.commit()

    con.close()


# ──────────────────────────────────────────────────────────────────────────────
# HORAS INDIRECTAS — CRUD
# ──────────────────────────────────────────────────────────────────────────────

def get_horas_general() -> pd.DataFrame:
    con = _conn()
    df = pd.read_sql("SELECT id, tipo, nombre, horas FROM horas_indirectas_general ORDER BY tipo, nombre", con)
    con.close()
    return df


def upsert_hora_general(nombre: str, tipo: str, horas: float):
    con = _conn()
    con.execute(
        "INSERT INTO horas_indirectas_general (tipo, nombre, horas) VALUES (?,?,?) "
        "ON CONFLICT(nombre) DO UPDATE SET tipo=excluded.tipo, horas=excluded.horas",
        (tipo, nombre, horas),
    )
    con.commit(); con.close()


def delete_hora_general(id_: int):
    con = _conn()
    con.execute("DELETE FROM horas_indirectas_general WHERE id=?", (id_,))
    con.commit(); con.close()


def get_horas_cesfam(cesfam: str = None) -> pd.DataFrame:
    con = _conn()
    if cesfam:
        df = pd.read_sql(
            "SELECT id, cesfam, encargatura, horas FROM horas_indirectas_cesfam WHERE cesfam=? ORDER BY encargatura",
            con, params=(cesfam,),
        )
    else:
        df = pd.read_sql(
            "SELECT id, cesfam, encargatura, horas FROM horas_indirectas_cesfam ORDER BY cesfam, encargatura",
            con,
        )
    con.close()
    return df


def upsert_hora_cesfam(cesfam: str, encargatura: str, horas: float):
    con = _conn()
    con.execute(
        "INSERT INTO horas_indirectas_cesfam (cesfam, encargatura, horas) VALUES (?,?,?) "
        "ON CONFLICT(cesfam, encargatura) DO UPDATE SET horas=excluded.horas",
        (cesfam, encargatura, horas),
    )
    con.commit(); con.close()


def delete_hora_cesfam(id_: int):
    con = _conn()
    con.execute("DELETE FROM horas_indirectas_cesfam WHERE id=?", (id_,))
    con.commit(); con.close()


def get_horas_pivot() -> pd.DataFrame:
    """Retorna la matriz encargatura x CESFAM para visualización."""
    con = _conn()
    df = pd.read_sql("SELECT cesfam, encargatura, horas FROM horas_indirectas_cesfam", con)
    con.close()
    if df.empty:
        return df
    return df.pivot_table(index="encargatura", columns="cesfam", values="horas", aggfunc="first")


def resolver_horas_encargatura(cesfam: str, encargatura: str) -> float:
    """
    Resuelve las horas para una encargatura:
    1. Busca en horas_indirectas_cesfam (específica por CESFAM)
    2. Si no existe, busca en horas_indirectas_general
    3. Si tampoco, retorna 0.0
    """
    con = _conn()
    # 1. Tabla CESFAM-específica (coincidencia exacta o fuzzy por contiene)
    row = con.execute(
        "SELECT horas FROM horas_indirectas_cesfam WHERE cesfam=? AND encargatura=?",
        (cesfam, encargatura),
    ).fetchone()
    if row:
        con.close()
        return float(row[0])
    # 2. Tabla general
    row2 = con.execute(
        "SELECT horas FROM horas_indirectas_general WHERE nombre=?",
        (encargatura,),
    ).fetchone()
    con.close()
    return float(row2[0]) if row2 else 0.0


# ──────────────────────────────────────────────────────────────────────────────
# UNIDADES DE DESEMPEÑO — CRUD
# ──────────────────────────────────────────────────────────────────────────────

def get_unidades_desempeno(cesfam: str = None) -> pd.DataFrame:
    con = _conn()
    if cesfam:
        df = pd.read_sql(
            "SELECT id, cesfam, unidad_sirh, unidad_desempeno FROM unidades_desempeno WHERE cesfam=? ORDER BY unidad_sirh",
            con, params=(cesfam,),
        )
    else:
        df = pd.read_sql(
            "SELECT id, cesfam, unidad_sirh, unidad_desempeno FROM unidades_desempeno ORDER BY cesfam, unidad_sirh",
            con,
        )
    con.close()
    return df


def upsert_unidad_desempeno(cesfam: str, unidad_sirh: str, unidad_desempeno: str):
    con = _conn()
    con.execute(
        "INSERT INTO unidades_desempeno (cesfam, unidad_sirh, unidad_desempeno) VALUES (?,?,?) "
        "ON CONFLICT(cesfam, unidad_sirh) DO UPDATE SET unidad_desempeno=excluded.unidad_desempeno",
        (cesfam, unidad_sirh, unidad_desempeno),
    )
    con.commit(); con.close()


def delete_unidad_desempeno(id_: int):
    con = _conn()
    con.execute("DELETE FROM unidades_desempeno WHERE id=?", (id_,))
    con.commit(); con.close()


def resolver_unidad_desempeno(cesfam: str, unidad_sirh: str) -> str:
    """Resuelve la unidad de desempeño real para un valor SIRH dado."""
    con = _conn()
    row = con.execute(
        "SELECT unidad_desempeno FROM unidades_desempeno WHERE cesfam=? AND unidad_sirh=?",
        (cesfam, unidad_sirh),
    ).fetchone()
    con.close()
    return row[0] if row else ""


# ──────────────────────────────────────────────────────────────────────────────
# ASIGNACIONES DE FUNCIONARIOS — CRUD
# ──────────────────────────────────────────────────────────────────────────────

def get_asignaciones(mes_anio: str, rut: str = None) -> pd.DataFrame:
    con = _conn()
    if rut:
        df = pd.read_sql(
            "SELECT * FROM asignaciones_funcionarios WHERE mes_anio=? AND rut=?",
            con, params=(mes_anio, rut),
        )
    else:
        df = pd.read_sql(
            "SELECT * FROM asignaciones_funcionarios WHERE mes_anio=? ORDER BY nombre, encargatura",
            con, params=(mes_anio,),
        )
    con.close()
    return df


def save_asignaciones_rut(mes_anio: str, rut: str, nombre: str, cesfam: str, encargaturas: list):
    """
    Guarda (reemplaza) las encargaturas de un funcionario para un mes.
    encargaturas: lista de (encargatura, horas, fuente)
    """
    con = _conn()
    con.execute(
        "DELETE FROM asignaciones_funcionarios WHERE mes_anio=? AND rut=?",
        (mes_anio, rut),
    )
    for encarg, hrs, fuente in encargaturas:
        con.execute(
            "INSERT OR IGNORE INTO asignaciones_funcionarios "
            "(mes_anio, rut, nombre, cesfam, encargatura, horas_indirectas, fuente) VALUES (?,?,?,?,?,?,?)",
            (mes_anio, rut, nombre, cesfam, encarg, hrs, fuente),
        )
    con.commit(); con.close()


# ──────────────────────────────────────────────────────────────────────────────
# REPOSITORIO MENSUAL — CRUD
# ──────────────────────────────────────────────────────────────────────────────

def get_meses_disponibles() -> list:
    con = _conn()
    rows = con.execute(
        "SELECT DISTINCT mes_anio FROM revision_mensual ORDER BY mes_anio DESC"
    ).fetchall()
    con.close()
    return [r[0] for r in rows]


def get_revision_mensual(mes_anio: str, cesfam: str = None) -> pd.DataFrame:
    con = _conn()
    if cesfam:
        df = pd.read_sql(
            "SELECT * FROM revision_mensual WHERE mes_anio=? AND cesfam=? ORDER BY nombre",
            con, params=(mes_anio, cesfam),
        )
    else:
        df = pd.read_sql(
            "SELECT * FROM revision_mensual WHERE mes_anio=? ORDER BY cesfam, nombre",
            con, params=(mes_anio,),
        )
    con.close()
    return df


def save_revision_mensual(mes_anio: str, rows: list):
    """
    Guarda o actualiza registros de revisión mensual.
    rows: lista de dicts con claves:
      rut, dv, nombre, cesfam, descripcion_unidad, calidad_juridica,
      descripcion_cargo, descripcion_planta, unidad_desempeno,
      horas_contrato, horas_indirectas_total, horas_clinicas, observaciones
    """
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = _conn()
    for r in rows:
        con.execute("""
            INSERT INTO revision_mensual
              (mes_anio, rut, dv, nombre, cesfam, descripcion_unidad,
               calidad_juridica, descripcion_cargo, descripcion_planta,
               unidad_desempeno, horas_contrato, horas_indirectas_total,
               horas_clinicas, observaciones, timestamp_creacion)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(mes_anio, rut) DO UPDATE SET
              dv=excluded.dv,
              nombre=excluded.nombre,
              cesfam=excluded.cesfam,
              descripcion_unidad=excluded.descripcion_unidad,
              calidad_juridica=excluded.calidad_juridica,
              descripcion_cargo=excluded.descripcion_cargo,
              descripcion_planta=excluded.descripcion_planta,
              unidad_desempeno=excluded.unidad_desempeno,
              horas_contrato=excluded.horas_contrato,
              horas_indirectas_total=excluded.horas_indirectas_total,
              horas_clinicas=excluded.horas_clinicas,
              observaciones=excluded.observaciones,
              timestamp_creacion=excluded.timestamp_creacion
        """, (
            mes_anio,
            r.get("rut", ""),
            r.get("dv", ""),
            r.get("nombre", ""),
            r.get("cesfam", ""),
            r.get("descripcion_unidad", ""),
            r.get("calidad_juridica", ""),
            r.get("descripcion_cargo", ""),
            r.get("descripcion_planta", ""),
            r.get("unidad_desempeno", ""),
            r.get("horas_contrato", 0.0),
            r.get("horas_indirectas_total", 0.0),
            r.get("horas_clinicas", 0.0),
            r.get("observaciones", ""),
            ts,
        ))
    con.commit(); con.close()


def delete_revision_mensual(mes_anio: str, cesfam: str = None):
    con = _conn()
    if cesfam:
        con.execute(
            "DELETE FROM revision_mensual WHERE mes_anio=? AND cesfam=?",
            (mes_anio, cesfam),
        )
    else:
        con.execute("DELETE FROM revision_mensual WHERE mes_anio=?", (mes_anio,))
    con.commit(); con.close()


# ──────────────────────────────────────────────────────────────────────────────
# DOTACIÓN IDEAL — CRUD
# ──────────────────────────────────────────────────────────────────────────────

def get_dotacion_ideal(cesfam: str = None) -> pd.DataFrame:
    con = _conn()
    if cesfam:
        df = pd.read_sql(
            "SELECT * FROM dotacion_ideal WHERE cesfam=? ORDER BY estamento, cargo",
            con, params=(cesfam,),
        )
    else:
        df = pd.read_sql(
            "SELECT * FROM dotacion_ideal ORDER BY cesfam, estamento, cargo",
            con,
        )
    con.close()
    return df


def upsert_dotacion_ideal(cesfam: str, estamento: str, cargo: str, horas_ideal: float, n_ideal: float):
    con = _conn()
    con.execute(
        "INSERT INTO dotacion_ideal (cesfam, estamento, cargo, horas_ideal, n_ideal) VALUES (?,?,?,?,?) "
        "ON CONFLICT(cesfam, estamento, cargo) DO UPDATE SET horas_ideal=excluded.horas_ideal, n_ideal=excluded.n_ideal",
        (cesfam, estamento, cargo, horas_ideal, n_ideal),
    )
    con.commit(); con.close()


def delete_dotacion_ideal(id_: int):
    con = _conn()
    con.execute("DELETE FROM dotacion_ideal WHERE id=?", (id_,))
    con.commit(); con.close()


def import_dotacion_ideal_from_df(df_ideal: pd.DataFrame):
    """
    Importa dotación ideal desde un DataFrame con columnas:
    cesfam, estamento, cargo, horas_ideal, n_ideal
    """
    con = _conn()
    for _, row in df_ideal.iterrows():
        con.execute(
            "INSERT INTO dotacion_ideal (cesfam, estamento, cargo, horas_ideal, n_ideal) VALUES (?,?,?,?,?) "
            "ON CONFLICT(cesfam, estamento, cargo) DO UPDATE SET horas_ideal=excluded.horas_ideal, n_ideal=excluded.n_ideal",
            (
                str(row.get("cesfam", "")),
                str(row.get("estamento", "")),
                str(row.get("cargo", "")),
                float(row.get("horas_ideal", 0) or 0),
                float(row.get("n_ideal", 0) or 0),
            ),
        )
    con.commit(); con.close()

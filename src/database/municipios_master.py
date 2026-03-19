"""
Tabla maestra de municipios con datos tributarios para ICA.
Pobladla con los 60 municipios activos de PCC Integrity en 2025.

IMPORTANTE: Las tarifas marcadas con verificado=False son estimadas
basadas en promedios regionales. Verificar con cada municipio antes
de presentar declaraciones.

Fuentes confirmadas:
  - Santa Marta 7‰: Declaración ICA 2025 presentada (Formulario Único Nacional)
"""
from typing import Optional
import pandas as pd
from src.database.models import MunicipioICA

# ---------------------------------------------------------------------------
# Tabla maestra — 60 municipios activos PCC 2025
# ---------------------------------------------------------------------------
MUNICIPIOS_ICA: dict[str, MunicipioICA] = {

    # ── Antioquia ──────────────────────────────────────────────────────────
    "ARBOLETES": MunicipioICA(
        nombre="ARBOLETES", departamento="ANTIOQUIA",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "CAUCASIA": MunicipioICA(
        nombre="CAUCASIA", departamento="ANTIOQUIA",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "MEDELLÍN": MunicipioICA(
        nombre="MEDELLÍN", departamento="ANTIOQUIA",
        periodicidad="ANUAL", tarifa_por_mil=9.66,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "PUERTO BERRIO": MunicipioICA(
        nombre="PUERTO BERRIO", departamento="ANTIOQUIA",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "REMEDIOS": MunicipioICA(
        nombre="REMEDIOS", departamento="ANTIOQUIA",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "SEGOVIA": MunicipioICA(
        nombre="SEGOVIA", departamento="ANTIOQUIA",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Atlántico ──────────────────────────────────────────────────────────
    "BARRANQUILLA": MunicipioICA(
        nombre="BARRANQUILLA", departamento="ATLÁNTICO",
        periodicidad="ANUAL", tarifa_por_mil=8.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Bolívar ────────────────────────────────────────────────────────────
    "CARTAGENA": MunicipioICA(
        nombre="CARTAGENA", departamento="BOLÍVAR",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "SANTA ROSA": MunicipioICA(
        nombre="SANTA ROSA", departamento="BOLÍVAR",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Boyacá ─────────────────────────────────────────────────────────────
    "JENESANO": MunicipioICA(
        nombre="JENESANO", departamento="BOYACÁ",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "MIRAFLORES": MunicipioICA(
        nombre="MIRAFLORES", departamento="BOYACÁ",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "OTANCHE": MunicipioICA(
        nombre="OTANCHE", departamento="BOYACÁ",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "PAEZ": MunicipioICA(
        nombre="PAEZ", departamento="BOYACÁ",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "PUERTO BOYACA": MunicipioICA(
        nombre="PUERTO BOYACA", departamento="BOYACÁ",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "SOGAMOSO": MunicipioICA(
        nombre="SOGAMOSO", departamento="BOYACÁ",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Casanare ───────────────────────────────────────────────────────────
    "AGUAZUL": MunicipioICA(
        nombre="AGUAZUL", departamento="CASANARE",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "MONTERREY": MunicipioICA(
        nombre="MONTERREY", departamento="CASANARE",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "TAURAMENA": MunicipioICA(
        nombre="TAURAMENA", departamento="CASANARE",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "VILLANUEVA": MunicipioICA(
        nombre="VILLANUEVA", departamento="CASANARE",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "YOPAL": MunicipioICA(
        nombre="YOPAL", departamento="CASANARE",
        periodicidad="TRIMESTRAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="Último día hábil de abril, julio, oct y enero",
    ),

    # ── Cesar ──────────────────────────────────────────────────────────────
    "JAGUA DE IBIRICO": MunicipioICA(
        nombre="JAGUA DE IBIRICO", departamento="CESAR",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "VALLEDUPAR": MunicipioICA(
        nombre="VALLEDUPAR", departamento="CESAR",
        periodicidad="TRIMESTRAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="Último día hábil de abril, julio, oct y enero",
    ),

    # ── Córdoba ────────────────────────────────────────────────────────────
    "BUENAVISTA": MunicipioICA(
        nombre="BUENAVISTA", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "CERETE": MunicipioICA(
        nombre="CERETE", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "CHINU": MunicipioICA(
        nombre="CHINU", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "COTORRA": MunicipioICA(
        nombre="COTORRA", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "LA APARTADA": MunicipioICA(
        nombre="LA APARTADA", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "LORICA": MunicipioICA(
        nombre="LORICA", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "LOS CORDOBAS": MunicipioICA(
        nombre="LOS CORDOBAS", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "MONTERIA": MunicipioICA(
        nombre="MONTERIA", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "PLANETA RICA": MunicipioICA(
        nombre="PLANETA RICA", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "SAN ANTERO": MunicipioICA(
        nombre="SAN ANTERO", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "SAN CARLOS": MunicipioICA(
        nombre="SAN CARLOS", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "SAN PELAYO": MunicipioICA(
        nombre="SAN PELAYO", departamento="CÓRDOBA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Cundinamarca ───────────────────────────────────────────────────────
    "PUERTO SALGAR": MunicipioICA(
        nombre="PUERTO SALGAR", departamento="CUNDINAMARCA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Bogotá D.C. ────────────────────────────────────────────────────────
    "BOGOTA": MunicipioICA(
        nombre="BOGOTA", departamento="BOGOTÁ D.C.",
        periodicidad="TRIMESTRAL", tarifa_por_mil=9.66,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="Último día hábil de abril, julio, oct y enero",
        verificado=True,
    ),

    # ── Huila ──────────────────────────────────────────────────────────────
    "AIPE": MunicipioICA(
        nombre="AIPE", departamento="HUILA",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "NEIVA": MunicipioICA(
        nombre="NEIVA", departamento="HUILA",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── La Guajira ─────────────────────────────────────────────────────────
    "FONSECA": MunicipioICA(
        nombre="FONSECA", departamento="LA GUAJIRA",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Magdalena ──────────────────────────────────────────────────────────
    "SANTA MARTA": MunicipioICA(
        nombre="SANTA MARTA", departamento="MAGDALENA",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
        verificado=True,  # Confirmado: declaración ICA 2025 presentada
    ),

    # ── Meta ───────────────────────────────────────────────────────────────
    "ACACIAS": MunicipioICA(
        nombre="ACACIAS", departamento="META",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "PUERTO GAITAN": MunicipioICA(
        nombre="PUERTO GAITAN", departamento="META",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "VILLAVICENCIO": MunicipioICA(
        nombre="VILLAVICENCIO", departamento="META",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Nariño ─────────────────────────────────────────────────────────────
    "TUMACO": MunicipioICA(
        nombre="TUMACO", departamento="NARIÑO",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Santander ──────────────────────────────────────────────────────────
    "BARBOSA": MunicipioICA(
        nombre="BARBOSA", departamento="SANTANDER",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "BARRANCABERMEJA": MunicipioICA(
        nombre="BARRANCABERMEJA", departamento="SANTANDER",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "BUCARAMANGA": MunicipioICA(
        nombre="BUCARAMANGA", departamento="SANTANDER",
        periodicidad="ANUAL", tarifa_por_mil=9.66,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "CIMITARRA": MunicipioICA(
        nombre="CIMITARRA", departamento="SANTANDER",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "FLORIAN": MunicipioICA(
        nombre="FLORIAN", departamento="SANTANDER",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "JESUS MARIA": MunicipioICA(
        nombre="JESUS MARIA", departamento="SANTANDER",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "LA BELLEZA": MunicipioICA(
        nombre="LA BELLEZA", departamento="SANTANDER",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "PUERTO OLAYA": MunicipioICA(
        nombre="PUERTO OLAYA", departamento="SANTANDER",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Sucre ──────────────────────────────────────────────────────────────
    "COVEÑAS": MunicipioICA(
        nombre="COVEÑAS", departamento="SUCRE",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "SAN MARCOS": MunicipioICA(
        nombre="SAN MARCOS", departamento="SUCRE",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "SAN ONOFRE": MunicipioICA(
        nombre="SAN ONOFRE", departamento="SUCRE",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "SINCELEJO": MunicipioICA(
        nombre="SINCELEJO", departamento="SUCRE",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "TOLU VIEJO": MunicipioICA(
        nombre="TOLU VIEJO", departamento="SUCRE",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Tolima ─────────────────────────────────────────────────────────────
    "GUAMO": MunicipioICA(
        nombre="GUAMO", departamento="TOLIMA",
        periodicidad="ANUAL", tarifa_por_mil=5.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=False,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),

    # ── Valle del Cauca ────────────────────────────────────────────────────
    "CALI": MunicipioICA(
        nombre="CALI", departamento="VALLE DEL CAUCA",
        periodicidad="ANUAL", tarifa_por_mil=9.66,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
    "YUMBO": MunicipioICA(
        nombre="YUMBO", departamento="VALLE DEL CAUCA",
        periodicidad="ANUAL", tarifa_por_mil=7.0,
        aplica_avisos_tableros=True, aplica_sobretasa_bomberil=True,
        fecha_limite_declaracion="31 de marzo del año siguiente",
    ),
}


# ---------------------------------------------------------------------------
# Funciones de consulta
# ---------------------------------------------------------------------------

def get_municipio(nombre: str) -> Optional[MunicipioICA]:
    """Retorna MunicipioICA por nombre (usa normalización automática)."""
    from src.processors.municipio_normalizer import normalizar_municipio
    nombre_norm = normalizar_municipio(nombre)
    return MUNICIPIOS_ICA.get(nombre_norm)


def todos_municipios_df() -> pd.DataFrame:
    """Retorna DataFrame con todos los municipios para mostrar en Streamlit."""
    filas = []
    for m in MUNICIPIOS_ICA.values():
        filas.append({
            "Municipio": m.nombre,
            "Departamento": m.departamento,
            "Periodicidad": m.periodicidad,
            "Tarifa ICA (‰)": m.tarifa_por_mil,
            "Avisos y Tableros (15%)": "Sí" if m.aplica_avisos_tableros else "No",
            "Sobretasa Bomberil": "Sí" if m.aplica_sobretasa_bomberil else "No",
            "Fecha Límite": m.fecha_limite_declaracion,
            "Tarifa Verificada": "✅" if m.verificado else "⚠️ Estimada",
        })
    return pd.DataFrame(filas).sort_values(["Departamento", "Municipio"]).reset_index(drop=True)


def municipios_trimestrales() -> list[str]:
    """Lista de municipios con declaración trimestral."""
    return [m.nombre for m in MUNICIPIOS_ICA.values() if m.periodicidad == "TRIMESTRAL"]


def municipios_anuales() -> list[str]:
    """Lista de municipios con declaración anual."""
    return [m.nombre for m in MUNICIPIOS_ICA.values() if m.periodicidad == "ANUAL"]

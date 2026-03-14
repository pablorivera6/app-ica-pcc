"""
Normaliza nombres de municipios inconsistentes encontrados en el Excel de Luz.
Basado en el análisis real del archivo CONCILIAICON INGRESOS MUNICIPIOS 2025.xlsx
que tiene 60 entradas de municipio con muchas variantes del mismo municipio.
"""

# Tabla de normalización basada en los municipios reales encontrados en el Excel.
# Formato: "VARIANTE_ENCONTRADA": "NOMBRE_NORMALIZADO"
MUNICIPIO_MAP = {
    # Acacias
    "ACACIAS": "ACACIAS",
    "ACACIAS - META": "ACACIAS",
    # Aguazul
    "AGUAZUL": "AGUAZUL",
    # Aipe
    "AIPE": "AIPE",
    "AIPE - HUILA": "AIPE",
    # Arboletes
    "ARBOLETES - ANTIOQUIA": "ARBOLETES",
    # Barbosa
    "BARBOSA": "BARBOSA",
    "BARBOSA ": "BARBOSA",
    # Barrancabermeja
    "BARRANCABERMEJA": "BARRANCABERMEJA",
    "BARRANCABERMEJA -  SANTANDER": "BARRANCABERMEJA",
    # Bogotá
    "BOGOTA": "BOGOTA",
    "BOGOTÁ": "BOGOTA",
    "BOGOTA D.C.": "BOGOTA",
    # Buenavista
    "BUENAVISTA - CORDOBA": "BUENAVISTA",
    # Cartagena
    "CARTAGENA-BOLIVAR": "CARTAGENA",
    "CARTAGENA": "CARTAGENA",
    # Caucasia
    "CAUCASIA - ANTIOQUIA": "CAUCASIA",
    # Cereté
    "CERETE - CORDOBA": "CERETE",
    # Chinú
    "CHINU - CORDOBA": "CHINU",
    # Cimitarra
    "CIMITARRA - SANT": "CIMITARRA",
    # Cotorra
    "COTORRA - CORDOBA": "COTORRA",
    # Coveñas
    "COVEÑAS - SUCRE": "COVEÑAS",
    # Florián
    "FLORIAN - SANTANDER": "FLORIAN",
    # Fonseca
    "FONSECA - LA GUAJIRA": "FONSECA",
    # Guamo
    "GUAMO - TOLIMA": "GUAMO",
    # Jagua de Ibiroco
    "JAGUA DE IBIRICO": "JAGUA DE IBIRICO",
    "JAGUA DE IBIRICO - CESAR": "JAGUA DE IBIRICO",
    # Jenesano
    "JENESANO - BOY": "JENESANO",
    # Jesús María
    "JESUS MARIA": "JESUS MARIA",
    # La Apartada
    "LA APARTADA - CORDOBA": "LA APARTADA",
    # La Belleza
    "LA BELLEZA": "LA BELLEZA",
    "LA BELLEZA - SANT": "LA BELLEZA",
    # Lorica
    "LORICA - CORDOBA": "LORICA",
    # Los Córdobas
    "LOS CORDOBAS - CORDOBA": "LOS CORDOBAS",
    # Miraflores
    "MIRAFLORES - BOY": "MIRAFLORES",
    "MIRAFLORES - BOYACA": "MIRAFLORES",
    # Montería
    "MONTERIA - CORDOBA": "MONTERIA",
    # Monterrey
    "MONTERREY - CASANARE": "MONTERREY",
    "MONTERREY-CASANARE": "MONTERREY",
    # Otanche
    "OTANCHE - BOYACA": "OTANCHE",
    # Páez
    "PAEZ - BOY": "PAEZ",
    # Planeta Rica
    "PLANETA RICA - CORDOBA": "PLANETA RICA",
    # Puerto Berrío
    "PUERTO BERRIO": "PUERTO BERRIO",
    # Puerto Boyacá
    "PUERTO BOYACA - BOY": "PUERTO BOYACA",
    # Puerto Gaitán
    "PUERTO GAITAN": "PUERTO GAITAN",
    # Puerto Olaya
    "PUERTO OLAYA - SANTANDER": "PUERTO OLAYA",
    # Puerto Salgar
    "PUERTO SALGAR": "PUERTO SALGAR",
    # Remedios
    "REMEDIOS - ANTOQUIA": "REMEDIOS",
    # San Antero
    "SAN ANTERO - CORDOBA": "SAN ANTERO",
    # San Carlos
    "SAN CARLOS - CORDOBA": "SAN CARLOS",
    # San Marcos
    "SAN MARCOS - SUCRE": "SAN MARCOS",
    # San Onofre
    "SAN ONOFRE - SUCRE": "SAN ONOFRE",
    # San Pelayo
    "SAN PELAYO - CORDOBA": "SAN PELAYO",
    # Santa Marta
    "SANTA MARTA - MAG": "SANTA MARTA",
    "SANTA MARTA": "SANTA MARTA",
    "SANTA MARTA, MAGDALENA": "SANTA MARTA",
    # Santa Rosa
    "SANTA ROSA (BOLIVAR)": "SANTA ROSA",
    # Segovia
    "SEGOVIA - ANTOIQUIA": "SEGOVIA",
    # Sincelejo
    "SINCELEJO": "SINCELEJO",
    "SINCELEJO ": "SINCELEJO",
    "SINCELO - SUCRE": "SINCELEJO",
    # Tauramena
    "TAURAMENA": "TAURAMENA",
    # Tolú Viejo
    "TOLU VIEJO": "TOLU VIEJO",
    "TOLU VIEJO ": "TOLU VIEJO",
    # Valledupar
    "VALLEDUPAR": "VALLEDUPAR",
    # Villanueva
    "VILLANUEVA  - CASANARE": "VILLANUEVA",
    # Villavicencio
    "VILLAVICENCIO": "VILLAVICENCIO",
    # Yopal
    "YOPAL - CASANARE": "YOPAL",
    "YOPAL": "YOPAL",
    # Yumbo
    "YUMBO (VALLE DEL CAUCA)": "YUMBO",
}


def normalizar_municipio(nombre: str) -> str:
    """
    Normaliza el nombre de un municipio a su forma canónica.
    Si no se encuentra en el mapa, retorna el nombre en mayúsculas y sin espacios extra.
    """
    if not nombre:
        return ""
    nombre_limpio = nombre.strip().upper()
    return MUNICIPIO_MAP.get(nombre_limpio, nombre_limpio)


def son_mismo_municipio(nombre1: str, nombre2: str) -> bool:
    """Compara dos nombres de municipio después de normalizarlos."""
    return normalizar_municipio(nombre1) == normalizar_municipio(nombre2)

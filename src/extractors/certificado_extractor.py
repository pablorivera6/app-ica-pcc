"""
Extractor de certificados de retención de ICA.

Los certificados NO tienen formato estándar — cada empresa emisora tiene su propio diseño.
Este módulo usa pdfplumber + regex para extraer campos clave.

Probado con: TERMOTECNICA Cert ReteIca BIM VI SANTA MARTA (1).pdf
TODO: Probar con más emisores (Ocensa, TGI, Ecopetrol, etc.) y agregar patrones.
"""
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional
import pdfplumber
from src.database.models import CertificadoReteICA


def extraer_certificado(ruta_pdf: str | Path) -> CertificadoReteICA:
    """
    Extrae los datos de un certificado de retención ICA desde un PDF.

    Args:
        ruta_pdf: Ruta al archivo PDF del certificado

    Returns:
        CertificadoReteICA con los datos extraídos
    """
    ruta = Path(ruta_pdf)
    cert = CertificadoReteICA(
        retenedor_nombre="",
        retenedor_nit="",
        archivo_origen=ruta.name
    )

    with pdfplumber.open(ruta) as pdf:
        texto_completo = ""
        for page in pdf.pages:
            texto_completo += (page.extract_text() or "") + "\n"

    cert = _parsear_texto(texto_completo, cert)
    return cert


def _parsear_texto(texto: str, cert: CertificadoReteICA) -> CertificadoReteICA:
    """Aplica patrones regex al texto extraído del PDF."""
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]

    # --- Retenedor: primera línea suele ser el nombre de la empresa ---
    if lineas:
        cert.retenedor_nombre = lineas[0]

    # --- NIT del retenedor ---
    for i, linea in enumerate(lineas[:5]):
        nit = _extraer_nit(linea)
        if nit and nit != cert.retenido_nit:
            cert.retenedor_nit = nit
            break

    # --- Ciudad donde se practicó la retención ---
    patron_ciudad_retencion = re.compile(
        r"ciudad donde se practic[oó] la retenci[oó]n[:\s]+(.+)", re.IGNORECASE
    )
    patron_ciudad_consignacion = re.compile(
        r"ciudad donde se consign[oó] la retenci[oó]n[:\s]+(.+)", re.IGNORECASE
    )
    for linea in lineas:
        m = patron_ciudad_retencion.search(linea)
        if m:
            cert.ciudad_retencion = m.group(1).strip()
        m = patron_ciudad_consignacion.search(linea)
        if m:
            cert.ciudad_consignacion = m.group(1).strip()

    # --- Período ---
    patron_periodo = re.compile(
        r"(\d{1,2}/\d{1,2}/\d{4})\s+al\s+(\d{1,2}/\d{1,2}/\d{4})", re.IGNORECASE
    )
    m = patron_periodo.search(texto)
    if m:
        cert.periodo_inicio = _parse_fecha(m.group(1))
        cert.periodo_fin = _parse_fecha(m.group(2))

    # --- Valores monetarios ---
    # Buscar tabla de valores: la última fila con $valores suele ser el total
    patron_valor = re.compile(r"\$([0-9,\.]+)")
    todos_valores = patron_valor.findall(texto)
    valores_numericos = [_parse_valor(v) for v in todos_valores if _parse_valor(v) > 0]

    # Buscar base gravable y valor retenido por posición en el texto
    patron_base_retenido = re.compile(
        r"\$0[,\.]0+\s+\$([0-9,\.]+)\s+\$([0-9,\.]+)"
    )
    m = patron_base_retenido.search(texto)
    if m:
        cert.base_gravable = _parse_valor(m.group(1))
        cert.valor_retenido = _parse_valor(m.group(2))

    # --- Tarifa ---
    patron_tarifa = re.compile(r"(\d+)\*1000")
    m = patron_tarifa.search(texto)
    if m:
        cert.tarifa_por_mil = float(m.group(1))

    # --- Fecha de expedición ---
    patron_fecha_exp = re.compile(
        r"fecha de expedici[oó]n[:\s]+(\d{1,2}/\d{1,2}/\d{4})", re.IGNORECASE
    )
    m = patron_fecha_exp.search(texto)
    if m:
        cert.fecha_expedicion = _parse_fecha(m.group(1))

    return cert


def _extraer_nit(texto: str) -> Optional[str]:
    """Extrae un NIT colombiano de un texto."""
    patron = re.compile(r"(\d{8,10})-?(\d)")
    m = patron.search(texto)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return None


def _parse_fecha(texto: str) -> Optional[date]:
    """Parsea fechas en formato dd/mm/yyyy o yyyy-mm-dd."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(texto.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_valor(texto: str) -> float:
    """Convierte string de valor monetario colombiano a float."""
    try:
        limpio = texto.replace(".", "").replace(",", ".").strip()
        return float(limpio)
    except (ValueError, AttributeError):
        return 0.0


def procesar_carpeta(carpeta: str | Path) -> list[CertificadoReteICA]:
    """
    Procesa todos los PDFs en una carpeta y retorna lista de certificados extraídos.
    """
    carpeta = Path(carpeta)
    resultados = []
    for pdf in sorted(carpeta.glob("*.pdf")):
        try:
            cert = extraer_certificado(pdf)
            resultados.append(cert)
            print(f"✅ {pdf.name} → {cert.retenedor_nombre} | {cert.ciudad_retencion} | ${cert.valor_retenido:,.0f}")
        except Exception as e:
            print(f"❌ {pdf.name} → Error: {e}")
    return resultados

"""
Extractor de certificados de retención de ICA.

Los certificados NO tienen formato estándar — cada empresa emisora tiene su propio diseño.

Estrategia (con fallback):
  1. Convierte el PDF a imagen (pdf2image)
  2. Envía la imagen a Claude Haiku via API → JSON estructurado
  3. Si falla (sin API key, error de red, etc.) → fallback a extractor regex (pdfplumber)

Requiere: ANTHROPIC_API_KEY en variables de entorno
"""
import base64
import io
import json
import os
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import pdfplumber
from src.database.models import CertificadoReteICA


# ---------------------------------------------------------------------------
# PRIORIDAD 1 — Extractor con Claude API
# ---------------------------------------------------------------------------

def _extraer_con_claude_api(ruta_pdf: str | Path) -> dict:
    """
    Convierte el PDF a imagen y envía a Claude Haiku para extracción estructurada.
    Retorna un dict con los campos del certificado.
    Lanza excepción si falla (para que el caller haga fallback).
    """
    import anthropic
    from pdf2image import convert_from_path

    ruta = Path(ruta_pdf)

    # 1. PDF → imagen (primera página, 200 dpi)
    imagenes = convert_from_path(str(ruta), dpi=200, first_page=1, last_page=1)
    if not imagenes:
        raise ValueError(f"No se pudo convertir el PDF a imagen: {ruta.name}")

    buf = io.BytesIO()
    imagenes[0].save(buf, format="PNG")
    img_b64 = base64.standard_b64encode(buf.getvalue()).decode("utf-8")

    # 2. Llamada a Claude Haiku
    client = anthropic.Anthropic()  # Usa ANTHROPIC_API_KEY del entorno

    prompt = (
        "Eres un asistente contable colombiano especializado en certificados de retención ICA.\n"
        "Analiza esta imagen de un certificado de retención ICA y extrae los siguientes campos.\n"
        "Retorna ÚNICAMENTE un objeto JSON válido, sin texto adicional ni bloques de código.\n\n"
        "Campos a extraer:\n"
        "{\n"
        '  "retenedor_nombre": "nombre completo de la empresa que practica la retención",\n'
        '  "retenedor_nit": "NIT con dígito de verificación formato XXXXXXXXXX-X",\n'
        '  "ciudad_retencion": "ciudad donde se practicó la retención (solo nombre ciudad)",\n'
        '  "periodo_inicio": "fecha inicio en formato DD/MM/YYYY o null",\n'
        '  "periodo_fin": "fecha fin en formato DD/MM/YYYY o null",\n'
        '  "base_gravable": 0,\n'
        '  "tarifa_por_mil": 0,\n'
        '  "valor_retenido": 0,\n'
        '  "fecha_expedicion": "fecha en formato DD/MM/YYYY o null"\n'
        "}\n\n"
        "Notas:\n"
        "- base_gravable y valor_retenido son enteros (sin puntos ni comas)\n"
        "- tarifa_por_mil es el número de la tarifa en por mil (ej: si dice 7‰ → 7)\n"
        "- Si un campo no está disponible en el documento, usa null"
    )

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )

    texto = response.content[0].text.strip()

    # Limpiar bloques markdown si vienen envueltos
    if texto.startswith("```"):
        texto = re.sub(r"```\w*\n?", "", texto).strip()

    return json.loads(texto)


def _dict_a_certificado(datos: dict, ruta: Path) -> CertificadoReteICA:
    """Convierte el dict JSON de Claude a CertificadoReteICA."""
    cert = CertificadoReteICA(
        retenedor_nombre=datos.get("retenedor_nombre") or "",
        retenedor_nit=datos.get("retenedor_nit") or "",
        archivo_origen=ruta.name,
        confianza_extraccion=0.95,  # Alta confianza cuando viene de Claude
    )
    cert.ciudad_retencion = datos.get("ciudad_retencion") or ""
    cert.base_gravable = float(datos.get("base_gravable") or 0)
    cert.tarifa_por_mil = float(datos.get("tarifa_por_mil") or 0)
    cert.valor_retenido = float(datos.get("valor_retenido") or 0)
    cert.periodo_inicio = _parse_fecha(datos.get("periodo_inicio"))
    cert.periodo_fin = _parse_fecha(datos.get("periodo_fin"))
    cert.fecha_expedicion = _parse_fecha(datos.get("fecha_expedicion"))
    return cert


# ---------------------------------------------------------------------------
# Función principal con fallback
# ---------------------------------------------------------------------------

def extraer_certificado(ruta_pdf: str | Path) -> CertificadoReteICA:
    """
    Extrae los datos de un certificado de retención ICA desde un PDF.

    Intenta primero con Claude API (alta precisión para formatos variables).
    Si falla o no hay API key, usa el extractor regex como fallback.

    Args:
        ruta_pdf: Ruta al archivo PDF del certificado

    Returns:
        CertificadoReteICA con los datos extraídos
    """
    ruta = Path(ruta_pdf)

    # Intentar con Claude API si hay API key disponible
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            datos = _extraer_con_claude_api(ruta)
            cert = _dict_a_certificado(datos, ruta)
            return cert
        except Exception as e:
            print(f"⚠️  Claude API falló para {ruta.name}: {e} — usando extractor regex")

    # Fallback: extractor regex con pdfplumber
    return _extraer_con_regex(ruta)


# ---------------------------------------------------------------------------
# FALLBACK — Extractor regex con pdfplumber
# ---------------------------------------------------------------------------

def _extraer_con_regex(ruta: Path) -> CertificadoReteICA:
    """Extractor original basado en pdfplumber + regex (fallback)."""
    cert = CertificadoReteICA(
        retenedor_nombre="",
        retenedor_nit="",
        archivo_origen=ruta.name,
        confianza_extraccion=0.6,  # Confianza menor — regex es frágil
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

    if lineas:
        cert.retenedor_nombre = lineas[0]

    for i, linea in enumerate(lineas[:5]):
        nit = _extraer_nit(linea)
        if nit and nit != cert.retenido_nit:
            cert.retenedor_nit = nit
            break

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

    patron_periodo = re.compile(
        r"(\d{1,2}/\d{1,2}/\d{4})\s+al\s+(\d{1,2}/\d{1,2}/\d{4})", re.IGNORECASE
    )
    m = patron_periodo.search(texto)
    if m:
        cert.periodo_inicio = _parse_fecha(m.group(1))
        cert.periodo_fin = _parse_fecha(m.group(2))

    patron_base_retenido = re.compile(
        r"\$0[,\.]0+\s+\$([0-9,\.]+)\s+\$([0-9,\.]+)"
    )
    m = patron_base_retenido.search(texto)
    if m:
        cert.base_gravable = _parse_valor(m.group(1))
        cert.valor_retenido = _parse_valor(m.group(2))

    patron_tarifa = re.compile(r"(\d+)\*1000")
    m = patron_tarifa.search(texto)
    if m:
        cert.tarifa_por_mil = float(m.group(1))

    patron_fecha_exp = re.compile(
        r"fecha de expedici[oó]n[:\s]+(\d{1,2}/\d{1,2}/\d{4})", re.IGNORECASE
    )
    m = patron_fecha_exp.search(texto)
    if m:
        cert.fecha_expedicion = _parse_fecha(m.group(1))

    return cert


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _extraer_nit(texto: str) -> Optional[str]:
    """Extrae un NIT colombiano de un texto."""
    patron = re.compile(r"(\d{8,10})-?(\d)")
    m = patron.search(texto)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return None


def _parse_fecha(texto: Optional[str]) -> Optional[date]:
    """Parsea fechas en formato dd/mm/yyyy o yyyy-mm-dd."""
    if not texto:
        return None
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


# ---------------------------------------------------------------------------
# Procesamiento por lote
# ---------------------------------------------------------------------------

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
            metodo = "🤖 API" if cert.confianza_extraccion >= 0.9 else "📝 regex"
            print(
                f"✅ {metodo} {pdf.name} → "
                f"{cert.retenedor_nombre} | {cert.ciudad_retencion} | "
                f"${cert.valor_retenido:,.0f}"
            )
        except Exception as e:
            print(f"❌ {pdf.name} → Error: {e}")
    return resultados

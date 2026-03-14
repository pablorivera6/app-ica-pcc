"""
Extractor de facturas SIGO.

TODO: Este módulo está pendiente de muestras reales de PDFs de facturas SIGO.
Por ahora lee datos desde el Excel de conciliación de Luz.

Una vez que Luz envíe muestras de facturas PDF, implementar extracción directa.
"""
import re
from datetime import datetime, date
from pathlib import Path
from typing import Optional
import pandas as pd
import pdfplumber
from src.database.models import FacturaSIGO
from src.processors.municipio_normalizer import normalizar_municipio


def leer_facturas_desde_excel(ruta_excel: str | Path, hoja: str = "INGRESOS MUNICIPIOS 2025") -> list[FacturaSIGO]:
    """
    Lee las facturas desde el Excel de conciliación de Luz.

    Estructura del Excel:
    - Filas 0-7: Encabezado de empresa (ignorar)
    - Fila 8 (índice): Headers de columnas
    - Fila 9+ (índice): Datos
    """
    df = pd.read_excel(ruta_excel, sheet_name=hoja, header=None)

    # Los headers están en la fila de índice 8
    headers = [str(h).strip() for h in df.iloc[8].tolist()]
    datos = df.iloc[9:].copy()
    datos.columns = headers
    datos = datos.dropna(subset=["Nombre cliente"])

    facturas = []
    for _, fila in datos.iterrows():
        try:
            factura = FacturaSIGO(
                numero_factura=str(fila.get("Comprobante", "")).strip(),
                fecha_elaboracion=_parse_fecha(fila.get("Fecha elaboración")),
                cliente_nombre=str(fila.get("Nombre cliente", "")).strip(),
                cliente_nit=str(fila.get("Identificación", "")).strip(),
                municipio=normalizar_municipio(str(fila.get("CIUDAD/ MUNICIPIO", ""))),
                subtotal=_parse_float(fila.get("SubTotal", 0)),
                iva=_parse_float(fila.get("Iva", 0)),
                total=_parse_float(fila.get("Total", 0)),
                concepto=str(fila.get("CONCEPTO", "SERVICIOS")).strip(),
                reteica=_parse_float(fila.get("RETEICA", 0)),
                tarifa=str(fila.get("TARIFA", "")).strip(),
                archivo_origen=str(ruta_excel),
            )
            facturas.append(factura)
        except Exception as e:
            print(f"⚠️  Error procesando fila {fila.get('Comprobante')}: {e}")

    return facturas


def extraer_factura_pdf(ruta_pdf: str | Path) -> FacturaSIGO:
    """
    Extrae datos de una factura SIGO desde PDF.
    TODO: Implementar cuando se reciban muestras de Luz.

    Campos a extraer del PDF de factura SIGO:
    - Número de factura
    - Fecha
    - NIT y nombre del cliente
    - Municipio del servicio
    - Subtotal, IVA, Total
    """
    raise NotImplementedError(
        "Pendiente de muestras de PDFs de facturas SIGO. "
        "Usar leer_facturas_desde_excel() por ahora."
    )


def _parse_fecha(valor) -> Optional[date]:
    if pd.isna(valor) if hasattr(pd, 'isna') else valor is None:
        return None
    if isinstance(valor, (datetime, date)):
        return valor.date() if isinstance(valor, datetime) else valor
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(str(valor).strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_float(valor) -> float:
    try:
        if pd.isna(valor):
            return 0.0
    except (TypeError, ValueError):
        pass
    try:
        return float(str(valor).replace(",", "").strip())
    except (ValueError, AttributeError):
        return 0.0

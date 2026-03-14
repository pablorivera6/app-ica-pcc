"""
Modelos de datos del sistema ICA PCC.
Usar dataclasses para representar las entidades principales.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class CertificadoReteICA:
    """
    Representa un certificado de retención de ICA emitido por un cliente.
    Extraído desde PDF.
    """
    # Retenedor (cliente que retiene)
    retenedor_nombre: str
    retenedor_nit: str

    # Retenido (siempre PCC)
    retenido_nombre: str = "PROTECCION CATODICA DE COLOMBIA"
    retenido_nit: str = "860068218"

    # Ubicación
    ciudad_retencion: str = ""
    ciudad_consignacion: str = ""

    # Valores
    base_gravable: float = 0.0
    tarifa_por_mil: float = 0.0
    valor_retenido: float = 0.0

    # Período
    periodo_inicio: Optional[date] = None
    periodo_fin: Optional[date] = None

    # Metadata
    fecha_expedicion: Optional[date] = None
    archivo_origen: str = ""
    confianza_extraccion: float = 1.0  # 0.0 a 1.0


@dataclass
class FacturaSIGO:
    """
    Representa una factura de venta generada en SIGO.
    Extraída desde PDF o desde el Excel de conciliación.
    """
    numero_factura: str
    fecha_elaboracion: Optional[date]
    cliente_nombre: str
    cliente_nit: str
    municipio: str
    subtotal: float
    iva: float
    total: float
    concepto: str = "SERVICIOS"
    reteica: float = 0.0
    tarifa: str = ""
    archivo_origen: str = ""


@dataclass
class ResultadoCruce:
    """
    Resultado del cruce entre una factura y un certificado de retención.
    """
    factura: Optional[FacturaSIGO]
    certificado: Optional[CertificadoReteICA]

    # Resultado
    estado: str = ""  # "COINCIDE", "NO_COINCIDE", "SIN_MATCH_FACTURA", "SIN_MATCH_CERT"
    municipio_factura: str = ""
    municipio_certificado: str = ""
    diferencia_valor: float = 0.0
    observacion: str = ""


@dataclass
class DeclaracionICA:
    """
    Borrador de declaración de ICA para un municipio y período.
    """
    municipio: str
    periodo: str  # "2025-ANUAL", "2025-T1", etc.
    anno_gravable: int = 2025

    # Base gravable
    total_ingresos_pais: float = 0.0
    ingresos_fuera_municipio: float = 0.0
    base_gravable_municipio: float = 0.0

    # Tarifa y liquidación
    tarifa_por_mil: float = 0.0
    impuesto_ica: float = 0.0
    avisos_tableros: float = 0.0
    sobretasa_bomberil: float = 0.0
    total_impuesto_cargo: float = 0.0

    # Descuentos
    retenciones_periodo: float = 0.0
    anticipo_anno_anterior: float = 0.0
    saldo_favor_anterior: float = 0.0

    # Resultado
    total_a_pagar: float = 0.0
    anticipo_siguiente: float = 0.0

    # Estado
    estado: str = "BORRADOR"  # BORRADOR, REVISADO, PRESENTADO, PAGADO

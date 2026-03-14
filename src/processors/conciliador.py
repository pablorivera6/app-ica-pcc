"""
Motor de conciliación: cruza facturas vs certificados de retención ICA.

Lógica:
1. Para cada certificado, busca la factura correspondiente por cliente + municipio + período
2. Compara municipio de factura vs municipio del certificado
3. Clasifica: COINCIDE / NO_COINCIDE / SIN_MATCH
4. Genera reporte de discrepancias para Luz
"""
from datetime import date
from typing import Optional
import pandas as pd
from src.database.models import FacturaSIGO, CertificadoReteICA, ResultadoCruce
from src.processors.municipio_normalizer import son_mismo_municipio, normalizar_municipio


# Mapa de NIT de cliente a nombre normalizado (para cruce)
# TODO: Completar con todos los clientes de PCC
NIT_A_NOMBRE = {
    "890903035": "TERMOTECNICA COINDUSTRIAL",
    "900155729": "OLEODUCTO CENTRAL",       # Ocensa
    "800058291": "TRANSPORTADORA DE GAS INTERNACIONAL",  # TGI
    "899999068": "ECOPETROL",
    "860032463": "PERENCO COLOMBIA",
}


def conciliar(
    facturas: list[FacturaSIGO],
    certificados: list[CertificadoReteICA]
) -> list[ResultadoCruce]:
    """
    Cruza listas de facturas y certificados.
    Retorna lista de ResultadoCruce con el estado de cada par.
    """
    resultados = []
    certificados_usados = set()

    for cert in certificados:
        factura_match = _buscar_factura(cert, facturas)

        if factura_match is None:
            resultados.append(ResultadoCruce(
                factura=None,
                certificado=cert,
                estado="SIN_MATCH_FACTURA",
                municipio_certificado=cert.ciudad_retencion,
                observacion=f"No se encontró factura para {cert.retenedor_nombre} en {cert.ciudad_retencion}"
            ))
        else:
            coincide = son_mismo_municipio(factura_match.municipio, cert.ciudad_retencion)
            diferencia = abs(factura_match.subtotal - cert.base_gravable)

            resultados.append(ResultadoCruce(
                factura=factura_match,
                certificado=cert,
                estado="COINCIDE" if coincide else "NO_COINCIDE",
                municipio_factura=factura_match.municipio,
                municipio_certificado=normalizar_municipio(cert.ciudad_retencion),
                diferencia_valor=diferencia,
                observacion="" if coincide else (
                    f"Municipio factura: {factura_match.municipio} | "
                    f"Municipio certificado: {cert.ciudad_retencion}"
                )
            ))
            certificados_usados.add(id(cert))

    # Facturas sin certificado
    facturas_con_reteica = [f for f in facturas if f.reteica > 0]
    for factura in facturas_con_reteica:
        if not _tiene_certificado(factura, certificados):
            resultados.append(ResultadoCruce(
                factura=factura,
                certificado=None,
                estado="SIN_MATCH_CERT",
                municipio_factura=factura.municipio,
                observacion=f"Factura {factura.numero_factura} tiene ReteICA pero no se encontró certificado"
            ))

    return resultados


def _buscar_factura(cert: CertificadoReteICA, facturas: list[FacturaSIGO]) -> Optional[FacturaSIGO]:
    """
    Busca la factura que corresponde a un certificado.
    Estrategia: cliente (por NIT o nombre aproximado) + período + valor similar.
    """
    nombre_retenedor = cert.retenedor_nombre.upper()
    nit_retenedor = cert.retenedor_nit.split("-")[0] if cert.retenedor_nit else ""

    candidatas = []
    for f in facturas:
        # Coincidencia por NIT
        if nit_retenedor and nit_retenedor in f.cliente_nit:
            candidatas.append(f)
            continue
        # Coincidencia por nombre parcial
        nombre_factura = f.cliente_nombre.upper()
        palabras_cert = set(nombre_retenedor.split())
        palabras_factura = set(nombre_factura.split())
        if len(palabras_cert & palabras_factura) >= 2:
            candidatas.append(f)

    if not candidatas:
        return None

    # Si hay varias candidatas, buscar la de valor más cercano
    if cert.base_gravable > 0:
        candidatas.sort(key=lambda f: abs(f.subtotal - cert.base_gravable))

    return candidatas[0]


def _tiene_certificado(factura: FacturaSIGO, certificados: list[CertificadoReteICA]) -> bool:
    """Verifica si una factura ya tiene un certificado asociado."""
    for cert in certificados:
        nit_retenedor = cert.retenedor_nit.split("-")[0] if cert.retenedor_nit else ""
        if nit_retenedor and nit_retenedor in factura.cliente_nit:
            if son_mismo_municipio(factura.municipio, cert.ciudad_retencion):
                return True
    return False


def generar_reporte_excel(resultados: list[ResultadoCruce], ruta_salida: str) -> None:
    """
    Genera un Excel con el reporte de conciliación para Luz.
    Columnas: Estado, Factura, Cliente, Municipio Factura, Municipio Certificado, Diferencia, Observación
    """
    filas = []
    for r in resultados:
        filas.append({
            "Estado": r.estado,
            "Factura": r.factura.numero_factura if r.factura else "",
            "Cliente": r.factura.cliente_nombre if r.factura else (
                r.certificado.retenedor_nombre if r.certificado else ""
            ),
            "Municipio Factura": r.municipio_factura,
            "Municipio Certificado": r.municipio_certificado,
            "Base Factura": r.factura.subtotal if r.factura else 0,
            "Base Certificado": r.certificado.base_gravable if r.certificado else 0,
            "Diferencia": r.diferencia_valor,
            "Observación": r.observacion,
        })

    df = pd.DataFrame(filas)

    # Ordenar: primero los NO_COINCIDE, luego SIN_MATCH, luego COINCIDE
    orden = {"NO_COINCIDE": 0, "SIN_MATCH_FACTURA": 1, "SIN_MATCH_CERT": 2, "COINCIDE": 3}
    df["_orden"] = df["Estado"].map(orden)
    df = df.sort_values("_orden").drop(columns=["_orden"])

    with pd.ExcelWriter(ruta_salida, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Conciliación")

    print(f"\n📊 Reporte guardado en: {ruta_salida}")
    _imprimir_resumen(resultados)


def _imprimir_resumen(resultados: list[ResultadoCruce]) -> None:
    total = len(resultados)
    coinciden = sum(1 for r in resultados if r.estado == "COINCIDE")
    no_coinciden = sum(1 for r in resultados if r.estado == "NO_COINCIDE")
    sin_cert = sum(1 for r in resultados if r.estado == "SIN_MATCH_CERT")
    sin_fact = sum(1 for r in resultados if r.estado == "SIN_MATCH_FACTURA")

    print(f"\n{'='*50}")
    print(f"RESUMEN DE CONCILIACIÓN")
    print(f"{'='*50}")
    print(f"✅ Coinciden:              {coinciden:>4} ({100*coinciden/total:.0f}%)")
    print(f"⚠️  No coinciden (municipio): {no_coinciden:>4} ({100*no_coinciden/total:.0f}%)")
    print(f"❌ Sin certificado:         {sin_cert:>4} ({100*sin_cert/total:.0f}%)")
    print(f"❌ Sin factura:             {sin_fact:>4} ({100*sin_fact/total:.0f}%)")
    print(f"{'='*50}")
    print(f"   TOTAL:                  {total:>4}")

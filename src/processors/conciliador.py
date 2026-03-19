"""
Motor de conciliación: cruza facturas vs certificados de retención ICA.

Lógica mejorada (PRIORIDAD 2):
1. Match por NIT (primario) + período (secundario) + valor EXACTO (sin tolerancias)
2. Si el valor no coincide exactamente → NO_COINCIDE
3. Detecta cuando un certificado cubre múltiples facturas (suma exacta)
4. Calcula porcentaje de confianza del match
5. Verifica coincidencia de municipio (COINCIDE vs NO_COINCIDE)
"""
from datetime import date
from typing import Optional
import pandas as pd
from src.database.models import FacturaSIGO, CertificadoReteICA, ResultadoCruce
from src.processors.municipio_normalizer import son_mismo_municipio, normalizar_municipio


# Mapa de NIT de cliente a nombre normalizado
NIT_A_NOMBRE = {
    "890903035": "TERMOTECNICA COINDUSTRIAL",
    "900155729": "OLEODUCTO CENTRAL",
    "800058291": "TRANSPORTADORA DE GAS INTERNACIONAL",
    "899999068": "ECOPETROL",
    "860032463": "PERENCO COLOMBIA",
}

# Tolerancia cero para valor exacto (puede ser 0 o un mínimo por redondeo bancario)
TOLERANCIA_VALOR = 0


def conciliar(
    facturas: list[FacturaSIGO],
    certificados: list[CertificadoReteICA],
) -> list[ResultadoCruce]:
    """
    Cruza listas de facturas y certificados.
    Retorna lista de ResultadoCruce con estado y confianza de cada par.
    """
    resultados: list[ResultadoCruce] = []
    facturas_usadas: set[int] = set()  # ids de facturas ya matcheadas

    for cert in certificados:
        resultado = _procesar_certificado(cert, facturas, facturas_usadas)
        if resultado is not None:
            # Marcar facturas usadas (simple + múltiples)
            if resultado.factura is not None:
                facturas_usadas.add(id(resultado.factura))
            for f in resultado.facturas_multiple:
                facturas_usadas.add(id(f))
        else:
            resultado = ResultadoCruce(
                factura=None,
                certificado=cert,
                estado="SIN_MATCH_FACTURA",
                municipio_certificado=normalizar_municipio(cert.ciudad_retencion),
                confianza=0.0,
                observacion=(
                    f"No se encontró factura para {cert.retenedor_nombre} "
                    f"en {cert.ciudad_retencion}"
                ),
            )
        resultados.append(resultado)

    # Facturas con ReteICA sin certificado
    for factura in facturas:
        if factura.reteica > 0 and id(factura) not in facturas_usadas:
            resultados.append(ResultadoCruce(
                factura=factura,
                certificado=None,
                estado="SIN_MATCH_CERT",
                municipio_factura=factura.municipio,
                confianza=0.0,
                observacion=(
                    f"Factura {factura.numero_factura} tiene ReteICA "
                    f"pero no se encontró certificado"
                ),
            ))

    return resultados


def _procesar_certificado(
    cert: CertificadoReteICA,
    facturas: list[FacturaSIGO],
    facturas_usadas: set[int],
) -> Optional[ResultadoCruce]:
    """
    Intenta hacer match de un certificado contra las facturas disponibles.
    Retorna ResultadoCruce o None si no hay candidatos.
    """
    nit_retenedor = cert.retenedor_nit.split("-")[0] if cert.retenedor_nit else ""
    nombre_upper = cert.retenedor_nombre.upper()

    # 1. Candidatas por NIT o nombre
    candidatas_nit: list[FacturaSIGO] = []
    candidatas_nombre: list[FacturaSIGO] = []

    for f in facturas:
        if id(f) in facturas_usadas:
            continue
        if nit_retenedor and nit_retenedor in f.cliente_nit:
            candidatas_nit.append(f)
        else:
            palabras_cert = set(nombre_upper.split())
            palabras_fact = set(f.cliente_nombre.upper().split())
            if len(palabras_cert & palabras_fact) >= 2:
                candidatas_nombre.append(f)

    candidatas = candidatas_nit if candidatas_nit else candidatas_nombre
    por_nit = bool(candidatas_nit)

    if not candidatas:
        return None

    # 2. Filtrar por período si el certificado tiene fechas
    candidatas_periodo = _filtrar_por_periodo(candidatas, cert)
    tiene_periodo = bool(cert.periodo_inicio or cert.periodo_fin)

    pool = candidatas_periodo if candidatas_periodo else candidatas

    # 3. Buscar match por valor EXACTO — una sola factura
    for f in pool:
        if abs(f.subtotal - cert.base_gravable) <= TOLERANCIA_VALOR:
            confianza = _calcular_confianza(
                por_nit=por_nit,
                periodo_ok=bool(candidatas_periodo),
                tiene_periodo=tiene_periodo,
                valor_ok=True,
                multi=False,
            )
            coincide_muni = son_mismo_municipio(f.municipio, cert.ciudad_retencion)
            estado = "COINCIDE" if coincide_muni else "NO_COINCIDE"
            obs = "" if coincide_muni else (
                f"Municipio factura: {f.municipio} | "
                f"Municipio certificado: {cert.ciudad_retencion}"
            )
            return ResultadoCruce(
                factura=f,
                certificado=cert,
                estado=estado,
                municipio_factura=normalizar_municipio(f.municipio),
                municipio_certificado=normalizar_municipio(cert.ciudad_retencion),
                diferencia_valor=0.0,
                confianza=confianza,
                observacion=obs,
            )

    # 4. Buscar match por valor EXACTO — múltiples facturas (suma)
    resultado_multi = _buscar_facturas_multiples(cert, pool, por_nit, tiene_periodo, bool(candidatas_periodo))
    if resultado_multi:
        return resultado_multi

    # 5. Sin match de valor → NO_COINCIDE (valor no coincide exactamente)
    mejor = pool[0]
    diferencia = abs(mejor.subtotal - cert.base_gravable)
    confianza = _calcular_confianza(
        por_nit=por_nit,
        periodo_ok=bool(candidatas_periodo),
        tiene_periodo=tiene_periodo,
        valor_ok=False,
        multi=False,
    )
    return ResultadoCruce(
        factura=mejor,
        certificado=cert,
        estado="NO_COINCIDE",
        municipio_factura=normalizar_municipio(mejor.municipio),
        municipio_certificado=normalizar_municipio(cert.ciudad_retencion),
        diferencia_valor=diferencia,
        confianza=confianza,
        observacion=(
            f"Valor no coincide: factura ${mejor.subtotal:,.0f} ≠ "
            f"base cert ${cert.base_gravable:,.0f} (diferencia ${diferencia:,.0f})"
        ),
    )


def _buscar_facturas_multiples(
    cert: CertificadoReteICA,
    candidatas: list[FacturaSIGO],
    por_nit: bool,
    tiene_periodo: bool,
    periodo_ok: bool,
) -> Optional[ResultadoCruce]:
    """
    Detecta si la base gravable del certificado corresponde a la suma de 2 ó más facturas.
    Prueba combinaciones de hasta 5 facturas.
    """
    from itertools import combinations

    base = cert.base_gravable
    if base <= 0:
        return None

    for r in range(2, min(6, len(candidatas) + 1)):
        for combo in combinations(candidatas, r):
            suma = sum(f.subtotal for f in combo)
            if abs(suma - base) <= TOLERANCIA_VALOR:
                confianza = _calcular_confianza(
                    por_nit=por_nit,
                    periodo_ok=periodo_ok,
                    tiene_periodo=tiene_periodo,
                    valor_ok=True,
                    multi=True,
                )
                municipios = set(normalizar_municipio(f.municipio) for f in combo)
                muni_cert = normalizar_municipio(cert.ciudad_retencion)
                todos_coinciden = all(son_mismo_municipio(f.municipio, cert.ciudad_retencion) for f in combo)
                estado = "COINCIDE" if todos_coinciden else "NO_COINCIDE"
                obs = (
                    f"Certificado cubre {r} facturas: "
                    f"{', '.join(f.numero_factura for f in combo)}"
                )
                if not todos_coinciden:
                    obs += f" | Municipios distintos: {municipios} vs cert: {muni_cert}"

                return ResultadoCruce(
                    factura=combo[0],
                    certificado=cert,
                    estado=estado,
                    municipio_factura=normalizar_municipio(combo[0].municipio),
                    municipio_certificado=muni_cert,
                    diferencia_valor=0.0,
                    confianza=confianza,
                    facturas_multiple=list(combo),
                    observacion=obs,
                )
    return None


def _filtrar_por_periodo(
    candidatas: list[FacturaSIGO],
    cert: CertificadoReteICA,
) -> list[FacturaSIGO]:
    """Retorna las facturas cuya fecha cae dentro del período del certificado."""
    if not cert.periodo_inicio and not cert.periodo_fin:
        return []
    resultado = []
    for f in candidatas:
        if not f.fecha_elaboracion:
            continue
        fecha = f.fecha_elaboracion
        inicio_ok = (not cert.periodo_inicio) or (fecha >= cert.periodo_inicio)
        fin_ok = (not cert.periodo_fin) or (fecha <= cert.periodo_fin)
        if inicio_ok and fin_ok:
            resultado.append(f)
    return resultado


def _calcular_confianza(
    por_nit: bool,
    periodo_ok: bool,
    tiene_periodo: bool,
    valor_ok: bool,
    multi: bool,
) -> float:
    """
    Calcula porcentaje de confianza del match (0–100).

    Criterios:
      NIT exacto             → 40 pts
      Nombre parcial (no NIT)→ 20 pts
      Período coincide       → 30 pts (solo si el cert tiene fechas)
      Valor exacto (1 fact.) → 30 pts
      Valor exacto (multi)   → 20 pts (menos confianza por ser suma)
    """
    puntos = 0.0
    puntos += 40.0 if por_nit else 20.0
    if tiene_periodo:
        puntos += 30.0 if periodo_ok else 0.0
    else:
        puntos += 15.0  # sin período en cert, puntaje parcial
    if valor_ok:
        puntos += 20.0 if multi else 30.0

    return round(min(puntos, 100.0), 1)


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------

def generar_reporte_excel(resultados: list[ResultadoCruce], ruta_salida: str) -> None:
    """
    Genera un Excel con el reporte de conciliación para Luz.
    """
    filas = []
    for r in resultados:
        n_facturas = len(r.facturas_multiple) if r.facturas_multiple else (1 if r.factura else 0)
        filas.append({
            "Estado": r.estado,
            "Confianza %": f"{r.confianza:.0f}%",
            "Comprobante(s)": (
                ", ".join(f.numero_factura for f in r.facturas_multiple)
                if r.facturas_multiple
                else (r.factura.numero_factura if r.factura else "")
            ),
            "# Facturas": n_facturas,
            "Cliente / Retenedor": (
                r.factura.cliente_nombre if r.factura
                else (r.certificado.retenedor_nombre if r.certificado else "")
            ),
            "NIT": (
                r.factura.cliente_nit if r.factura
                else (r.certificado.retenedor_nit if r.certificado else "")
            ),
            "Municipio Factura": r.municipio_factura,
            "Municipio Certificado": r.municipio_certificado,
            "Base Factura": (
                sum(f.subtotal for f in r.facturas_multiple)
                if r.facturas_multiple
                else (r.factura.subtotal if r.factura else 0)
            ),
            "Base Certificado": r.certificado.base_gravable if r.certificado else 0,
            "Diferencia": r.diferencia_valor,
            "Observación": r.observacion,
        })

    df = pd.DataFrame(filas)

    orden = {"NO_COINCIDE": 0, "SIN_MATCH_FACTURA": 1, "SIN_MATCH_CERT": 2, "COINCIDE": 3}
    df["_orden"] = df["Estado"].map(orden)
    df = df.sort_values("_orden").drop(columns=["_orden"])

    with pd.ExcelWriter(ruta_salida, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Conciliación")

    print(f"\n📊 Reporte guardado en: {ruta_salida}")
    _imprimir_resumen(resultados)


def _imprimir_resumen(resultados: list[ResultadoCruce]) -> None:
    total = len(resultados)
    if total == 0:
        return
    coinciden    = sum(1 for r in resultados if r.estado == "COINCIDE")
    no_coinciden = sum(1 for r in resultados if r.estado == "NO_COINCIDE")
    sin_cert     = sum(1 for r in resultados if r.estado == "SIN_MATCH_CERT")
    sin_fact     = sum(1 for r in resultados if r.estado == "SIN_MATCH_FACTURA")
    confianza_avg = sum(r.confianza for r in resultados) / total

    print(f"\n{'='*52}")
    print(f"RESUMEN DE CONCILIACIÓN")
    print(f"{'='*52}")
    print(f"✅ Coinciden:                {coinciden:>4} ({100*coinciden/total:.0f}%)")
    print(f"⚠️  No coinciden:             {no_coinciden:>4} ({100*no_coinciden/total:.0f}%)")
    print(f"❌ Sin certificado:           {sin_cert:>4} ({100*sin_cert/total:.0f}%)")
    print(f"❌ Sin factura:               {sin_fact:>4} ({100*sin_fact/total:.0f}%)")
    print(f"{'='*52}")
    print(f"   TOTAL:                     {total:>4}")
    print(f"   Confianza promedio:       {confianza_avg:.0f}%")

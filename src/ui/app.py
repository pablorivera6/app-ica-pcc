"""
Interfaz Streamlit — Automatización ICA Municipal
PCC Integrity

Flujo:
  1. Cargar certificados PDF  → extrae datos con certificado_extractor
  2. Cargar Excel de facturas → lee con factura_extractor
  3. Ejecutar conciliación    → cruza ambos y genera reporte Excel
"""
import sys
import io
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

# Asegurar que el root del proyecto esté en sys.path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.extractors.certificado_extractor import extraer_certificado
from src.extractors.factura_extractor import leer_facturas_desde_excel
from src.processors.conciliador import conciliar, generar_reporte_excel
from src.database.models import CertificadoReteICA, FacturaSIGO, ResultadoCruce

# ---------------------------------------------------------------------------
# Configuración de página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ICA Municipal — PCC Integrity",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Estilos mínimos
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stMetric label { font-size: 0.85rem; }
    .estado-COINCIDE     { color: #1e7e34; font-weight: 600; }
    .estado-NO_COINCIDE  { color: #c0392b; font-weight: 600; }
    .estado-SIN_MATCH_CERT   { color: #e67e22; font-weight: 600; }
    .estado-SIN_MATCH_FACTURA { color: #8e44ad; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — branding y estado de sesión
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://img.shields.io/badge/PCC_Integrity-ICA_Municipal-005A9C?style=for-the-badge",
        use_container_width=True,
    )
    st.markdown("### Estado de sesión")

    cert_count = len(st.session_state.get("certificados", []))
    fact_count = len(st.session_state.get("facturas", []))
    cruce_count = len(st.session_state.get("resultados", []))

    st.metric("Certificados cargados", cert_count)
    st.metric("Facturas cargadas", fact_count)
    st.metric("Registros conciliados", cruce_count)

    if cert_count > 0 or fact_count > 0:
        st.divider()
        if st.button("🗑️ Limpiar sesión", use_container_width=True):
            for key in ["certificados", "facturas", "resultados"]:
                st.session_state.pop(key, None)
            st.rerun()

    st.divider()
    st.caption("Responsable: Pablo Rivera\nÁrea: Contabilidad — PCC\nAño gravable: 2025")

# ---------------------------------------------------------------------------
# Título principal
# ---------------------------------------------------------------------------
st.title("🏛️ Automatización ICA Municipal")
st.markdown("**Protección Catódica de Colombia S.A.S. — NIT 860068218-1**")
st.divider()

# ---------------------------------------------------------------------------
# Pestañas
# ---------------------------------------------------------------------------
tab_cert, tab_fact, tab_cruce, tab_ayuda = st.tabs(
    ["📄 Certificados ReteICA", "📊 Facturas SIGO", "🔄 Conciliación", "❓ Ayuda"]
)

# ===========================================================================
# PESTAÑA 1 — Certificados ReteICA
# ===========================================================================
with tab_cert:
    st.header("Cargar certificados de retención ICA")
    st.markdown(
        "Sube uno o más PDFs de certificados. "
        "El extractor identifica automáticamente retenedor, ciudad, período y valores."
    )

    archivos = st.file_uploader(
        "Selecciona PDFs de certificados",
        type=["pdf"],
        accept_multiple_files=True,
        key="upload_certs",
    )

    if archivos:
        if st.button("⚙️ Extraer datos de certificados", type="primary"):
            certificados: list[CertificadoReteICA] = []
            errores: list[str] = []

            progreso = st.progress(0, text="Procesando...")
            for i, archivo in enumerate(archivos):
                progreso.progress((i + 1) / len(archivos), text=f"Procesando {archivo.name}…")
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(archivo.read())
                    tmp_path = tmp.name
                try:
                    cert = extraer_certificado(tmp_path)
                    cert.archivo_origen = archivo.name
                    certificados.append(cert)
                except Exception as e:
                    errores.append(f"{archivo.name}: {e}")
            progreso.empty()

            st.session_state["certificados"] = certificados

            if errores:
                for err in errores:
                    st.warning(f"⚠️ {err}")
            st.success(f"✅ {len(certificados)} certificado(s) procesado(s) correctamente.")

    certificados_sesion: list[CertificadoReteICA] = st.session_state.get("certificados", [])

    if certificados_sesion:
        st.subheader(f"Resultados — {len(certificados_sesion)} certificado(s)")

        filas = []
        for c in certificados_sesion:
            filas.append({
                "Archivo": c.archivo_origen,
                "Retenedor": c.retenedor_nombre,
                "NIT Retenedor": c.retenedor_nit,
                "Ciudad Retención": c.ciudad_retencion,
                "Período Inicio": str(c.periodo_inicio) if c.periodo_inicio else "",
                "Período Fin": str(c.periodo_fin) if c.periodo_fin else "",
                "Base Gravable": c.base_gravable,
                "Tarifa ‰": c.tarifa_por_mil,
                "Valor Retenido": c.valor_retenido,
                "Fecha Expedición": str(c.fecha_expedicion) if c.fecha_expedicion else "",
            })

        df_cert = pd.DataFrame(filas)
        st.dataframe(
            df_cert.style.format({
                "Base Gravable": "${:,.0f}",
                "Valor Retenido": "${:,.0f}",
                "Tarifa ‰": "{:.0f}‰",
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Resumen
        col1, col2, col3 = st.columns(3)
        col1.metric("Total base gravable", f"${df_cert['Base Gravable'].sum():,.0f}")
        col2.metric("Total valor retenido", f"${df_cert['Valor Retenido'].sum():,.0f}")
        col3.metric("Municipios distintos", df_cert["Ciudad Retención"].nunique())

        # Descarga
        buf = io.BytesIO()
        df_cert.to_excel(buf, index=False)
        st.download_button(
            "⬇️ Descargar certificados como Excel",
            data=buf.getvalue(),
            file_name="certificados_reteica.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ===========================================================================
# PESTAÑA 2 — Facturas SIGO
# ===========================================================================
with tab_fact:
    st.header("Cargar Excel de facturas SIGO")
    st.markdown(
        "Sube el archivo **`CONCILIAICON INGRESOS MUNICIPIOS 2025.xlsx`** "
        "(o cualquier Excel con la misma estructura del área de Contabilidad)."
    )

    archivo_excel = st.file_uploader(
        "Selecciona el Excel de conciliación",
        type=["xlsx", "xls"],
        key="upload_excel",
    )

    hoja = st.text_input("Nombre de la hoja", value="INGRESOS MUNICIPIOS 2025")

    if archivo_excel:
        if st.button("⚙️ Cargar facturas", type="primary"):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(archivo_excel.read())
                tmp_path = tmp.name
            try:
                with st.spinner("Leyendo facturas…"):
                    facturas = leer_facturas_desde_excel(tmp_path, hoja=hoja)
                st.session_state["facturas"] = facturas
                st.success(f"✅ {len(facturas)} facturas cargadas correctamente.")
            except Exception as e:
                st.error(f"❌ Error al leer el Excel: {e}")

    facturas_sesion: list[FacturaSIGO] = st.session_state.get("facturas", [])

    if facturas_sesion:
        st.subheader(f"Resultados — {len(facturas_sesion)} factura(s)")

        filas = []
        for f in facturas_sesion:
            filas.append({
                "Comprobante": f.numero_factura,
                "Fecha": str(f.fecha_elaboracion) if f.fecha_elaboracion else "",
                "Cliente": f.cliente_nombre,
                "NIT": f.cliente_nit,
                "Municipio": f.municipio,
                "Subtotal": f.subtotal,
                "IVA": f.iva,
                "Total": f.total,
                "ReteICA": f.reteica,
                "Tarifa": f.tarifa,
            })

        df_fact = pd.DataFrame(filas)

        # Filtros rápidos
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_cliente = st.selectbox(
                "Filtrar por cliente",
                ["Todos"] + sorted(df_fact["Cliente"].unique().tolist()),
            )
        with col_f2:
            filtro_muni = st.selectbox(
                "Filtrar por municipio",
                ["Todos"] + sorted(df_fact["Municipio"].unique().tolist()),
            )

        df_filtrado = df_fact.copy()
        if filtro_cliente != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Cliente"] == filtro_cliente]
        if filtro_muni != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Municipio"] == filtro_muni]

        st.dataframe(
            df_filtrado.style.format({
                "Subtotal": "${:,.0f}",
                "IVA": "${:,.0f}",
                "Total": "${:,.0f}",
                "ReteICA": "${:,.0f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total subtotal", f"${df_filtrado['Subtotal'].sum():,.0f}")
        col2.metric("Total ReteICA", f"${df_filtrado['ReteICA'].sum():,.0f}")
        col3.metric("Clientes distintos", df_filtrado["Cliente"].nunique())
        col4.metric("Municipios distintos", df_filtrado["Municipio"].nunique())

        buf = io.BytesIO()
        df_filtrado.to_excel(buf, index=False)
        st.download_button(
            "⬇️ Descargar facturas filtradas como Excel",
            data=buf.getvalue(),
            file_name="facturas_sigo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ===========================================================================
# PESTAÑA 3 — Conciliación
# ===========================================================================
with tab_cruce:
    st.header("Conciliación Facturas ↔ Certificados")

    certificados_ok = st.session_state.get("certificados", [])
    facturas_ok = st.session_state.get("facturas", [])

    if not certificados_ok and not facturas_ok:
        st.info("Carga primero los certificados y/o las facturas en las pestañas anteriores.")
    else:
        col_estado1, col_estado2 = st.columns(2)
        col_estado1.metric(
            "Certificados listos",
            len(certificados_ok),
            delta="✅ Cargados" if certificados_ok else None,
        )
        col_estado2.metric(
            "Facturas listas",
            len(facturas_ok),
            delta="✅ Cargadas" if facturas_ok else None,
        )

        if not certificados_ok:
            st.warning("⚠️ No hay certificados cargados — el cruce detectará facturas sin certificado.")
        if not facturas_ok:
            st.warning("⚠️ No hay facturas cargadas — el cruce detectará certificados sin factura.")

        if st.button("🔄 Ejecutar conciliación", type="primary", disabled=(not certificados_ok and not facturas_ok)):
            with st.spinner("Cruzando datos…"):
                resultados = conciliar(facturas_ok, certificados_ok)
            st.session_state["resultados"] = resultados
            st.success(f"✅ Conciliación completada — {len(resultados)} registro(s).")

    resultados_sesion: list[ResultadoCruce] = st.session_state.get("resultados", [])

    if resultados_sesion:
        # Métricas resumen
        total = len(resultados_sesion)
        coinciden    = sum(1 for r in resultados_sesion if r.estado == "COINCIDE")
        no_coinciden = sum(1 for r in resultados_sesion if r.estado == "NO_COINCIDE")
        sin_cert     = sum(1 for r in resultados_sesion if r.estado == "SIN_MATCH_CERT")
        sin_fact     = sum(1 for r in resultados_sesion if r.estado == "SIN_MATCH_FACTURA")

        st.subheader("Resumen")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("✅ Coinciden",        f"{coinciden}",    f"{100*coinciden/total:.0f}%")
        c2.metric("⚠️ No coinciden",     f"{no_coinciden}", f"{100*no_coinciden/total:.0f}%")
        c3.metric("❌ Sin certificado",  f"{sin_cert}",     f"{100*sin_cert/total:.0f}%")
        c4.metric("❌ Sin factura",      f"{sin_fact}",     f"{100*sin_fact/total:.0f}%")

        # Tabla de resultados
        st.subheader("Detalle")

        filtro_estado = st.multiselect(
            "Filtrar por estado",
            options=["COINCIDE", "NO_COINCIDE", "SIN_MATCH_CERT", "SIN_MATCH_FACTURA"],
            default=["NO_COINCIDE", "SIN_MATCH_CERT", "SIN_MATCH_FACTURA"],
        )

        filas_cruce = []
        for r in resultados_sesion:
            filas_cruce.append({
                "Estado": r.estado,
                "Comprobante": r.factura.numero_factura if r.factura else "",
                "Cliente / Retenedor": (
                    r.factura.cliente_nombre if r.factura
                    else (r.certificado.retenedor_nombre if r.certificado else "")
                ),
                "Municipio Factura": r.municipio_factura,
                "Municipio Certificado": r.municipio_certificado,
                "Base Factura": r.factura.subtotal if r.factura else 0,
                "Base Certificado": r.certificado.base_gravable if r.certificado else 0,
                "Diferencia": r.diferencia_valor,
                "Observación": r.observacion,
            })

        df_cruce = pd.DataFrame(filas_cruce)

        if filtro_estado:
            df_cruce_filtrado = df_cruce[df_cruce["Estado"].isin(filtro_estado)]
        else:
            df_cruce_filtrado = df_cruce

        # Colorear columna Estado
        COLORES_ESTADO = {
            "COINCIDE":             "background-color: #d4edda; color: #155724;",
            "NO_COINCIDE":          "background-color: #f8d7da; color: #721c24;",
            "SIN_MATCH_CERT":       "background-color: #fff3cd; color: #856404;",
            "SIN_MATCH_FACTURA":    "background-color: #e8d5f5; color: #6f42c1;",
        }

        def colorear_estado(val):
            return COLORES_ESTADO.get(val, "")

        st.dataframe(
            df_cruce_filtrado.style
                .applymap(colorear_estado, subset=["Estado"])
                .format({
                    "Base Factura":      "${:,.0f}",
                    "Base Certificado":  "${:,.0f}",
                    "Diferencia":        "${:,.0f}",
                }),
            use_container_width=True,
            hide_index=True,
            height=420,
        )

        # Descarga del reporte
        st.divider()
        st.subheader("Exportar reporte")

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_out:
            tmp_out_path = tmp_out.name

        generar_reporte_excel(resultados_sesion, tmp_out_path)

        with open(tmp_out_path, "rb") as f:
            st.download_button(
                "⬇️ Descargar reporte de conciliación (Excel)",
                data=f.read(),
                file_name="reporte_conciliacion_ica.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )

# ===========================================================================
# PESTAÑA 4 — Ayuda
# ===========================================================================
with tab_ayuda:
    st.header("Guía de uso")

    st.markdown("""
### Flujo recomendado

1. **Pestaña "Certificados ReteICA"**
   - Sube los PDFs de certificados que envían los clientes (Termotécnica, Ocensa, TGI, etc.)
   - Haz clic en *Extraer datos* y revisa que los campos sean correctos
   - Descarga el Excel si necesitas verificar manualmente

2. **Pestaña "Facturas SIGO"**
   - Sube el archivo `CONCILIAICON INGRESOS MUNICIPIOS 2025.xlsx`
   - La hoja por defecto es `INGRESOS MUNICIPIOS 2025` — cámbiala si es necesario
   - Usa los filtros para explorar por cliente o municipio

3. **Pestaña "Conciliación"**
   - Con certificados y facturas cargados, ejecuta la conciliación
   - Revisa primero los registros **NO_COINCIDE** (municipio factura ≠ municipio certificado)
   - Descarga el Excel para revisión en Contabilidad

---

### Estados de conciliación

| Estado | Significado |
|--------|-------------|
| ✅ COINCIDE | El municipio de la factura coincide con el del certificado |
| ⚠️ NO_COINCIDE | Los municipios no coinciden — revisar y corregir en SIGO |
| ❌ SIN_MATCH_CERT | La factura tiene ReteICA pero no se encontró certificado |
| ❌ SIN_MATCH_FACTURA | Existe un certificado pero no se encontró la factura correspondiente |

---

### Municipios con declaración trimestral

- **Bogotá** (D.C.)
- **Yopal** (Casanare)
- **Valledupar** (Cesar)

Todos los demás municipios son **anuales**.

---

### Contacto técnico
Para reportar errores o solicitar mejoras: **Pablo Rivera** — Área de Sistemas / Contabilidad PCC Integrity
    """)

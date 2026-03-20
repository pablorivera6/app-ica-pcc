"""
Interfaz Streamlit — Automatización ICA Municipal
PCC Integrity

Pestañas:
  1. Certificados ReteICA  — extrae datos de PDFs con Claude API
  2. Facturas SIGO         — carga Excel de conciliación
  3. Conciliación          — cruza ambos y genera reporte
  4. Municipios            — tabla maestra con tarifas ICA
  5. Declaraciones         — calcula y exporta borrador ICA
  6. Ayuda
"""
import io
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.extractors.certificado_extractor import extraer_certificado
from src.extractors.factura_extractor import leer_facturas_desde_excel
from src.processors.conciliador import conciliar, generar_reporte_excel
from src.database.models import CertificadoReteICA, FacturaSIGO, ResultadoCruce
from src.database.municipios_master import (
    get_municipio, todos_municipios_df, MUNICIPIOS_ICA,
    municipios_trimestrales, municipios_anuales,
)

# ---------------------------------------------------------------------------
# Configuración de página — modo claro
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ICA Municipal — PCC Integrity",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .stMetric label { font-size: 0.9rem; color: #555; }
    .stMetric [data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 700; }
    .badge-COINCIDE     { background:#d4edda; color:#155724; padding:2px 8px;
                          border-radius:4px; font-weight:600; font-size:0.85rem; }
    .badge-NO_COINCIDE  { background:#f8d7da; color:#721c24; padding:2px 8px;
                          border-radius:4px; font-weight:600; font-size:0.85rem; }
    .badge-SIN_MATCH_CERT   { background:#fff3cd; color:#856404; padding:2px 8px;
                              border-radius:4px; font-weight:600; font-size:0.85rem; }
    .badge-SIN_MATCH_FACTURA { background:#e8d5f5; color:#6f42c1; padding:2px 8px;
                               border-radius:4px; font-weight:600; font-size:0.85rem; }
    .alerta-error { background:#fff3cd; border-left:4px solid #ffc107;
                    padding:12px; border-radius:4px; margin:8px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🏛️ ICA Municipal")
    st.markdown("**PCC Integrity**")
    st.divider()

    cert_count  = len(st.session_state.get("certificados", []))
    fact_count  = len(st.session_state.get("facturas", []))
    cruce_count = len(st.session_state.get("resultados", []))

    st.markdown("### Estado de sesión")
    st.metric("Certificados", cert_count)
    st.metric("Facturas", fact_count)
    st.metric("Conciliados", cruce_count)

    if cert_count > 0 or fact_count > 0:
        st.divider()
        if st.button("🗑️ Limpiar sesión", use_container_width=True):
            for key in ["certificados", "facturas", "resultados"]:
                st.session_state.pop(key, None)
            st.rerun()

    st.divider()
    st.caption("Responsable: Pablo Rivera\nÁrea: Contabilidad — PCC\nAño gravable: 2025")

# ---------------------------------------------------------------------------
# Título
# ---------------------------------------------------------------------------
st.title("🏛️ Automatización ICA Municipal")
st.markdown("**Protección Catódica de Colombia S.A.S. — NIT 860068218-1**")
st.divider()

# ---------------------------------------------------------------------------
# Pestañas
# ---------------------------------------------------------------------------
tab_cert, tab_fact, tab_cruce, tab_munis, tab_decl, tab_ayuda = st.tabs([
    "📄 Certificados ReteICA",
    "📊 Facturas SIGO",
    "🔄 Conciliación",
    "🗺️ Municipios",
    "📋 Declaraciones",
    "❓ Ayuda",
])

# ===========================================================================
# PESTAÑA 1 — Certificados ReteICA
# ===========================================================================
with tab_cert:
    st.header("Cargar certificados de retención ICA")
    st.markdown(
        "Sube uno o más PDFs de certificados. "
        "El extractor usa **Claude API** para identificar automáticamente "
        "retenedor, ciudad, período y valores (fallback a regex si no hay conexión)."
    )

    # ── Diagnóstico de API key ────────────────────────────────────────────
    with st.expander("🔍 Diagnóstico — estado de la API key", expanded=True):
        import os as _os

        # 1. st.secrets
        try:
            key_secrets = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception as _e:
            key_secrets = ""
            st.caption(f"st.secrets no disponible: {_e}")

        # 2. os.environ
        key_env = _os.environ.get("ANTHROPIC_API_KEY", "")

        def _mask(k: str) -> str:
            return f"{k[:8]}…{k[-4:]}" if len(k) > 12 else ("(vacía)" if not k else k)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if key_secrets:
                st.success(f"✅ **st.secrets** → `{_mask(key_secrets)}`")
            else:
                st.error("❌ **st.secrets** → no encontrada")
        with col_d2:
            if key_env:
                st.success(f"✅ **os.environ** → `{_mask(key_env)}`")
            else:
                st.error("❌ **os.environ** → no encontrada")

        key_activa = key_secrets or key_env
        if key_activa:
            st.info(f"🤖 Se usará **Claude API** (`{_mask(key_activa)}`)")
        else:
            st.warning(
                "⚠️ **No se detectó ninguna API key.** "
                "El extractor usará regex como fallback.\n\n"
                "**En Streamlit Cloud:** Ve a *Settings → Secrets* y agrega:\n"
                "```toml\nANTHROPIC_API_KEY = \"sk-ant-...\"\n```\n"
                "**En local:** Ejecuta `export ANTHROPIC_API_KEY=sk-ant-...` antes de iniciar la app."
            )

        # ── Botón de prueba directa de la API ────────────────────────────
        if key_activa and st.button("🧪 Probar conexión con Claude API"):
            try:
                import anthropic as _anthropic
                _client = _anthropic.Anthropic(api_key=key_activa)
                _resp = _client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=20,
                    messages=[{"role": "user", "content": "Responde solo: OK"}],
                )
                st.success(f"✅ **API funciona correctamente.** Respuesta: `{_resp.content[0].text.strip()}`")
            except Exception as _api_err:
                st.error(
                    f"❌ **Error de Claude API:**\n\n"
                    f"`{type(_api_err).__name__}: {_api_err}`\n\n"
                    "Esto explica por qué el extractor cae a Regex."
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

            progreso = st.progress(0, text="Iniciando extracción…")
            for i, archivo in enumerate(archivos):
                pct = (i + 1) / len(archivos)
                progreso.progress(pct, text=f"Procesando {i+1}/{len(archivos)}: {archivo.name}")
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(archivo.read())
                    tmp_path = tmp.name
                try:
                    cert = extraer_certificado(tmp_path)
                    cert.archivo_origen = archivo.name
                    certificados.append(cert)
                except Exception as e:
                    errores.append(f"**{archivo.name}** — `{type(e).__name__}: {e}`")
            progreso.empty()

            st.session_state["certificados"] = certificados

            if errores:
                st.markdown(
                    '<div class="alerta-error">'
                    '<b>⚠️ Algunos archivos no pudieron procesarse:</b><br>' +
                    "<br>".join(f"• {e}" for e in errores) +
                    "<br><i>Verifique que el archivo sea un PDF válido y legible.</i>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            if certificados:
                st.success(f"✅ {len(certificados)} certificado(s) procesado(s) correctamente.")

    certificados_sesion: list[CertificadoReteICA] = st.session_state.get("certificados", [])

    if certificados_sesion:
        st.subheader(f"Resultados — {len(certificados_sesion)} certificado(s)")

        filas = []
        for c in certificados_sesion:
            metodo = "🤖 Claude API" if c.confianza_extraccion >= 0.9 else "📝 Regex"
            filas.append({
                "Archivo": c.archivo_origen,
                "Extracción": metodo,
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

        col1, col2, col3 = st.columns(3)
        col1.metric("Total base gravable", f"${df_cert['Base Gravable'].sum():,.0f}")
        col2.metric("Total valor retenido", f"${df_cert['Valor Retenido'].sum():,.0f}")
        col3.metric("Municipios distintos", df_cert["Ciudad Retención"].nunique())

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
        "o cualquier Excel con la misma estructura del área de Contabilidad."
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
            except KeyError:
                st.error(
                    f"❌ **No se encontró la hoja '{hoja}'** en el archivo.\n\n"
                    "Verifique el nombre exacto de la hoja (distingue mayúsculas y espacios). "
                    "Las hojas disponibles aparecen en las pestañas del Excel."
                )
            except Exception as e:
                st.error(
                    f"❌ **Error al leer el archivo Excel.**\n\n"
                    f"Detalle técnico: `{e}`\n\n"
                    "Asegúrese de que el archivo no esté abierto en Excel y que tenga el formato correcto."
                )

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
    facturas_ok     = st.session_state.get("facturas", [])

    if not certificados_ok and not facturas_ok:
        st.info("📌 Carga primero los certificados y/o las facturas en las pestañas anteriores.")
    else:
        col_e1, col_e2 = st.columns(2)
        col_e1.metric("Certificados listos", len(certificados_ok))
        col_e2.metric("Facturas listas", len(facturas_ok))

        if not certificados_ok:
            st.warning("⚠️ **No hay certificados cargados.** El cruce identificará facturas sin certificado.")
        if not facturas_ok:
            st.warning("⚠️ **No hay facturas cargadas.** El cruce identificará certificados sin factura.")

        puede_conciliar = certificados_ok or facturas_ok
        if st.button("🔄 Ejecutar conciliación", type="primary", disabled=not puede_conciliar):
            with st.spinner("Cruzando datos…"):
                resultados = conciliar(facturas_ok, certificados_ok)
            st.session_state["resultados"] = resultados
            st.success(f"✅ Conciliación completada — {len(resultados)} registro(s).")

    resultados_sesion: list[ResultadoCruce] = st.session_state.get("resultados", [])

    if resultados_sesion:
        total        = len(resultados_sesion)
        coinciden    = sum(1 for r in resultados_sesion if r.estado == "COINCIDE")
        no_coinciden = sum(1 for r in resultados_sesion if r.estado == "NO_COINCIDE")
        sin_cert     = sum(1 for r in resultados_sesion if r.estado == "SIN_MATCH_CERT")
        sin_fact     = sum(1 for r in resultados_sesion if r.estado == "SIN_MATCH_FACTURA")
        conf_prom    = sum(r.confianza for r in resultados_sesion) / total

        # ── Métricas grandes ──────────────────────────────────────────────
        st.subheader("Resumen")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("✅ Coinciden",       coinciden,    f"{100*coinciden/total:.0f}%")
        c2.metric("⚠️ No coinciden",    no_coinciden, f"{100*no_coinciden/total:.0f}%")
        c3.metric("❌ Sin certificado", sin_cert,     f"{100*sin_cert/total:.0f}%")
        c4.metric("❌ Sin factura",     sin_fact,     f"{100*sin_fact/total:.0f}%")
        c5.metric("🎯 Confianza prom.", f"{conf_prom:.0f}%")

        if no_coinciden > 0:
            st.markdown(
                '<div class="alerta-error">'
                f'<b>⚠️ {no_coinciden} registro(s) con discrepancias</b> '
                'requieren revisión en SIGO. '
                'Filtra por estado NO_COINCIDE para ver el detalle.'
                '</div>',
                unsafe_allow_html=True,
            )

        # ── Tabla de resultados ───────────────────────────────────────────
        st.subheader("Detalle")
        filtro_estado = st.multiselect(
            "Filtrar por estado",
            options=["COINCIDE", "NO_COINCIDE", "SIN_MATCH_CERT", "SIN_MATCH_FACTURA"],
            default=["NO_COINCIDE", "SIN_MATCH_CERT", "SIN_MATCH_FACTURA"],
        )

        filas_cruce = []
        for r in resultados_sesion:
            n_facts = len(r.facturas_multiple) if r.facturas_multiple else (1 if r.factura else 0)
            base_fact = (
                sum(f.subtotal for f in r.facturas_multiple)
                if r.facturas_multiple
                else (r.factura.subtotal if r.factura else 0)
            )
            filas_cruce.append({
                "Estado": r.estado,
                "Confianza": f"{r.confianza:.0f}%",
                "Comprobante": (
                    f"{r.factura.numero_factura} +{len(r.facturas_multiple)-1} más"
                    if r.facturas_multiple else
                    (r.factura.numero_factura if r.factura else "")
                ),
                "# Facturas": n_facts,
                "Cliente / Retenedor": (
                    r.factura.cliente_nombre if r.factura
                    else (r.certificado.retenedor_nombre if r.certificado else "")
                ),
                "Municipio Factura": r.municipio_factura,
                "Municipio Certificado": r.municipio_certificado,
                "Base Factura": base_fact,
                "Base Certificado": r.certificado.base_gravable if r.certificado else 0,
                "Diferencia": r.diferencia_valor,
                "Observación": r.observacion,
            })

        df_cruce = pd.DataFrame(filas_cruce)
        df_cruce_filtrado = (
            df_cruce[df_cruce["Estado"].isin(filtro_estado)]
            if filtro_estado else df_cruce
        )

        COLORES_ESTADO = {
            "COINCIDE":             "background-color:#d4edda; color:#155724;",
            "NO_COINCIDE":          "background-color:#f8d7da; color:#721c24;",
            "SIN_MATCH_CERT":       "background-color:#fff3cd; color:#856404;",
            "SIN_MATCH_FACTURA":    "background-color:#e8d5f5; color:#6f42c1;",
        }

        st.dataframe(
            df_cruce_filtrado.style
                .map(lambda v: COLORES_ESTADO.get(v, ""), subset=["Estado"])
                .format({
                    "Base Factura":     "${:,.0f}",
                    "Base Certificado": "${:,.0f}",
                    "Diferencia":       "${:,.0f}",
                }),
            use_container_width=True,
            hide_index=True,
            height=420,
        )

        # ── Exportar ──────────────────────────────────────────────────────
        st.divider()
        st.subheader("Exportar reporte")
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_out:
            tmp_out_path = tmp_out.name
        generar_reporte_excel(resultados_sesion, tmp_out_path)
        with open(tmp_out_path, "rb") as f_out:
            st.download_button(
                "⬇️ Descargar reporte de conciliación (Excel)",
                data=f_out.read(),
                file_name="reporte_conciliacion_ica.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )

# ===========================================================================
# PESTAÑA 4 — Municipios (PRIORIDAD 3)
# ===========================================================================
with tab_munis:
    st.header("🗺️ Tabla Maestra de Municipios ICA")
    st.markdown(
        f"**{len(MUNICIPIOS_ICA)} municipios** activos de PCC Integrity. "
        "Las tarifas marcadas con ⚠️ son estimadas — verifique con cada municipio antes de declarar."
    )

    df_munis = todos_municipios_df()

    # Filtros
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        filtro_depto = st.selectbox(
            "Departamento",
            ["Todos"] + sorted(df_munis["Departamento"].unique().tolist()),
        )
    with col_m2:
        filtro_period = st.selectbox(
            "Periodicidad",
            ["Todos", "ANUAL", "TRIMESTRAL"],
        )
    with col_m3:
        filtro_verif = st.selectbox(
            "Tarifa",
            ["Todos", "✅ Verificada", "⚠️ Estimada"],
        )

    df_m = df_munis.copy()
    if filtro_depto != "Todos":
        df_m = df_m[df_m["Departamento"] == filtro_depto]
    if filtro_period != "Todos":
        df_m = df_m[df_m["Periodicidad"] == filtro_period]
    if filtro_verif == "✅ Verificada":
        df_m = df_m[df_m["Tarifa Verificada"] == "✅"]
    elif filtro_verif == "⚠️ Estimada":
        df_m = df_m[df_m["Tarifa Verificada"] == "⚠️ Estimada"]

    st.dataframe(
        df_m.style.format({"Tarifa ICA (‰)": "{:.2f}"}),
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    # Métricas resumen
    trimestrales = municipios_trimestrales()
    st.divider()
    cm1, cm2, cm3 = st.columns(3)
    cm1.metric("Total municipios", len(MUNICIPIOS_ICA))
    cm2.metric("Declaración trimestral", len(trimestrales))
    cm3.metric("Declaración anual", len(municipios_anuales()))

    st.info(
        f"**Municipios trimestrales:** {', '.join(sorted(trimestrales))}\n\n"
        "Todos los demás son anuales."
    )

    # Descarga
    buf_m = io.BytesIO()
    df_munis.to_excel(buf_m, index=False)
    st.download_button(
        "⬇️ Descargar tabla de municipios",
        data=buf_m.getvalue(),
        file_name="municipios_ica_pcc.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# ===========================================================================
# PESTAÑA 5 — Declaraciones (PRIORIDAD 4)
# ===========================================================================
with tab_decl:
    st.header("📋 Asistente de Declaraciones ICA")
    st.markdown(
        "Selecciona un municipio y período. El sistema calcula el impuesto, "
        "aplica avisos y tableros y sobretasa bomberil si corresponde, "
        "y genera el borrador para revisión."
    )

    municipios_lista = sorted(MUNICIPIOS_ICA.keys())
    resultados_decl = st.session_state.get("resultados", [])

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        muni_sel = st.selectbox("Municipio", municipios_lista, key="decl_muni")
    with col_d2:
        periodo_sel = st.selectbox(
            "Período",
            ["2025-ANUAL", "2025-T1", "2025-T2", "2025-T3", "2025-T4"],
            key="decl_periodo",
        )

    muni_obj = MUNICIPIOS_ICA.get(muni_sel)

    if muni_obj:
        # Info del municipio seleccionado
        col_i1, col_i2, col_i3, col_i4 = st.columns(4)
        col_i1.metric("Departamento", muni_obj.departamento)
        col_i2.metric("Periodicidad", muni_obj.periodicidad)
        col_i3.metric("Tarifa ICA", f"{muni_obj.tarifa_por_mil:.1f}‰")
        col_i4.metric(
            "Tarifa",
            "✅ Verificada" if muni_obj.verificado else "⚠️ Estimada",
        )

        if not muni_obj.verificado:
            st.warning(
                "⚠️ **Tarifa estimada.** Confirme la tarifa vigente con el municipio "
                f"antes de presentar la declaración de {muni_sel}."
            )

        st.divider()

        # Auto-poblar base gravable desde conciliación si hay resultados
        base_auto = 0.0
        if resultados_decl:
            for r in resultados_decl:
                muni_fact = r.municipio_factura or ""
                muni_cert = r.municipio_certificado or ""
                if (muni_sel.upper() in muni_fact.upper() or muni_sel.upper() in muni_cert.upper()):
                    if r.factura:
                        base_auto += r.factura.subtotal
                    for f in r.facturas_multiple:
                        base_auto += f.subtotal

        # ── Sección 1: Ingresos ────────────────────────────────────────────
        st.subheader("1. Ingresos")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            ingresos_pais = st.number_input(
                "Renglón 8 — Total ingresos país ($)",
                min_value=0.0, step=1000.0, format="%.0f",
                value=0.0, key="decl_ing_pais",
            )
        with col_b2:
            ingresos_fuera = st.number_input(
                "Renglón 9 — Ingresos fuera del municipio ($)",
                min_value=0.0, step=1000.0, format="%.0f",
                value=0.0, key="decl_ing_fuera",
            )

        base_gravable = st.number_input(
            "Renglón 10 — Base gravable en el municipio ($)",
            min_value=0.0, step=1000.0, format="%.0f",
            value=float(round(base_auto)),
            help=(
                f"Auto-calculado desde conciliación: ${base_auto:,.0f}"
                if base_auto > 0 else
                "Ingrese la base gravable del municipio seleccionado"
            ),
            key="decl_base",
        )

        if base_auto > 0 and abs(base_gravable - base_auto) < 1:
            st.success(f"✅ Base gravable tomada del reporte de conciliación: ${base_auto:,.0f}")

        # ── Sección 2: Liquidación ────────────────────────────────────────
        st.subheader("2. Liquidación")

        impuesto_base = base_gravable * muni_obj.tarifa_por_mil / 1000
        avisos = impuesto_base * 0.15 if muni_obj.aplica_avisos_tableros else 0.0
        bomberil = impuesto_base * 0.05 if muni_obj.aplica_sobretasa_bomberil else 0.0
        total_cargo = impuesto_base + avisos + bomberil

        col_l1, col_l2, col_l3, col_l4 = st.columns(4)
        col_l1.metric(
            f"Impuesto ICA ({muni_obj.tarifa_por_mil}‰)",
            f"${impuesto_base:,.0f}",
        )
        col_l2.metric(
            "Avisos y Tableros (15%)" if muni_obj.aplica_avisos_tableros else "Avisos y Tableros",
            f"${avisos:,.0f}" if muni_obj.aplica_avisos_tableros else "No aplica",
        )
        col_l3.metric(
            "Sobretasa Bomberil (5%)" if muni_obj.aplica_sobretasa_bomberil else "Sobretasa Bomberil",
            f"${bomberil:,.0f}" if muni_obj.aplica_sobretasa_bomberil else "No aplica",
        )
        col_l4.metric("Total a cargo", f"${total_cargo:,.0f}")

        # ── Sección 3: Descuentos ─────────────────────────────────────────
        st.subheader("3. Descuentos y anticipos")

        col_desc1, col_desc2, col_desc3 = st.columns(3)
        with col_desc1:
            retenciones = st.number_input(
                "Retenciones del período ($)",
                min_value=0.0, step=1000.0, format="%.0f",
                key="decl_ret",
            )
        with col_desc2:
            saldo_favor = st.number_input(
                "Saldo a favor período anterior ($)",
                min_value=0.0, step=1000.0, format="%.0f",
                key="decl_saldo",
            )
        with col_desc3:
            anticipo_ant = st.number_input(
                "Anticipo año anterior ($)",
                min_value=0.0, step=1000.0, format="%.0f",
                key="decl_anticipo_ant",
            )

        # ── Resultado ─────────────────────────────────────────────────────
        total_descuentos = retenciones + saldo_favor + anticipo_ant
        saldo_pagar = max(0.0, total_cargo - total_descuentos)
        saldo_favor_nuevo = max(0.0, total_descuentos - total_cargo)
        anticipo_sig = total_cargo * 0.25  # anticipo típico 25%

        st.divider()
        st.subheader("4. Resultado")

        col_r1, col_r2, col_r3 = st.columns(3)
        if saldo_pagar > 0:
            col_r1.metric("💰 TOTAL A PAGAR", f"${saldo_pagar:,.0f}", delta=None)
        else:
            col_r1.metric("💚 SALDO A FAVOR", f"${saldo_favor_nuevo:,.0f}")
        col_r2.metric("Anticipo siguiente período (25%)", f"${anticipo_sig:,.0f}")
        col_r3.metric("Fecha límite declaración", muni_obj.fecha_limite_declaracion)

        # ── Borrador completo ─────────────────────────────────────────────
        with st.expander("📄 Ver borrador completo de la declaración"):
            st.markdown(f"""
| Renglón | Concepto | Valor |
|---------|----------|-------|
| 8 | Total ingresos brutos del país | ${ingresos_pais:,.0f} |
| 9 | Ingresos brutos obtenidos fuera del municipio | ${ingresos_fuera:,.0f} |
| 10 | **Base gravable en {muni_sel}** | **${base_gravable:,.0f}** |
| 11 | Tarifa | {muni_obj.tarifa_por_mil:.1f}‰ |
| 12 | Impuesto ICA | ${impuesto_base:,.0f} |
| 13 | Avisos y tableros (15%) | ${avisos:,.0f} |
| 14 | Sobretasa bomberil | ${bomberil:,.0f} |
| **15** | **Total impuesto a cargo** | **${total_cargo:,.0f}** |
| 26 | Retenciones practicadas | ${retenciones:,.0f} |
| 27 | Saldo a favor período anterior | ${saldo_favor:,.0f} |
| 28 | Anticipo liquidado año anterior | ${anticipo_ant:,.0f} |
| **29** | **Total a pagar** | **${saldo_pagar:,.0f}** |
| 30 | Anticipo para siguiente período | ${anticipo_sig:,.0f} |

*Municipio: {muni_sel} — {muni_obj.departamento}*
*Período: {periodo_sel} — Tarifa: {"✅ Verificada" if muni_obj.verificado else "⚠️ Estimada"}*
            """)

        # ── Exportar a Excel ──────────────────────────────────────────────
        if st.button("📥 Exportar borrador a Excel", type="primary"):
            datos_decl = {
                "Concepto": [
                    "Municipio", "Departamento", "Período", "Periodicidad",
                    "Tarifa ICA (‰)", "Tarifa verificada",
                    "R8 — Total ingresos país",
                    "R9 — Ingresos fuera municipio",
                    "R10 — Base gravable municipio",
                    "R12 — Impuesto ICA",
                    "R13 — Avisos y tableros",
                    "R14 — Sobretasa bomberil",
                    "R15 — Total a cargo",
                    "R26 — Retenciones período",
                    "R27 — Saldo a favor anterior",
                    "R28 — Anticipo año anterior",
                    "R29 — TOTAL A PAGAR",
                    "R30 — Anticipo siguiente período",
                    "Fecha límite declaración",
                    "Estado",
                ],
                "Valor": [
                    muni_sel, muni_obj.departamento, periodo_sel, muni_obj.periodicidad,
                    muni_obj.tarifa_por_mil, "Verificada" if muni_obj.verificado else "ESTIMADA — verificar",
                    ingresos_pais, ingresos_fuera, base_gravable,
                    impuesto_base, avisos, bomberil, total_cargo,
                    retenciones, saldo_favor, anticipo_ant,
                    saldo_pagar, anticipo_sig,
                    muni_obj.fecha_limite_declaracion,
                    "BORRADOR",
                ],
            }
            df_decl = pd.DataFrame(datos_decl)
            buf_decl = io.BytesIO()
            df_decl.to_excel(buf_decl, index=False, sheet_name="Declaración ICA")
            st.download_button(
                f"⬇️ Descargar borrador {muni_sel} {periodo_sel}",
                data=buf_decl.getvalue(),
                file_name=f"borrador_ICA_{muni_sel}_{periodo_sel}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

# ===========================================================================
# PESTAÑA 6 — Ayuda
# ===========================================================================
with tab_ayuda:
    st.header("Guía de uso")

    st.markdown("""
### Flujo recomendado

1. **Pestaña "Certificados ReteICA"**
   - Sube los PDFs de certificados que envían los clientes
   - El extractor usa Claude API automáticamente (alta precisión)
   - Si no hay conexión, usa extractor regex como respaldo

2. **Pestaña "Facturas SIGO"**
   - Sube el archivo `CONCILIAICON INGRESOS MUNICIPIOS 2025.xlsx`
   - La hoja por defecto es `INGRESOS MUNICIPIOS 2025`

3. **Pestaña "Conciliación"**
   - Con certificados y facturas cargados, ejecuta la conciliación
   - El sistema cruza por **NIT + período + valor EXACTO**
   - Revisa primero los estados **NO_COINCIDE** (requieren corrección en SIGO)
   - La columna **Confianza %** indica qué tan seguro es el match

4. **Pestaña "Municipios"**
   - Tabla con los 60 municipios activos, tarifas y periodicidades
   - Las tarifas ⚠️ son estimadas — verificar antes de declarar

5. **Pestaña "Declaraciones"**
   - Selecciona municipio y período
   - Si ya ejecutaste la conciliación, la base gravable se auto-completa
   - Completa los campos de descuentos y exporta el borrador

---

### Estados de conciliación

| Estado | Significado | Acción |
|--------|-------------|--------|
| ✅ COINCIDE | Municipio y valor coinciden | Ninguna |
| ⚠️ NO_COINCIDE | Municipio o valor no coincide | Corregir en SIGO |
| ❌ SIN_MATCH_CERT | Factura con ReteICA sin certificado | Solicitar al cliente |
| ❌ SIN_MATCH_FACTURA | Certificado sin factura | Verificar en SIGO |

---

### Lógica de matching

El sistema cruza por estos criterios en orden:
1. **NIT exacto** del retenedor (peso: 40%)
2. **Período** del certificado coincide con fecha de factura (peso: 30%)
3. **Valor exacto** — base gravable == subtotal factura, sin tolerancias (peso: 30%)
4. Si el valor del certificado cubre varias facturas, detecta la combinación exacta

---

### Municipios trimestrales

- **Bogotá** (D.C.) — Vence último día hábil de abril, julio, octubre y enero
- **Yopal** (Casanare) — Mismo calendario
- **Valledupar** (Cesar) — Mismo calendario

---

### Contacto técnico
Para reportar errores: **Pablo Rivera** — Sistemas / Contabilidad PCC Integrity
    """)

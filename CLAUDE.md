# App de Automatización ICA Municipal — PCC Integrity

## Contexto del Proyecto

**Empresa:** Protección Catódica de Colombia S.A.S. (PCC Integrity)
**NIT:** 860068218-1
**Responsable:** Pablo Rivera
**Origen:** Reunión con Luz (Contabilidad) — 10/03/2026

Este proyecto automatiza el proceso de declaración y conciliación del **Impuesto de Industria y Comercio (ICA)** municipal, que actualmente es 100% manual y consume ~80% del tiempo de contabilidad en digitación.

---

## Problema que Resuelve

### Flujo actual (manual)
1. Se genera factura en SIGO → llega como PDF
2. Cliente envía certificado de retención de ICA → llega como PDF
3. Luz valida manualmente que municipio de factura = municipio del certificado
4. Si no coincide → corrección manual en SIGO
5. Se alimenta Excel manualmente con: cliente, municipio, ingreso, reteICA
6. Al cierre del año → se consulta tarifa/normatividad de cada municipio
7. Se monta y presenta declaración en portal de cada municipio

### Puntos de dolor
- Extracción manual de datos de PDFs
- Cruce manual factura vs certificado
- Nombres de municipios inconsistentes en el Excel (ej: "ACACIAS" vs "ACACIAS - META")
- 60 municipios activos en 2025
- 95% de ICA son anuales; trimestrales: Bogotá, Yopal, Valledupar

---

## Archivos de Referencia (en `../`)

### `CONCILIAICON INGRESOS MUNICIPIOS 2025.xlsx`
Base de datos maestra de ingresos. Tiene 3 hojas:
- **`INGRESOS MUNICIPIOS 2025`** — 148 facturas de venta (hoja principal)
  - Columnas: Tipo transacción, Comprobante, Fecha elaboración, Identificación, Nombre cliente, SubTotal, Iva, Total, CONCEPTO, CIUDAD/MUNICIPIO, RETEICA, TARIFA
  - 22 clientes distintos (Ocensa, TGI, Ecopetrol, Perenco, Promigas, etc.)
  - 60 entradas de municipio (con nombres inconsistentes — normalizar)
  - Total ingresos 2025: $6,357,207,959
  - Las filas de datos empiezan en la fila 10 (índice 9), los headers están en fila 9 (índice 8)
  - Las primeras 8 filas son encabezado de empresa (ignorar)
- **`10022 DDI-010349-ART13`** — Reporte Bogotá DIAN (352,127 filas)
- **`INGRESOS BOG Y MUNI`** — Ingresos Bogotá + municipios (299 filas)

### `Ica Santa Marta Catodica 2025.pdf`
Declaración de ICA presentada en Santa Marta, año gravable 2025.
- 6 páginas (3 copias: contribuyente, alcaldía, banco)
- Campos clave extraíbles con pdfplumber:
  - Renglón 8: Total ingresos país = $14,569,301,000
  - Renglón 9: Ingresos fuera del municipio = $14,530,774,000
  - Renglón 10: Base gravable en municipio = $38,527,000
  - Tarifa: 7‰ (actividad 7110 - Arquitectura e Ingeniería)
  - Impuesto ICA: $270,000
  - Sobretasa bomberil: $19,000
  - Retención descontada (renglón 27): $270,000
  - Total a pagar: $19,000
- Formato: FORMULARIO ÚNICO NACIONAL (estándar para todos los municipios)

### `TERMOTECNICA Cert ReteIca BIM VI SANTA MARTA (1).pdf`
Certificado de retención ICA emitido por Termotécnica Coindustrial S.A.S.
- 1 página
- Campos clave:
  - Retenedor: TERMOTECNICA COINDUSTRIAL S.A.S. (NIT 890903035-2)
  - Retenido: PROTECCION CATODICA DE COLOMBIA Y CIA S C S (NIT 860068218-1)
  - Ciudad retención: Santa Marta, Magdalena
  - Período: Bimestre 1/11/2025 al 31/12/2025
  - Base gravable: $38,527,327
  - Tarifa: 7‰
  - Valor retenido: $269,691
  - Fecha expedición: 12/02/2026

### Cruce exitoso observado
- Certificado base: $38,527,327 ≈ Declaración base: $38,527,000 ✅ (diferencia de redondeo normal)

---

## Arquitectura de la Solución

```
app_ica_pcc/
├── CLAUDE.md                    # Este archivo — contexto del proyecto
├── README.md                    # Instrucciones de uso
├── requirements.txt             # Dependencias Python
├── main.py                      # Entry point principal
├── config.py                    # Configuración global
│
├── data/
│   ├── pdfs_facturas/           # PDFs de facturas SIGO
│   ├── pdfs_certificados/       # PDFs de certificados de retención ICA
│   └── excel_base/              # Excel de conciliación de Luz
│
├── src/
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── factura_extractor.py     # Extrae datos de PDFs de facturas SIGO
│   │   └── certificado_extractor.py # Extrae datos de certificados ReteICA
│   │
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── municipio_normalizer.py  # Normaliza nombres de municipios
│   │   └── conciliador.py           # Cruza facturas vs certificados
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py                # Estructuras de datos (dataclasses)
│   │   └── excel_manager.py         # Lee/escribe Excel de conciliación
│   │
│   └── ui/
│       ├── __init__.py
│       └── app.py                   # Interfaz Streamlit (Fase futura)
│
├── outputs/
│   ├── conciliaciones/          # Reportes de cruce factura-certificado
│   ├── declaraciones/           # Borradores de declaraciones ICA
│   └── reportes/                # Reportes de estado y alertas
│
├── tests/
│   └── test_extractors.py
│
└── docs/
    └── municipios_tarifa.md     # Tabla de municipios y tarifas (a completar)
```

---

## Fases de Desarrollo

### ✅ Fase 0 — Análisis (COMPLETADO en Cowork)
- Archivos analizados y estructura comprendida
- Problema definido y arquitectura diseñada

### 🔴 Fase 1 — Extracción de PDFs (PRIORIDAD ALTA)
**Objetivo:** Script que recibe una carpeta de PDFs y genera CSV/Excel con datos extraídos.

Para **certificados de retención** (como el de Termotécnica), extraer:
- Nombre del retenedor (empresa que retiene)
- NIT del retenedor
- Nombre del retenido (PCC)
- Ciudad donde se practicó la retención
- Período (fechas)
- Base gravable
- Tarifa
- Valor retenido
- Fecha de expedición

Para **facturas SIGO** (cuando se tengan muestras), extraer:
- Número de factura
- Cliente
- NIT cliente
- Municipio del servicio
- Valor subtotal
- Fecha

**Tecnología:** pdfplumber (textos digitales) + pytesseract (PDFs escaneados)

### 🔴 Fase 2 — Cruce automático (PRIORIDAD ALTA)
- Tomar certificado → buscar factura por cliente + período
- Comparar municipio de factura vs municipio de certificado
- Clasificar: ✅ Coincide / ⚠️ No coincide / ❌ Sin match
- Generar reporte de discrepancias para Luz

### 🔴 Fase 3 — Base de datos centralizada (PRIORIDAD ALTA)
- Reemplazar Excel manual por Excel avanzado con Power Query
- O app Streamlit (similar a la app CIPS que ya existe en PCC)
- Tabla maestra de municipios con tarifas y normatividad

### 🟡 Fase 4 — Asistente de declaraciones (PRIORIDAD MEDIA)
- Pre-diligenciar declaraciones automáticamente
- Calcular base gravable, tarifa, anticipo, avisos y tableros
- Arrastrar saldos a favor de período anterior
- Generar calendario de vencimientos

### 🟢 Fase 5 — Automatización de portales (OPCIONAL)
- RPA con Playwright para portales municipales sistematizados
- Riesgo medio-alto (portales cambian sin aviso)

---

## Decisiones de Arquitectura Importantes

1. **Formato de salida:** Excel (no base de datos SQL) para mantener familiaridad con Luz
2. **Interfaz:** Streamlit si se necesita UI visual (ya hay precedente con app CIPS en PCC)
3. **Extracción de PDFs:** pdfplumber para digitales; pytesseract + pdf2image para escaneados
4. **Normalización de municipios:** Crear tabla maestra con variantes conocidas (ej: "ACACIAS", "ACACIAS - META" → "ACACIAS")
5. **API de IA:** Usar Claude API para PDFs con formato muy variable o mal estructurado

---

## Notas Técnicas

- Los certificados de retención ICA **no tienen formato estándar** — cada empresa emisora tiene su propio diseño
- Las declaraciones ICA **sí tienen formato estándar** (Formulario Único Nacional)
- El Excel de Luz tiene espacios extra en algunos nombres de columnas: `'CIUDAD/ MUNICIPIO '` (con espacio al final)
- Los datos empiezan en la fila 10 del Excel (las primeras 9 son encabezado)
- Hay ~15 duplicados de nombres de municipio que necesitan normalización

---

## Comandos de Desarrollo

```bash
# Instalar dependencias
pip install -r requirements.txt

# Procesar certificados en una carpeta
python main.py --modo certificados --carpeta data/pdfs_certificados/

# Procesar facturas
python main.py --modo facturas --carpeta data/pdfs_facturas/

# Ejecutar conciliación
python main.py --modo conciliar --excel data/excel_base/conciliacion.xlsx

# Interfaz visual
streamlit run src/ui/app.py
```

---

## Próximos Pasos Inmediatos

- [ ] Recibir más muestras de PDFs de Luz (facturas SIGO + más certificados)
- [ ] Completar tabla maestra de municipios con tarifas
- [ ] Probar extractor de certificados con más emisores distintos
- [ ] Definir si la UI será Streamlit o Excel avanzado

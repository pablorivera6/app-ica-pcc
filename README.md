# App Automatización ICA Municipal — PCC Integrity

Automatiza el proceso de declaración y conciliación del Impuesto de Industria y Comercio (ICA) municipal para Protección Catódica de Colombia S.A.S.

## Instalación

```bash
pip install -r requirements.txt
```

## Uso rápido

```bash
# Extraer datos de certificados de retención PDF
python main.py --modo certificados --carpeta data/pdfs_certificados/

# Leer facturas desde el Excel de Luz
python main.py --modo facturas --excel data/excel_base/conciliacion.xlsx

# Conciliar facturas vs certificados
python main.py --modo conciliar \
    --excel data/excel_base/conciliacion.xlsx \
    --carpeta data/pdfs_certificados/ \
    --salida outputs/conciliaciones/reporte_2025.xlsx
```

## Estado del proyecto

- ✅ Fase 0: Análisis de archivos reales (completado)
- 🔄 Fase 1: Extracción de PDFs (en progreso)
- ⏳ Fase 2: Cruce automático (pendiente)
- ⏳ Fase 3: Base de datos centralizada (pendiente)
- ⏳ Fase 4: Asistente de declaraciones (pendiente)
- ⏳ Fase 5: Automatización de portales (opcional)

## Archivos de referencia

Los archivos reales de Luz están en la carpeta padre `../`:
- `CONCILIAICON INGRESOS MUNICIPIOS 2025.xlsx`
- `Ica Santa Marta Catodica 2025.pdf`
- `TERMOTECNICA Cert ReteIca BIM VI SANTA MARTA (1).pdf`

Ver `CLAUDE.md` para contexto completo del proyecto.

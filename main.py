"""
App de Automatización ICA Municipal — PCC Integrity
Entry point principal.

Uso:
    python main.py --modo certificados --carpeta data/pdfs_certificados/
    python main.py --modo facturas --excel data/excel_base/conciliacion.xlsx
    python main.py --modo conciliar --excel data/excel_base/conciliacion.xlsx --carpeta data/pdfs_certificados/
    streamlit run src/ui/app.py
"""
import argparse
from pathlib import Path
from src.extractors.certificado_extractor import procesar_carpeta as procesar_certificados
from src.extractors.factura_extractor import leer_facturas_desde_excel
from src.processors.conciliador import conciliar, generar_reporte_excel


def main():
    parser = argparse.ArgumentParser(
        description="Automatización ICA Municipal — PCC Integrity"
    )
    parser.add_argument(
        "--modo",
        choices=["certificados", "facturas", "conciliar"],
        required=True,
        help="Modo de operación"
    )
    parser.add_argument("--carpeta", help="Carpeta con PDFs de certificados")
    parser.add_argument("--excel", help="Ruta al Excel de conciliación de Luz")
    parser.add_argument("--salida", default="outputs/conciliaciones/reporte.xlsx", help="Ruta del reporte de salida")

    args = parser.parse_args()

    if args.modo == "certificados":
        if not args.carpeta:
            print("❌ Se requiere --carpeta para el modo certificados")
            return
        print(f"📂 Procesando PDFs de certificados en: {args.carpeta}")
        certificados = procesar_certificados(args.carpeta)
        print(f"\n✅ {len(certificados)} certificados procesados")

    elif args.modo == "facturas":
        if not args.excel:
            print("❌ Se requiere --excel para el modo facturas")
            return
        print(f"📊 Leyendo facturas desde: {args.excel}")
        facturas = leer_facturas_desde_excel(args.excel)
        print(f"\n✅ {len(facturas)} facturas cargadas")
        for f in facturas[:5]:
            print(f"   {f.numero_factura} | {f.cliente_nombre[:30]} | {f.municipio} | ${f.subtotal:,.0f}")

    elif args.modo == "conciliar":
        if not args.excel or not args.carpeta:
            print("❌ Se requieren --excel y --carpeta para el modo conciliar")
            return

        print(f"📊 Cargando facturas desde: {args.excel}")
        facturas = leer_facturas_desde_excel(args.excel)
        print(f"   → {len(facturas)} facturas cargadas")

        print(f"\n📂 Procesando certificados en: {args.carpeta}")
        certificados = procesar_certificados(args.carpeta)
        print(f"   → {len(certificados)} certificados procesados")

        print(f"\n🔄 Ejecutando conciliación...")
        resultados = conciliar(facturas, certificados)

        Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
        generar_reporte_excel(resultados, args.salida)


if __name__ == "__main__":
    main()

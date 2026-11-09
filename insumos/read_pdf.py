import pdfplumber
import pandas as pd

def leer_tablas_pdf(ruta_pdf: str) -> pd.DataFrame:
    """
    Lee todas las tablas de un PDF y devuelve un DataFrame.
    """

    registros = []

    with pdfplumber.open(ruta_pdf) as pdf:

        for pagina in pdf.pages:

            tablas = pagina.extract_tables()

            for tabla in tablas:

                if not tabla or len(tabla) <= 1:
                    continue

                encabezado = tabla[0]

                # Validar que es la tabla de movimientos
                if "ID" in encabezado: 
                
                    for fila in tabla[1:]:

                        if len(fila) >= 7:
                            registros.append({
                                    "id_operacion": fila[0],
                                    "fecha": fila[1],
                                    "sucursal": fila[2],
                                    "tipo_operacion": fila[3],
                                    "monto": fila[4],
                                    "canal": fila[5],
                                    "estado": fila[6]
                                })

    df = pd.DataFrame(registros)

    # Limpieza
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    return df
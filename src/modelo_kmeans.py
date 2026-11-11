"""Segmentación de la cartera de créditos con K-means.

Lee outputs/muestra.xlsx, construye las variables, evalúa varios valores de k,
entrena el modelo final y exporta un Excel listo para Power BI
(outputs/muestra_clusters.xlsx) junto con el modelo entrenado
(outputs/modelo_kmeans.joblib).

Uso (desde la raíz del proyecto):
    python src/modelo_kmeans.py
    python src/modelo_kmeans.py --k 5
    python src/modelo_kmeans.py --entrada otra.xlsx --salida resultado.xlsx

Notas de diseño:
- Los montos están en bolívares nominales de años distintos, por lo que no son
  comparables entre sí. Se usa el monto relativo dentro de su año de aprobación.
- Se excluyen el nombre y el RIF del cliente de la salida (datos personales).
- NÚMERO DE CRÉDITO no es único, por eso se genera un id_registro propio.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "outputs" / "muestra.xlsx"
SALIDA = RAIZ / "outputs" / "muestra_clusters.xlsx"
MODELO = RAIZ / "outputs" / "modelo_kmeans.joblib"

K_FINAL = 4
K_RANGO = range(2, 10)
SEMILLA = 42
FEATURES = ["monto_relativo_anio", "log_plazo", "pct_amortizacion"]

# Las fechas del Excel vienen como números seriales
EXCEL_EPOCH = pd.Timestamp("1899-12-30")

COLUMNAS_SALIDA = [
    "id_registro", "numero_credito", "tipo_persona", "actividad", "tipo_credito",
    "entidad_federal", "situacion", "fecha_aprobacion", "fecha_vencimiento",
    "anio_aprobacion", "plazo_dias", "monto_original_bs", "saldo_bs",
    "pct_amortizacion", "monto_relativo_anio", "cluster", "cluster_nombre",
    "pca_1", "pca_2",
]


def cargar_datos(ruta: Path) -> pd.DataFrame:
    """Lee el Excel y limpia los saltos de línea de los nombres de columna."""
    df = pd.read_excel(ruta)
    df.columns = [" ".join(str(c).split()) for c in df.columns]
    return df


def preparar_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Renombra columnas y construye las variables del modelo."""
    df = df.rename(columns={
        "NÚMERO DE CRÉDITO": "numero_credito",
        "TIPO PERSONA RIF": "tipo_persona",
        "ACTIVIDAD DEL CLIENTE": "actividad",
        "TIPO DE CRÉDITO": "tipo_credito",
        "ENTIDAD FEDERAL": "entidad_federal",
        "SITUACIÓN DEL CRÉDITO": "situacion",
        "MONTO ORIGINAL (BOLÍVARES)": "monto_original_bs",
        "SALDO DEL CRÉDITO (BOLÍVARES)": "saldo_bs",
        "PORCENTAJE DE AMORTIZACIÓN": "pct_amortizacion",
    }).copy()

    df["fecha_aprobacion"] = EXCEL_EPOCH + pd.to_timedelta(
        df["FECHA DE APROBACIÓN DEL CRÉDITO"], unit="D")
    df["fecha_vencimiento"] = EXCEL_EPOCH + pd.to_timedelta(
        df["FECHA DE VENCIMIENTO DEL CRÉDITO"], unit="D")
    df["plazo_dias"] = (df["fecha_vencimiento"] - df["fecha_aprobacion"]).dt.days.clip(lower=0)
    df["anio_aprobacion"] = df["fecha_aprobacion"].dt.year

    # Monto relativo: z-score del log10(monto) dentro de cada año de aprobación
    log_monto = np.log10(df["monto_original_bs"])
    por_anio = log_monto.groupby(df["anio_aprobacion"])
    df["monto_relativo_anio"] = (log_monto - por_anio.transform("mean")) / por_anio.transform("std")

    df["log_plazo"] = np.log1p(df["plazo_dias"])
    df["id_registro"] = np.arange(1, len(df) + 1)
    return df


def evaluar_k(X: np.ndarray, rango=K_RANGO) -> pd.DataFrame:
    """Calcula inercia, silueta y Davies-Bouldin para cada k."""
    filas = []
    for k in rango:
        modelo = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA).fit(X)
        filas.append({
            "k": k,
            "inercia": modelo.inertia_,
            "silueta": silhouette_score(X, modelo.labels_, sample_size=6000, random_state=SEMILLA),
            "davies_bouldin": davies_bouldin_score(X, modelo.labels_),
        })
    return pd.DataFrame(filas)


def nombrar_clusters(df: pd.DataFrame, k: int) -> dict[int, str]:
    """Asigna nombres según las características de cada cluster.

    Los nombres están pensados para k = 4 con estos datos. Con otro k se
    usan nombres genéricos (Cluster 0, Cluster 1, ...). Los nombres con años
    deben revisarse si cambia el conjunto de datos.
    """
    if k != 4:
        return {i: f"Cluster {i}" for i in range(k)}

    r = df.groupby("cluster").agg(
        pct_activos=("situacion", lambda s: (s == "Activo").mean()),
        plazo=("plazo_dias", "median"),
        monto_rel=("monto_relativo_anio", "mean"),
    )
    nombres = {}
    vigentes = r["pct_activos"].idxmax()
    nombres[vigentes] = "Vigentes anuales (2026)"
    restantes = r.drop(index=vigentes)
    corto = restantes["plazo"].idxmin()
    nombres[corto] = "Corto plazo 2020-2021"
    resto = restantes.drop(index=corto)
    nombres[resto["monto_rel"].idxmax()] = "Semestrales de monto alto"
    nombres[resto["monto_rel"].idxmin()] = "Semestrales de monto bajo"
    return nombres


def construir_perfil(df: pd.DataFrame) -> pd.DataFrame:
    """Resumen estadístico de cada cluster."""
    perfil = df.groupby(["cluster", "cluster_nombre"]).agg(
        n_creditos=("id_registro", "size"),
        monto_mediano_bs=("monto_original_bs", "median"),
        monto_relativo_prom=("monto_relativo_anio", "mean"),
        plazo_mediano_dias=("plazo_dias", "median"),
        pct_amortizacion_prom=("pct_amortizacion", "mean"),
        saldo_prom_bs=("saldo_bs", "mean"),
        anio_mediano=("anio_aprobacion", "median"),
        pct_activos=("situacion", lambda s: (s == "Activo").mean() * 100),
        pct_castigados=("situacion", lambda s: (s == "Castigado").mean() * 100),
    ).reset_index()
    perfil["pct_cartera"] = perfil["n_creditos"] / len(df) * 100
    return perfil


def entrenar(df: pd.DataFrame, k: int = K_FINAL):
    """Entrena K-means y devuelve (df con clusters, scaler, modelo, pca, métricas)."""
    scaler = StandardScaler()
    X = scaler.fit_transform(df[FEATURES])

    metricas = evaluar_k(X)
    modelo = KMeans(n_clusters=k, n_init=20, random_state=SEMILLA).fit(X)

    df = df.copy()
    df["cluster"] = modelo.labels_
    df["cluster_nombre"] = df["cluster"].map(nombrar_clusters(df, k))

    pca = PCA(n_components=2, random_state=SEMILLA)
    coords = pca.fit_transform(X)
    df["pca_1"], df["pca_2"] = coords[:, 0], coords[:, 1]
    return df, scaler, modelo, pca, metricas


def construir_centroides(scaler, modelo, df: pd.DataFrame) -> pd.DataFrame:
    """Centroides en las unidades originales de las variables."""
    cent = pd.DataFrame(scaler.inverse_transform(modelo.cluster_centers_), columns=FEATURES)
    cent["plazo_dias_aprox"] = np.expm1(cent["log_plazo"])
    nombres = df.drop_duplicates("cluster").set_index("cluster")["cluster_nombre"]
    cent.insert(0, "cluster", range(len(cent)))
    cent.insert(1, "cluster_nombre", cent["cluster"].map(nombres))
    return cent


def exportar(df, perfil, centroides, metricas, salida: Path) -> None:
    """Escribe el Excel para Power BI (sin nombre ni RIF del cliente)."""
    salida.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(salida, engine="openpyxl", datetime_format="yyyy-mm-dd") as w:
        df[COLUMNAS_SALIDA].to_excel(w, sheet_name="creditos_clusters", index=False)
        perfil.round(3).to_excel(w, sheet_name="perfil_clusters", index=False)
        centroides.round(3).to_excel(w, sheet_name="centroides", index=False)
        metricas.round(4).to_excel(w, sheet_name="metricas_k", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Segmentación K-means de la cartera de créditos")
    parser.add_argument("--entrada", type=Path, default=ENTRADA)
    parser.add_argument("--salida", type=Path, default=SALIDA)
    parser.add_argument("--modelo", type=Path, default=MODELO)
    parser.add_argument("--k", type=int, default=K_FINAL, help="número de clusters")
    args = parser.parse_args()

    df = preparar_variables(cargar_datos(args.entrada))
    df, scaler, modelo, pca, metricas = entrenar(df, args.k)
    perfil = construir_perfil(df)
    centroides = construir_centroides(scaler, modelo, df)

    exportar(df, perfil, centroides, metricas, args.salida)
    joblib.dump({"scaler": scaler, "kmeans": modelo, "pca": pca, "features": FEATURES}, args.modelo)

    print(f"Registros procesados: {len(df)}")
    print(f"Excel guardado en:    {args.salida}")
    print(f"Modelo guardado en:   {args.modelo}")
    print()
    print(perfil[["cluster", "cluster_nombre", "n_creditos", "pct_cartera"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()

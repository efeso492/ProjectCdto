"""Modelo de datos (esquema en estrella) para el dashboard de Power BI.

Toma outputs/muestra.xlsx, reutiliza el modelo K-means de modelo_kmeans.py y
genera outputs/modelo_datos.xlsx con una tabla de hechos y sus dimensiones:

    fact_creditos      1 fila = 1 crédito reportado
    dim_calendario     fechas de aprobación y vencimiento (+ valor de la unidad)
    dim_cliente        cliente anonimizado (solo las personas jurídicas conservan nombre)
    dim_actividad      actividad económica (código + descripción CIIU)
    dim_entidad_federal
    dim_tipo_credito
    dim_tipo_persona
    dim_situacion
    dim_estado_contable  estado inferido del prefijo de la cuenta contable
    perfil_clusters / centroides / metricas_k   (resultado del K-means)
    calidad_datos      hallazgos de calidad para revisar con el área dueña del dato

Uso (desde la raíz del proyecto):
    python src/modelo_datos.py
    python src/modelo_datos.py --k 5 --salida outputs/otro.xlsx

Decisiones de diseño (ver también calidad_datos):
- El RIF no es una llave de cliente confiable en esta muestra (un mismo nombre
  aparece con muchos RIF distintos), por eso el cliente se identifica por su nombre.
- Los montos en bolívares no son comparables entre años. La columna "Unidad de valor
  del crédito (cantidad)" se usa para expresar monto y saldo en una medida estable.
- El estado contable (vigente, reestructurado, vencido, en litigio, castigado) se
  infiere del prefijo de la cuenta contable. Confirmar con el catálogo contable.
- Se excluyen nombre y RIF de personas naturales de la salida.
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from modelo_kmeans import (EXCEL_EPOCH, ENTRADA, K_FINAL, RAIZ, cargar_datos,
                               construir_centroides, construir_perfil, entrenar,
                               preparar_variables)
except ImportError:  # cuando se importa como paquete (src.modelo_datos)
    from src.modelo_kmeans import (EXCEL_EPOCH, ENTRADA, K_FINAL, RAIZ, cargar_datos,
                                   construir_centroides, construir_perfil, entrenar,
                                   preparar_variables)

SALIDA = RAIZ / "outputs" / "modelo_datos.xlsx"
COL_CORTE = "FECHA DE LA SITUACIÓN DEL CRÉDITO"
COL_UVC = "UNIDAD DE VALOR DEL CRÉDITO (CANTIDAD)"
COL_CUENTA = "CÓDIGO CUENTA CONTABLE"
COL_AMORT = "MONTO DE LA AMORTIZACIÓN (BOLÍVARES)"
TOLERANCIA_UVC = 0.05  # desvío máximo del valor implícito de la unidad respecto a su fecha

ESTADOS_CONTABLES = {
    "131": ("Vigente", 1, 0),
    "132": ("Reestructurado", 2, 0),
    "133": ("Vencido", 3, 1),
    "134": ("En litigio", 4, 1),
    "819": ("Castigado", 5, 0),
}
TIPOS_PERSONA = {
    "J": "Persona jurídica", "V": "Persona natural venezolana", "E": "Persona natural extranjera",
    "G": "Gobierno", "R": "R (sin descripción en el catálogo)",
}
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

SECCIONES = {
    "A": "Agricultura, ganadería, silvicultura y pesca", "B": "Explotación de minas y canteras",
    "C": "Industrias manufactureras", "D": "Suministro de electricidad, gas y vapor",
    "E": "Suministro de agua y gestión de desechos", "F": "Construcción",
    "G": "Comercio y reparación de vehículos", "H": "Transporte y almacenamiento",
    "I": "Alojamiento y servicios de comidas", "J": "Información y comunicaciones",
    "K": "Actividades financieras y de seguros", "L": "Actividades inmobiliarias",
    "M": "Actividades profesionales, científicas y técnicas",
    "N": "Servicios administrativos y de apoyo", "O": "Administración pública y defensa",
    "P": "Enseñanza", "Q": "Salud humana y asistencia social",
    "R": "Artes, entretenimiento y recreación", "S": "Otras actividades de servicios",
    "T": "Hogares como empleadores", "U": "Organizaciones extraterritoriales",
}
DIVISIONES = {
    "01": "Agricultura y ganadería", "02": "Silvicultura", "03": "Pesca y acuicultura",
    "05": "Carbón", "06": "Petróleo crudo y gas natural", "07": "Minerales metalíferos",
    "08": "Otras minas y canteras", "09": "Apoyo a la minería", "10": "Productos alimenticios",
    "11": "Bebidas", "12": "Tabaco", "13": "Textiles", "14": "Prendas de vestir", "15": "Cuero y calzado",
    "16": "Madera y corcho", "17": "Papel", "18": "Impresión", "19": "Coque y refinación de petróleo",
    "20": "Sustancias químicas", "21": "Productos farmacéuticos", "22": "Caucho y plástico",
    "23": "Minerales no metálicos", "24": "Metales básicos", "25": "Productos metálicos",
    "26": "Informática y electrónica", "27": "Equipo eléctrico", "28": "Maquinaria",
    "29": "Vehículos automotores", "30": "Otro equipo de transporte", "31": "Muebles",
    "32": "Otras manufacturas", "33": "Reparación de maquinaria", "35": "Electricidad y gas",
    "36": "Captación de agua", "37": "Alcantarillado", "38": "Gestión de desechos",
    "39": "Saneamiento", "41": "Construcción de edificios", "42": "Obras de ingeniería civil",
    "43": "Construcción especializada", "45": "Comercio y reparación de vehículos",
    "46": "Comercio al por mayor", "47": "Comercio al por menor", "49": "Transporte terrestre",
    "50": "Transporte acuático", "51": "Transporte aéreo", "52": "Almacenamiento y apoyo al transporte",
    "53": "Correo y mensajería", "55": "Alojamiento", "56": "Servicios de comidas y bebidas",
    "58": "Edición", "59": "Cine, video y música", "60": "Radio y televisión",
    "61": "Telecomunicaciones", "62": "Programación y consultoría informática",
    "63": "Servicios de información", "64": "Servicios financieros", "65": "Seguros",
    "66": "Auxiliares financieros", "68": "Actividades inmobiliarias", "69": "Jurídicas y contables",
    "70": "Consultoría de gestión", "71": "Arquitectura e ingeniería", "72": "Investigación científica",
    "73": "Publicidad y estudios de mercado", "74": "Otras profesionales y técnicas",
    "75": "Veterinarias", "77": "Alquiler y arrendamiento", "78": "Empleo", "79": "Agencias de viajes",
    "80": "Seguridad e investigación", "81": "Servicios a edificios y jardinería",
    "82": "Apoyo administrativo de oficina", "84": "Administración pública", "85": "Enseñanza",
    "86": "Salud humana", "87": "Asistencia residencial", "88": "Asistencia social sin alojamiento",
    "90": "Creación artística y espectáculos", "91": "Bibliotecas y museos", "92": "Juegos de azar",
    "93": "Deportes y recreación", "94": "Asociaciones", "95": "Reparación de computadores y enseres",
    "96": "Otros servicios personales", "97": "Hogares como empleadores",
    "98": "Hogares producen para uso propio", "99": "Organizaciones extraterritoriales",
}
ACENTOS = {
    "ANZOATEGUI": "Anzoátegui", "BOLIVAR": "Bolívar", "FALCON": "Falcón", "GUARICO": "Guárico",
    "MERIDA": "Mérida", "TACHIRA": "Táchira", "DISTRITO CAPITAL": "Distrito Capital",
}


def normalizar_nombre(texto: str) -> str:
    """Mayúsculas, sin tildes y sin espacios repetidos (llave de cliente)."""
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).upper().strip()


# ----------------------------------------------------------------- unidades de valor
def agregar_unidades_de_valor(df: pd.DataFrame):
    """Expresa monto y saldo en unidades de valor (comparables entre años).

    El valor implícito por unidad (monto / cantidad de unidades) es prácticamente
    idéntico para todos los créditos aprobados el mismo día, por lo que se estima
    un valor por fecha. Si la cantidad reportada falta o se desvía más de
    TOLERANCIA_UVC de ese valor, se recalcula con el valor de la fecha.
    """
    uvc = pd.to_numeric(df[COL_UVC], errors="coerce")
    implicito = df["monto_original_bs"] / uvc
    observado = implicito.groupby(df["fecha_aprobacion"]).median().dropna()

    rango = pd.date_range(df["fecha_aprobacion"].min(), df["fecha_aprobacion"].max(), freq="D")
    serie = observado.reindex(rango)
    interpolado = serie.isna()
    serie = np.exp(np.log(serie).interpolate(method="time", limit_direction="both"))

    valor_fecha = df["fecha_aprobacion"].map(serie)
    desvio = (implicito / valor_fecha - 1).abs()
    reportada_ok = uvc.notna() & (desvio <= TOLERANCIA_UVC)

    df = df.copy()
    df["monto_uvc"] = np.where(reportada_ok, uvc, df["monto_original_bs"] / valor_fecha)
    df["uvc_origen"] = np.select([reportada_ok, uvc.isna()], ["reportada", "estimada"], default="corregida")
    df["saldo_uvc"] = df["monto_uvc"] * df["saldo_bs"] / df["monto_original_bs"]
    return df, serie, interpolado


# ----------------------------------------------------------------- indicadores
def agregar_indicadores(df: pd.DataFrame, corte: pd.Timestamp) -> pd.DataFrame:
    """Estado contable, vencimientos y banderas de riesgo."""
    df = df.copy()
    prefijo = df[COL_CUENTA].astype(str).str[:3]
    df["cuenta_contable"] = df[COL_CUENTA].astype(str)
    df["estado_contable"] = prefijo.map({k: v[0] for k, v in ESTADOS_CONTABLES.items()}).fillna("Otro")
    df["monto_amortizado_bs"] = df[COL_AMORT]

    activo = df["situacion"] == "Activo"
    dias = (df["fecha_vencimiento"] - corte).dt.days
    vencido = activo & (dias < 0)
    df["dias_para_vencimiento"] = dias
    df["dias_vencido"] = np.where(vencido, -dias, 0)
    df["es_vencido_por_fecha"] = vencido.astype(int)
    df["es_cancelacion_anticipada"] = ((df["situacion"] == "Cancelado") & (dias > 0)).astype(int)
    df["es_mal_clasificado"] = (vencido & (df["estado_contable"] == "Vigente")).astype(int)

    # Rango de vencimiento (solo créditos activos)
    condiciones = [
        ~activo,
        vencido & (-dias > 90),
        vencido & (-dias > 30),
        vencido,
        dias <= 30,
        dias <= 90,
    ]
    etiquetas = ["No aplica", "Vencido > 90 días", "Vencido 31-90 días", "Vencido 1-30 días",
                 "Por vencer 0-30 días", "Por vencer 31-90 días"]
    orden = [7, 1, 2, 3, 4, 5]
    df["rango_vencimiento"] = np.select(condiciones, etiquetas, default="Por vencer > 90 días")
    df["rango_vencimiento_orden"] = np.select(condiciones, orden, default=6)

    # Rango de plazo
    plazo = df["plazo_dias"]
    cond_p = [plazo <= 60, plazo <= 180, plazo <= 270, plazo <= 365]
    df["rango_plazo"] = np.select(cond_p, ["0-60 días", "61-180 días", "181-270 días", "271-365 días"],
                                  default="Más de 365 días")
    df["rango_plazo_orden"] = np.select(cond_p, [1, 2, 3, 4], default=5)
    return df


# ----------------------------------------------------------------- dimensiones
def construir_clientes(df: pd.DataFrame):
    """Cliente por nombre normalizado; las personas naturales se anonimizan."""
    clave = df["NOMBRE O RAZÓN SOCIAL"].map(normalizar_nombre)
    codigos, _ = pd.factorize(clave)
    df = df.copy()
    df["id_cliente"] = codigos + 1
    g = df.assign(clave=clave).groupby("id_cliente").agg(
        nombre=("clave", "first"),
        tipo_persona=("tipo_persona", lambda s: s.mode().iloc[0]),
        n_creditos=("id_registro", "size"),
    )
    anonimo = pd.Series("Persona natural " + g.index.astype(str).str.zfill(5), index=g.index)
    g["cliente"] = g["nombre"].where(g["tipo_persona"].isin(["J", "G"]), anonimo)
    return df, g.reset_index()[["id_cliente", "cliente", "tipo_persona", "n_creditos"]]


def construir_actividades(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for cod in sorted(df["actividad"].unique()):
        seccion, division = cod[0], cod[1:]
        nombre = DIVISIONES.get(division, "Sin descripción")
        filas.append({
            "actividad": cod, "seccion": seccion,
            "seccion_nombre": SECCIONES.get(seccion, "Sin descripción"),
            "division": division, "actividad_nombre": nombre,
            "actividad_etiqueta": f"{cod} - {nombre}",
        })
    return pd.DataFrame(filas)


def construir_entidades(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for e in sorted(df["entidad_federal"].unique()):
        m = re.match(r"\s*(\d+)\s*-\s*(.+)", e)
        codigo, nombre_src = (int(m.group(1)), m.group(2).strip()) if m else (0, e.strip())
        filas.append({"entidad_federal": e, "codigo_entidad": codigo,
                      "entidad": ACENTOS.get(nombre_src.upper(), nombre_src.title()), "pais": "Venezuela"})
    return pd.DataFrame(filas)


def construir_calendario(df: pd.DataFrame, valor_unidad: pd.Series, interpolado: pd.Series) -> pd.DataFrame:
    inicio = df["fecha_aprobacion"].min().normalize()
    fin = pd.Timestamp(year=df["fecha_vencimiento"].max().year, month=12, day=31)
    cal = pd.DataFrame({"fecha": pd.date_range(inicio, fin, freq="D")})
    cal["anio"] = cal["fecha"].dt.year
    cal["trimestre_num"] = cal["fecha"].dt.quarter
    cal["trimestre"] = "T" + cal["trimestre_num"].astype(str)
    cal["mes_num"] = cal["fecha"].dt.month
    cal["mes"] = cal["mes_num"].map(lambda m: MESES[m - 1])
    cal["anio_mes"] = cal["fecha"].dt.strftime("%Y-%m")
    cal["anio_mes_orden"] = cal["anio"] * 100 + cal["mes_num"]
    cal["valor_unidad_bs"] = cal["fecha"].map(valor_unidad)
    cal["valor_unidad_interpolado"] = cal["fecha"].map(interpolado).fillna(False).astype(int)
    return cal


def construir_dimensiones_pequenas(df: pd.DataFrame):
    tipo_credito = pd.DataFrame({"tipo_credito": sorted(df["tipo_credito"].astype(str).unique())})
    tipo_credito["tipo_credito_nombre"] = "Tipo " + tipo_credito["tipo_credito"] + " (sin catálogo)"

    tp = pd.DataFrame({"tipo_persona": sorted(df["tipo_persona"].unique())})
    tp["tipo_persona_nombre"] = tp["tipo_persona"].map(TIPOS_PERSONA).fillna("Sin descripción")

    situacion = pd.DataFrame({
        "situacion": ["Activo", "Cancelado", "Castigado"], "situacion_orden": [1, 2, 3],
        "descripcion": ["Crédito con saldo pendiente", "Crédito pagado en su totalidad",
                        "Crédito dado de baja del balance (castigado)"],
    })
    estado = pd.DataFrame([
        {"estado_contable": v[0], "estado_orden": v[1], "es_cartera_improductiva": v[2],
         "prefijo_cuenta": k} for k, v in ESTADOS_CONTABLES.items()
    ])
    estado["descripcion"] = "Inferido del prefijo de la cuenta contable; confirmar con el catálogo contable"
    return tipo_credito, tp, situacion, estado


# ----------------------------------------------------------------- calidad de datos
def construir_calidad(bruto: pd.DataFrame, df: pd.DataFrame, corte: pd.Timestamp) -> pd.DataFrame:
    n = len(df)
    por_nombre = bruto.groupby("NOMBRE O RAZÓN SOCIAL")["IDENTIFICACIÓN TIPO PERSONA RIF"].nunique()
    constantes = [c for c in bruto.columns if bruto[c].nunique(dropna=False) == 1]
    activos = df["situacion"] == "Activo"
    filas = [
        ("Fecha de corte del reporte", str(corte.date()), "Info", "Es la fecha de situación de todos los créditos."),
        ("Registros", n, "Info", ""),
        ("Número de crédito repetido (filas)", int(df["numero_credito"].duplicated(keep=False).sum()), "Alta",
         "No es llave única; se usa id_registro. Validar con el sistema origen."),
        ("Nombres con más de un RIF distinto", int((por_nombre > 1).sum()), "Alta",
         "El RIF no identifica al cliente en esta muestra; confirmar si está enmascarado."),
        ("Nombres con exactamente 30 caracteres (posible truncamiento)",
         int((bruto["NOMBRE O RAZÓN SOCIAL"].str.len() == 30).sum()), "Media",
         "Pedir el nombre completo o un id de cliente al área de datos."),
        ("Castigados con saldo 0 y amortización 100%", int(((df["situacion"] == "Castigado") & (df["saldo_bs"] == 0)).sum()),
         "Alta", "El monto castigado no queda registrado; se usa el monto original como aproximación."),
        ("Activos con fecha de vencimiento ya pasada", int(df["es_vencido_por_fecha"].sum()), "Alta",
         "Revisar su clasificación y provisión."),
        ("Vencidos por fecha pero con cuenta de cartera vigente", int(df["es_mal_clasificado"].sum()), "Alta",
         "Posible reclasificación pendiente a vencido."),
        ("Cancelados antes de su vencimiento", int(df["es_cancelacion_anticipada"].sum()), "Info",
         "Pagos anticipados."),
        ("Créditos con plazo 0 días", int((df["plazo_dias"] <= 0).sum()), "Media", "Validar fechas de vencimiento."),
        ("Unidades de valor faltantes (se estiman)", int((df["uvc_origen"] == "estimada").sum()), "Media",
         "Completar en el origen."),
        ("Unidades de valor inconsistentes con su fecha (se corrigen)", int((df["uvc_origen"] == "corregida").sum()), "Media",
         "Revisar esos créditos."),
        ("Rubro 'No aplica'", f"{(df['RUBRO'].astype(str).str.strip(chr(34) + ' ') == 'No aplica').mean():.1%}", "Baja",
         "Columna casi vacía; no se modela."),
        ("Columnas constantes (se descartan)", ", ".join(constantes), "Baja", "No aportan información."),
        ("Saldo de activos (suma, Bs nominales)", f"{df.loc[activos, 'saldo_bs'].sum():,.0f}", "Info",
         "Mezcla años; para comparar usar saldo_uvc."),
    ]
    return pd.DataFrame(filas, columns=["hallazgo", "valor", "severidad", "recomendacion"])


# ----------------------------------------------------------------- principal
COLUMNAS_HECHOS = [
    "id_registro", "numero_credito", "id_cliente", "tipo_persona", "actividad", "tipo_credito",
    "entidad_federal", "situacion", "estado_contable", "cuenta_contable",
    "fecha_aprobacion", "fecha_vencimiento", "anio_aprobacion", "plazo_dias",
    "monto_original_bs", "monto_amortizado_bs", "saldo_bs", "pct_amortizacion",
    "monto_uvc", "saldo_uvc", "uvc_origen",
    "dias_para_vencimiento", "dias_vencido", "es_vencido_por_fecha", "es_cancelacion_anticipada",
    "es_mal_clasificado", "rango_vencimiento", "rango_vencimiento_orden", "rango_plazo", "rango_plazo_orden",
    "monto_relativo_anio", "cluster", "cluster_nombre", "pca_1", "pca_2",
]


def construir_modelo(entrada: Path, k: int = K_FINAL) -> dict[str, pd.DataFrame]:
    bruto = cargar_datos(entrada)
    df = preparar_variables(bruto)
    df, _scaler, _modelo, _pca, metricas = entrenar(df, k)
    perfil = construir_perfil(df)
    centroides = construir_centroides(_scaler, _modelo, df)

    corte = EXCEL_EPOCH + pd.to_timedelta(int(df[COL_CORTE].max()), unit="D")
    df["tipo_credito"] = df["tipo_credito"].astype(str)
    df, valor_unidad, interpolado = agregar_unidades_de_valor(df)
    df = agregar_indicadores(df, corte)
    df, dim_cliente = construir_clientes(df)

    tipo_credito, tipo_persona, situacion, estado = construir_dimensiones_pequenas(df)
    return {
        "fact_creditos": df[COLUMNAS_HECHOS],
        "dim_calendario": construir_calendario(df, valor_unidad, interpolado),
        "dim_cliente": dim_cliente,
        "dim_actividad": construir_actividades(df),
        "dim_entidad_federal": construir_entidades(df),
        "dim_tipo_credito": tipo_credito,
        "dim_tipo_persona": tipo_persona,
        "dim_situacion": situacion,
        "dim_estado_contable": estado,
        "perfil_clusters": perfil.round(3),
        "centroides": centroides.round(3),
        "metricas_k": metricas.round(4),
        "calidad_datos": construir_calidad(bruto, df, corte),
    }


def exportar(tablas: dict[str, pd.DataFrame], salida: Path) -> None:
    salida.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(salida, engine="openpyxl", datetime_format="yyyy-mm-dd") as w:
        for nombre, tabla in tablas.items():
            tabla.to_excel(w, sheet_name=nombre, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el modelo de datos en estrella para Power BI")
    parser.add_argument("--entrada", type=Path, default=ENTRADA)
    parser.add_argument("--salida", type=Path, default=SALIDA)
    parser.add_argument("--k", type=int, default=K_FINAL, help="número de clusters")
    args = parser.parse_args()

    tablas = construir_modelo(args.entrada, args.k)
    exportar(tablas, args.salida)

    print(f"Modelo guardado en: {args.salida}")
    for nombre, t in tablas.items():
        print(f"  {nombre:22s} {len(t):>7,} filas x {t.shape[1]:>2} columnas")


if __name__ == "__main__":
    main()

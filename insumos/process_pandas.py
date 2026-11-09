import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt



def process_pandas(dicc,df):

    msg={"status":False}
   
    df.to_csv(Path(dicc["file_csv"]), index=False)
    
    df = pd.read_csv(dicc["file_csv"], header=0)

    if not df.empty:
        print("Estoy exportando la data a un archivo csv")
        print("=" * 60)
        print("=" * 60)
        print("Lei Correctamente el dataframe......")
        msg["status"]=True

    print("=" * 60)
    print("Caracteristicas el dataframe......")
    print("=" * 60)
    print("=" * 60)    
    
    print("primeros 10 registros del dataframe......")
    print("=" * 60)    
    print(df.head(10)) 
    df.shape

    print("=" * 60)
    print("Metadata del dataframe......")
    print("=" * 60)    
    df.info()     

    print("******************PASO 2 ***************")
    print("Mira una muestra, no todo el archivo ")

    print(df.sample(10, random_state=1))

    print("******************PASO 2 ***************")
    print("Data frame no ordenado")

    print("=" * 60)
    print("*" * 60)
    print("**********Duplicados por identificador*******")
    print("*" * 60)
    print("Mira una muestra, no todo el archivo ")

    df_id=df["id_operacion"].duplicated().sum()

    duplicados = df[df["id_operacion"].duplicated(keep=False)]
    
    if df_id>0:
        print(f" ¿Cuántos identificadores duplicados detectas? : {df_id}")
        print("-" * 60)   
        print(f"Id duplicado {duplicados}")

    
    print("=" * 60)   
    print("**********Después, localiza las filas involucradas: *******")
    df_id_uni   = df[df["id_operacion"].duplicated(keep=False)].sort_values("id_operacion") 
    cant_id_uni = df_id_uni.duplicated().sum()

    if cant_id_uni==0:
        print(f"Cantidad de id_operacion duplicados: {cant_id_uni}") 
        print("Se han eliminado los duplicados") 

            
    print("*" * 60)
    print("**********Campos vacíos *******")
    print("*" * 60)
    df_null= df.isna()
    print("Muestra de registros nulos")
    print(df_null.head(5))
    print("*" * 60)
    print(f"Cantidad de registros nulos {len(df_null)}")
    print("=" * 60)
    print("¿Cuántos valores faltantes hay en canal? ")
    canal_null=df[df["canal"].isna()]
    print(f"Catidad.....{len(canal_null)}")
    print(f"Regsitro.............")  
    print(f"{canal_null}")

    print("=" * 60)
    print("**********Operaciones superiores a 5.000  *******")
    print("=" * 60)
      
    altas = df[df["monto"] > 5000] 
    altas[["id_operacion", "sucursal", "tipo_operacion", "monto", "estado"]]

    print("********** ¿Cuántas operaciones superan 5.000?   *******")
    print(f"Catidad.....{len(altas)}")
    print(f"Regsitro(s).............")  
    print(f"{altas}")

    sucursal_monto = altas.loc[altas["monto"].idxmax()]

    print(f"Monto mayor : {sucursal_monto["monto"]}")
    print(f"Sucursal : {sucursal_monto["sucursal"]}")
    print("=" * 60)
    print("**********Solo operaciones pendientes  *******")
    print("=" * 60)
    pendientes = df[df["estado"] == "Pendiente"] 
    pendientes.shape
    num_filas = pendientes.shape[0] 
    
    print("Muestra")
    print(pendientes.head(5))
    print(f"Cantidad de registros pendiente : {num_filas}")

    
    print("=" * 60)
    print("**********  Combina dos condiciones  *******")
    print("=" * 60)
    
    df_com= df[(df["estado"] == "Pendiente") & (df["monto"] > 1000)] 

    print(df_com.head(5))
    
    print("=" * 60)
    print("**********  Monto total por sucursal   *******")
    print("=" * 60)
    por_sucursal = (df.groupby("sucursal")["monto"].sum().sort_values(ascending=False))

    print(" ¿Qué sucursal aparece de primera?")
    print(por_sucursal)

    sucursal_mayor = por_sucursal.idxmax()
    monto_mayor = por_sucursal.max()
    print("=" * 60)
    print(f"Sucursal: {sucursal_mayor}")
    print(f"Monto: {monto_mayor}")

    print("=" * 60)
    print("**********  Cantidad de operaciones por estado   *******")
    print("=" * 60)
    
    df_estado = df["estado"].value_counts() 

    print(df_estado)
    
    
    print("=" * 60)
    print("**********  Cantidad por tipo de operación    *******")
    print("=" * 60)

    print(df["tipo_operacion"].value_counts())


    print("=" * 60)
    print("**********  Calcula dos medidas sobre la misma columna    *******")
    print("=" * 60)

    media = df["monto"].mean() 
    mediana = df["monto"].median() 
    print("Media:", media) 
    print("Mediana:", mediana)

    print("=" * 60)
    print("**********  Busca el máximo     *******")
    print("=" * 60)
    max  = df.loc[df["monto"].idxmax()] 
    print(max)

    print("=" * 60)
    print("**********  Comprueba su efecto     *******")
    print("=" * 60)
    
    sin_maximo = df[df["monto"] < df["monto"].max()] 
    print("Media sin máximo:", sin_maximo["monto"].mean()) 
    print("Mediana sin máximo:", sin_maximo["monto"].median())    

    print("=" * 60)
    print("**********  Barras por sucursal     *******")
    print("=" * 60)
    por_sucursal.plot(kind="bar") 
    plt.title("Monto total por sucursal") 
    plt.xlabel("Sucursal") 
    plt.ylabel("Monto total") 
    plt.tight_layout() 
    plt.show()
    

    print("=" * 60)
    print("**********  Histograma de montos     *******")
    print("=" * 60)

    plt.hist(df["monto"], bins=20) 
    plt.title("Distribución de montos") 
    plt.xlabel("Monto") 
    plt.ylabel("Cantidad de operaciones") 
    plt.show() 

    resumen = { 
        "filas": len(df), 
        "media_monto": df["monto"].mean(), 
        "mediana_monto": df["monto"].median(), 
        "operaciones_mayores_5000": (df["monto"] > 5000).sum(), 
        "ids_duplicados": df["id_operacion"].duplicated().sum() 
        } 
    
    print(resumen)
            
    
    return msg
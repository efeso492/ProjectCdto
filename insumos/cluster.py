import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder
from sklearn.decomposition import PCA
from sklearn.metrics import classification_report,confusion_matrix
from sklearn.datasets import make_blobs
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import silhouette_score
from sklearn.metrics import calinski_harabasz_score

    #%matplotlib inline


def cluster(dicc):
#data=make_blobs(n_samples=200,n_features=2,centers=4,cluster_std=1.8,random_state=101)
    columnas =["id_cdto","Entidad_federal","tipo_id","nro_id","nom_clte",
           "act_econ","col1","col2","tipo_cdto","fch_aproba","fch_liquidacion",
           "fch_vencimiento","mto_bs","mto_petro","dest_recursos","col3",
           "mto_liq_bs","mto_divisas","mto_divisas_petro","col4","col5",
           "genero","cta_contable","col6","col7","proyec_cpun",
           "col8","col9","col10","col11"]

    #kmeans = KMeans(n_clusters=2)
    #le = LabelEncoder()

    df                    = pd.read_csv(dicc["file_inputs"],sep="~",names=columnas)
    
    df["fch_aproba"]      = pd.to_datetime(df["fch_aproba"].astype(str),format="%Y%m%d")

    df["fch_vencimiento"] = pd.to_datetime(df["fch_vencimiento"].astype(str),format="%Y%m%d")

    df["plazo_dias"]      = (df["fch_vencimiento"] - df["fch_aproba"]).dt.days
    
    df["plazo_meses"]     = ((df["fch_vencimiento"].dt.year - df["fch_aproba"].dt.year) * 12 + (df["fch_vencimiento"].dt.month - df["fch_aproba"].dt.month))
    #print(df["plazo_meses"].dtype)
    
    df_new                = df[["Entidad_federal","tipo_id","act_econ","tipo_cdto","plazo_meses","mto_bs","genero"]].copy()  
       
    df_new["mto_bs"]      = (df_new["mto_bs"].str.replace(",", ".", regex=False).astype(float))

    df_new                = pd.get_dummies(df_new,columns=["act_econ","tipo_cdto","tipo_id","Entidad_federal","genero"],drop_first=True,dtype=int)
    
    # Proceso de Escalado
    scaler = StandardScaler()
    #df_new["act_econ"] = le.fit_transform(df_new["act_econ"])
    #df_new["tipo_cdto"] = le.fit_transform(df_new["tipo_cdto"])
    #df_new["tipo_id"] = le.fit_transform(df_new["tipo_id"])
    X = scaler.fit_transform(df_new)

    #print(X)
    #exit()
    
    mejor_k = 0
    mejor_score = -1


    for k in range(2, 11):

        kmeans = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=10
        )
        labels = kmeans.fit_predict(X)
        score = silhouette_score(X, labels)
        print(f"k={k} -> score={score:.4f}")
        if score > mejor_score:
            mejor_score = score
            mejor_k = k
            
    print(f"k={k} -> mejor score={mejor_score:.4f}")
          
    
    
    kmeans = KMeans(
    n_clusters=mejor_k,
    random_state=42,
    n_init=10)
    
    df_new["cluster"] = kmeans.fit_predict(X)    
    
    print(df_new["cluster"].value_counts())

    kmeans.cluster_centers_
    print(kmeans.cluster_centers_
    )

    resumen = (
    df_new.groupby("cluster")
          .agg(
              monto_promedio=("mto_bs","mean"),
              plazo_promedio=("plazo_meses","mean"),
              cantidad=("cluster","count")
          )
    )

    print(resumen)

    score = silhouette_score(X, kmeans.labels_)
    #Cercano a 1  -> muy bueno
    #Cercano a 0  -> grupos superpuestos
    #Menor que 0  -> mala agrupación

    print(f"Silhouette Score: {score:.4f}")
    score = calinski_harabasz_score(X,kmeans.labels_)

    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)
    plt.figure(figsize=(10,6))

    plt.scatter(X_pca[:,0],X_pca[:,1],c=df_new["cluster"],cmap="viridis"    )
    plt.xlabel("Componente 1")
    plt.ylabel("Componente 2")
    plt.title("Clusters de Clientes")
    plt.colorbar(label="Cluster")
    #plt.show()

    for i, var in enumerate(pca.explained_variance_ratio_, start=1):
        print(f"Componente {i}: {var*100:.2f}%")


    #Más alto es mejor.
    exit()
    
    
    #kmeans.fit(df.drop('Private', axis=1))

    
    
    
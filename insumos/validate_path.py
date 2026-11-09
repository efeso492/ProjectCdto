from pathlib import Path
import shutil
import sys
from time import perf_counter

#verify_path(ruta_pdf: str):
def verify_path(ruta_pdf: Path):

    msg={"status":False,
         "path":"",
         "path_basic":"",
         "file_csv":""}
    
    PDF = "DATOS.pdf"
    CSV = "DATOS.csv"

    #BASE_DIR = Path(__file__).resolve().parent

    DIR_PDF = ruta_pdf / "pdf" 
    DIR_INP = ruta_pdf / "inputs" 
    DIR_CSV = ruta_pdf / "csv" 

    if not DIR_PDF.is_dir():
        print(f"Error: no existe la carpeta de entrada: {DIR_PDF}")
        #ermina la función actual y devuelve el valor 1.
        print("Process aborteddd")
        exit() 
    else:
        print("Buenas noticias... puedes continuar")
        print("el folder pdf existe....")
        msg["status"]=True

    if not DIR_INP.is_dir():
        print(f"Error: no existe la carpeta de entrada: {DIR_INP}")
        #ermina la función actual y devuelve el valor 1.
        print("Process aborteddd")
        exit() 
    else:
        print("Buenas noticias... puedes continuar")
        print("el folder inputs existe....")
        msg["status"]=True



    if not DIR_CSV.is_dir():
        print(f"Error: no existe la carpeta de entrada: {DIR_CSV}")
        #ermina la función actual y devuelve el valor 1.
        print("Process aborteddd")
        exit() 
    else:
        print("Buenas noticias... puedes continuar")
        print("el folder csv existe....")
        msg["status"]=True

    
    
    archivo     =   DIR_PDF / PDF
    archivo_csv =   DIR_CSV / CSV

    file_inputs = list(DIR_INP.glob("*.txt"))    
             
    

    if len(file_inputs)==1:
        archivo_input=file_inputs[0].resolve()
        msg["file_inputs"]=archivo_input
        msg["status_file_inputs"]=True
        print(f"Archivo encontrado: {archivo_input}")
    elif len(file_inputs) == 0:
        print("No se encontró ningún archivo TXT")
    else:
        print(f"Se encontraron {len(file_inputs)} archivos")
    
    


    if archivo.is_file():
        print("el archivo Exite ")
        msg["status"]=True
        msg["path"] = archivo
        msg["file_csv"]=archivo_csv 
        return msg
    else:
        print("el archivo no Exite ")
        return msg
        exit(1)

        

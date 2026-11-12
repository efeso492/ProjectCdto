from pathlib import Path
import json
from .tools import *
import sys
from .logs import *

class ConfigError(Exception):
    """Error al leer o validar el archivo de configuración."""
def config():

    logs = configurar_logger()
    BASE       = Path(__file__).resolve().parent.parent / "confi"
    BASE_RAIZ = Path(__file__).resolve().parent.parent

    path = BASE  / "configuration.json"

    print(path)
    try:
        with path.open(encoding="utf-8") as f:
            jsonData = json.load(f)
    
        for folder in jsonData["folder"]:
            
            path         = BASE_RAIZ / folder
            path_verifay = path_checker(folder, path)
            if path_verifay:
                jsonData[folder] = path_verifay
            logs.info(f"folder: {folder} . Exist..")  

        
        
        if not isinstance(jsonData['ext'], str):
            logs.info(jsonData['at_name'] + "  is not an string.")
            logs.info("==> Process aborted...")
            sys.exit(1)
        #
        if not isinstance(jsonData['ext_pbix'], str):
            logs.info(jsonData['at_name'] + "  is not an string.")
            logs.info("==> Process aborted...")
            sys.exit(1)
        #
        if len(jsonData['archivos']) <= 0 :
            logging.error("==> The database connection credentials were not found.")
            logging.error("==> Process aborted...")
            sys.exit(1)
        #
        SQL_list = [p.name for p in (jsonData["sql"]).iterdir()]
        if len(SQL_list) <= 0 :
            logging.error(f"==> The SQL Queries folder {jsonData['sql']} it's empty, please checkit.") 
            logging.error("==> Process aborted...")
            sys.exit(1)
        
        queries_data={} 
        for query in  jsonData['lis_sql']: 
            q_name, __ = query.split(".")
            if not query in SQL_list:
                logs.error(f"==> Consulta SQL -- {q_name} -- no se encuentra en el directorio, por favor revise el directorio {jsonData['queriesPath']} y el archivo de confirugración") 
                sys.exit(1)
            RUTA = jsonData['sql'] / query
            queries_data[q_name] = openQuery(RUTA)

        if queries_data:
            jsonData['sql']=queries_data

        
    except FileNotFoundError as e:
        raise ConfigError(f"Archivo de configuración no encontrado: '{path}'") from e
    except PermissionError as e:
        raise ConfigError(f"Sin permisos para leer: '{path}'") from e
    except json.JSONDecodeError as e:
        raise ConfigError(
            f"JSON inválido en '{path}' (línea {e.lineno}, columna {e.colno}): {e.msg}"
        ) from e
    except OSError as e:
        raise ConfigError(f"Error al leer '{path}': {e}") from e

    if not isinstance(jsonData, dict):
        raise ConfigError(f"Se esperaba un objeto JSON en '{path}', se recibió {type(jsonData).__name__}")

    return jsonData


    
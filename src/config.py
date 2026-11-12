from pathlib import Path
import json
from .tools import *

class ConfigError(Exception):
    """Error al leer o validar el archivo de configuración."""
def config():

    BASE = Path(__file__).resolve().parent.parent / "confi"

    path = BASE  / "configuration.json"

    print(path)
    try:
        with path.open(encoding="utf-8") as f:
            jsonData = json.load(f)
    
    
    
    
    
    
    
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


    
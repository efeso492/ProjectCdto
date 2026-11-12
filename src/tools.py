from pathlib import Path
from .logs import configurar_logger


def path_checker(name: str, value: str | Path) -> Path:


    logs = configurar_logger()
    """
    Verifica que un directorio exista; si no, lo crea (incluyendo padres).
    Args:
        name: Nombre descriptivo de la ruta (para mensajes).
        value: Ruta del directorio.
    Returns:
        Path: Ruta como objeto Path, garantizada como directorio existente.
    Raises:
        NotADirectoryError: Si la ruta existe pero es un archivo.

    TODO: Propiedad de Mercantil Banco :-)
    """
    path = Path(value).expanduser()

    if path.exists() and not path.is_dir():
        raise NotADirectoryError(f"{name}: '{path}' existe pero no es un directorio")

    if not path.exists():
        logs.info("%s: ruta no encontrada, creando '%s'", name, path)
        path.mkdir(parents=True, exist_ok=True)

    return path

class SQLFileError(Exception):
    """Error al leer o validar un archivo SQL."""


def open_query(query_file: str | Path, encoding: str = "utf-8") -> str:
    """
    Lee un archivo SQL y devuelve su contenido.

    Raises:
        SQLFileError: si el archivo no existe, no se puede leer o está vacío.

    TODO: Propiedad de Mercantil Banco :-)
    """
    path = Path(query_file).expanduser()

    try:
        query = path.read_text(encoding=encoding).strip()
    except FileNotFoundError as e:
        raise SQLFileError(f"Archivo SQL no encontrado: '{path}'") from e
    except IsADirectoryError as e:
        raise SQLFileError(f"La ruta es un directorio, no un archivo: '{path}'") from e
    except PermissionError as e:
        raise SQLFileError(f"Sin permisos para leer: '{path}'") from e
    except UnicodeDecodeError as e:
        raise SQLFileError(f"Error de codificación ({encoding}) en '{path}': {e}") from e
    except OSError as e:
        raise SQLFileError(f"Error al leer '{path}': {e}") from e

    if not query:
        raise SQLFileError(f"El archivo SQL está vacío: '{path}'")

    return query
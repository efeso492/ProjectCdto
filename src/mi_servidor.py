#from mcp.server.mcpserver import MCPServer
#mcp = MCPServer("MisHerramientasPython")


"""
mi-python-mcp: servidor MCP para trabajar con el entorno virtual de Python activo.

Usa sys.executable, así que opera sobre el venv desde el que se lanza el servidor.
Requisito: pip install "mcp[cli]"
"""
import os
import re
import subprocess
import sys
from pathlib import Path

#from mcp.server.fastmcp import FastMCP
#mcp = FastMCP("mi-python-mcp")

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("MisHerramientasPython")


# Carpeta de trabajo: todo lo que se lea/escriba/ejecute queda confinado aquí.
# Puedes cambiarla con la variable de entorno MCP_WORKSPACE.
WORKSPACE = Path(os.environ.get("MCP_WORKSPACE", Path.home() / "mcp_workspace")).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)

TIMEOUT_SEG = 60          # tiempo máximo por comando
MAX_SALIDA = 20000        # caracteres máximos devueltos
PATRON_PAQUETE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._\-]*(\[[A-Za-z0-9,_\-]+\])?"
    r"((==|>=|<=|~=|!=|<|>)[A-Za-z0-9.*+!_\-]+)?$"
)


def _ruta_segura(ruta: str) -> Path:
    """Resuelve la ruta dentro del workspace y bloquea escapes (../)."""
    destino = (WORKSPACE / ruta).resolve()
    if not destino.is_relative_to(WORKSPACE):
        raise ValueError(f"Ruta fuera del workspace: {ruta}")
    return destino


def _ejecutar(cmd: list[str], timeout: int = TIMEOUT_SEG) -> str:
    try:
        r = subprocess.run(
            cmd, cwd=WORKSPACE, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return f"Error: el comando superó el límite de {timeout} s."
    salida = f"[código de salida: {r.returncode}]\n"
    if r.stdout:
        salida += f"--- stdout ---\n{r.stdout}\n"
    if r.stderr:
        salida += f"--- stderr ---\n{r.stderr}\n"
    if len(salida) > MAX_SALIDA:
        salida = salida[:MAX_SALIDA] + "\n... [salida truncada]"
    return salida


@mcp.tool()
def prueba_conexion(mensaje: str) -> str:
    """Devuelve un saludo para confirmar que el servidor MCP funciona."""
    return f"Conexión exitosa. Recibido: {mensaje}"


@mcp.tool()
def info_entorno() -> str:
    """Muestra el intérprete de Python, la versión, el venv y el workspace en uso."""
    return (
        f"Python: {sys.executable}\n"
        f"Versión: {sys.version}\n"
        f"Entorno virtual: {os.environ.get('VIRTUAL_ENV', sys.prefix)}\n"
        f"Workspace: {WORKSPACE}"
    )


@mcp.tool()
def ejecutar_codigo(codigo: str) -> str:
    """Ejecuta código Python en el venv (dentro del workspace) y devuelve stdout/stderr."""
    return _ejecutar([sys.executable, "-c", codigo])


@mcp.tool()
def ejecutar_script(archivo: str) -> str:
    """Ejecuta un archivo .py que esté dentro del workspace."""
    ruta = _ruta_segura(archivo)
    if ruta.suffix != ".py" or not ruta.is_file():
        return "Error: indica un archivo .py existente dentro del workspace."
    return _ejecutar([sys.executable, str(ruta)])


@mcp.tool()
def listar_paquetes() -> str:
    """Lista los paquetes instalados en el entorno (pip list)."""
    return _ejecutar([sys.executable, "-m", "pip", "list", "--format=columns"])


@mcp.tool()
def instalar_paquete(paquete: str) -> str:
    """Instala un paquete con pip. Acepta nombre y versión, p. ej. 'requests==2.32.3'."""
    if not PATRON_PAQUETE.match(paquete):
        return "Error: nombre de paquete no válido."
    return _ejecutar([sys.executable, "-m", "pip", "install", paquete], timeout=300)


@mcp.tool()
def desinstalar_paquete(paquete: str) -> str:
    """Desinstala un paquete con pip (sin pedir confirmación)."""
    if not PATRON_PAQUETE.match(paquete):
        return "Error: nombre de paquete no válido."
    return _ejecutar([sys.executable, "-m", "pip", "uninstall", "-y", paquete])


@mcp.tool()
def listar_archivos(subcarpeta: str = ".") -> str:
    """Lista archivos y carpetas dentro del workspace."""
    carpeta = _ruta_segura(subcarpeta)
    if not carpeta.is_dir():
        return "Error: la carpeta no existe."
    items = sorted(carpeta.iterdir(), key=lambda p: (p.is_file(), p.name))
    return "\n".join(f"{'[D]' if p.is_dir() else '[F]'} {p.name}" for p in items) or "(vacía)"


@mcp.tool()
def leer_archivo(archivo: str) -> str:
    """Lee un archivo de texto del workspace."""
    ruta = _ruta_segura(archivo)
    if not ruta.is_file():
        return "Error: el archivo no existe."
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    return texto[:MAX_SALIDA] + ("\n... [truncado]" if len(texto) > MAX_SALIDA else "")


@mcp.tool()
def escribir_archivo(archivo: str, contenido: str) -> str:
    """Crea o sobrescribe un archivo de texto dentro del workspace."""
    ruta = _ruta_segura(archivo)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")
    return f"Archivo guardado: {ruta.relative_to(WORKSPACE)} ({len(contenido)} caracteres)"


if __name__ == "__main__":
    mcp.run()  # transporte stdio
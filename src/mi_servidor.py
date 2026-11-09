from mcp.server.mcpserver import MCPServer

mcp = MCPServer("MisHerramientasPython")

@mcp.tool()
def prueba_conexion(mensaje: str) -> str:
    """Devuelve un saludo para confirmar que el servidor MCP funciona."""
    return f"Conexión exitosa. Recibido: {mensaje}"

if __name__ == "__main__":
    mcp.run()
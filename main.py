import logging
from logging.handlers import RotatingFileHandler
from typing import Any, Iterable, List, Tuple
from src.connection_impala import *
from src.config import config
from src.logs import configurar_logger

#from impala.util import as_pandas

def main():

    logs = configurar_logger()
    dicc_main = config()

    if dicc_main:    
        logs.info("dicc_main")

    return print("Hola mundo")

main()


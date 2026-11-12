from datetime import date, time, datetime, timedelta
from decimal import Decimal
import os
import pandas as pd
#import puretransport
#from pyhive import hive
#from sqlalchemy import create_engine
#import sqlalchemy as sa
#import bd_connection as bd
#from impala.dbapi import connect
#from impala.util import as_pandas
#
#
class Connection_hive_impala:

    def __init__(self, credentials,logs):
        self.server = credentials["SERVER"]
        self.kinit_user = credentials["KINIT_USER"]
        self.kinit_pswd = credentials["KINIT_PASSWORD"]
        self.logs = logs

    def impala_hive_consult_all(self, query):
        #
        try:
            star_time = datetime.now()
            #
            self.logs.info("--> Iniciando coneccion regular con IMPALA ")
            #
            
            #"""
            #if  self.server == "dev":
              #  self.logs.info("--> Apuntando al servidor de desarrollo ")
              #  server = bd.DevelopmentConnectionFactory()
           # else:
               # self.logs.info("--> Apuntando al servidor de produccion ")
             #   server = bd.ProductionConnectionFactory()
            
            
            #conn = bd.DataBaseHue(
             #   self.kinit_user ,
              #  self.kinit_pswd ,
              #  server
           # ).connection()
            #"""
            #
            conn = bd.Client('PROD')

            self.logs.info("--> Estableciendo cursor")
            cursor = conn().cursor()
            #
            self.logs.info("--> Ejecutando consulta Sql")
            cursor.execute(query)
            columnas = [desc[0] for desc in cursor.description]  
            #data = cursor.fetchall()
            #
             
            self.logs.info("--> Esperando respuesta de la BD ...")
            
            for fila in cursor:
              if fila is None:
                return None  
              elif "cannot recognize input near" in fila or 'error' in fila:
                raise Exception("El query esta mal redactado")
              else:
                
                yield fila
            #
            #
            #
            end_time = datetime.now()
            total = datetime.timestamp(end_time) - datetime.timestamp(star_time)
            time=Decimal(str(total)).quantize(Decimal('.01'))
            self.logs.info(f" Total consultation time day review: {time} seconds") 
            #
            #
            conn.disconnect()
            
        except Exception as e:
            return(f"--> Error consultando BD, descripcion: {e}")
            
    def impala_hive_consult_one(self, query):
        #
        try:
            start = datetime.now()
            #
            self.logs.info("--> Iniciando coneccion regular con IMPALA ")
            #
            
            #"""
            #if  self.server == "dev":
              #  self.logs.info("--> Apuntando al servidor de desarrollo ")
              #  server = bd.DevelopmentConnectionFactory()
           # else:
               # self.logs.info("--> Apuntando al servidor de produccion ")
             #   server = bd.ProductionConnectionFactory()
            
            
            #conn = bd.DataBaseHue(
             #   self.kinit_user ,
              #  self.kinit_pswd ,
              #  server
           # ).connection()
            #"""
            #
            conn = bd.Client('PROD')


            self.logs.info("--> Estableciendo cursor")
            cursor = conn().cursor()
            #
            self.logs.info("--> Ejecutando consulta Sql")
            cursor.execute(query)

            data = cursor.fetchone()
            #
            self.logs.info("--> Esperando respuesta de la BD ...")
            
            '''
            if fetch_type == 'one':
                self.logs.info("--> Consulta con FetchOne")
                data = cursor.fetchone()
            elif fetch_type == 'all':
                self.logs.info("--> Consulta con FetchAll")
                data = cursor.fetchall()
            else:
                raise Exception (f"El tipo de fetch que recibe no es el correcto: {fetch_type}")
            '''
            #
            if not data:
                return None
            #
            #
            if "cannot recognize input near" in data or 'error' in data:
                raise Exception("El query esta mal redactado")
            #
            end=datetime.now()
            total = datetime.timestamp(end) - datetime.timestamp(start)
            time=Decimal(str(total)).quantize(Decimal('.01'))
            self.logs.info(f" Total consultation time day review: {time} seconds")
            #
            #
            conn.disconnect()
            return data
        except Exception as e:
            return(f"--> Error consultando BD, descripcion: {e}")        

    def impala_pandas_hive_consult(self, query):
        try:
            starttime_conection_BD = time.perf_counter()
            #
            self.logs.info("--> Iniciando coneccion regular con IMPALA ")
            #
            if  self.server == "dev":
                self.logs.info("--> Apuntando al servidor de desarrollo ")
                server = bd.DevelopmentConnectionFactory()
            else:
                self.logs.info("--> Apuntando al servidor de produccion ")
                server = bd.ProductionConnectionFactory()
            #
            conn = bd.DataBaseHue(
                self.kinit_user ,
                self.kinit_pswd ,
                server
            ).connection()
            #
            data_df = pd.read_sql(query, conn)
            #
            endtime_conection_BD = (time.perf_counter() - starttime_conection_BD) / 60
            self.logs.info(f"-->  {round(endtime_conection_BD , 2 )} Min   Tiempo de consulta")
            #
            self.logs.info("--> Cerrando conexion a hive")
            conn.close()  # Cierra la conexion
            # return data[0]
            return data_df
        except Exception as e:
            return(f"--> Error consultando BD, descripcion: {e}")
        # --
    # --

class Connection_hive:
    #
    def __init__(self, credentials,  logs):
        self.host = credentials["HOST"]
        self.port = credentials["PORT"]
        self.user = credentials["USERNAME"]
        self.password = credentials["PASSWORD"]
        self.db = credentials["DATABASE_NAME"]
        self.logs = logs
    #

    def connect(self):
        """
            Connects to Hive data base
            Args:
                credentials: database credentials
                logs: obejt loggings
            Returns:
                connection
        """
        self.logs.getLogger('pyhive').setLevel(self.logs.CRITICAL) 
        try:
            transport = puretransport.transport_factory(
                host = self.host,
                port = self.port,
                username = self.user,
                password = self.password
            )
            conn= hive.connect(username=self.user,  thrift_transport=transport,database=self.db)
            self.logs.info("--> Conectado a la Base de datos Satisfactoriamente")
            return conn
        except Exception as err:
            self.logs.error(f'--> Error connectandose a la base de datos: {err}') 
            exit(1)
            

    def alchemy_connect(self):
        self.logs.getLogger('pyhive').setLevel(self.logs.INFO)
        try:
            engine_url = f"hive://{self.user}@{self.host}:{self.port}/{self.db}"
            engine = sa.create_engine(engine_url)
            self.logs.info("--> Conectado a la Base de datos Satisfactoriamente usando SQL-ALCHEMY")
            return engine
        except Exception as err:
            self.logs.error(f"--> Error conectandose a la Base de datos: {err}") 
            exit(1)

    def cursor(self):
        """
        Devuelve un cursor para realizar consultas

        Returns:
            cursor
        """
        # return self.dbconn.cursor()
        return self.cursor()

    def close(self):
        """
            cierra la conexion
        """
        if hasattr(self, 'conn') and self.conn is not None:  # Check if connection exists
            try:
                self.logs.info("--> Closing Hive connection")  # Inform about connection closure
                self.conn.close()  # Close the connection
            except Exception as err:
                self.logs.error(f"--> Error closing connection: {err}")  # Log any errors
            finally:
                self.conn = None  # Set connection to None to indicate closure
        else:
            self.logs.info("--> Connection already closed")  # Log if already closed

    def hive_consult(self, query, fetch_type='all'):
        try:
            self.logs.info("--> Instancia de conexion sencilla a hive")
            conn = self.connect()   #instancio  conexion sencilla
            cursor = conn.cursor()  #instancio cursor
            self.logs.info("--> Ejecutando consulta Sql")
            cursor.execute(query)  # Usa self.query para ejecutar a la consulta
            #
            if fetch_type == 'one':
                self.logs.info("--> Consulta con FetchOne")
                data = cursor.fetchone()
            else:
                self.logs.info("--> Consulta con FetchAll")
                data = cursor.fetchall()
            #
            self.logs.info("--> Cerrando conexion a hive")
            cursor.close()  # Cierra el cursor
            conn.close()  # Cierra la conexion
            #
            return data
        except Exception as e:
            self.logs.error(f"Error consultando BD, descripcion: {e}") 
            exit(1)

    def alchemy_pandas_hive_consult(self,query):
        try:
            self.logs.info("--> Hive connection instance with SQLAlchemy and Pandas")  
            conn = self.alchemy_connect()
            self.logs.info("--> Hive consult instance")
            dataframe = pd.read_sql(query, conn)
            return dataframe
        except Exception as e:
            self.logs.error(f"Error consultando BD, descripcion: {e}") 
            exit(1)



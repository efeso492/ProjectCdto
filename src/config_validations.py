import sys
import os 
import logging
from logging.handlers import RotatingFileHandler
import json 
from decimal import * 
import os.path
import datetime
# import re
# from Lib.JSON_open import JSON_reader  
  

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)
    # --
# 
def validateFile(value,logs=False): 
    if os.path.isfile(value) == False:  
        if logs == False: 
            print("") 
            print (f"--> {value} file not found") 
            return False   
        logs.error(f"{value} agent config file not found")
        return False
    else:
        return  value

def validateDate( param_date):
    try: 
        # Convierte la fecha inicial a un objeto datetime
        start_date = datetime.datetime.strptime(param_date, "%Y%m%d") 
        # Convierte el objeto datetime a una cadena de texto en formato YYYYmmdd
        start_date_formatted = start_date.strftime("%Y%m%d").strip() 
        return start_date_formatted
    except Exception as e:
        print(f"Wrong date {param_date}, descrpt: {e}")
        return False

def pathChecker(name, value):
    """
        Checking path
        TODO: Propiedad de Mercantil Banco :-)    
    """ 
    if (os.path.isdir(value) == False): 
        print(name + " path file not found, creating as new path") 
        os.mkdir(value) 
        pathChecker(name, value)
    # --
# 
def intChecker(name, value):
    """
        Checking integer value
        TODO: Propiedad de Mercantil Banco :-)    
    """
    if value is None or value == 0 or not isinstance(value, int):
        print(name + " - is not an integer or is  null/zero")
        sys.exit(1)
    # --
# 
def openQuery(query_file, logs): 
    try:
        with open(query_file, "r") as f:
            query = f.read() 
            f.close()             
            if query  : 
                return query 
            else:  
                print("...") 
                logs.error(f"==> SQL file  '{query_file}' it's empty.") 
                logs.error("==> Process aborted...")
                exit(1)
            #
        #                
    except Exception as e: 
        print("...") 
        logs.error(f"==> Error in SQL file: '{query_file}', descrp:  {str(e)}.")
        logs.error("==> Process aborted...")
        exit(1)
    # --
#         
def config(configfile_path):   
     
    jsonData = False 
    
    try: 
        file = open(configfile_path)
        jsonData = json.load(file) 
        file.close()  
    except Exception as e: 
        print("...")
        trace_back = sys.exc_info()[2]
        line = trace_back.tb_lineno
        print("==> Error in line: " + str(line))
        print(f"==> Config file error message: {e}.")
        print("==> Process aborted...")
    # 
    
    if jsonData == False:
        print("") 
        print ("Config data not found or corrupt")
        print("") 
        sys.exit(1) 
        
    pathChecker("Logfile-Path", jsonData["logFilePath"])
    pathChecker("Queries-Path", jsonData["queriesPath"])
    pathChecker("Temps-Path", jsonData["tempPath"])
    pathChecker("fide_temps", jsonData["fide_temps"])
    pathChecker("prepagadas_temps", jsonData["prepagadas_temps"])
   
    pathChecker("temp_212", jsonData["temp_212"])
    pathChecker("bk_temps", jsonData["bk_temps"])
    pathChecker("queriesPath_aux", jsonData["queriesPath_aux"])
    
    pathChecker("temps_file_excel", jsonData["temps_file_excel"])
    pathChecker("bk_temps_file_excel", jsonData["bk_temps_file_excel"])
    pathChecker("html", jsonData["html"])
    pathChecker("temps_captaciones", jsonData["temps_captaciones"])
    #pathChecker("summary", jsonData["summary"])
    
    pathChecker("queries_Path_calendar", jsonData["queries_Path_calendar"])
    pathChecker("inputs_file", jsonData["inputs_file"])
    pathChecker("imput_fide", jsonData["imput_fide"])
    pathChecker("imputs_010X", jsonData["imputs_010X"])
    pathChecker("bk_folder_fide", jsonData["bk_folder_fide"])
    pathChecker("captaciones_temps", jsonData["captaciones_temps"])
    
    #
    outputsPath = os.path.join(*jsonData["outputsPath"]) 
    pathChecker("Outputs-Path", outputsPath)
    #
    if not isinstance(jsonData['at_name'], str):
        print(jsonData['at_name'] + "  is not an string.")
        print("==> Process aborted...")
        sys.exit(1)
    #
    if not isinstance(jsonData['cod_ent_superv'], str):
        print(jsonData['cod_ent_superv'] + "  is not an string.")
        print("==> Process aborted...")
        sys.exit(1) 
    #
    if not isinstance(jsonData['output_ext'], str):
        print(jsonData['output_ext'] + "  is not an string")
        print("==> Process aborted...")
        sys.exit(1)
        
    if not isinstance(jsonData['bookmark'], str):
        print(jsonData['bookmark'] + "  is not an string")
        print("==> Process aborted...")
        sys.exit(1)
    #    
    if not isinstance(jsonData['logFile_Name'], str):
        print(jsonData['logFile_Name'] + "  is not an string")
        sys.exit(1)
    #    
    intChecker("max_logfile_size", jsonData["max_logfile_size"])
    intChecker("backupCount", jsonData["backupCount"]) 
    #
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
        handlers=[
            RotatingFileHandler(
                os.path.join(jsonData["logFilePath"], jsonData['logFile_Name']),
                maxBytes = jsonData["max_logfile_size"],
                backupCount = jsonData["backupCount"]
            ),
            logging.StreamHandler()
        ]
    )
    # logging.getLogger('pyhive').setLevel(logging.CRITICAL)
    #
    if len(jsonData['credentials_conn']) <= 0 :
        logging.error("==> The database connection credentials were not found.")
        logging.error("==> Process aborted...")
        exit(1)
    #
    if len(jsonData['file_excel_export']) <= 0 :
        logging.error("==> The database connection file_excel_export were not found.")
        logging.error("==> Process aborted...")
        exit(1)    
    #       
    if len(jsonData['credentials_email']) <= 0 :
        logging.error("==> The email connection credentials were not found.")
        logging.error("==> Process aborted...")
        exit(1)
    #
    if len(jsonData['credentials_conn_impala']) <= 0 :
        logging.error("==> The database connection credentials impala were not found.")
        logging.error("==> Process aborted...")
        exit(1)
    #
    if len(jsonData['list_queries_aux']) <= 0 :
        logging.error("==> The list_queries_aux were not found.")
        logging.error("==> Process aborted...")
        exit(1)
    #
    if len(jsonData['imputs_010X']) <= 0 :
        logging.error("==> The imputs_010X were not found.")
        logging.error("==> Process aborted...")
        exit(1)    
    #    
    if len(jsonData['list_inputs_file']) <= 0 :
        logging.error("==> The list_inputs_file were not found.")
        logging.error("==> Process aborted...")
        exit(1)
    #
    SQL_list = os.listdir(jsonData['queriesPath']) 
    if len(SQL_list) <= 0 :
        logging.error(f"==> The SQL Queries folder {jsonData['queriesPath']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)
    
    SQL_list_aux = os.listdir(jsonData['queriesPath_aux']) 
    if len(SQL_list_aux) <= 0 :
        logging.error(f"==> The SQL Queries folder {jsonData['queriesPath_aux']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)    

    SQL_list_path = os.listdir(jsonData['queries_Path_calendar']) 
    if len(SQL_list_path) <= 0 :
        logging.error(f"==> The SQL Queries folder {jsonData['queries_Path_calendar']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)
       
    
    dir_query_aux=os.path.join(os.getcwd(),jsonData['queriesPath_aux'])
    if not os.path.isdir(dir_query_aux):
        logging.error(f"==> The concealer folder {jsonData['queriesPath_aux']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)
        
    dir_temp_212=os.path.join(os.getcwd(),jsonData['temp_212'])
    if not os.path.isdir(dir_temp_212):
        logging.error(f"==> The concealer folder {jsonData['temp_212']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)    
    
    dir_bk_temps=os.path.join(os.getcwd(),jsonData['bk_temps'])
    if not os.path.isdir(dir_bk_temps):
        logging.error(f"==> The concealer folder {jsonData['bk_temps']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)    
    
    dir_temps_file_excel=os.path.join(os.getcwd(),jsonData['temps_file_excel'])
    if not os.path.isdir(dir_temps_file_excel):
        logging.error(f"==> The concealer folder {jsonData['temps_file_excel']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)    
    
    dir_bk_temps_file_excel=os.path.join(os.getcwd(),jsonData['bk_temps_file_excel'])
    if not os.path.isdir(dir_bk_temps_file_excel):
        logging.error(f"==> The concealer folder {jsonData['dir_bk_temps_file_excel']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)
    
    dir_html=os.path.join(os.getcwd(),jsonData['html'])
    if not os.path.isdir(dir_bk_temps_file_excel):
        logging.error(f"==> The concealer folder {jsonData['html']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)        
    
    dir_capta=os.path.join(os.getcwd(),jsonData['temps_captaciones'])
    if not os.path.isdir(dir_bk_temps_file_excel):
        logging.error(f"==> The concealer folder {jsonData['httemps_captacionesml']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)
    
    dir_fide=os.path.join(os.getcwd(),jsonData['imput_fide'])
    if not os.path.isdir(dir_fide):
        logging.error(f"==> The concealer folder {jsonData['imput_fide']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)  
        
    dir_bk_fide=os.path.join(os.getcwd(),jsonData['bk_folder_fide'])
    if not os.path.isdir(dir_bk_fide):
        logging.error(f"==> The concealer folder {jsonData['bk_folder_fide']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)                
                   
    #################################################################################################    
    #           SECCION DEL REPROCESO                                                               #     
    #################################################################################################
    dir_reprocces=os.path.join(os.getcwd(),jsonData['reprocess'])
    if not os.path.isdir(dir_reprocces):
        logging.error(f"==> The concealer folder {jsonData['reprocess']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)    
    #################################################################################################
    #################################################################################################
        
    file_reprocces=os.listdir(jsonData['reprocess'])
    if len(file_reprocces) <= 0 :
        logging.error(f"==> The concealer file {jsonData['reprocess']} it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)
    
    folder_reprocess=os.path.join(dir_reprocces,file_reprocces[0])
    print("folder_reprocess")
    print(folder_reprocess)
    try: 
        file_json_reprocess = open(folder_reprocess)
        jsonReproces = json.load(file_json_reprocess) 
        file_json_reprocess.close()  
    except Exception as e: 
        print("...")
        trace_back = sys.exc_info()[2]
        line = trace_back.tb_lineno
        print("==> Error in line: " + str(line))
        print(f"==> Config JasonReprocess error message: {e}.")
        print("==> Process aborted...")
    
    #################################################################################################        
    #################################################################################################
    #################################################################################################    
    
    # queries_list  
    if len(jsonData['queries_list']) <= 0 :
        logging.error(f" The SQL Queries List it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)
              
    # queries_list_Calendar  
    if len(jsonData['queries_list_Calendar']) <= 0 :
        logging.error(f" The SQL Queries List Calendar it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)    
    #   
    if len(jsonData['info_cols']) <= 0 :
        logging.error(f"==> The Columns info list it's empty, please checkit.") 
        logging.error("==> Process aborted...")
        exit(1)
    # 
    queries_data={} 
    #
    for query in  jsonData['queries_list']: 
        q_name, __ = query.split(".")
        if not query in SQL_list:
            logging.error(f"==> Consulta SQL -- {q_name} -- no se encuentra en el directorio, por favor revise el directorio {jsonData['queriesPath']} y el archivo de confirugración") 
            exit(1)
        queries_data[q_name] = openQuery(os.path.join(jsonData['queriesPath'], query), logging)

    queries_list_Calendar={} 
    for query in  jsonData['queries_list_Calendar']: 
        q_name, __ = query.split(".")
        if not query in SQL_list_path:
            logging.error(f"==> Consulta SQL -- {q_name} -- no se encuentra en el directorio, por favor revise el directorio {jsonData['queries_Path_calendar']} y el archivo de confirugración") 
            exit(1)
        queries_list_Calendar[q_name] = openQuery(os.path.join(jsonData['queries_Path_calendar'], query), logging)

    
    queries_list_aux={} 
    for query in os.listdir(jsonData['queriesPath_aux']): 
        print(query)
        q_name, __ = query.split(".")
        if not query in SQL_list_aux:
            logging.error(f"==> Consulta SQL -- {q_name} -- no se encuentra en el directorio, por favor revise el directorio {jsonData['queriesPath_aux']} y el archivo de confirugración") 
            exit(1)
        queries_list_aux[q_name] = openQuery(os.path.join(jsonData['queriesPath_aux'], query), logging)
        
        
    dicc_file_imputs={} 
    for arch in os.listdir(jsonData['inputs_file']): 
        print(arch)
        a_name, __ = arch.split(".")
        if not arch in jsonData['list_inputs_file']:
            logging.error(f"==> Archivo Excel -- {a_name} -- no se encuentra en el directorio, por favor revise el directorio {jsonData['inputs_file']} y el archivo de confirugración") 
            exit(1)
        dicc_file_imputs[a_name] = arch
      
    ##########################################################################################################################################
    ##########################################################################################################################################
    ##########################################################################################################################################
    #queries_list_extrac={} 
    #for query in  jsonData['queries_list_extrac']: 
        #q_name, __ = query.split(".")
        #if not query in SQL_query_extrac:
         #   logging.error(f"==> Consulta SQL -- {q_name} -- no se encuentra en el directorio, por favor revise el directorio {jsonData['queries_list_extrac']} y el archivo de confirugración") 
          #  exit(1)
        #queries_list_extrac[q_name] = openQuery(os.path.join(jsonData['query_extrac'], query), logging)      
    
    ##########################################################################################################################################
    ##########################################################################################################################################
    ##########################################################################################################################################
    
    
    
    
    
    start_date_valid = None
    end_date_valid = None  
     
    if (len(sys.argv)  ==  4)  :
        print (f"==> AT agent missing dates parameters")
        print("") 
        sys.exit(1) 
    
    
    if (len(sys.argv)  ==  5) and (sys.argv[3]  ) and (sys.argv[4] ): 
        #
        if (sys.argv[3] != False): 
            if validateDate(sys.argv[3]) == False : 
                logging.error(f"==> Start date sintax error, follow example '20231201'") 
                sys.exit(1) 
            start_date_valid =sys.argv[3] 
        #
        if sys.argv[4] != False:  
            if validateDate(sys.argv[4]) == False: 
                logging.error(f"==> End date sintax error, follow example '20231202'") 
                sys.exit(1)  
            end_date_valid = sys.argv[4] 
            # --
        # --
        #        
        datetime1 = datetime.datetime.strptime(start_date_valid, '%Y%m%d')
        datetime2 = datetime.datetime.strptime(end_date_valid, '%Y%m%d')
        #
        if (datetime.datetime.strptime(start_date_valid, '%Y%m%d') ) > (datetime.datetime.strptime(end_date_valid, '%Y%m%d')):
            logging.error(f"==> Start date is later than End date")
            sys.exit(1)   
    
    date_now=datetime.date.today()
    respConfig={}
    respConfig = { 
        "at_name"              : jsonData['at_name'], 
        "cod_ent_superv"       : jsonData['cod_ent_superv'], 
        "output_ext"           : jsonData['output_ext'], 
        "bookmark"             : jsonData['bookmark'], 
        #################################################################
        "queriesPath"          : jsonData['queriesPath'],
        "imputs_010X"          : jsonData['imputs_010X'],
        "tempPath"             : jsonData['tempPath'],
        "bk_temps"             : jsonData['bk_temps'],
        #################################################################
        "temps_format"         : jsonData['temps_format'],
        "reprocess"            : jsonData['reprocess'],
        "file_reprocess"       : jsonReproces,        
        #################################################################
        "outputsPath"          : jsonData['outputsPath'],
        "captaciones_temps"    : jsonData['captaciones_temps'],
        "bk_outputs"           : jsonData['bk_outputs'],
        "temps_file_excel"     : jsonData['temps_file_excel'],
        "bk_temps_file_excel"  : jsonData['bk_temps_file_excel'],
        "html"                 : jsonData['html'],
        "temps_captaciones"    : jsonData['temps_captaciones'],
        "outputs_at"           : jsonData['outputs_at'],
        "outputs_at_bk"        : jsonData['outputs_at_bk'],
        "temp_212"             : jsonData['temp_212'],
        "prepagadas_temps"     : jsonData['prepagadas_temps'],
        "fide_temps"           : jsonData['fide_temps'],
        "bk_temps"             : jsonData['bk_temps'],
        "imput_fide"           : jsonData['imput_fide'],
        "bk_folder_fide"       : jsonData['bk_folder_fide'],
        "list_col_categ"       : jsonData['list_col_categ'],
        #
        "logFile_Name"         : jsonData['logFile_Name'],
        "list_file_basi"       : jsonData['list_file_basi'],           
        "logfile_path"         : jsonData["logFilePath"] ,         
        "max_logfile_size"     : int(jsonData['max_logfile_size']),
        "backupCount"          : int(jsonData['backupCount']),
        #
        "credentials_conn"     : jsonData['credentials_conn'],
        "credentials_conn_impala":jsonData['credentials_conn_impala'],
        "credentials_email"    : jsonData['credentials_email'],
        "file_excel_export"    : jsonData['file_excel_export'],
        "queries_data"         : queries_data,
        "info_cols"            : jsonData['info_cols'] ,
        #
        "categoria_01_26"          : jsonData["categoria_01_26"],
        "categoria_01_04"          : jsonData["categoria_01_04"],
        "categoria_02_05_esq"      : jsonData["categoria_02_05_esq"],
        "categoria_01_01_02_03"    : jsonData["categoria_01_01_02_03"],
        "categoria_01_23_28"       : jsonData["categoria_01_23_28"],
        "categoria_01_23_28_21105" : jsonData["categoria_01_23_28_21105"],
        "categoria_03_10"          : jsonData["categoria_03_10"],
        "categoria_03_08_09"       : jsonData["categoria_03_08_09"],
        "categoria_05_16"          : jsonData["categoria_05_16"],
        "categoria_02_05"          : jsonData["categoria_02_05"],
        "categoria_05_16_24108"    : jsonData["categoria_05_16_24108"],
        "categoria_02_05_bal"      : jsonData["categoria_02_05_bal"],
        "list_file_212"            : jsonData["list_file_212"],
        "categoria_07"             : jsonData["categoria_07"],
        "list_file_catg_01"        : jsonData["list_file_catg_01"],
        "fide"                     : jsonData["fide"],
        "list_inputs_file"         : dicc_file_imputs,
        "inputs_file"              : jsonData["inputs_file"],
        "list_temp_format"         : jsonData["list_temp_format"],
        #
        "list_table"               : jsonData['list_table'],
        "tipo_trans"               : jsonData['tipo_trans'],
        "list_queries_aux"         : jsonData['list_queries_aux'],
        #
        "queries_Path_calendar"    : jsonData['queries_Path_calendar'],
        "queriesPath_aux"          : jsonData['queriesPath_aux'],
        "queries_list_Calendar"    : queries_list_Calendar,
        "queries_list_aux"         : queries_list_aux,
        #
        "start_date"               : start_date_valid,
        "end_date"                 : end_date_valid,
        "date_now"                 : date_now,
        #
        "at_name"                  : jsonData['at_name'],
        "at_name_file"             : jsonData['at_name_file'],
        "at_name_type"             : jsonData['at_name_type'],
        "cod_ent_superv"           : jsonData['cod_ent_superv'],
        # 
        "logs":logging 
    } 

    
    #
    return respConfig
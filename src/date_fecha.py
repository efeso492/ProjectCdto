import datetime
import logging
#import formats
import json 
import os
import pandas as pd 
from datetime            import date, time, datetime as dt, timedelta
from decimal             import Decimal
from .config_validations import config , validateFile, openQuery
from .connection_impala  import *
from .import_time        import *
from .formats            import *




def fch_trans_prep(fecha_nueva,fch_contb_def,fch_friday,dicc_main,dh):
    #fecha_nueva=date y es la fecha del sistema
    #fch_friday fecha ultima particion dia habil
     
    logs= dicc_main["logs"] #logs
    fch_system=dicc_main["date_now"]
    logs.info("-------------------------------------") 
    logs.info("--> calculating transaction date <---")
    logs.info("-------------------------------------") 
    messg = {
        'fecha_contable':'',
        'fecha_viernes':'',
        'fecha_trans':'',
        'fecha_particion':'',
            }
    
    #fecha_str=datetime.strptime(fecha_nueva,"%Y-%m-%d").strftime("%Y-%m-%d")
    fecha_dt=dt.strptime(fecha_nueva,"%Y-%m-%d") #Fecha nueva es la fecha de reproceso
    #fch_d=fecha_dt-timedelta(days=1)
    nro_day=fecha_dt.weekday() #convertir este objeto en datetime.date
    ##nro_day : Es el numero de dia con respecto a las tras
    ### SEGMENTO PARA TESTEAR DIAS HABILES
    #dia=1  
    dh=int(dh)    
    ###
        
    #day=1
    #nro_day=int(day)
    
    list_fech=[]
    
    try:
        if (nro_day==6): #DOMINGO AQUI NO IMPORTA SI EL SABADO FUE O NO HABIL
           logs.info("-------------------------------------") 
           logs.info("------> Processing on Sunday <-------")
           logs.info("-------------------------------------") 
           messg["fecha_particion"]=fecha_nueva
           messg["fecha_contable"]=fch_contb_def
           messg["fecha_viernes"]=fch_friday
           messg["fecha_trans"]=fecha_nueva
           messg["fecha_contb_fs"]=fch_contb_def
              
        elif (nro_day==0 and dh==1):   ##MARTES Y DIA LUNES HABIL
           logs.info("-------------------------------------") 
           logs.info("------> Processing on Monday <------")
           logs.info("-------------------------------------")
           messg["fecha_particion"]=fecha_nueva
           messg["fecha_contable"]=fch_friday
           messg["fecha_viernes"]=fch_friday
           messg["fecha_trans"]=fecha_nueva
           messg["fecha_contb_fs"]=fch_friday
           fch_tr=dt.strptime(fecha_nueva,"%Y-%m-%d")
           fch_a=fch_tr-timedelta(days=1)
           fch_a=fch_a.strftime("%Y-%m-%d")
           dia_habil = consult_business_day(fch_a,dicc_main)
           if (int(dia_habil)==1):
              messg["fecha_contb_fs"]=fch_a
           else:
              messg["fecha_contb_fs"]=fch_friday
       
        elif (nro_day==0 and dh==0):   ##MARTES Y DIA LUNES NO HABIL
           logs.info("-------------------------------------") 
           logs.info("------> Processing on Monday <------")
           logs.info("-------------------------------------")
           messg["fecha_particion"]=fecha_nueva
           messg["fecha_contable"]=fch_contb_def
           messg["fecha_viernes"]=fch_friday
           messg["fecha_trans"]=fecha_nueva
           messg["fecha_contb_fs"]=fch_contb_def
           """
             fch_tr=datetime.strptime(fecha_nueva,"%Y-%m-%d")
             fch_a=fch_tr-timedelta(days=1)
             fch_a=fch_a.strftime("%Y-%m-%d")
             dia_habil = consult_business_day(fch_a,dicc_main)
             if (int(dia_habil)==1):
                messg["fecha_contb_fs"]=fch_a
             else:
                messg["fecha_contb_fs"]=fch_contb_def  
           """ 
               
          
        elif (nro_day==5):   ##SABADO Y DIA TRANSACCIONAL HABIL
           logs.info("-------------------------------------") 
           logs.info("-----> Processing on Saturday <------")
           logs.info("-------------------------------------") 
           messg["fecha_particion"]=fecha_nueva
           messg["fecha_contable"]=fch_contb_def
           messg["fecha_viernes"]=fch_friday
           messg["fecha_trans"]=fecha_nueva
           fch_tr=dt.strptime(fecha_nueva,"%Y-%m-%d")
           fch_a=fch_tr-timedelta(days=1)
           fch_a=fch_a.strftime("%Y-%m-%d")
           dia_habil = consult_business_day(fch_a,dicc_main)
           if (int(dia_habil)==1):
              messg["fecha_contb_fs"]=fch_a
           else:
              messg["fecha_contb_fs"]=fch_contb_def
           
        elif (nro_day==1 and dh==1):   ##MARTES Y DIA LUNES HABIL
           logs.info("-------------------------------------") 
           logs.info("------> Processing on Tuesday <------")
           logs.info("-------------------------------------")
           messg["fecha_particion"]=fecha_nueva
           messg["fecha_contable"]=fch_friday
           messg["fecha_viernes"]=fch_friday
           messg["fecha_trans"]=fecha_nueva
           messg["fecha_contb_fs"]=fch_friday
           fch_tr=dt.strptime(fecha_nueva,"%Y-%m-%d")
           fch_a=fch_tr-timedelta(days=1)
           fch_a=fch_a.strftime("%Y-%m-%d")
           dia_habil = consult_business_day(fch_a,dicc_main)
           if (int(dia_habil)==1):
              messg["fecha_contb_fs"]=fch_a
           else:
              messg["fecha_contb_fs"]=fch_friday
       
        elif (nro_day==1 and dh==0):   ##MARTES Y DIA LUNES NO HABIL
           logs.info("-------------------------------------") 
           logs.info("------> Processing on Tuesday <------")
           logs.info("-------------------------------------")
           messg["fecha_particion"]=fecha_nueva
           messg["fecha_contable"]=fch_contb_def
           messg["fecha_viernes"]=fch_friday
           messg["fecha_trans"]=fecha_nueva
           fch_tr=dt.strptime(fecha_nueva,"%Y-%m-%d")
           fch_a=fch_tr-timedelta(days=1)
           fch_a=fch_a.strftime("%Y-%m-%d")
           dia_habil = consult_business_day(fch_a,dicc_main)
           if (int(dia_habil)==1):
              messg["fecha_contb_fs"]=fch_a
           else:
              messg["fecha_contb_fs"]=fch_contb_def  
            
        
        elif (nro_day==2 and dh==1):   ##MIERCOLES Y DIA MARTES HABIL
           logs.info("-------------------------------------") 
           logs.info("-----> Processing on Wednesday <-----")
           logs.info("-------------------------------------")
           messg["fecha_particion"]=fecha_nueva
           messg["fecha_contable"]=fch_friday
           messg["fecha_viernes"]=fch_friday
           messg["fecha_trans"]=fecha_nueva
           fch_tr=dt.strptime(fecha_nueva,"%Y-%m-%d")
           fch_a=fch_tr-timedelta(days=1)
           fch_a=fch_a.strftime("%Y-%m-%d")
           dia_habil = consult_business_day(fch_a,dicc_main)
           if (int(dia_habil)==1):
              messg["fecha_contb_fs"]=fch_a
           else:
              messg["fecha_contb_fs"]=fch_contb_def
           
        elif (nro_day==2 and dh==0):   ##MIERCOLES Y DIA MARTES NO HABIL
           logs.info("-------------------------------------") 
           logs.info("-----> Processing on Wednesday <-----")
           logs.info("-------------------------------------")
           messg["fecha_particion"]=fecha_nueva
           messg["fecha_contable"]=fch_contb_def
           messg["fecha_viernes"]=fch_friday
           messg["fecha_trans"]=fecha_nueva
           #messg["fecha_contb_fs"]=fch_contb_def
           fch_tr=dt.strptime(fecha_nueva,"%Y-%m-%d")
           fch_a=fch_tr-timedelta(days=1)
           fch_a=fch_a.strftime("%Y-%m-%d")
           dia_habil = consult_business_day(fch_a,dicc_main)
           if (int(dia_habil)==1):
              messg["fecha_contb_fs"]=fch_a
           else:
              messg["fecha_contb_fs"]=fch_contb_def
            
         
        elif (nro_day==3 and dh==1):   ##JUEVES Y DIA MIERCOLES HABIL
           logs.info("-------------------------------------") 
           logs.info("-----> Processing on Thursday <------")
           logs.info("-------------------------------------")
           messg["fecha_particion"]    = fecha_nueva
           messg["fecha_contable"]     = fch_friday
           messg["fecha_viernes"]      = fch_friday
           messg["fecha_trans"]        = fecha_nueva
           fch_tr=dt.strptime(fecha_nueva,"%Y-%m-%d")
           fch_a=fch_tr-timedelta(days=1)
           fch_a=fch_a.strftime("%Y-%m-%d")
           dia_habil = consult_business_day(fch_a,dicc_main)
           if (int(dia_habil)==1):
              messg["fecha_contb_fs"]=fch_a
           else:
              messg["fecha_contb_fs"]=fch_friday
           
        elif (nro_day==3 and dh==0):   ##JUEVES Y DIA MIERCOLES NO HABIL
           logs.info("-------------------------------------") 
           logs.info("-----> Processing on Thursday <------")
           logs.info("-------------------------------------")
           messg["fecha_particion"]=fecha_nueva
           messg["fecha_contable"]=fch_contb_def
           messg["fecha_viernes"]=fch_friday
           messg["fecha_trans"]=fecha_nueva
           fch_tr=dt.strptime(fecha_nueva,"%Y-%m-%d")
           fch_a=fch_tr-timedelta(days=1)
           fch_a=fch_a.strftime("%Y-%m-%d")
           dia_habil = consult_business_day(fch_a,dicc_main)
           if (int(dia_habil)==1):
              messg["fecha_contb_fs"]=fch_a
           else:
              messg["fecha_contb_fs"]=fch_contb_def
            
        
        elif (nro_day==4 and dh==1):   ##VIERNES Y DIA JUEVES HABIL
           logs.info("-------------------------------------") 
           logs.info("------> Processing on Friday <-------")
           logs.info("-------------------------------------")
           messg["fecha_particion"]=fecha_nueva
           messg["fecha_contable"]=fch_friday
           messg["fecha_viernes"]=fch_friday
           messg["fecha_trans"]=fecha_nueva
           fch_tr=dt.strptime(fecha_nueva,"%Y-%m-%d")
           fch_a=fch_tr-timedelta(days=1)
           fch_a=fch_a.strftime("%Y-%m-%d")
           dia_habil = consult_business_day(fch_a,dicc_main)
           if (int(dia_habil)==1):
              messg["fecha_contb_fs"]=fch_a
           else:
              messg["fecha_contb_fs"]=fch_contb_def
           
        elif (nro_day==4 and dh==0):   ##VIERNES Y DIA JUEVES NO HABIL
           logs.info("-------------------------------------") 
           logs.info("------> Processing on Friday <-------")
           logs.info("-------------------------------------")
           messg["fecha_particion"]=fecha_nueva
           messg["fecha_contable"]=fch_contb_def
           messg["fecha_viernes"]=fch_friday
           messg["fecha_trans"]=fecha_nueva
           fch_tr=dt.strptime(fecha_nueva,"%Y-%m-%d")
           fch_a=fch_tr-timedelta(days=1)
           fch_a=fch_a.strftime("%Y-%m-%d")
           dia_habil = consult_business_day(fch_a,dicc_main)
           if (int(dia_habil)==1):
              messg["fecha_contb_fs"]=fch_a
           else:
              messg["fecha_contb_fs"]=fch_contb_def
           
        for k,v in messg.items():
          f=messg[k]
          if (len(f)!=0):     
             list_fech.append(str(f))        
             logs.info(f" {k} * {v}")
        
        return list_fech
    
    except UnboundLocalError as err:
       logs.error("Se ha capturado un UnboundLocalError")
       logs.error("Un byte, no forma parte de una secuencia UTF-8 valida")
       logs.error("Revisa el metodo para encontrar los caracteres especiales")
       logs.error(f"A problem was encountered when taking the system date {err}")
       messg["status"]  = False
       messg["err"]  = err 
       return logs.info("Proceso abortado")
       exit(1)
    
    
    except Exception as err:
       logs.error("Se ha capturado un Exception")
       logs.error(f"A problem was encountered when taking the system date {err}")
       messg["status"]  = False
       messg["err"]  = err 
       return logs.info("Proceso abortado")
       exit(1) 
    
    
    
        
    
def fch_trans_api(fecha_nueva,fch_contb_def,fch_friday,dicc_main,dh):
    logs= dicc_main["logs"] #logs
    logs.info("-------------------------------------") 
    logs.info("--> calculating transaction date <---")
    logs.info("-->           cards API          <---")
    logs.info("-------------------------------------") 
    messg = {
        'fecha_contable':'',
        'fecha_viernes':'',
        'fecha_trans':'',
        'fecha_particion':'',
            }
         
    fecha_dt=dt.strptime(fecha_nueva,"%Y-%m-%d") # COVERTIMOS A STRING LA FECHA
    nro_day=fecha_dt.weekday() # NUMERO DEL DIA DE LA TRANSACCION
    #nro_day=6
    logs.info("API business day test")  
    try:    
      if (int(nro_day)==0 or int(nro_day)==1 or int(nro_day)==2 or int(nro_day)==3): 
        fch_contb_estimada=fecha_dt-timedelta(days=-1)
        fch_contb_l=fch_contb_estimada.strftime("%Y-%m-%d")
        dia_h_api = consult_business_day(fch_contb_l,dicc_main)
        
        if (int(dia_h_api)==1):
          logs.info("The following date is a business day")
          fch_contb_sem=fch_contb_l
        else:          
          logs.info("The following date is not a business day")
          tupla_sem=consult_business_date_next(dicc_main,fch_contb_l)
          tupla_sem_new=tupla_sem
          fch_contb_sem=tupla_sem
        
      elif (int(nro_day)==4): 
          fch_contb_l=fecha_dt-timedelta(days=-3)
          fch_contb_l=fch_contb_l.strftime("%Y-%m-%d")
          dia_h_l = consult_business_day(fch_contb_l,dicc_main)
          if (int(dia_h_l)==1):
            logs.info("The following date is a business day Friday")
            fch_contb_sem=fch_contb_l
            logs.info("The following date is not a business day Friday ")
          else:          
            logs.info("The following date is not a business day Friday ")
            tupla_sem=consult_business_date_next(dicc_main,fch_contb_l)
            tupla_sem_new=tupla_sem
            fch_contb_sem=tupla_sem
      
      elif (int(nro_day)==5): 
          fch_contb_l=fecha_dt-timedelta(days=-2)
          fch_contb_l=fch_contb_l.strftime("%Y-%m-%d")
          dia_h_l = consult_business_day(fch_contb_l,dicc_main)
          print("############")
          print(dia_h_l)
          if (int(dia_h_l)==1):
            logs.info("The following date is a business day Saturday")
            fch_contb_sem=fch_contb_l
            logs.info("The following date is not  a business day Saturday")
          else:          
            logs.info("The following date is not a business day after Saturday")
            tupla_sem=consult_business_date_next(dicc_main,fch_contb_l)
            tupla_sem_new=tupla_sem
            print("############")
            print(tupla_sem)
            fch_contb_sem=tupla_sem
            print("############")
            print(fch_contb_sem)    
      else:
          fch_contb_l=fecha_dt-timedelta(days=-1)
          fch_contb_l=fch_contb_l.strftime("%Y-%m-%d")
          dia_h_l = consult_business_day(fch_contb_l,dicc_main)
          if (int(dia_h_l)==1):
            logs.info("The next date is a business day Sunday")
            fch_contb_sem=fch_contb_l
          else:          
            logs.info("The next date is not a business day Sunday")
            tupla_sem=consult_business_date_next(dicc_main,fch_contb_l)
            tupla_sem_new=tupla_sem
            fch_contb_sem=tupla_sem
            
      messg["fecha_particion"]=fch_contb_sem
      messg["fecha_viernes"]=fch_friday
      messg["fecha_trans"]=fecha_nueva
      messg["fecha_contable"]=fch_contb_sem
               
      list_fech=[]        
      logs.info("Vector of valid dates for API")    
      for k,v in messg.items():
        f=messg[k]
        if (len(f)!=0):     
           list_fech.append(str(f))        
           logs.info(f" {k} * {v}")
      
      return list_fech  
    
    except UnboundLocalError as err:
       logs.error("Se ha capturado un UnboundLocalError")
       logs.error("Un byte, no forma parte de una secuencia UTF-8 valida")
       logs.error("Revisa el metodo para encontrar los caracteres especiales")
       logs.error(f"A problem was encountered when taking the system date {err}")
       messg["status"]  = False
       messg["err"]  = err 
       return logs.info("Proceso abortado")
       exit(1)
    
    
    except Exception as err:
       logs.error("Se ha capturado un Exception")
       logs.error(f"A problem was encountered when taking the system date {err}")
       messg["status"]  = False
       messg["err"]  = err 
       return logs.info("Proceso abortado")
       exit(1)       
    
    
    
    
    
    
def fch_trans_tdc(fch_trans,fch_contb_def,fch_act,dicc_main,dh):
    logs= dicc_main["logs"] #logs
    logs.info("-------------------------------------") 
    logs.info("--> calculating transaction date <---")
    logs.info("-->           cards TDC          <---")
    logs.info("-------------------------------------")
    messg = {
        'fecha_contable':'',
        'fecha_viernes':'',
        'fecha_trans':'',
        'fecha_particion':'',
            }
     
    fecha_dt=dt.strptime(fch_trans,"%Y-%m-%d")
    #print(fecha_dt)
    nro_day=fecha_dt.weekday() # NUMERO DEL DIA DE LA TRANSACCION
            
    try:
      logs.info("TDC business day test")    
      if (int(nro_day)==0 or int(nro_day)==1 or int(nro_day)==2 or int(nro_day)==3 or int(nro_day)==4): 
        dia_h_api = consult_business_day(fch_trans,dicc_main)
        #print("PRUEBA DIA HABIL TDC")
        #print(dia_h_api)
        if (int(dia_h_api)==1):
          logs.info("he following date is a business day")
          fch_contb_sem=fch_trans
        else:          
          logs.info("The following date is not a business day")
          tupla_sem=consult_business_date_next(dicc_main,fch_trans)
          fch_contb_sem=tupla_sem
      
      elif (int(nro_day)==5): 
          fch_contb_l=fecha_dt-timedelta(days=-2)
          fch_contb_l=fch_contb_l.strftime("%Y-%m-%d")
          logs.info("Estimated Accounting date beig  ")
          dia_sab=consult_business_day(fch_contb_l,dicc_main)
          if (int(dia_sab)==1):
            logs.info("The following date is a business day from Saturday")
            fch_contb_sem=fch_contb_l
            logs.info("The next date is the business day after Saturday")
          else:          
            logs.info("The following date is not a business day from Saturday ")
            tupla_sem=consult_business_date_next(dicc_main,fch_contb_l)
            fch_contb_sem=tupla_sem      
      else:
          fch_contb_l=fecha_dt-timedelta(days=-1)
          fch_contb_l=fch_contb_l.strftime("%Y-%m-%d")
          dia_dom = consult_business_day(fch_contb_l,dicc_main)
          if (int(dia_dom)==1):
            logs.info("The following date is a business day from Sunday")
            fch_contb_sem=fch_contb_l
          else:          
            logs.info("The following date is not a business day from Sunday")
            tupla_sem=consult_business_date_next(dicc_main,fch_contb_l)
            fch_contb_sem=tupla_sem
    
             
      messg["fecha_particion"]=fch_contb_sem
      messg["fecha_viernes"]=fch_act
      messg["fecha_trans"]=fch_trans
      messg["fecha_contable"]=fch_contb_sem
               
      list_fech=[]        
          
      for k,v in messg.items():
        f=messg[k]
        if (len(f)!=0):     
           list_fech.append(str(f))        
           logs.info(f" {k} * {v}")
    
      return messg
    
    except UnboundLocalError as err:
       logs.error("Se ha capturado un UnboundLocalError")
       logs.error("Un byte, no forma parte de una secuencia UTF-8 valida")
       logs.error("Revisa el metodo para encontrar los caracteres especiales")
       logs.error(f"A problem was encountered when taking the system date {err}")
       messg["status"]  = False
       messg["err"]  = err 
       return logs.info("Proceso abortado")
       exit(1)
    
    
    except Exception as err:
       logs.error("Se ha capturado un Exception")
       logs.error(f"A problem was encountered when taking the system date {err}")
       messg["status"]  = False
       messg["err"]  = err 
       return logs.info("Proceso abortado")
       exit(1)  
    
    


def fch_trans_tdd(fch_trans,fch_contb_def,fch_act,dicc_main,dh):
    logs= dicc_main["logs"] #logs
    logs.info("-------------------------------------") 
    logs.info("--> calculating transaction date <---")
    logs.info("-->           cards TDD          <---")
    logs.info("-------------------------------------")
    messg = {
        'fecha_contable':'',
        'fecha_viernes':'',
        'fecha_trans':'',
        'fecha_particion':'',
            }
            
    if (len(fch_act)>0):
      messg["fecha_viernes"]=fch_act
    
    return messg          
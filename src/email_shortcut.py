import sys
from mailer import mailer

def email_shorter(email_active,credentials_email,to, subject, attachment,logs,html_template):    
    if email_active: 
        if not sys.platform.startswith("win"): 
            try:   
                
                credentials_email["subject"] = subject#  asunto
                
                credentials_email["html_template"] = html_template
                if html_template == False: #plantilla html
                    credentials_email["html_template"] = False 
                #
                #
                credentials_email["attachment"] = attachment
                if attachment == False:#  doc adjunto
                    credentials_email["attachment"] = False  
                #
                #
                credentials_email["to"] = to 
                msngr = mailer(credentials_email, logs=logs)#instancia del objeto mailer
                msngr.send_email() #invocacion del metodo send_email
            except Exception as e: 
                logs.error( e ) 
        # --
    # --
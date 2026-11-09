import os
import smtplib 
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.encoders import encode_base64

import logging
import logging.handlers

# Configura el logger
logger = logging.getLogger()
logger.setLevel(logging.ERROR)


class mailer:
    
    def __init__(self, credentials,  logs=False):  
        self.smtp_server = credentials["smtp_server"]
        self.sender = credentials["sender"]
        self.to = credentials["to"] 
        self.cc = credentials["cc"]
        self.subject = credentials["subject"] 
        self.html_template = credentials["html_template"] 
        self.attachment = credentials["attachment"] 
        self.logs = logs  


    # def send_email(smtp_server, sender, to, cc=False, subject=False, html_template=False, attachment=False): 
    def send_email(self): 
        """
            Libreria para enviar correos con plantillas HTML y documentos adjuntos

            Args:
                credentials: Un diccionario que contiene los valores de configuración. 
                logs: herramienta de logs.

            Returns:
                N/A
        """
        #
        #
        try:
            if self.logs != False:
                self.logs.getLogger('email').setLevel(self.logs.CRITICAL) 
            #
            # Connect to the SMTP server
            service = smtplib.SMTP(self.smtp_server, 25) 
            service.ehlo() 
            service.set_debuglevel(1) 
            #
            header = MIMEMultipart()
            header["Subject"] = self.subject        
            header["From"] = self.sender  
            header["To"]  = ",".join(self.to )  
            #
            if(  self.cc   != False):
                header["Cc"]  = ",".join(self.cc )  
            # 
            # Add the body of the message
            if(  self.html_template   != False):
                template_Msj = MIMEText(self.html_template, "html")
                header.attach(template_Msj)  
            #
            # Add the attachment, if necessary
            if (self.attachment != False) and (len(self.attachment) > 0):
                for file_name in self.attachment:
                    with open(file_name, "rb") as f:
                        attachment = MIMEApplication(f.read())
                        attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_name))
                        header.attach(attachment)
                    # -- 
                # -- 
            # 
            # Send the message  
            service.sendmail(self.sender, self.to, header.as_string())
            if self.logs != False:
                self.logs.info('Email was send successfully')
            else:
                print('Email send successfully')
            #Cerrar la conexión SMTP
            service.quit()
        except Exception as err:
            if self.logs != False:
                self.logs.error(f'Error sending email, Descript: {err}') 
            else:
                print(f'Error sending email, Descript: {err}') 
            # --
        # --
    # --
#
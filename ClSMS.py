#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4 import QtCore
import StringIO
import serial
from curses import ascii
import time
import os 
import re
import base64
import ftplib
import datetime
import sys
import subprocess

class clSMS(QtCore.QThread):
# Constantes
    minAttempts = 5

    RED = "\033[1;31m"
    BLUE = "\033[1;34m"
    CYAN = "\033[1;36m"
    GREEN = "\033[1;32m"
    RESET = "\033[0;0m"
    BOLD = "\033[;1m"
    REVERSE = "\033[;7m"
    
    def __init__(self, parent, clDB, clserial):
        QtCore.QThread.__init__(self)
        self.parent = parent
        self.clSerial = clserial
        self.clDB = clDB

    def printDebug(self,msg):
        return
        print datetime.datetime.now().strftime("%H:%M:%S"), msg

    def run(self):
        while True:
            #if True:
            try:
                if self.parent.smsEnabled:
                    while self.parent.sendData and not self.parent.smsEnabled:
                        time.sleep(1.77)
                        self.printDebug(self.REVERSE+'### Waitting..... (Modem sending data) ###'+self.RESET)
                    if not self.parent.sendData and self.parent.smsEnabled:
                        self.obtenerMensaje()
                else:
                    self.printDebug(self.RED+'### Disabled SMS Function ###'+self.RESET)
            #else:
            except:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print sys.exc_info()[1]
                print fname
                print exc_tb.tb_lineno
            time.sleep(10)

    def write(self, cmd, answer, attempts):
        while True:
            self.parent.locked = True
            stRead = self.clSerial.write(cmd, answer, attempts)
            self.parent.locked = False
            if (stRead is None):
                stRead = ""
            if (stRead.find("pdpdeact") != -1):
                self.parent.reInit3G = 1
            elif (stRead.find("closed") != -1):
                self.parent.reInit3G = 2
            elif (stRead.find("I/O Error") != -1):
                self.parent.reInit3G = 3
            else:
                break
            time.sleep(1)
        return stRead

     #Agregados para mensaje
    def obtenerMensaje(self):
        '''
        ##################################################
        #                 Lectura de SMS                 #
        ##################################################
        '''
        print "Se va a enviar el comando de SMS"
        i = 0
        while (self.parent.locked):
            self.printDebug(self.RED+self.REVERSE+'### Lectura SMS - Locked ###'+self.RESET)
            time.sleep(1)
            if (i == 30):
                return
            i += 1
        self.printDebug(self.GREEN+'### Lectura de mensajes ###'+self.RESET)
        stRead = self.write("AT+CMGF?\r",("OK", "ERROR"), self.minAttempts)        
        if (stRead.find('+CMGF: 0') != -1):
            self.printDebug(self.GREEN+self.REVERSE+'### Cambiando SMS a Modo Texto ###'+self.RESET)
            stRead = self.write("AT+CMGF=1\r",("OK", "ERROR"), self.minAttempts)
        stRead = self.write("AT+CMGR=1\r",("OK", "ERROR"), self.minAttempts)
        if (stRead.find('+CMGR: "REC READ"') != -1) or (stRead.find('+CMGR: "REC UNREAD"') != -1):
            self.printDebug(self.GREEN+'New SMS'+self.RESET)
            stRead = " ".join(stRead.split())
            stRead = stRead.split(",")
            #self.printDebug('stRead '+str(stRead[4]))
            cmd = " ".join(stRead[4].split())
            cmd = cmd.split(" ")
            #self.printDebug('cmd '+str(cmd[1]))
            #if True:
            try:
                cmd = cmd[1]
                #este pasa cuando hay una actualizacion por lo que
                #obtendre el comando sin la actualizacion
                if cmd[:2] == 'IU':
                    self.printDebug('Actualizacion de algo')
                    strActualizacion = cmd
                    cmd = cmd[:6]
                    self.printDebug(strActualizacion)
                else:
                    #esto pasa cuando es un comando normal
                    #cmd = text[8]
                    self.printDebug(cmd)
                    strActualizacion = 'nulo'
            #else:
            except:
                self.printDebug(self.RED+'Mensaje sms no valido'+self.RESET)
                cmd = 'ERROR'
                strActualizacion = 'nulo'
            self.validarComando(cmd, strActualizacion, 1, stRead[1])
            #self.printDebug('validar comando')
            self.printDebug(self.CYAN+'SMS has been Readed and Ejecuted'+self.RESET)            
        else:
            #print (datetime.datetime.now().strftime("%H:%M:%S")+' ### No New SMS to Read and ejecute ###',color="green")
            self.printDebug(self.BLUE+'No New SMS to Read and ejecute'+self.RESET)

    def validarComando(self, comando, strActualizacion, sms, telefono):
        #comando = 'IREUC'       
        if(comando.find("OK") != -1):
                comando = self.write("AT+CMGR=1\r",("OK", "ERROR"), self.minAttempts)                          
                self.printDebug('###  ###')
                i = comando.find("+CMGR:")
                j = comando.find("OK")                              
                comando=comando[i+56:j-4] 
        
        c= self.clDB.dbComando.cursor()
        self.printDebug("select validarComando")
        c.execute("SELECT comando, accion, dEjec FROM tComando WHERE comando = ?",(comando, ))
        self.printDebug("fetch validarComando")
        data = c.fetchone()
        self.printDebug(str(data))
        if data is None:
            self.printDebug('Comando no valido')
        else:
            comaT = data[0]
            acciT = data[1]
            dEjeT = data[2]
        #self.printDebug(execc)
        self.printDebug("close cursos validarComando")
        c.close()
        c = None
        stRead = self.write("AT+CMGD=1\r",("OK", "ERROR"), self.minAttempts)                          
        if data is None:
            self.printDebug('###           Comando no soportado        ###')
        else:
            self.parent.waitting = True
            self.parent.sendData = True
            stRead = self.write('AT+CMGS='+str(telefono)+'\r', ("ERROR", '>'), self.minAttempts)              #---
            if (stRead.find(">") != -1):
                cmd = "Respuesta Automatica de la unidad "+str(self.clDB.economico)+" al Comando SMS: "+comando+"\x1A\r"
                stRead = self.write(cmd,("FAIL", 'OK', 'ERROR'), 20)                  #---
            self.parent.sendData = False
            self.parent.waitting = False
         
            if dEjeT == 'L':
                #local execute
                exec acciT
            elif dEjeT == 'C':
                #console execute
                return_code = subprocess.call("%s"%str(acciT), shell=True)
                self.printDebug(str(return_code))
                #Elimino el comando SMS
            elif dEjeT == 'o':
                self.printDebug(acciT)
            elif dEjeT == 'S':
                self.printDebug('Comando '+comando)
                self.printDebug('strComando '+strActualizacion)

                #self.printDebug("Connect comando accion")
                #connC = sqlite3.connect(cdDbC)
                self.printDebug("cursos comando accion")
                c= self.clDB.dbComando.cursor()
                self.printDebug("select comando accion")

                c.execute("SELECT accion FROM tComando WHERE comando = ?",(comando,))
                self.printDebug("fetch comando accion")
                datosComando = c.fetchone()
                self.printDebug("close comando accion")
                c.close()
                c = None
                if datosComando is None:
                    self.printDebug('No hay parametros de configuracon contacta al administrador')
                else:
                    accion = datosComando[0]

                self.printDebug( strActualizacion.split("@"))
                obtDatoActualizar =  strActualizacion.split("@")
                datoAActualizar = obtDatoActualizar[1]

                self.printDebug(accion.split(","))
                datosDeBase = accion.split(",")
                nombreTabla = str(datosDeBase[0])
                nombreRow = str(datosDeBase[1])
                nombreBase = str(datosDeBase[2])

                self.printDebug('Nueva pagina '+ datoAActualizar)
                self.printDebug('Donde lo voy a guardar '+ nombreTabla)
                self.printDebug('Nombre del campo a afectar '+ nombreRow)
                self.printDebug('Nombre de la base que voy a alterar '+ nombreBase)

                '''
                    Aca empieza el proceso de actualizacion de registro
                    esto va a funcionar para la actualizacion/sincronizacion
                    de los paramtros de configuracion del sistema
                '''
                
                self.printDebug("update data nombreBase")
                self.conn.execute('UPDATE ' +'"'+ nombreTabla +'"'+ ' set ' +'"'+ nombreRow +'"'+ ' = ?', (datoAActualizar, ))
                self.printDebug("commit data nombreBase")
                self.conn.commit()
                self.printDebug("close Connect data nombreBase")
            else:
                self.printDebug('###          Comando no soportado         ###')






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
import zipfile
import datetime
import sys
import subprocess
import math
import RPi.GPIO as GPIO
import variables_globales as vg
from PyQt4.QtCore import QSettings

from alttusDB import obtener_estado_de_todas_las_ventas_no_enviadas, actualizar_estado_aforo_mipase_check_servidor, obtener_estadisticas_no_enviadas, actualizar_estado_estadistica_check_servidor, insertar_estadisticas_alttus, actualizar_estado_hora_check_hecho, obtener_estado_de_todas_las_horas_no_hechas, actualizar_estado_hora_por_defecto, obtener_ultima_ACT, obtener_parametros
from tarjetasDB import obtener_tarjeta_mipase_por_UID
import FTPAlttus

class clQuectel(QtCore.QThread):
# Constantes
    maxSendError = 5
    iMaxSocket = 5
    
    idCons = 0
    sendError = 0
    ser = None
    qData = ()
    aforo = False
    stIP = ""
    iNoGPS = 0
    iMaxTryGPS = 180
    minCSQ = 5
    velAnt = -1
    horaAnt = 0
    latAnt = 0
    lonAnt = 0
    latitud = ""
    longitud = ""
    datetimes = ""
    velGPS = 0
    intentosHTTPOST = 0
    ser = None
    minAttempts = 10
    timeOutGPS = 5
    timeOutFTP = 20
    flGPSOn = True
    GPSOffline = 0
    GPSDelay = 120
    GPSWaitting = 0
    blockSize = 1024
    sendingData = False
    flReinicio = False

    GPSAttempts = 11
    nowAnt = 0
    tolerancia = "0.0006"
    enTerminal = False
    enPuntoDeControl = False
    rutaOK = False
    idPITerminal = 0
    idRuta = 0
    itmp = 0
    distanciaPC = 0
    
    RED = "\033[1;31m"
    BLUE = "\033[1;34m"
    CYAN = "\033[1;36m"
    GREEN = "\033[1;32m"
    RESET = "\033[0;0m"
    BOLD = "\033[;1m"
    REVERSE = "\033[;7m"
    stReset3G = b"+++\x1B\r"

    def __init__(self, parent, clDB, clserial, clbarras):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(12,GPIO.IN)
        QtCore.QThread.__init__(self)
        self.parent = parent
        self.serial = clserial
        self.clDB = clDB
        self.parent.flFecha = False
        self.parent.iComm = 0
        self.parent.rdy = False
        self.flDownload = False
        self.iMax = 0
        self.clbarras = clbarras
        self.parent.stBoton = ""
        self.settings = QSettings("/home/pi/innobusmx/settings.ini", QSettings.IniFormat)
        #if True:
        try:
            c = self.clDB.dbAforo.cursor()
            c.execute("SELECT idValidador FROM validador WHERE enviado = 0 ORDER BY idValidador LIMIT 1")
            data = c.fetchone()
            self.parent.flSendAforo = not (data is None)

            c.execute("SELECT idRecorrido FROM recorrido WHERE enviadoInicio = 0 ORDER BY idRecorrido LIMIT 1")
            data = c.fetchone()
            self.parent.flSendInicioRecorrido = not (data is None)

            c.execute("SELECT idRecorrido FROM recorrido WHERE enviadoInicio = 1 AND enviadoTermino = 0 ORDER BY idRecorrido LIMIT 1")
            data = c.fetchone()
            self.parent.flSendTerminoRecorrido = not (data is None)

            c.execute("SELECT idRecorrido FROM vuelta WHERE enviadoInicio = 0 ORDER BY idRecorrido, vuelta LIMIT 1")
            data = c.fetchone()
            self.parent.flSendInicioVuelta = not (data is None)

            c.execute("SELECT idRecorrido FROM vuelta WHERE enviadoInicio = 1 AND enviadoTermino = 0 ORDER BY idRecorrido, vuelta LIMIT 1")
            data = c.fetchone()
            self.parent.flSendTerminoVuelta = not (data is None)

            c.execute("SELECT idRuta FROM vuelta ORDER BY inicio DESC LIMIT 1")
            data = c.fetchone()
            if not (data is None):
                if (str(data[0]) != str(self.clDB.idRuta)):
                    self.clDB.dbAforo.execute("UPDATE parametros SET idRutaActual = "+str(data[0]))
                    self.clDB.dbAforo.commit()
                    self.clDB.idRuta = data[0]
                    #print ('SELECT numRuta, Nombre FROM ruta WHERE idTransportista = '+str(self.clDB.idTransportista)+ ' and idRuta = '+str(self.clDB.idRuta))
                    c.execute('SELECT numRuta, Nombre FROM ruta WHERE idTransportista = '+str(self.clDB.idTransportista)+ ' and idRuta = '+str(self.clDB.idRuta))
                    data = c.fetchone()
                    if (data is None):
                        self.parent.lblNoRuta.setText('')
                        self.parent.lblRuta.setText('')
                    else:
                        self.parent.lblNoRuta.setText(str(data[0]))
                        self.parent.lblRuta.setText(str(data[1].encode('latin-1')))

                
            c.close
            c = None
            self.idRuta = self.clDB.idRuta

            #print "Ruta ", self.clDB.idRuta
            #print "Recorrido", self.parent.idRecorrido
            
            c = self.clDB.dbMensajes.cursor()
            c.execute("SELECT idEnvio FROM envio WHERE envio = 0 ORDER BY idEnvio LIMIT 1")
            data = c.fetchone()
            self.parent.flSendEnvio = not (data is None)

            c.close()
            c = None

            c = self.clDB.dbGPS.cursor()
            c.execute("SELECT idTransportista FROM gps LIMIT 1")
            data = c.fetchone()
            self.parent.flDataGPS = not (data is None)

            c.close()
            c = None

            self.clDB.dbFlota.execute("UPDATE puntoControl SET enviado = 0 WHERE enviado = -1")
            self.clDB.dbFlota.commit()

            c = self.clDB.dbFlota.cursor()
            c.execute("SELECT idPuntoInteres FROM puntoControl WHERE enviado = 0 LIMIT 1")
            data = c.fetchone()
            self.parent.flSendPuntoControl = not (data is None)
            if self.parent.flSendPuntoControl:
                self.printDebug(self.parent.PURPLE+'Hay coordenadas GPS de Puntos de Control pendientes por enviar'+self.parent.RESET)

            c.execute("SELECT COUNT(*) FROM asignacion")
            data = c.fetchone()
            self.rutaOK = (data[0] == 1)
            c.close()
            c = None
            
        #else:    
        except:
            print "except __init clModem__"
        self.first = True

    def vigencias(self):
        return
        #if True:
        try:
            c = self.clDB.dbVigencias.cursor()
            c.execute("SELECT fecha FROM descarga")
            data = c.fetchone()
            if (data is None):
                c.execute("INSERT INTO descarga (fecha) VALUES (191217)")
                self.clDB.dbVigencias.commit()
                dia = 191217
            else:
                dia = int(data[0])
            hoy = int(time.strftime('%y%m%d'))
            if (hoy > dia):
                #print "hoy: "+str(hoy)+"  dia:"+str(dia)
                fl = False
                while hoy >= dia:
                    if self.descargarArchivoFTP("vigencias/"+str(dia)+".txt","/home/pi/innobusmx/data/"+str(dia)+".txt",False):
                        if (os.path.getsize("/home/pi/innobusmx/data/"+str(dia)+".txt") > 20):
                            #print 'sqlite3 /home/pi/innobusmx/data/db/vigencia ".import /home/pi/innobusmx/data/'+str(dia)+'.txt vigencia"'
                            os.system('sqlite3 /home/pi/innobusmx/data/db/vigencia ".import /home/pi/innobusmx/data/'+str(dia)+'.txt vigencia"')
                            time.sleep(1)
                        #else:
                            #print "Invalid file: /home/pi/innobusmx/data/"+str(dia)+".txt"
                        os.system("rm /home/pi/innobusmx/data/"+str(dia)+".txt")

                    if self.descargarArchivoFTP("vigencias/d"+str(dia)+".txt","/home/pi/innobusmx/data/d"+str(dia)+".txt",False):
                        if (os.path.getsize("/home/pi/innobusmx/data/d"+str(dia)+".txt") > 12):
                            #print 'sqlite3 /home/pi/innobusmx/data/db/vigencia ".import /home/pi/innobusmx/data/d'+str(dia)+'.txt vigenciaOK"'
                            os.system('sqlite3 /home/pi/innobusmx/data/db/vigencia ".import /home/pi/innobusmx/data/d'+str(dia)+'.txt vigenciaOK"')
                            time.sleep(1)
                            fl = True
                        #else:
                            #print "Invalid file: /home/pi/innobusmx/data/d"+str(dia)+".txt"
                        os.system("rm /home/pi/innobusmx/data/d"+str(dia)+".txt")
                    if (dia == 191231):
                        dia = 200101
                    elif (dia == 200131):
                        dia = 200201
                    elif (dia == 200229):
                        dia = 200301
                    elif (dia == 200331):
                        dia = 200401
                    elif (dia == 200430):
                        dia = 200501
                    elif (dia == 200531):
                        dia = 200601
                    elif (dia == 200630):
                        dia = 200701
                    else:
                        dia += 1
                    #print "hoy: "+str(hoy)+"  dia:"+str(dia)

                if fl:
                    c.execute("DELETE FROM vigencia WHERE substr(csn,-14,14) IN (SELECT substr(csn,-14,14) FROM vigenciaOK)")
                    c.execute("DELETE FROM vigenciaOK")
                    self.clDB.dbVigencias.commit()

                #print "UPDATE descarga SET fecha = "+str(dia)
                c.execute("UPDATE descarga SET fecha = "+str(dia))
                self.clDB.dbVigencias.commit()
            c.close()
        #else:
        except:
            print "Error al leer vigencias"

    def printDebug(self,msg):
        #return
        print datetime.datetime.now().strftime("%H:%M:%S"), msg

    def run(self):
        self.ser = self.serial.setup3G()
        self.setupModem()
        eini=GPIO.input(12)
        self.vigencias()
        alerta = 0
        while True:
            self.obtenerCoordenadaGPS()
            self.clbarras.Barras()
            if (self.clbarras.ModuloBarras == False):
                self.printDebug(self.RED+'Falla modulo de Barras'+self.RESET)
            #else:
            #    self.printDebug(self.GREEN+'[Modulo de Barras funcionando]'+self.RESET)
            #if True:
            try:
                eact=GPIO.input(12)
                if eini != eact :
                    now = int(time.time())
                    if ((now - alerta) > 5):
                        fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                        #print fecha+"  "+self.parent.REVERSE+self.parent.RED+'BOTON DE PANICO ACTIVADO'+self.parent.RESET
                        if (self.latitud != ""):
                            lat = str(self.latitud)
                        else:
                            lat = "0"
                        if (self.longitud != ""):
                            lon = str(self.longitud)
                        else:
                            lon = "0"
                        if (self.datetimes != ""):
                            fechaGPS = str(self.datetimes)
                        else:
                            fechaGPS = fecha
                        self.parent.stBoton = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",1,Boton panico,"+str(self.parent.csn)+","+lat+","+lon+","+str(self.velGPS)+","+fechaGPS+","+str(fecha)+","+str(self.clDB.idRuta)+","+str(self.parent.idOperador)
                        self.clDB.envio(1,self.parent.stBoton)
                        self.parent.flSendEnvio = True
                    eini=eact
                    alerta = now
                else:
                    alerta = 0                
                if (self.parent.stBoton != ""):
                    #self.printDebug(self.parent.PURPLE+'###      Enviando Boton de Panico      ###'+self.parent.RESET)
                    stSendData = self.sendData(self.parent.stBoton)
                    if (stSendData != ""):
                        stSendData = ''.join(stSendData)
                        stSendData = stSendData.split("\r\n")
                        if (len(stSendData) > 3):
                            if stSendData[2] == "1":
                                #self.printDebug(self.parent.PURPLE+'###      Envio Exitoso de Alerta de Boton de Panico      ###'+self.parent.RESET)
                                self.parent.stBoton = ""
                    #if (self.parent.stBoton != ""):
                    #    self.printDebug(self.parent.REVERSE+self.parent.PURPLE+"Error al enviar Emergencia. Intenando Nuevamente........"+self.parent.RESET)
            #else:
            except:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
                fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,GPIO - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                self.clDB.envio(1,stB)
                self.parent.flSendEnvio = True
                eini=eact
                alerta = int(time.time())
            if (self.parent.rdy):
                #if True:
                try:
                    #self.printDebug(self.parent.PURPLE+"Se recibio RDY"+self.parent.RESET)
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    if (self.latitud != ""):
                        lat = str(self.latitud)
                    else:
                        lat = "0"
                    if (self.longitud != ""):
                        lon = str(self.longitud)
                    else:
                        lon = "0"
                    fechaGPS = datetime.datetime.fromtimestamp(self.parent.lastConnection).strftime('%Y-%m-%d %H:%M:%S') 
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",10,Desc RDY,"+str(self.parent.csn)+","+lat+","+lon+",0,"+fechaGPS+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True
                    self.parent.rdy = False
                #else:
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,RDY - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True

            if (self.parent.flSendAforo):
                #if True:
                try:
                    c = self.clDB.dbAforo.cursor()
                    c.execute(" SELECT idValidador, idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado FROM validador WHERE enviado = 0 ORDER BY idValidador LIMIT 1")
                    data = c.fetchone()
                    if (data):
                        stSendData = '3,'+str(data[1])+','+str(data[2])+','+str(data[3])+','+str(data[4])+','+str(data[5])+','+str(data[6])+','+str(data[8])+','+str(data[7])+'\r'
                        stSendData = self.sendData(stSendData)
                        if (stSendData != ""):
                            stSendData = ''.join(stSendData)
                            stSendData = stSendData.split("\r\n")
                            if (len(stSendData) > 3):
                                dato = stSendData[2].split('@')
                                if (len(dato) == 2 and dato[0] == "1"):
                                    self.clDB.dbAforo.execute('UPDATE validador SET enviado = '+str(dato[1])+' WHERE idValidador = '+str(data[0]))
                                    self.clDB.dbAforo.commit()
                    else:
                        self.parent.flSendAforo = False
                    c.close()
                    c = None
                #else:
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,Aforo - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True

            # Revisar si hay nuevos turnos abiertos            
            if (self.parent.flSendInicioRecorrido):
                #if True:
                try:
                    c = self.clDB.dbAforo.cursor()
                    c.execute("SELECT idRecorrido, inicio, csnInicio, idTurno FROM recorrido WHERE enviadoInicio = 0 ORDER BY inicio LIMIT 1")
                    data = c.fetchone()
                    if (data):
                        st = "0"
                        stSendData = '6,'+str(data[1])+','+str(self.clDB.idUnidad)+','+st+','+str(data[2])+','+str(data[3])+','+str(data[0])+',I\r'
                        stSendData = self.sendData(stSendData)
                        if (stSendData != ""):
                            stSendData = ''.join(stSendData)
                            stSendData = stSendData.split("\r\n")
                            if (len(stSendData) > 3):
                                if stSendData[2] == "1":
                                    self.clDB.dbAforo.execute('UPDATE recorrido SET enviadoInicio = 1 WHERE idRecorrido = '+str(data[0]))
                                    self.clDB.dbAforo.commit()
                                    self.parent.flSendTerminoRecorrido = True
                    else:
                        self.parent.flSendInicioRecorrido = False
                        self.parent.flSendTerminoRecorrido = True
                    c.close()
                    c = None
                #else:
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,Abrir Turno - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True

            # Revisar si hay nuevos turnos cerrados            
            if (self.parent.flSendTerminoRecorrido):
                #if True:
                try:
                    c = self.clDB.dbAforo.cursor()
                    c.execute("SELECT idRecorrido, termino, csnTermino, idTurno, inicio FROM recorrido WHERE enviadoInicio = 1 AND enviadoTermino = 0 ORDER BY termino LIMIT 1")
                    data = c.fetchone()
                    if (data):
                        st = "0"
                        stSendData = '6,'+str(data[1])+','+str(self.clDB.idUnidad)+','+st+','+str(data[2])+','+str(data[3])+','+str(data[0])+',F,'+str(data[4])+'\r'
                        stSendData = self.sendData(stSendData)
                        if (stSendData != ""):
                            stSendData = ''.join(stSendData)
                            stSendData = stSendData.split("\r\n")
                            if (len(stSendData) > 3):
                                if stSendData[2] == "1":
                                    self.clDB.dbAforo.execute('UPDATE recorrido SET enviadoTermino = 1 WHERE idRecorrido = '+str(data[0]))
                                    self.clDB.dbAforo.commit()
                    else:
                        self.parent.flSendTerminoRecorrido = False
                        self.parent.flSendInicioVuelta = True
                    c.close()
                    c = None
                #else:
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,Cerrar Turno - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True

            # Revisar si hay nuevas vueltas abiertas            
            if (self.parent.flSendInicioVuelta):
                #if True:
                try:
                    c = self.clDB.dbAforo.cursor()
                    c.execute("SELECT vuelta.idRecorrido, vuelta, vuelta.inicio, vuelta.csnInicio, idRuta, idTurno, tipo FROM vuelta, recorrido WHERE recorrido.idRecorrido = vuelta.IdRecorrido AND vuelta.enviadoInicio = 0 and idVuelta = 0 ORDER BY vuelta.inicio LIMIT 1")
                    data = c.fetchone()
                    if (data):
                        if (data[4] is None):
                            st = "0"
                        else:
                            st = str(data[4])
                        stSendData = '5,'+str(data[2])+','+str(data[0])+','+str(self.clDB.idUnidad)+','+st+','+str(data[3])+','+str(data[1])+','+str(data[5])+',I,'+str(data[6])+'\r'
                        stSendData = self.sendData(stSendData)
                        if (stSendData != ""):
                            stSendData = ''.join(stSendData)
                            stSendData = stSendData.split("\r\n")
                            if (len(stSendData) > 3):
                                if stSendData[2] == "1":
                                    self.clDB.dbAforo.execute('UPDATE vuelta SET enviadoInicio = 1, idVuelta = '+str(stSendData[3])+' WHERE inicio = "'+str(data[2])+'"')
                                    self.clDB.dbAforo.commit()
                                    self.parent.flSendTerminoVuelta = True
                    else:
                        self.parent.flSendInicioVuelta = False
                        self.parent.flSendTerminoVuelta = True
                    c.close()
                    c = None
                #else:
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,Abrir Vuelta - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True

            # Revisar si hay cambio de Ruta            
            if (self.parent.flSendActualizaVuelta):
                #if True:
                try:
                    c = self.clDB.dbAforo.cursor()
                    c.execute("SELECT vuelta.idRecorrido, vuelta, vuelta.inicio, vuelta.csnInicio, idRuta, idTurno, idVuelta FROM vuelta, recorrido WHERE recorrido.idRecorrido = vuelta.IdRecorrido AND vuelta.enviadoInicio = 0 and idVuelta <> 0 ORDER BY vuelta.inicio LIMIT 1")
                    data = c.fetchone()
                    if (data):
                        if (data[4] is None):
                            st = "0"
                        else:
                            st = str(data[4])
                        stSendData = '5,'+str(data[2])+','+str(data[6])+','+str(self.clDB.idUnidad)+','+st+','+str(data[3])+','+str(data[1])+','+str(data[5])+',U'
                        stSendData = self.sendData(stSendData)
                        if (stSendData != ""):
                            stSendData = ''.join(stSendData)
                            stSendData = stSendData.split("\r\n")
                            if (len(stSendData) > 3):
                                if stSendData[2] != "0":
                                    self.clDB.dbAforo.execute('UPDATE vuelta SET enviadoInicio = 1 WHERE idVuelta = '+str(data[6]))
                                    self.clDB.dbAforo.commit()
                    else:
                        self.parent.flSendActualizaVuelta = False
                    c.close()
                    c = None
                #else:
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,Actualizar Vuelta - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True

            # Revisar si hay nuevas vueltas cerradas            
            if (self.parent.flSendTerminoVuelta):
                #if True:
                try:
                    c = self.clDB.dbAforo.cursor()
                    c.execute("SELECT vuelta.idRecorrido, vuelta, vuelta.termino, vuelta.csnTermino, idRuta, idTurno, idVuelta, vuelta.inicio FROM vuelta, recorrido WHERE recorrido.idRecorrido = vuelta.idRecorrido AND vuelta.enviadoInicio = 1 and vuelta.enviadoTermino = 0 ORDER BY vuelta.inicio LIMIT 1")
                    data = c.fetchone()
                    if (data):
                        if (data[4] is None):
                            st = "0"
                        else:
                            st = str(data[4])
                        if (data[6] is None):
                            st6 = "0"
                        else:
                            st6 = str(data[6])
                        stSendData = '5,'+str(data[2])+','+str(data[0])+','+str(self.clDB.idUnidad)+','+st+','+str(data[3])+','+str(data[1])+','+str(data[5])+',F,'+st6+'\r'
                        stSendData = self.sendData(stSendData)
                        if (stSendData != ""):
                            stSendData = ''.join(stSendData)
                            stSendData = stSendData.split("\r\n")
                            if (len(stSendData) > 3):
                                if stSendData[2] == "1":
                                    self.clDB.dbAforo.execute('UPDATE vuelta SET enviadoTermino = 1 WHERE inicio = "'+str(data[7])+'"')
                                    self.clDB.dbAforo.commit()
                                    flSendData = True
                    else:
                        self.parent.flSendTerminoVuelta = False
                    c.close()
                    c = None
                #else:
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,Cerrar Vuelta - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True

            # Revisar si hay mensajes por enviar            
            if (self.parent.flSendEnvio):
                #if True:
                try:
                    c = self.clDB.dbMensajes.cursor()
                    c.execute("SELECT idEnvio, msg, app FROM envio WHERE envio = 0 ORDER BY idEnvio LIMIT 1")
                    data = c.fetchone()
                    if (data):
                        stSendData = self.sendData(str(data[1].encode('UTF-8'))+'\r')
                        if (stSendData != ""):
                            stSendData = ''.join(stSendData)
                            stSendData = stSendData.split("\r\n")
                            if (len(stSendData) > 3):
                                if stSendData[2] == "1":
                                    self.clDB.dbMensajes.execute('DELETE FROM envio WHERE idEnvio = '+str(data[0])+' AND app = '+str(data[2]))
                                    self.clDB.dbMensajes.commit()
                                    flSendData = True
                    else:
                        self.parent.flSendEnvio = False
                    c.close()
                    c = None
                #else:
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,MSG - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True
                    self.clDB.dbMensajes.execute('DELETE FROM envio LIMIT 1')
                    self.clDB.dbMensajes.commit()

            # Revisar si hay coordenadas GPS por enviar            
            if (self.parent.flDataGPS):
                #if True:
                try:
                    c = self.clDB.dbGPS.cursor()
                    c.execute("SELECT idTransportista, idUnidad, fecha, latitud, longitud, velocidad,idCons, distancia FROM gps LIMIT 1")
                    data = c.fetchone()
                    if (data):
                        stSendData = '1,'+str(data[0])+','+str(data[1])+','+str(data[2])+','+str(data[3])+','+str(data[4])+','+str(data[5])+',-'+str(data[6])+','+str(int(data[7]))+'\r'
                        stSendData = self.sendData(stSendData)
                        if (stSendData != ""):
                            if (self.returnGPS(stSendData) == "1"):
                                self.clDB.dbGPS.execute('DELETE FROM gps WHERE fecha = "'+str(data[2])+'"')
                                self.clDB.dbGPS.commit()
                    else:
                        self.parent.flDataGPS = False
                    c.close()
                    c = None
                #else:
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,GPS - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True

            # Revisar si hay coordenadas GPS de Puntos de Control por enviar
            if (self.parent.flSendPuntoControl):
                #if True:
                try:
                    c = self.clDB.dbFlota.cursor()
                    c.execute("SELECT idUnidad, idPuntoInteres, fecha, latitud, longitud, distancia, idRecorrido, idRuta, vuelta FROM puntoControl WHERE enviado = 0 ORDER BY Fecha LIMIT 1")
                    data = c.fetchone()
                    if (data):
                        v = self.clDB.dbAforo.cursor()
                        v.execute("SELECT idVuelta FROM vuelta WHERE idRuta = "+str(data[7])+" AND idRecorrido = "+str(data[6])+" AND vuelta = "+str(data[8]))
                        d = v.fetchone()
                        if (d is None):
                            self.clDB.dbFlota.execute('UPDATE puntoControl SET enviado = -1 WHERE fecha = "'+str(data[2])+'"')
                            self.clDB.dbFlota.commit()
                        else: #if (int(d[0] != 0)):
                            stSendData = 'pc,'+str(data[0])+','+str(data[1])+','+str(data[2])+','+str(data[3])+','+str(data[4])+','+str(d[0])+','+str(int(data[5]))+'\r'
                            #self.printDebug(self.parent.PURPLE+stSendData+self.parent.RESET)
                            stSendData = self.sendData(stSendData)
                            #self.printDebug(self.parent.REVERSE+self.parent.PURPLE+stSendData+self.parent.RESET)
                            if (stSendData != ""):
                                stSendData = ''.join(stSendData)
                                stSendData = stSendData.split("\r\n")
                                if (len(stSendData) > 3):
                                    if stSendData[2] == "1":
                                        self.clDB.dbFlota.execute('UPDATE puntoControl SET enviado = 1 WHERE fecha = "'+str(data[2])+'"')
                                        self.clDB.dbFlota.commit()
                    else:
                        self.parent.flSendPuntoControl = False
                    c.close()
                    c = None
                #else:
                except:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,PC GPS - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True
                    
                    
            ##################### ERNESTO LOMAR #####################
            try:
                datos_enviados_azure = False
                
                ####### VERIFICAR SI HAY AFOROS PENDIENTES POR ENVIAR #######
                aforos_pendientes_mipase = obtener_estado_de_todas_las_ventas_no_enviadas()
                if len(aforos_pendientes_mipase) > 0:
                    #self.settings.setValue("mandando_datos",1)
                    self.enviar_aforos_mipase()
                    datos_enviados_azure = True
                    #self.settings.setValue("mandando_datos",0)
                else:
                    print "Sin aforos mipase pendientes de enviar a Azure"
                ############################################################
                    
                ####### VERIFICAR SI HAY ESTADISTICAS PENDIENTES POR ENVIAR #######
                estadisticas_pendientes =obtener_estadisticas_no_enviadas()
                if len(estadisticas_pendientes) > 0:
                    #self.settings.setValue("mandando_datos",1)
                    self.enviar_estadisticas_azure()
                    datos_enviados_azure = True
                    #self.settings.setValue("mandando_datos",0)
                else:
                    print "Sin estadisticas mipase pendientes de enviar a Azure"
                
                ############################################################
                
                ####### VERIFICAR SI ESTA EN EL RANGO DE LAS 04:37:00-04:40:00 #######
                hora_actual = datetime.datetime.now().time()
                if int(str(hora_actual.strftime("%H:%M:%S")).replace(":",""))  >= 43700 and int(str(hora_actual.strftime("%H:%M:%S")).replace(":",""))  <= 44000:
                    self.parent.crear_tramas9()
                    FTPAlttus.main(self.serial, self.parent)
                    datos_enviados_azure = True
                ############################################################
                
                ####### VERIFICAR SI SE TIENE QUE ASIGNAR LA CONEXION CON CYTIBUS #######
                if datos_enviados_azure:
                    datos_enviados_azure = False
                    self.reAsignarConexionCytibus()
                ############################################################
                
                ####### VERIFICAR SI SE PUEEDE ENVIAR LA TRAMA ACT #######
                obtener_todas_las_horasdb = obtener_estado_de_todas_las_horas_no_hechas()
                for i in xrange(len(obtener_todas_las_horasdb)):
                    hora_iteracion = obtener_todas_las_horasdb[i]
                    hora_actual = datetime.datetime.now().time()
                    if int(str(hora_actual.strftime("%H:%M:%S")).replace(":","")) >= int(str(hora_iteracion[1]).replace(":","")):
                        hecho = actualizar_estado_hora_check_hecho("Ok", hora_iteracion[0])
                        if hecho:
                            print "Ya se actualizo la hora check en servidor de: " + str(hora_iteracion)
                            fecha_actual = datetime.date.today()
                            insertar_estadisticas_alttus(str(self.clDB.economico), self.clDB.idTransportista, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), "ACT", "") # Solicitar actualizacion
                ############################################################
                
                ####### VERIFICAR SI HAY QUE PONER POR DEFECTO LA BASE DE DATOS HORAS #######
                
                reiniciar_valores_por_defecto = False
                if len(str(obtener_ultima_ACT())) > 2:
                    fecha_str = obtener_ultima_ACT()[0][3]
                    fecha_datetime = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
                    if fecha_datetime.strftime("%Y-%m-%d") != datetime.date.today().strftime("%Y-%m-%d"):
                        reiniciar_valores_por_defecto = True
                        print "Es un dia diferente"
                    else:
                        print "Es el mismo dia"
                
                if int(str(hora_actual.strftime("%H:%M:%S")).replace(":",""))  >= 235959 and int(str(hora_actual.strftime("%H:%M:%S")).replace(":",""))  <= 1000 or reiniciar_valores_por_defecto:
                    hecho_horas = actualizar_estado_hora_por_defecto()
                    intentos_cambiar = 0
                    if not hecho_horas:
                        while not hecho_horas or intentos_cambiar <= 5:
                            hecho_horas = actualizar_estado_hora_por_defecto()
                            intentos_cambiar += 1
                        if hecho_horas:
                            reiniciar_valores_por_defecto = False
                            print "Se actualizaron las BD horas a por defecto"
                        else:
                            reiniciar_valores_por_defecto = True
                            print "No se actualizaron las BD horas a por defecto"
                ############################################################
                
            except Exception, e:
                print "\x1b[1;31;47m"+"Fallo codigo de verificacion de datos pendientes."+str(e)+"\033[0;m"
            ##################### ERNESTO LOMAR #####################
            time.sleep(1)
    
    ##################### ERNESTO LOMAR #####################

    def inicializar_configuraciones_quectel(self):
        ###########################
        ######   Ernesto   ########
        ###########################
        
        try:
            ########## QICLOSE #########

            comando = "AT+QICLOSE=1\r\n"
            print self.serial.readln3G()
            self.serial.write3G(comando)
            i = 0
            print "Comando: AT+QICLOSE=1"
            
            while True:
                res = self.serial.readln3G()
                print "res es: " + str(res)
                i = i + 1
                time.sleep(1)
                if 'OK' in res:
                    break
                elif i == 5:
                    print "\x1b[1;33m"+"No se pudo inicializar AT+QICLOSE=1"
                    time.sleep(1)
                    break
                    #return False
            print "\x1b[1;32m"+"#####################################"
            
            ##########################
        except Exception, e:
            print "\x1b[1;31;47m"+"Error al ejecutar QICLOSE: "+str(e)+'\033[0;m'
            return False
        
        try:
            ########## QIDEACT #########

            comando = "AT+QIDEACT=1\r\n"
            print self.serial.readln3G()
            self.serial.write3G(comando)
            i = 0
            print "Comando: AT+QIDEACT=1"
            
            while True:
                res = self.serial.readln3G()
                print "res es: " + str(res)
                i = i + 1
                time.sleep(1)
                if 'OK' in res:
                    break
                elif i == 5:
                    print "\x1b[1;33m"+"No se pudo inicializar AT+QIDEACT=1"
                    time.sleep(1)
                    break
                    #return False
            print "\x1b[1;32m"+"#####################################"
            
            ##########################
        except Exception, e:
            print "\x1b[1;31;47m"+"Error al ejecutar QIDEACT: "+str(e)+'\033[0;m'
            return False
        
        try:
            ########## QICSGP #########
            
            comando = "AT+QICSGP=1,1,\"internet.itelcel.com\",\"\",\"\",0\r\n"
            print self.serial.readln3G()
            self.serial.write3G(comando)
            i = 0
            print "Comando: AT+QICSGP"
            
            while True:
                res = self.serial.readln3G()
                print "res es: " + str(res)
                i = i + 1
                time.sleep(1)
                if 'OK' in res:
                    break
                elif i == 5:
                    print "\x1b[1;33m"+"No se pudo inicializar AT+QICSGP=1"
                    time.sleep(1)
                    break
                    #return False
            print "\x1b[1;32m"+"#####################################"
            
            ##########################
        except Exception, e:
            print "\x1b[1;31;47m"+"Error al ejecutar QICSDGP: "+str(e)+'\033[0;m'
            return False
        
        try:
            ########## QIACT #########

            comando = "AT+QIACT=1\r\n"
            print self.serial.readln3G()
            self.serial.write3G(comando)
            i = 0
            print "Comando: AT+QIACT"
            
            while True:
                res = self.serial.readln3G()
                print "res es: " + str(res)
                i = i + 1
                time.sleep(1)
                if 'OK' in res:
                    break
                elif i == 5:
                    print "\x1b[1;33m"+"No se pudo inicializar AT+QIACT=1"
                    time.sleep(1)
                    break
                    #return False
            print "\x1b[1;32m"+"#####################################"
            
            ##########################
            
            return True
        except Exception, e:
            print "\x1b[1;31;47m"+"Error al ejecutar QIACT: "+str(e)+'\033[0;m'
            return False
        
    def abrir_puerto(self):
        try:
            time.sleep(0.0001)
            time.sleep(0.0001)
            
            parametros = obtener_parametros()
            
            # variables de prueba
            tcp = "\"TCP\""
            # identifica el envio por tcp
            ip = "\"20.106.77.209\""
            # ip publica o URL del servidor
            #print("qi open")
            # comando at, formato de envio, direciion ip o url, puerto del servidor, puerto por defecto del quectel, parametro de envio por push
            comando = "AT+QIOPEN=1,0,"+tcp+","+ip+","+str(parametros[0][2])+",0,1\r\n"
            self.serial.write3G(comando)
            i = 0
            print "Comando: AT+QIOPEN"
            
            while True:
                res = self.serial.readln3G()
                print "res es: " + str(res)
                i = i + 1
                time.sleep(1)
                if 'OK' in res:
                    break
                elif i == 5:
                    print "\x1b[1;33m"+"No se pudo inicializar AT+QIOPEN"
                    time.sleep(1)
                    break
            print "\x1b[1;32m"+"#####################################"
            
            '''print self.serial.readln3G()
            Aux = self.serial.readln3G()
            print Aux.decode()
            if "ERROR" in str(Aux.decode()):
                self.serial.readln3G()
                self.serial.readln3G()
                return False
            self.serial.readln3G()
            self.serial.readln3G()'''
            return True
        except Exception, e:
            print "\x1b[1;31;47m"+"comand.py, linea 180: "+str(e)+'\033[0;m'
            return False
            
    def mandar_datos(self,Trama):
        try:
            self.parent.lastConnection = time.time()
            self.parent.waitting = True
            time.sleep(0.0001)
            self.parent.sendData = True
            byte = len(Trama)
            comando = "AT+QISEND=0,"+str(byte)+"\r\n"
            self.serial.write3G(comando)
            print "Comando: AT+QISEND"
            i = 0
            j = 0
            while True:
                i = i+1
                Aux = self.serial.readln3G()
                resultado = Aux.decode()
                if '>' in resultado:
                    # Mando los datos
                    print "> encontrado"
                    time.sleep(0.0001)
                    self.serial.write3G(Trama.encode())
                    while True:
                        Aux = self.serial.readln3G()
                        resultado = Aux.decode()
                        j = j+1
                        if 'OK' in resultado:
                            print "\x1b[1;32m"+"Se envio correctamente el dato con SEND OK"
                            print "\x1b[1;32m"+str(Aux.decode())
                            break
                        elif 'ERROR' in resultado or 'FAIL' in resultado or j == 20:
                            print "\x1b[1;33m"+"La trama no se pudo enviar: "+str(resultado)
                            self.parent.flAlttus = False
                            return {
                                "enviado": False,
                                "accion": "error"
                            }
                    break
                elif 'ERROR' in resultado or i == 20:
                    print "\x1b[1;33m"+"Error al ejecutar el comando AT+QISEND"
                    print "\x1b[1;33m"+str(Aux.decode())
                    self.parent.flAlttus = False
                    return {
                        "enviado": False,
                        "accion": "error"
                    }

            if Trama == "quit":
                #variables_globales.conexion_servidor = "SI"
                return {
                    "enviado": True,
                    "accion": "error"
                }
            # recibir datos del servidor
            time.sleep(0.0001)
            #comando = "AT+QIRD=0,300\r\n"
            #self.serial.write3G(comando.encode())
            i = 0
            print "\x1b[1;32m"+"Esperando respuesta del servidor..."
            while True:
                Aux = self.serial.readln3G()
                resultado = Aux.decode()
                print "\x1b[1;32m"+"Leyendo: "+str(resultado)
                i = i+1
                if 'QIURC:' in resultado or 'RC' in resultado or 'IURC' in resultado or "recv" in resultado:
                    pass
                elif 'TrEm' in resultado or 'ErTr' in resultado or 'EmEr' in resultado:
                    print "\x1b[1;31;47m"+"La trama llego mal al servidor"+"\033[0;m"
                    self.parent.flAlttus = False
                    return {
                        "enviado": False,
                        "accion": "error"
                    }
                else:
                    if (Aux != b'\r\n' and Aux != b'') and ("SKT" in Aux):
                        print "\x1b[1;32m"+"Dato registrado en el servidor"
                        print "\x1b[1;32m"+"Respondio: "+resultado
                        self.parent.flAlttus = True
                        return {
                            "enviado": True,
                            "accion": resultado
                        }
                if i == 20:
                    print "\x1b[1;31;47m"+"Se terminaron los intentos de espera..."+"\033[0;m"
                    self.parent.flAlttus = False
                    return {
                        "enviado": False,
                        "accion": "error"
                    }
        except Exception, e:
            print "\x1b[1;31;47m"+"comand.py, linea 238: "+str(e)+'\033[0;m'
            
    def cerrar_socket(self):
        try:
            #self.mandar_datos('quit')
            time.sleep(0.001)
            comando = "AT+QICLOSE=1\r\n"  # cierra conexion con el servidor - Modificado de "AT+QICLOSE=0\r\n" a "AT+QICLOSE=1\r\n"
            self.serial.write3G(comando)
            print self.serial.readln3G()
            Aux = self.serial.readln3G()
            print Aux.decode()
        except Exception, e:
            print "comand.py, linea 251: "+str(e)
            
    def reiniciar_configuracion_quectel(self):
        try:
            time.sleep(0.001)
            comando = "AT+QIDEACT=1\r\n"
            self.serial.write3G(comando)
            print self.serial.readln3G()
            Aux = self.serial.readln3G()
            print Aux.decode()
            self.inicializar_configuraciones_quectel()
        except Exception, e:
            print "\x1b[1;31;47m"+"comand.py, linea 251: "+str(e)+'\033[0;m'
    
    def reAsignarConexionCytibus(self):
        
        try:
            self.parent.sendData = False
            self.parent.waitting = False
            ########## AT+QICLOSE #########
            
            comando = "AT+QICLOSE=1\r\n"
            print self.serial.readln3G()
            self.serial.write3G(comando)
            i = 0
            print "Comando: AT+QICLOSE"
            
            while True:
                res = self.serial.readln3G()
                print "res es: " + str(res)
                i = i + 1
                time.sleep(1)
                if 'OK' in res:
                    break
                elif i == 5:
                    print "\x1b[1;33m"+"No se pudo inicializar AT+QICLOSE=1"
                    time.sleep(1)
                    break
                    #return False
            print "\x1b[1;32m"+"#####################################"
            
            ##########################
        except Exception, e:
            print "\x1b[1;31;47m"+"Error al ejecutar AT+QICLOSE: "+str(e)+'\033[0;m'
            return False
        
        try:
            ########## AT+QIDEACT #########
            
            comando = "AT+QIDEACT=1\r\n"
            print self.serial.readln3G()
            self.serial.write3G(comando)
            i = 0
            print "Comando: AT+QIDEACT"
            
            while True:
                res = self.serial.readln3G()
                print "res es: " + str(res)
                i = i + 1
                time.sleep(1)
                if 'OK' in res:
                    break
                elif i == 5:
                    print "\x1b[1;33m"+"No se pudo inicializar AT+QIDEACT"
                    time.sleep(1)
                    break
                    #return False
            print "\x1b[1;32m"+"#####################################"
            
            ##########################
        except Exception, e:
            print "\x1b[1;31;47m"+"Error al ejecutar AT+QIDEACT: "+str(e)+'\033[0;m'
            return False
        
        try:
            ########## QICSGP #########
            
            comando = 'AT+QICSGP=1,1,"%s","%s","%s",1\r\n' % (self.clDB.urlAPN, self.clDB.userAPN, self.clDB.pwdAPN)
            print self.serial.readln3G()
            self.serial.write3G(comando)
            i = 0
            print "Comando: AT+QICSGP Cytibus"
            
            while True:
                res = self.serial.readln3G()
                print "res es: " + str(res)
                i = i + 1
                time.sleep(1)
                if 'OK' in res:
                    break
                elif i == 5:
                    print "\x1b[1;33m"+"No se pudo inicializar AT+QICSGP Cytibus"
                    time.sleep(1)
                    break
                    #return False
            print "\x1b[1;32m"+"#####################################"
            
            ##########################
        except Exception, e:
            print "\x1b[1;31;47m"+"Error al ejecutar QICSDGP Cytibus: "+str(e)+'\033[0;m'
            return False
    
    def enviar_aforos_mipase(self):
        try:
            aforos_pendientes_mipase = obtener_estado_de_todas_las_ventas_no_enviadas()
            if len(aforos_pendientes_mipase) > 0:
                print "\x1b[1;33m"+"Existen aforos de mi pase penientes por enviar.."
                configuracion_realizada = False
                abrir_puerto_azure = False
                intentos = 0
                intentos_enviar_aforos = 0
                while intentos_enviar_aforos <= 2:
                    print "\x1b[1;32m"+"¨Se iniciaran las configuraciones del quectel"
                    while configuracion_realizada != True or intentos <= 3:
                        configuracion_realizada = self.inicializar_configuraciones_quectel()
                        if configuracion_realizada:
                            print "\x1b[1;32m"+"Se configuro el quectel"
                            intentos = 0
                            break
                        intentos += 1
                    if configuracion_realizada:
                        print "\x1b[1;32m"+"Se abrira el puerto"
                        while abrir_puerto_azure != False or intentos <= 3:
                            abrir_puerto_azure = self.abrir_puerto()
                            if abrir_puerto_azure:
                                print "\x1b[1;32m"+"Se abrio el puerto para enviar datos a Azure"
                                intentos = 0
                                break
                            intentos += 1
                    else:
                        print "\x1b[1;33m"+"No se pudo configurar el quectel"
                        continue
                    if abrir_puerto_azure:
                        aforo_enviado = False
                        uid_aforo = ""
                        costo_aforo = ""
                        fecha_aforo = ""
                        hora_aforo = ""
                        print "\x1b[1;32m"+"Se van a enviar datos a Azure"
                        for i in xrange(5):
                            aforo = obtener_estado_de_todas_las_ventas_no_enviadas()
                            if len(aforo) > 0:
                                print "\x1b[1;32m"+"Se encontro este aforo" + str(aforo)
                                id_aforo = str(aforo[0][0])
                                uid_aforo = str(aforo[0][1])
                                costo_aforo = str(aforo[0][2])
                                fecha_aforo = str(aforo[0][3])
                                hora_aforo = str(aforo[0][4])
                                latitud_aforo = str(aforo[0][5])
                                longitud_aforo = str(aforo[0][6])
                                transportista_aforo = str(aforo[0][7])
                                num_economico_aforo = str(aforo[0][8])
                                
                                lblanca_o_lnegra = obtener_tarjeta_mipase_por_UID(uid_aforo)[1]
                                
                                if lblanca_o_lnegra:
                                    trama = "[5,"+id_aforo+","+num_economico_aforo+","+transportista_aforo+","+uid_aforo+","+str(fecha_aforo.replace("-","")[3:]+hora_aforo.replace(":",""))+","+latitud_aforo+","+longitud_aforo+"]"
                                else:
                                    trama = "[5,B,"+num_economico_aforo+","+transportista_aforo+","+uid_aforo+","+str(fecha_aforo.replace("-","")[3:]+hora_aforo.replace(":",""))+","+latitud_aforo+","+longitud_aforo+"]"
                                
                                print "\x1b[1;32m"+"Aforo a enviar: " + str(trama)
                                enviado = self.mandar_datos(trama)
                                aforo_enviado = enviado['enviado']
                                respuesta_aforo = enviado['accion']
                                aforo_actualizado_db = False
                                if aforo_enviado:
                                    print "\x1b[1;32m"+"La respuesta de Azure es: " + str(respuesta_aforo)
                                    while aforo_actualizado_db != False or intentos <= 3:
                                        aforo_actualizado_db = actualizar_estado_aforo_mipase_check_servidor("OK", id_aforo)
                                        intentos += 1
                                        if aforo_actualizado_db or intentos >= 3:
                                            intentos = 0
                                            break
                                    if aforo_actualizado_db:
                                        intentos = 0
                                        print "\x1b[1;32m"+"Aforo enviado registrado en BD"
                                    else:
                                        print "\x1b[1;33m"+"No se actualizo el aforo en la base de datos"
                                    self.realizar_accion(enviado)
                                else:
                                    print "\x1b[1;31;47m"+"El aforo no pudo ser enviado"+"\033[0;m"
                            else:
                                break
                        break
                    else:
                        print "\x1b[1;33m"+"No se pudo abrir el puerto de Azure"
                    intentos_enviar_aforos += 1
            else:
                print "\x1b[1;32m"+"Sin aforos pendientes de Azure"
        except Exception, e:
            print "\x1b[1;31;47m"+"Fallo el metodo de enviar aforo: "+str(e)+"\033[0;m"
            
    def enviar_estadisticas_azure(self):
        try:
            estadisticas_pendientes_mipase = obtener_estadisticas_no_enviadas()
            if len(estadisticas_pendientes_mipase) > 0:
                print "\x1b[1;33m"+"Existen estadisticas de mi pase penientes por enviar.."
                configuracion_realizada = False
                abrir_puerto_azure = False
                intentos = 0
                intentos_enviar_estadisticas = 0
                while intentos_enviar_estadisticas <= 2:
                    print "\x1b[1;32m"+"¨Se iniciaran las configuraciones del quectel"
                    while configuracion_realizada != True or intentos <= 3:
                        configuracion_realizada = self.inicializar_configuraciones_quectel()
                        if configuracion_realizada:
                            print "\x1b[1;32m"+"Se configuro el quectel"
                            intentos = 0
                            break
                        intentos += 1
                    if configuracion_realizada:
                        print "\x1b[1;32m"+"Se abrira el puerto"
                        while abrir_puerto_azure != False or intentos <= 3:
                            abrir_puerto_azure = self.abrir_puerto()
                            if abrir_puerto_azure:
                                print "\x1b[1;32m"+"Se abrio el puerto para enviar datos a Azure"
                                intentos = 0
                                break
                            intentos += 1
                    else:
                        print "\x1b[1;33m"+"No se pudo configurar el quectel"
                        continue
                    if abrir_puerto_azure:
                        estadistica_enviada = False
                        id_estadistica = ""
                        unidad_estadistica = ""
                        transportista_estadistica = ""
                        fecha_estadistica = ""
                        hora_estadistica = ""
                        columna_estadistica = ""
                        valor_estadistica = ""
                        print "\x1b[1;32m"+"Se van a enviar datos a Azure"
                        for i in xrange(5):
                            estadistica = obtener_estadisticas_no_enviadas()
                            if len(estadistica) > 0:
                                print "\x1b[1;32m"+"Se encontro esta estadistica" + str(estadistica)
                                id_estadistica = str(estadistica[0][0])
                                unidad_estadistica = str(estadistica[0][1])
                                transportista_estadistica = str(estadistica[0][2])
                                fecha_estadistica = str(estadistica[0][3])
                                hora_estadistica = str(estadistica[0][4])
                                columna_estadistica = str(estadistica[0][5])
                                valor_estadistica = str(estadistica[0][6])
                                
                                if not "ACT" in str(columna_estadistica):
                                    trama = "[9,"+str(unidad_estadistica)+","+str(transportista_estadistica)+","+str(fecha_estadistica.replace("-","")[3:]+hora_estadistica.replace(":",""))+","+str(columna_estadistica)+","+str(valor_estadistica)+"]"
                                else:
                                    trama = "[9,"+str(unidad_estadistica)+","+str(transportista_estadistica)+","+str(fecha_estadistica.replace("-","")[3:]+hora_estadistica.replace(":",""))+","+str(columna_estadistica)+"]"
                                    
                                print "\x1b[1;32m"+"Estadistica a enviar: " + str(trama)
                                enviado = self.mandar_datos(trama)
                                estadistica_enviada = enviado['enviado']
                                respuesta_estadistica = enviado['accion']
                                estadistica_actualizada_db = False
                                if estadistica_enviada:
                                    print "\x1b[1;32m"+"La respuesta de Azure es: " + str(respuesta_estadistica)
                                    while estadistica_actualizada_db != False or intentos <= 3:
                                        estadistica_actualizada_db = actualizar_estado_estadistica_check_servidor("OK", id_estadistica)
                                        intentos += 1
                                        if estadistica_actualizada_db or intentos >= 3:
                                            intentos = 0
                                            break
                                    if estadistica_actualizada_db:
                                        intentos = 0
                                        print "\x1b[1;32m"+"Estadistica enviada registrada en BD"
                                    else:
                                        print "\x1b[1;33m"+"No se actualizo la estadistica en la base de datos"
                                    self.realizar_accion(enviado)
                                else:
                                    print "\x1b[1;31;47m"+"La estadistica no pudo ser enviada"+"\033[0;m"
                            else:
                                break
                        break
                    else:
                        print "\x1b[1;33m"+"No se pudo abrir el puerto de Azure"
                    intentos_enviar_estadisticas += 1
            else:
                print "\x1b[1;32m"+"Sin estadisticas pendientes de Azure"
        except Exception, e:
            print "\x1b[1;31;47m"+"Fallo el metodo de enviar estadistica: "+str(e)+"\033[0;m"
    
    
    def realizar_accion(self, result):
        """
        Si la clave "accion" esta en el diccionario de resultados del servidor, entonces el valor de la clave
        "accion" se asigna a la variable accion. Si accion es igual a "APAGAR", entonces la raspberrry se
        apaga. Si accion es igual a "REINICIAR", entonces se reinicia la raspberry. Si accion es igual a
        "ACTUALIZAR", entonces se actualiza el raspberry
        """
        try:
            if "accion" in result.keys():
                accion = result['accion']
                print "\x1b[1;32m"+"La accion a realizar es: " + str(accion)
                if "C" in accion:
                    try:
                        datos = str(accion).replace("SKT:","").split(',')
                        if len(datos) == 2:
                            try:
                                FTPAlttus.main(self.serial, self.parent, datos[1])
                            except Exception, e:
                                print "\x1b[1;33m"+"No se pudo iniciar la actualizacion remota."
                        else:
                            print "\x1b[1;33m"+"El tamanio de datos de la letra C no son 2."
                    except Exception, e:
                        print "LeerMinicom.py, linea 239: "+str(e)
        except Exception, e:
            print "LeerMinicom.py, linea 255: "+str(e)
    
    ##################### ERNESTO LOMAR #####################

    def reInitApp(self):
        self.settings.setValue("apagado_forzado",1)
        self.write3G(self.stReset3G)
        self.serial.closeRFID()
        self.serial.close3G()
        python = sys.executable
        os.execl(python, python, * sys.argv)

    def write3G(self, cmd):
        i = 0
        while (self.parent.locked):
            self.printDebug(self.RED+self.REVERSE+'### clModem.write 3G ('+cmd+')- Locked ###'+self.RESET)
            time.sleep(1)
            if (i == 30):
                return
            i += 1
        self.parent.locked = True
        self.serial.write3G(cmd)
        self.parent.locked = False

    def write(self, cmd, answer, attempts):
        stRead = ""
        i = 0
        while (self.parent.locked):
            self.printDebug(self.RED+self.REVERSE+str(i)+'.- ### clModem.write ('+cmd+') - Locked ###'+self.RESET)
            time.sleep(1)
            if (i == 30):
                return
            i += 1
        self.parent.locked = True
        if (i != 0):
            self.printDebug(self.parent.REVERSE+self.parent.YELLOW+'### write - '+cmd+'  Unlocked ###'+self.parent.RESET)
        stRead = self.serial.write(cmd, answer, attempts)
        st = " ".join(stRead.split())
        st = " ".join(st.split("\x1A"))
        if ((st.find("RDY") != -1) or (st.find("+PACSP1") != -1) or (st == "AT+")):
            self.printDebug(self.parent.RED+self.parent.REVERSE+'### ERROR RDY / PACSP1 / AT+ - '+st+'   ###'+self.parent.RESET)
            self.serial.write('ATE0\r', ("OK", "ERROR"), attempts)
            '''
            #self.reset()
            self.write('AT+QGPSEND\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
            time.sleep(2)
            #self.write('AT+QGPSDEL=0\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
            #time.sleep(5)
            self.write("AT+QGPS=1\r",("OK", "ERROR"), self.minAttempts)             #---
            '''
        self.parent.locked = False
        if (stRead.find("pdpdeact") != -1) or (stRead.find("closed") != -1):
            self.printDebug(self.parent.RED+" Error write pdpdeact/closed ("+st+")"+self.parent.RESET)
        return stRead

    def initModem(self):
        self.parent.smsEnabled = False
        self.configuraAPN()
        self.configuraFTP()
        #self.configuraSMS()
        self.configuraGPS()
        #if (not self.first):
        self.parent.smsEnabled = True

    def setupModem(self):
        self.parent.smsEnabled = False
        self.printDebug('### Iniciando el modulo de comunicaciones ###')
        self.printDebug('###                v0.10                  ###')
        self.printDebug('#############################################')
        self.idCons = 0
        self.flG = False
        self.flR = True
        paso = 0
        self.flRed = False
        self.parent.iComm = 0
        self.flSIM = False
        self.stFecha = "" 
        self.validaSIM()
        self.configuraTZ()
        self.initModem()
        self.parent.smsEnabled = False
        self.inicializaAPN()
        self.inicializaTCP()
        if (self.first):
            self.syncFecha()
            self.syncVersion()
        #debug = 2
        self.first = False
        self.parent.smsEnabled = True

    def reset(self):
        #return
        stRead = self.write('AT+QICLOSE=0,10\r', ("OK", "ERROR"),1)               #60s
        self.parent.locked = True
#        smsEnabled = self.parent.smsEnabled
#        self.parent.smsEnabled = False
        self.printDebug('### Reiniciando Modem                     ###')
        st = ""
        self.serial.write3G(self.stReset3G)
        time.sleep(2)
        self.serial.write3G("AT+QPOWD\r")                               #300ms
        stAnt = ""
        i = 0
        r = 0
        while ((st.find("PACSP1") == -1)):
            st += self.serial.readln3G()
            if len(st) == len(stAnt):
                time.sleep(2)
                i += 1
            else:
                i = 0
            #print i, ".- ", st
            if (st.find("ERROR") != -1) or (i == 15):
                self.parent.lblError.setText("Reiniciando Modem 3G")
                stRead = self.serial.write('AT+CREG?\r', ("OK", "ERROR"), self.minAttempts)                            #-----
                if (stRead.find("0,0") == -1):
                    r += 1
                    if (r == 5):
                        st = " ".join(st.split())
                        st = " ".join(st.split(","))
                        st = " ".join(st.split("\x00"))
                        stRead = " ".join(stRead.split())
                        stRead = " ".join(stRead.split(","))
                        stRead = " ".join(stRead.split("\x00,"))
                        stRead = st + " - " + stRead                        
                        st = self.write('AT+CSQ\r', ("OK", "ERROR"), self.minAttempts)                                    #300ms       
                        st = " ".join(st.split())
                        st = " ".join(st.split(","))
                        st = " ".join(st.split("\x00"))
                        stRead = stRead + " - " + st
                        fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                        if (self.latitud != ""):
                            lat = str(self.latitud)
                        else:
                            lat = "0"
                        if (self.longitud != ""):
                            lon = str(self.longitud)
                        else:
                            lon = "0"
                        fechaGPS = datetime.datetime.fromtimestamp(self.parent.lastConnection).strftime('%Y-%m-%d %H:%M:%S') 
                        stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",4,"+stRead+","+str(self.parent.csn)+","+lat+","+lon+",0,"+fechaGPS+","+str(fecha)
                        self.clDB.envio(1,stB)
                        self.reInitApp()
                self.serial.write3G("AT+QPOWD\r")                               #300ms
                i = 0
                st = ""
            stAnt = st
        self.parent.rdy = False
        time.sleep(5)
        self.printDebug('###                           Reinicio OK ###')
        self.parent.locked = False
        stRead = self.write('ATE0\r', ("OK", "ERROR"), self.minAttempts)                            #-----
        self.parent.lblError.setText("")
        #self.initModem()
        #self.parent.smsEnabled = smsEnabled
    
    def configuraTZ(self):
        stRead = self.write('ATE0\r', ("OK", "ERROR"), self.minAttempts)                            #-----
        reboot = False

        self.printDebug('### Obteniendo IMEI de Modem            ###')
        self.parent.imei = ""
        stRead = self.write("AT+CGSN\r",("OK","ERROR"), self.minAttempts)                 #300ms
        if(stRead.find("OK") != -1):
            self.printDebug('###                              IMEI OK ###')
            stRead = " ".join(stRead.split())
            stRead = stRead.split(" ")
            self.parent.imei = stRead[0]
        else:
            self.printDebug('###                      ERROR LEER IMEI - NS DEL MODEM  ###')
            self.parent.lblError.setText("ERROR LEER IMEI - NS DEL MODEM")

        self.printDebug('### Configurando Auto GPS                 ###')
        st = ""
        stRead = self.write('AT+QGPSCFG="autogps"\r', ("OK", "ERROR"), self.timeOutGPS)             #-----
        if stRead.find('"autogps",0') != -1:
            stRead = self.write('AT+QGPSCFG="autogps",1\r', ("OK", "ERROR"), self.timeOutGPS)    #----
            reboot = True
        self.printDebug('### Configurando Zona Horaria             ###')
        st = ""
        stRead = self.write('AT+CTZU?\r', ("OK", "ERROR"), self.minAttempts)                         #300ms
        if stRead.find("CTZU: 0") != -1:
            stRead = self.write('AT+CTZU=1\r', ("OK", "ERROR"), self.minAttempts)                 #300ms
            reboot = True
        if reboot:
            os.system("sudo reboot")
        self.printDebug('###                       Zona Horario OK ###')

    def validaSIM(self):
        stRead = self.write('ATE0\r', ("OK", "ERROR"), self.minAttempts)                            #-----
        stRead = self.write("AT+CREG=0\r",("OK","ERROR"), self.minAttempts)                #300ms
        self.printDebug('### VALIDAR MODULO SIM                    ###')
        self.parent.flSIM = False
        stRead = self.write("AT+CPIN?\r",("OK","ERROR"), 8)                    #5s
        if (stRead.find("OK") != -1):
            self.printDebug('###                        TARJETA SIM OK ###')
            stRead = self.write("AT+CCID\r",("OK","ERROR"), self.minAttempts)                 #300ms
            if(stRead.find("+QCCID:") != -1):
                stRead = " ".join(stRead.split())
                j = stRead.find("+QCCID:")
                self.printDebug('###                              ICCID OK ###')
                self.parent.iccid = stRead[j+8:j+28]
                fecha_actual = datetime.date.today()
                hora_actual = datetime.datetime.now().time()
                insertar_estadisticas_alttus(str(self.clDB.economico), self.clDB.idTransportista, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), "SIM", str(self.parent.iccid)) # ID SIM
                fecha_actual = ""
                hora_actual = ""
            else:
                self.parent.iccid = ""
                self.printDebug('###                      ERROR LEER ICCID - NS DE LA SIM ###')
                self.parent.lblError.setText("ERROR LEER ICCID - NS DE LA SIM")
                time.sleep(2)
            stRead = self.write("AT+CREG?\r",("OK","ERROR"), self.minAttempts)                #300ms
            if (stRead.find("+CREG: 0,1") != -1):
                self.printDebug('###             REGISTRO DE SIM EN RED OK ###')
                self.parent.flSIM = True
            if (stRead.find("+CREG: 0,2") != -1):
                self.printDebug('###            FUERA DE ZONA DE COBERTURA ###')
                self.parent.flSIM = True
            elif(stRead.find("+CREG: 0,0") != -1):
                self.printDebug('###  FALLO DE REGISTRO EN LA RED CELULAR  ### ')
                self.parent.lblError.setText("FALLO EN REGISTRO EN LA RED CELULAR")
                self.reset()
        else:
            self.printDebug('###                  ERROR EN TARJETA SIM ###')
            self.parent.lblError.setText("ERROR EN TARJETA SIM")
            self.reset()
        self.parent.lblError.setText("")
        
    def configuraGPS(self):
        self.printDebug('### Iniciando GPS                         ###')
        self.iNoGPS = 0
        self.parent.flGPSOK = False
        stRead = self.write("AT+QGPS?\r",("OK", "ERROR"),40)                   #30s
        #if False:
        if(stRead.find("+QGPS: 1") != -1):
            self.printDebug('###                                GPS OK ###')
            self.parent.flGPSOK = True
        else:
            #stRead = self.write("AT+QGPS=1,"+str(self.timeOutGPS)+",5\r",("OK", "ERROR"), self.minAttempts)             #---
            stRead = self.write("AT+QGPS=1\r",("OK", "ERROR"), self.minAttempts)             #---
            if (stRead.find("OK") != -1) or (stRead.find("504") != -1):
                self.printDebug('###                                GPS OK ###')
                self.parent.flGPSOK = True
            else:
                self.printDebug('                          ERROR EN EL GPS ###')
    
    def configuraAPN(self):
        self.printDebug('### CONFIGURAR APN                        ###')
        self.parent.APN = False
        stRead = self.write('AT+QICSGP=1\r', ("OK", "ERROR"), self.minAttempts)                                   #-----
        if (stRead.find(self.clDB.urlAPN) != -1):
            self.printDebug('###                                APN OK ###')
            self.parent.APN = True
        else:
            cmd =   'AT+QICSGP=1,1,"%s","%s","%s",1\r' % (self.clDB.urlAPN, self.clDB.userAPN, self.clDB.pwdAPN)
            stRead = self.write(cmd, ("OK", "ERROR"), self.minAttempts)                               #----
            if (stRead.find("OK") == -1):
                self.printDebug('###               FALLO AL CONFIGURAR APN ###')
                self.parent.lblError.setText("FALLO AL CONFIGURAR APN")
                stRead = self.write("AT+QIDEACT=1\r",("OK", "ERROR"), 50)                  #40s
                if (stRead.find("ERROR") != -1):
                    self.printDebug('###            ERROR EN ACTIVACION DE APN ###')
                    self.parent.lblError.setText("ERROR EN ACTIVACION DE APN")
                    time.sleep(2)
                    #self.reset()
            else:
                self.printDebug('###                  CONFIGURACION APN OK ###')
                self.parent.APN = True
        self.parent.lblError.setText("")
        
    def configuraFTP(self): 
        self.printDebug('### CONFIGURACION FTP                     ###')
        cmd ='AT+QFTPCFG="account","%s","%s"\r'% (self.clDB.userFTP, self.clDB.pwdFTP)
        stRead = self.write(cmd, ("OK", "ERROR"), self.minAttempts)                                       #----
        stRead = self.write('AT+QFTPCFG="filetype",0\r', ("OK", "ERROR"), self.minAttempts)               #----
        stRead = self.write('AT+QFTPCFG="transmode",0\r', ("OK", "ERROR"), self.minAttempts)              #----
        stRead = self.write('AT+QFTPCFG="contextid",1\r', ("OK", "ERROR"), self.minAttempts)              #----
        stRead = self.write('AT+QFTPCFG="rsptimeout",'+str(self.timeOutFTP)+'\r', ("OK", "ERROR"), self.minAttempts)            #----
        stRead = self.write('AT+QFTPCFG="ssltype",0\r', ("OK", "ERROR"), self.minAttempts)                #----
        stRead = self.write('AT+QFTPCFG="sslctxid",1\r', ("OK", "ERROR"), self.minAttempts)               #----
        self.printDebug('###                       CONEXION FTP OK ###')

    def configuraSMS(self):
        #self.parent.smsEnabled = False
        self.printDebug('### Configuracion SMS                     ###')
        flSMS = False
        while (not flSMS):
            stRead = self.write("AT+CMGF=1\r",("OK", "ERROR"), self.minAttempts)                  #300ms
            if(stRead.find("OK") != -1):
                self.printDebug('###                         MODULO SMS OK ###')
                #stRead = self.write("AT+CMGD=1,4\r",("OK", "ERROR"), self.minAttempts)                  #300ms
                flSMS = True
            else:
                self.printDebug('###                   ERROR en Modulo SMS ###')
                self.parent.lblError.setText("ERROR en Modulo SMS")
                time.sleep(1)
        self.parent.lblError.setText("")

    def inicializaAPN(self):
        self.printDebug('### INICIALIZANDO CONEXION APN            ###')
        self.parent.flRed = False
        while (not self.parent.flRed):
            if self.senial3G():
                stRead = self.write("AT+QIACT?\r", ("OK","ERROR"), 160)                      # 150seg
                if (stRead.find("+QIACT: 1,1,1") != -1):
                    self.printDebug('                        Conx PDP Conf Ant ###')
                    if (stRead != ""):
                        self.stIP = " ".join(stRead.split())
                        self.stIP = self.stIP.split(" ")
                        self.stIP = self.stIP[1].split(",")
                        if (len(self.stIP) > 2):
                            self.stIP = self.stIP[3][1:-1]
                            self.printDebug('###                     ACTIVACION PDP OK ### '+"  "+self.stIP)
                            self.parent.flRed = True
                            #self.configuraFTP()
                        else:
                            self.stIP = ""
                            self.printDebug('###                   FALLO AL Obtener IP ###')
                            self.parent.lblError.setText("FALLO AL OBTENER LA IP")
                            time.sleep(1)
                else:
                    stRead = self.write('AT+QIDEACT=1\r', ("OK", "ERROR"), 50)          # 40seg
                    stRead += self.write('AT+QIACT=1\r', ("OK", "ERROR"), 160)            # 150seg
                    if (stRead.find("ERROR") != -1):
                        self.printDebug('###            ERROR EN ACTIVACION DE APN ###')
                        self.parent.lblError.setText("ERROR EN ACTIVACION DE APN")
                        time.sleep(2)
                        #self.reset()
            else:
                self.printDebug("Inicializa APN Error: Bad Signal Quality: "+str(self.parent.iComm ))
                self.parent.lblError.setText("Inicializa APN Error: Bad Signal Quality: "+str(self.parent.iComm ))
                time.sleep(10)
        self.parent.lblError.setText("")

    def reInicializaAPN(self):
        self.parent.flRed = False
        self.parent.flSocket = False
        self.printDebug('###  Reiniciando Conexion General        ###')
        self.write3G(self.stReset3G)
        self.printDebug('###           Cerrando conexion  TCP      ###')
        stRead = self.write('AT+QICLOSE=0,10\r', ("OK", "ERROR"), 10)               #60s
        self.printDebug('###           Cerrando conexion  APN      ###')
        stRead += self.write('AT+QIDEACT=1\r', ("OK", "ERROR"), 50)                  #40s
        if (stRead.find("ERROR") != -1):
            self.printDebug('###            ERROR EN ACTIVACION DE APN ###')
            self.parent.lblError.setText("ERROR EN ACTIVACION DE APN")
            #self.reset()
        self.inicializaAPN()
        self.inicializaTCP()
        
    def inicializaTCP(self):
        self.parent.flSocket = False
        self.parent.flRed = False
        self.printDebug('### CONEXION TCP                          ### ')
        if self.senial3G():
            
            self.reAsignarConexionCytibus()
            
            cmd =  'AT+QIOPEN=1,0,"TCP","%s",%s,0,0\r' % (self.clDB.urlSocket, self.clDB.puertoSocket)
            stRead = self.write(cmd, ("QIOPEN:", "ERROR"), 1)                          #150seg
            if(stRead.find("QIOPEN: 0,0") != -1):
                self.printDebug('###                       CONEXION TCP OK ### ')
                self.parent.flSocket = True
                self.parent.flRed = True
            else:
                if(stRead.find('562') != -1):
                    self.printDebug('###                           TCP ABIERTA ### ')
                    self.parent.flSocket = True
                    self.parent.flRed = True
                elif(stRead.find('552') != -1):
                    self.printDebug('###                 SERVIDOR DESCONECTADO ### ')
                    stRead = self.write('AT+QICLOSE=0,10\r', ("OK", "ERROR"), 1)       #,60seg
                else:
                    self.printDebug('###                             ERROR TCP ### ')
                    self.parent.lblError.setText("ERROR CONEXION TCP")
                    stRead = self.write('AT+QICLOSE=0,10\r', ("OK", "ERROR"), 1)       #,60seg
                    self.parent.flRed = True
        else:
            self.printDebug("Error: Bad SignalQuality --- INIT TCP."+str(self.parent.iComm ))
            self.parent.lblError.setText("Error TCP: Bad Signal Quality: "+str(self.parent.iComm ))
        self.parent.lblError.setText("")

    def reInicializaTCP(self):
        self.printDebug('###           Cerrando conexion  TCP      ###')
        #self.write3G(self.stReset3G)
        stRead = self.write('AT+QICLOSE=0,10\r', ("OK", "ERROR"),1)               #60s
        self.inicializaTCP()

    def syncFecha(self):
        if os.path.exists("/lib/systemd/system/innobus.service"):
            stService = "*"
        else:
            stService = "-"
        if os.path.exists("/etc/debian_version"):
            f = open("/etc/debian_version")
            stVersion = f.readline()
            f.close()
            stVersion = stVersion[:-1]
        else:
            stVersion = "."
        if os.path.exists("/usr/bin/arduino"):
            stVersion = stVersion + " a"
        else:
            stVersion = stVersion + "  "
        if os.path.exists("/usr/bin/avrdude"):
            stVersion = stVersion + "v"
        else:
            stVersion = stVersion + " "
        if os.path.exists("/dev/ttyUSB_0"):
            stVersion = stVersion + "U"
        else:
            stVersion = stVersion + " "
        if os.path.exists("/home/pi/innobusmx/application"):
            stVersion = stVersion + "G"
        else:
            stVersion = stVersion + " "
        comando = ""
        if os.path.exists("/sys/block/mmcblk0/device/cid"):
            f = open("/sys/block/mmcblk0/device/cid")
            self.parent.sd = f.readline()
            f.close()
            self.parent.sd = self.parent.sd[:-1]
        else:
            self.parent.sd = ""
        while (not self.parent.flFecha):
            self.printDebug('###   Sincronizando Fecha con Proveedor   ###')
            stRead = self.write("AT+CCLK?\r",("OK","ERROR"), self.minAttempts)                       #300ms
            i = stRead.find('"')
            if (stRead != ""):
                #if True:
                try:
                    if (int(stRead[i+1:i+3]) > 17 and int(stRead[i+1:i+3]) < 50):
                        stFecha = "20"+stRead[i+1:i+3]+"-"+stRead[i+4:i+6]+"-"+stRead[i+7:i+9]+" "+stRead[i+10:i+18]
                        fecha = datetime.datetime(int("20"+stRead[i+1:i+3]), int(stRead[i+4:i+6]), int(stRead[i+7:i+9]), int(stRead[i+10:i+12]), int(stRead[i+13:i+15]), int(stRead[i+16:i+18])) - datetime.timedelta(hours=int(stRead[i+19:i+21])/4)
                        stFecha = fecha.strftime("%Y/%m/%d %H:%M:%S")
                        comando = 'sudo date --set "%s"'%str(stFecha)
                        self.parent.flFecha = True
                        self.printDebug('###  FECHA Proveedor '+stFecha)
                        self.stFecha = stVersion + "R" + stService 
                    else:        
                        self.printDebug('###                  No hay Servicio      ###')
                        self.printDebug('###   Sincronizando fecha con Servidor    ###')
                        i = 0
                        fecha = self.sendData("0,"+str(self.clDB.idUnidad))
                        if (fecha != ""):
                            fecha = " ".join(fecha.split()) #se le aplica un split al mismo comando
                            fecha = fecha.split(' ')
                            stRead = "\""+fecha[2]+' '+fecha[3]+"\""
                            self.printDebug('###   Fecha Servidor '+stRead+'         ###')
                            comando = 'sudo date --set %s'%str(stRead)
                            self.parent.flFecha = True
                            self.stFecha = stVersion + "S" + stService 
                        else:
                            self.printDebug('###                  No hay Conexion   ###')
                            self.parent.lblError.setText("NO SE PUEDE SINCRONIZAR LA FECHA")
                #else:
                except:
                    self.printDebug("Error:"+stRead)
                    self.parent.lblError.setText("ERROR: "+stRead)
        self.parent.lblError.setText("")
        if (comando != ""):
            os.system(comando)

    def syncVersion(self):
        self.printDebug('### Sincronizando Versiones del Validador ###')
        i = 0
        self.parent.cpuSerial = ""
        cpuHardware = ""
        cpuRevision = ""
        #if True:
        try:
            f = open('/proc/cpuinfo','r')
            for line in f:
                if line[0:8] == 'Hardware':
                    cpuHardware = line[11:-1]
                if line[0:8] == 'Revision':
                    cpuRevision = line[11:-1]
                if line[0:6] == 'Serial':
                    self.parent.cpuSerial = line[10:-1]
            f.close()
        #else:
        except:
            self.parent.cpuSerial   = "-----"
            cpuHardware = "-----"
            cpuRevision = "-----"
        while ((i < 100) and (self.parent.serialNumber == '')):
            #print i, "Esperando NS Validador"
            i += 1
            time.sleep(5)
        i = 0
        dato = ""
        self.parent.lblNSFirmware.setText(self.parent.version+"   "+self.parent.cpuSerial)
        while (dato == ""):
            dato = self.sendData("I,"+str(self.clDB.idUnidad)+","+self.parent.iccid+","+self.parent.serialNumber+","+self.parent.stVersion+","+self.parent.version+","+self.stFecha+","+self.stIP+","+str(self.clDB.economico)+","+self.parent.imei+","+self.parent.sd+","+self.parent.cpuSerial+","+cpuHardware+","+cpuRevision)
            i += 1
            if (dato == ""):
                self.parent.lblError.setText("Syncronizando Version del Validador. Intento "+str(i))
                self.printDebug('###  Sincronizando Software con Servidor  ### ' + str(i))
                time.sleep(2)
        self.parent.lblError.setText("")
        i = 0
        dato = self.sendData("S,0,"+str(self.clDB.idUnidad)+",Prepago")
        dato = " ".join(dato.split()) #se le aplica un split al mismo comando
        dato = dato.split('@')
        if (len(dato) > 2):
            self.parent.flFTP = True
            self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
            if (dato[3] == 'd'):
                self.parent.lblNombreOperador.setText("Copiando "+dato[1]+".....")
                self.subirArchivoFTP(dato[1],dato[2])
                stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0\r'                # latitud = 3  ----> SyncSoftware OK
                stGPS = self.sendData(stGPS)
            else:    
                self.parent.lblNombreOperador.setText("Actualizando Software "+self.parent.stVersion)
                '''
                cmd =  'AT+QFTPOPEN="%s",%s\r' % (self.clDB.urlFTP, self.clDB.puertoFTP)
                stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                                       #20s
                if (stRead.find('601') != -1):
                    stRead = self.write("AT+QFTPCLOSE\r", ("+QFTPCLOSE", "ERROR"), self.timeOutFTP)          #FTPTimeOut = 20
                    time.sleep(1)
                    stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                                       #20s
                elif (stRead.find('625') != -1) or (stRead.find('530') != -1):
                    self.printDebug('### NOT LOGGED IN FTP                     ###')
                    self.configuraFTP()
                    stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                                       #20s
                self.printDebug('### CONEXION FTP                          ###')
                if (stRead.find("QFTPOPEN: 0,0") != -1):
                    self.printDebug('###                       CONEXION FTP OK ###')
                '''

                if (self.descargarArchivoFTP(dato[2],dato[3], True)):
                    stRead = self.sendData("S,1,"+str(self.clDB.idUnidad)+","+dato[2])
                    if (dato[4] == "r") or (dato[4] == "U") or (dato[4] == "B"):
                        stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                        #print "envio", stGPS
                        stGPS = self.sendData(stGPS)
                        #print "resultado", stGPS
                        self.reInitApp()
                    if (dato[4] == "R"):
                        stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0\r'   # latitud = 1    ----> Reinicio OK
                        stGPS = self.sendData(stGPS)
                        #self.printDebug("Reboot:"+dato[4])
                        self.write3G(self.stReset3G)
                        os.system('sudo reboot')
                    if (dato[4] == "A") or (dato[4] == "a"):
                        self.parent.sendData = True
                        self.serial.closeRFID()
                        #self.serial.setupB(True)
                        self.parent.updateFirmware = True
                        time.sleep(3)
                        okb = 0
                        ok = 0
                        i = 0
                        while (ok != 3) and (i < 5):
                            i += 1
                            self.parent.lblError.setText(str(i) + "  Actualizando Firmware .....")
                            self.printDebug(str(i) + "  Actualizando Firmware .....")
                            os.system('sudo avrdude -v -patmega328p  -c avrisp -Uflash:w:'+dato[3]+':i -carduino -b 115200 -P '+self.serial.sPort+' -l /tmp/log -F')
                            if os.path.exists("/tmp/log"):
                                f = open("/tmp/log")
                                st = f.readline()
                                ok = 0
                                while st:
                                    if (st.find('### | 100%') != -1):
                                        ok += 1
                                    self.printDebug(st)
                                    st = f.readline()
                                f.close()
                                if (ok == 3):
                                    self.parent.lblError.setText("Actualizacion de Firmware OK.....")
                                    self.printDebug("Actualizacion de Firmware OK.....")
                                    msg = "Actualizacion de Firmware OK....."
                                else:
                                    self.parent.lblError.setText("ERROR en actualizacion.....intento: "+str(i))
                                    self.printDebug("ERROR Firmware: Actualizacion no se realizo.  Intento: "+str(i))
                                    msg = "ERROR Firmware: Actualizacion no se realizo.  Intento: "+str(i)
                                time.sleep(2)
                        if (ok == 3):
                            os.rename(dato[3],'/home/pi/innobusmx/data/sync/bak')
                        else:
                            #if True:
                            try:
                                msg += "Kill"
                                os.system("sudo killall -9 avrdude")
                                msg += "-Remove "
                                os.remove(dato[3])
                                msg += "-Exists "
                                if os.path.exists("/home/pi/innobusmx/data/sync/bak"):
                                    j = 0
                                    msg += "-while "
                                    while (j < 5):
                                        j += 1
                                        msg += "-avrdude "
                                        os.system('sudo avrdude -v -patmega328p  -c avrisp -Uflash:w:/home/pi/innobusmx/data/sync/bak:i -carduino -b 115200 -P '+self.serial.sPort+' -l /tmp/log.bak -F')
                                        if os.path.exists("/tmp/log.bak"):
                                            msg += "-open "
                                            f = open("/tmp/log.bak")
                                            st = f.readline()
                                            okb = 0
                                            while st:
                                                if (st.find('### | 100%') != -1):
                                                    okb += 1
                                                st = f.readline()
                                            f.close()
                                            if (okb == 3):
                                                msg += "ERROR FATAL: No se pudo restarar Firware"
                                                break
                                        else:
                                            msg += "ERROR Firmaware: No existe tmp/log.bak"                                    
                                        if (j == 5):
                                            msg += "ERROR Firmware: Restauracion Exitosa"
                                else:
                                    msg += "Error Firmware: Respaldo no encontrado"
                            #else:
                            except:
                                self.printDebug("Error probablemante archivo no encontrado") 
                                msg +=  "Error  Firmware: probablemante archivo no encontrado"
                        #self.serial.setupB(False)
                        self.parent.sendData = False
                        stRead = self.sendData("Err,1,"+str(self.clDB.idUnidad)+","+msg)
                        if (ok == 3):
                            stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0\r'    # latitud = 3   ----> SyncSoftware OK
                            stGPS = self.sendData(stGPS)
                            if (dato[4] == "A"):
                                self.reInitApp()
                        self.parent.updateFirmware = False
                        self.serial.setupRFID()
                        self.parent.lblError.setText("")
                    if ((dato[4] == "b") or (dato[4] == "B")):
                        stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0\r'        # latitud = 3   ----> SyncSoftware OK
                        stGPS = self.sendData(stGPS)
                        os.system("sudo chmod +x /home/pi/innobusmx/script/innobusmx.sh")
                        os.system("/home/pi/innobusmx/script/innobusmx.sh")
                        os.system("rm /home/pi/innobusmx/script/*")
                        os.system("rmdir /home/pi/innobusmx/script")
                        if (dato[4] == "B"):
                            self.write3G(self.stReset3G)
                            os.system("sudo reboot")
                else:
                    try:
                        self.printDebug('###              ERROR LEER ARCHIVOFTP ###')
                        if ((dato[4] == "b") or (dato[4] == "B")or (dato[4] == "a") or (dato[4] == "A")):
                            stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0\r'        # latitud = 3   ----> SyncSoftware OK
                            stGPS = self.sendData(stGPS)
                    except:
                        self.printDebug('###              ERROR LEER ARCHIVOFTP ###')
                #else:
                #    self.printDebug('###                             ERROR FTP ###')
            self.parent.lblNombreOperador.setText("")
            stRead = self.write("AT+QFTPCLOSE\r", ("QFTPCLOSE:", "ERROR"), self.timeOutFTP)                  #----
            self.parent.flFTP = False

    def senial3G(self):
        senial = 0
        n = 0
        #if self.rdy:
        #    self.write('AT+CREG=0\r', ("OK", "ERROR"), self.minAttempts)                                    #300ms
        #    self.write('ATE0\r', ("OK", "ERROR"), self.minAttempts)                                    #300ms
        stRead = self.write('AT+COPS?\r', ("OK", "ERROR"), self.minAttempts)                                    #300ms
        #print "self write ", stRead
        #if True:
        try:
            j = stRead.find("+COPS:")
            if (j != -1):
                stRead = stRead[j:]
                stRead = " ".join(stRead.split())
                stRead = stRead.split(",")
                #print "split ",stRead
                if (len(stRead) == 4):
                    if (stRead[3][0] != "0") and (stRead[3][0] != "3"):
                        n = 1
                elif ((len(stRead) == 1) and (stRead[0] == "+COPS: 2 OK")):
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,"+stRead[0]+","+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    #print stB
                    self.clDB.envio(1,stB)
                    self.reset()
                
        #else:
        except:
            n = 0
            #print "n = 0"
        if (n == 1):
            stRead = self.write('AT+CSQ\r', ("OK", "ERROR"), self.minAttempts)                                    #300ms       
            if (stRead.find("OK") != -1):
                stRead = " ".join(stRead.split())
                if (stRead.find("AT+CSQ") != -1):
                    self.printDebug('Se activo el Echo')
                    self.write('ATE0\r', ("OK", "ERROR"), self.minAttempts)                                    #300ms
                j = stRead.find("+CSQ:")
                if (j != -1):
                    stRead = stRead[j:]
                    #if True:
                    try:
                        i = stRead.find(",")
                        if (i != -1):
                            senial = int(stRead[i-2:i])
                    #else:
                    except:
                        senial = 0
                else:
                    self.printDebug("Error: Casting int() SignalQuality. "+stRead)
            else:
                self.printDebug("Error: SignalQuality. "+stRead)
        self.parent.iComm = senial
        #self.parent.lblError.setText("Signal: "+str(self.parent.iComm))       
        return (senial > self.minCSQ and senial != 99) and (n == 1)
    
    def TCPStatus(self):
        tcpStatus = False
        if self.senial3G():
            stRead = self.write('AT+QISTATE=0,1\r', ("OK", "ERROR"), self.minAttempts)                                    #300ms
            if (stRead.find("OK") != -1):
                stRead = " ".join(stRead.split())
                stRead = stRead.split(",")
                if (len(stRead) == 10):
                    tcpStatus = (stRead[5] == '2')
                    if (not tcpStatus):
                        self.parent.lblError.setText("ERROR: Se perdio la conexion con el Servidor.")
                        self.printDebug("ERROR: Validador desconectado del Servidor.")
                        self.reInicializaTCP()                    
                else:
                    print "Se va a reiniciar el TCP."
                    self.reInicializaTCP()
            #elif (stRead.find("ERROR") != -1):
            #    self.reset()
        else:
            self.parent.lblError.setText("ERROR: Bad SignalQuality. "+str(self.parent.iComm))
            self.printDebug("Error: Bad SignalQuality. "+str(self.parent.iComm))
        self.parent.flSocket = tcpStatus
        return tcpStatus

    def sendData(self, data):
        result = ""
        self.parent.waitting = True
        if self.TCPStatus():
            print "Ya se verifico el status de TCP."
            stRead = self.write('AT+QIRD=0\r', ("OK", "ERROR"), self.minAttempts)             #----
            self.parent.sendData = True
            stRead = self.write('AT+QISEND=0\r', ("ERROR", '>'), self.minAttempts)              #---
            if (stRead.find(">") != -1):
                cmd = data+"\r\x1A"
                stRead = self.write(cmd,("FAIL", 'recv', 'ERROR'), self.minAttempts)                  #---
                if (stRead.find('"recv",0') != -1):
                    result = self.write('AT+QIRD=0\r', ("OK", "ERROR"), self.minAttempts)             #----
                #elif (stRead.find('RDY') != -1):
                #    result = self.write(stReset3G, ("OK", "OK"), 1)             #----
        else:
            time.sleep(1)
            self.parent.lblError.setText("")        
        self.parent.sendData = False
        self.parent.waitting = False
        return result

    def gpsOn(self):
        self.flGPSOn = True
        #stRead = self.write("AT+QGPS=1,"+str(self.timeOutGPS)+",5\r",("OK", "ERROR"), self.minAttempts)             #---
        stRead = self.write("AT+QGPS=1\r",("OK", "ERROR"), self.minAttempts)             #---
        if (stRead.find("OK") != -1) or (stRead.find("504") != -1):
            self.printDebug('###                                GPS OK ###')
            self.parent.flGPSOK = True
        else:
            self.printDebug('                          ERROR EN EL GPS ###')
            self.parent.flGPSOK = False
        
    def gpsOff(self):
        self.flGPSOn = False
        self.parent.flGPSOK = False
        self.printDebug('### Cerrando GPS                         ###')
        stRead = self.write("AT+QGPSEND\r",("OK", "ERROR"), self.timeOutGPS)                               #---
        time.sleep(1)

    def gpsOffDel(self):
        self.flGPSOn = False
        self.parent.flGPSOK = False
        self.printDebug('### Cerrando GPS                         ###')
        stRead = self.write("AT+QGPSEND\r",("OK", "ERROR"), self.timeOutGPS)                               #---
        time.sleep(2)
        self.write('AT+QGPSDEL=0\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
        time.sleep(2)

    def cmdDebug(self, cmd, answer, attempts):
        st = self.write(cmd, answer, attempts)
        st = " ".join(st.split())
        return st

    def returnGPS(self, stGPS):
        self.parent.lastConnection = time.time()
        st = ""
        stGPS = ''.join(stGPS)
        stGPS = stGPS.split("\r\n")
        if (len(stGPS) > 1):
            stGPS = stGPS[2].split("@")
            st = stGPS[0]
            if (len(stGPS) > 1):
                if (stGPS[1] == "d"):
                    self.subirArchivoFTP(stGPS[2],stGPS[3])
                    st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0\r'    # latitud = 3   ----> SynSoftware OK
                    st = self.sendData(st)
                '''
                if (stGPS[1] == "IV"):
                    st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',1,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                    st = self.sendData(stGPS)
                if (stGPS[1] == "CV"):
                    #print "Cerrar Vuelta"
                    self.clDB.dbAforo.execute('UPDATE vuelta SET termino = "'+stGPS[3]+'", csnTermino = "'+self.parent.csn+'", enviadoTermino = 0 WHERE idRecorrido = '+stGPS[3]+' AND idRuta = '+str(self.clDB.idRuta)+' AND vuelta = '+str(self.parent.noVuelta))
                    self.clDB.dbAforo.commit()      
                    self.parent.flSendTerminoVuelta = True
                    self.parent.lblVuelta.setText("")
                    self.parent.noVuelta = 0


                    stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',1,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                    stGPS = self.sendData(stGPS)



                if (stGPS[1] == "CR"):
                        #print "Cerrando Recorrido "+str(self.parent.idRecorrido)+" en Terminal"
                        #print("UPDATE recorrido SET termino = '"+self.datetimes+"', csnTermino = '"+self.parent.csn+"', enviadoTermino = 0 WHERE idRecorrido = " + str(self.parent.idRecorrido))
                        c.execute("UPDATE recorrido SET termino = '"+self.datetimes+"', csnTermino = '"+self.parent.csn+"', enviadoTermino = 0 WHERE idRecorrido = " + str(self.parent.idRecorrido))
                        self.clDB.dbAforo.commit()
                        self.parent.idRecorrido = 0 
                        self.parent.flSendTerminoRecorrido = True
                if (stGPS[1] == "IR"):
                    if (self.parent.idRecorrido == 0):
                        #print "Iniciar Recorrido"
                        #print('INSERT INTO recorrido (inicio, csnInicio, idTurno, enviadoInicio) VALUES ("'+str(time.strftime("%Y-%m-%d %H:%M:%S"))+'","'+str(self.parent.csn)+'",0,0)')
                        c.execute('INSERT INTO recorrido (inicio, csnInicio, idTurno, enviadoInicio) VALUES ("'+str(time.strftime("%Y-%m-%d %H:%M:%S"))+'","'+str(self.parent.csn)+'",0,0)')
                        self.clDB.dbAforo.commit()
                        self.parent.flSendInicioRecorrido = True
                        #print('SELECT last_insert_rowid()')
                        c.execute('SELECT last_insert_rowid()')
                        d = c.fetchone()
                        self.parent.idRecorrido = d[0]
                        #print "Recorrido: ",self.parent.idRecorrido
                '''
                if (stGPS[1] == "R"):
                    st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',1,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                    st = self.sendData(st)
                    self.write3G(self.stReset3G)
                    os.system("sudo reboot")
                if (stGPS[1] == "r"):
                    st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',1,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                    st = self.sendData(st)
                    self.reInitApp()
                if ((stGPS[1] == "u") or (stGPS[1] == "U") or (stGPS[1] == "b") or (stGPS[1] == "B")):
                    if (self.descargarArchivoFTP(stGPS[2],stGPS[3], True)):
                        st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                        st = self.sendData(st)
                        if ((stGPS[1] == "b") or (stGPS[1] == "B")):
                            os.system("sudo chmod +x /home/pi/innobusmx/script/innobusmx.sh")
                            os.system("/home/pi/innobusmx/script/innobusmx.sh")
                            os.system("rm /home/pi/innobusmx/script/*")
                            os.system("rmdir /home/pi/innobusmx/script")
                        if (stGPS[1] == "U") or (stGPS[1] == "B"):
                            self.reInitApp()

                '''
                if ((stGPS[1] == "u") or (stGPS[1] == "U") or (stGPS[1] == "a") or (stGPS[1] == "A") or (stGPS[1] == "b") or (stGPS[1] == "B")):
                    self.syncVersion()
                    if (stGPS[1] == "U") or (stGPS[1] == "A") or (stGPS[1] == "B"):
                        self.reInitApp()

                    if self.descargarArchivoFTP(stGPS[2],stGPS[3], True):
                        stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0'    # latitud = 3   ----> SynSoftware OK
                        s = self.sendData(stGPS)
                        if (stGPS[1] == "U") or (stGPS[1] == "A") or (stGPS[1] == "B"):
                            self.reInitApp()
                    
                    self.syncVersion()
                if ((stGPS[1] == "u") or (stGPS[1] == "U")):
                    #stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0\r'    # latitud = 3   ----> SynSoftware OK
                    #stGPS = self.sendData(stGPS)
                    self.syncVersion()
                    if (stGPS[1] == "U"):
                        self.reInitApp()
                if (stGPS[1] == "a") or (stGPS[1] == "A"):
                    #stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0\r'    # latitud = 3   ----> SynSoftware OK
                    #stGPS = self.sendData(stGPS)
                    self.syncVersion()
                    if (stGPS[1] == "A"):
                        self.reInitApp()
                if (stGPS[1] == "b") or (stGPS[1] == "B"):
                    #stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',3,0,0,0,0\r'    # latitud = 3   ----> SynSoftware OK
                    #stGPS = self.sendData(stGPS)
                    self.syncVersion()
                    if (stGPS[1] == "B"):
                        self.reInitApp()
                '''
                if (stGPS[1] == "g"):
                    st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',1,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                    st = self.sendData(st)
                    self.gpsOff()
                if (stGPS[1] == "h"):
                    st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',1,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                    st = self.sendData(st)
                    self.gpsOffDel()
                if (stGPS[1] == "G"):
                    st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',1,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                    st = self.sendData(st)
                    self.gpsOn()
                if (stGPS[1] == "v"):
                    c = self.clDB.dbVigencias.cursor()
                    c.execute("SELECT csn FROM vigencia WHERE csn = '"+str(stGPS[2])+"'")
                    d = c.fetchone()
                    try:
                        if (d is None): 
                            self.clDB.dbVigencias.execute("INSERT INTO vigencia (csn, vigencia) VALUES ('"+str(stGPS[2])+"',"+str(stGPS[3])+")")
                        else:
                            self.clDB.dbVigencias.execute("UPDATE vigencia SET vigencia = "+str(stGPS[3])+" WHERE csn = '"+str(stGPS[2])+"'")
                        self.clDB.dbVigencias.commit()
                    except:
                        return st
                    st = self.sendData("v,"+stGPS[2]+","+str(self.clDB.idUnidad))
                if (stGPS[1] == "V"):
                    self.clDB.dbVigencias.execute("DELETE FROM vigencia WHERE csn = '"+str(stGPS[2])+"'")
                    self.clDB.dbVigencias.commit()
                    st = self.sendData("V,"+stGPS[2]+","+str(self.clDB.idUnidad))
                    #stGPS = self.sendData(stGPS)
                if (stGPS[1] == "9"):
                    self.descargarFotografia(stGPS[2])
                if (stGPS[1] == "8"):
                    c = self.clDB.dbListaNegra.cursor()
                    #if True:
                    try:
                        c.execute("INSERT INTO csn (csn) values ('"+stGPS[2]+"')")
                    #else:
                    except:
                        print "Ya se registro"
                    st = self.sendData("8,"+stGPS[2]+","+str(self.clDB.idUnidad))
                    c.close()
                    c = None

                if (stGPS[1] == "T"):
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    os.system('sudo date --set "'+str(stGPS[2])+'"')                  
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,Hora "+str(fecha)+ " a "+str(stGPS[2])+","+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True                   
                if (stGPS[1] == "m"):
                    stRead = ""
                    stRead = stRead + self.cmdDebug('AT+QGPSLOC=2\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    stRead = stRead + self.cmdDebug('AT+QGPS?\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    stRead = stRead + self.cmdDebug('AT+QGPSCFG="outport"\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    stRead = stRead + self.cmdDebug('AT+QGPSCFG="nmeasrc"\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    stRead = stRead + self.cmdDebug('AT+QGPSCFG="gpsnmeatype"\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    stRead = stRead + self.cmdDebug('AT+QGPSCFG="glonassnmeatype"\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    stRead = stRead + self.cmdDebug('AT+QGPSCFG="glonassenable"\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    stRead = stRead + self.cmdDebug('AT+QGPSCFG="odpcontrol"\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    stRead = stRead + self.cmdDebug('AT+QGPSCFG="dpoenable"\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    stRead = stRead + self.cmdDebug('AT+QGPSCFG="lnacontrol"\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    stRead = stRead + self.cmdDebug('AT+QGPSCFG="autogps"\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    stRead = stRead.replace(',',' ')
                    stRead = stRead.replace('"',' ')
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,"+stRead+","+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True
                    st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',1,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                    st = self.sendData(st)
                if (stGPS[1] == "x"):
                    st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',1,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                    st = self.sendData(st)
                    self.parent.locked = True
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setup(8,GPIO.OUT)
                    #print "apagando GPIO"
                    GPIO.output(8,GPIO.LOW)
                    time.sleep(3)
                    #print "activando GPIO"
                    GPIO.output(8,GPIO.HIGH)
                    st = ""
                    stAnt = ""
                    i = 0
                    while ((i < 10) and (st.find("PACSP1") == -1)):
                        st += self.serial.readln3G()
                        #print st
                        if (len(st) == len(stAnt)):
                            time.sleep(2)
                            i += 1
                        else:
                            i = 0
                            stAnt = st
                    self.parent.rdy = False
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    if (i == 30):
                        stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,No Reinicio i=30,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    else:
                        stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,Reincio Ok,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.parent.locked = False
                    self.reset()
                    self.write('AT+QGPSEND\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    time.sleep(2)
                    self.write('AT+QGPSDEL=0\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
                    time.sleep(2)
                    self.write("AT+QGPS=1\r",("OK", "ERROR"), self.minAttempts)             #---
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True
                if (stGPS[1] == "y"):
                    st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',1,0,0,0,0\r'    # latitud = 1   ----> Reinicio OK
                    st = self.sendData(st)
                    self.reset()
                    
        return st


    def obtenerCoordenadaGPS(self):
      '''
      self.idCons = 100
      print "Coordenada de Inicio de GPS"
      self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
      self.idTerminal(22.18122, -101.02755)
      time.sleep(10)
      print
      print "Terminal 1 Inicio de Vuelta"
      self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
      self.idTerminal(22.19122, -101.02755)
      time.sleep(15)
      print
      print "Coordenada de salida T1"
      self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
      self.idTerminal(22.18122, -101.02755)
      time.sleep(15)
      print
      print "Punto Control 1", self.clDB.idRuta
      self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
      self.idTerminal(22.17391,-101.01379)
      time.sleep(15)
      print
      print "Punto Control 2", self.clDB.idRuta
      self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
      self.idTerminal(22.13054, -100.96872)
      time.sleep(15)
      print
      print "Terminal 2 Fin de Vuelta", self.clDB.idRuta
      self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
      self.idTerminal(22.10418, -100.94889)
      time.sleep(15)


      print
      print "Terminal 2 Inicio Vuelta", self.clDB.idRuta
      self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
      self.idTerminal(22.10418, -100.94889)
      time.sleep(15)
      print
      print "Coordenada de Salida T2", self.clDB.idRuta
      self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
      self.idTerminal(22.11018, -100.96049)
      time.sleep(15)
      print
      print "Punto Control 2", self.clDB.idRuta
      self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
      self.idTerminal(22.13054, -100.96872)
      time.sleep(15)
      print
      print "Punto Control 1", self.clDB.idRuta
      self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
      self.idTerminal(22.17391,-101.01379)
      time.sleep(15)
      print
      print "Terminal 1 Fin de Vuelta"
      self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
      self.idTerminal(22.19122, -101.02755)
      time.sleep(15)


      return
      '''

      #if True:
      try:
        stGPS = "."
        if (self.flGPSOn and not self.parent.flGPSOK):
            #print self.REVERSE+self.RED+"Configuracion de GPS en ruta"+self.RESET
            self.configuraGPS()
        self.datetimes = time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S")
        if self.flGPSOn:
            stRead = self.write('AT+QGPSLOC=2\r', ("OK", "ERROR"), self.timeOutGPS)                      #---
            stRead = " ".join(stRead.split())
            j = stRead.find("+QGPSLOC: ")
            if (j != -1):
                stRead = stRead[j:]
            #print stReadl 
            #self.parent.lblError.setText(stRead)
            self.parent.flGPS = (stRead.find("OK") != -1)
            if self.parent.flGPS:
                self.GPSOffline = 0
                self.GPSWaitting = 0
                my_list = stRead.split(",")
                # 0 Hora  (hh-mm-ss)
                # 1 latitud
                # 2 longitud
                # 7 velocidad
                # 9 Fecha (dd-mm-aa)
                if (len(my_list) == 11):
                    #print my_list[0][10:]
                    now = int(float(my_list[0][10:]))
                    self.latitud = my_list[1]
                    self.longitud = my_list[2]
                    self.velGPS = int(float(my_list[7]))
                    #idInser = my_list[9][0:2]+my_list[0][10:16]
                    self.parent.lblVelocidad.setText(str(self.velGPS))
                    lat = float(self.latitud)
                    lon = float(self.longitud)
                    dist = math.sqrt(pow(self.latAnt-lat,2)+pow(self.lonAnt-lon,2)) * 111111.111111

                    tiempo = now - self.nowAnt
                    if (self.nowAnt != 0):
                        vel = (dist/1000.0)/(tiempo/3600.0)
                    else:
                        vel = float(my_list[7])
                    self.parent.lblVelocidad.setText(str(int(vel)) + '/' + str(int(float(my_list[7]))))
                    self.velGPS = vel
                    #self.parent.lblVelocidad.setText(str(self.velGPS))

                    
                    '''
                    now = int(time.time())
                    lat = float(self.latitud)
                    lon = float(self.longitud)
                    dist = math.sqrt(pow(self.latAnt-lat,2)+pow(self.lonAnt-lon,2)) * 111111.111111
                    tiempo = now - self.nowAnt
                    #print "Tiempo = "+str(now)+"-"+str(self.nowAnt)
                    if (self.nowAnt != 0):
                        vel = (dist/1000.0)/(tiempo/3600.0)
                    else:
                        vel = float(my_list[7])
                    self.parent.lblVelocidad.setText(str(int(vel)))
                    #self.velGPS = vel
                    #self.parent.lblVelocidad.setText(str(self.velGPS))
                    '''
                    if ((self.velAnt >= 0) and (self.velAnt < 6) and (self.velGPS < 6)) or (self.velGPS > 100):
                        st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',2,0,0,0,0\r'        # latitud = 2   ----> Unidad conectada
                        dist = 0
                    else:
                        self.idCons += 1
                        if (self.velAnt == -1):
                             dist = 0
                        #else:
                        #    dist = int(math.sqrt(pow(self.latAnt-lat,2)+pow(self.lonAnt-lon,2))) * 111111.111111
                        st = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+','+str(self.latitud)+','+str(self.longitud)+','+str(int(self.velGPS))+','+str(self.idCons)+','+str(int(dist))+'\r'
                        self.idTerminal(self.latitud, self.longitud)
                    self.latAnt = lat
                    self.lonAnt = lon
                    self.velAnt = vel #self.velGPS
                    self.nowAnt = now
                    stGPS = self.sendData(st)
                    #print "stGPS ",stGPS
                    if ((stGPS == '') and (self.velGPS > 5)):
                        self.clDB.dbGPS.execute('INSERT INTO gps (idTransportista, idUnidad, fecha, latitud, longitud, velocidad, distancia, idCons) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (str(self.clDB.idTransportista),str(self.clDB.idUnidad),str(self.datetimes), str(self.latitud), str(self.longitud), str(int(self.velGPS)), str(int(dist)), self.idCons))
                        self.clDB.dbGPS.commit()
                        self.parent.flDataGPS = True
                else:
                    self.printDebug(str(my_list))
                    self.printDebug("###              Error: Lista mal formada ### ")       
            else:
                self.velGPS = 0
                self.parent.lblVelocidad.setText("-")
                if (self.GPSOffline == 0):
                    self.GPSWaitting += self.GPSDelay
                    self.GPSOffline = int(time.time())
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    #print self.parent.YELLOW+fecha+"   Desconexion de GPS "+str(self.GPSWaitting)+" seg para reinicio."+self.RESET
                    if (self.latitud != ""):
                        lat = str(self.latitud)
                    else:
                        lat = "0"
                    if (self.longitud != ""):
                        lon = str(self.longitud)
                    else:
                        lon = "0"
                    fechaGPS = datetime.datetime.fromtimestamp(self.parent.lastConnection).strftime('%Y-%m-%d %H:%M:%S') 
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,GPS Off ("+str(self.GPSWaitting)+" seg p/reinic),"+str(self.parent.csn)+","+lat+","+lon+",0,"+str(fechaGPS)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True
                elif ((int(time.time())-self.GPSOffline) > self.GPSWaitting):
                    self.GPSOffline = int(time.time())                  
                    #self.gpsOff()
                    fecha = time.strftime('%Y-%m-%d %H:%M:%S')
                    #print self.parent.RED+fecha+"   Reiniciando Modem GPS Off ("+str(self.GPSWaitting)+" seg)"+self.RESET
                    #print self.parent.RED+fecha+"   Apagado de GPS"+self.RESET`
                    #stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,Apagado de GPS,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,GPS Reinit ("+str(self.GPSWaitting)+" seg),"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
                    self.clDB.envio(1,stB)
                    self.parent.flSendEnvio = True
                    self.GPSWaitting += self.GPSDelay                   
                    self.reset()
            #self.parent.lblError.setText("")
        '''
        elif ((int(time.time())-self.GPSOffline) > self.GPSWaitting):
            fecha = time.strftime('%Y-%m-%d %H:%M:%S')
            #print self.parent.CYAN+fecha+"   Encendiendo GPS"+self.RESET
            self.gpsOn()
            stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,Encendiendo GPS,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
            self.clDB.envio(1,stB)
            self.parent.flSendEnvio = True
            self.GPSOffline = 0
        '''
        if (stGPS == "."):
            stGPS = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(self.datetimes)+',0,0,0,0,0\r'           # latitud = 0    ----> GPS Apagado
            stGPS = self.sendData(stGPS)
        self.returnGPS(stGPS)
      #else:              
      except:
        print "error al obtener coordenada GPS"
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        st = str(sys.exc_info()[1]) + " " + str(fname) + "  " + str(exc_tb.tb_lineno)
        fecha = time.strftime('%Y-%m-%d %H:%M:%S')
        stB = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+",11,GPS - "+st+" ,"+str(self.parent.csn)+",0,0,0,"+str(fecha)+","+str(fecha)
        self.clDB.envio(1,stB)
        self.parent.flSendEnvio = True

    def cambiaRuta(self, idRuta):
        try:
            c = self.clDB.dbAforo.cursor()
            #print "Cambio de Ruta "+ str(self.clDB.idRuta)+" = "+str(idRuta)
            self.clDB.idRuta = idRuta
            #print "UPDATE parametros SET idRutaActual = "+str(self.clDB.idRuta)
            c.execute("UPDATE parametros SET idRutaActual = "+str(self.clDB.idRuta))
            self.clDB.dbAforo.commit()
            #print("SELECT numRuta, nombre FROM ruta WHERE idRuta = "+str(self.clDB.idRuta))
            c.execute("SELECT numRuta, nombre FROM ruta WHERE idRuta = "+str(self.clDB.idRuta))
            d = c.fetchone()
            if (d is None):
                self.parent.lblNoRuta.setText("")
                self.parent.lblRuta.setText("")
            else:
                self.parent.lblNoRuta.setText(str(d[0]))
                self.parent.lblRuta.setText(str(d[1].encode('latin-1')))
        except:
            self.parent.lblNoRuta.setText("")
            self.parent.lblRuta.setText("")
            

    def idTerminal(self, latitud, longitud):
      #if True:
      try:
        #print "Identificando Terminal"
        t = self.clDB.dbFlota.cursor()
        #print("SELECT COUNT(DISTINCT idRuta) FROM vTerminales WHERE ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia)
        t.execute("SELECT COUNT(DISTINCT idRuta) FROM vTerminales WHERE ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia)
        n = t.fetchone()
        if (n[0] == 0):
            if (self.enTerminal):
                #print "Saliendo de terminal"
                c = self.clDB.dbAforo.cursor()
                #print "Buscando si no han asignado Ruta"
                #print("SELECT idRuta FROM asignacion WHERE idPuntoInteres = 2")
                t.execute("SELECT idRuta FROM asignacion WHERE idPuntoInteres = 2")
                d = t.fetchone()
                if (not d is None):
                    #print "Iniciando Ruta de Manual a Automatica"
                    t.execute("DELETE FROM asignacion WHERE idPuntoInteres = 2")
                    self.clDB.dbFlota.commit()
                    #print "Cerrando vuelta Manual, Despachador no cerro vuelta"
                    #print ('UPDATE vuelta SET termino = "'+str(time.strftime("%Y-%m-%d %H:%M:%S"))+'", csnTermino = "'+self.parent.csn+'", enviadoTermino = 0 WHERE idRecorrido = '+str(self.parent.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta) +' AND vuelta = '+str(self.parent.noVuelta))
                    self.clDB.dbAforo.execute('UPDATE vuelta SET termino = "'+str(time.strftime("%Y-%m-%d %H:%M:%S"))+'", csnTermino = "'+self.parent.csn+'", enviadoTermino = 0 WHERE idRecorrido = '+str(self.parent.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta) +' AND vuelta = '+str(self.parent.noVuelta))
                #print("SELECT idRuta FROM asignacion WHERE idPuntoInteres = 1")
                t.execute("SELECT idRuta FROM asignacion WHERE idPuntoInteres = 1")
                d = t.fetchone()
                if (d is None):
                    #print("SELECT idRecorrido, inicio, termino FROM recorrido ORDER BY idRecorrido DESC LIMIT 1")
                    c.execute("SELECT idRecorrido, inicio, termino FROM recorrido ORDER BY idRecorrido DESC LIMIT 1")
                    d = c.fetchone()
                    if (d is None):
                        self.parent.idRecorrido = 0 
                        #print "Comenzando Recorridos"
                    elif ((str(d[1][0:10]) != str(self.datetimes[0:10])) and (d[2] is None)):
                        #print "Cerrando Recorrido "+str(self.parent.idRecorrido)+" en Terminal"
                        #print("UPDATE recorrido SET termino = '"+self.datetimes+"', csnTermino = '"+self.parent.csn+"', enviadoTermino = 0 WHERE idRecorrido = " + str(self.parent.idRecorrido))
                        c.execute("UPDATE recorrido SET termino = '"+self.datetimes+"', csnTermino = '"+self.parent.csn+"', enviadoTermino = 0 WHERE idRecorrido = " + str(self.parent.idRecorrido))
                        self.clDB.dbAforo.commit()
                        self.parent.idRecorrido = 0 
                        self.parent.flSendTerminoRecorrido = True
                    if (self.parent.idRecorrido == 0):
                        #print "Iniciar Recorrido"
                        #print('INSERT INTO recorrido (inicio, csnInicio, idTurno, enviadoInicio) VALUES ("'+str(time.strftime("%Y-%m-%d %H:%M:%S"))+'","'+str(self.parent.csn)+'",0,0)')
                        c.execute('INSERT INTO recorrido (inicio, csnInicio, idTurno, enviadoInicio) VALUES ("'+str(time.strftime("%Y-%m-%d %H:%M:%S"))+'","'+str(self.parent.csn)+'",0,0)')
                        self.clDB.dbAforo.commit()
                        self.parent.flSendInicioRecorrido = True
                        #print('SELECT last_insert_rowid()')
                        c.execute('SELECT last_insert_rowid()')
                        d = c.fetchone()
                        self.parent.idRecorrido = d[0]
                        #print "Recorrido: ",self.parent.idRecorrido
                    if (self.clDB.idRuta != self.idRuta):
                        self.cambioRuta(self.idRuta)
                    #print "Buscando Vuelta en Ruta "+str(self.clDB.idRuta)
                    if (str(self.clDB.idTransportista) != "2"):
                        #print("SELECT MAX(Vuelta) FROM vuelta WHERE idRecorrido = "+str(self.parent.idRecorrido)+" AND idRuta = "+str(self.clDB.idRuta))
                        c.execute("SELECT MAX(Vuelta) FROM vuelta WHERE idRecorrido = "+str(self.parent.idRecorrido)+" AND idRuta = "+str(self.clDB.idRuta))
                    else:
                        #print("SELECT MAX(Vuelta) FROM vuelta WHERE idRecorrido = "+str(self.parent.idRecorrido)+" AND idRuta = "+str(self.clDB.idRuta))
                        c.execute("SELECT MAX(Vuelta) FROM vuelta WHERE idRecorrido = "+str(self.parent.idRecorrido)+" AND vuelta > 0")
                    d = c.fetchone()
                    if (d[0] is None):
                        #print "vuelta 1"
                        self.parent.noVuelta = 1
                    else:
                        #print "nueva vuelta",d[0] + 1
                        self.parent.noVuelta = d[0] + 1
                    #print("SELECT numRuta, nombre FROM ruta WHERE idRuta = "+str(self.clDB.idRuta))
                    c.execute("SELECT numRuta, nombre FROM ruta WHERE idRuta = "+str(self.clDB.idRuta))
                    d = c.fetchone()
                    if (d is None):
                        self.parent.lblNoRuta.setText("")
                        self.parent.lblRuta.setText("")
                    else:
                        self.parent.lblNoRuta.setText(str(d[0]))
                        self.parent.lblRuta.setText(str(d[1].encode('latin-1')))
                    self.parent.lblVuelta.setText(str(self.parent.noVuelta))                    
                    st = self.parent.stOperador.decode('latin-1')
                    #print("INSERT INTO vuelta (idRecorrido, idRuta, vuelta, inicio, csnInicio, operador, enviadoInicio, idVuelta, tipo) VALUES (?,?,?,?,?,?,0,0,2)",(str(self.parent.idRecorrido), str(self.clDB.idRuta), str(self.parent.noVuelta), time.strftime("%Y-%m-%d %H:%M:%S"), str(self.parent.csn), st))
                    c.execute("INSERT INTO vuelta (idRecorrido, idRuta, vuelta, inicio, csnInicio, operador, enviadoInicio, idVuelta,tipo) VALUES (?,?,?,?,?,?,0,0,2)",(str(self.parent.idRecorrido), str(self.clDB.idRuta), str(self.parent.noVuelta), time.strftime("%Y-%m-%d %H:%M:%S"), str(self.parent.csn), st))
                    self.clDB.dbAforo.commit()
                    self.parent.flSendInicioVuelta = True
                    self.parent.retorno = False 
                    #print('INSERT INTO puntoControl (idPuntoInteres, idUnidad, fecha, latitud, longitud, idRecorrido, idVuelta, orden, enviado, idRuta, vuelta, distancia) VALUES (' + str(self.idPITerminal)+', '+str(self.clDB.idUnidad)+', "'+ self.datetimes+'", '+ str(latitud)+', '+ str(longitud)+', '+ str(self.parent.idRecorrido)+', '+ str(self.parent.noVuelta)+', 0, 0, '+str(self.clDB.idRuta)+', '+str(self.parent.noVuelta)+', 0)')
                    t.execute('INSERT INTO puntoControl (idPuntoInteres, idUnidad, fecha, latitud, longitud, idRecorrido, idVuelta, orden, enviado, idRuta, vuelta, distancia) VALUES (' + str(self.idPITerminal)+', '+str(self.clDB.idUnidad)+', "'+ self.datetimes+'", '+ str(latitud)+', '+ str(longitud)+', '+ str(self.parent.idRecorrido)+', '+ str(self.parent.noVuelta)+', 0, 0, '+str(self.clDB.idRuta)+', '+str(self.parent.noVuelta)+', 0)')
                    self.clDB.dbFlota.commit()
                else:
                    #print "Ruta "+str(self.clDB.idRuta) + "  " + self.parent.lblRuta.text()
                    self.idRuta = self.clDB.idRuta
                self.enTerminal = False
            else:
                #print "Fuera de terminal"
                self.idPuntoControl(latitud, longitud)
        else:
            if (not self.enTerminal):
                self.rutaOK = (n[0] == 1)
                #print "Llegando a terminal"
                if (self.idCons > 1):
                    #print ("SELECT idPuntoInteres FROM asignacion WHERE idPuntoInteres = 0")
                    t.execute("SELECT idPuntoInteres FROM asignacion WHERE idPuntoInteres = 0")
                    d = t.fetchone()
                    t.execute("SELECT count(*) FROM asignacion")
                    c = t.fetchone()
                    if not (d is None) or (c[0] == 0):
                        if (str(self.clDB.idTransportista) == "4"):
                            #print("SELECT DISTINCT idRuta, idPC, latitud, longitud FROM vTerminales WHERE orden = 1 AND ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia)
                            t.execute("SELECT DISTINCT idRuta, idPC, latitud, longitud FROM vTerminales WHERE orden = 1 AND ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia + " ORDER BY idRuta")
                        else:
                            #print ("SELECT DISTINCT idRuta, idPC, latitud, longitud FROM vTerminales WHERE ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia)
                            t.execute("SELECT DISTINCT idRuta, idPC, latitud, longitud FROM vTerminales WHERE ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia)
                        data = t.fetchone()
                        self.idPITerminal = data[1]
                        if (self.parent.noVuelta != 0):
                            distanciaPC = math.sqrt(pow(data[2]-float(latitud),2)+pow(data[3]-float(longitud),2)) * 111111.111111
                            #print('INSERT INTO puntoControl (idPuntoInteres, idUnidad, fecha, latitud, longitud, idRecorrido, idVuelta, enviado, idRuta, vuelta, distancia, orden) VALUES ('+str(data[1])+', '+str(self.clDB.idUnidad)+', "'+ self.datetimes+'", '+ str(latitud)+', '+ str(longitud)+', '+ str(self.parent.idRecorrido)+', '+str(self.parent.noVuelta)+', 0, '+str(self.clDB.idRuta)+', '+str(self.parent.noVuelta)+', '+str(distanciaPC)+', 1)')
                            t.execute('INSERT INTO puntoControl (idPuntoInteres, idUnidad, fecha, latitud, longitud, idRecorrido, idVuelta, enviado, idRuta, vuelta, distancia, orden) VALUES ('+str(data[1])+', '+str(self.clDB.idUnidad)+', "'+ self.datetimes+'", '+ str(latitud)+', '+ str(longitud)+', '+ str(self.parent.idRecorrido)+', '+str(self.parent.noVuelta)+', 0, '+str(self.clDB.idRuta)+', '+str(self.parent.noVuelta)+', '+str(distanciaPC)+', 1)')
                            self.clDB.dbFlota.commit()
                            if not self.clDB.vueltaValida(self.parent.idRecorrido, self.parent.noVuelta):
                                #print "Cerrar Vuelta fuera de Ruta"
                                #print ('UPDATE vuelta SET vuelta = 0, termino = "'+str(time.strftime("%Y-%m-%d %H:%M:%S"))+'", csnTermino = "'+self.parent.csn+'", enviadoTermino = 0 WHERE idRecorrido = '+str(self.parent.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta)+' AND vuelta = '+str(self.parent.noVuelta))
                                self.clDB.dbAforo.execute('UPDATE vuelta SET vuelta = 0, termino = "'+str(time.strftime("%Y-%m-%d %H:%M:%S"))+'", csnTermino = "'+self.parent.csn+'", enviadoTermino = 0 WHERE idRecorrido = '+str(self.parent.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta)+' AND vuelta = '+str(self.parent.noVuelta))
                                #print('UPDATE puntoControl SET vuelta = 0 WHERE idRecorrido = '+str(self.parent.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta)+' AND vuelta = '+str(self.parent.noVuelta))
                                self.clDB.dbFlota.execute('UPDATE puntoControl SET vuelta = 0 WHERE idRecorrido = '+str(self.parent.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta)+' AND vuelta = '+str(self.parent.noVuelta))
                            else:
                                #print "Cerrar Vuelta"
                                #print ('UPDATE vuelta SET termino = "'+str(time.strftime("%Y-%m-%d %H:%M:%S"))+'", csnTermino = "'+self.parent.csn+'", enviadoTermino = 0 WHERE idRecorrido = '+str(self.parent.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta)+' AND vuelta = '+str(self.parent.noVuelta))
                                self.clDB.dbAforo.execute('UPDATE vuelta SET termino = "'+str(time.strftime("%Y-%m-%d %H:%M:%S"))+'", csnTermino = "'+self.parent.csn+'", enviadoTermino = 0 WHERE idRecorrido = '+str(self.parent.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta)+' AND vuelta = '+str(self.parent.noVuelta))
                            self.clDB.dbAforo.commit()      
                            self.parent.flSendTerminoVuelta = True
                            self.parent.lblVuelta.setText("")
                            self.parent.noVuelta = 0
                        #print("DELETE FROM asignacion")
                        t.execute("DELETE FROM asignacion")
                        self.clDB.dbFlota.commit()
                    else:
                        #print "Esperando a Cerrar vuelta por despachador"
                        t.execute("UPDATE asignacion SET idPuntoInteres = 2 WHERE idPuntoInteres = 1")
                    if (self.clDB.idTransportista == 4):                
                        #print ("INSERT INTO asignacion SELECT DISTINCT "+str(self.clDB.idTransportista)+",idRuta, 0, (SELECT COUNT(*) FROM vPuntoControl WHERE vTerminales.idRuta = vPuntoControl.idRuta) FROM vTerminales WHERE orden = 1 AND ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia)
                        t.execute("INSERT INTO asignacion SELECT DISTINCT "+str(self.clDB.idTransportista)+",idRuta, 0, (SELECT COUNT(*) FROM vPuntoControl WHERE vTerminales.idRuta = vPuntoControl.idRuta) FROM vTerminales WHERE orden = 1 AND ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia)
                        if not (d is None):
                            self.clDB.dbFlota.commit()
                            t.execute("SELECT idRuta FROM asignacion WHERE idPuntoInteres = 0 ORDER BY idRuta LIMIT 1")
                            d = t.fetchone()
                            self.idRuta = d[0]
                            self.cambiaRuta(self.idRuta)
                    else:
                        #print("INSERT INTO asignacion SELECT DISTINCT "+str(self.clDB.idTransportista)+",idRuta,0, (SELECT COUNT(*) FROM vPuntoControl WHERE vTerminales.idRuta = vPuntoControl.idRuta) FROM vTerminales WHERE ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia)
                        t.execute("INSERT INTO asignacion SELECT DISTINCT "+str(self.clDB.idTransportista)+",idRuta,0, (SELECT COUNT(*) FROM vPuntoControl WHERE vTerminales.idRuta = vPuntoControl.idRuta) FROM vTerminales WHERE ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia)
                    self.clDB.dbFlota.commit()
                #else:
                    #print "Reinicio de Validador en Terminal"
            self.enTerminal = True
            self.enPuntoDeControl = False
      #else:
      except:
          print "Error en Buscar Terminal"

    def idPuntoControl(self, latitud, longitud):
      #if True:
      try:
        #print "Identificando Punto de Control"
        t = self.clDB.dbFlota.cursor()
        t.execute("SELECT COUNT(DISTINCT vPuntoControl.idRuta) FROM vPuntoControl, asignacion WHERE vPuntoControl.idRuta = asignacion.idRuta AND ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia)
        n = t.fetchone()
        if (n[0] > 0):
            #print "SELECT idRuta, idPuntoInteres, orden, latitud, longitud  FROM vPuntoControl WHERE ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia
            t.execute("SELECT vPuntoControl.idRuta, idPC, orden, latitud, longitud, PuntoRetorno FROM vPuntoControl, asignacion WHERE vPuntoControl.idRuta = asignacion.idRuta AND ABS(latitud-"+str(latitud)+") < "+self.tolerancia+" AND ABS(ABS(longitud)-ABS("+str(longitud)+")) < "+self.tolerancia + " LIMIT 1")
            data = t.fetchone()
            distanciaPC = math.sqrt(pow(data[3]-float(latitud),2)+pow(data[4]-float(longitud),2)) * 111111.111111
            #print "Distancia inicial al PC "+str(data[1])+" de: "+str(distanciaPC)                   
            if (not self.enPuntoDeControl):
                self.distanciaPC = distanciaPC
                #print "Llegando a punto de Control",data[1]
                self.parent.retorno = self.parent.retorno or (data[5] == 1) 
                if (n[0] == 1 and not self.rutaOK):
                    #print "Ruta Identificada", data[0]
                    #print "if ("+str(self.clDB.idRuta)+" != "+str(data[0])+"):"
                    t.execute("DELETE FROM asignacion WHERE idRuta <> "+str(data[0]))
                    self.clDB.dbFlota.commit()
                    if (int(self.clDB.idRuta) != int(data[0])):
                        c = self.clDB.dbAforo.cursor()
                        if (str(self.clDB.idTransportista) != "2"):
                            c.execute("SELECT MAX(Vuelta) FROM vuelta WHERE idRecorrido = "+str(self.parent.idRecorrido)+" AND idRuta = "+str(data[0]))
                            #print "SELECT MAX(Vuelta) FROM vuelta WHERE idRecorrido = "+str(self.parent.idRecorrido)+" AND idRuta = "+str(data[0])
                            d = c.fetchone()
                            if (d[0] is None):
                                noVuelta = 1
                            else:
                                noVuelta = d[0] + 1
                        else:
                            noVuelta = self.parent.noVuelta
                        t.execute('UPDATE puntoControl SET vuelta = ' + str(noVuelta) + ', idRuta = '+str(data[0])+' WHERE idRecorrido = ' + str(self.parent.idRecorrido)+" AND idRuta = "+str(self.clDB.idRuta) + ' AND vuelta = ' +  str(self.parent.noVuelta))
                        self.clDB.dbFlota.commit()
                        self.clDB.dbAforo.execute("UPDATE vuelta SET idRuta = "+str(data[0])+", vuelta = "+str(noVuelta)+", enviadoInicio = 0 WHERE idRecorrido = "+str(self.parent.idRecorrido)+" AND idRuta = "+str(self.clDB.idRuta)+" AND vuelta = "+str(self.parent.noVuelta))
                        self.clDB.dbAforo.commit()
                        self.idRuta = data[0]
                        self.cambiaRuta(self.idRuta)
                        self.parent.noVuelta = noVuelta
                        self.parent.lblVuelta.setText(str(self.parent.noVuelta))
                        self.parent.flSendActualizaVuelta = True
                    self.rutaOK = True
                self.enPuntoDeControl = True
                #print 'INSERT INTO puntoControl (idPuntoInteres, idUnidad, fecha, latitud, longitud, idRecorrido, idVuelta, orden, enviado, idRuta, vuelta) VALUES (' + str(data[1])+', '+str(self.clDB.idUnidad)+', "'+ self.datetimes+'", '+ str(latitud)+', '+ str(longitud)+', '+ str(self.parent.idRecorrido)+', '+ str(self.parent.noVuelta)+', '+ str(data[2])+',0,'+str(self.clDB.idRuta)+','+ str(self.parent.noVuelta)+')'
                t.execute('INSERT INTO puntoControl (idPuntoInteres, idUnidad, fecha, latitud, longitud, idRecorrido, idVuelta, orden, enviado, idRuta, vuelta, distancia) VALUES (' + str(data[1])+', '+str(self.clDB.idUnidad)+', "'+ self.datetimes+'", '+ str(latitud)+', '+ str(longitud)+', '+ str(self.parent.idRecorrido)+', '+ str(self.parent.noVuelta)+', '+ str(data[2])+',0,'+str(self.clDB.idRuta)+','+ str(self.parent.noVuelta)+', '+ str(self.distanciaPC) + ')')
                self.clDB.dbFlota.commit()
            else:
                #print "En punto de Control",data[1]
                if (self.distanciaPC > distanciaPC):
                    self.distanciaPC = distanciaPC
                    #print 'UPDATE puntoControl SET fecha = "'+ self.datetimes+'", latitud = '+ str(latitud)+', longitud = '+ str(longitud)+', distancia = '+ str(self.distanciaPC) + ' WHERE idPuntoInteres = ' + str(data[1])+' AND idUnidad = '+str(self.clDB.idUnidad)+' AND idRecorrido = '+ str(self.parent.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta)+' AND Vuelta =  '+ str(self.parent.noVuelta)+' AND orden = '+ str(data[2])
                    t.execute('UPDATE puntoControl SET fecha = "'+ self.datetimes+'", latitud = '+ str(latitud)+', longitud = '+ str(longitud)+', distancia = '+ str(self.distanciaPC) + ' WHERE idPuntoInteres = ' + str(data[1])+' AND idUnidad = '+str(self.clDB.idUnidad)+' AND idRecorrido = '+ str(self.parent.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta)+' AND Vuelta =  '+ str(self.parent.noVuelta)+' AND orden = '+ str(data[2]))
                    self.clDB.dbFlota.commit()
        else:
            if (self.enPuntoDeControl):
                #print "Saliendo de punto de Control"
                self.enPuntoDeControl = False
                self.parent.flSendPuntoControl = True
                #self.parent.flSendActualizaVuelta = True
                self.distanciaPC = 5000
            #else:
                #print "Coordenada GPS"
      #else:
      except:
          print "Error en Buscar Punto de Control"

    def subirArchivoFTP(self, origen, destino):
        fl = False
        try:
            if os.path.exists(origen):
                stOperador = self.parent.lblNombreOperador.text()
                self.parent.smsEnabled = False
                self.parent.sendData = True
                self.flDownload = True
                self.printDebug('###                       Inicia Upload  ###')
                self.parent.lblError.setText("Enviar Archivo "+origen)
                cmd =  'AT+QFTPOPEN="%s",%s\r' % (self.clDB.urlFTP, self.clDB.puertoFTP)
                stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                           #FTPTimeOut = 20
                if (stRead.find('601') != -1):
                    stRead = self.write("AT+QFTPCLOSE\r", ("+QFTPCLOSE", "ERROR"), self.timeOutFTP)          #FTPTimeOut = 20
                    time.sleep(1)
                    stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                                       #20s
                elif (stRead.find('625') != -1) or (stRead.find('530') != -1):
                    self.printDebug('### NOT LOGGED IN FTP                     ###')
                    self.configuraFTP()
                    stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                                       #20s
                self.printDebug('### CONEXION FTP                          ###')
                if(stRead.find("QFTPOPEN: 0,0") != -1):
                    self.parent.flFTP = True
                    i = destino.rfind("/")
                    path = destino[0:i]
                    archivo = destino[i+1:]
                    size = os.path.getsize(origen)
                    cmd = 'AT+QFTPCWD="%s"\r'%(path)
                    stRead = self.write(cmd, ("+QFTPCWD", "ERROR"), self.timeOutFTP)                         #FTPTimeOut = 20
                    if (stRead.find("QFTPCWD: 0,0") != -1):
                        cmd = 'AT+QFTPPUT="%s","COM:",0,%s\r'%(destino, size)
                        stRead = self.write(cmd, ("CONNECT", "ERROR"), self.timeOutFTP)                      #FTPTimeOut = 20
                        if (stRead.find("CONNECT") != -1):
                            i = 0
                            #print "Inicio: ",datetime.datetime.now().strftime("%H:%M:%S")
                            self.parent.locked = True
                            f = open(origen, 'rb')
                            b = f.read(self.blockSize)
                            while b:
                                self.serial.ser3G.write(b)
                                b = f.read(self.blockSize)
                                i += len(b)
                                self.parent.lblNombreOperador.setText("Uploading  "+str(i)+"....")
                            self.parent.locked = False                    
                            stRead = self.write("+++", ("+QFTPPUT", "ERROR"), self.timeOutFTP)
                            if (stRead.find("+QFTPPUT: 0,") != -1):
                                stRead = " ".join(stRead.split())
                                i = stRead.find(",")
                                if (i != -1):
                                    i = int(stRead[i+1:])
                                    fl = (i == size)
                                    if (not fl):
                                        self.printDebug("ERROR: No se Completo el Envio del Archivo al Servidor")
                                        self.parent.lblError.setText("ERROR: No se Completo el Envio del Archivo al Servidor")
                                else:
                                    self.parent.lblError.setText("ERROR: Falla al enviar el Archivo")
                                    self.printDebug("ERROR: Falla al enviar el Archivo")
                            else:
                                self.parent.lblError.setText("ERROR: En Transferencia de Informacion")
                                self.printDebug("ERROR: En Transferencia de Informacion")
                            f.close()
                            #print "Termino: ",datetime.datetime.now().strftime("%H:%M:%S")
                            self.parent.locked = False
                        else:
                            self.printDebug("ERROR de Transmision de Datos con el Servidor")
                            self.parent.lblError.setText("ERROR de Transmision de Datos con el Servidor")
                    else:
                        self.printDebug("ERROR no existe el Directorio Destino en el Servidor")
                        self.parent.lblError.setText("ERROR no existe el Directorio Destino en el Servidor")
                else:
                    self.parent.lblError.setText("ERROR al Conectarse al Servidor FTP")
                    self.printDebug("ERROR al Conectarse al Servidor FTP")
                    
                stRead = self.write("AT+QFTPCLOSE\r", ("+QFTPCLOSE", "ERROR"), self.timeOutFTP)          #FTPTimeOut = 20
                self.parent.lblNombreOperador.setText(stOperador)                           
                #if fl:
                #    stRead = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,3,0,0,0,0\r'       # latitud = 3   ----> SyncSoftware OK
                #    self.sendData(stRead)
                #else:
                #    time.sleep(5)
                self.parent.lblError.setText("")                                    
                self.parent.flFTP = False            
                self.flDownload = False
                self.parent.sendData = False
                self.parent.smsEnabled = True
            else:
                stRead = '1,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+',2000-01-01 00:00:00,3,0,0,0,0\r'       # latitud = 3   ----> SyncSoftware OK
                self.sendData(stRead)
            self.parent.lblError.setText("")
        except:
            self.parent.lblError.setText("")                                    
            self.parent.flFTP = False            
            self.flDownload = False
            self.parent.sendData = False
            self.parent.smsEnabled = True
        return fl

    def descargarArchivoFTP(self, origen, destino, msg):
        #if True:
        try:
            fl = False
            stOperador = self.parent.lblNombreOperador.text()
            self.printDebug('###                       Inicia Descarga ###')
            self.parent.lblError.setText("Descargando archivo "+origen)
            cmd =  'AT+QFTPOPEN="%s",%s\r' % (self.clDB.urlFTP, self.clDB.puertoFTP)
            stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                           #FTPTimeOut = 20
            if (stRead.find('601') != -1):
                stRead = self.write("AT+QFTPCLOSE\r", ("+QFTPCLOSE", "ERROR"), self.timeOutFTP)          #FTPTimeOut = 20
                time.sleep(1)
                stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                                       #20s
            elif (stRead.find('625') != -1) or (stRead.find('530') != -1):
                self.printDebug('### NOT LOGGED IN FTP                     ###')
                self.configuraFTP()
                stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                                       #20s
            self.printDebug('### CONEXION FTP                          ###')
            if(stRead.find("QFTPOPEN: 0,0") != -1):
                self.parent.flFTP = True
                self.parent.smsEnabled = False
                self.parent.sendData = True
                self.flDownload = True
                cmd = 'AT+QFTPSIZE="%s"\r'%(origen)
                stRead = self.write(cmd, ("QFTPSIZE", "ERROR"), self.timeOutFTP)                         #FTPTimeOut = 20
                iLenFile = 0
                stFind = ""
                if (stRead.find("QFTPSIZE") != -1):
                    stRead = stRead.split("\r\n")
                    stRead = stRead[3].split(" ")
                    stRead = stRead[1].split(",")
                    if (stRead[0] == "0"):
                        iLenFile = int(stRead[1])
                        stFind = "+QFTPGET: 0,"+stRead[1]
                if (stFind != ""):
                    cmd = 'AT+QFTPGET="'+origen+'","RAM:'+origen+'"\r'
                    self.printDebug(str(iLenFile)+"   "+destino)
                    stRead = self.write(cmd, ("QFTPGET", "ERROR"), self.timeOutFTP)                     #FTPTimeOut = 20
                    if (stRead.find("QFTPGET: 0") != -1):
                        cmd = 'AT+QFDWL="RAM:'+origen+'"\r'
                        self.write3G(cmd.encode())
                        self.parent.locked = True
                        stRead = ""
                        i = 0
                        j = 0
                        while (len(stRead) < iLenFile):
                            stRead += self.serial.ser3G.read(iLenFile+100)
                            self.parent.lblNombreOperador.setText("Actualizando Software "+str(len(stRead)))
                            if (i < len(stRead)):
                                i = len(stRead)
                                j = 0
                            else:
                                j += 1
                            if (j == 5):
                                self.parent.lblNombreOperador.setText(stOperador)                           
                                self.printDebug("Archivo Incompleto")
                                self.parent.locked = False
                                self.parent.flFTP = False
                                self.parent.smsEnabled = True
                                self.parent.sendData = False
                                self.flDownload = False
                                self.parent.lblError.setText("")
                                stRead = self.write("AT+QFTPCLOSE\r", ("+QFTPCLOSE", "ERROR"), self.timeOutFTP)          #FTPTimeOut = 20
                                return False
                        self.parent.lblNombreOperador.setText(stOperador)                           
                        f = open(destino+".tmp", 'wb')
                        f.write(stRead[11:iLenFile+11])
                        f.close()
                        self.printDebug("Archivo OK: "+destino+' ('+str(len(stRead))+')')
                        self.parent.locked = False
                        self.parent.smsEnabled = True
                        self.flDownload = False
                        self.parent.flFTP = False
                        stRead = self.write('AT+QFDEL="RAM:*"\r', ("OK", "ERROR"), self.timeOutFTP)                     #FTPTimeOut = 20
                        time.sleep(1)
                        if (destino.find(".zip") != -1):
                            self.printDebug('###                      Unzipping File   ###')
                            os.rename(destino+".tmp", destino)
                            zip_ref = zipfile.ZipFile(destino,'r')
                            zip_ref.extractall('/home/pi/innobusmx')
                            zip_ref.close()
                            time.sleep(1)
                            os.remove(destino)
                            #return True
                        else:
                            if os.path.exists(destino):
                                os.remove(destino)
                            os.rename(destino+".tmp", destino)
                            #return False
                        fl = True
                    else:
                        self.printDebug("Error ("+str(stRead)+")")
                        #return False
                else:
                    #self.parent.flFTP = False
                    #self.parent.smsEnabled = True
                    #self.parent.locked = False
                    #self.parent.sendData = False
                    #self.flDownload = False
                    self.printDebug("Error ("+str(stRead)+")")
                    #return False
        #else:
        except:
            self.printDebug("Error: Path not found")
            #return False

        self.parent.flFTP = False
        self.parent.smsEnabled = True
        self.parent.locked = False
        self.parent.sendData = False
        self.flDownload = False
        self.parent.lblNombreOperador.setText(stOperador)                           
        self.parent.lblError.setText("")
        return fl

    def descargarFotografia(self, csn):
      fl = False
      #if True:
      try:
        self.parent.sendData = True
        self.flDownload = True
        self.printDebug('###                Descarga Fotografia ###')
        #self.parent.lblError.setText("Descargando Fotografia "+csn+".jpeg")
        cmd =  'AT+QFTPOPEN="%s",%s\r' % (self.clDB.urlFTP, self.clDB.puertoFTP)
        stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                           #FTPTimeOut = 20
        if (stRead.find('601') != -1):
            stRead = self.write("AT+QFTPCLOSE\r", ("+QFTPCLOSE", "ERROR"), self.timeOutFTP)          #FTPTimeOut = 20
            time.sleep(1)
            stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                                       #20s
        elif (stRead.find('625') != -1) or (stRead.find('530') != -1):
            self.printDebug('### NOT LOGGED IN FTP                     ###')
            self.configuraFTP()
            stRead = self.write(cmd, ("QFTPOPEN: ", "ERROR"), self.timeOutFTP)                                       #20s
        self.printDebug('### CONEXION FTP                          ###')
        if(stRead.find("QFTPOPEN: 0,0") != -1):
            self.parent.flFTP = True
            self.printDebug('###                       CONEXION FTP OK ###')
            path = '/home/pi/innobusmx/data/user/'+csn[0:5]
            origen = "FTPShare\\Fotos\\"+csn+".jpeg"
            if os.path.exists(path+"/"+csn+".Jpeg"):
                sizeLocal = os.path.getsize(path+"/"+csn+".Jpeg")
            else:
                sizeLocal = 0
            cmd = 'AT+QFTPSIZE="%s"\r'%(origen)
            stRead = self.write(cmd, ("QFTPSIZE", "ERROR"), self.timeOutFTP)                     #FTPTimeOut = 20
            iLenFile = 0
            if (stRead.find("QFTPSIZE: 627,550") != -1):
                origen = "FTPShare\\Fotos\\"+csn[0:5]+"\\"+csn+".jpeg"
                cmd = 'AT+QFTPSIZE="%s"\r'%(origen)
                stRead = self.write(cmd, ("QFTPSIZE", "ERROR"), self.timeOutFTP)                     #FTPTimeOut = 20
            if (stRead.find("QFTPSIZE: 0") != -1):
                stRead = " ".join(stRead.split()) #se le aplica un split al mismo comando
                stRead = stRead.split(",")
                iLenFile = int(stRead[1])
                cmd = 'AT+QFTPGET="'+origen+'","RAM:'+csn+'"\r'
                self.printDebug("Descargar: "+str(sizeLocal)+"  "+str(iLenFile)+"   "+csn+".jpeg")
                if (sizeLocal != iLenFile):
                    if self.senial3G():
                        if not os.path.exists(path):
                            os.mkdir(path)
                        stRead = self.write(cmd, ("QFTPGET", "ERROR"), self.timeOutFTP)                     #FTPTimeOut = 20
                        if (stRead.find("QFTPGET: 0") != -1):
                            cmd = 'AT+QFDWL="RAM:'+csn+'"\r'
                            self.write3G(cmd.encode())
                            self.parent.locked = True
                            stRead = ""
                            i = 0
                            j = 0
                            while (len(stRead) < iLenFile):
                                stRead += self.serial.ser3G.read(iLenFile+100)
                                if (i < len(stRead)):
                                    i = len(stRead)
                                    j = 0
                                else:
                                    j += 1
                                if (j == 5):
                                    self.printDebug("Foto Incompleta")
                                    self.parent.locked = False
                                    self.parent.flFTP = False
                                    self.parent.sendData = False
                                    self.flDownload = False
                                    stRead = self.write("AT+QFTPCLOSE\r", ("+QFTPCLOSE", "ERROR"), self.timeOutFTP)          #FTPTimeOut = 20
                                    self.parent.lblError.setText("")
                                    return False
                            #stRead = self.serial.ser3G.read(iLenFile+100)
                            f = open(path+"/"+csn+".Jpeg.tmp", 'wb')
                            f.write(stRead[11:iLenFile+11])
                            f.close()
                            self.printDebug("Foto OK: "+csn+".Jpeg.")
                            self.parent.locked = False
                            os.rename(path+"/"+csn+".Jpeg.tmp", path+"/"+csn+".Jpeg")
                            fl = True
                            stRead = self.write('AT+QFDEL="RAM:*"\r', ("OK", "ERROR"), self.timeOutFTP)                     #FTPTimeOut = 20
                        else:
                            self.printDebug("Error ("+' '.join(stRead.split())+" ) al descargar la Fotografia: "+csn+".Jpeg.")
                else:
                    self.printDebug("Foto Repetida: "+csn+".Jpeg.")
                    fl = True
            else:
                if ((stRead.find("500") != -1) or (stRead.find("501") != -1) or (stRead.find("502") != -1) or (stRead.find("503") != -1) or (stRead.find("550") != -1) or (stRead.find("553") != -1)):
                    self.printDebug("Foto no Encontrada en el Servidor: "+csn+".Jpeg.")
                    fl = True
                else:
                    self.printDebug("Error de Conexion con el Servidor FTP")
                
        self.parent.locked = False
        self.parent.sendData = False
        stRead = self.write("AT+QFTPCLOSE\r", ("+QFTPCLOSE", "ERROR"), self.timeOutFTP)          #FTPTimeOut = 20
        if fl:
            stRead = self.sendData("9,"+csn+","+str(self.clDB.idUnidad))                
        self.parent.flFTP = False            
        self.flDownload = False
      #else:
      except:
        self.parent.locked = False
        self.parent.sendData = False
        self.parent.flFTP = False            
        self.flDownload = False          
        stRead = self.write("AT+QFTPCLOSE\r", ("+QFTPCLOSE", "ERROR"), self.timeOutFTP)          #FTPTimeOut = 20
      self.parent.lblError.setText("")
      return fl        

    def procesoDeEnvioSMS(self, dato, idActualizar, salgo):
        #print '### Proceso de envio SMS ###'
        c = self.clDB.dbAforo.cursor()
        c.execute("SELECT telefono FROM numTelefono WHERE puntoInteres = 0 OR puntoInteres = ?",(str(self.clDB.idTransportista), ))
        data = c.fetchone()
        self.parent.sendData = True        
        while not (data is None):
            st = ""
            cmd = 'AT+CMGS="'+str(data[0])+'"\r'
            self.write3G(cmd.encode())
            flError = False
            i = 0
            st = ""
            stAnt = ""
            #print "Enviando mensaje a:" + str(data[0])
            while ((st.find(">") == -1) and (st.find("ERROR") == -1) and i < 10):
                st += self.serial.readln3G()
                if len(st) == len(stAnt):
                    time.sleep(1)
                    i += 1
                else:
                    i = 0
                    stAnt = st
            if (st.find(">") != -1):
                self.write3G(dato+'\r\x1A')
                #print dato
                st = ""
                stAnt = ""
                i = 0
                while ((st.find("OK") == -1) and (st.find("ERROR") == -1) and i < 10):
                    st += self.serial.readln3G()
                    if len(st) == len(stAnt):
                        time.sleep(1)
                        i += 1
                    else:
                        i = 0
                        stAnt = st
                    #print i, ".- ", st
                if (st.find("ERROR") != -1) or (i == 10):
                    flError = True
            else:
                flError = True
            if (flError):
                ce = self.clDB.dbMensajes.cursor()
                ce.execute("SELECT MAX(idEnvio) FROM envio WHERE app = 2")
                dataE = ce.fetchone()
                if (dataE[0] is None):
                    i = "1"
                else:
                    i = str(dataE[0]+1)
                ce.close
                self.clDB.dbMensajes.execute("INSERT INTO envio (idEnvio, app, msg, envio) VALUES ("+i+",2,"+"'e,"+str(self.clDB.idUnidad)+","+str(data[0])+",1001,"+time.strftime("%Y-%m-%d %H:%M:%S")+"',0)")
                self.clDB.dbMensajes.commit()
                self.parent.flSendEnvio = True
                #print "No pudo enviar MSG al Tel "+str(data[0]) 
            data = c.fetchone()
        c.close()
        self.parent.sendData = False


#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui
from PyQt4 import QtCore
from PyQt4.QtCore import QSettings
import sqlite3
import os
import time
import datetime
import traceback
import subprocess

from ClSerial import clSerial
from ClModem import clQuectel
from ClDB import sqLite
from ClMifare import clMifare
from ClSMS import clSMS
from ClBarras import clBarras
import RPi.GPIO as GPIO

from alttusDB import insertar_estadisticas_alttus, eliminar_aforos_antiguos, eliminar_estadisticas_antiguas
from horariosDB import obtener_estado_de_todas_las_horas_no_hechas, actualizar_estado_hora_check_hecho, actualizar_estado_hora_por_defecto
from parametrosDB import actualizar_socket, obtener_parametros

os.environ['DISPLAY'] = ":0"

class mainWin(QtGui.QMainWindow):

    stVersion = "vA2.43h"
    flRFID = False
    updateFirmware = False

    locked = False
    rdy = False
    #ftpLocked = False
    #gpsLocked = False
    #smsLocked = False

    #sendDataLocked = False
    #sendDataFTPLocked = False
    #sendDataGPSLocked = False
    #sendDataSMSLocked = False

    smsOK = False
    gpsOK = False
    ftpOK = False

    APN = False
    reInit3G = 0
    waitting = False
    latitud = ""
    longitud = ""
    datetimes = ""
    csn = ""
    velGPS = ""
    idOperador = ""
    stBoton = ""
    flEventoExitoso = 0
    flIdRutaAutomatica = True
    aforo = False
    
    BLACK = "\033[1;30m"
    RED   = "\033[1;31m"
    GREEN = "\033[1;32m"
    YELLOW= "\033[1;33m"
    BLUE  = "\033[1;34m"
    PURPLE= "\033[1;35m"
    CYAN  = "\033[1;36m"
    WHITE = "\033[1;37m"

    RESET = "\033[0;0m"
    BOLD  = "\033[;1m"
    REVERSE = "\033[;7m"
    idCons = 0
    
    def initUI(self):
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.Time)
        timer.start(1000)
        self.mes=["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]

    def Time(self):
        if (self.flFecha):
            self.lblHora.setText(time.strftime("%d/")+self.mes[int(time.strftime("%m"))]+time.strftime("/%Y %H:%M:%S"))
    
    def __init__(self, cldb):
        self.clDB = cldb
        self.flFecha = False
        self.idRecorrido = 0
        self.stTurno = ""
        self.closeTV = False
        self.settings = QSettings("/home/pi/innobusmx/settings.ini", QSettings.IniFormat)

        subprocess.call("xset dpms force on",shell=True)
        subprocess.call("xset dpms s off",shell=True)
        subprocess.call("xset dpms s noblank",shell=True)
        subprocess.call("xset -dpms",shell=True)                    
        
        super(mainWin, self).__init__()
        self.initUI()

        '''
            ############################################################
                    Pantalla Principal del Sistema de Prepago

            ############################################################
        '''
        if os.path.exists('/home/pi/innobusmx/innobus.log'):
            os.remove('/home/pi/innobusmx/innobus.log')
        self.logo = QtGui.QLabel(self)
        self.logo.setScaledContents(True)
        pathImgFondo = os.path.join('/home/pi/innobusmx/data/img/wall2.jpg')
        self.logo.setPixmap(QtGui.QPixmap(pathImgFondo))
        self.logo.move(0, 0)
        self.logo.resize(800, 480)
        
        self.imgOperador = QtGui.QLabel(self)
        self.imgOperador.setPixmap(QtGui.QPixmap(''))
        self.imgOperador.setScaledContents(True)
        self.imgOperador.move(90, 5)
        self.imgOperador.resize(280, 368)
        self.imgOperador.hide()

        self.lblNombreOperador = QtGui.QLabel("", self)
        self.lblNombreOperador.resize(self.width(), 50)
        self.lblNombreOperador.move(65, 380)
        self.lblNombreOperador.setStyleSheet('QLabel { font-size: 20pt; font-family: Arial; color:White}')

        self.lblVersion = QtGui.QLabel("", self)
        self.lblVersion.resize(self.width(), 50)
        self.lblVersion.move(750, 42)
        self.lblVersion.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:Gray}')
        self.lblVersion.setText(self.stVersion)

        self.lblError = QtGui.QLabel("", self)
        self.lblError.resize(self.width(), 50)
        self.lblError.move(5, 420)
        self.lblError.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:White}')

        self.lblNS = QtGui.QLabel("", self)
        self.lblNS.resize(self.width(), 50)
        self.lblNS.move(5, 435)
        self.lblNS.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:White}')

        self.lblNSFirmware = QtGui.QLabel("", self)
        self.lblNSFirmware.resize(self.width(), 50)
        self.lblNSFirmware.move(5, 447)
        self.lblNSFirmware.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:White}')

        self.lblUnidad = QtGui.QLabel("", self)
        self.lblUnidad.resize(self.width(), 50)
        self.lblUnidad.move(650, 120)
        self.lblUnidad.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')

        self.lblVuelta = QtGui.QLabel("", self)
        self.lblVuelta.resize(self.width(), 50)
        self.lblVuelta.move(650, 190)
        self.lblVuelta.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')

        self.lblNoRuta = QtGui.QLabel("", self)
        self.lblNoRuta.resize(self.width(), 50)
        self.lblNoRuta.move(620, 260)
        self.lblNoRuta.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')

        self.lblRuta = QtGui.QLabel("", self)
        self.lblRuta.resize(330, 50)
        self.lblRuta.move(470, 290)
        self.lblRuta.setStyleSheet('QLabel { font-size: 18pt; font-family: Arial; color:White}')
        self.lblRuta.setAlignment(QtCore.Qt.AlignCenter)

        self.lblVelocidad = QtGui.QLabel("", self)
        self.lblVelocidad.resize(self.width(), 50)
        self.lblVelocidad.move(670, 325)
        self.lblVelocidad.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:White}')

        self.lblHora = QtGui.QLabel("", self)
        self.lblHora.resize(800, 50)
        #self.lblHora.resize(self.width(), 50)
        #self.lblHora.move(550, 440)
        self.lblHora.setStyleSheet('QLabel { font-size: 14pt; font-family: Arial; color:White}')
        self.lblHora.setAlignment(QtCore.Qt.AlignRight)
        self.lblHora.move(0, 455)

        self.no3G = QtGui.QLabel(self)
        self.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/no3G.Jpeg"))
        self.no3G.setScaledContents(True)
        self.no3G.move(770,425)
        self.no3G.resize(20, 20)

        self.noGPS = QtGui.QLabel(self)
        self.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPSEncendido.png"))
        self.noGPS.setScaledContents(True)
        self.noGPS.move(740,425)
        self.noGPS.resize(20, 20)
        #self.noGPS.mousePressEvent = self.Ok

        self.noSocket = QtGui.QLabel(self)
        self.noSocket.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noSocket.png"))
        self.noSocket.setScaledContents(True)
        self.noSocket.move(650,425)
        self.noSocket.resize(20, 20)

        self.noFTP = QtGui.QLabel(self)
        self.noFTP.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noFTP.Jpeg"))
        self.noFTP.setScaledContents(True)
        self.noFTP.move(680,425)
        self.noFTP.resize(20, 20)

        self.noRDIF = QtGui.QLabel(self)
        self.noRDIF.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRFID.Jpeg"))
        self.noRDIF.setScaledContents(True)
        self.noRDIF.move(620,425)
        self.noRDIF.resize(20, 20)

        self.noRed = QtGui.QLabel(self)
        self.noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRed.Jpeg"))
        self.noRed.setScaledContents(True)
        self.noRed.move(590,425)
        self.noRed.resize(20, 20)

        self.noSIM = QtGui.QLabel(self)
        self.noSIM.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noSIM.png"))
        self.noSIM.setScaledContents(True)
        self.noSIM.move(550,425)
        self.noSIM.resize(32, 20)
        """
        ########## ERNESTO LOMAR ##########
        self.noAlttus = QtGui.QLabel(self)
        self.noAlttus.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/alttusti.png"))
        self.noAlttus.setScaledContents(True)
        self.noAlttus.move(680,425)
        self.noAlttus.resize(50, 20)
        ###################################"""

        imgTarjetaAtras = "/home/pi/innobusmx/data/img/imgTarjetas/Cl.jpg"
        imgUsuarioTarjeta = "/home/pi/innobusmx/data/user/admin.Jpeg"
        
        self.flFTP = False
        self.flRed = False
        self.flSocket = False        
        ########## ERNESTO LOMAR ##########
        self.flAlttus  =False
        ###################################
        self.flComm = True
        self.iComm = 0
        self.flRFID = False
        self.flSIM = False
        self.flQuectel = False
        self.iccid = ""
        self.sd = ""
        self.cpuSerial = ""

        self.flSendAforo = False
        self.flSendInicioRecorrido = False
        self.flSendTerminoRecorrido = False
        self.flSendInicioVuelta = False
        self.flSendActualizaVuelta = False
        self.flSendTerminoVuelta = False
        self.flSendPuntoControl = False
        self.flSendActualizaPuntoControl = False
        self.flSendData = False
        self.flSendGPS = False
        self.flSendEnvio = False
        self.flDataGPS = False
        self.retorno = False

        self.mttoGPS = 0
        self.flGPS = False
        self.flGPSOK = False
        self.flMtto = False
        self.flTurno = False
        self.flVuelta = False
        self.flDespachador = False
        self.flOperador = False
        self.flIniciar = None

        self.serialNumber = ""
        self.version = ""
        self.versionSO = ""
        self.TISC = ""
        self.stImgTarjeta = ""
        self.stSaldo = ""
        self.stTarjeta = ""
        self.stNombre = ""
        self.stApellido = ""
        self.stNombreO = ""
        self.stApellidoO = ""
        self.stNombreD = ""
        self.stApellidoD = ""
        self.stSaldoInsuficiente = ""
        self.stMsg = ""
        self.stMsgVigencia = ""
        self.lastConnection = time.time()
        self.stNIP = ""
        self.stCSNO = ''
        self.stCSND = ''

        '''
            ############################################################
                Aqui estan las variables que necesito para mostrar
                        la informacion de los aforo
            ############################################################
        '''

        self.imgTarjeta = QtGui.QLabel(self)
        self.imgTarjeta.setPixmap(QtGui.QPixmap(''))
        self.imgTarjeta.setScaledContents(True)
        self.imgTarjeta.move(0,0)
        self.imgTarjeta.resize(800, 450)
        self.imgTarjeta.hide()

        self.imgDefault = QtGui.QLabel(self)
        self.imgDefault.setPixmap(QtGui.QPixmap(''))
        self.imgDefault.setScaledContents(True)
        self.imgDefault.move(0,0)
        self.imgDefault.resize(422,450)
        self.imgDefault.hide()

        self.lblNombre = QtGui.QLabel("", self)
        self.lblNombre.resize(376, 70)
        self.lblNombre.move(424, 80)
        self.lblNombre.setStyleSheet('QLabel { font-size: 40pt; font-family: Arial; color:White}')
        self.lblNombre.setAlignment(QtCore.Qt.AlignCenter)
        self.lblNombre.hide()       

        self.lblApellido = QtGui.QLabel("", self)
        self.lblApellido.resize(376, 50)
        self.lblApellido.move(424, 145)
        self.lblApellido.setStyleSheet('QLabel { font-size: 25pt; font-family: Arial; color:White}')
        self.lblApellido.setAlignment(QtCore.Qt.AlignCenter)

        self.lblSaldo = QtGui.QLabel("", self)
        self.lblSaldo.resize(376, 75)
        self.lblSaldo.move(424, 290)
        self.lblSaldo.setStyleSheet('QLabel { font-size: 50pt; font-family: Arial; color:White}')
        self.lblSaldo.setAlignment(QtCore.Qt.AlignCenter)

        self.lblMsgVigencia = QtGui.QLabel("", self)
        self.lblMsgVigencia.resize(400, 75)
        self.lblMsgVigencia.move(424, 10)
        self.lblMsgVigencia.setStyleSheet('QLabel { font-size: 25pt; font-family: Arial; color:Red}')
        self.lblMsgVigencia.setAlignment(QtCore.Qt.AlignCenter)

        self.lblSaldoInsuficiente = QtGui.QLabel("", self)
        self.lblSaldoInsuficiente.resize(self.width(), 75)
        self.lblSaldoInsuficiente.move(470, 380)
        self.lblSaldoInsuficiente.setStyleSheet('QLabel { font-size: 35pt; font-family: Arial; color:Red}')

        self.lblMsg = QtGui.QLabel("", self)
        self.lblMsg.resize(self.width(), 75)
        self.lblMsg.move(750, 355)
        self.lblMsg.setStyleSheet('QLabel { font-size: 8pt; font-family: Arial; color:Red}')
        self.lblMsg.setText("")

        self.lblSS = QtGui.QLabel("", self)
        self.lblSS.resize(self.width(), 50)
        self.lblSS.move(270, 45)
        self.lblSS.setStyleSheet('QLabel { font-size: 45pt; font-family: Arial; color:White}')

        self.lblVAI = QtGui.QLabel("", self)
        self.lblVAI.resize(self.width(), 50)
        self.lblVAI.move(150, 45)
        self.lblVAI.setStyleSheet('QLabel { font-size: 50pt; font-family: Arial; color:White}')

        self.lblSSMsg = QtGui.QLabel("", self)
        self.lblSSMsg.resize(self.width(), 50)
        self.lblSSMsg.move(150, 350)
        self.lblSSMsg.setStyleSheet('QLabel { font-size: 45pt; font-family: Arial; color:White}')

        self.lblTarjetas = QtGui.QLabel("", self)
        self.lblTarjetas.resize(self.width(), 50)
        self.lblTarjetas.move(180, 220)
        self.lblTarjetas.setStyleSheet('QLabel { font-size: 30pt; font-family: Arial; color:Yellow}')

        '''
            ############################################################
                Aqui estan las variables que necesito para mostrar
                        la informacion de las Vueltas y Turnos
            ############################################################
        '''

        self.lblInicioFin = QtGui.QLabel("", self)
        self.lblInicioFin.resize(363, 100)
        self.lblInicioFin.move(432, 85)
        self.lblInicioFin.setStyleSheet('QLabel { font-size: 35pt; font-family: Arial; color:White}')
        self.lblInicioFin.setAlignment(QtCore.Qt.AlignCenter)

        self.lblTurno = QtGui.QLabel("", self)
        self.lblTurno.resize(363, 50)
        self.lblTurno.move(432, 220)
        self.lblTurno.setStyleSheet('QLabel { font-size: 20pt; font-family: Arial; color:Black}')
        self.lblTurno.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTurno.hide()

        self.wLstVueltas = 480
        self.xLstVueltas = 320
        self.lstVueltas = QtGui.QListWidget(self)
        self.lstVueltas.resize(self.wLstVueltas, 290)
        self.lstVueltas.move(self.xLstVueltas, 110)
        self.lstVueltas.setStyleSheet('QListWidget { font-size: 14pt; font-family: Arial; color:Black}')
        self.lstVueltas.hide()

        self.lblNV = QtGui.QLabel("", self)
        self.lblNV.resize(376, 100)
        self.lblNV.move(432, 180)
        self.lblNV.setStyleSheet('QLabel { font-size: 50pt; font-family: Arial; color:Green}')
        self.lblNV.setAlignment(QtCore.Qt.AlignCenter)
        self.lblNV.hide()

        self.lblTurnoT = QtGui.QLabel("", self)
        self.lblTurnoT.resize(376,30)
        self.lblTurnoT.move(432,125)
        self.lblTurnoT.setStyleSheet('QLabel { font-size: 18pt; font-family: Arial; color:Black}')
        #self.lblTurnoT.setAlignment(QtCore.Qt.AlignCenter)
        self.lblTurnoT.hide()

        self.cbTurno = QtGui.QComboBox(self)
        self.cbTurno.move(515,120)
        self.cbTurno.resize(260, 50)
        #self.cbTurno.currentIndexChanged.connect(self.click_cbTurno)
        self.cbTurno.setStyleSheet('QComboBox { font-size: 20pt; font-family: Arial; color:Black}')
        self.cbTurno.hide()

        self.lblRutaT = QtGui.QLabel("", self)
        self.lblRutaT.resize(376,30)
        self.lblRutaT.move(432,165)
        self.lblRutaT.setStyleSheet('QLabel { font-size: 18pt; font-family: Arial; color:Black}')
        #self.lblRutaT.setAlignment(QtCore.Qt.AlignCenter)
        self.lblRutaT.hide()
        self.lblRutaT.setText("Ruta")

        self.cbRuta = QtGui.QComboBox(self)
        self.cbRuta.move(425,195)
        self.cbRuta.resize(350, 50)
        self.cbRuta.hide()
        #self.cbRuta.currentIndexChanged.connect(self.click_cbRuta)
        self.cbRuta.setStyleSheet('QComboBox { font-size: 20pt; font-family: Arial; color:Black}')

        self.lblNVT = QtGui.QLabel("", self)
        self.lblNVT.resize(376,70)
        self.lblNVT.move(450,290)
        self.lblNVT.setStyleSheet('QLabel { font-size: 18pt; font-family: Arial; color:Black}')
        self.lblNVT.hide()

        self.spNV = QtGui.QSpinBox(self)
        self.spNV.setRange(0,10)
        self.spNV.move(550,260)
        self.spNV.resize(136, 120)
        self.spNV.setStyleSheet('QSpinBox { font-size: 60pt; font-family: Arial; color:Green}')
        self.spNV.setAlignment(QtCore.Qt.AlignCenter)
        self.spNV.setRange(1,15)
        self.spNV.setValue(1)
        self.spNV.hide()


        self.chkVuelta = QtGui.QCheckBox("Cerrar Vuelta?",self)
        self.chkVuelta.move(400,280)
        self.chkVuelta.resize(180, 40)
        self.chkVuelta.setStyleSheet('QCheckBox { font-size: 16pt; font-family: Arial; color:Red; width:150; height:150}')
        self.chkVuelta.stateChanged.connect(self.click_chkVuelta)
        self.chkVuelta.hide()

        self.lblPersonal = QtGui.QLabel("", self)
        self.lblPersonal.resize(376, 70)
        self.lblPersonal.move(432, 400)
        self.lblPersonal.setStyleSheet('QLabel { font-size: 18pt; font-family: Arial; color:Black}')
        self.lblPersonal.setAlignment(QtCore.Qt.AlignCenter)
        self.lblPersonal.hide()

        self.btnOK = QtGui.QLabel(self)
        self.btnOK.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/ok.png"))
        self.btnOK.setScaledContents(True)
        self.btnOK.resize(45, 45)
        self.btnOK.move(575,400)
        self.btnOK.hide()
        self.btnOK.mousePressEvent = self.click_btnOK

        self.btnCancel = QtGui.QLabel(self)
        self.btnCancel.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/no.png"))
        self.btnCancel.setScaledContents(True)
        self.btnCancel.move(720, 400)
        self.btnCancel.resize(45, 45)
        self.btnCancel.hide()
        self.btnCancel.mousePressEvent = self.click_btnCancel

        self.btnCerrarVuelta = QtGui.QLabel(self)
        self.btnCerrarVuelta.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/cerrarVuelta.png"))
        self.btnCerrarVuelta.setScaledContents(True)
        self.btnCerrarVuelta.move(575, 395)
        self.btnCerrarVuelta.resize(45, 52)
        self.btnCerrarVuelta.hide()
        self.btnCerrarVuelta.mousePressEvent = self.click_btnCerrarVuelta

        self.btnIniciarVuelta = QtGui.QLabel(self)
        self.btnIniciarVuelta.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/iniciarVuelta.png"))
        self.btnIniciarVuelta.setScaledContents(True)
        self.btnIniciarVuelta.move(450, 395)
        self.btnIniciarVuelta.resize(45, 52)
        self.btnIniciarVuelta.hide()
        self.btnIniciarVuelta.mousePressEvent = self.click_btnIniciarVuelta

        self.lblVta = QtGui.QLabel("", self)
        self.lblVta.resize(376,20)
        self.lblVta.move(495,427)
        self.lblVta.setStyleSheet('QLabel { font-size: 20pt; font-family: Arial; color:Green}')
        self.lblVta.hide()

        self.btnCambiarRuta = QtGui.QLabel(self)
        self.btnCambiarRuta.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/cambiarRuta.png"))
        self.btnCambiarRuta.setScaledContents(True)
        self.btnCambiarRuta.move(540, 395)
        self.btnCambiarRuta.resize(45, 52)
        self.btnCambiarRuta.hide()
        self.btnCambiarRuta.mousePressEvent = self.click_btnCambiarRuta

        self.btnCerrarTurno = QtGui.QLabel(self)
        self.btnCerrarTurno.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/cerrarTurno.png"))
        self.btnCerrarTurno.setScaledContents(True)
        self.btnCerrarTurno.move(630, 395)
        self.btnCerrarTurno.resize(45, 52)
        self.btnCerrarTurno.hide()
        self.btnCerrarTurno.mousePressEvent = self.click_btnCerrarTurno

        '''
            ############################################################
                Aqui estan las variables que necesito para mostrar
                        la informacion de Mantenimiento
            ############################################################
        '''

        self.btnReset = QtGui.QLabel(self)
        self.btnReset.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/resetVal.jpg"))
        self.btnReset.setScaledContents(True)
        self.btnReset.move(275,125)
        self.btnReset.resize(145, 136)
        self.btnReset.hide()
        self.btnReset.mousePressEvent = self.click_btnReset

        self.btnReinicio = QtGui.QLabel(self)
        self.btnReinicio.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/resetCyti.jpg"))
        self.btnReinicio.setScaledContents(True)
        self.btnReinicio.move(536,138)
        self.btnReinicio.resize(158, 110)
        self.btnReinicio.hide()
        self.btnReinicio.mousePressEvent = self.click_btnReinicio

        self.btnGPSOn = QtGui.QLabel(self)
        self.btnGPSOn.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/GPSOn.jpg"))
        self.btnGPSOn.setScaledContents(True)
        self.btnGPSOn.move(242,280)
        self.btnGPSOn.resize(209, 52)
        self.btnGPSOn.hide()
        self.btnGPSOn.mousePressEvent = self.click_btnGPSOn

        self.btnGPSOff = QtGui.QLabel(self)
        self.btnGPSOff.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/GPSOff.jpg"))
        self.btnGPSOff.setScaledContents(True)
        self.btnGPSOff.move(242,280)
        self.btnGPSOff.resize(209, 52)
        self.btnGPSOff.hide()
        self.btnGPSOff.mousePressEvent = self.click_btnGPSOff

        self.btnResetModem = QtGui.QLabel(self)
        self.btnResetModem.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/reset3G.jpg"))
        self.btnResetModem.setScaledContents(True)
        self.btnResetModem.move(536,280)
        self.btnResetModem.resize(145, 52)
        self.btnResetModem.hide()
        self.btnResetModem.mousePressEvent = self.click_btnResetModem

        self.btnResetHard3G = QtGui.QLabel(self)
        self.btnResetHard3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/resetHard3G.jpg"))
        self.btnResetHard3G.setScaledContents(True)
        self.btnResetHard3G.move(546,350)
        self.btnResetHard3G.resize(145, 52)
        self.btnResetHard3G.hide()
        self.btnResetHard3G.mousePressEvent = self.click_btnResetHard3G

        self.btnResetUSB = QtGui.QLabel(self)
        self.btnResetUSB.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/resetUSB.jpg"))
        self.btnResetUSB.setScaledContents(True)
        self.btnResetUSB.move(310,350)
        self.btnResetUSB.resize(145, 52)
        self.btnResetUSB.hide()
        self.btnResetUSB.mousePressEvent = self.click_btnResetUSB

        self.btnGpioGUI = QtGui.QLabel(self)
        self.btnGpioGUI.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/resetGPIO.png"))
        self.btnGpioGUI.setScaledContents(True)
        self.btnGpioGUI.move(125,350)
        self.btnGpioGUI.resize(145, 52)
        self.btnGpioGUI.hide()
        self.btnGpioGUI.mousePressEvent = self.click_btnGpioGUI

        self.btnAmbulancia = QtGui.QLabel(self)
        self.btnAmbulancia.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/ambulancia.png"))
        self.btnAmbulancia.setScaledContents(True)
        self.btnAmbulancia.move(200,175)
        self.btnAmbulancia.resize(100, 100)
        self.btnAmbulancia.hide()
        self.btnAmbulancia.mousePressEvent = self.click_btnAmbulancia

        self.btnPolicia = QtGui.QLabel(self)
        self.btnPolicia.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/policia.png"))
        self.btnPolicia.setScaledContents(True)
        self.btnPolicia.move(350,175)
        self.btnPolicia.resize(100, 100)
        self.btnPolicia.hide()
        self.btnPolicia.mousePressEvent = self.click_btnPolicia

        self.btnTransito = QtGui.QLabel(self)
        self.btnTransito.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/policia.png"))
        self.btnTransito.setScaledContents(True)
        self.btnTransito.move(500,175)
        self.btnTransito.resize(100, 100)
        self.btnTransito.hide()
        self.btnTransito.mousePressEvent = self.click_btnTransito

        self.btn911 = QtGui.QLabel(self)
        self.btn911.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/911.png"))
        self.btn911.setScaledContents(True)
        self.btn911.move(650,175)
        self.btn911.resize(100, 100)
        self.btn911.hide()
        self.btn911.mousePressEvent = self.click_btn911
        
        self.btnSalir = QtGui.QLabel(self)
        self.btnSalir.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/salir.png"))
        self.btnSalir.setScaledContents(True)
        self.btnSalir.move(650,350)
        self.btnSalir.resize(100, 100)
        self.btnSalir.hide()
        self.btnSalir.mousePressEvent = self.click_btnSalir

        self.imgEvento = QtGui.QLabel(self)
        self.imgEvento.setPixmap(QtGui.QPixmap(''))
        self.imgEvento.setScaledContents(True)
        self.imgEvento.move(450, 110)
        self.imgEvento.resize(350, 290)
        self.imgEvento.hide()

        self.setGeometry(-1, 0, 800, 480)
        self.setWindowTitle('CytiBus '+self.stVersion)
        self.setStyleSheet('''QMainWindow { background-color:#1D2556;}
            QLabel{font-size: 15pt; font-family: Courier; color:black;
            font-weight: bold}''')

        self.lblNoRuta.setText("")
        self.lblRuta.setText("")

        #if True:
        try:
            c = self.clDB.dbAforo.cursor()
            try:
                c.execute('SELECT idChofer, csn, nombre, apellidoPa FROM usuario')
            except:
                c.execute('SELECT idChofer, csn, "-" AS nombre, "-" AS apellidoPa FROM usuario')
                
            data = c.fetchone()
            if (data is None or data[1] == ''):
                self.idOperador = 77
                self.csn = '042C43420A5758'
                self.stNombreO = ''
                self.stApellidoO = ''
                self.stOperador = ''
                self.lblNombreOperador.setText('')
                self.imgOperador.setPixmap(QtGui.QPixmap(''))
                self.imgOperador.hide()
                subprocess.call("xset dpms 0 300 0",shell=True)
            else:
                self.idOperador = data[0]
                self.csn = data[1]
                if (data[2] is None):
                    self.stNombreO = ""
                else:
                    self.stNombreO = data[2].encode('latin-1')
                if (data[3] is None):
                    self.stApellidoO = ""
                else:                    
                    self.stApellidoO = data[3].encode('latin-1')
                self.stOperador = self.stNombreO + ' ' + self.stApellidoO
                self.lblNombreOperador.setText(self.stOperador)
              
                path = '/home/pi/innobusmx/data/user/'+data[1][0:5]+"/"+data[1]+".Jpeg"
                if not os.path.isfile(path):
                    path = '/home/pi/innobusmx/data/user/generico.jpg'
                self.imgOperador.setPixmap(QtGui.QPixmap(path))
                self.imgOperador.show()
                subprocess.call("xset dpms 0 0 0",shell=True)

            self.lblUnidad.setText(str(self.clDB.economico))
            print ('SELECT numRuta, Nombre FROM ruta WHERE idTransportista = '+str(self.clDB.idTransportista)+ ' and idRuta = '+str(self.clDB.idRuta))
            c.execute('SELECT numRuta, Nombre FROM ruta WHERE idTransportista = '+str(self.clDB.idTransportista)+ ' and idRuta = '+str(self.clDB.idRuta))
            data = c.fetchone()
            if (data is None):
                self.lblNoRuta.setText('')
                self.lblRuta.setText('')
            else:
                self.lblNoRuta.setText(str(data[0]))
                self.lblRuta.setText(str(data[1].encode('latin-1')))
            self.stId = self.idOperador
            self.stCSNO = self.csn

            c.execute('SELECT Max(idRecorrido) FROM recorrido WHERE termino IS NULL')
            data = c.fetchone()
            if (data[0] is None):
                self.idRecorrido = 0
                self.noVuelta = 0
                self.lblVuelta.setText("")
            else:
                self.idRecorrido = data[0]
                c.execute('SELECT vuelta, csnInicio FROM vuelta WHERE termino IS NULL AND idRecorrido = '+str(self.idRecorrido)+' ORDER BY inicio DESC LIMIT 1')
                data = c.fetchone()
                if (data is None):
                    self.noVuelta = 0
                    self.lblVuelta.setText("")
                    #self.flIniciar = True
                else:
                    self.noVuelta = data[0]
                    self.lblVuelta.setText(str(data[0]))
                    self.csn = data[1]
                    #self.flIniciar = False

            c.execute('SELECT nombre, idTurno FROM tTurno')
            data = c.fetchone()
            while not (data is None):
                self.cbTurno.addItem(data[0], data[1])
                data = c.fetchone()
            c.execute('SELECT idRuta, nombre FROM ruta WHERE idTransportista = '+str(self.clDB.idTransportista)+' ORDER BY nombre')
            data = c.fetchone()
            while not (data is None):
                self.cbRuta.addItem(data[1], data[0])
                data = c.fetchone()
            self.cbRuta.hide()
            if (self.idRecorrido > 0):
                c.execute('SELECT nombre FROM recorrido, tTurno WHERE idRecorrido = '+str(self.idRecorrido)+' AND tTurno.idTurno = recorrido.idTurno')
                data = c.fetchone()
                if not (data is None):
                    self.stTurno = data[0]
            c.close()
            c = None
        #else:
        except:
            self.idOperador = 77
            self.csn = '042C43420A5758'
        self.showMaximized()
        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
        self.showFullScreen()
        #self.center()
        #self.show()
        self.cbRuta.currentIndexChanged.connect(self.click_cbRuta)
        self.cbTurno.currentIndexChanged.connect(self.click_cbTurno)
        
    def center(self): 
        frameGm = self.frameGeometry()
        centerPoint = QtGui.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def initNoVuelta(self, idTurno, idRuta):
        c = self.clDB.dbAforo.cursor()
        print 'SELECT MAX(vuelta) FROM vuelta, recorrido WHERE SUBSTR(vuelta.inicio,1,10) = "'+time.strftime("%Y-%m-%d")+'" AND idRuta = '+str(idRuta)+' AND idTurno = '+str(idTurno)+' AND SUBSTR(vuelta.inicio,1,10) = SUBSTR(recorrido.inicio,1,10) AND vuelta.idRecorrido = recorrido.idRecorrido'
        c.execute('SELECT MAX(vuelta) FROM vuelta, recorrido WHERE SUBSTR(vuelta.inicio,1,10) = "'+time.strftime("%Y-%m-%d")+'" AND idRuta = '+str(idRuta)+' AND idTurno = '+str(idTurno)+' AND SUBSTR(vuelta.inicio,1,10) = SUBSTR(recorrido.inicio,1,10) AND vuelta.idRecorrido = recorrido.idRecorrido')
        data = c.fetchone()
        if data[0] is None:
            noVuelta = 1
        else:
            if data[0] is None:
                noVuelta = 1
            else:
                noVuelta = data[0]+1
        self.spNV.setRange(noVuelta,15)
        self.spNV.setValue(noVuelta)

    def click_cbTurno(self):
        idRuta = self.cbRuta.itemData(self.cbRuta.currentIndex()).toString()
        idTurno = self.cbTurno.itemData(self.cbTurno.currentIndex()).toString()
        self.initNoVuelta(idTurno, idRuta)

    def click_cbRuta(self):
        idTurno = self.cbTurno.itemData(self.cbTurno.currentIndex()).toString()
        idRuta = self.cbRuta.itemData(self.cbRuta.currentIndex()).toString()
        if (idRuta is None or idRuta == ""):
            idRuta = 0
            self.spNV.hide()
        else:
            self.initNoVuelta(idTurno, idRuta)

    def ventanaEvento(self, fl):
        if fl:
            self.imgEvento.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/login.jpg'))
            self.imgEvento.show()
        else:    
            self.imgEvento.setPixmap(QtGui.QPixmap(""))
            self.imgEvento.hide()
            self.flEventoExitoso == 0

    def evento(self, tipo):
        if (tipo == 6):
            st = "Emergencia Medica"
        if (tipo == 7):
            st = "Emergencia de Seguridad"
        if (tipo == 8):
            st = "Emergencia de Transito"
        if (tipo == 9):
            st = "Llamada al 911"
        fecha = time.strftime('%Y-%m-%d %H:%M:%S')
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
        self.stBoton = "p,"+str(self.clDB.idTransportista)+","+str(self.clDB.idUnidad)+","+str(tipo)+","+st+","+str(self.csn)+","+lat+","+lon+","+str(self.velGPS)+","+fechaGPS+","+str(fecha)+","+str(self.clDB.idRuta)+","+str(self.idOperador)
        self.cierraVentanaOperador()

    def click_btnAmbulancia(self, event):
        self.evento(6)

    def click_btnPolicia(self, event):
        self.evento(7)

    def click_btnTransito(self, event):
        self.evento(8)

    def click_btn911(self, event):
        self.evento(9)
        
    def click_btnReset(self, event):
        os.system('sudo reboot')

    def click_btnGpioGUI(self, event):
	command="/home/pi/innobusmx/application"
	subprocess.Popen(command)
	self.btnGpioGUI.show()

    def click_btnReinicio(self, event):
        self.settings.setValue("apagado_forzado",1)
        python = sys.executable
        os.execl(python, python, * sys.argv)           

    def click_btnGPSOn(self, event):
        self.flGPSOK = False
        self.mttoGPS = 2
        self.btnGPSOn.hide()

    def click_btnGPSOff(self, event):
        self.flGPSOK = True
        self.mttoGPS = 1
        self.btnGPSOff.hide()

    def click_btnResetModem(self, event):
        self.mttoGPS = 3
        self.btnResetModem.hide()

    def click_btnResetUSB(self, event):
        self.mttoGPS = 4
        self.btnResetUSB.hide()
       
    def click_btnResetHard3G(self, event):
        self.mttoGPS = 5
        self.btnResetHard3G.hide()

    def click_btnSalir(self, event):
        self.cierreDeOperador()

    def click_btnCancel(self, event):
        self.cancelar()

    def click_btnCambiarRuta(self, event):
        self.cancelaDespachador()
        self.imgTarjeta.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/login.jpg'))
        self.imgTarjeta.show()
        self.lblInicioFin.setStyleSheet('QLabel { font-size: 28pt; font-family: Arial; background-color:Green; color:White}')
        self.lblInicioFin.resize(363, 35)
        self.lblInicioFin.move(432, 75)
        self.lblInicioFin.setText('Recorridos')
        self.lblInicioFin.show()
        self.lblTurnoT.setStyleSheet('QLabel { font-size: 22pt; font-family: Arial; color:Black}')
        st = "Turno: "+self.cbTurno.currentText()
        self.lblTurnoT.setText(st)
        self.lblTurnoT.show()
        #self.cbTurno.show()
        self.lblRutaT.show()
        self.cbRuta.show()
        self.lblNVT.show()
        self.spNV.show()
        self.lblNVT.setText('Inicia\nVuelta')
        if (self.cbRuta.count() > 0):
            self.btnOK.show()
            idRuta = self.cbRuta.itemData(self.cbRuta.currentIndex()).toString()
            idTurno = self.cbTurno.itemData(self.cbTurno.currentIndex()).toString()
            self.initNoVuelta(idTurno, idRuta)        
        else:
            self.btnOK.hide()
        self.btnCancel.show()

    def iniciaVuelta(self):
        print "iniciaVUelta"
        c = self.clDB.dbAforo.cursor()
        c.execute('SELECT MAX(vuelta) FROM vuelta WHERE SUBSTR(inicio,1,10) = "'+time.strftime("%Y-%m-%d")+'" AND idRuta = '+str(self.clDB.idRuta))
        data = c.fetchone()
        if (data is None):
            self.noVuelta = 1
        else:
            self.noVuelta = data[0]+1
        st = self.stOperador.decode('latin-1')
        c.execute("INSERT INTO vuelta (idRecorrido, idRuta, vuelta, inicio, csnInicio, operador, enviadoInicio, idVuelta, tipo) VALUES (?,?,?,?,?,?,0,0,1)",(str(self.idRecorrido), str(self.clDB.idRuta), str(self.noVuelta), time.strftime("%Y-%m-%d %H:%M:%S"), str(self.stCSND), st))
        self.clDB.dbAforo.commit()  
        self.lblVuelta.setText(str(self.noVuelta))
        self.flSendInicioVuelta = True

        c = self.clDB.dbFlota.cursor()
        print('DELETE FROM asignacion')
        c.execute('DELETE FROM asignacion')
        print('INSERT INTO asignacion (idTransportista, idRuta, idPuntoInteres, total) VALUES (' + str(self.clDB.idTransportista) + ',' + str(self.clDB.idRuta) + ',1,' +  '(SELECT COUNT(*) FROM vPuntoControl WHERE idRuta = ' + str(self.clDB.idRuta) + '))' )
        c.execute('INSERT INTO asignacion (idTransportista, idRuta, idPuntoInteres, total) VALUES (' + str(self.clDB.idTransportista) + ',' + str(self.clDB.idRuta) + ',1,' +  '(SELECT COUNT(*) FROM vPuntoControl WHERE idRuta = ' + str(self.clDB.idRuta) + '))' )
        self.clDB.dbFlota.commit()
        self.flIdRutaAutomatica = False
        self.cancelaDespachador()

    def click_btnIniciarVuelta(self, event):
        print "btnIniciaVuelta"
        self.iniciaVuelta()

    def click_btnCerrarVuelta(self, event):
        print "btnCerrarVuelta"
        if self.clDB.vueltaValida(self.idRecorrido, self.noVuelta):
            print("UPDATE vuelta SET termino = ?, csnTermino = ?, enviadoTermino = 0 WHERE idRecorrido = ? AND vuelta = ?",(time.strftime("%Y-%m-%d %H:%M:%S"), self.stCSND, self.idRecorrido, str(self.noVuelta)))
            self.clDB.dbAforo.execute("UPDATE vuelta SET termino = ?, csnTermino = ?, enviadoTermino = 0 WHERE idRecorrido = ? AND vuelta = ?",(time.strftime("%Y-%m-%d %H:%M:%S"), self.stCSND, self.idRecorrido, str(self.noVuelta)))
        else:
            print("UPDATE vuelta SET vuelta = 0, termino = ?, csnTermino = ?, enviadoTermino = 0 WHERE idRecorrido = ? AND vuelta = ?",(time.strftime("%Y-%m-%d %H:%M:%S"), self.stCSND, self.idRecorrido, str(self.noVuelta)))
            self.clDB.dbAforo.execute("UPDATE vuelta SET vuelta = 0, termino = ?, csnTermino = ?, enviadoTermino = 0 WHERE idRecorrido = ? AND vuelta = ?",(time.strftime("%Y-%m-%d %H:%M:%S"), self.stCSND, self.idRecorrido, str(self.noVuelta)))
            print('UPDATE puntoControl SET vuelta = 0 WHERE idRecorrido = '+str(self.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta)+' AND vuelta = '+str(self.noVuelta))
            self.clDB.dbFlota.execute('UPDATE puntoControl SET vuelta = 0 WHERE idRecorrido = '+str(self.idRecorrido)+' AND idRuta = '+str(self.clDB.idRuta)+' AND vuelta = '+str(self.noVuelta))
        self.clDB.dbAforo.commit()      
        self.flSendTerminoVuelta = True
        self.flIdRutaAutomatica = True
        self.lblVuelta.setText("")
        self.noVuelta = 0
        self.cancelaDespachador()

    def click_btnCerrarTurno(self, event):
        c = self.clDB.dbAforo.cursor()
        c.execute("UPDATE recorrido SET termino = ?, csnTermino = ?, enviadoTermino = 0 WHERE idRecorrido = ?",(time.strftime("%Y-%m-%d %H:%M:%S"), self.stCSND, self.idRecorrido))
        self.clDB.dbAforo.commit()
        c.execute("UPDATE parametros SET idRutaActual = 0")
        self.clDB.dbAforo.commit()
        self.lblNoRuta.setText("")
        self.lblRuta.setText("")
        self.idRecorrido = 0
        self.clDB.idRuta = 0
        self.flSendTerminoRecorrido = True
        self.cancelaDespachador()

    def Mantenimiento(self):
        self.imgTarjeta.show()
        self.imgTarjeta.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/login.jpg'))
        self.lblInicioFin.setStyleSheet('QLabel { font-size: 24pt; font-family: Arial; background-color:Gray; color:White}')
        self.lblInicioFin.resize(550, 40)
        self.lblInicioFin.move(230, 75)
        self.lblInicioFin.setText('Ventana de Mantenimiento')
        self.btnReset.show()
        self.btnReinicio.show()
        self.lblInicioFin.show()
        self.btnGpioGUI.show()
        if (self.flGPSOK):
            self.btnGPSOn.show()
        else:
            self.btnGPSOff.show()
        self.btnResetModem.show()
        if (self.serialNumber[0:3] != "Ix1"):
            self.btnResetHard3G.show()
            self.btnResetUSB.show()
        self.btnOK.move(482,400)
        self.btnOK.show()

    def cancelar(self):
        if self.spNV.isVisible() or self.lstVueltas.isVisible():
            self.cancelaDespachador()
        
        self.flMtto = False
        self.flOperador = False
        self.flDespachador = False
        self.TISC = ""

    def cancelMtto(self):
        self.flMtto = False
        self.lblInicioFin.setText('')
        self.lblInicioFin.hide()
        self.imgTarjeta.setPixmap(QtGui.QPixmap(''))
        self.imgTarjeta.hide()
        self.btnReset.hide()
        self.btnReinicio.hide()
        self.btnGPSOn.hide()
        self.btnGPSOff.hide()
        self.btnResetModem.hide()
        self.btnOK.hide()
        self.lblInicioFin.resize(363, 100)
        self.lblInicioFin.move(432, 85)
        self.btnResetHard3G.hide()
        self.btnResetUSB.hide()
        self.btnGpioGUI.hide()
     
    def ventanaOperador(self):
        if self.flOperador:
            self.flOperador = False          
            self.imgTarjeta.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/login.jpg'))
            self.imgTarjeta.show()
            if (self.csn == self.stCSNO):
                self.lblInicioFin.setStyleSheet('QLabel { font-size: 24pt; font-family: Arial; background-color:Gray; color:White}')
                self.lblInicioFin.resize(550, 40)
                self.lblInicioFin.move(230, 75)
                self.lblInicioFin.setText('Ventana de Operador')
                self.lblInicioFin.show()
                self.btnPolicia.show()      
                self.btnTransito.show()      
                self.btnAmbulancia.show()      
                self.btn911.show()      
                if (self.noVuelta == 0):
                    self.btnSalir.show()      
            else:
                if self.btnOK.isVisible():
                    self.cancelMtto()
                else:
                    self.btnOK.show()      
                    self.lblInicioFin.setStyleSheet('QLabel { font-size: 35pt; font-family: Arial; background-color:Red; color:White}')
                    self.lblInicioFin.resize(570, 100)
                    self.lblInicioFin.move(230, 100)
                    self.lblInicioFin.setText('Este Operador\nNO Inicio la Vuelta')
                    self.btnOK.move(500,350)
                    self.lblInicioFin.show()
                
    def registraOperador(self):
        self.idOperador = self.stId
        print ("UPDATE usuario SET csn = '"+self.stCSNO+"', idChofer = "+str(self.idOperador)+", password = '"+self.stNIP+"', nombre = '"+self.stNombreO+"', apellidoPa = '"+self.stApellidoO+"'")
        self.clDB.dbAforo.execute("UPDATE usuario SET csn = '"+self.stCSNO+"', idChofer = "+str(self.idOperador)+", password = '"+self.stNIP+"', nombre = '"+self.stNombreO+"', apellidoPa = '"+self.stApellidoO+"'")
        self.lblNombreOperador.setText(self.stNombreO+" "+self.stApellidoO)
        self.imgOperador.setPixmap(QtGui.QPixmap(self.stPathTISC))
        self.imgOperador.show()
        self.clDB.dbAforo.commit()  
        self.csn = self.stCSNO
        self.flOperador = False          
        msg = "7,"+str(self.clDB.idUnidad)+","+time.strftime("%Y-%m-%d %H:%M:%S")+","+str(self.stCSNO)+",1"
        self.clDB.envio(1,msg)  
        self.flSendEnvio = True            
        subprocess.call("xset dpms 0 0 0",shell=True)

    def cierraVentanaOperador(self):
        self.lblInicioFin.setText('')
        self.lblInicioFin.hide()
        self.imgTarjeta.setPixmap(QtGui.QPixmap(''))
        self.imgTarjeta.hide()
        self.btnPolicia.hide()
        self.btnTransito.hide()
        self.btnAmbulancia.hide()
        self.btn911.hide()
        self.btnSalir.hide()

    def cierreDeOperador(self):
        self.clDB.dbAforo.execute("UPDATE usuario SET csn = '', idChofer = '', password = '', nombre = '', apellidoPa = ''")
        self.lblNombreOperador.setText("")
        self.imgOperador.setPixmap(QtGui.QPixmap(''))
        self.imgOperador.hide()
        self.clDB.dbAforo.commit()
        msg = "7,"+str(self.clDB.idUnidad)+","+time.strftime("%Y-%m-%d %H:%M:%S")+","+str(self.stCSNO)+",0"
        self.clDB.envio(1,msg)
        self.flSendEnvio = True
        self.idOperador = 77
        self.stCSNO = ''
        self.flOperador = False
        self.cierraVentanaOperador()
        subprocess.call("xset dpms 0 300 0",shell=True)

    def cancelaDespachador(self):
        self.imgTarjeta.setPixmap(QtGui.QPixmap(''))
        self.imgTarjeta.hide()
        self.imgDefault.setPixmap(QtGui.QPixmap(''))
        self.imgDefault.move(0,0)
        self.imgDefault.resize(422,450)
        self.imgDefault.hide()
        self.lblInicioFin.setText("")       
        self.lblInicioFin.hide()
        self.lblTurnoT.hide()
        self.lblTurnoT.setText("")
        self.cbTurno.hide()
        self.lblRutaT.hide()
        self.cbRuta.hide()
        self.lblNVT.setText('')
        self.lblNVT.hide()
        self.spNV.hide()
        self.btnOK.hide()
        self.btnCancel.hide()
        self.btnCambiarRuta.hide()
        self.btnIniciarVuelta.hide()
        self.btnCerrarVuelta.hide()
        self.btnCerrarTurno.hide()
        self.lstVueltas.hide()
        self.lstVueltas.clear()
        self.chkVuelta.hide()
        self.lblVta.setText("")
        self.lblVta.hide()

    def Turno(self):
        self.imgTarjeta.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/login.jpg'))
        self.imgTarjeta.show()
        if (self.idOperador == 77):
            self.btnOK.move(482,400)
            self.btnOK.show()      
            self.lblInicioFin.setStyleSheet('QLabel { font-size: 35pt; font-family: Arial; background-color:Red; color:White}')
            self.lblInicioFin.resize(570, 100)
            self.lblInicioFin.move(220, 175)
            self.lblInicioFin.setText('Operador NO ha \nIniciado Recorrido')
            self.lblInicioFin.show()
            self.flIniciar = None          
        else:
            #self.btnOK.move(575,400)
            if (self.idRecorrido == 0):
                self.lblInicioFin.setStyleSheet('QLabel { font-size: 28pt; font-family: Arial; background-color:Green; color:White}')
                self.lblInicioFin.resize(363, 35)
                self.lblInicioFin.move(432, 75)
                self.lblInicioFin.setText('Recorridos')
                self.lblInicioFin.show()
                self.lblTurnoT.setText("Turno")
                self.lblTurnoT.show()
                self.cbTurno.show()
                self.lblRutaT.show()
                self.cbRuta.show()
                self.lblNVT.show()
                if (self.cbRuta.count() > 0):
                    if (self.noVuelta == 0):
                        self.spNV.show()
                        self.lblNVT.setText('Inicia\nVuelta')
                    else:
                        self.lblNVT.setText('Fin de\nVuelta')
                    self.btnOK.show()
                else:
                    self.cbRuta.hide()
                    self.lblInicioFin.setStyleSheet('QLabel { font-size: 18pt; font-family: Arial; background-color:Red; color:White}')
                    self.lblInicioFin.setText('No se han Capturado Rutas')
                    self.lblInicioFin.show()
                    self.btnOK.hide()
                self.btnCancel.show()
            else:
                c = self.clDB.dbAforo.cursor()
                self.imgTarjeta.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/login.jpg'))
                self.imgTarjeta.show()
                self.imgDefault.setPixmap(QtGui.QPixmap(self.stPathTISC))

                self.imgDefault.move(10,20)
                self.imgDefault.resize(310,405)

                self.imgDefault.show()
                self.lblPersonal.show()
                self.lblPersonal.setText(self.stNombre)
                self.lblInicioFin.setStyleSheet('QLabel { font-size: 20pt; font-family: Arial; background-color:Red; color:White}')
                #self.lblInicioFin.setText('Recorrido T. '+self.stTurno)
                if (self.clDB.idRuta is None):
                    self.clDB.idRuta = 0
                
                print ('SELECT numRuta, corto FROM ruta WHERE idTransportista = '+str(self.clDB.idTransportista)+ ' and idRuta = '+str(self.clDB.idRuta))
                c.execute('SELECT numRuta, corto FROM ruta WHERE idTransportista = '+str(self.clDB.idTransportista)+ ' and idRuta = '+str(self.clDB.idRuta))
                data = c.fetchone()
                if (data is None):
                    self.lblInicioFin.setText('')
                else:
                    #self.lblInicioFin.setText(str(self.clDB.idUnidad)+"R"+str(data[0])+" "+str(data[1].encode('latin-1')))
                    self.lblInicioFin.setText(str(self.clDB.idUnidad)+" "+str(data[1].encode('latin-1')))
                self.lblTurnoT.setStyleSheet('QLabel { font-size: 20pt; font-family: Arial; background-color:White; color:Red}')
                self.lblVta.show()
                self.flIniciar = False
                #print ('SELECT vuelta, termino FROM vuelta WHERE DATE(inicio) = "'+time.strftime("%Y-%m-%d")+'" ORDER BY inicio LIMIT 1')
                c.execute('SELECT vuelta, termino FROM vuelta WHERE DATE(inicio) = "'+time.strftime("%Y-%m-%d")+'" ORDER BY inicio DESC LIMIT 1')
                data = c.fetchone()
                inicio = True
                if (data is None):
                    data = (0, 0)
                elif (data[1] is None):
                    inicio = False
                if inicio:
                #if (self.lblVuelta.text() != ""):
                    self.btnIniciarVuelta.show()
                    self.btnCambiarRuta.show()
                    self.btnCerrarTurno.show()
                    self.btnCerrarVuelta.hide()
                    self.lblVta.move(495,427)
                    self.lblVta.setText(str(data[0]+1))
                else:
                    self.btnIniciarVuelta.hide()
                    self.btnCambiarRuta.hide()
                    self.btnCerrarTurno.hide()
                    self.btnCerrarVuelta.show()
                    self.lblVta.move(620,427)
                    self.lblVta.setText(str(data[0]))
                self.btnCancel.show()
                l = 1
                #c.execute('SELECT DISTINCT tarifa, 0 FROM validador ORDER BY tarifa')
                #print ('SELECT DISTINCT tarifa, 0 FROM validador WHERE DATE(fechaHora) = "' +time.strftime("%Y-%m-%d")+ '" ORDER BY tarifa')
                c.execute('SELECT DISTINCT tarifa, 0 FROM validador WHERE DATE(fechaHora) = "' +time.strftime("%Y-%m-%d")+ '" ORDER BY tarifa')
                data = c.fetchone()
                if not (data is None):
                    tarifas = {}
                    i = 0
                    st = 'Vuelta'
                    while not (data is None):
                        tarifas[i] = list(data)
                        stT = "{:.2f}".format(float(tarifas[i][0])/100)
                        st = st + '\t'+'$ '+ stT 
                        i += 1
                        data = c.fetchone()
                    maxT = i - 1
                    st = st + "\tTOTAL"
                    self.wLstVueltas = 160 + (i*80)
                    self.xLstVueltas = 320 + ((480 - self.wLstVueltas) / 2)
                    self.lblInicioFin.resize(480, 35)
                    self.lblInicioFin.move(320, 75)
                    self.lstVueltas.resize(self.wLstVueltas,290)
                    self.lstVueltas.move(self.xLstVueltas,110)

                    #print("SELECT termino FROM recorrido WHERE date(inicio) = '" +time.strftime("%Y-%m-%d")+ "' ORDER BY inicio DESC LIMIT 1")
                    c.execute("SELECT termino FROM recorrido WHERE date(inicio) = '" +time.strftime("%Y-%m-%d")+ "' ORDER BY inicio DESC LIMIT 1")
                    d = c.fetchone()
                    if (d is None):
                        stInicio = time.strftime("%Y-%m-%d") + " 00:00:00"
                    else:
                        if (d[0] is None):
                            stInicio = time.strftime("%Y-%m-%d") + " 00:00:00"
                        else:
                            stInicio = str(d[0])
                        
                    #print (" SELECT 0 AS recorrido, ' ' AS vuelta, tarifa, count(*),'Fuera de Vuelta' AS nombre FROM validador WHERE vuelta = 0 AND fechaHora >= '" +stInicio+ "' GROUP BY vuelta, tarifa UNION SELECT recorrido, vuelta, tarifa, count(*), 'R'|| numRuta || ' - ' || Corto  FROM validador, ruta WHERE idTransportista = "+str(self.clDB.idTransportista)+" AND validador.idRuta = ruta.idRuta AND recorrido = "+str(self.idRecorrido)+" and vuelta > 0 AND fechaHora >= '" +stInicio+ "' GROUP BY recorrido, validador.idRuta, vuelta, tarifa ORDER BY recorrido, nombre, vuelta, tarifa;")
                    c.execute(" SELECT 0 AS recorrido, ' ' AS vuelta, tarifa, count(*),'Fuera de Vuelta' AS nombre FROM validador WHERE vuelta = 0 AND fechaHora >= '" +stInicio+ "' GROUP BY vuelta, tarifa UNION SELECT recorrido, vuelta, tarifa, count(*), 'R'|| numRuta || ' - ' || Corto  FROM validador, ruta WHERE idTransportista = "+str(self.clDB.idTransportista)+" AND validador.idRuta = ruta.idRuta AND recorrido = "+str(self.idRecorrido)+" and vuelta > 0 AND fechaHora >= '" +stInicio+ "' GROUP BY recorrido, validador.idRuta, vuelta, tarifa ORDER BY recorrido, nombre, vuelta, tarifa;")
                    detalle = c.fetchone()
                    vAnt = -1
                    totalVuelta = 0
                    rAnt =  ''
                    while not (detalle is None):
                        if ((vAnt != detalle[1]) or (rAnt != detalle[4])):
                            if (vAnt != -1):
                                while (i < maxT):
                                    st = st + '\t'
                                    i += 1
                                st = st + '\t'+str(totalVuelta).rjust(7,' ')
                            st = st #+ '\n'
                            self.lstVueltas.addItem(st)
                            st = ""
                            if (rAnt != detalle[4]):
                                st = st + detalle[4] #+ '\n'
                                self.lstVueltas.addItem(st)
                                st = ""                    
                                rAnt = detalle[4]
                            st = st + str(detalle[1]).rjust(6,' ') + '\t'
                            i = 0
                            totalVuelta = 0
                            l += 1
                            vAnt = detalle[1]
                        #print tarifas
                        #print detalle
                        #print "(" + str(tarifas[i][0]) + " !=  " + str(detalle[2]) + " or " + str(vAnt) + " != " + str(detalle[1]) + " or " + str(rAnt) + " != " + str(detalle[4])
                        while (tarifas[i][0] != detalle[2] or vAnt != detalle[1] or rAnt != detalle[4]):
                            i += 1
                            st = st + '\t'
                            #print "(" + tarifas[i][0] + " !=  " + detalle[2] + " or " + vAnt + " != " + detalle[1] + " or " + rAnt + " != " + detalle[4]
                        if (tarifas[i][0] == detalle[2]):
                            st = st + str(detalle[3]).rjust(8, ' ')
                            tarifas[i][1] = tarifas[i][1] + detalle[3]
                            totalVuelta = totalVuelta + detalle[3]
                        detalle = c.fetchone()
                    if (totalVuelta > 0):
                        while (i < maxT):
                            st = st + '\t'
                            i += 1
                        st = st + '\t'+str(totalVuelta).rjust(7,' ')
                    self.lstVueltas.addItem(st)
                self.lstVueltas.show()
                c.close()
            self.lblInicioFin.show()
            #self.ShowInicioFin(True)
            
    def ShowInicioFin(self,show):
        if (show):
            self.imgTarjeta.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/login.jpg'))
            self.imgTarjeta.show()
            self.imgDefault.setPixmap(QtGui.QPixmap(self.stPathTISC))
            self.imgDefault.move(10,20)
            self.imgDefault.resize(310,405)
            self.imgDefault.show()
            self.lblPersonal.show()
            if (self.flTurno and self.chkVuelta.isVisible() and self.chkVuelta.checkState() == QtCore.Qt.Unchecked): 
                self.btnOK.hide()
            else:
                self.btnOK.show()
            self.btnCancel.show()
            self.lblPersonal.setText(self.stNombre)
#            if (self.flTurno):
#                self.lblTurno.setText("T U R N O")
#                self.lblTurno.show()
            if (self.flVuelta):
                #self.lblTurnoT.move(432, 220)
                #self.lblTurnoT.resize(376,80)
                self.lblInicioFin.resize(363,100)
                if (self.cbRuta.count() > 0):
                #if self.cbRuta.isVisible(): 
                    if self.flIniciar:
                        self.cbRuta.show()
                        self.spNV.show()
                        #self.lblTurnoT.setStyleSheet('QLabel { font-size: 64pt; font-family: Arial; color:Green}')
                        self.lblInicioFin.setStyleSheet('QLabel { font-size: 35pt; font-family: Arial; background-color:Green; color:White}')
                        self.lblInicioFin.setText('Inicio de\nVuelta')
                        self.cbRuta.show()
                    else:
                        #self.lblNV.show()
                        self.lblTurnoT.setStyleSheet('QLabel { font-size: 64pt; font-family: Arial; color:Red}')
                        self.lblInicioFin.setStyleSheet('QLabel { font-size: 35pt; font-family: Arial; background-color:Red; color:White}')
                        self.lblInicioFin.setText('Fin de\nVuelta')
                        self.lblTurnoT.setText(str(self.noVuelta))
                        self.lblTurnoT.show()
                    self.lblInicioFin.show()
                else:
                    self.cbRuta.hide()
                    self.lblInicioFin.setStyleSheet('QLabel { font-size: 18pt; font-family: Arial; background-color:Red; color:White}')
                    self.lblInicioFin.setText('No se han Capturado Rutas')
                    self.lblInicioFin.show()
                    self.btnOK.hide()
        else:
            self.imgTarjeta.setPixmap(QtGui.QPixmap(''))
            self.imgDefault.setPixmap(QtGui.QPixmap(''))
            self.imgDefault.move(0,0)
            self.imgDefault.resize(422,450)
            self.imgTarjeta.hide()
            self.lblPersonal.hide()
            self.lblInicioFin.hide()
            self.lblTurno.hide()
            self.lblTurnoT.hide()
            self.lblNV.hide()
            self.spNV.hide()
            self.lstVueltas.hide()

            self.cbTurno.hide()
            self.btnOK.hide()
            self.btnCancel.hide()
            self.chkVuelta.hide()
            self.cbRuta.hide()

            self.lblPersonal.setText("")
            self.lblInicioFin.setText("")
            self.lblTurno.setText("")
            #self.lblTurnoT.setText("")
            self.lblNV.setText("")
            self.lstVueltas.clear()
            #self.lstVueltas.setText("")
            
            #self.lblTurnoT.setStyleSheet('QLabel { font-size: 18pt; font-family: Arial; color:Black}')
            #self.lblTurnoT.resize(376,30)
            #self.lblTurnoT.move(432,280)
            
    def click_btnOK(self, event):
        if (self.btnResetHard3G.isVisible()):
            self.cancelMtto()

## Turno
        if (self.spNV.isVisible()):
            c = self.clDB.dbAforo.cursor()
            stFecha = time.strftime("%Y-%m-%d %H:%M:%S")
            if (int(self.spNV.value()) > 0):
                if (self.cbTurno.isVisible()):
                    self.idTurno = self.cbTurno.itemData(self.cbTurno.currentIndex()).toString()
                    self.stTurno = self.cbTurno.currentText()
                    c.execute("INSERT INTO recorrido (inicio, csnInicio, idTurno, enviadoInicio) VALUES (?,?,?,0)",(stFecha, self.csn, str(self.idTurno)))
                    self.clDB.dbAforo.commit()
                    self.flSendInicioRecorrido = True
                    c.execute('SELECT MAX(idRecorrido) FROM recorrido')
                    data = c.fetchone()
                    self.idRecorrido = data[0]
                if (self.cbRuta.itemData(self.cbRuta.currentIndex()) is None):
                    self.clDB.idRuta = 0
                else:
                    self.clDB.idRuta = self.cbRuta.itemData(self.cbRuta.currentIndex()).toString()
                c.execute("UPDATE parametros SET idRutaActual = '"+str(self.clDB.idRuta)+"'")
                self.clDB.dbAforo.commit()  
                self.lblRuta.setText(self.cbRuta.currentText())
                c.execute("SELECT numRuta FROM ruta WHERE idRuta = "+str(self.clDB.idRuta))
                data = c.fetchone()           
                self.lblNoRuta.setText(str(data[0]))
                self.noVuelta = int(self.spNV.value())
                st = self.stOperador.decode('latin-1')
                print("INSERT INTO vuelta (idRecorrido, idRuta, vuelta, inicio, csnInicio, operador, enviadoInicio, idVuelta, tipo) VALUES (?,?,?,?,?,?,0,0,1)",(str(self.idRecorrido), str(self.clDB.idRuta), str(self.noVuelta), stFecha, str(self.csn), st))
                c.execute("INSERT INTO vuelta (idRecorrido, idRuta, vuelta, inicio, csnInicio, operador, enviadoInicio, idVuelta, tipo) VALUES (?,?,?,?,?,?,0,0,1)",(str(self.idRecorrido), str(self.clDB.idRuta), str(self.noVuelta), stFecha, str(self.csn), st))
                self.clDB.dbAforo.commit()  
                self.lblVuelta.setText(str(self.noVuelta))
                c = self.clDB.dbFlota.cursor()
                print('DELETE FROM asignacion')
                c.execute('DELETE FROM asignacion')
                print('INSERT INTO asignacion (idTransportista, idRuta, idPuntoInteres, total) VALUES (' + str(self.clDB.idTransportista) + ',' + str(self.clDB.idRuta) + ',1,' +  '(SELECT COUNT(*) FROM vPuntoControl WHERE idRuta = ' + str(self.clDB.idRuta) + '))' )
                c.execute('INSERT INTO asignacion (idTransportista, idRuta, idPuntoInteres, total) VALUES (' + str(self.clDB.idTransportista) + ',' + str(self.clDB.idRuta) + ',1,' +  '(SELECT COUNT(*) FROM vPuntoControl WHERE idRuta = ' + str(self.clDB.idRuta) + '))' )
                self.clDB.dbFlota.commit()
                self.flSendInicioVuelta = True
            self.cancelaDespachador()
                
            '''
            if (self.chkVuelta.isVisible()):
                self.flIniciar = False
                self.CierraVuelta()
                self.flVuelta = False
                self.flTurno = False
            else:
                if (self.flIniciar):
                    self.flSendInicioRecorrido = True
                    c.execute("INSERT INTO recorrido (inicio, csnInicio, idTurno, enviadoInicio) VALUES (?,?,?,0)",(stFecha, self.csn, str(self.idTurno)))
                    conn.commit()
                    c.execute('SELECT MAX(idRecorrido) FROM recorrido')
                    data = c.fetchone()
                    self.idRecorrido = data[0]
                else:
                    self.flSendTerminoRecorrido = True
                    c.execute("UPDATE recorrido SET termino = ?, csnTermino = ?, enviadoTermino = 0 WHERE idRecorrido = ?",(stFecha, self.csn, self.idRecorrido))
                    conn.commit()
                    c.execute("DELETE FROM validador WHERE enviado = 1")
                    conn.commit()
                    self.idRecorrido = 0
                    self.noVuelta = 0
                self.idOperador = self.stId
                self.csn = self.stCSN
                c.execute("UPDATE usuario SET csn = '"+self.csn+"', idChofer = "+str(self.idOperador))
                conn.commit()
                self.flTurno = False
            '''

### Vuelta
            
#        if (self.flVuelta):
#            if self.flIniciar is None:
#                self.lblInicioFin.resize(363, 100)
#                self.lblInicioFin.move(432, 85)
#                #self.btnOK.move(575,435)
#            else:
#                self.CierraVuelta()
#            self.flVuelta = False
        self.ShowInicioFin(False)

    def CierraVuelta(self):
        c = self.clDB.dbAforo.cursor()
        stFecha = time.strftime("%Y-%m-%d %H:%M:%S")     
        self.idOperador = self.stId
        self.csn = self.stCSN
        if (self.flIniciar):
            self.clDB.idRuta = self.cbRuta.itemData(self.cbRuta.currentIndex()).toString()
            if (self.cbRuta.itemData(self.cbRuta.currentIndex()) is None):
                self.clDB.idRuta = 0
            else:
                self.clDB.idRuta = self.cbRuta.itemData(self.cbRuta.currentIndex()).toString()
            self.flSendInicioVuelta = True
            self.noVuelta = int(self.spNV.value())
            st = self.stOperador.decode('latin-1')
            c.execute("INSERT INTO vuelta (idRecorrido, idRuta, vuelta, inicio, csnInicio, operador, enviadoInicio, idVuelta, tipo) VALUES (?,?,?,?,?,?,0,0,1)",(str(self.idRecorrido), str(self.clDB.idRuta), str(self.noVuelta), stFecha, str(self.csn), st))
            self.clDB.dbAforo.commit()  
            self.flIdRutaAutomatica = False
            c.execute("UPDATE parametros SET idRutaActual = '"+str(self.clDB.idRuta)+"'")
            self.clDB.dbAforo.commit()  
            self.lblVuelta.setText(str(self.noVuelta))
            self.lblNombreOperador.setText(self.stOperador)
            self.imgOperador.setPixmap(QtGui.QPixmap(self.stPathTISC))
            self.lblRuta.setText(self.cbRuta.currentText())
            c.execute("SELECT numRuta FROM ruta WHERE idRuta = "+str(self.clDB.idRuta))
            data = c.fetchone()           
            self.lblNoRuta.setText(str(data[0]))
        else:
            self.flSendTerminoVuelta = True
            c.execute("UPDATE vuelta SET termino = ?, csnTermino = ?, enviadoTermino = 0 WHERE idRecorrido = ? AND vuelta = ?",(stFecha, self.csn, self.idRecorrido, str(self.noVuelta)))
            self.clDB.dbAforo.commit()      
            c.execute("UPDATE parametros SET idRutaActual = NULL")
            self.clDB.dbAforo.commit()  
            self.lblVuelta.setText("")
            self.lblNombreOperador.setText("")
            self.imgOperador.setPixmap(QtGui.QPixmap(''))
            self.lblNoRuta.setText("")
            self.lblRuta.setText("")
            self.clDB.idRuta = 0
            self.noVuelta = 0
            self.flIdRutaAutomatica = True
        c.execute("UPDATE usuario SET csn = '"+self.csn+"', idChofer = "+str(self.idOperador)+", password = '"+self.stNIP+"'")
        self.clDB.dbAforo.commit()  

    def cancelTurnoVuelta (self):
        if (self.flTurno):
            self.lblInicioFin.setText("")       
            self.lstVueltas.clear()
            self.lblInicioFin.hide()
            self.cbTurno.hide()
            self.lblTurnoT.hide()
            self.lstVueltas.hide()

        if (self.flVuelta):
            self.lblInicioFin.setText("")       
            self.lblTurnoT.hide()
            self.lblInicioFin.hide()
            self.lblInicioFin.resize(363, 100)
            self.lblInicioFin.move(432, 85)
            #self.lblTurnoT.resize(376,30)
            #self.lblTurnoT.move(432,280)
            self.spNV.hide()
            
        self.ShowInicioFin(False)
        self.flMtto = False
        self.flTurno = False
        self.flVuelta = False
        self.TISC = ""
    
    def crear_tramas9(self):
        try:
            try:
                fecha_actual = datetime.date.today()
                hora_actual = datetime.datetime.now().time()
                
                version_raspberry = ""
                
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().strip()
                    if 'Raspberry Pi' in model:
                        version_raspberry = model.split('Raspberry Pi')[1].strip()

                # Leer el archivo /proc/meminfo para obtener información sobre la memoria RAM
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()

                # Extraer la cantidad de memoria RAM total y usada
                total_ram = int(meminfo.split('MemTotal:')[1].split('kB')[0].strip()) * 1024
                usada_ram = int(meminfo.split('MemAvailable:')[1].split('kB')[0].strip()) * 1024

                # Ejecutar el comando 'df -h' y capturar la salida
                df_output = subprocess.check_output(['df', '-h'])

                # Convertir la salida a una lista de líneas de texto
                df_lines = df_output.decode('utf-8').split('\n')

                # Buscar la línea que contiene la información del sistema de archivos /
                root_fs_line = None
                for line in df_lines:
                    if line.startswith('/dev/root'):
                        root_fs_line = line
                        break

                # Obtener los campos de espacio total y usado de la línea del sistema de archivos /
                if root_fs_line is not None:
                    root_fs_fields = root_fs_line.split()
                    total_rom = root_fs_fields[1]
                    usada_rom = root_fs_fields[2]
                else:
                    total_rom = 'Unknown'
                    usada_rom = 'Unknown'

                # Convertir bytes a megabytes
                total_ram_mb = total_ram / (1024 * 1024)
                usada_ram_mb = usada_ram / (1024 * 1024)
                
            except Exception, e:
                print e
            
            RAM = str(usada_ram_mb)[:6] + "/" + str(total_ram_mb)[:6]+"MB"
            ROM = str(usada_rom) + "/" + str(total_rom)

            process = subprocess.Popen("cat /sys/class/net/eth0/address", stdout=subprocess.PIPE, shell=True)
            stdout, _ = process.communicate()
            mac = stdout.decode().strip()  # Convierte la salida de bytes a una cadena
            
            parametros = obtener_parametros()
            
            puertoSocket = str(parametros[0][2])
            if puertoSocket is None:
                puertoSocket = self.clDB.puertoSocket
            else:
                puertoSocket = self.clDB.puertoSocket + "/" + str(puertoSocket)
            
            insertar_estadisticas_alttus(str(self.clDB.economico), self.clDB.idTransportista, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), "SW", str(self.stVersion)) # Version del software
            insertar_estadisticas_alttus(str(self.clDB.economico), self.clDB.idTransportista, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), "MAC", str(mac)) # MAC de raspberry
            insertar_estadisticas_alttus(str(self.clDB.economico), self.clDB.idTransportista, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), "SKT", str(puertoSocket)) # Socket
            insertar_estadisticas_alttus(str(self.clDB.economico), self.clDB.idTransportista, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), "VRPI", str(version_raspberry)) # Version raspberry
            insertar_estadisticas_alttus(str(self.clDB.economico), self.clDB.idTransportista, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), "RAM", str(RAM)) # RAM raspberry
            insertar_estadisticas_alttus(str(self.clDB.economico), self.clDB.idTransportista, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), "ROM", str(ROM)) # ROM raspberry
            insertar_estadisticas_alttus(str(self.clDB.economico), self.clDB.idTransportista, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), "APN", str(self.clDB.urlAPN)) # APN SIM
            print "Tramas 9 creadas."
        except Exception, e:
            print "Fallo la creacion de las tramas 9 en innobus.py: " + str(e)
            
    def eliminarDatosAntiguos(self):
        print "\n"
        print "################################################"
        print "Se procedera a revisar las bases de datos"
        try:
            fecha_ahora = datetime.datetime.utcnow()
            print "Hoy es "+str(fecha_ahora)
            fecha_antigua = fecha_ahora - datetime.timedelta(days=15)
            print "Hace 15 días fue "+str(fecha_antigua)
            fecha_limite = fecha_antigua.strftime('%Y-%m-%d')
            print "La fecha hace 15 días es "+str(fecha_limite)
            
            eliminado_estadisticas_db = False
            eliminado_ventas_db = False
            
            try:
                
                eliminado_ventas_db = eliminar_aforos_antiguos(fecha_limite)
                if eliminado_ventas_db:
                    print "Aforos verificados, se eliminaron registros antiguos"
                else:
                    print "No se eliminaron registros de aforos"
            except Exception, e:
                print "Error al verificar los tickets: "+str(e)
                    
            time.sleep(0.10)
            
            try:
                
                eliminado_estadisticas_db = eliminar_estadisticas_antiguas(fecha_limite)
                if eliminado_estadisticas_db:
                    print "Estadisticas verificadas, se eliminaron registros antiguos"
                else:
                    print "No se eliminaron registros de estadisticas"
            except Exception, e:
                print "Error al verificar las estadisticas: "+str(e)
                    
            time.sleep(0.10)
            
            print "Se terminó de verificar las bases de datos"
            print "################################################"
            print "\n"
        except Exception, e:
                print "Ocurrió un error al verificar las bases de datos: ", e
                time.sleep(0.10)
                print "################################################"
                
    def escogerSocket(self):
        try:
            print "Se procedera a escoger el socket"
            
            if self.clDB.idTransportista is not None:
                if self.clDB.idTransportista == 0:
                    actualizar_socket("8100")
                elif self.clDB.idTransportista == 1:
                    actualizar_socket("8101")
                elif self.clDB.idTransportista == 2:
                    actualizar_socket("8102")
                elif self.clDB.idTransportista == 3:
                    actualizar_socket("8103")
                elif self.clDB.idTransportista == 4:
                    actualizar_socket("8104")
                elif self.clDB.idTransportista == 5:
                    actualizar_socket("8105")
                elif self.clDB.idTransportista == 6:
                    actualizar_socket("8106")
                elif self.clDB.idTransportista == 7:
                    actualizar_socket("8107")
                elif self.clDB.idTransportista == 8:
                    actualizar_socket("8108")
                elif self.clDB.idTransportista == 9:
                    actualizar_socket("8109")
                elif self.clDB.idTransportista == 10:
                    actualizar_socket("8110")
                else:
                    actualizar_socket("8141")
            else:
                actualizar_socket("8141")
                
            parametros = obtener_parametros()
            
            print "El socket escogido es: "+str(parametros[0][2])
            print "################################################"
            print "\n"
        except Exception, e:
            print "Ocurrió un error al escoger el socket: ", e
            time.sleep(0.10)
            print "################################################"

    def Operador(self):
        if self.imgOperador.isVisible():
            if (self.csn == self.stCSNO):
                self.clDB.dbAforo.execute("UPDATE usuario SET csn = '', idChofer = '', password = '', nombre = '', apellidoPa = ''")
                self.lblNombreOperador.setText("")
                self.imgOperador.setPixmap(QtGui.QPixmap(''))
                self.imgOperador.hide()
                self.clDB.dbAforo.commit()
                msg = "7,"+str(self.clDB.idUnidad)+","+time.strftime("%Y-%m-%d %H:%M:%S")+","+str(self.stCSNO)+",0"
                self.clDB.envio(1,msg)  
                self.flSendEnvio = True
                self.stCSNO = ''
                self.flOperador = False          
            elif not self.imgTarjeta.isVisible():
                self.imgTarjeta.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/login.jpg'))
                self.imgTarjeta.show()
                self.btnOK.show()      
                self.lblInicioFin.setStyleSheet('QLabel { font-size: 35pt; font-family: Arial; background-color:Red; color:White}')
                self.lblInicioFin.resize(570, 100)
                self.lblInicioFin.move(230, 100)
                self.lblInicioFin.setText('Este Operador\nNO inicio la Vuelta')
                self.btnOK.move(500,350)
                self.lblInicioFin.show()
        else:
            self.registraOperador()

    def Vuelta(self):
        self.btnOK.move(575,400)
        c = self.clDB.dbAforo.cursor()
        print "Recorrido", self.idRecorrido
        if (self.idRecorrido == 0):
            print "No se ha iniciado Turno"
            self.imgTarjeta.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/login.jpg'))
            self.imgTarjeta.show()
            self.btnOK.show()      
            self.lblInicioFin.setStyleSheet('QLabel { font-size: 35pt; font-family: Arial; background-color:Red; color:White}')
            self.lblInicioFin.resize(570, 50)
            self.lblInicioFin.move(230, 100)
            self.lblInicioFin.setText('No se ha Iniciado Turno')
            self.lblInicioFin.show()
            self.flIniciar = None
        else:
            c.execute("SELECT csnInicio FROM vuelta WHERE idRecorrido = "+str(self.idRecorrido)+" AND idRuta = "+str(self.clDB.idRuta)+" AND vuelta = "+str(self.noVuelta))
            data = c.fetchone()
            if data is None:
                self.flIniciar = True
            else:
                self.flIniciar = False
                if (data[0] != self.stCSN):
                    self.imgTarjeta.setPixmap(QtGui.QPixmap('/home/pi/innobusmx/data/img/login.jpg'))
                    self.imgTarjeta.show()
                    self.btnOK.show()      
                    self.lblInicioFin.setStyleSheet('QLabel { font-size: 35pt; font-family: Arial; background-color:Red; color:White}')
                    self.lblInicioFin.resize(570, 100)
                    self.lblInicioFin.move(230, 100)
                    self.lblInicioFin.setText('Este Operador\nNO inicio el Recorrido')
                    self.lblInicioFin.show()
                    self.flIniciar = None                    
            if not (self.flIniciar is None):
                self.click_cbRuta()
                self.ShowInicioFin(True)
            
        c.close

    def click_chkVuelta(self,state):
        if (state == QtCore.Qt.Checked):
            self.lblInicioFin.setText('Cierre de Vuelta '+str(self.noVuelta))
            self.lstVueltas.move(self.wLstVueltas, 110)
            self.lstVueltas.resize(self.xLstVueltas, 290)
            self.lblTurnoT.hide()
            self.btnOK.show()
        else:
            self.lblInicioFin.setText('Cierre de Turno')
            self.lstVueltas.move(self.wLstVueltas, 140)
            self.lstVueltas.resize(self.xLstVueltas, 260)
            self.lblTurnoT.show()
            self.btnOK.hide()


class Screen():
    
    def __init__(self, parent, clmodem, clmifare):
        self.parent = parent
        self.flG = False
        self.red = False
        self.ftp = False
        self.flR = True
        ########## ERNESTO LOMAR ##########
        self.fAl = False
        ###################################
        self.rfid = not self.parent.flRFID
        self.clmodem = clmodem
        self.clmifare = clmifare
        self.icomm = -999
        self.sim = False
        self.tisc = ""
        self.socket = False
        self.show()

    def show(self):
        if (self.parent.flQuectel):
            if (self.icomm != self.parent.iComm):
                if (self.parent.iComm == 0 or self.parent.iComm == 99):
                    self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/no3G.Jpeg"))
                elif (self.parent.iComm == 1):
                    self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/no3G0.png"))
                elif (self.parent.iComm >= 2 and self.parent.iComm <= 4):
                    self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G0.png"))
                elif (self.parent.iComm >= 5 and self.parent.iComm <= 10):
                    self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G25.png"))
                elif (self.parent.iComm >= 11 and self.parent.iComm <= 20):
                    self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G50.png"))
                elif (self.parent.iComm >= 21 and self.parent.iComm <= 30):
                    self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G75.png"))
                elif (self.parent.iComm >= 31 and self.parent.iComm <= 98):
                    self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/3G.png"))
                self.icomm = self.parent.iComm
        else:
            self.parent.no3G.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noUSB.jpg"))
        
        """
        ########## ERNESTO LOMAR ##########
        if (self.parent.flAlttus):
            self.parent.noAlttus.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/alttusti.png"))
        else:
            if (self.fAl):
                self.parent.noAlttus.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/alttusti.png"))
                self.fAl = False
            else:
                self.parent.noAlttus.setPixmap(QtGui.QPixmap(""))
                self.fAl = True
        ###################################   """

        if (self.parent.flRFID != self.rfid):
            if (not self.parent.flRFID):
                self.parent.noRDIF.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRFID.Jpeg"))
            else:
                self.parent.noRDIF.setPixmap(QtGui.QPixmap(''))
            self.rfid = self.parent.flRFID

        if (self.parent.flSocket != self.socket):
            if (not self.parent.flSocket):
                self.parent.noSocket.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noSocket.png"))
            else:
                self.parent.noSocket.setPixmap(QtGui.QPixmap(''))
            self.socket = self.parent.flSocket

        if (self.parent.flRed != self.red):
            if (not self.parent.flRed):
                self.parent.noRed.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noRed.Jpeg"))
            else:
                self.parent.noRed.setPixmap(QtGui.QPixmap(''))
            self.red = self.parent.flRed

        if (self.parent.TISC != self.tisc):
            if (self.parent.TISC != ""):
                self.parent.lblNombre.show()
                self.parent.lblApellido.show()
                self.parent.imgDefault.setPixmap(QtGui.QPixmap(self.parent.TISC))
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(self.parent.stImgTarjeta))
                self.parent.imgDefault.move(0,0)
                self.parent.imgDefault.resize(422,450)
                self.parent.imgDefault.show()
                self.parent.imgTarjeta.show()
                self.parent.lblNombre.setText(self.parent.stNombre)
                self.parent.lblApellido.setText(self.parent.stApellido)
                self.parent.lblSaldo.setText(self.parent.stSaldo)               
                self.parent.lblSaldoInsuficiente.setText(self.parent.stSaldoInsuficiente)
                self.parent.lblMsg.setText(self.parent.stMsg)
                self.parent.lblMsgVigencia.setText(self.parent.stMsgVigencia)
            else:
                self.parent.imgDefault.setPixmap(QtGui.QPixmap(''))
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(''))
                self.parent.imgTarjeta.hide()
                self.parent.lblNombre.hide()
                self.parent.lblApellido.hide()
                
                self.parent.lblNombre.setText("")
                self.parent.lblApellido.setText("")
                self.parent.lblSaldo.setText("")
                self.parent.lblSaldoInsuficiente.setText("")
                self.parent.lblMsg.setText("")
                self.parent.lblMsgVigencia.setText("")
            self.tisc = self.parent.TISC

        if (self.parent.flSIM != self.sim):
            if (not self.parent.flSIM):
                self.parent.noSIM.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noSIM.png"))
            else:
                self.parent.noSIM.setPixmap(QtGui.QPixmap(''))
            self.sim = self.parent.flSIM

        if (not self.parent.flGPSOK):
            self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPSEncendido.png"))
        else:
            if (self.flG):
                if (self.parent.flGPS):
                    self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/GPS.png"))
                else:
                    self.parent.noGPS.setPixmap(QtGui.QPixmap("/home/pi/innobusmx/data/img/noGPS.png"))
                self.flG = False
            else:
                self.parent.noGPS.setPixmap(QtGui.QPixmap(''))
                self.flG = True

        if (self.parent.closeTV):
            self.parent.cancelTurnoVuelta()
            self.parent.closeTV = False
        if self.parent.flMtto:
            if self.parent.btnReset.isVisible():
                self.parent.cancelMtto()
            else:
                self.parent.Mantenimiento()
            self.parent.flMtto = False
        
        if self.parent.flDespachador:
            if self.parent.spNV.isVisible() or self.parent.lstVueltas.isVisible():
                self.parent.cancelaDespachador()
            else:
                if (self.parent.idOperador == 77 and self.parent.imgTarjeta.isVisible()):
                    self.parent.ShowInicioFin(False)
                else:
                    self.parent.Turno()
            self.parent.flDespachador = False

        if self.parent.flOperador:
            if self.parent.imgOperador.isVisible():
                self.parent.cierreDeOperador()
            else:
                self.parent.registraOperador()
            self.parent.flOperador = False

        '''
        Ventana C5
        if self.parent.flOperador:
            if self.parent.imgOperador.isVisible() and not self.parent.btn911.isVisible():
                print "VentanaDeOperador"
                self.parent.ventanaOperador()
            elif self.parent.btn911.isVisible():
                if self.parent.btnSalir.isVisible():
                    print "cierreDeOperador"
                    self.parent.cierreDeOperador()
                else:
                    print "cierraVentanaDeOperador"
                    self.parent.cierraVentanaOperador()
            else:
                print "registraOperador"
                self.parent.registraOperador()
            self.parent.flOperador = False
        '''

        '''
        if self.parent.flOperador:
            #if self.parent.btnSalir.isVisible():
            if (self.parent.noVuelta == 0) and (self.parent.idRecorrido == 0):
                print "cierreDeOperador"
                self.parent.cierreDeOperador()
            else:
                if self.parent.btn911.isVisible():
                    print "cierraVentanaDeOperador"
                    self.parent.cierraVentanaOperador()
                elif self.parent.imgOperador.isVisible():
                    print "VentanaDeOperador"
                    self.parent.ventanaOperador()
                else:
                    print "registraOperador"
                    self.parent.registraOperador()
            print "OPERADORS"
            self.parent.flOperador = False
        '''


        if (self.parent.flEventoExitoso == 1 or self.parent.flEventoExitoso == -1):
            self.parent.ventanaEvento(True)
        if (self.parent.flEventoExitoso == 2): 
            self.parent.ventanaEvento(False)
        if (self.parent.mttoGPS == 1):
            self.clmodem.gpsOn()
            self.parent.mttoGPS = 0
            self.parent.btnGPSOn.show()
            self.parent.btnGPSOff.hide()
        if (self.parent.mttoGPS == 2):
            self.clmodem.gpsOff()
            self.parent.mttoGPS = 0
            self.parent.btnGPSOn.hide()
            self.parent.btnGPSOff.show()
        if (self.parent.mttoGPS == 3):
            self.clmodem.reset()
            self.parent.mttoGPS = 0
            self.parent.btnResetModem.show()
        if (self.parent.mttoGPS == 4):
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(24,GPIO.OUT)
            GPIO.output(24,False)
            time.sleep(2)
            GPIO.output(24,True)
            self.parent.btnResetUSB.show()
            self.parent.mttoGPS = 0
        if (self.parent.mttoGPS == 5):
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(8,GPIO.OUT)
            GPIO.output(8,False)
            time.sleep(2)
            GPIO.output(8,True)
            self.parent.btnResetHard3G.show()
            self.parent.mttoGPS = 0

        now = int(time.time())
        if (now - int(self.parent.lastConnection) > 600):
            self.parent.settings.setValue("apagado_forzado",1)
            python = sys.executable
            os.execl(python, python, * sys.argv)
        QtCore.QTimer.singleShot(1000, self.show)

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(13,GPIO.OUT)
    GPIO.setup(8,GPIO.OUT)
    GPIO.setup(24,GPIO.OUT)
    GPIO.output(13,GPIO.LOW)
    GPIO.output(8,GPIO.HIGH)
    GPIO.output(24,GPIO.HIGH)
    GPIO.setup(12,GPIO.IN)
    
    time.sleep(3)    
    app = QtGui.QApplication(sys.argv)

    cldb = sqLite()
    ex = mainWin(cldb)
    
    ##################### ERNESTO LOMAR #####################
    
    try:
        if not bool(int(ex.settings.value('apagado_forzado').toPyObject())):
            
            """
            # Creacion de tramas 9
            try:
                ex.crear_tramas9()
            except Exception, e:
                print "Fallo la creacion de las tramas 9 en main: " + str(e)"""
            
            # Verificacion de hora actual en BD
            try:
                # Primero colocamos todas las horas como no hechas
                hecho_horas = actualizar_estado_hora_por_defecto()
                    
                intentos_cambiar = 0
                
                if not hecho_horas:
                    while not hecho_horas or intentos_cambiar <= 5:
                        hecho_horas = actualizar_estado_hora_por_defecto()
                        intentos_cambiar += 1
                    if hecho_horas:
                        print "Se actualizaron las BD horas a por defecto 2"
                    else:
                        print "No se actualizaron las BD horas a por defecto"
                else:
                    print "Se actualizaron las BD horas a por defecto"
                    
                # Luego verificamos si la hora actual es mayor a la hora de la BD
                obtener_todas_las_horasdb = obtener_estado_de_todas_las_horas_no_hechas()
                for i in xrange(len(obtener_todas_las_horasdb)):
                    hora_iteracion = obtener_todas_las_horasdb[i]
                    hora_actual = datetime.datetime.now().time()
                    if int(str(hora_actual.strftime("%H:%M:%S")).replace(":","")) >= int(str(hora_iteracion[1]).replace(":","")):
                        hecho = actualizar_estado_hora_check_hecho("Ok", hora_iteracion[0])
                        if hecho:
                            print "Se actualizo la hora"
            except Exception, e:
                print "No se pudo actualizar las horas db"
                
            try:
                ex.eliminarDatosAntiguos()
            except Exception, e:
                print "Fallo la eliminacion de datos antiguos: " + str(e)
                
            try:
                ex.escogerSocket()
            except Exception, e:
                print "Fallo la eleccion del socket: " + str(e)
        else:
            ex.settings.setValue("apagado_forzado",0)
    except Exception, e:
        print "Fallo la creacion de tramas 9"
        
    #########################################################

    clserial = clSerial(ex, cldb)
    clserial.start()

    clbarras = clBarras(ex, cldb)

    clmodem = clQuectel(ex, cldb, clserial, clbarras)
    clmodem.start()

    clmifare = clMifare(ex, cldb, clserial, clmodem)
    clmifare.start()

    clsms = clSMS(ex, cldb, clserial)
    clsms.start()

    clscreen = Screen(ex, clmodem, clmifare)

    sys.exit(app.exec_())   

if __name__ == '__main__':
    main()

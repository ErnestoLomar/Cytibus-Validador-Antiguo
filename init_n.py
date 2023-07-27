#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui
from PyQt4 import QtCore
import serial
import sqlite3
import os
from time import strftime
import time
import threading
import subprocess
from datetime import datetime
import urllib
from PyQt4 import QtCore as qtcore
from curses import ascii
import base64
import re
#sys.path.insert(0, '/home/hiram/Documentos/innobusmx/src/')
sys.path.insert(0, '/home/pi/innobusmx/src/')
from func import funciones
#from func import reloj
#from func import fecha
from rwdux3G import rwsGPS


class reloj():
    def __init__(self, parent):
        self.parent = parent
        self.mes=["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        self.mostrarHora()
        
    def mostrarHora(self):
        self.parent.lblHora.setText(time.strftime("%d/")+self.mes[int(time.strftime("%m"))]+time.strftime("/%Y %H:%M:%S"))
        if (self.parent.flGPS):
            self.parent.noGPS.setPixmap(QtGui.QPixmap(""))
        else:
            self.parent.noGPS.setPixmap(QtGui.QPixmap("data/img/noGPS.Jpeg"))
        QtCore.QTimer.singleShot(1000, self.mostrarHora)
        
class escucharSerial(qtcore.QThread):
    #el constructor no hace falta especificarlo
    #ya que la clase lo hace por nosotros.
    def __init__(self, parent, funcCore):
           #threading.Thread.__init__(self)
           qtcore.QThread.__init__(self)
           self.parent = parent
           self.funcCore = funcCore
           self.signal = qtcore.SIGNAL("signal")
           self.signal2 = qtcore.SIGNAL("signal2")
           #self.funcCore.dormir()


    def run(self):
        self.preaderLocal = self.parent.initSerial()
        while(True):
##            self.preaderLocal = self.parent.initSerial()
            print '     Siempre leyendo aca'
            self.out = ''
            print '#############################'
            self.out = self.preaderLocal.readline()
            ok = self.parent.cobrar(self.out, self.preaderLocal)
##            self.preaderLocal.close()
            print 'Respuesta del cobro', ok
            senial = self.emit(self.signal, ok)
            print 'Termine la primer senial'
            #el sleep de tres es para la Pi
            time.sleep(3)
            #time.sleep1)
            #time.sleep(8)
            self.emit(self.signal2)
            print 'Termine la segunda senial'
##            self.preaderLocal = self.parent.initSerial()
            print '#############################'


class mainWin(QtGui.QMainWindow):
    def __init__(self):
        super(mainWin, self).__init__()
        self.dir = os.path.dirname(__file__)
        self.cdDb = os.path.join(self.dir, 'data/db/tarifas')
        self.openDBAforo = os.path.join(self.dir,'data/db/aforo')
        self.openDBFotos = os.path.join(self.dir,'data/db/existeFoto')
        self.openDBEV2 = os.path.join(self.dir,'data/db/ev2')
        #Definicion de variables globales
        self.retardo = 1
        self.intervaloTiempoParaInFin = 5
        self.nVuelta = 0

#        self.sPort = '/dev/ttyUSB1'
        self.velocidad = 115200
        self.sPort = ''
        self.sPort3G = ''

        if self.sPort == '':
            path = "/dev"
            listdir = os.listdir(path)
            for file in listdir:
                if (file[0:6] == "ttyUSB"):
                    s = serial.Serial("/dev/"+file,self.velocidad, timeout=1)
                    s.flushInput()
                    s.flushOutput()
                    s.write("AT\r")
                    st = "."
                    while (st[-2:] != "AT") and (st != ""):
                        if (st == "."):
                            st = ""
                        st += str(s.read(1))
                    s.close
                    if (st == ""):
                        self.sPort = "/dev/"+file
                    if (st == "AT"):
                        self.sPort3G = "/dev/"+file
                
        print "RFID: "+self.sPort
        print "3G:"+self.sPort3G


        self.inicioFinUno = 'empezando'
        self.inicioFinActual = 'empezando'
        self.banderaIngreso  = 1
        self.valoresCard = {}
        self.versionOS = '0.10'
        self.turnoIniciadoFlag = False
        self.initUI()

        csnS = "HOLA"
        self.funcCore = funciones(self, csnS)
        #self.funcCore.dormir()

        self.hora = reloj(self)

        self.funcCore.datosVuelta
#        self.usbRFID = usbRFID(self)
        

        self.esS = escucharSerial(self, self.funcCore)
        self.esS.daemon = True
        self.connect(self.esS, self.esS.signal, self.funcCore.mostrarFoto)
        self.connect(self.esS, self.esS.signal2, self.funcCore.borrarFoto)
        self.esS.start()
        
        self.obj = rwsGPS(self)
        self.modem = inicioGPS(self, self.obj, self.flGPS, self.noGPS)
        self.modem.daemon = True
        self.modem.start()

        


    def initSerial(self):
        print '*****************************************Iniciando puerto serie'
        #self.sPort = '/dev/ttyUSB0'
        #velocidad = 115200
        self.ser = serial.Serial(self.sPort, self.velocidad)
        self.ser.flushInput()
        self.ser.flushOutput()
        return self.ser

    def initSerialEsperandoOK(self):
        print '*******************************Iniciando puerto esperando el OK'
        #self.sPort = '/dev/ttyUSB0'
        #velocidad = 115200
        self.ser = serial.Serial(self.sPort, self.velocidad, timeout = 1)
        self.ser.flushInput()
        self.ser.flushOutput()
        return self.ser

    def closeSerial(self):
        print '****************************************Cerrando el puerto serie'
        self.ser.close()

    def initUI(self):
        self.logo = QtGui.QLabel(self)
        self.logo.setScaledContents(True)
        pathImgFondo = os.path.join(self.dir,'data/img/wall2.bmp')
        self.logo.setPixmap(QtGui.QPixmap(pathImgFondo))
        self.logo.move(0, 0)
        self.logo.resize(800, 480)

        self.lblOperador = QtGui.QLabel(self)
        self.lblOperador.setScaledContents(True)
#        pathChofer = os.path.join(self.dir,'')
#        self.lblOperador.setPixmap(QtGui.QPixmap(pathChofer))
        self.lblOperador.move(30, 120)
        self.lblOperador.resize(243, 320)

        self.lblUnidad = QtGui.QLabel('', self)
        self.lblUnidad.resize(self.width(), 50)
        self.lblUnidad.move(400, 170)
        self.lblUnidad.setStyleSheet('QLabel { font-size: 40pt; font-family: \
            Arial; color:Ref}')
#        self.lblUnidad.setText("52")

        self.lblNombreOperador = QtGui.QLabel('', self)
        self.lblNombreOperador.resize(self.width(), 50)
        self.lblNombreOperador.move(400, 370)
        self.lblNombreOperador.setStyleSheet('QLabel { font-size: 35pt; font-family: \
            Arial; color:Green}')

        self.lblRuta = QtGui.QLabel('', self)
        self.lblRuta.resize(self.width(), 50)
        self.lblRuta.move(400, 270)
        self.lblRuta.setStyleSheet('QLabel { font-size: 35pt; font-family: \
            Arial; color:Green}')

        self.lblVuelta = QtGui.QLabel('', self)
        self.lblVuelta.resize(self.width(), 50)
        self.lblVuelta.move(670, 170)
        self.lblVuelta.setStyleSheet('QLabel { font-size: 35pt; font-family: \
            Arial; color:Black}')

        self.lblVelocidad = QtGui.QLabel('', self)
        self.lblVelocidad.resize(self.width(), 50)
        self.lblVelocidad.move(670, 270)
        self.lblVelocidad.setStyleSheet('QLabel { font-size: 35pt; font-family: \
            Arial; color:Black}')


        conn = sqlite3.connect(self.openDBAforo)
        c = conn.cursor()
        c.execute("SELECT nunEco, Operador FROM configuraSistema")
        data = c.fetchone()
        if data is None:
            self.lblUnidad.setText("")
            self.lblNombreOperador.setText("")
        else:
            self.lblUnidad.setText(str(data[0]))
            self.lblNombreOperador.setText(data[1])
        c.close

        c = conn.cursor()
        c.execute('select fechaHora, ruta.nombre, csn, num_vuelta, tTurno.nombre, inicioFin from soloVuelta, ruta, tTurno WHERE soloVuelta.idRuta = ruta.Id AND soloVuelta.turno = tTurno.idTurno ORDER BY idSoloVuelta DESC LIMIT 1')
        data = c.fetchone()
        if data[5] == "F":
            self.lblOperador.setPixmap(QtGui.QPixmap(""))
            self.lblRuta.setText("")
            self.lblNombreOperador.setText("")
            self.lblVuelta.setText("")
        else:
            self.lblRuta.setText(data[1])
            imgChofer = "data/user/%s.Jpeg"%data[2]
            scriptChofer = os.path.join(self.dir, imgChofer)
            self.lblOperador.setPixmap(QtGui.QPixmap(scriptChofer))
            self.lblVuelta.setText(str(data[3]))
        c.close

        self.lblHora = QtGui.QLabel('', self)
        self.lblHora.resize(self.width(), 50)
        self.lblHora.move(10, 440)
        self.lblHora.setStyleSheet('QLabel { font-size: 14pt; font-family: \
            Arial; color:White}')


        self.lblMsg = QtGui.QLabel('', self)
        self.lblMsg.resize(self.width(), 50)
        self.lblMsg.move(10, 380)
        self.lblMsg.setStyleSheet('QLabel { font-size: 75pt; font-family: \
            Arial; color:Black}')


        self.msg = QtGui.QLabel('', self)
        self.msg.resize(self.width(), 50)
        self.msg.move(135, 400)
        self.msg.setStyleSheet('QLabel { font-size: 30pt; font-family: \
            Arial; color:red}')

        '''
            ############################################################
                Aqui estan las variables que necesito para mostrar
                        la informacion de los aforo
            ############################################################
        '''

        self.lblAlteTurno = QtGui.QLabel('', self)
        self.lblAlteTurno.resize(self.width(), 50)
        self.lblAlteTurno.move(200, 360)
        self.lblAlteTurno.setStyleSheet('QLabel { font-size: 25pt; font-family: \
            Arial; color:white}')


        self.lblAlteTurnoDos = QtGui.QLabel('', self)
        self.lblAlteTurnoDos.resize(self.width(), 50)
        self.lblAlteTurnoDos.move(200, 400)
        self.lblAlteTurnoDos.setStyleSheet('QLabel { font-size: 25pt; font-family: \
            Arial; color:white}')


        imgTarjetaAtras = "data/img/imgTarjetas/CD.jpg"
        imgUsuarioTarjeta = "data/user/admin.Jpeg"

        self.imgTarjeta = QtGui.QLabel(self)
        self.imgTarjeta.setPixmap(QtGui.QPixmap(""))
        #self.imgTarjeta.setPixmap(QtGui.QPixmap(imgTarjetaAtras))
        self.imgTarjeta.setScaledContents(True)
        self.imgTarjeta.move(0,0)
        self.imgTarjeta.resize(800, 480)

        self.noRed = QtGui.QLabel(self)
        self.noRed.setPixmap(QtGui.QPixmap("data/img/noRed.Jpeg"))
        self.noRed.setScaledContents(True)
        self.noRed.move(770,425)
        self.noRed.resize(20, 20)

        self.noGPS = QtGui.QLabel(self)
        self.noGPS.setPixmap(QtGui.QPixmap("data/img/noGPS.Jpeg"))
        self.noGPS.setScaledContents(True)
        self.noGPS.move(740,425)
        self.noGPS.resize(20, 20)

        self.flGPS = False   

        self.noRDIF = QtGui.QLabel(self)
        if self.sPort == '':
            self.noRDIF.setPixmap(QtGui.QPixmap("data/img/noRFID.Jpeg"))
        else:
            self.noRDIF.setPixmap(QtGui.QPixmap(""))
        self.noRDIF.setScaledContents(True)
        self.noRDIF.move(710,425)
        self.noRDIF.resize(20, 20)

        self.noSevidor = QtGui.QLabel(self)
        self.noSevidor.setPixmap(QtGui.QPixmap("data/img/noServidor.Jpeg"))
        self.noSevidor.setScaledContents(True)
        self.noSevidor.move(680,425)
        self.noSevidor.resize(20, 20)


        self.imgDefault = QtGui.QLabel(self)
        self.imgDefault.setPixmap(QtGui.QPixmap(""))
        self.imgDefault.setScaledContents(True)
        self.imgDefault.move(0,0)
        self.imgDefault.resize(480,480)
        #antigui tamano
        #self.imgDefault.resize(335,345)

        self.lblNombreApe = QtGui.QLabel('', self)
        self.lblNombreApe.resize(self.width(), 50)
        self.lblNombreApe.move(100, 400)
        self.lblNombreApe.setStyleSheet('QLabel { font-size: 50pt; font-family: \
            Arial; color:black}')

        self.lblSaldo = QtGui.QLabel('', self)
        self.lblSaldo.resize(self.width(), 75)
        #antiguo
        self.lblSaldo.move(480, 260)
        #self.lblSaldo.move(400, 300)
        self.lblSaldo.setStyleSheet('QLabel { font-size: 55pt; font-family: \
            Arial; color:Green}')
            #E6F9AF
        #self.lblNombreApe.hide()

        self.lblSS = QtGui.QLabel('', self)
        self.lblSS.resize(self.width(), 50)
        self.lblSS.move(270, 45)
        self.lblSS.setStyleSheet('QLabel { font-size: 45pt; font-family: \
            Arial; color:White}')
            ##8BBEB2

        self.lblVAI = QtGui.QLabel('', self)
        self.lblVAI.resize(self.width(), 50)
        self.lblVAI.move(150, 45)
        self.lblVAI.setStyleSheet('QLabel { font-size: 50pt; font-family: \
            Arial; color:White}')

        self.lblSSMsg = QtGui.QLabel('', self)
        self.lblSSMsg.resize(self.width(), 50)
        self.lblSSMsg.move(150, 350)
        self.lblSSMsg.setStyleSheet('QLabel { font-size: 45pt; font-family: \
            Arial; color:White}')

        self.lblTarjetas = QtGui.QLabel('', self)
        self.lblTarjetas.resize(self.width(), 50)
        self.lblTarjetas.move(180, 220)
        self.lblTarjetas.setStyleSheet('QLabel { font-size: 30pt; font-family: \
            Arial; color:Yellow}')

        self.lblNV = QtGui.QLabel('', self)
        self.lblNV.resize(self.width(), 50)
        self.lblNV.move(265, 45)
        self.lblNV.setStyleSheet('QLabel { font-size: 45pt; font-family: \
            Arial; color:White}')

        self.lblInFinVuelta = QtGui.QLabel('', self)
        self.lblInFinVuelta.resize(self.width(), 50)
        self.lblInFinVuelta.move(200, 220)
        self.lblInFinVuelta.setStyleSheet('QLabel { font-size: 40pt; font-family: \
            Arial; color:red}')

        self.setGeometry(-1, 0, 800, 480)
        self.setWindowTitle('InnoBusMx v0.2')
        self.setStyleSheet('''QMainWindow { background-color:#1D2556;}
            QLabel{font-size: 15pt; font-family: Courier; color:black;
            font-weight: bold}''')
            #18314F
        self.center()
        self.show()
        #self.showMaximized()
        #self.setWindowFlags(QtCore.Qt.CustomizeWindowHint)
        #self.showFullScreen()


    def center(self):
        frameGm = self.frameGeometry()
        centerPoint = QtGui.QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())


    def cobrar(self, datos, ser):
        print 'Empiezo el proceso de cobro'
        self.datos = datos
        self.ser = ser
        print self.datos
        if self.datos:
            for c in self.datos:
                if c == '\n':
                    data = list(datos)
                    print "Recibi el fin de linea..."
                    longLis = len(datos)
                    print 'Longitud de la cadena', longLis
                    if data[0] == "3":
                        '''
                            TODO
                            Validar que cuando haya error en algun punto
                            quitar el println y dejar puros print ya que
                            el buffer se queda con errores de validaciones
                            anteriores :)
                        '''
                        print 'Es EV2'
                        self.valoresCard = self.funcCore.validarDataEV2(data)
                        if self.valoresCard['error']:
                                numError = 1
                                self.ser = self.initSerial()
                                self.algunError(numError, self.ser)
                                no = 'NO,NV,S*S,1'
                                return no
                        else:
                            print 'Aca esta el valor csn del diccionario'
                            print self.valoresCard.get("csn")
                            print self.valoresCard.get("llave")
                            print self.valoresCard.get("nomTipoTar")
                            print self.valoresCard.get("eTarjeta")
                            print self.valoresCard.get("idTipoTarjeta")
                            print self.valoresCard.get("fecha")
                            print self.valoresCard.get("nombre")
                            print self.valoresCard.get("apellido")
                            self.validacionLLlaveB = self.funcCore.validacionLlave\
                                (self.valoresCard.get('llave'),\
                                 self.valoresCard.get('csn'))
                            if self.validacionLLlaveB:
                                print 'Llave digital es invalida'
                                numError = 1
                                self.ser = self.initSerial()
                                self.algunError(numError, self.ser)
                                no = 'NO,NV,S*S,1'
                                return no
                            else:
                                if(self.valoresCard.get("nomTipoTar") == 'KI'):
                                    print 'Es un pinche chofi chofi'
                                    nombre = self.valoresCard.get("nombre") + " " + self.valoresCard.get("apellido")
                                    self.ser = self.initSerial()
                                    respuesta = self.inicioFinVueltaChofer(self.ser, self.valoresCard.get("csn"), nombre)
                                    #print 'Respuesta de abajo', respuesta
                                    numError = 4
                                    self.algunError(numError, self.ser)
                                    self.closeSerial()
                                    
                                    conn = sqlite3.connect(self.openDBAforo)
                                    c = conn.cursor()
                                    c.execute("SELECT nombre FROM configuraSistema, ruta WHERE idRutaActual = id")
                                    data = c.fetchone()
                                    if data is None:
                                        self.lblRuta.setText("")
                                    else:
                                        self.lblRuta.setText(data[0])
                                    c.close
                                    
                                    no = '%s,O,S*S,%s,%s'%(self.valoresCard.get("csn"), str(respuesta), nombre)
                                    #no = 'NO,O,S*S,'
                                    return no
                                if(self.valoresCard.get("nomTipoTar") == 'AN'):
                                    self.ser = self.initSerial()
                                    respuesta = self.mostrarAforosOInicioFinTurno(self.ser, self.valoresCard.get("csn"))
                                    print 'Respuesta de abajo', respuesta
                                    numError = 4
                                    self.algunError(numError, self.ser)
                                    self.closeSerial()
                                    nombre = self.valoresCard.get("nombre") + " " + self.valoresCard.get("apellido")
                                    #no = 'NO,A%s,S*S,1'%str(respuesta)
                                    no = 'NO,A,S*S,%s,%s'%(str(respuesta), nombre)
                                    return no
                                else:
                                    print 'La firma digital es correcta'
                                    validarSiExiste = self.obtenerTarifa(\
                                        self.valoresCard.get('idTipoTarjeta'))
                                    print validarSiExiste
                                    if validarSiExiste == False:
                                        print 'Tarifa no existe en el sistema no \
                                            se puede cobrar'
                                        numError = 1
                                        self.ser = self.initSerial()
                                        self.algunError(numError, self.ser)
                                        no = 'NO,NV,S*S,1'
                                        return no
                                    else:
                                        print 'Tarifa valida en el sistema'
                                        cobrarTarifa = validarSiExiste
                                        self.validarSaldo = self.funcCore.saldoSuf(\
                                            cobrarTarifa, self.valoresCard.get\
                                            ('saldo'))
                                        if self.validarSaldo:
                                            print 'Iniciando el serial'
                                            self.ser = self.initSerial()
                                            self.sinSaldo(cobrarTarifa, \
                                            self.valoresCard.get\
                                            ('saldo'), self.ser)
                                            self.closeSerial()
                                            #DAACD9C7,ES,don**vergas*u8ov��,959
                                            no = 'NO,SS,S*S,%s'%str(self.valoresCard.get('saldo'))
                                            return no
                                        else:
                                            print 'Saldo suficiente cobrare'
                                            nuevoSaldo = int(self.valoresCard.get('saldo')) - int(validarSiExiste)
                                            lonSaldoNuevo = len(str(nuevoSaldo))
                                            respuesta = self.funcCore.validarListaNegra(self.valoresCard.get("csn"))
                                            print 'Iniciando el Serial'
                                            print 'Imprimiendo validar si existe'
                                            print validarSiExiste
                                            self.ser = self.initSerialEsperandoOK()
                                            errorCobro = self.parsearSaldoCobrar  \
                                            (self.valoresCard.get("nomTipoTar"), self.valoresCard.get("csn"),\
                                            validarSiExiste, self.valoresCard.get("saldo"), nuevoSaldo,\
                                            lonSaldoNuevo, respuesta, int(self.valoresCard.get("folio")),self.ser)
                                            if respuesta == True or errorCobro == True:
                                                self.closeSerial()
                                                if respuesta == True:
                                                    print 'No mando imagen porque esta en lista negra'
                                                    no = 'NO,NV,S*S,1'
                                                    return no
                                                if errorCobro == True:
                                                    print 'No mando imagen'
                                                    no = 'NO,VAI,S*S,1'
                                                    return no
                                            else:
                                                self.closeSerial()
                                                respuesta = self.valoresCard.get("csn")+","+self.valoresCard.get("nomTipoTar")+\
                                                    ","+self.valoresCard.get("nombre")+","+str(nuevoSaldo)
                                                return respuesta
                    if data[0] == "1":
                        print 'No hago nada'
                        numError = 1
                        self.ser = self.initSerial()
                        self.algunError(numError, self.ser)
                        no = 'NO,VAI,S*S,1'
                        return no
                    if data[0] == "2":
                        print 'No hago nada'
                        numError = 1
                        self.ser = self.initSerial()
                        self.algunError(numError, self.ser)
                        no = 'NO,VAI,S*S,1'
                        return no
                    else:
                            numError = 1
                            self.ser = self.initSerial()
                            self.algunError(numError, self.ser)
                            no = 'NO,VAI,S*S,1'
                            return no
            print 'Sali del self. if datos'
        print 'Termine el proceso de pago'
        return True

    def inicioFinVueltaChofer(self, ser, csn, stOperador):
        self.ser = ser
        #funcion que inicia o termna un recorrido
        conn = sqlite3.connect(self.openDBAforo)
        c = conn.cursor()
        #Validar si hay una vuelta iniciada o no
        fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
        c.execute("SELECT idUnidad, kmActual FROM configuraSistema");
        datosSistema = c.fetchone()

        if datosSistema is None:
            print('No existen datos de configuracion del sistema')
        else:
            print('Si existen los datos necesaios del sistema')
            idUni = datosSistema[0]
            kmAct = datosSistema[1]

        #voy a buscar si hay turno iniciado si no no inicio
        c.execute("SELECT inicioFin FROM turnoDelDia ORDER BY idTurnoDelDia DESC LIMIT 1")
        turno = c.fetchone()

        if turno[0] == 'I':
            #busco si la vuelt esta iniciada o terminada si esta iniciada me decuelte un I
            #por lo cual la voy a finzalizar
            # si me devuelve una F la voy a iniciar
            c.execute("SELECT inicioFin FROM soloVuelta ORDER BY idSoloVuelta DESC LIMIT 1")
            data = c.fetchone()

            if data[0] == 'I':
                print 'Voy a finalizar'
                #self.lblTN.setText('Finalizando')
                #self.lblTNV.setText('vuelta')
                c.execute("SELECT km, csn, num_vuelta FROM soloVuelta ORDER BY idSoloVuelta DESC LIMIT 1")
                data = c.fetchone()
                if data is None:
                    print 'No hay vueltas antes'
                else:
                    km = data[0]
                    csnA  = data[1]
                    nVuelta = data[2]
                c.execute("SELECT idUnidad, idRutaActual FROM configuraSistema")
                ruta = c.fetchone()
                if ruta is None:
                    print 'No hay vueltas antes'
                else:
                    iUnidad = ruta[0]
                    ruta = ruta[1]
                c.execute("SELECT kmEstimado FROM ruta WHERE id = ?", (ruta, ))
                kmE = c.fetchone()
                if kmE is None:
                    print 'kmEstimado no se encuentra'
                else:
                    kmS = kmE[0]
                    
                kmNuevo = int(km) + int(kmS)
                c.execute("SELECT turno FROM turnoDelDia ORDER BY idTurnoDelDia DESC LIMIT 1")
                turno = c.fetchone()
                if turno is None:
                    print 'No hay turnos'
                else:
                    turnoA = turno[0]
                #INSERT INTO soloVuelta(fechahora, km, idUnidad, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?,? ,?), ('esta-siempre-va', 0, 0, 00000000, 0, 'M','F', 1);
                c.execute("INSERT INTO soloVuelta(fechahora, km, idUnidad, idRuta, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (fechaHora, kmNuevo, iUnidad, ruta, csn, nVuelta, turnoA, 'F', 0))
                conn.commit()
                #actualizo el kilometraje de la unidad despues de la vuelta
                c.execute("UPDATE configuraSistema SET kmActual = ?, operador = ''",(kmNuevo, ))
                conn.commit()
                numError = 4
                return 1
                #self.algunError(numError, self.ser)
            if data[0] == 'F':
                print 'Voy a iniciar'
                print 'Iniciando vuelta'
                #self.lblTN.setText('Iniciando')
                #self.lblTNV.setText('vuelta')
                '''
                    #########################################################
                        Antes de iniciar vuelta debo de conocer si hay una
                        vuelta iniciada el dia de hoy si hay una vuelta debo
                        de obtener el numero de vuelta actual y sumarle uno
                        si no hay vuelta de hoy iniciare un nuevo conteo de
                        vuelta.
                    #########################################################
                '''
                c.execute("SELECT km, csn, num_vuelta, fechahora FROM soloVuelta ORDER BY idSoloVuelta DESC LIMIT 1")
                data = c.fetchone()
                if data is None:
                    print 'No hay vueltas antes'
                else:
                    km = data[0]
                    csnA  = data[1]
                    nVuelta = data[2]
                    fecha = data[3]

                c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                data = c.fetchone()
                if data is None:
                    print('No hay parametros de configuracon contacta al administrador')
                else:
                    idUni = data[0]
                    idRuta = data[1]

                c.execute("SELECT turno FROM turnoDelDia ORDER BY idTurnoDelDia DESC LIMIT 1")
                turno = c.fetchone()
                if turno is None:
                    print 'No hay turnos'
                else:
                    turnoA = turno[0]

                print fecha
                fechaF = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
                print fechaF
                if fechaF.date() == datetime.today().date():
                    print 'Si hay vueltas inicidas antes'
                    self.nVuelta = int(nVuelta) + 1
                    c.execute("INSERT INTO soloVuelta(fechahora, km, idUnidad, idRuta, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (fechaHora, kmAct, idUni, idRuta, csn, self.nVuelta, turnoA, 'I', 0))
                    conn.commit()
                else:
                    #nVueltaNueva = int(nVuelta) + 1
                    print 'Error en la validaciop'
                    c.execute("INSERT INTO soloVuelta(fechahora, km, idUnidad, idRuta, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", (fechaHora, kmAct, idUni, idRuta, csn, 1, turnoA, 'I', 0))
                    conn.commit()

                c.execute("UPDATE configuraSistema SET operador = ?",(stOperador, ))
                conn.commit()

                numError = 4
                return 2
                #self.algunError(numError, self.ser)

        if turno[0] == 'F':
            #self.lblTN.setText('No hay turno iniciado')
            print 'No hay turno inciado'
            numError = 4
            return 3
            #self.algunError(numError, self.ser)


    def mostrarAforosOInicioFinTurno(self, ser, csn):
            '''
                ##############################################################
                    Funcion que muestra aforos si hay una vuelta iniciada
                    o inicia o termina turno.
                ##############################################################
            '''
            respuesta = 0;
            self.ser = ser
            conn = sqlite3.connect(self.openDBAforo)
            c = conn.cursor()

            #Consulta que me devuelve si hay o no un turno iniciado
            c.execute("SELECT fechaHora, turno, inicioFin  FROM \
                turnoDelDia WHERE date('now')=date(fechaHora) ORDER BY \
                idTurnoDelDia DESC LIMIT 1")
            data = c.fetchone()
            if data is None:
                print 'No hay turno iniciado'
                #Valido si hay un paso de tarjeta anterior para ver si quiere cerrar el turno
                c.execute("SELECT id, fechahora FROM inicioFinTurno")
                hayDato = c.fetchone()
                if hayDato is None:
                    print 'Es la primera la guardo'
                    tiempoActual = time.strftime("%H:%M:%S")
                    c.execute("INSERT INTO inicioFinTurno(fechahora) VALUES(?)", (tiempoActual,))
                    conn.commit()
                    respuesta = 1;
                else:
                    print 'Ya hay un tiempo anterior'
                    #Como se que es el primero del dia simplemente asigno
                    #el turno numero uno del dia, de igual manera es un inicio
                    turnoLocal = 1
                    inFin = "I"
                    tiempoAnterior = hayDato[1]
                    FMT = '%H:%M:%S'
                    tiempoActual = time.strftime("%H:%M:%S")
                    fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
                    tdelta = datetime.strptime(tiempoActual, FMT) - datetime.strptime(tiempoAnterior, FMT)
                    print 'Esta es la diferencia de tiempos'
                    print tdelta.seconds
                    if tdelta.seconds <= self.intervaloTiempoParaInFin:
                        print 'Voy a iniciar turno'
                        print 'Eliminando tiempos para que quede limpia'
                        idBorrar = hayDato[0]
                        c.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        conn.commit()
                        print 'Registro Borrado'
                        c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                        data = c.fetchone()
                        if data is None:
                            print('No hay parametros de configuracon contacta al administrador')
                        else:
                            idUni = data[0]
                            idRuta = data[1]
                        c.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                        idRuta, csn, turno, inicioFin, enviados) \
                        VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                        idRuta, csn, turnoLocal, inFin, 0))
                        conn.commit()
                        respuesta =  21
                    #esto pasa cuando ya hay un tiempo y es mas la diferencia
                    #entr tiempos asi que los voy a eliminar
                    else:
                        print 'Eliminando tiempos'
                        idBorrar = hayDato[0]
                        c.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        conn.commit()
                        print 'Registro Borrado'
                        respuesta = 11
            else:
                turno = data[1]
                print 'Si hay un turno iniciado'
                #Valido si hay un paso de tarjeta anterior para ver si quiere cerrar el turno
                c.execute("SELECT id, fechahora FROM inicioFinTurno")
                hayDato = c.fetchone()
                if hayDato is None:
                    print 'Es la primera la guardo'
                    tiempoActual = time.strftime("%H:%M:%S")
                    c.execute("INSERT INTO inicioFinTurno(fechahora) VALUES(?)", (tiempoActual,))
                    conn.commit()
                    respuesta = 1
                else:
                    print 'Ya hay un tiempo anterior'
                    #Como se que es el primero del dia simplemente asigno
                    #el turno numero uno del dia, de igual manera es un inicio
                    turnoLocal = 1
                    inFin = "F"
                    tiempoAnterior = hayDato[1]
                    FMT = '%H:%M:%S'
                    tiempoActual = time.strftime("%H:%M:%S")
                    fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
                    tdelta = datetime.strptime(tiempoActual, FMT) - datetime.strptime(tiempoAnterior, FMT)
                    print 'Esta es la diferencia de tiempos'
                    print tdelta.seconds
                    if tdelta.seconds <= self.intervaloTiempoParaInFin:
                        print 'Voy a cerrar turno'
                        print 'Eliminando tiempos para que quede limpia'
                        idBorrar = hayDato[0]
                        c.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        conn.commit()
                        print 'Registro Borrado'
                        #lo que voy a hacer aca es que si el turno anterior es un
                        #inicio solo lo voy a finalizar tal cual
                        if data[2] == 'I':
                            c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                            data = c.fetchone()
                            if data is None:
                                print('No hay parametros de configuracon contacta al administrador')
                            else:
                                idUni = data[0]
                                idRuta = data[1]

                            c.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                            idRuta, csn, turno, inicioFin, enviados) \
                            VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                            idRuta, csn, turno, inFin, 0))
                            conn.commit()
                            respuesta = 3;
                        else:
                        #if data[2] == 'F':
                            turnoNuevo = int(turno) + 1
                            c.execute("SELECT idTurno from tTurno WHERE idTurno = ?", (turnoNuevo,))
                            turnoN = c.fetchone()
                            if turnoN is None:
                                print 'No hay turno siguiente'

                                turnoLocal = 1
                                inFin = "I"
                                fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")

                                c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                                data = c.fetchone()
                                if data is None:
                                    print('No hay parametros de configuracon contacta al administrador')
                                else:
                                    idUni = data[0]
                                    idRuta = data[1]

                                c.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                                idRuta, csn, turno, inicioFin, enviados) \
                                VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                                idRuta, csn, turnoLocal, inFin, 0))
                                conn.commit()
                                respuesta = 21
                            else:
                                print 'Si hay un turno siguiente'
                                inFin = "I"
                                fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")

                                c.execute('SELECT idUnidad, idRutaActual FROM configuraSistema')
                                data = c.fetchone()
                                if data is None:
                                    print('No hay parametros de configuracon contacta al administrador')
                                else:
                                    idUni = data[0]
                                    idRuta = data[1]

                                c.execute("INSERT INTO turnoDelDia(fechahora, idUnidad, \
                                idRuta, csn, turno, inicioFin, enviados) \
                                VALUES(?, ?, ?, ?, ?, ?, ?)", (fechaHora, idUni, \
                                idRuta, csn, turnoNuevo, inFin, 0))
                                conn.commit()
                                respuesta= 21
                    #no supero el tiempo asi que no lo voy a acabar
                    else:
                        print 'Eliminando tiempos'
                        idBorrar = hayDato[0]
                        c.execute("DELETE FROM inicioFinTurno WHERE id = ?", (idBorrar, ))
                        conn.commit()
                        print 'Registro Borrado'
                        respuesta = 11

            numError = 4
            return respuesta
            #self.algunError(numError, self.ser)

    def algunError(self, numError, ser):
        self.ser = ser
        #este se tiene que enviar para que el cobrador no se
        #quede esperando el posible nuevo saldo
        mensajes = ['Hiram Zuniga','Tarjeta invalida en el sistema', \
            'Ya habias pagado','Tarjeta invalida',' ', '','Tarifa no actualizada']
        print 'Enviando codigo de cancelacion de transaccion'
        #time.sleep(self.retardo)
        self.ser.write('99999')
        aforoExitoso = 1
        while(aforoExitoso == 1):
            exito = ser.readline()
            print 'Esperando el NO'
            esperaRespuesta = 0
            esperaRespuesta = esperaRespuesta + 1
            for c in exito:
                if c == '\n':
                    print 'Que me regresa el validador'
                    rExito = list(exito)
                    print(rExito)
                    if(rExito[0] == 'N' and rExito[1] == 'O'):
                        print 'Recibi el NO por serial'
                        print 'No hago nada solo ceere bien la transaccion'
                        aforoExitoso = 2
                        #self.msg.setText(mensajes[numError])
                    else:
                        print 'No se hizo la transacion aviar al usuario del aforo normal'
                        aforoExitoso = 2
                        print 'Suelto el hanger'

    def sinSaldo(self, tarifaC, saldoPesos ,ser):
        '''
        print 'No tiene saldo suficiente para tarifa actual a cobrar'
        ser.write('11111')
        aforoExitoso = 1
        while(aforoExitoso == 1):
            exito = ser.readline()
            print('Esperando el NO')
            esperaRespuesta = 0
            esperaRespuesta = esperaRespuesta + 1
            for c in exito:
                if c == '':
                    print 'Que me regresa el validador'
                    rExito = list(exito)
                    print(rExito)
                    if(rExito[0] == 'N' and rExito[1] == 'O'):
                        print 'Recibi el NO por serial'
                        print 'No hago nada solo ceere bien la transaccion'
                        #Variable para romper el while
                        aforoExitoso = 2
                    else:
                        print 'No se hizo la transacion aviar al usuario del aforo normal'
                        aforoExitoso = 2
                        print 'Suelto el hanger'
        '''

        print 'No tiene saldo suficiente para tarifa actual a cobrar'
        ser.write('99999')
        #self.guardarAforo(tipoS, csnS, nuevoSaldo, tarifaC)
        aforoExitoso = 1
        esperaRespuesta = 0
        while aforoExitoso == 1:
            print 'Esperando el NO'
            #ser.flushInput()
            #ser.flushOutput()
            time.sleep(0.1)
            exito = ser.readline()
            esperaRespuesta = esperaRespuesta + 1
            print esperaRespuesta
            #print 'No recibi nada'
            if esperaRespuesta == 2:
                aforoExitoso = 1
                break
            #for c in exito:
            my_list = exito.split(",")
            print 'aca imprimo lo que tiene exito', my_list
            if my_list[0] == 'NO\r\n':
                print 'Que me regresa el validador?', exito
                rExito = list(exito)
                #print rExito
                if(rExito[0] == 'N' and rExito[1] == 'O'):
                    print 'Recibi el NO por serial'
                    print 'No hago nada solo ceere bien la transaccion'
                    #Variable para romper el while
                    #aforoExitoso = 2
                    return True
                else:
                    print 'No se hizo la transacion aviar al usuario del aforo normal'
                    print 'Suelto el hanger'
                    #aforoExitoso = 2
                    return True
            else:
                print 'No se hizo la transacion aviar al usuario del aforo normal'
                print 'Suelto el hanger'
                #aforoExitoso = 2
                return True


    def parsearSaldoCobrar(self, tipoS, csnS, tarifaC, saldoPesos,nuevoSaldo, lonSaldoNuevo, respuesta, folio, ser):
        if respuesta == False:
            if lonSaldoNuevo == 1:
                print 'Saldo con 1 caracteres rellenar para que sean 5 '
                nuevoSaldoCompleto = '0000' + str(nuevoSaldo)
                ser.write(str(nuevoSaldoCompleto))
            if lonSaldoNuevo == 2:
                print 'Saldo con 2 caracteres rellenar para que sean 5 '
                nuevoSaldoCompleto = '000' + str(nuevoSaldo)
                ser.write(str(nuevoSaldoCompleto))
            if lonSaldoNuevo == 3:
                print 'Saldo con 3 caracteres rellenar para que sean 5 '
                nuevoSaldoCompleto = '00' + str(nuevoSaldo)
                ser.write(str(nuevoSaldoCompleto))
            if lonSaldoNuevo == 4:
                print 'Saldo con 4 caracteres rellenar para que sean 5 '
                nuevoSaldoCompleto = '0' + str(nuevoSaldo)
                print nuevoSaldoCompleto
                ser.write(str(nuevoSaldoCompleto))
            if lonSaldoNuevo == 5:
                print 'Saldo con 5 no voy a rellenar'
                ser.write(str(nuevoSaldo))

            #self.guardarAforo(tipoS, csnS, nuevoSaldo, tarifaC)
            aforoExitoso = 1
            esperaRespuesta = 0
            while aforoExitoso == 1:
                print 'Esperando el OK'
                #ser.flushInput()
                #ser.flushOutput()
                time.sleep(0.1)
                exito = ser.readline()
                esperaRespuesta = esperaRespuesta + 1
                print esperaRespuesta
                #print 'No recibi nada'
                if esperaRespuesta == 2:
                    aforoExitoso = 1
                    break
                #for c in exito:
                my_list = exito.split(",")
                print 'aca imprimo lo que tiene exito', my_list
                if my_list[0] == 'OK\r\n':
                    print 'Que me regresa el validador?', exito
                    rExito = list(exito)
                    #print rExito
                    if(rExito[0] == 'O' and rExito[1] == 'K'):
                        print 'Recibi el OK, guardando aforo'
                        #print 'Entonces si voy a guaradr'
                        self.guardarAforo(tipoS, csnS, nuevoSaldo, tarifaC, folio)
                        #aforoExitoso = 2
                        return False
                    else:
                        print 'No se hizo la transacion aviar al usuario del \
                            aforo normal'
                        print 'Suelto el hanger'
                        #aforoExitoso = 2
                        return True
                else:
                    print 'No se hizo la transacion aviar al usuario del aforo \
                        normal'
                    print 'Suelto el hanger'
                    #aforoExitoso = 2
                    return True
        else:
            print 'La csn esta reportada con anomalias Esta en la lista negra \
                y no puedo cobrar'
            #ser.write('11111')
            ser.write('99999')
            aforoExitoso = 1
            while(aforoExitoso == 1):
                exito = ser.readline()
                print 'Esperando el NO'
                esperaRespuesta = 0
                esperaRespuesta = esperaRespuesta + 1
                for c in exito:
                    if c == '\n':
                        print 'Que me regresa el validador'
                        rExito = list(exito)
                        print(rExito)
                        if(rExito[0] == 'N' and rExito[1] == 'O'):
                            print 'Recibi el NO por serial'
                            print 'No hago nada solo ceere bien la transaccion'
                            #Variable para romper el while
                            aforoExitoso = 2
                            return True
                        else:
                            print 'No se hizo la transacion aviar al usuario \
                                del aforo normal'
                            aforoExitoso = 2
                            print 'Suelto el hanger'
                            return True


    def parsearSaldoCobrarEV2(self, tipoS, csnS, tarifaC, saldoPesos,nuevoSaldo, lonSaldoNuevo, respuesta, ser, saldo):
        if respuesta == False:
            ser.write('11111')
            #self.guardarAforo(tipoS, csnS, nuevoSaldo, tarifaC)
            aforoExitoso = 1
            esperaRespuesta = 0
            while aforoExitoso == 1:
                print 'Esperando el OK'
                #ser.flushInput()
                #ser.flushOutput()
                time.sleep(0.1)
                exito = ser.readline()
                esperaRespuesta = esperaRespuesta + 1
                print esperaRespuesta
                #print 'No recibi nada'
                if esperaRespuesta == 2:
                    aforoExitoso = 1
                    break
                #for c in exito:
                my_list = exito.split(",")
                print 'aca imprimo lo que tiene exito', my_list
                if my_list[0] == 'OK\r\n':
                    print 'Que me regresa el validador?', exito
                    rExito = list(exito)
                    #print rExito
                    if(rExito[0] == 'O' and rExito[1] == 'K'):
                        print 'Recibi el OK, guardando aforo'
                        #print 'Entonces si voy a guaradr'
                        print 'Mientras no lo voy a guardar'
                        #print tipoS
                        #print csnS
                        #print nuevoSaldo
                        #print tarifaC
                        self.actualizarSaldoEV2(csnS, tarifaC, saldo)
                        self.guardarAforo(tipoS, csnS, nuevoSaldo, tarifaC)
                        #aforoExitoso = 2
                        return False
                    else:
                        print 'No se hizo la transacion aviar al usuario del \
                            aforo normal'
                        print 'Suelto el hanger'
                        #aforoExitoso = 2
                        return True
                else:
                    print 'No se hizo la transacion aviar al usuario del aforo \
                        normal'
                    print 'Suelto el hanger'
                    #aforoExitoso = 2
                    return True
        else:
            print 'La csn esta reportada con anomalias Esta en la lista negra \
                y no puedo cobrar'
            #ser.write('11111')
            ser.write('99999')
            aforoExitoso = 1
            while(aforoExitoso == 1):
                exito = ser.readline()
                print 'Esperando el NO'
                esperaRespuesta = 0
                esperaRespuesta = esperaRespuesta + 1
                for c in exito:
                    if c == '\n':
                        print 'Que me regresa el validador'
                        rExito = list(exito)
                        print(rExito)
                        if(rExito[0] == 'N' and rExito[1] == 'O'):
                            print 'Recibi el NO por serial'
                            print 'No hago nada solo ceere bien la transaccion'
                            #Variable para romper el while
                            aforoExitoso = 2
                            return True
                        else:
                            print 'No se hizo la transacion aviar al usuario \
                                del aforo normal'
                            aforoExitoso = 2
                            print 'Suelto el hanger'
                            return True


    def actualizarSaldoEV2(self, csn, tarifa, saldo):
        saldonuevo = int(saldo) - int(tarifa)
        self.Scsn = str(csn)
        conn = sqlite3.connect(self.openDBEV2)
        c = conn.cursor()
        c.execute("UPDATE tag SET saldo = ? WHERE csn = ?",(saldonuevo, self.Scsn, ))
        conn.commit()


    def yaPagoAntes(self, tipoS, csnS):
        print 'Validando si ya pago antes'
        enviados = 0
        conn = sqlite3.connect(self.openDBAforo)
        c = conn.cursor()
        ini = 'I'
        c.execute("SELECT fechaHora FROM soloVuelta WHERE inicioFin=? ORDER BY idSoloVuelta DESC LIMIT 1", (ini,))
        comparar = c.fetchone()
        if comparar is None:
            print 'No hay turno activo el dia de hoy'
        else:
            horaComparar = comparar[0]

        c.execute("SELECT fechaHora FROM validador WHERE csn = ? ORDER BY idValidador DESC LIMIT 1" ,(csnS, ))
        data = c.fetchone()
        if data is None:
            print 'No habias pagado antes'
            return False
        else:
            horaDelPago = data[0]

        FMT = '%Y-%m-%d %H:%M:%S'
        tdelta = datetime.strptime(horaComparar, FMT) < datetime.strptime(horaDelPago, FMT)

        #print 'hora del inicio de turno', horaComparar
        #print 'hora del ultimo pago', horaDelPago

        #Aqui modificare que pueda pagar mas de dos veces cambiando el True del if
        #por un False en el if.
        if tdelta == True:
            #return True
            return False
        else:
            return False

    def obtenerTarifa(self, tipoTS):
        print 'Obteniendo tarifa actual'
        try:
            conn = sqlite3.connect(self.cdDb)
            c = conn.cursor()
            c.execute("SELECT cantidad FROM tar WHERE nom = ?", (str(tipoTS),))
            tarifa = c.fetchone()

            if tarifa is None:
                print 'No se encuentra la tarifa para este tipo de usuario'
                return False
            else:
                tarifaC = tarifa[0]
                return tarifaC
        except:
            return False

    def guardarAforo(self, tipoS, csnS, nuevoSaldo, tarifaC, folio):
        enviados = 0
        print 'Guardando aforo...'
        #Obtener los datos a utilizar constantes en este caso
        #dos idUnidad y idChofer

        '''
            Ahora solo agregare el folio primero le sumare una accion y despues
            lo guardare
        '''
        print 'Dentro de parsearCobrar aca esta el folio que guardare pero primero le sumare uno'
        print folio
        print type(folio)
        folio += 1
        print folio

        conn = sqlite3.connect(self.openDBAforo)
        c = conn.cursor()
        c.execute('SELECT idUnidad FROM configuraSistema')
        data = c.fetchone()
        if data is None:
            print('No hay parametros de configuracon contacta al administrador')
        else:
            idUni = data[0]

        c.execute('SELECT idChofer FROM usuario')
        dataUsuario = c.fetchone()
        if dataUsuario is None:
            print('No hay parametros de configuracon contacta al administrador')
        else:
            idChofer = dataUsuario[0]
        c.close()

        fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
        c = conn.cursor()
        c.execute("INSERT INTO validador(idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado) values(?, ?, ?, ?, ?, ?, ?, ?, ?)", (tipoS, idUni, idChofer, csnS, nuevoSaldo, tarifaC, fechaHora, str(folio), enviados))
        conn.commit()

class inicioGPS(QtCore.QThread):
    def __init__(self, parent, obj, flGPS, noGPS):
           #threading.Thread.__init__(self)
           qtcore.QThread.__init__(self)
           self.parent = parent
#           self.obj = obj
#           self.flGPS = flGPS
#           self.noGPS = noGPS

    def run(self):
        accion = 1
        while (True):
            self.parent.obj.realizarAccion(accion)
            accion = (accion % 10) + 1
            #time.sleep(1)
#            print "Accion "+str(accion)
        #dir = os.path.dirname(__file__)
#        scriptPath = os.path.join(dir, 'data/script/comm/rwdux3G.py')
#        comando = "python %s"%scriptPath
#        subprocess.Popen(comando, shell=True)
        #print 'No hago nada'
        #el metodo run es donde se debe introducir el codigo que se ejecuta en segundo plano.


def main():
    app = QtGui.QApplication(sys.argv)
    ex = mainWin()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

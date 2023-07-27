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


class funciones():
    def __init__(self, parent, csn):
        print csn
        self.parent = parent
        self.dir = os.path.dirname(__file__)
        self.openDBNegra = os.path.join(self.dir, '/home/hiram/Documentos/innobusmx/data/db/listaNegra')
        #self.openDBNegra = os.path.join(self.dir, '/home/pi/innobusmx/data/db/listaNegra')
    def dormir(self):
        print "zzz"

    def mostrarFoto(self, sigstr):
        print sigstr
        try:
            #DAACD9C7,ES,don**vergas*u8o,959
            #print sigstr.split(",")
            dos = sigstr.split(",")
            #print dos[0]
            #print dos[1]
            #print dos[2]
            nombre = dos[2].split("*")
            #print nombre[0]
            #print nombre[1]
            saldo = dos[3]
            #print saldo
            try:
                nombreOperador = dos[4]
            except:
                print 'ni peiper'

            print dos[1]

            if dos[1] == 'EV2':
                print 'Poner lo que va en pantalla'
                self.parent.lblVAI.setText("Eres una EV2 :D")
                imgTarjetaAtras = "data/img/error.png"
                scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
            if dos[1] == 'AP':
                self.parent.close()
            if dos[1] == 'SS':
                imgTarjetaAtras = "data/img/error.png"
                scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                #print 'Sin saldo'
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                #self.parent.lblSS.setText("Sin saldo")
                print 'Aqui esta el saldo como llega'
                print saldo
                self.parent.lblSS.setText("Sin saldo")
                saldoInt = int(saldo)
                nuevoSaldoP = float(saldoInt)/100
                print 'Aqui esta el saldo transformado'
                print nuevoSaldoP
                #elf.SA.setText(str("%.2f" % saldoPesos))
                mensaje = 'Saldo actual: $ %.2f'%(nuevoSaldoP)
                self.parent.lblSSMsg.setText(mensaje)
                QtGui.qApp.processEvents()

            if dos[1] == 'VAI':
                imgTarjetaAtras = "data/img/error.png"
                scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                #print 'Sin saldo'
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                self.parent.lblVAI.setText("Intenta de nuevo")
                QtGui.qApp.processEvents()

            if dos[1] == 'NV':
                imgTarjetaAtras = "data/img/error.png"
                scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                #print 'Sin saldo'
                self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                #self.parent.lblVAI.setText("No valida")
                self.parent.lblNV.setText("No Valida")
                QtGui.qApp.processEvents()

            if dos[1] == 'A':
                if saldo == "1":
                    if self.parent.turnoIniciadoFlag == False:
                        imgTarjetaAtras = "data/img/us.jpg"
                        scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                        #print 'Sin saldo'
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.lblVAI.setText("Cuidado puedes alterar")
                        self.parent.lblSSMsg.setText("el turno")
                        QtGui.qApp.processEvents()
                    if self.parent.turnoIniciadoFlag == True:
                        conn = sqlite3.connect(self.parent.openDBAforo)
                        c = conn.cursor()
                        c.execute("SELECT inicioFin, fechaHora FROM soloVuelta \
                            ORDER BY idSoloVuelta DESC LIMIT 1")
                        fechaHoraUltimaVuelta = c.fetchone()
                        fechahoraInicio = fechaHoraUltimaVuelta[1]
                        print fechahoraInicio
                        #Consulta que me devuelve si hay o no un turno iniciado
                        c.execute("SELECT idTipoTisc, Count(idTipoTisc)   FROM \
                        validador WHERE fechaHora BETWEEN ? AND DATETIME('now')\
                        GROUP BY idTipoTisc",(fechahoraInicio,))
                        data = c.fetchall()
                        print 'Aca estan los datos de la consulta'
                        print data

                        transData = str(data).encode('ascii','ignore')
                        nstr = re.sub(r'[?|$|.|!|u]',r'',str(transData))
                        nestr = re.sub(r'[^a-zA-Z0-9 ]',r'',nstr)
                        print nestr

                        imgTarjetaAtras = "data/img/us.jpg"
                        scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                        #print 'Sin saldo'
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.lblVAI.setText("Cuidado puedes alterar")
                        self.parent.lblSSMsg.setText("el turno")
                        self.parent.lblTarjetas.setText(str(nestr))
                        QtGui.qApp.processEvents()
                if saldo == "21":
                    imgTarjetaAtras = "data/img/us.jpg"
                    scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                    #print 'Sin saldo'
                    self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                    self.parent.lblVAI.setText("Turno iniciado")
                    self.parent.turnoIniciadoFlag = True
                    QtGui.qApp.processEvents()
                if saldo == "11":
                    if self.parent.turnoIniciadoFlag == False:
                        imgTarjetaAtras = "data/img/us.jpg"
                        scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                        #print 'Sin saldo'
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.lblVAI.setText("Inicio de turno")
                        self.parent.lblSSMsg.setText("cancelado")
                        QtGui.qApp.processEvents()
                    if self.parent.turnoIniciadoFlag == True:
                        conn = sqlite3.connect(self.parent.openDBAforo)
                        c = conn.cursor()
                        c.execute("SELECT inicioFin, fechaHora FROM soloVuelta \
                            ORDER BY idSoloVuelta DESC LIMIT 1")
                        fechaHoraUltimaVuelta = c.fetchone()
                        fechahoraInicio = fechaHoraUltimaVuelta[1]
                        print fechahoraInicio
                        #Consulta que me devuelve si hay o no un turno iniciado
                        c.execute("SELECT idTipoTisc, Count(idTipoTisc)   FROM \
                        validador WHERE fechaHora BETWEEN ? AND DATETIME('now')\
                        GROUP BY idTipoTisc",(fechahoraInicio,))
                        data = c.fetchall()
                        print 'Aca estan los datos de la consulta'
                        print data
                        transData = str(data).encode('ascii','ignore')
                        nstr = re.sub(r'[?|$|.|!|u]',r'',str(transData))
                        nestr = re.sub(r'[^a-zA-Z0-9 ]',r'',nstr)
                        print nestr

                        imgTarjetaAtras = "data/img/us.jpg"
                        scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                        #print 'Sin saldo'
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.lblVAI.setText("Inicio de turno")
                        self.parent.lblSSMsg.setText("cancelado")
                        self.parent.lblTarjetas.setText(str(nestr))
                        QtGui.qApp.processEvents()
                if saldo == "3":
                    imgTarjetaAtras = "data/img/us.jpg"
                    scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                    #print 'Sin saldo'
                    self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                    self.parent.lblVAI.setText("Turno")
                    self.parent.lblSSMsg.setText("Finalizado")
                    self.parent.turnoIniciadoFlag = False
                    QtGui.qApp.processEvents()
            if dos[1] == 'O':
                if saldo == "1":
                    imgTarjetaAtras = "data/img/chofer.bmp"
                    scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                    #print 'Sin saldo'
                    self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                    self.parent.lblInFinVuelta.setText("Finalizando Vuelta")
                    #self.parent.lblVAI.setText("Finalizando")
                    #self.parent.lblSSMsg.setText("Vuelta")

                    self.parent.lblOperador.setPixmap(QtGui.QPixmap(""))

                    self.parent.lblRuta.setText("")
                    self.parent.lblNombreOperador.setText("")

                    QtGui.qApp.processEvents()
                if saldo == "2":
                    imgTarjetaAtras = "data/img/chofer.bmp"
                    scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                    self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))

                    #self.parent.lblVAI.setText("Iniciando")
                    #self.parent.lblSSMsg.setText("Vuelta")
                    self.parent.lblInFinVuelta.setText("Iniciando Vuelta")

                    imgChofer = "data/user/chofer.jpg"
                    scriptChofer = os.path.join(self.parent.dir, imgChofer)
                    self.parent.lblOperador.setPixmap(QtGui.QPixmap(scriptChofer))


                    self.parent.lblRuta.setText("Cactus")
                    self.parent.lblNombreOperador.setText(str(nombreOperador))

                    QtGui.qApp.processEvents()
                if saldo == "3":
                    imgTarjetaAtras = "data/img/us.jpg"
                    scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                    #print 'Sin saldo'
                    self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                    self.parent.lblVAI.setText("No hay turno")
                    self.parent.lblSSMsg.setText("iniciado")
                    QtGui.qApp.processEvents()
            else:
                if dos[0] ==  'NO':
                    print 'No hagas nada con la foto'
                else:
                    saldoInt = int(saldo)
                    nuevoSaldoP = float(saldoInt)/100
                    filename = 'data/user/%s.Jpeg'%dos[0]
                    print 'Estoy aqui adentro de descargar la foto', filename
                    scriptImgBusqueda = os.path.join(self.parent.dir, filename)
                    print scriptImgBusqueda
                    if os.path.exists(scriptImgBusqueda):
                        print 'La foto existe la voy a procesar'
                        imgTarjetaAtras = "data/img/imgTarjetas/%s.jpg"%dos[1]
                        imgUsuarioTarjeta = "data/user/%s.Jpeg"%dos[0]
                        #print 'Imprimo los nombres de las dos variables'
                        #print imgTarjetaAtras
                        #print imgUsuarioTarjeta
                        scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                        scriptPathTarjeta = os.path.join(self.parent.dir, imgUsuarioTarjeta)
                        #print 'Imprimo las dos variables completas donde voy a busccar las fotos'
                        #print scriptPathTarjeta
                        #print scriptPathAtras
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.imgDefault.setPixmap(QtGui.QPixmap(scriptPathTarjeta))
                        self.parent.lblNombreApe.setText(str(nombre[0])
                        self.parent.lblSaldo.setText(str('$ %.2f' % nuevoSaldoP))
                        QtGui.qApp.processEvents()
                        #print 'Lo termine bien'
                        return True
                    else:
                        print 'La foto no existe'
                        #try:
                        #    urllib.urlretrieve('ftp://innogps:inno@192.168.1.8/Fotos/'+dos[0]+'.Jpeg', filename)
                        #    fotoD = 1
                        #except:
                        #   print 'No hemos podido descargar la foto'
                        #    if fotoD == 1:
                        #print 'Ya descargue la foto aca  voy a mostrar'
                        #print 'Esto lo paso como parametro'
                        #print sigstr
                        #self.parent.mostrarFoto(sigstr)
                        #self.parent.emit(self.parent.signal, sigstr)
                        #print 'Como ya la tengo ahora la voy a mostrar sin recursion'
                        #print '*******nueva manera***************'
                        imgTarjetaAtras = "data/img/imgTarjetas/%s.jpg"%dos[1]
                        #imgUsuarioTarjeta = "data/user/admin.png"
                        imgUsuarioTarjeta = "data/user/adminis.jpg"
                        #print 'Imprimo los nombres de las dos variables'
                        #print imgTarjetaAtras
                        #print imgUsuarioTarjeta
                        scriptPathAtras = os.path.join(self.parent.dir, imgTarjetaAtras)
                        scriptPathTarjeta = os.path.join(self.parent.dir, imgUsuarioTarjeta)
                        #print 'Imprimo las dos variables completas donde voy a busccar las fotos'
                        #print scriptPathTarjeta
                        #print scriptPathAtras
                        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(scriptPathAtras))
                        self.parent.imgDefault.setPixmap(QtGui.QPixmap(scriptPathTarjeta))
                        self.parent.lblNombreApe.setText(str(nombre[0]))
                        self.parent.lblSaldo.setText(str("$ %.2f" % nuevoSaldoP))
                        QtGui.qApp.processEvents()
                        #ser.close()
                        #print 'Lo termine bien'
                        salgo = 1
                        return True
                        print '###         Muestro imagen generica      ###'
        except:
            print 'Error al parsear los datos de la foto'

    def borrarFoto(self):
        #print 'La voy a quitar de pantalla'
        self.parent.lblNombreApe.setText("")
        self.parent.lblSaldo.setText("")
        self.parent.lblSS.setText("")
        self.parent.lblVAI.setText("")
        self.parent.lblSSMsg.setText("")
        self.parent.imgDefault.setPixmap(QtGui.QPixmap(""))
        self.parent.imgTarjeta.setPixmap(QtGui.QPixmap(""))
        self.parent.lblTarjetas.setText("")
        self.parent.lblNV.setText("")
        self.parent.lblInFinVuelta.setText("")
        QtGui.qApp.processEvents()

    def validarDataClassic(self, data):
        longLis = len(data)
        regreso = {}
        if longLis > 65:
            regreso['error'] = False
            #print 'imprimiendo datos desde el metodo de validar datos'
            #print data
            csnS = data[1:9]
            csnSS = ''.join(csnS)
            regreso['csn'] = csnSS
            print csnSS
            '''
            HZRGHYRGTFEASAFR
            ES
            8
            01

            2
            7A7ED7C7
            485A5247485952475446454153414652
            4553
            3031
            303130313230
            *1*
            *12000*
            '''
            llaveD = data[9:41]
            llaveS = ''.join(llaveD)
            llaveA = llaveS.decode("hex")
            regreso['llave'] = llaveA
            print llaveA

            tipoTarD = data[41:45]
            tipoTarS = ''.join(tipoTarD)
            tipoTarA = tipoTarS.decode("hex")
            regreso['nomTipoTar'] = tipoTarA
            print tipoTarS
            print tipoTarA

            #eTarD = data[51:53]
            #eTarS = ''.join(eTarD)
            #eTarA = eTarS.decode("hex")
            #eTarA = int(eTarS, 10)
            #regreso['eTarjeta'] = eTarA

            idTipoD = data[45:49]
            idTipoS = ''.join(idTipoD)
            idTipoA = idTipoS.decode("hex")
            regreso['idTipoTarjeta'] = idTipoA
            print idTipoA

            nombreApeD = data[49:81]
            nombreApeS = ''.join(nombreApeD)
            nombreApeA = nombreApeS.decode("hex")
            #print nombreApeA
            nombreApe = nombreApeA.split("*")
            regreso['nombre'] = nombreApe[0]
            regreso['apellido'] = nombreApe[1]
            print nombreApe[0]
            print nombreApe[1]

            #print '*'
            #nombreApeA.index('*')

            fechaD = data[49:61]
            fechaS = ''.join(fechaD)
            fechaA = fechaS.decode("hex")
            regreso['fecha'] = fechaA
            print fechaA

            #saldoS = datos[longLis-7:longLis]
            saldoD = data[61:longLis]
            saldoS = ''.join(saldoD)
            #saldoA = saldoS.decode("hex")
            saldo = saldoS.split('*')
            print 'folio'
            print saldo[1]
            print 'saldo'
            print saldo[2]
            regreso['saldo'] = saldo[2]
            regreso['folio'] = saldo[1]
        else:
            regreso['error'] = True

        return regreso

    def validarDataUL(self, data):
        regreso = {}
        longLis = len(data)
        #saldoS = datos[longLis-7:longLis]
        datos = ''.join(data)
        #saldoA = saldoS.decode("hex")
        datosAs = datos.split('*')

        print datosAs[0]
        print 'csn'
        print datosAs[1]
        print 'saldo'
        print datosAs[2]
        print 'folio'
        print datosAs[3]

        regreso['csn'] = datosAs[1]
        regreso['saldo'] = datosAs[2]
        regreso['folio'] = datosAs[3]

        return regreso

    def validarDataEV2(self, data):
        longLis = len(data)
        regreso = {}
        if longLis > 110:
            regreso['error'] = False
            #print 'imprimiendo datos desde el metodo de validar datos'
            #print data
            csnS = data[1] + data[2] + data[3] + data[4] + data[5]\
                + data[6] + data[7] + data[8] + data[9] + data[10]\
                + data[11] + data[12] + data[13] + data[14]
            regreso['csn'] = csnS
            print csnS

            llaveD = data[15:47]
            llaveS = ''.join(llaveD)
            llaveA = llaveS.decode("hex")
            regreso['llave'] = llaveA
            print llaveA

            tipoTarD = data[47:51]
            tipoTarS = ''.join(tipoTarD)
            tipoTarA = tipoTarS.decode("hex")
            regreso['nomTipoTar'] = tipoTarA
            print tipoTarA

            eTarD = data[51:53]
            eTarS = ''.join(eTarD)
            eTarA = eTarS.decode("hex")
            #eTarA = int(eTarS, 10)
            regreso['eTarjeta'] = eTarA
            print eTarA

            idTipoD = data[53:57]
            idTipoS = ''.join(idTipoD)
            idTipoA = idTipoS.decode("hex")
            regreso['idTipoTarjeta'] = idTipoA
            print idTipoA

            nombreApeD = data[57:97]
            nombreApeS = ''.join(nombreApeD)
            nombreApeA = nombreApeS.decode("hex")
            nombreApe = nombreApeA.split("*")
            regreso['nombre'] = nombreApe[0]
            regreso['apellido'] = nombreApe[1]
            print nombreApe[0]
            print nombreApe[1]
            #print '*'
            #nombreApeA.index('*')

            #fechaD = data[97:109]
            #fechaS = ''.join(fechaD)
            #fechaA = fechaS.decode("hex")
            #regreso['fecha'] = fechaA

            #saldoS = datos[longLis-7:longLis]
            saldoD = data[102:longLis]
            saldoS = ''.join(saldoD)
            #saldoA = saldoS.decode("hex")
            saldo = saldoS.split('*')
            print 'folio'
            print saldo[1]
            print 'saldo'
            print saldo[2]
            regreso['saldo'] = saldo[2]
            regreso['folio'] = saldo[1]
        else:
            regreso['error'] = True

        return regreso

    def validacionLlave(self, llave, csn):
        '''
            TODO Validar la llave
        '''
        print llave
        print csn
        return False

    def saldoSuf(self, importe, saldo):
        if int(saldo) > int(importe):
            return False
        else:
            return True

    def validarListaNegra(self, csnS):
        conn = sqlite3.connect(self.openDBNegra)
        c = conn.cursor()
        c.execute("SELECT csn FROM negra WHERE csn = ?", (csnS, ))
        data = c.fetchone()
        if data is None:
            return False
        else:
            return True

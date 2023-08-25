#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
from PyQt4.QtCore import QSettings

class sqLite():
    idTransportista = ""
    idUnidad = ""
    economico = ""
    idRuta  = ""
    urlAPN = ""
    userAPN = ""
    pwdAPN = ""
    urlSocket = ""
    puertoSocket = ""
    urlFTP = ""
    puertoFTP = ""
    userFTP = ""
    pwdFTP = ""
    tarifaNormal = 0

    dbAforo      = sqlite3.connect('/home/pi/innobusmx/data/db/aforo',       check_same_thread = False, isolation_level = None)
    dbGPS        = sqlite3.connect('/home/pi/innobusmx/data/db/gps',         check_same_thread = False, isolation_level = None)
    dbComando    = sqlite3.connect('/home/pi/innobusmx/data/db/comandoComm', check_same_thread = False, isolation_level = None)
    dbListaNegra = sqlite3.connect('/home/pi/innobusmx/data/db/listaNegra',  check_same_thread = False, isolation_level = None)
    dbFoto       = sqlite3.connect('/home/pi/innobusmx/data/db/existeFoto',  check_same_thread = False, isolation_level = None)
    dbAlarma     = sqlite3.connect('/home/pi/innobusmx/data/db/alarmas',     check_same_thread = False, isolation_level = None)
    dbTarifa     = sqlite3.connect('/home/pi/innobusmx/data/db/tarifas',     check_same_thread = False, isolation_level = None)
    dbMensajes   = sqlite3.connect('/home/pi/innobusmx/data/db/mensajes',    check_same_thread = False, isolation_level = None)
    dbVigencias  = sqlite3.connect('/home/pi/innobusmx/data/db/vigencia',    check_same_thread = False, isolation_level = None)
    dbFlota      = sqlite3.connect('/home/pi/innobusmx/data/db/flota',       check_same_thread = False, isolation_level = None)

    def __init__(self):
        v = self.dbVigencias.cursor()
        v.execute("PRAGMA table_info(vigencia)")
        data = v.fetchone()
        if data is None:
            v.execute("CREATE TABLE vigencia (csn VARCHAR(14) PRIMARY KEY, vigencia VARCHAR(6))")
            v.execute("CREATE TABLE vigenciaOK (csn VARCHAR(14) PRIMARY KEY)")
            v.execute("CREATE TABLE descarga (fecha VARCHAR(6))")
            v.execute("INSERT INTO descarga (fecha) values ('191230')") 
        v.close()
        settings = QSettings("/home/pi/innobusmx/settings.ini", QSettings.IniFormat)

        c = self.dbAforo.cursor()
        c.execute("PRAGMA table_info(csn)")
        data = c.fetchone()
        if data is None:
            os.system('sqlite3 /home/pi/innobusmx/data/db/aforo ".read /home/pi/innobusmx/data/db.sql"')
            os.system('rm /home/pi/innobusmx/data/db.sql')
            os.system('sudo cp /home/pi/innobusmx/data/img/imgTarjetas/ES.jpg  /home/pi/innobusmx/data/img/imgTarjetas/AM.jpg')
            os.system('sudo cp /home/pi/innobusmx/data/img/imgTarjetas/ES.jpg  /home/pi/innobusmx/data/img/imgTarjetas/CD.jpg')
            os.system('sudo cp /home/pi/innobusmx/data/img/imgTarjetas/ES.jpg  /home/pi/innobusmx/data/img/imgTarjetas/EP.jpg')
            os.system('sudo cp /home/pi/innobusmx/data/img/imgTarjetas/ES.jpg  /home/pi/innobusmx/data/img/imgTarjetas/EU.jpg')
            os.system('sudo cp /home/pi/innobusmx/data/img/imgTarjetas/ES.jpg  /home/pi/innobusmx/data/img/imgTarjetas/JU.jpg')
            os.system('sudo cp /home/pi/innobusmx/data/img/imgTarjetas/ES.jpg  /home/pi/innobusmx/data/img/imgTarjetas/ME.jpg')
            os.system('sudo cp /home/pi/innobusmx/data/img/imgTarjetas/ES.jpg  /home/pi/innobusmx/data/img/imgTarjetas/PR.jpg')
            os.system('sudo cp /home/pi/innobusmx/data/img/imgTarjetas/ES.jpg  /home/pi/innobusmx/data/img/imgTarjetas/SA.jpg')
            settings.setValue("apagado_forzado",1)
            python = sys.executable
            os.execl(python, python, * sys.argv)
        else:
            try:
                self.dbAforo.execute('alter table validador add column idRuta int')
            except:
                print "Ya existe idRuta"
            try:
                self.dbAforo.execute('alter table vuelta add column idVuelta int')
            except:
                print "Ya existe idVuelta"
            try:
                self.dbAforo.execute('alter table vuelta add column tipo int')
            except:
                print "Ya existe tipo vuelta"
                

        c.execute("SELECT csn FROM usuario")
        data = c.fetchone()
        if data is None:
            c.execute("INSERT INTO usuario (csn, idChofer, password, nombre, apellidoPa) VALUES ('', '', '', '', '')")
            self.dbAforo.commit() 
        c.close()

        c = self.dbListaNegra.cursor()
        c.execute("PRAGMA table_info(csn)")
        data = c.fetchone()
        if data is None:
            c.execute("CREATE TABLE csn (csn varchar(14) PRIMARY KEY);")
            c.execute("DROP TABLE negra")
            self.dbListaNegra.commit()
        c.close()
            
        c = self.dbAforo.cursor()
        c.execute("PRAGMA table_info(barras2)")
        data = c.fetchone()
        if data is None:
            c.execute("CREATE TABLE barras2(idBarra INTEGER PRIMARY KEY AUTOINCREMENT,auxiliar int(3),duracion int(2),puerta  varchar(1),direccion int(1), fechaHora varchar(10),enviado int(1))")
            self.dbAforo.commit()
            c.execute("PRAGMA table_info(barras)")
            data = c.fetchone()
            if data:
                c.execute("DROP TABLE barras")
                self.dbAforo.commit()
            c.execute("CREATE TABLE barras(idBarra INTEGER PRIMARY KEY AUTOINCREMENT,auxiliar int(3),duracion int(2),puerta  varchar(1),direccion int(1), fechaHora varchar(10),enviado int(1))")
            self.dbAforo.commit()

        c.execute("PRAGMA table_info(barrasExcepciones)")
        data = c.fetchone()
        if data is None:
            c.execute("CREATE TABLE barrasExcepciones(idBarra INTEGER PRIMARY KEY AUTOINCREMENT,auxiliar int(3),duracion int(2),puerta  varchar(1),direccion int(1), fechaHora varchar(10),enviado int(1))")
            self.dbAforo.commit()

        c.execute("PRAGMA table_info(barrasExcepciones2)")
        data = c.fetchone()
        if data is None:
            c.execute("CREATE TABLE barrasExcepciones2(idBarra INTEGER PRIMARY KEY AUTOINCREMENT,auxiliar int(3),duracion int(2),puerta  varchar(1),direccion int(1), fechaHora varchar(10),enviado int(1))")
            self.dbAforo.commit()

        c.close()
       
        self.dbAforo.execute('UPDATE vuelta SET idRecorrido = 1 WHERE idRecorrido = 0')
        self.dbAforo.commit()

        #self.dbAforo.execute('DELETE FROM validador WHERE enviado = 1')
        #self.dbAforo.commit()

        c = self.dbAforo.cursor()

        #self.dbAforo.execute('UPDATE parametros SET urlAPN="internet.itelcel.com", userAPN="webgprs", pwdAPN="webgprs2002", urlSocket="innovaslp.dyndns.org", puertoSocket=11004, urlFTP="innovaslp.dyndns.org", puertoFTP=21')
        #self.dbAforo.commit()
        
        c.execute("SELECT idTransportista, idUnidad FROM parametros")
        data = c.fetchone()
        if data is None:
            #self.dbAforo.execute('UPDATE parametros SET urlAPN="internet.itelcel.com", userAPN="webgprs", pwdAPN="webgprs2002", urlSocket="innovaslp.dyndns.org", puertoSocket=11001, urlFTP="innovaslp.dyndns.org", puertoFTP=21')
            self.idTransportista = 0
        else:
            self.idTransportista = data[0]            
            if (self.idTransportista == -1):
                self.dbAforo.execute('UPDATE parametros SET urlAPN="internet.itelcel.com", userAPN="webgprs", pwdAPN="webgprs2002", urlSocket="innovaslp.dyndns.org", puertoSocket=11000, urlFTP="innovaslp.dyndns.org", puertoFTP=21')
            if (self.idTransportista == 0):
#                self.dbAforo.execute('UPDATE parametros SET urlAPN="internet.itelcel.com", userAPN="webgprs", pwdAPN="webgprs2002", urlSocket="innovaslp.dyndns.org", puertoSocket=11000, urlFTP="innovaslp.dyndns.org", puertoFTP=21')
                self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=5800, urlFTP="192.168.2.175", puertoFTP=21')
            if (self.idTransportista == 1):  # Delgadillo
                self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=107, urlFTP="192.168.2.175", puertoFTP=21')
            if (self.idTransportista == 2):  # Express
                self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=5900, urlFTP="192.168.2.175", puertoFTP=21')
            if (self.idTransportista == 3):  # San Jose
                self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=107, urlFTP="192.168.2.175", puertoFTP=21')
            if (self.idTransportista == 4):  # Tulsa
                self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=143, urlFTP="192.168.2.175", puertoFTP=21')
            if (self.idTransportista == 5):  # Guadalupe
                self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=992, urlFTP="192.168.2.175", puertoFTP=21')
            if (self.idTransportista == 6):  # Estrella
                self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=49971, urlFTP="192.168.2.175", puertoFTP=21')
            if (self.idTransportista == 7):  # Movilidad
                self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=10000, urlFTP="192.168.2.175", puertoFTP=21')
            if (self.idTransportista == 8):  # Tangamanga
                if (data[1] < 60):
                    self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=1443, urlFTP="192.168.2.175", puertoFTP=21')
                else:
                    self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=443, urlFTP="192.168.2.175", puertoFTP=21')
            if (self.idTransportista == 9):  # Urbi
                self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=49971, urlFTP="192.168.2.175", puertoFTP=21')
            if (self.idTransportista == 10):  # Medellin
                self.dbAforo.execute('UPDATE parametros SET urlAPN="innobusmx.itelcel.com", userAPN="", pwdAPN="", urlSocket="192.168.2.175", puertoSocket=10000, urlFTP="192.168.2.175", puertoFTP=21')
            self.dbAforo.commit()
        
        c.execute("SELECT idTransportista, idUnidad, economico, idRutaActual, urlAPN, userAPN, pwdAPN, urlSocket, puertoSocket, urlFTP, puertoFTP, userFTP, pwdFTP FROM parametros")
        data = c.fetchone()
        print data
        if data is None:
            print 'No hay parAmetros de configuracIon contacta al administrador'
            self.idTransportista = -1            
            self.idUnidad = -1
            self.economico = -1
            self.idRuta = -1
            self.urlAPN = ''
            self.userAPN = ''
            self.pwdAPN = ''
            self.urlSocket = ''
            self.puertoSocket = -1
            self.urlFTP = ''
            self.puertoFTP = -1
            self.userFTP = ''
            self.pwdFTP = ''
        else:
            self.idTransportista = data[0]            
            self.idUnidad = data[1]
            self.economico = data[2]
            if (data[3] is None) or (data[3] == ''):
                self.idRuta = 0
            else:
                self.idRuta = data[3]
            self.urlAPN = data[4]
            self.userAPN = data[5]
            self.pwdAPN = data[6]
            self.urlSocket = data[7]
            self.puertoSocket = data[8]
            self.urlFTP = data[9]
            self.puertoFTP = data[10]
            self.userFTP = data[11]
            self.pwdFTP = data[12]
        c.close()
        c = None
        self.tarifa = {}
        t = self.dbTarifa.cursor()
        #self.dbTarifa.execute('DELETE FROM tar WHERE nom = "03"')
        #self.dbTarifa.commit()
        t.execute('SELECT * FROM tar')
        data = t.fetchone()
        while not (data is None):
            self.tarifa[data[0]] = data[1]
            #if (data[1] > self.tarifaNormal):
            if (data[0] == "02"):
                self.tarifaNormal = data[1]
            data = t.fetchone()
        t.close()
        try:
            t = self.dbFlota.cursor()
            t.execute('CREATE TEMP VIEW vTerminales AS SELECT idRuta, idPC, orden, latitud, longitud FROM puntoInteres WHERE idTransportista = '+str(self.idTransportista)+' and idTipoPuntoControl = 8')
            t.execute('CREATE TEMP VIEW vPuntoControl AS SELECT idRuta, idPC, orden, latitud, longitud, orden, puntoRetorno FROM puntoInteres WHERE idTransportista = '+str(self.idTransportista)+' and idTipoPuntoControl = 9')
            #t.execute('CREATE TEMP VIEW vRetorno AS SELECT idRuta, idPC, orden, latitud, longitud, orden FROM puntoInteres WHERE idTransportista = '+str(self.idTransportista)+' and idTipoPuntoControl = 9 AND puntoRetorno = 1')
            t.close()
        except:
            print "No existe BD de Puntos de Control"

    def isvalid(self, st):
        i = 0
        for c in st:
            if (c < chr(32) or c > chr(126)):
                st = st[:i-1]+st[i+1:]
            else:
                i += 1
        return st

    def envio(self, app, msg):
        c = self.dbMensajes.cursor()
        c.execute("SELECT MAX(idEnvio) FROM envio WHERE app = "+str(app))
        data = c.fetchone()
        if (data[0] is None):
            i = "1"
        else:
            i = str(data[0]+1)
        c.close
        msg = self.isvalid(msg)
        self.dbMensajes.execute('INSERT INTO envio (idEnvio, app, msg, envio) VALUES ('+i+','+str(app)+',"'+str(msg)+'",0)')
        self.dbMensajes.commit()

    def vueltaValida(self, idRecorrido, noVuelta):
        t = self.dbFlota.cursor()
        print "Buscar si la vuelta es valida"
        print('SELECT total FROM asignacion WHERE idRuta = '+str(self.idRuta))
        t.execute('SELECT total FROM asignacion WHERE idRuta = '+str(self.idRuta))
        d = t.fetchone()
        esVuelta = True
        if (d is None):
            esVuelta = False
        else:
            if (d[0] == 0):
                esVuelta = False
            else:
                print('SELECT COUNT(vuelta) FROM puntoControl WHERE idRecorrido = '+str(idRecorrido)+' AND idRuta = '+str(self.idRuta)+' AND vuelta = '+str(noVuelta))
                t.execute('SELECT COUNT(vuelta) FROM puntoControl WHERE idRecorrido = '+str(idRecorrido)+' AND idRuta = '+str(self.idRuta)+' AND vuelta = '+str(noVuelta))
                d = t.fetchone()
                if (d[0] < 3):
                    esVuelta = False
        return esVuelta














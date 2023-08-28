#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt4 import QtCore
import time
import os
import sys
from PyQt4 import QtGui
from PyQt4.QtCore import QSettings
from datetime import datetime, timedelta, date
import datetime as dt
import subprocess
from tarjetasDB import obtener_tarjeta_mipase_por_UID
from alttusDB import registrar_aforo_mipase

os.environ['DISPLAY'] = ":0"
class clMifare(QtCore.QThread):
    
    def __init__(self, parent, clDB, clserial, clquectel):
        QtCore.QThread.__init__(self)
        self.ser = clserial
        self.clDB = clDB
        self.clquectel = clquectel
        self.parent = parent
        self.settings = QSettings("/home/pi/innobusmx/settings.ini", QSettings.IniFormat)
        #self.preaderLocal = self.ser.ser

    def PathTISC(self,tisc):
        path = '/home/pi/innobusmx/data/user/'+tisc[0:5]+"/"+tisc+".Jpeg"
        if not os.path.isfile(path):
            #self.parent.TISC = '/home/pi/innobusmx/data/user/generico.jpg'
            path = '/home/pi/innobusmx/data/user/generico.jpg'            
            self.clDB.envio(2,"f,"+tisc+","+str(self.clDB.idUnidad))
            self.parent.flSendEnvio = True
        return path
    
    def mostrar_imagen(self, imagen):
        self.parent.stImgTarjeta = '/home/pi/innobusmx/data/img/'+imagen+'.jpg'
        self.parent.TISC = "MIPASE"
        self.parent.stMsg = "NADA"
        time.sleep(2)
        self.parent.TISC = ''
        self.parent.stImgTarjeta = ''
        self.parent.stSaldoInsuficiente = ""                                    
        self.parent.stMsgVigencia = ""
        self.parent.stMsg = ""
        
        
    def msgError(self, msgCode, out, csn):
        if (out != "0"):
            #self.parent.lblMsgVigencia.resize(480, 75)
            #self.parent.lblMsgVigencia.move(320, 300)
            self.parent.stImgTarjeta = '/home/pi/innobusmx/data/img/'+out+'.jpg'
            self.parent.TISC = out
            self.parent.stMsg = msgCode
            time.sleep(2)
            self.parent.TISC = ''
            self.parent.stImgTarjeta = ''
            self.parent.stSaldoInsuficiente = ""                                    
            self.parent.stMsgVigencia = ""
            self.parent.stMsg = ""
        msg = "e,"+str(self.clDB.idUnidad)+","+str(csn)+","+str(msgCode)+","+time.strftime("%Y-%m-%d %H:%M:%S")
        self.clDB.envio(1,msg)  
        self.parent.flSendEnvio = True

    def run(self):
        self.preaderLocal = self.ser.setupRFID()
        print '     Siempre leyendo aca'
        print '#############################'
        while(True):
            self.out = ''
            commOK = True
            tarjeta_de_mi_pase = False
            #if True:
            try:
                self.preaderLocal.flushInput()
                self.preaderLocal.flushOutput()
                self.out = self.preaderLocal.readline()
            #else:
            except:
                commOK = False
                #self.preaderLocal = self.ser.initRFID()
            #if True:
            try:
                
                try:
                    ##################### ERNESTO LOMAR #####################
                    tarjeta_mi_pase = obtener_tarjeta_mipase_por_UID(str(self.out)[:14])
                    if tarjeta_mi_pase != None:
                        print "\x1b[1;33m"+"La tarjeta es identificada como MI PASE"
                        tarjeta_de_mi_pase = True
                        fecha_actual = dt.date.today()
                        hora_actual = datetime.now().time()
                        registro_aforo_mipase = registrar_aforo_mipase(str(self.out)[:14], 0, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), self.clquectel.latitud, self.clquectel.longitud, self.clDB.idTransportista, self.clDB.economico)
                        if registro_aforo_mipase:
                            print "\x1b[1;33m"+"Registro de aforo exitoso MI PASE"
                            if tarjeta_mi_pase[1]:
                                self.mostrar_imagen("aprobada_mipase")
                            else:
                                self.mostrar_imagen("declinada_mipase")
                        else:
                            print "\x1b[1;33m"+"No se registro el aforo MI PASE"
                    else:
                        tarjeta_mi_pase = False
                except Exception, e:
                    print "Fallo la lectura de tarjeta mi pase: " + str(e)
                ##################### ERNESTO LOMAR #####################
                
                #print "(",len(self.out),') out', self.out
                if not tarjeta_de_mi_pase:
                    if commOK:
                        if (self.parent.flMtto or self.parent.TISC != ""):
                            print "Lector Ocupado"    
                        elif (self.parent.flTurno or self.parent.flVuelta):
                            self.parent.closeTV = True
                        elif (len(self.out) == 3):
                            if (self.out.find(".") != -1):
                                subprocess.call("xset dpms force on",shell=True)
                                #os.system("DISPLAY=:0 xset dpms force on")
                            if (self.out.find("1") != -1):
                                self.settings.setValue("apagado_forzado",1)
                                python = sys.executable
                                os.execl(python, python, * sys.argv)
                        else:
                            if (len(self.out) == 19):
                                out = "001"
                                err = self.out[14:17]
                                if (err == "003" or err == "004"):
                                    out = "002"                        
                                if (err == "001" or err == "101" or err == "102" or err == "103"):
                                    out = "003"
                                if (self.parent.btnCancel.isVisible()):
                                    print "Pantalla de Operador"
                                else:
                                    self.msgError(err, out, self.out[0:14])
                            elif (len(self.out) == 13):
                                c = self.clDB.dbAforo.cursor()
                                c.execute("SELECT csn FROM csn WHERE csn = '"+self.out[0:11]+"'")
                                if c.fetchone():
                                    self.parent.flMtto = True
                                    res = '1'
                                else:
                                    self.msgError("501", "003", self.out[0:8])
                                    res = '0'
                                c.close
                                #if True:
                                try:
                                    self.preaderLocal.write(res)
                                #else:
                                except:
                                    print 'Error al escribir en el puerto'
                            elif (len(self.out) == 5):
                                if (self.out.find("000") != -1):
                                    print 'No Alcanzo a leer el CSN de la TISC'
                                else:
                                    print "Otro Error:",self.out
                            elif (len(self.out) > 0):
                                if (self.out[0] == '0' or self.out[0] == '3'):
                                    ok = self.cobrar(self.out)
                                    if not ok:
                                        self.preaderLocal.write('9999999')
                                    print 'Respuesta del cobro', ok
                                    print 'Termine la primer senial'
                                    print '#############################'                           
                            elif (len(self.out) == 0):
                                print 'Reinicio Serial'
                                if self.parent.flRFID:
                                    self.ser.closeRFID()
                                    self.ser.openRFID(0)
                                    time.sleep(1)
                            print '     Siempre leyendo aca'
                            print '#############################'
                    else:
                        print "initRFID Comm No OK"
                        #while self.parent.updateFirmware:
                        #    time.sleep(1)
                        #print "Inicializando RFID "
                        self.preaderLocal = self.ser.setupRFID()
                        time.sleep(1)
                        #self.preaderLocal = self.ser.initRFID()
            #else:
            except Exception, e:
                print "Fallo el run de ClMifare: " + str(e)
                self.msgError("001", "001", "00000000000000")
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print sys.exc_info()[1]
                print fname
                print exc_tb.tb_lineno

    def DatosTISC(self, data):
        print "Data", data
        regreso = {}
        regreso['error'] = False
        regreso['csn'] = data[1:15]
        regreso['llave'] = data[15:31]
        regreso['nomTipoTar'] = data[31:33]
        if (data[0] == '0'):
            datos = data[33:]
            datos = datos.split("*")
            regreso['nombre'] = datos[0]
            regreso['apellido'] = datos[1]
            regreso['caducidad'] = datos[3][-6:]
            regreso['NIP'] = datos[5]
            regreso['id'] = datos[4]
        elif (data[0] == '3'): 
            datos = data[33:57]
            datos = datos.split("*")
            #print "datos: (", len(datos) , ")", datos
            regreso['nombre'] = ""
            regreso['apellido'] = ""
            if (len(datos) == 3):
                #print ("len(datos) == 3")
                regreso['nombre'] = datos[0]
                regreso['apellido'] = datos[1]
            else:
                #print ("len(datos) != 3")
                #if True:
                try:
                    if len(datos) > 3:
                        if (len(datos[0]) > 9):
                            regreso['nombre'] = datos[0][0:9]
                            i = 1
                        else:
                            regreso['nombre'] = datos[0]
                            i = 1
                            while (len(datos) > i) and len(regreso['nombre']+' '+datos[i]) < 10:
                                regreso['nombre'] = regreso['nombre'] + ' ' + datos[i]
                                i += 1
                            regreso['apellido'] = ""
                            if (len(datos) > i):
                                regreso['apellido'] = datos[i]
                                i += 1
                                while (len(datos) > i) and len(regreso['apellido']+' '+datos[i]) < 16:
                                    regreso['apellido'] = regreso['apellido'] + ' ' + datos[i]
                                    i += 1
                    else:
                        regreso['nombre'] = ""
                        regreso['apellido'] = ""
                #else:
                except:
                        regreso['nombre'] = "."
                        regreso['apellido'] = "."
            regreso['caducidad'] = data[57:63]
            if (regreso['caducidad'][0] == '\x00'):
                regreso['caducidad'] = "0"
            datos = data[64:-1]
            datos = datos.split("*")
            #regreso['idTipoTarjeta'] = datos[0]
            regreso['folio'] = datos[0]
            regreso['saldo'] = datos[1]
            regreso['folioV'] = datos[2]
            regreso['saldoV'] = datos[3]
            regreso['tarifa'] = datos[4]
            regreso['vigencia'] = datos[5]
            if (regreso['nomTipoTar'] == "PP" or regreso['nomTipoTar'] == "PG"):
                regreso['tarifa'] = "03"
        print regreso    
        return regreso

    def validarListaNegra(self, csnS):
        c = self.clDB.dbListaNegra.cursor()
        c.execute("SELECT csn FROM csn WHERE csn = ?", (csnS, ))
        data = c.fetchone()
        if (data is None):
            print "TISC OK"
        else:
            print "TISC en Lista Negra"
        c.close
        c = None
        return not (data is None)

    def parsearSaldoCobrar(self, saldo, tarifa):
        while (len(saldo) < 7):
            saldo = "0" + saldo
        #print "saldo: ", saldo
        stRead = "."
        while (stRead == "."):
            #if True:
            try:
                stRead = "."
                self.preaderLocal.write(saldo)
                stRead = ""
                stRead = self.preaderLocal.readline()
                #print 'Que me regresa el validador?', stRead
            #else:
            except:
                if (stRead == ""):
                    stRead == "OK"
                else:    
                    stRead = "20"
        print 'Que me regresa el validador?', stRead        
        if stRead.find("OK") != -1:
            folio = int(self.valoresCard.get("folio")) + int(self.valoresCard.get("folioV")) + 1
            fechaHora = time.strftime("%Y-%m-%d %H:%M:%S")
            self.clquectel.aforo = True
            #if True:
            try:
                print ("INSERT INTO validador(idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado, recorrido, vuelta, idRuta) values (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)",(str(self.valoresCard.get("nomTipoTar")), self.clDB.idUnidad, self.parent.idOperador, str(self.valoresCard.get("csn")), saldo, tarifa, fechaHora, str(folio), str(self.parent.idRecorrido), str(self.parent.noVuelta), str(self.clDB.idRuta)))
                self.clDB.dbAforo.execute("INSERT INTO validador(idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado, recorrido, vuelta, idRuta) values (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)",(str(self.valoresCard.get("nomTipoTar")), self.clDB.idUnidad, self.parent.idOperador, str(self.valoresCard.get("csn")), saldo, tarifa, fechaHora, str(folio), str(self.parent.idRecorrido), str(self.parent.noVuelta), str(self.clDB.idRuta)))
            #else:
            except:
                print ("INSERT INTO validador(idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado, recorrido, vuelta, idRuta) values (?, ?, 77, ?, ?, ?, ?, ?, 0, 0, 0, 0)",(str(self.valoresCard.get("nomTipoTar")), self.clDB.idUnidad, self.parent.idOperador, str(self.valoresCard.get("csn")), saldo, tarifa, fechaHora, str(folio)))
                self.clDB.dbAforo.execute("INSERT INTO validador(idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado, recorrido, vuelta, idRuta) values (?, ?, 77, ?, ?, ?, ?, ?, 0, 0, 0, 0)",(str(self.valoresCard.get("nomTipoTar")), self.clDB.idUnidad, self.parent.idOperador, str(self.valoresCard.get("csn")), saldo, tarifa, fechaHora, str(folio)))
            self.clDB.dbAforo.commit()
            self.clquectel.aforo = True
            self.parent.flSendAforo = True
            return True
        else:
            print 'No se hizo la transacion avisar al usuario del aforo normal'
            self.parent.stMsgVigencia = ""
            if (len(stRead) == 19):
                self.msgError(stRead[14:17], "001", str(self.valoresCard.get("csn")))
            else:
                self.msgError("005","001",str(self.valoresCard.get("csn")))
            return False

    def PeriodoPreferencial5Mins(self, csn):
        c = self.clDB.dbAforo.cursor()
        c.execute("SELECT fechaHora FROM validador WHERE csn = '"+csn+"' order by fechaHora DESC LIMIT 1")
        data = c.fetchone()
        if data is None:
            result = True
        else:
            tsDel = datetime.strptime(data[0],'%Y-%m-%d %H:%M:%S')
            tsAl = datetime.strptime(time.strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')
            td = tsAl - tsDel
            result = int(round(td.total_seconds() / 60)) > 5  
        c.close
        return result
       
    def PeriodoPreferencial(self, csn):
        c = self.clDB.dbAforo.cursor()
        c.execute("SELECT idValidador FROM validador WHERE csn = '"+csn+"' and recorrido = "+str(self.parent.idRecorrido)+" and vuelta = "+str(self.parent.noVuelta)+" and idRuta = "+str(self.clDB.idRuta))
        data = c.fetchone()
        if data is None:
            result = True
        else:
            result = False
        c.close
        return result

    def dias(self, stDia):
        hoy = date.today()
        #if True:
        try:
            vig = date(int('20'+stDia[0:2]), int(stDia[2:4]), int(stDia[4:6]))
            dias = (vig - hoy).days
        #else:
        except:
            dias = None
        return dias
        
    def cobrar(self, datos):
        print 'Empiezo el proceso de cobro'
        numError = '0'
        self.parent.stMsgVigencia = ""                                    
        if datos:
            self.valoresCard = self.DatosTISC(datos)
            if datos[0] == "3":
                if self.valoresCard['error']:
                    numError = '601' #'003'
                    self.msgError(numError,'003',str(self.valoresCard.get("csn")))                                  
                    return False
                else:
                    if self.validarListaNegra(self.valoresCard.get("csn")):
                        numError = '602' #'003'
                        self.msgError(numError,'003',str(self.valoresCard.get("csn")))                                  
                        return False
                    else:
                        if (self.valoresCard.get("tarifa") != "00"):
                            #if True:
                            try:
                                tarifa = self.clDB.tarifa[self.valoresCard.get("tarifa")]
                                #print self.clDB.tarifa[self.valoresCard.get("tarifa")]
                            #else:
                            except:
                                print 'Tarifa no existe en el sistema no se puede cobrar'
                                numError = '603' #'002'
                                self.msgError(numError,'002',str(self.valoresCard.get("csn")))
                                return False
                            if (numError == '0'):
                                cad = self.dias(self.valoresCard.get("caducidad"))
                                if (cad is None):
                                    cad = 100
                                vig = self.dias(self.valoresCard.get("vigencia"))
                                if (cad < 0):
                                    '''
                                    #vigencia = datetime.strptime(time.strftime("%y%m%d"),'%y%m%d')
                                    vigencia  = int(time.strftime("%y%m%d"))
                                    caducidad =  int(self.valoresCard.get("caducidad")) - vigencia
                                    if (caducidad < 0):
                                    '''
                                    print "Sin caducidad"
                                    numError = '607' #'005'
                                    self.msgError(numError,'005',str(self.valoresCard.get("csn")))                                  
                                    return False
                                else:
                                    if (self.valoresCard.get("tarifa") == "03"):
                                        vig = 100
                                    else:
                                        c = self.clDB.dbVigencias.cursor()
                                        c.execute("SELECT vigencia FROM vigencia WHERE csn = '"+str(self.valoresCard.get("csn"))+"'")
                                        data = c.fetchone()
                                        if data is None:
                                            if (vig is None):
                                            #if (self.valoresCard.get("vigencia") == "" or self.valoresCard.get("vigencia")[0] == '\x00'):
                                                vig = 100
                                                print "TISC No vigente = 100"
                                            #    numError = '604' #'005'
                                            #    self.msgError(numError,'005',str(self.valoresCard.get("csn")))                                  
                                            #    return False
                                            #else:
                                            #    vig =  dias(int(self.valoresCard.get("vigencia")) - vigencia
                                        else:
                                            vig = self.dias(data[0])
                                        c.close
                                    saldo = int(self.valoresCard.get('saldo'))+int(self.valoresCard.get('saldoV'))
                                    tipoTarjeta = self.valoresCard.get("nomTipoTar")
                                    print "Tipo Tarj:", self.valoresCard.get("nomTipoTar"), "Tarifa: ", self.valoresCard.get("tarifa"), "Vig:", vig
                                    if (vig < 0):
                                        tarifa = self.clDB.tarifaNormal
                                        tipoTarjeta = "NO"
                                        self.parent.stMsgVigencia = "Tarifa Preferencial\nha Vencido"
                                    else:
                                        #tarifa = self.clDB.tarifa[self.valoresCard.get("tarifa")]
                                        if (vig <= 15):
                                            self.parent.stMsgVigencia = "En "+str(vig)+" dias Vence \nTarifa Preferencial"
                                    if (saldo < tarifa):
                                        saldo = saldo / 100.0
                                        self.parent.stSaldoInsuficiente = str("$ %.2f" % saldo)
                                        #if (vigencia < 0):
                                        #    self.parent.stMsgVigencia = "Tarifa Preferencial\nha Vencido"
                                        numError = '605' #'004'
                                        self.msgError(numError,'004',str(self.valoresCard.get("csn")))
                                        return False
                                    else:
                                        #if (self.parent.idRecorrido != 0):
                                        #    TISC_Usada = self.PeriodoPreferencial(self.valoresCard.get("csn"))
                                        #else:
                                        #    TISC_Usada = self.PeriodoPreferencial5Mins(self.valoresCard.get("csn"))
                                        TISC_Usada = self.PeriodoPreferencial5Mins(self.valoresCard.get("csn"))
                                        if ((tarifa < self.clDB.tarifaNormal) and (not TISC_Usada)):
                                            print 'Tarjeta con Tarifa Preferencial Excede el Tiempo Minino'
                                            self.parent.stMsgVigencia = ""
                                            numError = '606' #'006'
                                            self.msgError(numError,'006',str(self.valoresCard.get("csn")))                                  
                                            return False
                                        else:
                                            saldo = saldo - tarifa
                                            #if True:
                                            if self.parsearSaldoCobrar(str(saldo), tarifa):
                                                self.parent.TISC = self.PathTISC(self.valoresCard.get("csn"))
                                                saldo = saldo / 100.0
                                                if ((self.valoresCard.get("nomTipoTar") == "PP") or (self.valoresCard.get("nomTipoTar") == "PG")):
                                                    self.parent.stImgTarjeta = '/home/pi/innobusmx/data/img/imgTarjetas/NO.jpg'
                                                else:
                                                    self.parent.stImgTarjeta = '/home/pi/innobusmx/data/img/imgTarjetas/'+tipoTarjeta+'.jpg'
                                                self.parent.stSaldo = str("$ %.2f" % saldo)
                                                self.parent.stNombre = self.valoresCard.get("nombre").decode('latin-1')
                                                self.parent.stApellido = self.valoresCard.get("apellido").decode('latin-1')
                                                time.sleep(3)
                                                self.parent.stImgTarjeta = ''
                                                self.parent.TISC = ""
                                                self.parent.stSaldo = ""
                                                self.parent.stNombre = ""
                                                self.parent.stApellido = ""
                                                self.parent.stMsgVigencia = ""                                    
                                                return "OK"
            if datos[0] == "0":
                self.parent.stCSN = self.valoresCard.get("csn")
                self.parent.stPathTISC = self.PathTISC(self.valoresCard.get("csn"))
                self.parent.stNombre = "" #self.valoresCard.get("nombre")
                self.parent.stApellido = "" #self.valoresCard.get("apellido")
                #self.parent.stNIP = self.valoresCard.get("NIP")
                #self.parent.stId = self.valoresCard.get("id")
                self.parent.stNIP = "0000"
                self.parent.stId = "77"
                if(self.valoresCard.get("nomTipoTar") == 'KI'):
                    print "Operador"
                    self.parent.flOperador = True
                    self.parent.flDespachador = False
                    self.parent.stNombreO = self.valoresCard.get("nombre").decode('latin-1')
                    self.parent.stApellidoO = self.valoresCard.get("apellido").decode('latin-1')
                    self.parent.stOperador = self.valoresCard.get("nombre").decode('latin-1')+" "+self.valoresCard.get("apellido").decode('latin-1')
                    self.parent.stCSNO = self.valoresCard.get("csn")
                if(self.valoresCard.get("nomTipoTar") == 'DE'):
                    print "Despachador"
                    self.parent.stCSND = self.valoresCard.get("csn")
                    self.parent.flOperador = False
                    self.parent.flDespachador = True
                    self.parent.stNombreD = self.valoresCard.get("nombre").decode('latin-1')
                    self.parent.stApellidoD = self.valoresCard.get("apellido").decode('latin-1')
                                
        print 'Termine el proceso de pago'
        return True


#!/usr/bin/python
# -*- coding: utf-8 -*-

#import threading
import time
import serial
from PyQt4 import QtCore
import os
import datetime
#from ClMifare import clMifare
import RPi.GPIO as GPIO
#from ClSMS import clSMS
import variables_globales as vg
from alttusDB import insertar_estadisticas_alttus

class clSerial(QtCore.QThread):
    sPort = '/dev/ttyUSB_1'
    sPort3G = '/dev/ttyUSB_0'
    #sPort = ''
    #sPort3G = ''
    velocidad = 115200
    ser = None
    ser3G = None
    bSetup = False

    def __init__(self, parent, clDB):
        self.clDB = clDB
        self.parent = parent
        QtCore.QThread.__init__(self)
        self.parent.smsEnabled = False
        self.parent.sendData = False
        self.parent.flQuectel = False
        self.parent.flGPSOK = False
        self.parent.flSocket = False
        self.parent.locked = False
        self.parent.rdy = False
        
    def run(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(8,GPIO.OUT)
        GPIO.setup(24,GPIO.OUT)
        GPIO.output(8,GPIO.HIGH)
        GPIO.output(24,GPIO.HIGH)

    def printDebug(self,msg):
        return
        print "  ", datetime.datetime.now().strftime("%H:%M:%S"), msg
        
    def open3G(self):
        smsEnabled = self.parent.smsEnabled
        flQuectel = self.parent.flQuectel
        flGPSOK = self.parent.flGPSOK
        flSocket = self.parent.flSocket
        flLocked = self.parent.locked

        self.parent.smsEnabled = False
        self.parent.flQuectel = False
        self.parent.flGPSOK = False
        self.parent.flSocket = False
        self.parent.locked = True
        self.parent.iComm = 0
        #print '****************************Abriendo Modem 3G'
        while True:
            #if True:
            try:
                self.ser3G = serial.Serial(self.sPort3G, self.velocidad, timeout=1)
                self.ser3G.flushInput()
                self.ser3G.flushOutput()
                self.parent.smsEnabled = smsEnabled
                self.parent.flQuectel = flQuectel
                self.parent.flGPSOK = flGPSOK
                self.parent.flSocket = flSocket
                self.parent.locked = flLocked
                print 'Modem 3G ------ OK *********************'
                break
            #else:
            except Exception, e:
                print "\x1b[1;31;47m"+"No se pudo abrir el puerto 3G: " + str(e)+"\033[0;m"
                #print 'Modem 3G ------ waitting 1 sec *********************'
                time.sleep(1)

    def close3G(self):
        print '****************************Cerrando Modem 3G'
        #if True:
        try:
            self.ser3G.flushInput()
            self.ser3G.flushOutput()
            self.ser3G.close()
            print "3G Cerrado OK"
        #else:
        except:
            print "Error al Cerrar puerto 3G"
        self.ser3G = None
        return None

    def write3G(self, cmd):
        while True:
            #if True:
            try:
                self.ser3G.write(cmd.encode())
                break
            #else:
            except Exception, e:
                print "\x1b[1;31;47m"+"No se pudo escribir en el puerto 3G: " + str(e)+"\033[0;m"
                self.printDebug(self.parent.RED+self.parent.REVERSE+'###      ERROR: Write3G        ###'+self.parent.RESET)
                time.sleep(1)
                self.open3G()

    def readln3G(self):
        #if True:
        try:
            st = self.ser3G.readline()
            self.parent.rdy = ((st.find("RDY") != -1) or (st.find("+PACSP1") != -1) or (st == "AT+")) or self.parent.rdy
        #else:
        except Exception, e:
            vg.modem_reiniciado = True
            print "\x1b[1;31;47m"+"No se pudo leer el puerto 3G: " + str(e)+"\033[0;m"
            self.printDebug(self.parent.RED+self.parent.REVERSE+'###      ERROR: Readln3G        ###'+self.parent.RESET)
            time.sleep(1)
            self.open3G()
            st  = ""
        return st


    def read3G(self, size):
        #if True:
        try:
            st = self.ser3G.read(size)
        #else:
        except:
            self.printDebug(self.parent.RED+self.parent.REVERSE+'###      ERROR: Read3G        ###'+self.parent.RESET)
            self.open3G()
            st = ""
        return st

    def write(self, cmd, answer, attempts):
        while True:
            intentos = 0
            stRead = ""
            stReadAnt = ""
            self.printDebug("Tx >>>> "+cmd+"\r")
            answer += ("incoming full","ERROR","closed")
            self.write3G(cmd)

            #if (self.parent.waitting):
            #    print "Waitting......."
            #    time.sleep(5)            


            find = False
            while (not find and intentos < attempts) or (self.ser3G.inWaiting() > 0):
                stRead += self.readln3G()           
                for  j in answer:
                    if ( stRead.find(j) != -1):
                        find = True
                        break
                if (len(stRead) == len(stReadAnt)):
                    intentos += 1
                else:
                    intentos = 0        
                stReadAnt = stRead
            if (intentos != attempts):
                break
            elif self.parent.sendData:
                break
            else:
                self.printDebug(self.parent.RED+"Error stRead."+stRead+".("+str(intentos)+"/"+str(attempts)+")"+self.parent.RESET)
                self.write3G(b"+++\x1B\r")
                time.sleep(1)            
                self.ser3G.flushInput()
                self.ser3G.flushOutput()
                self.write3G(cmd)
        if (intentos == attempts):    
            self.printDebug(self.parent.RED+"stRead ("+str(intentos)+"/"+str(attempts)+")"+self.parent.RESET)
        else:
            self.printDebug("stRead ("+str(intentos)+"/"+str(attempts)+")")
        st = " ".join(stRead.split())
        st = " ".join(st.split("\x1A"))
        self.printDebug(st)
        return stRead

    def setup3G(self):
        self.printDebug('###           Buscando Puerto 3G '+self.sPort3G+'      ###')
        if (self.ser3G):
            self.close3G()
        self.printDebug(self.parent.CYAN+'Abriendo Puerto 3G '+self.sPort3G+self.parent.RESET)
        self.parent.lblError.setText("Abriendo Puerto 3G")
        self.open3G()
        print "3G: " + self.sPort3G
        self.parent.lblError.setText("")
        self.parent.flQuectel = True
        self.parent.smsEnabled = True
        return self.ser3G

    def openRFID(self, seg):
        print '****************************Abriendo Puerto RFID'
        while True:
            #if True:
            try:
                if (seg == 0):
                    self.ser = serial.Serial(self.sPort, self.velocidad)
                else:
                    self.ser = serial.Serial(self.sPort, self.velocidad, timeout=seg)                    
                time.sleep(5)  # Esperar a que reinicie el FTDI
                self.ser.flushInput()
                self.ser.flushOutput()
                break
            #else:
            except:
                time.sleep(1)

    def closeRFID(self):
        print '****************************Cerrando Puerto RFID'
        #if True:
        try:
            self.ser.flushInput()
            self.ser.flushOutput()
            self.ser.close()
            print "RFID Cerrado OK"
        #else:
        except:
            print "Error al Cerrar puerto RFID"
        self.ser = None
        return None

    def writeRFID(self, cmd):
        while True:
            #if True:
            try:
                self.ser.write(cmd.encode())
                break
            #else:
            except:
                self.printDebug(self.parent.RED+self.parent.REVERSE+'###      ERROR: Write RFID        ###'+self.parent.RESET)
                time.sleep(1)
                self.openRFID(0)

    def readlnRFID(self):
        st = ""
        #if True:
        try:
            st = self.ser.readline()
        #else:
        except:
            self.printDebug(self.parent.RED+self.parent.REVERSE+'###      ERROR: Readln RFID        ###'+self.parent.RESET)
            time.sleep(1)
            self.openRFID(0)
        return st

    def readRFID(self, size):
        st = ""
        #if True:
        try:
            st = self.ser.read(size)
        #else:
        except:
            self.printDebug(self.parent.RED+self.parent.REVERSE+'###      ERROR: Read RFID        ###'+self.parent.RESET)
            self.openRFID(0)
        return st

    def RFIDwrite(self, cmd, attempts):
        while True:
            intentos = 0
            stReadAnt = ""
            stRead = ""
            self.printDebug("Tx RFID >>>> "+cmd+"\r")
            self.writeRFID(cmd.encode())
            while (stRead == "" and intentos < attempts):
                stRead += self.readlnRFID()
                #print "stRead",stRead
                if (len(stRead) == len(stReadAnt)):
                    intentos += 1
                else:
                    intentos = 0        
                stReadAnt = stRead
            if (intentos != attempts):
                break
        self.printDebug("stRead ("+str(intentos)+"/"+str(attempts)+") " + stRead)
        return stRead

    def setupRFID(self):
        if self.parent.updateFirmware:
            print '###           Actualizando Firmware       ###', datetime.datetime.now().strftime("%H:%M:%S")
            return
        self.parent.flRFID = False
        while (not self.parent.flRFID):
            self.parent.version = ""
            self.parent.serialNumber = ""
            self.printDebug(self.parent.CYAN + '###           Buscando Puerto RFID ' + self.sPort + '      ###' + self.parent.RESET)
            if (self.ser):
                self.printDebug(self.parent.CYAN + 'Cerrando Puerto RFID ' + self.sPort + self.parent.RESET)
                self.closeRFID()
            self.parent.lblError.setText("Buscando Puerto RFID")
            self.printDebug(self.parent.CYAN + 'Abriendo Puerto RFID ' + self.sPort + self.parent.RESET)
            self.openRFID(1)
            self.printDebug(self.parent.CYAN + "Buscando NS Tablilla" + self.parent.RESET)
            st = self.RFIDwrite(b's',5)
            self.printDebug(self.parent.CYAN + "NS: " + st + self.parent.RESET)
            if (len(st) == 12) and (st.find("Ix") != -1 or st.find("In") != -1):
                self.parent.serialNumber = st[:-2]
                self.printDebug(self.parent.CYAN + "Buscando Version" + self.parent.RESET)
                st = self.RFIDwrite(b'v',5)
                self.parent.version = st[:-2]
                self.printDebug(self.parent.CYAN + "version: " + self.parent.version + self.parent.RESET)
                self.closeRFID()
                self.printDebug(self.parent.CYAN + "Asignando puerto RFID " + self.sPort + self.parent.RESET)
                self.openRFID(0)
                self.parent.flRFID = ((len(st) > 3) and st[0] == "v")
        self.parent.serialNumber = self.parent.serialNumber.split("\r\n")[0]
        self.parent.version = self.parent.version.split("\r\n")[0]
        print "RFID: " + self.sPort
        print "SN: ",self.parent.serialNumber
        print "ver: ",self.parent.version
        self.parent.lblNS.setText("NS:"+self.parent.serialNumber)
        self.parent.lblNSFirmware.setText(self.parent.version+"   "+self.parent.cpuSerial)
        self.parent.lblError.setText("")
        fecha_actual = datetime.date.today()
        hora_actual = datetime.datetime.now().time()
        insertar_estadisticas_alttus(str(self.clDB.economico), self.clDB.idTransportista, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), "NST", str(self.parent.serialNumber)) # Numero de serie de tablilla
        insertar_estadisticas_alttus(str(self.clDB.economico), self.clDB.idTransportista, fecha_actual.strftime("%Y-%m-%d"), hora_actual.strftime("%H:%M:%S"), "VT", str(self.parent.version)) # Version de la tablilla

        c = self.clDB.dbListaNegra.cursor()
        c.execute("SELECT csn FROM csn where csn = '"+self.parent.serialNumber+"'")
        data = c.fetchone()
        if data:
            print "En lista Negra"
            os.system("sudo shutdown 0")
        return self.ser



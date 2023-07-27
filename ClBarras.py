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

class clBarras(QtCore.QThread):
    debug = 1
    
    
    def __init__(self, parent, clDB):
        QtCore.QThread.__init__(self)
        self.parent = parent
        self.clDB = clDB


    def printDebug(self,msg):
	return
        if self.debug == 1:
            print datetime.datetime.now().strftime("%H:%M:%S")
            print msg
        if self.debug == 2:
            stRead = self.sendData('d,'+str(self.clDB.idTransportista)+','+str(self.clDB.idUnidad)+','+str(time.strftime("%Y-")+time.strftime("%m")+time.strftime("-%d %H:%M:%S"))+","+msg+"\n")
   
    def Barras(self):
      #if True:
      try:  
        c = self.clDB.dbAforo.cursor()
        c.execute("SELECT idBarra, puerta, direccion, duracion, fechaHora FROM barras WHERE enviado = 0 ORDER BY fechaHora LIMIT 1")
        dataBarras = c.fetchone()
        c.close()
                    
        if not (dataBarras is None):
             self.printDebug('### Si hay subidas y bajadas ###')
             c = self.clDB.dbMensajes.cursor()
             c.execute("SELECT MAX(idEnvio) FROM envio WHERE app = 1")
             data = c.fetchone()
             if (data[0] is None):
                        i = "1"
             else:
                i = str(data[0]+1)
             c.close
             stB = "2,0,"+str(self.clDB.idUnidad)+",0,"+str(dataBarras[3])+","+str(dataBarras[1])+","+str(dataBarras[2])+","+str(dataBarras[4])
             print stB
             self.clDB.dbMensajes.execute("INSERT INTO envio (idEnvio, app, msg, envio) VALUES ("+i+",1,"+"'"+stB+"',0)")
             self.clDB.dbMensajes.commit()
             self.printDebug('###  BORRANDO BARRAS ###')
             self.clDB.dbAforo.execute('DELETE FROM barras WHERE idBarra ='+str(dataBarras[0]))
             self.clDB.dbAforo.commit()
             
             self.parent.flSendEnvio = True   
        
        #~ barras2
        c = self.clDB.dbAforo.cursor()    
        c.execute("SELECT idBarra, puerta, direccion, duracion, fechaHora FROM barras2 WHERE enviado = 0 ORDER BY fechaHora LIMIT 1")
        dataBarras = c.fetchone()
        c.close()
                    
        if not (dataBarras is None):
             self.printDebug('### Si hay subidas y bajadas ###')
             c = self.clDB.dbMensajes.cursor()
             c.execute("SELECT MAX(idEnvio) FROM envio WHERE app = 1")
             data = c.fetchone()
             if (data[0] is None):
                        i = "1"
             else:
                i = str(data[0]+1)
             c.close
             stB = "2,0,"+str(self.clDB.idUnidad)+",0,"+str(dataBarras[3])+","+str(dataBarras[1])+","+str(dataBarras[2])+","+str(dataBarras[4])
             print stB
             self.clDB.dbMensajes.execute("INSERT INTO envio (idEnvio, app, msg, envio) VALUES ("+i+",1,"+"'"+stB+"',0)")
             self.clDB.dbMensajes.commit()
             self.printDebug('###  BORRANDO BARRAS ###')
             self.clDB.dbAforo.execute('DELETE FROM barras2 WHERE idBarra ='+str(dataBarras[0]))
             self.clDB.dbAforo.commit()
             
             self.parent.flSendEnvio = True
        self.ModuloBarras = True

      #else:
      except:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print "Fallas en Modulo Barras"
                self.ModuloBarras = False


    

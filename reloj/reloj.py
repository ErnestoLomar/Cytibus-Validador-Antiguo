# -*- coding: utf-8 -*-

import sys, time

from PyQt4 import QtCore, QtGui, Qt
from PyQt4.uic import *
import sqlite3


cdDb = '/home/pi/innobusmx/data/db/gps'


class reloj(QtGui.QMainWindow):
    def __init__(self, parent=None):
        locale=unicode(QtCore.QLocale.system().name())
        QtGui.QWidget.__init__(self, parent)
        self.ui=loadUi("reloj.ui",self)
        self.mostrarHora()
        
    def mostrarHora(self):
        self.ui.label.setText(time.strftime("%H:%M:%S"))
        conn = sqlite3.connect(cdDb)
        c = conn.cursor()
        c.execute(" SELECT fecha, hora, latitud, longitud, velocidad, idPos, idCons \
                            FROM tgps \
                            WHERE enviado = 0 \
                            ORDER BY hora DESC LIMIT 1;")
        datosGPS = c.fetchone()
        #c.close()
        #conn.close()
        QtCore.QTimer.singleShot(1000, self.mostrarHora)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    
    myapp = reloj()
    myapp.show()
    
    sys.exit(app.exec_())

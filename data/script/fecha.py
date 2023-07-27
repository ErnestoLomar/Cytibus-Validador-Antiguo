from PyQt4 import QtGui
from time import strftime


class Fecha():
    def __init__(self, parent):
        self.lblHora = QtGui.QLabel(time.strftime("%d-%m-%Y %H:%M:%S"), self)
        self.lblHora.resize(self.width(), 50)
        self.lblHora.move(10, 440)
        self.lblHora.setStyleSheet('QLabel { font-size: 14pt; font-family: \
            Arial; color:White}')
        while (True):
            self.parent.lblHora.setText("Intenta de nuevo")
            time.sleep(1)
            
        

obj = Fecha()



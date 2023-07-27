#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui, QtCore
import sqlite3

class Example(QtGui.QWidget):

    def __init__(self):

        super(Example, self).__init__()
        self.initUI()

    def initUI(self):

        self.dbAforo = '/home/hiram/Documentos/innobusvalidador/data/db/aforo'
        self.lbl = QtGui.QLabel('Ingresa nuevo numero:',self)
        self.qle = QtGui.QLineEdit(self)

        btn = QtGui.QPushButton('Guardar', self)
        btn.resize(btn.sizeHint())
        btn.clicked[bool].connect(self.actualizar)

        self.qle.move(60, 30)
        self.lbl.move(60, 10)
        btn.move(90, 80)

        self.setGeometry(300, 300, 270, 130)
        self.setWindowTitle('Actualizar')
        self.show()

    def actualizar(self):

        telAc = self.qle.text()
        print telAc
        punInteres = 'C4'
        conn = sqlite3.connect(self.dbAforo)
        c = conn.cursor()
        c.execute("UPDATE numTelefono SET telefono = ? WHERE puntoInteres = ?\
            ", (str(telAc), str(punInteres)))
        conn.commit()
        #print text


def main():

    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

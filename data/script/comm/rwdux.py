#!/usr/bin/python
# -*- coding: utf-8 -*-

import serial
import subprocess

'''
        ##############################################################
                                 rwdux
                         create by: Hiram Zuniga
                              13-abr-2016
        ##############################################################

        ##############################################################
            Lista negra ya solo falta la parte del servidor
            Falta validar el tipoTarifa
        ##############################################################

'''

# /dev/ttrUSB0 es para gprs en la pc lo apago
sPort = '/dev/ttyUSB1'
velocidad = 9600

serialGPS = serial.Serial(sPort, velocidad,  timeout=1)
paso = 0

print '#############################################'
print '### Iniciando el modulo de comunicaciones ###'
print '###                v0.01                  ###'
print '#############################################'

ini = ''
print '###             Iniciando GPS             ###'
while (ini != 'AT+CGPSPWR=1 OK'):
    cmd = "AT+CGPSPWR=1\r"
    serialGPS.write(cmd.encode())
    inigps = serialGPS.read(64)
    inigp = inigps.rstrip()
    ini = " ".join(inigp.split())
    #print(ini)
    paso = paso + 1
    if (paso == 3):
        print '###       El Gps ya esta encendido        ###'
        ini = 'AT+CGPSPWR=1 OK'
        paso = 0

print '###           Reiniciando GPS             ###'
rgps = 'AT+CGPSRST=0 ERROR'
while (rgps == 'AT+CGPSRST=0 ERROR'):
    cmd = "AT+CGPSRST=0\r"
    serialGPS.write(cmd.encode())
    resetgps = serialGPS.read(64)
    rgp = resetgps.rstrip()
    rgps = " ".join(rgp.split())
    #print(rgps)

shutgs = ''
print '###Reinicia conexion si hay una existente ###'
while (shutgs != 'AT+CIPSHUT SHUT OK'):
    shutc = "AT+CIPSHUT\r"
    serialGPS.write(shutc.encode())
    shut = serialGPS.read(64)
    shutg = shut.rstrip()
    shutgs = " ".join(shutg.split())
    #print shutgs

statusS = ''
print '###      Satus de la conexion GRPS        ###'
while(statusS != 'AT+CIPSTATUS OK STATE: IP INITIAL'):
    cmd = "AT+CIPSTATUS\r"
    serialGPS.write(cmd.encode())
    status = serialGPS.read(64)
    statusS = " ".join(status.split())
    #print statusS

csttS = ''
print '###Conectandome a la red GPRS del provedor###'
while (csttS != 'AT+CSTT="internet.itelcel.com", "webgprs", "webgprs2002" OK'):
    cmd = 'AT+CSTT="internet.itelcel.com", "webgprs", "webgprs2002"\r'
    serialGPS.write(cmd.encode())
    cstt = serialGPS.read(64)
    csttS = " ".join(cstt.split())
    #print(csttS)

ciirS = ''
print '###     Enecendiendo la antena del GPRS   ###'
while(ciirS != 'AT+CIICR OK'):
    cmd = 'AT+CIICR\r'
    serialGPS.write(cmd.encode())
    ciir = serialGPS.read(64)
    ciirS = " ".join(ciir.split())
    #print(ciirS)
    paso = paso + 1
    if (paso == 3):
        print('La conexion no ha sido posible establecerla')
        ciirS = 'AT+CIICR OK'
        paso = 0

print '###    Opteniendo la IP local asignada    ###'
cmd = 'AT+CIFSR\r'
serialGPS.write(cmd.encode())
cifsr = serialGPS.read(64)
#print cifsr

cipstartS = ''
print '###   Intentando conectar a servidor FTP  ###'
while(cipstartS != 'AT+CIPSTART="TCP","innovaciones.no-ip.org","10000" OK'):
    cmd = 'AT+CIPSTART="TCP","innovaciones.no-ip.org","10000"\r'
    serialGPS.write(cmd.encode())
    cipstar = serialGPS.read(64)
    cipstartS = " ".join(cipstar.split())
    print(cipstartS)

statusS = ''
print '###           Configuracion SMS           ###'
while(statusS != 'AT+CMGF=1 OK'):
    cmd = "AT+CMGF=1\r"
    serialGPS.write(cmd.encode())
    status = serialGPS.read(64)
    statusS = " ".join(status.split())
    #print statusS

print '#############################################'

while True:
    comando = serialGPS.read(64)
    comandoS = comando.rstrip()
    comandoT = " ".join(comandoS.split())
    print 'completo', comandoT
    print 'evaluo',  comandoT[:6]
    #print type(comandoT)
    if str(comandoT[:6]) == '+CMTI:':
        cmd = 'AT+CMGR=%s\r'%str(comandoT[12:14])
        serialGPS.write(cmd.encode())
        mensaje = serialGPS.read(128)
        mensajeS = mensaje.rstrip()
        mensajeT = ",".join(mensajeS.split())
        #print mensajeT
        #print 'tipo del mensje'
        #print type(mensajeT)
        text = mensajeT.split(',')
        print 'Telefono:', text[4]
        print 'Comando', text[8]
        if text[8] == 'IONV':
            print 'Encender pantalla'
            return_code = subprocess.call("sudo echo 0 > /sys/class/backlight/rpi_backlight/bl_power", shell=True)
            cmd = 'AT+CMGD=%s\r'%str(comandoT[12:14])
            serialGPS.write(cmd.encode())
            mensaje = serialGPS.read(128)

        if text[8] == 'IOFV':
            print 'Apagar pantalla'
            return_code = subprocess.call("sudo echo 1 > /sys/class/backlight/rpi_backlight/bl_power", shell=True)
            cmd = 'AT+CMGD=%s\r'%str(comandoT[12:14])
            serialGPS.write(cmd.encode())
            mensaje = serialGPS.read(128)
        else:
            cmd = 'AT+CMGD=%s\r'%str(comandoT[12:14])
            serialGPS.write(cmd.encode())
            mensaje = serialGPS.read(128)

    if str(comandoT[:6]) == 'CLOSED':
        print 'Socket cerrado'
        #print 'Volvere a conectarme solo con lo necesario'
        cipstartS = ''
        print '###   Reintentando conectar a servidor FTP    ###'
        #while(cipstartS != 'AT+CIPSTART="TCP","innovaciones.no-ip.org","10000" OK'):
        cmd = 'AT+CIPSTART="TCP","innovaciones.no-ip.org","10000"\r'
        serialGPS.write(cmd.encode())
        cipstar = serialGPS.readline(64)
        cipstartS = " ".join(cipstar.split())
        #print(cipstartS)
    if str(comandoT[:16]) == 'AT+CIPSEND ERROR':
        print 'No hay comunicacion con el servidor'

    if str(comandoT[:10]) == 'CONNECT OK':
        print 'Volver a realizar la conexion inclutendo el gprs shut'
        print 'No neceito hacer nada solo volver a enviar los datos?'
        #print '###   Reintentando conectar a servidor FTP    ###'
        ##while(cipstartS != 'AT+CIPSTART="TCP","innovaciones.no-ip.org","10000" OK'):
        #cmd = 'AT+CIPSTART="TCP","innovaciones.no-ip.org","10000"\r'
        #serialGPS.write(cmd.encode())
        #cipstar = serialGPS.readline(64)
        #cipstartS = " ".join(cipstar.split())

import serial
from curses import ascii
import time
import sqlite3
import datetime
import subprocess
import os
import base64

#sPort = '/dev/ttyUSB0'
#velocidad = 115200
#ser = serial.Serial(sPort, velocidad, timeout=1)

romper = 0
barraEnvio = 0
controlEnvios = 10
velGPS = 0
idTransportista = 0
idUnidad = 0

sPort = ''
velocidad = 115200
path = "/dev"
while sPort == '':
    listdir = os.listdir(path)
    for file in listdir:
        if (file[0:6] == "ttyUSB"):
            s = serial.Serial("/dev/"+file,velocidad, timeout=1)
            s.flushInput()
            s.flushOutput()
            s.write("AT\r")
            st = s.readline()
            st = st + s.readline()
            st = st + s.readline()
            st = st + s.readline()
            s.close
            if (st != ""):
                sPort = "/dev/"+file
                ser = serial.Serial(sPort, velocidad, timeout=1)
            else:
                time.sleep(4)

print "3G/GPS: "+sPort


'''
        ##############################################################
                                 rwdux3G
                          create by: Hiram Zuniga
                              15-abr-2016
        ##############################################################

        ##############################################################

        ##############################################################
'''

cdDb = '/home/pi/innobusmx/data/db/aforo'
cdDbT = '/home/pi/innobusmx/data/db/gps'
cdDbC = '/home/pi/innobusmx/data/db/comandoComm'
cdDbLn = '/home/pi/innobusmx/data/db/listaNegra'
cdDbF = '/home/pi/innobusmx/data/db/existeFoto'
cdDbA = '/home/pi/innobusmx/data/db/alarmas'
cdDbE =  '/home/pi/innobusmx/data/db/ev2'


class rwsGPS:
    def __init__(self):
        self.inicializarTodo()
        self.actualizarAlgo = '#'
        self.reinicioAutomatico = 0
        self.entrarAccionSiete = 0
        #self.openDBAforo = 'data/db/aforo'
        while(True):
            for i in range(controlEnvios):
                i = i + 1
                self.realizarAccion(i)
            else:
                print '###          Terminando el barrido        ###'
                print '#############################################'
                time.sleep(2)


    def realizarAccion(self, i):
        '''
            ##############################################################
                        Acciones definifidas anteriormente
                        para el envio de informacion al
                        servidor
            ##############################################################
        '''
        accion = i
        print '#############################################'
        print '###     Iniciando el barrido de datos     ###'
        if accion == 1:
            print '###         Obteniendo posicion GPS       ###'
            self.obtenerCoordenadaGPS()
#            estaDetenido = self.validarVelocidad()
#            print 'Aca imprimo el valor de estado detenido'
#            print velGPS
            if velGPS == 0:

                conn = sqlite3.connect(cdDbT)
                c = conn.cursor()
                c.execute(" SELECT fecha, hora, latitud, longitud, velocidad, idPos \
                            FROM tgps \
                            WHERE enviado = 0 \
                            ORDER BY hora DESC LIMIT 1;")
                datosGPS = c.fetchone()

                c.close()
                conn.close()

                if datosGPS is None:
                    print '###     No tengo datos gps por enviar     ###'

                else:
                    print '###    Preparando dato GPS para enviar    ###'
                    fechaT = datosGPS[0]
                    horaT = datosGPS[1]
		    latitudT = datosGPS[2]
                    longitudT = datosGPS[3]
                    velocidadT = datosGPS[4]
                    idpos = datosGPS[5]
                    envio = 1
                    datetimes = fechaT + ' ' + horaT
                    gpr = '1,'+str(self.idTransportista)+','+str(self.idUnidad)+','+str(datetimes)+','+str(latitudT)+','+str(longitudT)+','+str(velocidadT)+'\r'+''
                    salgo = 0
                    #print "GPR: " + gpr
                    self.procesoDeEnvio(gpr, idpos, accion, salgo)
            else:
                print 'Me voy a parar aca x tiempo despues puedo validar de nuevo el km dentro de un while mientras solo lo quiero hacer por tiempo'
                time.sleep(40)

        if accion == 2:
            print '***        Obteniendo dato de barras      ***'
            #2,idTransportista,idUnidad,auxiliar,duracion,puerta,direccion,fecha/hora
            conn = sqlite3.connect(cdDb)
            c = conn.cursor()

            c.execute("SELECT idTransportista, idUnidad FROM configuraSistema")
            data = c.fetchone()
            if data is None:
                print('No hay parametros de configuracon contacta al administrador\
                    ')
            else:
                idTranspor = data[0]
                idUni = data[1]

            c.execute(" SELECT idBarra, auxiliar, duracion, puerta, direccion, fechaHora FROM barras WHERE enviado = 0")
            datosBarra = c.fetchone()
            c.close()

            if datosBarra is None:
                print '###       No hay dato nuevo en barras     ###'
            else:
                print '###              Si hay que enviar        ###'
                idBarras = datosBarra[0]
                auxiliarT = datosBarra[1]
                duracionT = datosBarra[2]
                puertaT = datosBarra[3]
                direccionT = datosBarra[4]
                fechaHoraT = datosBarra[5]
                barraEnvio = 1
                barrasS = '2,'+str(idTranspor)+','+str(idUni)+','+str(auxiliarT)+','+str(duracionT)+','+str(puertaT)+','+str(direccionT)+','+str(fechaHoraT)+'\r'+''
                print '###    Esto es lo  que contiene barras    ###'
                print(barrasS)
                salgo = 0
                self.procesoDeEnvio(barrasS, idBarras, accion, salgo)

        if accion == 3:
            #3,idTipoTisc,idUnidad,idOperador,csn,saldo,tarifa,fecha/hora
            '''
                Agregar aqui el folio para poder enviarlo de nuevo, despues borrar
                este mensaje ya que lo haya agregado
            '''
            print '***     Obteniendo dato de validaciones   ***'
            conn = sqlite3.connect(cdDb)
            c = conn.cursor()
            c.execute(" SELECT idValidador, idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, folios, enviado FROM validador WHERE enviado = 0")
            datosValidador = c.fetchone()
            c.close()

            if datosValidador is None:
                print '###       No hay validaciones nuevas      ###'

            else:
                print '###       Si hay validaciones nuevas      ###'
                idValida = datosValidador[0]
                idTipoT = datosValidador[1]
                idUnid = datosValidador[2]
                #Cambio de idUnidad de a miguel por de a hiram
                #idUnid = 3
                idOper = 4
                csn = datosValidador[4]
                saldo = datosValidador[5  ]
                tarifa = datosValidador[6]
                fechaHora = datosValidador[7]
                folio = datosValidador[8]
                validadorS = '3,'+str(idTipoT)+','+str(idUnid)+','+str(idOper)+','+str(csn)+','+str(saldo)+','+str(tarifa)+','+str(folio)+','+str(fechaHora)+'\r'+''
                print '###      Dato a enviar en validacion      ###'
                print(validadorS)
                salgo = 0
                self.procesoDeEnvio(validadorS, idValida, accion, salgo)

        if accion == 4:
            print '***  Obteniendo dato de recorrido UCSV    ***'
            conn = sqlite3.connect(cdDb)
            c = conn.cursor()
            c.execute(" SELECT idEnvRecorrido, fechaHora, km, idUnidad, idChofer, num_vuelta, recorrido, inicioFin FROM envRecorrido WHERE enviados = 0")
            datosFinRecorrido = c.fetchone()
            c.close()

            if datosFinRecorrido is None:
                print '###        No hay fin de recorridos       ###'
            else:
                print '### Si hay que enviar envio de Recorrido  ###'
                finRecorridoEnvio = 1
                idenvRecorridoE = datosFinRecorrido[0]
                fechaHoraE = datosFinRecorrido[1]
                kmE = datosFinRecorrido[2]
                idUnidadE = datosFinRecorrido[3]
                idChoferE = datosFinRecorrido[4]
                numVueltaE = datosFinRecorrido[5]
                recorridoE = datosFinRecorrido[6]
                inicioFinE = datosFinRecorrido[7]
                finRecorridoS = '4,'+str(fechaHoraE)+','+str(kmE)+','+str(idUnidadE)+','+str(idChoferE)+','+str(numVueltaE)+','+str(recorridoE)+','+str(inicioFinE)+'\r'+''
                print '###  Esto se enviara en fin de recorrido  ###'
                print(finRecorridoS)
                salgo = 0
                self.procesoDeEnvio(finRecorridoS, idenvRecorridoE, accion, salgo)

        if accion == 5:
            '''
            ######################################################################
            #                     Enviando inicio fin chofer                     #
            ######################################################################
            '''
            #5,fechaHora,kilometraje,idUnidad,csn,numVuelta,turo,inFin
            print '***          Inicio o Fin del chofer      ***'
            conn = sqlite3.connect(cdDb)
            c = conn.cursor()
            c.execute("SELECT idSoloVuelta, fechaHora, km, idUnidad, idRuta, csn, num_vuelta, turno, inicioFin FROM soloVuelta WHERE enviados = 0")
            datosSoloVuelta = c.fetchone()
            c.close()

            if datosSoloVuelta is None:
                print '###No hay in fin del chofer UCconValidador###'
            else:
                print '###   Si hay que enviar en in fin chofer  ###'
                finRecorridoEnvio = 1
                idSoloVueltas = datosSoloVuelta[0]
                fechaHoraE = datosSoloVuelta[1]
                kmE = datosSoloVuelta[2]
                idUnidadE = datosSoloVuelta[3]
                idRutaE = datosSoloVuelta[4]
                csnE = datosSoloVuelta[5]
                numVueltaE = datosSoloVuelta[6]
                turnoE = datosSoloVuelta[7]
                inicioFinE = datosSoloVuelta[8]
                finRecorridoS = '5,'+str(fechaHoraE)+','+str(kmE)+','+str(idUnidadE)+','+str(idRutaE)+','+str(csnE)+','+str(numVueltaE)+','+str(turnoE)+','+str(inicioFinE)+'\r'+''
                print '###  Esto se enviara en fin de recorrido  ###'
                print(finRecorridoS)
                salgo = 0
                self.procesoDeEnvio(finRecorridoS, idSoloVueltas, accion, salgo)


        if accion == 6:
                '''
                ######################################################################
                #       Enviando inicio fin de analista solo validador         #
                ######################################################################
                '''
                self.entrarAccionSiete = self.entrarAccionSiete + 1
                conn = sqlite3.connect(cdDb)
                c = conn.cursor()
                c.execute(" SELECT idTurnoDelDia, fechaHora, idUnidad, idRuta, csn, turno, inicioFin FROM turnoDelDia WHERE enviados = 0")
                datosinicioFinTurnoSoloValidador = c.fetchone()

                c.execute("SELECT idRutaActual FROM configuraSistema")
                idRuta = c.fetchone()
                ruta = idRuta[0]

                if datosinicioFinTurnoSoloValidador is None:
                    print '###      No hay fin  de solo validador    ###'
                else:
                    finRecorridoEnvio = 1
                    iddatosinicioFinTurnoSoloValidador= datosinicioFinTurnoSoloValidador[0]
                    fechaHoraE = datosinicioFinTurnoSoloValidador[1]
                    idUnidadE = datosinicioFinTurnoSoloValidador[2]
                    idRutaE = datosinicioFinTurnoSoloValidador[3]
                    csnE = datosinicioFinTurnoSoloValidador[4]
                    turnoE = datosinicioFinTurnoSoloValidador[5]
                    inicioFinE = datosinicioFinTurnoSoloValidador[6]
                    finRecorridoS = '6,'+str(fechaHoraE)+','+str(idUnidadE)+','+str(ruta)+','+str(csnE)+','+str(turnoE)+','+str(inicioFinE)+'\r'+''
                    print '###  Esto se enviara en fin de recorrido  ###'
                    print(finRecorridoS)
                    salgo = 0
                    self.procesoDeEnvio(finRecorridoS, iddatosinicioFinTurnoSoloValidador, accion, salgo)
                    print 'Antes de salirme hare un paso magico para que entre a accion cada'
                    print 'X pasadas que se transormaran en x Tiempo'
                #self.entrarAccionSiete = self.entrarAccionSiete + 1

        if accion == 7:
            '''
            ##################################################
            #                 Lectura de SMS                 #
            ##################################################
            '''
            if self.entrarAccionSiete == 3:
                print '###             Verificando SMSs          ###'
                nSMS = 1
                #cmd = "AT+CMGF=1\r"
                #ser.write(cmd.encode())
                while nSMS < 5:
                    ser.write('AT+CMGR=%s\r'%nSMS)
                    #cmd = 'AT+CMGR=%s\r'%str(comandoT[12:14])
                    comando = ser.read(128)
                    comandoS = comando.rstrip()
                    comandoT = ",".join(comandoS.split())
                    #print 'evaluo',  comandoT[10:16]
                    if str(comandoT[10:16]) == '+CMGR:':
                        text = comandoT.split(',')
                        print 'Text', text
                        try:
                            cmd = text[8]
                            #este pasa cuando hay una actualizacion por lo que
                            #obtendre el comando sin la actualizacion
                            if cmd[:2] == 'IU':
                                print 'Actualizacion de algo'
                                strActualizacion = cmd
                                cmd = cmd[:6]
                                print strActualizacion
                            else:
                                #esto pasa cuando es un comando normal
                                cmd = text[8]
                                strActualizacion = 'nulo'
                        except:
                            print 'Mensaje sms no valido'
                            cmd = 'ERROR'
                            strActualizacion = 'nulo'
                        self.validarComando(cmd, strActualizacion, nSMS)
                    nSMS = nSMS + 1
                self.entrarAccionSiete = 0


        if accion == 8:
                '''
                ######################################################################
                #                Enviando que ya tengo el csn quemado                #
                ######################################################################
                '''
                conn = sqlite3.connect(cdDbLn)
                c = conn.cursor()
                c.execute(" SELECT idNegra, csn FROM negra WHERE enviado = 0")
                datosListaNegra = c.fetchone()

                connn = sqlite3.connect(cdDb)
                cc = connn.cursor()
                cc.execute("SELECT idTransportista, idUnidad FROM configuraSistema")
                data = cc.fetchone()
                if data is None:
                    print('No hay parametros de configuracon contacta al administrador\
                        ')
                else:
                    idUni = data[1]

                if datosListaNegra is None:
                    print '###  No hay nuevos datos en lista negra   ###'
                else:
                    idListaNegra= datosListaNegra[0]
                    csn = datosListaNegra[1]
                    actListaNegra = '8,'+str(csn)+','+str(idUni)+'\r'+''
                    print '###     Esto se enviara en lista negra    ###'
                    print(actListaNegra)
                    salgo = 0
                    self.procesoDeEnvio(actListaNegra, idListaNegra, accion, salgo)

        if accion == 9:
                '''
                ######################################################################
                #              Haciendo la peticion de la foto por gprs              #
                ######################################################################
                '''
                print '###     Esto se enviara en nueva Fotografi                ###'
                '''
                actFoto =  '9,AC7D2AD1\r'
                salgo = 0
                print actFoto
                self.procesoDeEnvioFoto(actFoto, 1, accion, salgo)
                '''

                conn = sqlite3.connect(cdDb)
                c = conn.cursor()
                c.execute("SELECT idTransportista, idUnidad FROM configuraSistema")
                data = c.fetchone()
                if data is None:
                    print('No hay parametros de configuracon contacta al administrador\
                        ')
                else:
                    idUni = data[1]

                connn = sqlite3.connect(cdDbF)
                cc = connn.cursor()

                cc.execute(" SELECT idFotos, csn FROM fotos WHERE enviado = 0")
                datosFotos = cc.fetchone()
                if datosFotos is None:
                    print 'No hay csn almacenados'
                else:
                    idFoto = datosFotos[0]
                    csnFoto  = datosFotos[1]
                    idUnidad = 0
                    #actFoto = '9,'+str(csnFoto)+'\r'+''
                    actFoto = '9,'+str(csnFoto)+','+str(idUnidad)+'\r'+''
                    fotoConfirmar = '9,'+str(csnFoto)+','+str(idUni)+'\r'+''
                    print '###   Esto se enviara en la peticion de la foto    ###'
                    print actFoto
                    salgo = 0
                    self.procesoDeEnvioFoto(actFoto, idFoto, accion, salgo, csnFoto, fotoConfirmar)

        if accion == 10:
                '''
                ######################################################################
                #                Enviando SMS Alarma generada en unidad              #
                ######################################################################
                '''
                conn = sqlite3.connect(cdDbA)
                c = conn.cursor()
                c.execute(" SELECT idSensor, fechaHora FROM sensor WHERE enviado = 0")
                datosSensor = c.fetchone()

                connn = sqlite3.connect(cdDb)
                cc = connn.cursor()
                cc.execute("SELECT idTransportista, idUnidad FROM configuraSistema")
                data = cc.fetchone()
                if data is None:
                    print 'No hay parametros de configuracon contacta al administrador'
                else:
                    idUni = data[1]

                if datosSensor is None:
                    print '###  No hay nuevos datos en lista negra   ###'
                else:
                    idSensorL= datosSensor[0]
                    fechaL = datosSensor[1]
                    actSensor = '10,'+str(idSensorL)+','+str(fechaL)+'\r'+''
                    print '###     Esto se enviara en SMS    ###'
                    print(actSensor)
                    salgo = 0
                    self.procesoDeEnvioSMS(actSensor, idSensorL, salgo)

        if accion == 11:
                '''
                ######################################################################
                #                Enviando que ya tengo el csn quemado                #
                ######################################################################
                '''
                conn = sqlite3.connect(cdDbE)
                c = conn.cursor()
                c.execute(" SELECT iCsn, csn FROM tag WHERE enviado = 0")
                datosEV2 = c.fetchone()

                connn = sqlite3.connect(cdDb)
                cc = connn.cursor()
                cc.execute("SELECT idTransportista, idUnidad FROM configuraSistema")
                data = cc.fetchone()
                if data is None:
                    print 'No hay parametros de configuracon contacta al administrador'
                else:
                    idUni = data[1]

                if datosEV2 is None:
                    print '###  No hay nuevas transacciones de EV2   ###'
                else:
                    idEv2= datosEV2[0]
                    csn = datosEV2[1]
                    actEV2 = '11,'+str(csn)+','+str(idUni)+'\r'+''
                    print '###  Esto se enviara en transacciones EV2 ###'
                    print actEV2
                    salgo = 0
                    self.procesoDeEnvio(actEV2, idEv2, accion, salgo)

        if self.actualizarAlgo != '#':
            print 'Aqui voy a hacer una actualizacion dependiente la accion a realizar'
            print self.actualizarAlgo
            try:
                print  self.actualizarAlgo.split("@")
                dos =  self.actualizarAlgo.split("@")
                print dos[1]
                print dos[2]
                actualizacion = int(dos[1])
                comando = dos[2]

                if actualizacion == 1:
                    ev2Update = comando.find('#')!=-1
                    if ev2Update == True:
                        datosInsertarEV2 = dos[2].split("#")
                        accionEv2 = datosInsertarEV2[0]
                    else:
                        print 'No es nada de la EV2'

                    if accionEv2 == 'a':
                        csnEv2 = datosInsertarEV2[1]
                        nombreEv2 = datosInsertarEV2[2]
                        apellidoEv2 = datosInsertarEV2[3]
                        saldoEv2     = datosInsertarEV2[4]
                        tipoTarjetaEv2 = datosInsertarEV2[5]
                        tipoTarifaEv2 = datosInsertarEV2[6]
                        self.nuevaEv2Inicializada(csnEv2, nombreEv2, apellidoEv2, saldoEv2, tipoTarjetaEv2, tipoTarifaEv2)
                    if accionEv2 == 'b':
                        csnEv2 = datosInsertarEV2[1]
                        saldoEv2 = datosInsertarEV2[2]
                        self.recargaEv2(csnEv2, saldoEv2)

                if actualizacion == 8:
                    conn = sqlite3.connect(cdDbLn)
                    c = conn.cursor()
                    c.execute("SELECT csn FROM negra WHERE csn = ?",(str(comando), ))
                    data = c.fetchone()
                    if data is None:
                        print 'Voy a meter la tarjeta a lista negra'
                        #INSERT INTO soloVuelta(fechahora, km, idUnidad, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?,? ,?), ('esta-siempre-va', 0, 0, 00000000, 0, 'M','F', 1);
                        c.execute("INSERT INTO negra(csn, enviado) VALUES(?,?)", (str(comando), 0))
                        conn.commit()
                        c.close()
                    else:
                        print 'Ya no la meto ya existe'

                if actualizacion == 9:
                    conn = sqlite3.connect(cdDbF)
                    c = conn.cursor()
                    c.execute("SELECT csn FROM fotos WHERE csn = ?",(str(comando), ))
                    data = c.fetchone()
                    if data is None:
                        print 'Voy a meter la foto nueva a la base de datos de fotos'
                        #INSERT INTO soloVuelta(fechahora, km, idUnidad, csn, num_vuelta, turno, inicioFin, enviados) VALUES(?, ?, ?, ?, ?, ?,? ,?), ('esta-siempre-va', 0, 0, 00000000, 0, 'M','F', 1);
                        c.execute("INSERT INTO fotos(csn, enviado) VALUES(?,?)", (str(comando), 0))
                        conn.commit()
                        c.close()
                    else:
                        print 'Ya no la meto ya existe'
            except:
                print 'No pude parsear la actualizacion'
            #reinicio la variable para volver a cacharla
            self.actualizarAlgo = '#'




    def validarVelocidad(self):
        '''
            ##############################################################
                Modulo que obteniene la coordenada GPS la guarda cuando
                el GPS se establece de manera correcta.
            ##############################################################
        '''
        print 'Estoy dentro de validar la velocidad'
        detenido = False
        cmd = 'AT+QGPSLOC=0\r' 
        ser.write(cmd.encode())
        stRead = ""
        while (stRead[-2:] != "OK") and not ((stRead[-3:] >= "501") and (stRead[-3:] <= "549")):
            stRead += str(ser.read(1))
        print "QGPSLOC: "+stRead
        if(stRead[-2:] == "OK"):
            #try:
                my_list = stRead.split(",")
                # 1 Hora  (hh-mm-ss)
                # 3 Norte
                # 5 Sur
                # 7 velocidad
                # 9 Fecha (dd-mm-aa)
                horas = my_list[0]
		horas[25:0]

                latituds = my_list[1] #tomo el valor de la lista 
		latitud = list(latituds) # se crea una lista con dicho valor 
		posNegLat = ''.join(latitud[0:9]) #Se elimina la letra del valor 
		
		longituds = my_list[2] #tomo el valor de la lista 
		longitud = list(longituds) #se crea una lista con dicho valor 
		posNegLong = "-"+''.join(longitud[0:10]) #Se elimina la letra del valor 
		
                velocidada = my_list[7] #tomo el valor de la lista 
                fechas = my_list[9]  #tomo el valor de la lista 

                antes = list(horas)
                idHora = ''.join(antes[25:31])
                antesDia = list(fechas)
                idDia = ''.join(antesDia[0:2])
                idInser = idDia + idHora
                enviados = 0

                velocidadFlo = float(velocidada)
                velocidadKmf = ((velocidadFlo * 1.85200) / (1))
                velocidadKm = int(velocidadKmf)

                fechasF = datetime.datetime.strptime(fechas, "%d%m%y").strftime("%Y-%m-%d")

               	horasL = list(horas)
		hor = ''.join(horasL[25:27])
		minu = ''.join(horasL[27:29])
		seg = ''.join(horasL[29:31])
		horasFF = (hor+':'+minu+':'+seg)
		

                latitudL = list(latituds)
                horasLa = ''.join(latitudL[0:2])
                horasLaF = float(horasLa)
                minuLa = ''.join(latitudL[2:9])
                minuLaF = float(minuLa)
                minSegLa = minuLaF / 60
                coorLa = horasLaF + minSegLa
                coorLaD = ("%.6f" % coorLa)

                print '### Validar si el autobus esta andando    ###'
                if velocidadKm == 0:
                    #modificar a True cuando la prueba local de descarga de foto se acaba
                    detenido = False
                else:
                    detenido = False

                if (my_list[2] != "ERROR 516"):
                    print '###          Dato GPS aun no valido       ###'
                else:
                    print '###       Dato valido pero esta en 0      ###'

            #except:
                 #print '###   GPS fallo el parseo del dato   ###'
        else:
            print '###            Modulo gps fallando        ###'

        return detenido

    def procesoDeEnvioSMS(self, dato, idActualizar, salgo):
        print '###        Proceso de envio de SMS        ###'
        '''
            Preparar el mensaje que se enviara con la sig estructura
            Alarma: Boton de Panico Unidad
        '''
        comando = 'C4'
        conn = sqlite3.connect(cdDb)
        c = conn.cursor()
        c.execute("SELECT telefono FROM numTelefono WHERE puntoInteres = ?",(str(comando), ))
        data = c.fetchone()

        cmd = 'AT+CMGS=\"'+data[0]+'\"\r'
        ser.write(cmd.encode())
        time.sleep(1)
        send = ser.readline(64)
        ser.write("Alarma: Boton de panico unidad\r")
        time.sleep(1)
        send = ser.readline(64)
        ser.write(ascii.ctrl('z'))
        send = ser.readline(64)
        cambio = '1'
        conn = sqlite3.connect(cdDbA)
        c = conn.cursor()
        c.execute("UPDATE sensor SET enviado = ? WHERE idSensor = ?\
            ", (cambio, idActualizar))
        conn.commit()
        '''
            Esta parte es como una forma de solo para enviar el
            mensaje cada que presionen el boton de panico a las
            unidades
            Tel: 4442995551
            Solo es para darle un poco de tiempo y pueda enviarse
            un nuevo mensaje SMS a un numero diferente al dado por
            la base de datos
        '''
        time.sleep(4)
        cmd = 'AT+CMGS=\"4442995551"\r' ''' Aqui se coloca el numero donde se va a mandar el mensaje'''
        print cmd
        ser.write(cmd.encode())
        time.sleep(1)
        send = ser.readline(64)
        print send
        ser.write("Alarma: Boton de panico unidad\r")
        time.sleep(1)
        send = ser.readline(64)
        print send
        ser.write(ascii.ctrl('z'))
        send = ser.readline(64)
        print send

    def procesoDeEnvioFoto(self, dato, idActualizar, accion, salgo, csnFoto, fotoConfirmar):
        print 'Retardo de 8 segundos en una para que se descargue la madre de foto'
        time.sleep(8)
        print 'Descargando.. cha cha cha channnnnnnn'
        print '###       Proceso de envio de datos de FOTO FOTO FOTO FOTO        ###'
        salirEnvio = 0
        romper = 0
        fotoD = 0
        self.evento = accion
        filename = '/home/pi/innobusmx/data/user/%s.Jpeg'%csnFoto
        while(salgo != 1):
            #print 'Cuanto vale', salirEnvio
            cmd = 'AT+QISEND= 0\r'
            ser.write(cmd.encode())
            send = ser.readline(64)
            ser.write(dato.encode())
            dataS = ser.readline(64)
            ser.write(ascii.ctrl('z'))
            time.sleep(1)
            global last_received

            buffer_string = ''
            while romper != 1:
                buffer_string = buffer_string + ser.read(ser.inWaiting())
                if '\n' in buffer_string:
                    lines = buffer_string.split('\n') # Guaranteed to have at least 2 entries
                    last_received = lines[-2]
                    #If the Arduino sends lots of empty lines, you'll lose the
                    #last filled line, so you could make the above statement conditional
                    #like so: if lines[-2]: last_received = lines[-2]
                    buffer_string = lines[-1]
                    print lines[0][0]
                    print lines[0][1]
                    print lines[0][-1]
                    ok = lines[0][0]
                    ini = lines[0][1]
                    fin = lines[0][-1]
                    if ok == '1' and ini == '@' and fin == '@':
                        print 'La foto llego bien ahora tengo que romper el while para poder parsear la foto'
                        foto = lines[0][2:-1]
                        print foto
                        romper = 1
                        imgdata = base64.b64decode(foto)
                        with open(filename, 'wb') as f:
                            f.write(imgdata)
                        fotoD = 1
                    #ctzL = list(lines)
                    #print ctzL
            if fotoD == 1:
                #aca pondre el envio de que ya tengo la foto a ver que pasa
                #conn = sqlite3.connect(cdDbF)
                #c = conn.cursor()
                #cambio = '1'
                #c.execute("UPDATE fotos SET enviado = ? WHERE idFotos = ?\
                #    ", (cambio, idActualizar))
                #conn.commit()
                #c.close()
                salgo = 0
                print 'Ya la descargue ahora voy a enviar esto al metodo de proeceso de envio'
                print fotoConfirmar
                print idActualizar
                print accion
                print salgo
                print 'Estos son los datos'
                self.procesoDeEnvio(fotoConfirmar, idActualizar, accion, salgo)
                self.reinicioAutomatico = 0
            if fotoD == 0:
                print 'creo que cuando salgo de aca no se rompia vere si sirve'
                self.reinicioAutomatico = 0
            salgo = 1
            print '###         Ya descargue la foto  y ya la envie      ###'

    def validarComando(self, comando, strActualizacion, sms):

        conn = sqlite3.connect(cdDbC)
        c = conn.cursor()
        c.execute("SELECT comando, accion, dEjec FROM tComando WHERE comando = ?",(comando, ))
        data = c.fetchone()
        if data is None:
            print 'Comando no valido'
        else:
            comaT = data[0]
            acciT = data[1]
            dEjeT = data[2]
        #print execc
        c.close()

        if data is None:
            print '###           Comando no soportado        ###'
            cmd = 'AT+CMGD=%s\r'%str(sms)
            ser.write(cmd.encode())
            mensaje = ser.read(128)
        else:
            if dEjeT == 'L':
                #local execute
                exec acciT
                #Elimino el comando SMS
                cmd = 'AT+CMGD=%s\r'%str(sms)
                ser.write(cmd.encode())
                mensaje = ser.read(128)
            if dEjeT == 'C':
                #console execute
                return_code = subprocess.call("%s"%str(acciT), shell=True)
                print return_code
                #Elimino el comando SMS
                cmd = 'AT+CMGD=%s\r'%str(sms)
                ser.write(cmd.encode())
                mensaje = ser.read(128)
            if dEjeT == 'o':
                #mio de mi :D
                print acciT
                #Elimino el comando SMS
                cmd = 'AT+CMGD=%s\r'%str(sms)
                ser.write(cmd.encode())
                mensaje = ser.read(128)
            if dEjeT == 'S':
                print 'Comando', comando
                print 'strComando', strActualizacion

                conn = sqlite3.connect(cdDbC)
                c = conn.cursor()

                c.execute("SELECT accion FROM tComando WHERE comando = ?",(comando,))
                datosComando = c.fetchone()
                if datosComando is None:
                    print('No hay parametros de configuracon contacta al \
                        administrador')
                else:
                    accion = datosComando[0]

                print  strActualizacion.split("@")
                obtDatoActualizar =  strActualizacion.split("@")
                datoAActualizar = obtDatoActualizar[1]

                print accion.split(",")
                datosDeBase = accion.split(",")
                nombreTabla = str(datosDeBase[0])
                nombreRow = str(datosDeBase[1])
                nombreBase = str(datosDeBase[2])

                print 'Nueva pagina', datoAActualizar
                print 'Donde lo voy a guardar', nombreTabla
                print 'Nombre del campo a afectar', nombreRow
                print 'Nombre de la base que voy a alterar', nombreBase

                '''
                    Aca empieza el proceso de actualizacion de registro
                    esto va a funcionar para la actualizacion/sincronizacion
                    de los paramtros de configuracion del sistema
                '''

                conn = sqlite3.connect('/home/pi/innobusvalidador/data/db/%s'%nombreBase)
                c = conn.cursor()


                c.execute('UPDATE ' +'"'+ nombreTabla +'"'+ ' set ' +'"'+ nombreRow +'"'+ ' = ?', (datoAActualizar, ))
                conn.commit()
                c.close()

                #Elimino el comando SMS
                cmd = 'AT+CMGD=%s\r'%str(sms)
                ser.write(cmd.encode())
                mensaje = ser.read(128)

            else:
                print '###          Comando no soportado         ###'
                cmd = 'AT+CMGD=%s\r'%str(sms)
                ser.write(cmd.encode())
                mensaje = ser.read(128)

    def nuevaEv2Inicializada(self, csn ,nombre, apellido, saldo, tipoTarjeta, tipotarifa):
        #insert into tag values ("043E30C2094F80", "Piter", "Pan", "ES", "390","2000", 0);
        print 'Agregar nueva tarjeta'
        conn = sqlite3.connect(cdDbE)
        c = conn.cursor()
        c.execute("INSERT INTO tag(csn, nombre, apellido, tTajeta, tTarifa, saldo, enviado) \
            VALUES(?, ?, ?, ? , ?, ?, ?)", (str(csn), str(nombre), str(apellido), str(saldo), str(tipoTarjeta), str(tipoTarifa), 0))
        conn.commit()
        c.close()

    def recargaEv2(self, csn, saldo):
        print 'Recarga de saldo y avisar que ya la recargue'
        conn = sqlite3.connect(cdDbE)
        c = conn.cursor()
        c.execute("UPDATE tag SET saldo = ? WHERE csn = ?\
            ", (saldo, csn))
        conn.commit()
        c.execute("UPDATE tag SET enviado = ? WHERE csn = ?\
            ", (0, csn))
        conn.commit()
        c.close()

























    def procesoDeEnvio(self, dato, idActualizar, accion, salgo):
        print '###       Proceso de envio de datos       ###'
        salirEnvio = 0
        self.evento = accion

        while(salgo != 1):
            #print 'Cuanto vale', salirEnvio
            print "Dato: "+dato
            cmd = 'AT+QISEND=0\r'
            ser.write(cmd.encode())
            stRead = ""
            while (stRead[-5:] != "ERROR") and (stRead[-9:] != "SEND FAIL") and (stRead[-7:] != 'SEND OK') and (stRead[-1:] != ">"):
                stRead += str(ser.read(1))
            print "QISEND (Dato): "+stRead

            if (stRead[-1:] == ">"):
#                self.noRed.setPixmap(QtGui.QPixmap(""))
                ser.write(dato.encode()+"\x1A")
                stRead = ""
                while (stRead[-8:] != '"recv",0') and (stRead[-5:] != "ERROR") and (stRead[-10:] != '"closed",0'):
                    stRead += str(ser.read(1))
                print "send dato: "+stRead
                    
                if (stRead[-8:] == '"recv",0'):
    		    cmd = 'AT+QIRD=0\r'
                    ser.write(cmd.encode())
                    stRead = ""
                    while (stRead[-2:] != 'OK') and (stRead[-5:] != 'ERROR'):
                        stRead += str(ser.read(1))
                    print "QIRD: "+stRead
		    stRead = " ".join(stRead.split()) #se le aplica un split al mismo comando
                    print "QIRDs: "+stRead

                    if (stRead[-2:] == 'OK'):
                        lista = stRead.split(' ')
                        print "Lista "
                        print lista
                        if (lista[2] == "0"):
                            print '###         No hay Datos que leer         ###'
                        else:
                            if (lista[3][0] == "1"):
                                salgo = 1
                                enviado = 1
                                #buscar si hay una posible actualizacion
                                if (lista[3].find('@') != -1):
                                    print 'encontre una actualizacion'
                                    print lista[3]
                                    try:
                                        print lista[3].split("@")
                                        dos = lista[3].split("@")
                                        print dos[1]
                                        print dos[2]
                                        self.actualizarAlgo = lista[3]
                                    except:
                                        print 'No pude parsear la actualizacion'
                                else:
                                    print 'no encontre nada que hacer'
                            else:
                                print 'No recibi un numero osea que esta fallando la comun'
                                print salirEnvio
                                salirEnvio += 1
                                if (salirEnvio == 2):
                                    print 'Si es mayor entonces rompo el scrip'
                                    self.reinicioAutomatico = self.reinicioAutomatico + 1
                                    salgo = 1
                                    enviado = 0
                else:
#                    self.noRed.setPixmap(QtGui.QPixmap("data/img/noRed.Jpeg"))
                    print '###  Error Recepcion Datos Servidor      ###'
            else:
#                self.noRed.setPixmap(QtGui.QPixmap("data/img/noRed.Jpeg"))
                print '###   Error Conexion con el Servidor     ###'


        if(enviado == 1 and int(self.evento)==1):
            print '###          Actualizando GPS            ###'
            conn = sqlite3.connect(cdDbT)
            c = conn.cursor()
            c.execute("UPDATE tgps SET enviado = 1 WHERE idPos = ?", (idActualizar,))
	    #print "idActualizar "+idActualizar
            conn.commit()
            c.close()
            self.reinicioAutomatico = 0
        # Barras
        if(enviado == 1 and int(self.evento)==2):
            cambio = '1'
            conn = sqlite3.connect(cdDb)
            c = conn.cursor()
            c.execute("UPDATE barras SET enviado = ? WHERE idBarra = ?\
                ", (cambio, idActualizar))
            conn.commit()
            c.close()
            self.reinicioAutomatico = 0
        #Validaciones
        if(enviado == 1 and int(self.evento)==3):
            print '###       Actualizando Validaciones       ###'
            cambio = '1'
            conn = sqlite3.connect(cdDb)
            c = conn.cursor()
            c.execute("UPDATE validador SET enviado = ? WHERE idValidador = ?\
                ", (cambio, idActualizar))
            conn.commit()
            c.close()
            self.reinicioAutomatico = 0
        #recorridos
        if enviado == 1 and int(self.evento==4):
            print '###         Actualizando Recorrido        ###'
            cambio = '1'
            conn = sqlite3.connect(cdDb)
            c = conn.cursor()
            c.execute("UPDATE envRecorrido SET enviados = ? WHERE idEnvRecorrido = ?\
                ", (cambio, idActualizar))
            conn.commit()
            c.close()
            self.reinicioAutomatico = 0
        #soloVuelta del camionero
        if enviado == 1 and int(self.evento==5):
            cambio = '1'
            conn = sqlite3.connect(cdDb)
            c = conn.cursor()
            c.execute("UPDATE soloVuelta SET enviados = ? WHERE idSoloVuelta = ?\
                ", (cambio, idActualizar))
            conn.commit()
            c.close()
            self.reinicioAutomatico = 0
        #turno de la unidad
        if enviado == 1 and int(self.evento==6):
            cambio = '1'
            conn = sqlite3.connect(cdDb)
            c = conn.cursor()
            c.execute("UPDATE turnoDelDia SET enviados = ? WHERE idTurnoDelDia = ?\
                ", (cambio, idActualizar))
            conn.commit()
            c.close()
            self.reinicioAutomatico = 0
        #Lista negra
        if enviado == 1 and int(self.evento==8):
            conn = sqlite3.connect(cdDbLn)
            c = conn.cursor()
            cambio = '1'
            c.execute("UPDATE negra SET enviado = ? WHERE idNegra = ?\
                ", (cambio, idActualizar))
            conn.commit()
            c.close()
            self.reinicioAutomatico = 0
        #envio de foto para actualizar
        if enviado == 1 and int(self.evento==9):
            conn = sqlite3.connect(cdDbF)
            c = conn.cursor()
            cambio = '1'
            c.execute("UPDATE fotos SET enviado = ? WHERE idFotos = ?\
                ", (cambio, idActualizar))
            conn.commit()
            c.close()
            #conn = sqlite3.connect(cdDbLn)
            #c = conn.cursor()
            #cambio = '1'
            #c.execute("UPDATE negra SET enviado = ? WHERE idNegra = ?\
            #    ", (cambio, idActualizar))
            #conn.commit()
            #c.close()
            self.reinicioAutomatico = 0
        #en este caso solo caera cuando haya x intentos erroneos de envio
        # lo cual iniciara todo y reiniciara la variable a 0 de control
        if self.reinicioAutomatico == 5:
            print 'Primero lo que voy a hacer es regresar a 0 la variable de control que entra aqui'
            self.reinicioAutomatico = 0
            print 'Reinicio comunicacion de manera automatica'
#            self.inicializarTodo()
        else:
            print '###         Ya envie todo me saldre       ###'

 




    def obtenerCoordenadaGPS(self):
        '''
            ##############################################################
                Modulo que obteniene la coordenada GPS la guarda cuando
                el GPS se establece de manera correcta.
            ##############################################################
        '''
        cmd = 'AT+QGPSLOC=0\r' 
        ser.write(cmd.encode())
        stRead = ""
        while (stRead[-2:] != "OK") and not ((stRead[-10:] >= "ERROR: 501") and (stRead[-10:] <= "ERROR: 549")):
            stRead += str(ser.read(1))
#        print "QGPSLOC: "+stRead
        if(stRead[-2:] == "OK"):
            #try:
#                self.noGPS.setPixmap(QtGui.QPixmap(""))
		stRead = " ".join(stRead.split()) #se le aplica un split al mismo comando
		my_list = stRead.split(",")
                # 0 Hora  (hh-mm-ss)
		# 1 latitud
		# 2 longitud
                # 7 velocidad
                # 9 Fecha (dd-mm-aa)
                # print my_list
		hora = my_list[0][23:25] + ":" + my_list[0][25:27] + ":" + my_list[0][27:29]
		latitud = my_list[1][0:-1]
		if (my_list[1][-1:] == 'S'):
                    latitud = '-' + latitud
		longitud = my_list[2][0:-1]
		velGPS = my_list[7]
		fecha = my_list[9][0:2] + "-" + my_list[9][2:4] + "-20" + my_list[9][4:6]
                idInser = my_list[9][4:6]+my_list[0][23:29]
                l = float(latitud[0:2]) + (float(latitud[2:])/60)
                latitud = ("%.6f" % l)
                l = float(longitud[0:3]) + (float(longitud[3:])/60)
                longitud = ("%.6f" % l)
		if (my_list[2][-1:] == 'W'):
                    longitud = '-' + longitud
                print '###         Dato valido insertandolo      ###'
                conn = sqlite3.connect(cdDbT)
                c = conn.cursor()
                c.execute('''insert into tgps (hora, latitud, longitud, fecha,
                        velocidad,idPos,enviado) values (?, ?, ?, ?, ?, ?, 0)''',
                        (hora, latitud, longitud, fecha, velGPS, idInser))
                conn.commit()
                c.close()
            #except:
                 #print '###   GPS fallo el parseo del dato   ###'
        else:
            print '###            Modulo gps fallando        ###'
#            parent.noGPS.setPixmap(QtGui.QPixmap("data/img/noGPS.Jpeg"))



    def inicializarTodo(self):
        connn = sqlite3.connect(cdDb)
        c = connn.cursor()
        c.execute("SELECT idTransportista, idUnidad FROM configuraSistema")
        data = c.fetchone()
        if data is None:
            print 'No hay parametros de configuracon contacta al administrador'
        else:
            self.idTransportista = data[0]
            self.idUnidad = data[1]

        c.execute("SELECT gprsProve, gprsUser, gprsPass, socketLiga, \
            socketPuerto FROM configuraSistema")
        datosCon = c.fetchone()
        if datosCon is None:
            print('No hay parametros de configuracon contacta al administrador\
                ')
        else:
            provedor = datosCon[0]
            usuarioProvedor = datosCon[1]
            passProvedor = datosCon[2]
            urlSocket = datosCon[3]
            puertoSocket = datosCon[4]

        paso = 0
        print '#############################################'
        print '### Iniciando el modulo de comunicaciones ###'
        print '###                v0.02                  ###'
        print '#############################################'

#        cmd = "AT+QGPSEND\r"
#        ser.write(cmd.encode())
#        inigps = ser.read(64)
#        inigps = inigps.rstrip()
#        inigps = " ".join(inigps.split())
#        print(inigps)

        ini = ''
        print '###             Iniciando GPS             ###'
        cmd = "AT+QGPS=1\r"
        ser.write(cmd.encode())
        stRead = ""
        while (stRead[-2:] != "OK") and not ((stRead[-3:] >= "501") and (stRead[-3:] <= "549")):
            stRead += str(ser.read(1))
        #print "QGPS: "+stRead

        if (stRead[-2:] == "OK"):
            print '###       El GPS OK                       ###'
	else:
            if (stRead[-3:] == "504"):
                print '###       El GPS ya esta encendido        ###'
            else:
                print '###       Hay un problema con el GPS      ###'
                print '###       GPS: '+stRead

	print '###           Reiniciando conexion        ###'
	cmd = 'AT+QIDEACT=1\r'
	ser.write(cmd.encode())
	stRead = ""
	while (stRead[-2:] != "OK") and (stRead[-5:] != "ERROR"):
            stRead += str(ser.read(1))
	#print "QIDEACT: "+stRead

	
	cmd = 'AT+QIACT?\r'
	ser.write(cmd.encode())
	stRead = ""
	while (stRead[-2:] != "OK") and (stRead[-5:] != "ERROR"):
            stRead += str(ser.read(1))
	#print "QIACT? "+stRead

	print '###           Verificando Status          ###'
	if(stRead[-5:] == "ERROR"):
	    print '###               ERROR  Status           ###'
        else:            
            if(stRead[:23] == 'AT+QIACT? +QIACT: 1,1,1'):
                print '###            Status correcto            ###'
            else:
                print '### Conectandome a la red 3G del provedor ###'
                csttS = 'AT+QICSGP=1,1,"%s","%s","%s",1 OK' % (provedor, usuarioProvedor, passProvedor)
                cmd =   'AT+QICSGP=1,1,"%s","%s","%s",1\r' % (provedor, usuarioProvedor, passProvedor)
                ser.write(cmd.encode())
		#print "Dato: "+dato
            	#ser.write(cmd.encode())
            	stRead = ""
		while (stRead[-2:] != "OK") and (stRead[-5:] != "ERROR"):
                    stRead += str(ser.read(1))
                #print "QICSGP: "+stRead
                #stRead = ser.read(96)
                stRead = " ".join(stRead.split())
                if(stRead != csttS):
                    print '### Conectandome a la red 3G del provedor ###'
                else:
                    print '###            Conexion exitosa.          ###'	    
                    cmd = 'AT+QIACT=1\r'
                    ser.write(cmd.encode())
                    stRead = ""
                    while (stRead[-2:] != "OK") and (stRead[-5:] != "ERROR"):
                        stRead += str(ser.read(1))
                    print "QIACT=1 "+stRead
					
                    print '###              Activa el PDP            ###'
                    if(stRead[-2:] == "OK"):
			print '###            Conexion exitosa.          ###'	    
                    else:
                        print '###        Error al activar el PDP        ###'
	
#	cipstartS = 'AT+QIOPEN=1,0,"TCP","innovacion.no-ip.org",10000,0,0 OK'
	cmd =  'AT+QIOPEN=1,0,"TCP","innovaciones.no-ip.org",10000,0,0\r' 
	ser.write(cmd.encode())
	stRead = ""
	while (stRead[-9:] != "OPEN: 0,0") and not ((stRead[-3:] > "551" and stRead[-3:] < "576")):
            stRead += str(ser.read(1))
	#print "QIOPEN: "+stRead

	print '### Intentando conectar a servidor Socket ###'
	if(stRead[-9:] == "OPEN: 0,0"):
	    print '###             Conexion exitosa          ###'
	else:
            if(stRead[-3:] == '562'):
                print '###   Conexion abierta de forma exitosa   ###'
            else:
                print '###     ERROR con el servidor Socket      ###'


        print '###           Configuracion SMS           ###'
        cmd = "AT+CMGF=1\r"
        ser.write(cmd.encode())
	stRead = ""
	while (stRead[-2:] != "OK") and (stRead[-5:] != "ERROR"):
            stRead += str(ser.read(1))
	#print "CMGF: "+stRead
        if(stRead[-2:] == "OK"):
            print '###               MODULO SMS OK           ###'
	else:
            print '###          ERROR en Modulo SMS          ###'

        print '###   Sincronizando fecha con Servidor    ###'
        i = 0
        while(i <= 3):
            i += 1
            print '###            Intento de Sync '+str(i)+'          ###'
            cmd = 'AT+QISEND=0\r'
            ser.write(cmd.encode())
            stRead = ""
            while (stRead[-5:] != "ERROR") and (stRead[-9:] != "SEND FAIL") and (stRead[-7:] != 'SEND OK') and (stRead[-1:] != ">"):
                stRead += str(ser.read(1))
#            print "QISEND (Hora): "+stRead

            if (stRead[-1:] == ">"):
                cmd = "00\r\x1A\r"
                ser.write(cmd.encode())
                stRead = ""
                while (stRead[-8:] != '"recv",0') and (stRead[-5:] != "ERROR") and (stRead[-10:] != '"closed",0'):
                    stRead += str(ser.read(1))
#                print "send data: "+stRead
                    
                if (stRead[-8:] == '"recv",0'):
    		    cmd = 'AT+QIRD=0\r'
                    ser.write(cmd.encode())
                    stRead = ""
                    while (stRead[-2:] != 'OK') and (stRead[-5:] != 'ERROR'):
                        stRead += str(ser.read(1))
#                    print "QIRD: "+stRead
		    stRead = " ".join(stRead.split()) #se le aplica un split al mismo comando
#                    print "QIRDs: "+stRead


                    if (stRead[-2:] == 'OK'):
                        fecha = stRead.split(' ')
#                        print "ACTUALIZAR HORA "+fecha[3]+' '+fecha[4]
                        stRead = "\""+fecha[3]+' '+fecha[4]+"\""
                        print '###   Fecha '+stRead+'         ###'
                        comando = 'sudo date --set %s'%str(stRead)
                        os.system(comando)
                        i = 4
        print '#############################################'

obj = rwsGPS()

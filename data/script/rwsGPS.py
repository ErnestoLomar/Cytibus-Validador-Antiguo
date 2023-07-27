import serial
from curses import ascii
import time
import sqlite3
import datetime

sPort = '/dev/ttyUSB0'
velocidad = 9600

romper = 0
barraEnvio = 0
ser = serial.Serial(sPort, velocidad,  timeout=1)

'''
    #######################################
       Variables de cambios hablo de la BD
    ########################################
    /home/labo/Documentos/software/uc-cf-b/db/aforo
    /home/labo/Documentos/software/uc-cf-b/db/gps
'''

#cdDb = '/home/pi/uc-cf-b/db/aforo'
cdDb = 'data/db/aforo'
cdDbT = 'data/db/gps'

class rwsGPS:
    def __init__(self):
        while(True):
            print("#################################################################")
            print("#                  Empiezo el proceso de envio                  #")
            #bandera para saber si hay algo que enviar
            envio = 0
            #bandera para el control de los envios si la rompo dejara de enviar
            envioManage = 0
            while(envioManage == 0):
                '''
                ######################################################################
                # Envio de posicion gps desde el while de control hasta que se envian#
                ######################################################################
                '''
                connn = sqlite3.connect(cdDb)
                cc = connn.cursor()
                cc.execute("SELECT idTransportista, idUnidad FROM configuraSistema")
                data = cc.fetchone()
                if data is None:
                    print('No hay parametros de configuracon contacta al administrador\
                        ')
                else:
                    idTranspor = data[0]
                    idUni = data[1]

                conn = sqlite3.connect(cdDbT)
                c = conn.cursor()
                c.execute(" SELECT fecha, hora, latitud, longitud, velocidad, idPos \
                            FROM tgps \
                            WHERE enviado = 0")
                datosGPS = c.fetchone()

                cc.close()
                c.close()

                if datosGPS is None:
                    print('#                  No hay nada que enviar de gps                #')
                    romper = 0
                    #envio = 0
                else:
                    print('#                     Si hay que enviar en gps                  #')
                    fechaT = datosGPS[0]
                    horaT = datosGPS[1]
                    latitudT = datosGPS[2]
                    longitudT = datosGPS[3]
                    velocidadT = datosGPS[4]
                    idpos = datosGPS[5]
                    #print(idpos)
                    envio = 1
                    datetimes = fechaT + ' ' + horaT
                    gpr = '1,'+str(idTranspor)+','+str(idUni)+','+str(datetimes)+','+str(latitudT)+','+str(longitudT)+','+str(velocidadT)+'\r'+''
                    print("#   "+gpr+"   #")
                    #LUEGO QUITAR ESTAS
                    #envioManage = 1
                    #barra = 1

                if (envio == 1):
                    #gprs = str(gpr)
                    #ctzSS = ''
                    #ctzL = [1,2,3,4,5,6,7,8,9,10]#
                    print('#                    Proceso de envio de coordenadas            #')
                    salirEnvio = 0
                    salgo = 0
                    while(salgo != 1):
                        #print('antes del comando atsend')
                        cmd = 'AT+CIPSEND\r'
                        ser.write(cmd.encode())
                        send = ser.readline(64)
                        #print(send)
                        #data.encode()
                        ser.write(gpr.encode())
                        dataS = ser.readline(64)
                        #print(dataS)
                        ser.write(ascii.ctrl('z'))
                        time.sleep(1)
                        ctz = ser.read(64)
                        #ctzS = filter(lambda x: x in string.printable, ctz)   1, 3
                        ctzSS = " ".join(ctz.split())
                        #print(ctzSS[1])
                        #print(ctzSS)
                        #ctzS = list[ctzSS]
                        #print(ctzSS)
                        #print(type(ctzSS))
                        ctzL = list(ctzSS)
                        tamanio = len(ctzL)
                        print(ctzL)
                        if (tamanio < 10):
                            print('se desbordara')
                        else:
                            try:
                                retorno = int(ctzL[10])
                                if(retorno == 1):
                                    salgo = 1
                                    noSeEnvio = 1
                                else:
                                    print('que pedo')
                                    salgo = 0
                            except:
                                print('no hay un numero')
                                salirEnvio += 1
                                if(salirEnvio > 3):
                                    '''
                                        Voy ha agregar el metodo que reinicie el gps como metodo
                                        para que ademas que se reponga de errores tambien se haga
                                        inteligente y se reinicie cuando detecte que esta fallando
                                        el envio del dato, este metodo lo agregare en todos los
                                        envios de este script
                                    '''
                                    print('#                       Reiniciando gps                         #')
                                    self.reinicioGps()
                                    salgo = 1
                                    noSeEnvio = 0
                                else:
                                    print(salirEnvio)
                        #ser.close()

                    if(salgo == 1 & noSeEnvio == 1):
                        cambio = '1'
                        envio = 0
                        c.execute("UPDATE tgps SET enviado = ? WHERE idPos = ?\
                            ", (cambio, idpos))
                        conn.commit()
                    else:
                        print('#                 Ya hice todo  y mejor me saldre               #')
                        romper = 0
                        envioManage = 1

                else:
                    print('#                 No hay coordenadas que enviar                 #')
                    #er.close()
                    romper = 0
                    envioManage = 1
                    time.sleep(1)

            while(romper == 0):
                #ser.write('at+cgpsinf=32\r')
                #out = ''
                #time.sleep(1)
                #while ser.inWaiting() > 0:
                #    out += ser.read()

                cmd = 'AT+CGPSINF=32\r'
                ser.write(cmd.encode())
                dataI = ser.read(1024)
                #quite que me tire la coordenada gps ya que se veia muy fea
                #print(dataI)

                longLis = len(dataI)
                if(longLis > 60):
                    my_list = dataI.split(",")
                    #print(my_list)

                    # 1 Hora  (hh-mm-ss)
                    # 3 Norte
                    # 5 Sur
                    # 7 velocidad
                    # 9 Fecha (dd-mm-aa)

                    horas = my_list[1]
                    latituds = my_list[3]
                    posNegLat = my_list[4]
                    longituds = my_list[5]
                    posNegLong = my_list[6]
                    velocidada = my_list[7]
                    fechas = my_list[9]

                    antes = list(horas)
                    idHora = ''.join(antes[0:6])
                    antesDia = list(fechas)
                    idDia = ''.join(antesDia[0:2])
                    idInser = idDia + idHora
                    #print(idInser)
                    enviados = 0

                    velocidadFlo = float(velocidada)
                    velocidadKmf = ((velocidadFlo * 1.85200) / (1))
                    velocidadKm = int(velocidadKmf)

                    #print('velocidad')
                    #print(velocidadKm)

                    fechasF = datetime.datetime.strptime(fechas, "%d%m%y").strftime("%Y-%m-%d")

                    horasL = list(horas)
                    hor = ''.join(horasL[0:2])
                    minu = ''.join(horasL[2:4])
                    seg = ''.join(horasL[4:6])
                    horasFF = (hor+':'+minu+':'+seg)

                    latitudL = list(latituds)
                    horasLa = ''.join(latitudL[0:2])
                    horasLaF = float(horasLa)
                    minuLa = ''.join(latitudL[2:9])
                    minuLaF = float(minuLa)
                    minSegLa = minuLaF / 60
                    coorLa = horasLaF + minSegLa
                    coorLaD = ("%.6f" % coorLa)

                    #lo tengo que convertir a negativo
                    if(posNegLong == 'S'):
                        coorLaDF = -float(coorLaD)
                    else:
                        coorLaDF = float(coorLaD)

                    longitudL = list(longituds)
                    horasLo = ''.join(longitudL[0:3])
                    horasF = float(horasLo)
                    minuLo = ''.join(longitudL[3:10])
                    minuLoF = float(minuLo)
                    minSegLo = minuLoF / 60
                    coorLo = horasF + minSegLo
                    coorLoD = ("%.6f" % coorLo)

                    #lo tengo que convertir a negativo
                    if(posNegLong == 'W'):
                        coorloDF = -float(coorLoD)
                    else:
                        coorloDF = float(coorLoD)

                    #print(coorLaDF)
                    #print(coorloDF)

                    #1 knot  1.85200 km/h
                    #x Knot     ?    km/h

                    if (my_list[2] != "A"):
                        print("#                      Dato no valido                           #")
                        romper = 1
                        barra = 1
                    else:
                        print('#                  Dato valido insertandolo                     #')
                        conn = sqlite3.connect(cdDbT)
                        c = conn.cursor()
                        c.execute('''insert into tgps (hora, latitud, longitud, fecha,
                            velocidad, idPos, enviado) values (?, ?, ?, ?, ?, ?, ?)''',
                            (horasFF, coorLaDF, coorloDF, fechasF, velocidadKm, idInser,
                                enviados))
                        conn.commit()
                        c.close()
                        romper = 1
                        barra = 1
                else:
                    print('#                    No estoy obteniendo el dato                #')
                    romper = 1
                    barra = 1

            while (barra == 1):
                '''
                ######################################################################
                # Envio de Barras desde el while de control hasta que se envian...   #
                ######################################################################
                '''
                print("#                        Envio de barras                        #")
                #2,idTransportista,idUnidad,auxiliar,duracion,puerta,direccion,fecha/hora
                conn = sqlite3.connect(cdDb)
                c = conn.cursor()
                c.execute(" SELECT idBarra, auxiliar, duracion, puerta, direccion, fechaHora FROM barras WHERE enviado = 0")
                datosBarra = c.fetchone()

                if datosBarra is None:
                    print('#                       No ha subido nadie :)                   #')
                    barra = 0
                    barraEnvio = 0
                else:
                    print('Si hay que enviar')
                    idBarras = datosBarra[0]
                    auxiliarT = datosBarra[1]
                    duracionT = datosBarra[2]
                    puertaT = datosBarra[3]
                    direccionT = datosBarra[4]
                    fechaHoraT = datosBarra[5]
                    #barra = 0
                    barraEnvio = 1
                    #datetimes = fechaT + ' ' + horaT
                    #formar el string a enviar

                    barrasS = '2,'+str(idTranspor)+','+str(idUni)+','+str(auxiliarT)+','+str(duracionT)+','+str(puertaT)+','+str(direccionT)+','+str(fechaHoraT)+'\r'+''
                    print('#                    Esto es lo  que contiene barras            #')
                    print(barrasS)

                if (barraEnvio == 1):
                    #gprs = str(gpr)
                    #ctzSS = ''
                    #ctzL = [1,2,3,4,5,6,7,8,9,10]
                    print('#                           Enviando Barras                     #')
                    salirEnvio = 0
                    salgo = 0
                    while(salgo != 1):
                        #print('antes de enviar barras ')
                        cmd = 'AT+CIPSEND\r'
                        ser.write(cmd.encode())
                        time.sleep(1)
                        send = ser.readline(64)
                        #print(send)
                        #data.encode()
                        ser.write(barrasS.encode())
                        dataS = ser.readline(64)
                        #print(dataS)
                        #ser.write('2,1,3,0,2,d,0,2015-07-06 13:14:00')
                        ser.write(ascii.ctrl('z'))
                        time.sleep(1)
                        ctz = ser.read(64)
                        ctzSS = " ".join(ctz.split())
                        ctzL = list(ctzSS)
                        tamanio = len(ctzL)
                        print(ctzL)
                        if (tamanio < 10):
                            print('se desbordara')
                        else:
                            try:
                                retorno = int(ctzL[10])
                                if(retorno == 1):
                                    salgo = 1
                                    noSeEnvio = 1
                                else:
                                    print("que pedo")
                                    salgo = 0
                            except:
                                #print('no hay un numero')
                                salirEnvio += 1
                                if(salirEnvio > 3):
                                    print('#                        Reiniciando gps                        #')
                                    self.reinicioGps()
                                    salgo = 1
                                    noSeEnvio = 0
                                else:
                                    print(salirEnvio)
                        #ser.close()

                    if(salgo == 1 & noSeEnvio == 1):
                        cambio = '1'
                        envio = 0
                        c.execute("UPDATE barras SET enviado = ? WHERE idBarra = ?\
                            ", (cambio, idBarras))
                        conn.commit()
                    else:
                        print('ya no lo intentare y me saldre para enviar los \
                            atrasados')
                        barra = 0
                        validador = 1
                        #envioManage = 1

                else:
                    print('#                  Ya envie todo de barras                      #')
                    #er.close()
                    barra = 0
                    validador = 1
                    time.sleep(1)

            while (validador == 1):
                 #1,1,3,2015-08-27 18:41:03,22.139758,-101.03279,0
                '''
                ######################################################################
                #                        Enviando validaciones                       #
                ######################################################################
                '''
                #3,idTipoTisc,idUnidad,idOperador,csn,saldo,tarifa,fecha/hora
                conn = sqlite3.connect(cdDb)
                c = conn.cursor()
                c.execute(" SELECT idValidador, idTipoTisc, idUnidad, idOperador, csn, saldo, tarifa, fechaHora, enviado FROM validador WHERE enviado = 0")
                datosValidador = c.fetchone()

                if datosValidador is None:
                    print('#                   No hay validaciones  Nuevas                 #')
                    validador = 0
                    validadorEnvio = 0
                else:
                    print('#                    Si hay validaciones nuevas                 #')
                    idValida = datosValidador[0]
                    idTipoT = datosValidador[1]
                    #idTipoT = 1
                    #idUnid = datosValidador[2]
                    idUnid = 3
                    #idOper = datosValidador[3]
                    idOper = 1
                    csn = datosValidador[4]
                    saldo = datosValidador[5]
                    tarifa = datosValidador[6]
                    fechaHora = datosValidador[7]
                    #barra = 0
                    validadorEnvio = 1
                    #tipoTiscCOnv = idTipoT.decode("hex")
                    #datetimes = fechaT + ' ' + horaT
                    #formar el string a enviar
                    #barraS = '2,'+str(idTranspor)+','+str(idUni)+','+str(auxiliarT)+','+str(duracionT)+','+str(puertaT)+','+str(direccionT)+','+str(fechaHoraT)+'\r''

                    validadorS = '3,'+str(idTipoT)+','+str(idUnid)+','+str(idOper)+','+str(csn)+','+str(saldo)+','+str(tarifa)+','+str(fechaHora)+'\r'+''
                    print('#                   Dato a enviar en validacion                 #')
                    print(validadorS)

                if (validadorEnvio == 1):
                    print('#                      Enviando Validaciones                    #')
                    salirEnvio = 0
                    salgo = 0
                    while(salgo != 1):
                        print('Antes de enviar validaciones ')
                        cmd = 'AT+CIPSEND\r'
                        ser.write(cmd.encode())
                        time.sleep(1)
                        #send = ser.readline(64)
                        send = ser.readline(1024)
                        #print(send)
                        #data.encode()
                        ser.write(validadorS.encode())
                        dataS = ser.readline(64)
                        #print(dataS)
                        #ser.write('2,1,3,0,2,d,0,2015-07-06 13:14:00')
                        ser.write(ascii.ctrl('z'))
                        time.sleep(1)
                        ctz = ser.read(64)
                        ctzSS = " ".join(ctz.split())
                        ctzL = list(ctzSS)
                        tamanio = len(ctzL)
                        print(ctzL)
                        if (tamanio < 10):
                            print('se desbordara antes de enviar validaciones')
                        else:
                            try:
                                retorno = int(ctzL[10])
                                if(retorno == 1):
                                    salgo = 1
                                    noSeEnvio = 1
                                else:
                                    print("que pedo")
                                    salgo = 0
                            except:
                                print('no hay un numero')
                                salirEnvio += 1
                                if(salirEnvio > 3):
                                    print('Antes de salirme voy a reiniciar la conexion gprs como metodo')
                                    self.reinicioGps()
                                    salgo = 1
                                    noSeEnvio = 0
                                else:
                                    print(salirEnvio)
                        #ser.close()

                    if(salgo == 1 & noSeEnvio == 1):
                        cambio = '1'
                        envio = 0
                        c.execute("UPDATE validador SET enviado = ? WHERE idValidador = ?\
                            ", (cambio, idValida))
                        conn.commit()
                    else:
                        print('ya no lo intentare y me saldre para enviar los \
                            atrasados')
                        finRecorrido = 1
                        validador = 0
                        #envioManage = 1

                else:
                    print('#              No tengo  validaciones x enviar                  #')
                    #print('# ####################################### #')
                    #er.close()
                    finRecorrido = 1
                    validador = 0
                    #envioManage = 1
                    time.sleep(1)

            while (finRecorrido == 1):
                '''
                ######################################################################
                #                      Enviando de fin de recorrido                  #
                ######################################################################
                '''
                #4,FechaHora,kilometraje,idUnidad,idChofer,numVuelta,idServicio,inFin
                #CREATE TABLE envRecorrido(idEnvRecorrido INTEGER PRIMARY KEY AUTOINCREMENT, fechaHora varchar (10),
                #idUnidad int(4), idChofer int(4), num_vuelta int(2), recorrido int(4), inicioFin varchar(1), enviados int(1));
                conn = sqlite3.connect(cdDb)
                c = conn.cursor()
                c.execute(" SELECT idEnvRecorrido, fechaHora, km, idUnidad, idChofer, num_vuelta, recorrido, inicioFin FROM envRecorrido WHERE enviados = 0")
                datosFinRecorrido = c.fetchone()

                if datosFinRecorrido is None:
                    print('#                   No hay fin  de recorridos                   #')
                    finRecorrido = 0
                    finRecorridoEnvio = 0
                else:
                    print('Si hay que enviar')
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
                    print('Esto se enviara en fin de recorrido')
                    print(finRecorridoS)

                if (finRecorridoEnvio == 1):
                    print('#                    Enviando fin de recorrido                  #')
                    salirEnvio = 0
                    salgo = 0
                    while(salgo != 1):
                        print('Antes de enviar fin de recorrido ')
                        cmd = 'AT+CIPSEND\r'
                        ser.write(cmd.encode())
                        time.sleep(1)
                        #send = ser.readline(64)
                        send = ser.readline(1024)
                        #print(send)
                        #data.encode()
                        ser.write(finRecorridoS.encode())
                        dataS = ser.readline(64)
                        #print(dataS)
                        #ser.write('2,1,3,0,2,d,0,2015-07-06 13:14:00')
                        ser.write(ascii.ctrl('z'))
                        time.sleep(1)
                        ctz = ser.read(64)
                        ctzSS = " ".join(ctz.split())
                        ctzL = list(ctzSS)
                        tamanio = len(ctzL)
                        print(ctzL)
                        if (tamanio < 10):
                            print('se desbordara')
                        else:
                            try:
                                retorno = int(ctzL[10])
                                if(retorno == 1):
                                    salgo = 1
                                    noSeEnvio = 1
                                else:
                                    print("que pedo")
                                    salgo = 0
                            except:
                                print('no hay un numero')
                                salirEnvio += 1
                                if(salirEnvio > 3):
                                    print('Antes de salirme voy a reiniciar la conexion gprs como metodo')
                                    self.reinicioGps()
                                    salgo = 1
                                    noSeEnvio = 0
                                else:
                                    print(salirEnvio)
                        #ser.close()

                    if(salgo == 1 & noSeEnvio == 1):
                        cambio = '1'
                        envio = 0
                        c.execute("UPDATE envRecorrido SET enviados = ? WHERE idEnvRecorrido = ?\
                            ", (cambio, idenvRecorridoE))
                        conn.commit()
                    else:
                        print('ya no lo intentare y me saldre para enviar los \
                            atrasados')
                        finRecorrido = 0
                        inicioFinVuelta = 1
                        #envioManage = 1

                else:
                    print('#                  Ya envie  todo de recorrido                  #')
                    #print('# ########################################### #')
                    #er.close()
                    finRecorrido = 0
                    inicioFinVuelta = 1
                    #envioManage = 1
                    time.sleep(1)


            while (inicioFinVuelta == 1):
                '''
                ######################################################################
                #                     Enviando inicio fin chofer                     #
                ######################################################################
                '''
                #5,fechaHora,kilometraje,idUnidad,csn,numVuelta,turo,inFin
                #CREATE TABLE envRecorrido(idEnvRecorrido INTEGER PRIMARY KEY AUTOINCREMENT, fechaHora varchar (10),
                #idUnidad int(4), idChofer int(4), num_vuelta int(2), recorrido int(4), inicioFin varchar(1), enviados int(1));
                conn = sqlite3.connect(cdDb)
                c = conn.cursor()
                c.execute("SELECT idSoloVuelta, fechaHora, km, idUnidad, idRuta, csn, num_vuelta, turno, inicioFin FROM soloVuelta WHERE enviados = 0")
                datosSoloVuelta = c.fetchone()

                if datosSoloVuelta is None:
                    print('#                   No hay fin  de solo validador            #')
                    finRecorrido = 0
                    finRecorridoEnvio = 0
                else:
                    print('Si hay que enviar')
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
                    print('Esto se enviara en fin de recorrido')
                    print(finRecorridoS)

                if (finRecorridoEnvio == 1):
                    print('#                    Enviando inicio fin de vuelta ejecutada por chofer        #')
                    salirEnvio = 0
                    salgo = 0
                    while(salgo != 1):
                        print('Antes de enviar inicioFin de vuelta ')
                        cmd = 'AT+CIPSEND\r'
                        ser.write(cmd.encode())
                        time.sleep(1)
                        #send = ser.readline(64)
                        send = ser.readline(1024)
                        #print(send)
                        #data.encode()
                        ser.write(finRecorridoS.encode())
                        dataS = ser.readline(64)
                        #print(dataS)
                        #ser.write('2,1,3,0,2,d,0,2015-07-06 13:14:00')
                        ser.write(ascii.ctrl('z'))
                        time.sleep(1)
                        ctz = ser.read(64)
                        ctzSS = " ".join(ctz.split())
                        ctzL = list(ctzSS)
                        tamanio = len(ctzL)
                        print(ctzL)
                        if (tamanio < 10):
                            print('se desbordara')
                        else:
                            try:
                                retorno = int(ctzL[10])
                                if(retorno == 1):
                                    salgo = 1
                                    noSeEnvio = 1
                                else:
                                    print("que pedo")
                                    salgo = 0
                            except:
                                print('no hay un numero')
                                salirEnvio += 1
                                if(salirEnvio > 3):
                                    print('Antes de salirme voy a reiniciar la conexion gprs como metodo')
                                    self.reinicioGps()
                                    salgo = 1
                                    noSeEnvio = 0
                                else:
                                    print(salirEnvio)
                        #ser.close()

                    if(salgo == 1 & noSeEnvio == 1):
                        cambio = '1'
                        envio = 0
                        c.execute("UPDATE envRecorrido SET enviados = ? WHERE idEnvRecorrido = ?\
                            ", (cambio, idSoloVueltas))
                        conn.commit()
                    else:
                        print('ya no lo intentare y me saldre para enviar los \
                            atrasados')
                        inicioFinVuelta = 0
                        envioManage = 1

                else:
                    print('#                  Ya envie  todo de recorrido                  #')
                    #print('# ########################################### #')
                    #er.close()
                    inicioFinVuelta = 0
                    inicioFinAnalista = 1
                    time.sleep(1)


            while (inicioFinAnalista == 1):
                '''
                ######################################################################
                #       Enviando inicio fin de analista solo validador         #
                ######################################################################
                '''
                #5,fechaHora,kilometraje,idUnidad,csn,numVuelta,turo,inFin
                #CREATE TABLE envRecorrido(idEnvRecorrido INTEGER PRIMARY KEY AUTOINCREMENT, fechaHora varchar (10),
                #idUnidad int(4), idChofer int(4), num_vuelta int(2), recorrido int(4), inicioFin varchar(1), enviados int(1));
                conn = sqlite3.connect(cdDb)
                c = conn.cursor()
                c.execute(" SELECT idInicioFinTurnoSoloValidador, fechaHora, idUnidad, idRuta, csn, turno, inicioFin FROM inicioFinTurnoSoloValidador WHERE enviados = 0")
                datosinicioFinTurnoSoloValidador = c.fetchone()

                c.execute("SELECT idRutaActual FROM configuraSistema")
                idRuta = c.fetchone()
                ruta = idRuta[0]

                if datosinicioFinTurnoSoloValidador is None:
                    print('#                   No hay fin  de solo validador            #')
                    finRecorrido = 0
                    finRecorridoEnvio = 0
                else:
                    print('Si hay que enviar')
                    finRecorridoEnvio = 1
                    iddatosinicioFinTurnoSoloValidador= datosinicioFinTurnoSoloValidador[0]
                    fechaHoraE = datosinicioFinTurnoSoloValidador[1]
                    idUnidadE = datosinicioFinTurnoSoloValidador[2]
                    idRutaE = datosinicioFinTurnoSoloValidador[3]
                    csnE = datosinicioFinTurnoSoloValidador[4]
                    turnoE = datosinicioFinTurnoSoloValidador[5]
                    inicioFinE = datosinicioFinTurnoSoloValidador[6]
                    finRecorridoS = '6,'+str(fechaHoraE)+','+str(idUnidadE)+','+str(ruta)+','+str(csnE)+','+str(turnoE)+','+str(inicioFinE)+'\r'+''
                    print('Esto se enviara en fin de recorrido')
                    print(finRecorridoS)

                if (finRecorridoEnvio == 1):
                    print('#                    Enviando inicio fin de vuelta ejecutada por chofer        #')
                    salirEnvio = 0
                    salgo = 0
                    while(salgo != 1):
                        print('Antes de enviar inicioFin de vuelta ')
                        cmd = 'AT+CIPSEND\r'
                        ser.write(cmd.encode())
                        time.sleep(1)
                        #send = ser.readline(64)
                        send = ser.readline(1024)
                        #print(send)
                        #data.encode()
                        ser.write(finRecorridoS.encode())
                        dataS = ser.readline(64)
                        #print(dataS)
                        #ser.write('2,1,3,0,2,d,0,2015-07-06 13:14:00')
                        ser.write(ascii.ctrl('z'))
                        time.sleep(1)
                        ctz = ser.read(64)
                        ctzSS = " ".join(ctz.split())
                        ctzL = list(ctzSS)
                        tamanio = len(ctzL)
                        print(ctzL)
                        if (tamanio < 10):
                            print('se desbordara')
                        else:
                            try:
                                retorno = int(ctzL[10])
                                if(retorno == 1):
                                    salgo = 1
                                    noSeEnvio = 1
                                else:
                                    print("que pedo")
                                    salgo = 0
                            except:
                                print('no hay un numero')
                                salirEnvio += 1
                                if(salirEnvio > 3):
                                    print('Antes de salirme voy a reiniciar la conexion gprs como metodo')
                                    self.reinicioGps()
                                    salgo = 1
                                    noSeEnvio = 0
                                else:
                                    print(salirEnvio)
                        #ser.close()

                    if(salgo == 1 & noSeEnvio == 1):
                        cambio = '1'
                        envio = 0
                        c.execute("UPDATE envRecorrido SET enviados = ? WHERE idEnvRecorrido = ?\
                            ", (cambio, iddatosinicioFinTurnoSoloValidador))
                        conn.commit()
                    else:
                        print('ya no lo intentare y me saldre para enviar los \
                            atrasados')
                        inicioFinVuelta = 0
                        envioManage = 1

                else:
                    print('#                  Ya envie  todo de recorrido                  #')
                    #print('# ########################################### #')
                    #er.close()
                    inicioFinAnalista = 0
                    envioManage = 1
                    time.sleep(1)



    def reinicioGps(self):
        paso = 0
        print("#################################################################")
        ini = ''
        while (ini != 'at+cgpspwr=1 OK'):
            print('Entro del whle')
            cmd = "at+cgpspwr=1\r"
            ser.write(cmd.encode())
            inigps = ser.read(64)
            print('esto lo tiene inigps')
            inigp = inigps.rstrip()
            ini = " ".join(inigp.split())
            print(ini)
            paso = paso + 1
            if (paso == 3):
                print('Error tres veces porque ya estaba encendido')
                ini = 'at+cgpspwr=1 OK'
                paso = 0

        print('Reset GPS')
        rgps = 'at+cgpsrst=0 ERROR'
        while (rgps == 'at+cgpsrst=0 ERROR'):
            cmd = "at+cgpsrst=0\r"
            ser.write(cmd.encode())
            resetgps = ser.read(64)
            rgp = resetgps.rstrip()
            rgps = " ".join(rgp.split())
            print(rgps)

        #Este we es el que truena la rexonexion y tego que volver a iniciar
        #el script
        #print('#  Init GPRS #')
        #shutgs = ''
        #while (shutgs != 'AT+CIPSHUT SHUT OK'):
        #    shutc = "AT+CIPSHUT\r"
        #    ser.write(shutc.encode())
        #    shut = ser.read(64)
        #    shutg = shut.rstrip()
        #    shutgs = " ".join(shutg.split())
        #    print(shutgs)

        #Este no se si ponerlo ya que solo checa si el gps esta ok
        statusS = ''
        print('Status GPRS')
        while(statusS != 'AT+CIPSTATUS OK STATE: CONNECT OK'):
            cmd = "AT+CIPSTATUS\r"
            ser.write(cmd.encode())
            status = ser.read(64)
            statusS = " ".join(status.split())
            print(statusS)

        csttS = ''
        while (csttS != 'AT+CSTT="internet.itelcel.com", "webgprs", "webgprs2002" OK'):
            cmd ='AT+CSTT="internet.itelcel.com", "webgprs", "webgprs2002"\r'
            ser.write(cmd.encode())
            cstt = ser.read(64)
            csttS = " ".join(cstt.split())
            print(csttS)

        ciirS = ''
        while(ciirS != 'AT+CIICR OK'):
            cmd = 'AT+CIICR\r'
            ser.write(cmd.encode())
            ciir = ser.read(64)
            ciirS = " ".join(ciir.split())
            print(ciirS)

        cmd = 'AT+CIFSR\r'
        ser.write(cmd.encode())
        cifsr = ser.read(64)
        print(cifsr)

        '''
            Validar este error para poder descartar que se cuelgue de nuevo todo ya que no se cuelga
            porque recibe un string muy grande lo que propongo es convertir a arreglo el string y
            solo buscar el OK en el string para poder cerrarlo
        '''
        print("te encontie")
        cipstartS = ''
        while(cipstartS != 'AT+CIPSTART="TCP","innovaciones.no-ip.org","10000" OK'):
            cmd = 'AT+CIPSTART="TCP","innovaciones.no-ip.org","10000"\r'
            ser.write(cmd.encode())
            cipstar = ser.read(64)
            cipstartS = " ".join(cipstar.split())
            #cipstartS = cipstartS.split(',')
            #print(cipstartS[53:54])
            print(cipstartS)
        print("#################################################################")
        return

#obj = rwsGPS()

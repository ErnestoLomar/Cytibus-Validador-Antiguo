# -*- coding: utf-8 -*-

"""
Pruebas de FTP - Funcionamiento: PRuebas
"""



import time, serial
import os
import subprocess
import time
import base64
import sys
import glob
import shutil
import sqlite3
import datetime
import variables_globales

# Conexión a la base de datos
dbAforo = sqlite3.connect('/home/pi/innobusmx/data/db/aforo')
c = dbAforo.cursor()

# Ejecutar la consulta
c.execute('SELECT idUnidad FROM parametros')
data = c.fetchone()
id_Unidad = str(data[0]) if data else "Sin datos"  # Manejar caso de no encontrar datos


contador = 1
nombre = ""
ubicacion = ""
version_Lista = ""
tipo = ""
intentos_actualizacion = 0
intentos_ftp = 0

carpetaSoftware = "innobusmx" #Nombre de la carpeta que tiene el software
# Urban_Urbano
baseDeDatos = "tarjetas" # Nombre de base de datos actualizable 
#matrices_tarifarias

cuenta_azure = "\"account\""
usuario_FTP_azure = "\"Abraham\""
contra_FTP_azure = "\"May0admin2022*\""
host_FTP_azure = "\"20.106.77.209\""
conf_conexion_FTP_azure = "AT+QFTPCFG=" + cuenta_azure + "," + usuario_FTP_azure + "," + contra_FTP_azure
conexion_FTP_azure = "AT+QFTPOPEN=" + host_FTP_azure + ",21"

cuenta_webhost = "\"account\""
usuario_FTP_webhost = "\"daslom\""
contra_FTP_webhost = "\"geforceGTX\""
host_FTP_webhost = "\"files.000webhost.com\""
conf_conexion_FTP_webhost = "AT+QFTPCFG=" + cuenta_webhost + "," + usuario_FTP_webhost + "," + contra_FTP_webhost
conexion_FTP_webhost = "AT+QFTPOPEN=" + host_FTP_webhost + ",21"

# Importante: Asegúrate de tener la biblioteca 'serial' importada
import serial

quectelUSB = "" #Comunicacion con quectel
timeCheck = "" # Para evitar que software se reinicie por limite de tiempo
respFTP = ""

def config_PDP():
    # Reiniciar SIM
    enviaComando("AT+QFUN=5")
    time.sleep(5)
    enviaComando("AT+QFUN=6")
    time.sleep(5)

    # Configurar PDP context
    resp = enviaComando("AT+QICSGP=1,1,\"internet.itelcel.com\",\"\",\"\",0")
    if 'OK' in resp:
        print "PDP Context correcto"
        resp = enviaComando("AT+QIACT=1")
        if 'OK' in resp:
            print "PDP conetxt activado"
            resp = enviaComando("AT+QFTPCFG=\"contextid\",1")
            if 'OK' in resp:
                print "FTP contextid configurado correctamente"
            else:
                print "FTP contextid no se pudo configurar"
        else:
            print "PDP context no se pudo activar"
    else:
        print "Error PDP Context"

    

def QuectelON():
    print "Intentando comunicar con quectel..."
    # Envía datos al puerto serie
    dato = enviaComando("AT")
    if 'OK' in dato or 'RDY' in dato:
        print dato
        return True
    else:
        print "Quectel aun no esta disponible"
        return False


def verificar_memoria_UFS(version_matriz):
    try:
        global id_Unidad,respFTP
        Aux = enviaComando("AT+QFLST=\"*\"")
        #enviaComando("AT+QFDEL=\"*\"")
        if 'update.txt' in Aux:
            print "Ya existe el archivo update.txt en quectel, procede a eliminarse..."
            eliminar_archivos = enviaComando("AT+QFDEL=\"update.txt\"")
        if '%s' % id_Unidad in Aux:
            print "Ya existe el archivo %s.txt en quectel, procede a eliminarse..." % id_Unidad
            eliminar_archivos = enviaComando("AT+QFDEL=\"%s.txt\"" % id_Unidad)
        if '%s' % version_matriz in Aux:
            print "Ya existe el archivo %s.txt en quectel, procede a eliminarse..." % version_matriz
            eliminar_archivos = enviaComando("AT+QFDEL=\"%s.txt\"" % version_matriz)
        
        if os.path.exists('/home/pi/update.txt'):
            print "Ya existe el archivo update.txt en raspberry, procede a eliminarse..."
            subprocess.call('rm -rf /home/pi/update.txt', shell=True)
        if os.path.exists('/home/pi/%s.txt' % id_Unidad):
            print "Ya existe el archivo %s.txt en raspberry, procede a eliminarse..." % id_Unidad
            subprocess.call('rm -rf /home/pi/%s.txt' % id_Unidad, shell=True)
        if os.path.exists('/home/pi/update/'):
            print "Ya existe el directorio update en raspberry, procede a eliminarse..."
            subprocess.call('rm -rf /home/pi/update/', shell=True)
        
        quectelUSB.flushInput()
        quectelUSB.flushOutput()
        return True
    
    except Exception, e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print "FTP.py,", exc_tb.tb_lineno, " Error al verificar memoria: " + str(e)
        if intentos_actualizacion >= 2:
            respFTP = "eMemQuectel" #Mandar Error
        return False


def ConfigurarFTP(servidor, tamanio = False):
    try:
        global intentos_actualizacion,tipo,nombre,ubicacion,respFTP
        # version_Lista = version_LB

        timeCheck.lastConnection = time.time() # Reporta actividad  

        if tamanio == False:
            tipo = "Lista.db"
            nombre = str(datetime.datetime.now().strftime('%Y%m%d'))
            if str(variables_globales.version_tarjetas) == nombre:
                print "-- La base de datos ya esta actualizada --"
                return False
            ubicacion = "/MiPase/Tarjetas"
        else:
            tipo = "Software"
            nombre = id_Unidad
            ubicacion = "/MiPase/Software"
            tamanio = int(tamanio) 

        verificar_memoria_UFS(nombre)

        print "<<<<<<<<<<<< INTENTO DE ACTUALIZACION %s: %d >>>>>>>>>" % (tipo, intentos_actualizacion + 1)

        Tiempo = "\"rsptimeout\""
        enviaComando("AT+QFTPCFG=" + Tiempo + ",180")

        transmode = "\"transmode\""
        enviaComando("AT+QFTPCFG=" + transmode + ",1")

        filetype = "\"filetype\""
        enviaComando("AT+QFTPCFG=" + filetype + ",1")

        if servidor == "web":
            enviaComando(conf_conexion_FTP_webhost)
            return IniciarSesionFTP(servidor, tamanio)
        elif servidor == "azure":
            enviaComando(conf_conexion_FTP_azure)
            ret = IniciarSesionFTP(servidor, tamanio)
            if ret == False:
                intentos_actualizacion += 1
                if intentos_actualizacion >= 3:
                    intentos_actualizacion = 0
                    return False
                else:
                    return ConfigurarFTP(servidor, tamanio)
            else:
                return True
    except Exception, e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print "FTP.py,", exc_tb.tb_lineno, " Error al ConfigurarFTP: " + str(e)
        intentos_actualizacion += 1
        if intentos_actualizacion >= 3:
            intentos_actualizacion = 0
            respFTP = "eConfig"# Mandar Error [eConfig]
            return False
        else:
            return ConfigurarFTP(servidor, tamanio)


def enviaComando(comando, timeout = 5):
    global quectelUSB
    flush = quectelUSB.readline().decode()
    comando = comando + "\r\n"
    print "Comando enviado: %s" % comando
    quectelUSB.write(comando)
    time.sleep(timeout)
    # Recepción de datos
    datos_recibidos = quectelUSB.read(quectelUSB.inWaiting())
    print "Recibe: %s" % datos_recibidos
    return datos_recibidos    

def IniciarSesionFTP(servidor, tamanio):
    try:
        global intentos_ftp, contador,respFTP
        timeCheck.lastConnection = time.time() # Reporta actividad 
        print "Intentado conectar a servidor: %s" % servidor
        if servidor == "web":
            Aux = enviaComando(conexion_FTP_webhost)
            if "OK" in Aux:
                print "Conexion exitosa a servidor webhost"
                time.sleep(5)
                contador = 0
                intentos_ftp = 0
                return UbicarPathFTP("web", tamanio)
            else:
                print "Reintentando conectar a servidor webhost..."
                enviaComando("AT+QFTPCLOSE")
                time.sleep(5)
                if contador >= 6:
                    print "No se pudo establecer la conexion con el servidor FTP [web]"
                    if intentos_actualizacion >= 2:
                        pass
                    return False
                contador += 1
                intentos_ftp += 1
                print "contador:%d, intentos_ftp:%d" % (contador, intentos_ftp)
                ret = IniciarSesionFTP("web", tamanio)
            contador = 0
            intentos_ftp = 0
            print "####################################################### Regresa de webhost"
            return ret

        elif servidor == "azure":
            Aux = enviaComando(conexion_FTP_azure, 10)
            if "OK" in Aux and "625" not in Aux:
                print "Conexion exitosa a azure"
                time.sleep(5)
                contador = 0
                intentos_ftp = 0
                return UbicarPathFTP("azure", tamanio)
            else:
                if "625" in Aux:
                    print "Error Not logged in"
                print "Reintentando conectar a servidor azure..."
                enviaComando("AT+QFTPCLOSE")
                time.sleep(5)
                if intentos_ftp >= 3:
                    print "No se pudo establecer la conexion con el servidor FTP [Azure]"
                    print "intentando conexion alternativa con servidor webhost"
                    respFTP = "eServidor"# Mandar Error [eServidor]
                    ret = ConfigurarFTP("web", tamanio)
                else:
                    contador += 1
                    intentos_ftp += 1
                    print "contador:%d, intentos_ftp:%d" % (contador, intentos_ftp)
                    ret = IniciarSesionFTP("azure", tamanio)
            contador = 0
            intentos_ftp = 0
            print "####################################################### Regresa de azure:%s" % ret
            return ret

    except Exception, e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print "FTP.py,", exc_tb.tb_lineno, " Error al IniciarSesionFTP: " + str(e)
        if intentos_actualizacion >= 2:
            respFTP = "eSesion" # Mandar Error [eSesion]
        return False



def UbicarPathFTP(servidor, tamanio):
    try:
        global id_Unidad, nombre, ubicacion, tipo,respFTP

        global intentos_ftp

        timeCheck.lastConnection = time.time() # Reporta actividad 
        print ">>>>>>>>>>>>>>>>>Buscando archivo:%s.txt en la ubicacion:%s" % (nombre, ubicacion)
        # define ubicacion
        edo = enviaComando('AT+QFTPCWD="%s"' % ubicacion, 10)
        if "ERROR:" in edo:
            if intentos_actualizacion >= 2:
                respFTP = "eQFTPCWD"# Mandar Error [eQFTPCWD]
            return False
        time.sleep(2)
        edo = enviaComando('AT+QFTPSIZE="%s.txt"' % nombre, 10)

        if "ERROR:" in edo:
            if intentos_actualizacion >= 2:
                respFTP = "eQFTPSIZE"# Mandar Error [eQFTPSIZE]
            return False
        elif "+QFTPSIZE:" in edo:
            # Comparacion de tamano con el que esta en el servidor(aun no descargado)
            tam = edo.split(",")
            # Revisa si no hubo error al obtener size
            revision = tam[0].split()[-1]
            if int(revision) == 0:
                if tipo == "Software":
                    # Si es Software compara tamano recibido de trama con el del txt
                    if int(tam[1]) != int(tamanio):
                        print "El tamano del archivo en %s no coincide" % servidor
                        print "\tSe esperaba: %d Bytes, se encuentra un archivo de: %d Bytes" % (tamanio, int(tam[1]))
                        if intentos_actualizacion >= 2:
                            respFTP = "eSIZE"# Mandar Error [eSIZE]
                        return False
                elif tipo == "Lista.db":
                    # Si es Lista.db obtiene el tamano del servidor ya que hasta ahora se desconoce
                    tamanio = int(tam[1])
                    print "El tamano del archivo es %d" % tamanio
            else:
                print "Error al obtener tamano del archivo"
                if intentos_actualizacion >= 2:
                    respFTP = "eNOTXT"# Mandar Error [eNOTXT]
                return False
        # descarga archivo
        comando_descarga = 'AT+QFTPGET="%s.txt","UFS:%s.txt"\r\n' % (nombre, nombre)
        quectelUSB.write(comando_descarga)
        time.sleep(5)  # Esperar unos segundos para que se complete la descarga
        # print(quectelUSB.readline())
        Reintentar = "false"
        # Limpia buffer para no considerar echo de comando
        print quectelUSB.readline().decode()
        print quectelUSB.readline().decode()
        
        timeCheck.lastConnection = time.time() # Reporta actividad 
        # Espera y maneja respuesta
        while True:
            print "descargando archivo de %s..." % servidor
            Aux = quectelUSB.readline().decode()
            print Aux

            if "+QFTPGET: 0,0" in Aux:
                print "Ha ocurrido un error de descarga"
                Reintentar = "True"
                break

            if "+QFTPGET" in Aux:
                print "Revisando descargada..."
                Resp = Aux.split(",")
                if "+QFTPGET: 0" in Resp[0]:
                    print "Conexion del ftp correcta"
                    if int(Resp[1]) != int(tamanio):
                        print "El tamano del archivo descargado no coincide"
                        print "\tSe esperaba: %d Bytes, se descargo un archivo de: %d Bytes" % (tamanio, int(Resp[1]))
                        Reintentar = "True"
                        break
                    print "Tamano de archivo descargado coincide con el esperado"
                    break
                else:
                    print "Ha ocurrido un error..."
                    Reintentar = "True"
                    break
            if "ERROR:" in Aux:
                print "Error de comunicacion"
                Reintentar = "True"
                break
            if "QFTPCLOSE:606," in Aux:
                print "Error de timeout"
                Reintentar = "True"
                break
        if Reintentar == "True":
            if intentos_actualizacion >= 2:
                respFTP = "eDWLServidor"# Mandar Error [eDWLServidor]
            return False
        else:
            return leerArchivo(servidor, tamanio)

    except Exception, e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print "FTP.py,", exc_tb.tb_lineno, " Error al UbicarPathFTP: " + str(e)
        if intentos_actualizacion >= 2:
            respFTP = "ePath"# Mandar Error [ePath]
        return False


def leerArchivo(servidor, tamanio):
    
    global nombre,respFTP
    i_AT=1
    while i_AT <= 3:
        try:
            

            print "Descargando archivo de quectel y generando txt / intento: %d" % i_AT
            archivo = '%s.txt' % nombre
            comando = 'AT+QFDWL="%s"\r\n' % archivo
            quectelUSB.write(comando)
            
            content_started = False
            data = ""
            error = False
            
            while True:
                timeCheck.lastConnection = time.time() # Reporta actividad 
                response = quectelUSB.read(1024)  # Leer una línea de datos
                if response:
                    if not content_started:
                        if "[" in response:
                            content_started = True
                    if content_started:
                        data += response
                        if "]" in response:
                            break
                    if "ERROR:" in response:
                        print "Error en response"
                        error = True
                        break
            if error:
                if intentos_actualizacion >= 2:
                    respFTP = "eDWLQuectel"# Mandar Error [eDWLQuectel]
                    return False
                i_AT += 1
                continue


            decoded_data = data.decode("utf-8")
            start_idx = decoded_data.index("[")
            end_idx = decoded_data.index("]") + 1
            content = decoded_data[start_idx:end_idx]
            
            with open('/home/pi/%s' % archivo, "w") as file:
                file.write(content)
            
            print "Contenido entre corchetes en %s ha sido descargado y guardado." % archivo
            print "Decodificando archivo zip" 

            time.sleep(1)
            # Decodificar y guardar como archivo zip
            base64_bytes = content.encode("utf-8")
            with open("/home/pi/update.zip", "wb") as file_to_save:
                decode_data = base64.decodestring(base64_bytes)
                file_to_save.write(decode_data)


            #-------------Alejandro Valencia Revision de peso de archivo txt descargado
            
            time.sleep(2)
            print ">>>>>> El tamano Esperado del archivo txt en Bytes es: " + str(int(tamanio))
            if os.path.exists('/home/pi/%s.txt' % nombre):
                tamanio_del_archivo = int(os.path.getsize('/home/pi/%s.txt' % nombre))
                tamanio = int(tamanio)
                if len(str(tamanio_del_archivo)) > 0:
                    print ">>>>>> El tamano del archivo txt en Bytes es: " + str(int(tamanio_del_archivo))
                if len(str(tamanio_del_archivo)) > 3:
                    print ">>>>>> El tamano del archivo txt en KBytes es: " + str(int(tamanio_del_archivo) / 1024)
                if len(str(tamanio_del_archivo)) > 6:
                    print ">>>>>> El tamano del archivo txt en MBytes es: " + str(int(tamanio_del_archivo) / 1024 / 1024)

                if int(tamanio) == int(tamanio_del_archivo):
                    print "El tamano de los archivos coinciden"
                    return ActualizarArchivos(tamanio)
                
                if int(tamanio) != int(tamanio_del_archivo):
                    print "El tamano de los archivos no coinciden"
                    if int(tamanio) > int(tamanio_del_archivo):
                        print "El archivo txt creado es menor por %d Bytes" % (tamanio - tamanio_del_archivo)
                    elif int(tamanio) < int(tamanio_del_archivo):
                        print "El archivo txt creado es mayor por %d Bytes" % (tamanio_del_archivo - tamanio)
                    print "Borrando archivo txt y zip creados..."
                    subprocess.call('rm -rfv /home/pi/%s.txt' % nombre, shell=True)
                    subprocess.call('rm -rfv /home/pi/update.zip', shell=True)
                    i_AT += 1
                    continue
                
            else:
                print "No se puede leer el tamano del archivo: %s.txt" % nombre
                if intentos_actualizacion >= 2:
                    respFTP = "eTXTRPI"#Mandar Error [eTXTRPI]
            time.sleep(1)
            return False
        except Exception, e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print "FTP.py,", exc_tb.tb_lineno, " Error al leer archivo: " + str(e)
            if intentos_actualizacion >= 2:
                respFTP = "eCrearTXT"#Mandar Error [eCrearTXT]
                return False
            i_AT += 1
            continue
    # Termina while
    if intentos_actualizacion >= 2:
        respFTP = "eLeerArchivo"#Mandar Error [eLeerArchivo]
    return False
        

    

def ActualizarArchivos(tamanio_esperado):
    global nombre, intentos_ftp, tipo, respFTP
    time.sleep(1)
    timeCheck.lastConnection = time.time() # Reporta actividad 
    filename = '/home/pi/update.zip'

    try:
        if os.path.exists(filename):
            #-------------Alejandro Valencia Revision de peso de archivo zip descargado
            if os.path.exists('/home/pi/update.zip'):
                tamanio_del_archivo = os.path.getsize('/home/pi/update.zip')
                if len(str(tamanio_del_archivo)) > 0:
                    print ">>>>>> El tamano del archivo zip en Bytes es: " + str(int(tamanio_del_archivo))
                if len(str(tamanio_del_archivo)) > 3:
                    print ">>>>>> El tamano del archivo zip en KBytes es: " + str(int(tamanio_del_archivo) / 1024)
                if len(str(tamanio_del_archivo)) > 6:
                    print ">>>>>> El tamano del archivo zip en MBytes es: " + str(int(tamanio_del_archivo) / 1024 / 1024)
            else:
                print "No se puede leer el tamano del archivo: update.zip"
            
            time.sleep(5)
                
            print("Descomprimiendo...")
            subprocess.call('pwd', shell=True)
            subprocess.call('rm -rf /home/pi/update.txt', shell=True)
            subprocess.call('rm -rf /home/pi/%s.txt' % nombre, shell=True)

            if not os.path.exists("/home/pi/actualizacion/"):
                os.makedirs("/home/pi/actualizacion/")
            
            subprocess.call("mv -f /home/pi/update.zip /home/pi/actualizacion/", shell=True)
            
            if os.path.exists("/home/pi/update/"):
                subprocess.call('rm -rf /home/pi/update/', shell=True)
            
            subprocess.call("unzip -o /home/pi/actualizacion/update.zip -d /home/pi/", shell=True)
            time.sleep(2)
            print(".zip descomprimido")
                
            if os.path.exists("/home/pi/update/"):
                print("Carpeta descomprimida: update")
                print("Borrando zip...")
                subprocess.call('rm -rf /home/pi/actualizacion/update.zip', shell=True)
                
                #------------------Alejandro Valencia Actualizacion de archivos
                if tipo == "Software":
                    if os.path.exists("/home/pi/antigua/"):
                        subprocess.call('sudo chmod -R a+rwx /home/pi/antigua/', shell=True)
                        subprocess.call('sudo rm -rf /home/pi/antigua/', shell=True)
                    
                    print "Moviendo carpeta %s a carpeta 'antigua'..." % carpetaSoftware
                    subprocess.call('mv -f /home/pi/%s/ /home/pi/antigua/' % carpetaSoftware, shell=True)
                    print "Haciendo que carpeta update sea nueva %s..." % carpetaSoftware
                    subprocess.call('mv -f /home/pi/update/ /home/pi/%s/' % carpetaSoftware, shell=True)
                    print "Regresando archivos originales, manteniendo los actualizados..."
                    subprocess.call('cp -rn /home/pi/antigua/* /home/pi/%s/' % carpetaSoftware, shell=True)
                    time.sleep(5)
                    print "Eliminando carpeta antigua..."
                    subprocess.call('sudo chmod -R a+rwx /home/pi/antigua/', shell=True)
                    subprocess.call('rm -rf /home/pi/antigua/', shell=True)
                    print "Dando permisos a carpeta %s" % carpetaSoftware
                    subprocess.call('sudo chmod -R a+rwx /home/pi/%s/' % carpetaSoftware, shell=True)
                        
                elif tipo == "Lista.db":
                    #Actualizacion de archivo especificos
                    print "Copiando archivos de update a %s" % carpetaSoftware
                    subprocess.call('cp -rf /home/pi/update/* /home/pi/%s/' % carpetaSoftware, shell=True)
                    print "Eliminando carpeta update..."
                    subprocess.call('rm -rf /home/pi/update/', shell=True)
                    subprocess.call('sudo chmod -R a+rwx /home/pi/%s/' % carpetaSoftware, shell=True)

                if os.path.exists("/home/pi/%s/verificar_carpeta.py" % carpetaSoftware):
                    subprocess.call('mv -f /home/pi/%s/verificar_carpeta.py /home/pi/actualizacion/' % carpetaSoftware, shell=True)
                    print "Archivo verificar_carpeta.py movido"

                # Borando archivos del quectel
                enviaComando("AT+QFDEL=\"update.txt\"")
                enviaComando("AT+QFDEL=\"%s.txt\"" % nombre)

                print "#############################################"
                print "Actualización completada..."
                print "#############################################"

                if tipo == "Software":
                    respFTP = "FTPOK"#Mandar [FTPOK]
                    # subprocess.call("sudo reboot now", shell=True)
                elif tipo == "Lista.db":
                    variables_globales.version_tarjetas = str(nombre)
                    respFTP = "FTPOK"#Mandar [FTPOK]
                return True
                
            elif os.path.exists("/home/pi/tarjetas.db"):
                print "No existe la carpeta descomprimida como /home/pi/update/"
                print "Existe el archivo tarjetas.db"
                time.sleep(5)
                subprocess.call('rm -rf /home/pi/actualizacion/update.zip', shell=True)
                # Mueve el .db a su ubicacion necesaria y dando permisos a carpeta de software
                subprocess.call('mv -v /home/pi/tarjetas.db /home/pi/' + carpetaSoftware + '/data/db/', shell=True)
                subprocess.call('sudo chmod -R a+rwx /home/pi/' + carpetaSoftware + '/', shell=True)  # Carpeta recursiva

                # Borra archivos del quectel
                enviaComando("AT+QFDEL=\"update.txt\"")
                enviaComando("AT+QFDEL=\"" + nombre + ".txt\"")

                # variables_globales.version_de_MT = nombre
                # print "La version de MT en vg es: ", variables_globales.version_de_MT
                # insertar_estadisticas_boletera(str(datos_de_la_unidad[1]), fecha, variables_globales.hora_actual, "MT", variables_globales.version_de_MT) # Matriz tarifaría

                print "#############################################"
                #print "Actualización completada, Reiniciando boletera..."
                print "Actualización completada..."
                print "#############################################"
                variables_globales.version_tarjetas = str(nombre)
                
                print "La version de DB es: " + str(variables_globales.version_tarjetas)

                respFTP = "FTPOK"# Mandar [FTPOK]

                return True
            else:
                print "No existe la carpeta descomprimida como /home/pi/update/"
                print "No existe un archivo descomprimido del tipo .db"
                subprocess.call('rm -rf /home/pi/actualizacion/update.zip', shell=True)
            print "#############################################"
            print "Algo fallo"
            print "#############################################"
            if intentos_actualizacion >= 2:
                respFTP = "eCARPETAoDB"#Mandar Error [eCARPETAoDB]
            return False
        else:
            print "No se encontró el archivo"
            time.sleep(1)
            if intentos_actualizacion >= 2:
                respFTP = "eNOZIP"#Mandar Error [eNOZIP]
            return False
    except Exception, e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print "FTP.py,", str(exc_tb.tb_lineno) + str(e)
        if intentos_actualizacion >= 2:
            respFTP = "eUnknown"#Mandar Error [eUnknown]
        return False



def cerrar_conexion_ftp():
    if 'OK' in enviaComando('AT+QFTPCLOSE').strip():
        print "Conexion FTP cerrada."
    else:
        print "Error al cerrar la conexion FTP."


#----------------------------------------------------------Main
def main(objSerial,objCK,size = False):
    global quectelUSB,timeCheck
    try:
        timeCheck = objCK
        #objSerial.open3G()
        #quectelUSB = quectelUSB = serial.Serial('/dev/ttyUSB_0', baudrate=115200, timeout=5)
        quectelUSB = objSerial.ser3G
        inicio = 0
        while inicio < 3:
            time.sleep(1)
            timeCheck.lastConnection = time.time()
            ok = QuectelON()
            if ok:
                if size == False:
                    ok = ConfigurarFTP("azure") #Actualizacion de Tarjetas
                else:
                    ok = ConfigurarFTP("azure",size) #Actualizacion de Software
                
                if ok:
                    print "--------------CORRECTO----------------"
                    cerrar_conexion_ftp()
                    break
                else:
                    print "--------------INCORRECTO----------------"
                    cerrar_conexion_ftp()
                    break
            else:
                print "No se obtuvo respuesta del quectel..."
                inicio = inicio + 1
                continue
        return respFTP
    except Exception, e:
        print e
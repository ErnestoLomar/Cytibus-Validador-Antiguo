import sqlite3
from datetime import datetime
import time

URI = "/home/pi/innobusmx/data/db/alttusti.db"

#Creando una tabla llamada geocercas_servicios.
tabla_de_aforos = '''CREATE TABLE aforos (
    aforo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    UID TEXT(20),
    total INTEGER,
    fecha DATE,
    hora TIME,
    latitud TEXT(20),
    longitud TEXT(20),
    transportista INT,
    num_economico INT,
    check_servidor TEXT(10) default 'NO'
)'''

def crear_tabla_de_aforos():
    try:
        #Establecemos la conexion con la base de datos
        con = sqlite3.connect(URI)
        cur = con.cursor()
        #Ejecutando la sentencia SQL en la variable `tabla_geocercas_servicios`.
        cur.execute(tabla_de_aforos)
        con.close()
    except Exception, e:
        print "No se pudo crear la tabla de aforos mipase" + str(e)
        
def registrar_aforo_mipase(UID, total, fecha, hora, latitud, longitud, transportista, num_economico):
    try:
        #Creamos la conexion con la base de datos
        con = sqlite3.connect(URI)
        cur = con.cursor()
        cur.execute("INSERT INTO aforos(UID, total, fecha, hora, latitud, longitud, transportista, num_economico) VALUES ('{}' , '{}' , '{}' , '{}', '{}' , '{}' , '{}' , '{}')".format(UID, total, fecha, hora, latitud, longitud, transportista, num_economico))
        con.commit()
        con.close()
        return True
    except Exception, e:
        print "Fallo al registrar aforo de mipase: " + str(e)
        return False

def obtener_estado_de_todas_las_ventas_no_enviadas():
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM aforos WHERE check_servidor = 'NO' LIMIT 1")
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception, e:
        print "Fallo al obtener todos los aforos de mipase: " + str(e)

def actualizar_estado_aforo_mipase_check_servidor(estado, id):
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("UPDATE aforos SET check_servidor = ? WHERE aforo_id = ?", (estado,id))
        conexion.commit()
        conexion.close()
        return True
    except Exception, e:
        print "Fallo al actualizar check_servidor aforo mipase: " + str(e)
        return False
    
def obtener_aforos_antiguos(fecha_limite):
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM aforos WHERE fecha >= '{}'".format(fecha_limite))
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception, e:
        print "Fallo al obtener todos los aforos antiguos de mipase: " + str(e)
        
def eliminar_aforos_antiguos(fecha_limite):
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM aforos WHERE fecha < '{}'".format(fecha_limite))
        conexion.commit()
        conexion.close()
        return True
    except Exception, e:
        print "Fallo al eliminar aforos antiguos de mipase: " + str(e)
        return False
    
def periodo_5Mins_MiPase(csn):
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("SELECT fecha, hora FROM aforos WHERE UID = '{}' ORDER BY fecha DESC, hora DESC LIMIT 1".format(csn))
        data = cursor.fetchone()
        
        if data is None:
            conexion.close()
            return True
        else:
            tsDel = datetime.strptime(data[0] + ' ' + data[1], '%Y-%m-%d %H:%M:%S')
            tsAl = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
            td = tsAl - tsDel
            conexion.close()
            return int(round(td.total_seconds() / 60)) > 5
#crear_tabla_de_aforos()

##########################################################################################################
##########################################################################################################
##########################################################################################################

tabla_estadisticas = ''' CREATE TABLE IF NOT EXISTS estadisticas (
    idMuestreo INTEGER PRIMARY KEY AUTOINCREMENT,
    unidad TEXT(10),
    transportista INTEGER,
    fecha date,
    hora time,
    columna_db TEXT(30),
    valor_columna TEXT(50),
    check_servidor TEXT(10) default 'NO'
) '''

def crear_tabla_de_estadisticas():
    try:
        #Establecemos la conexion con la base de datos
        con = sqlite3.connect(URI)
        cur = con.cursor()
        #Ejecutando la sentencia SQL en la variable `tabla_geocercas_servicios`.
        cur.execute(tabla_estadisticas)
        con.close()
    except Exception, e:
        print "No se pudo crear la tabla de estadisticas alttus: " + str(e)
        
def insertar_estadisticas_alttus(unidad, transportista, fecha, hora, columna, valor):
    try:
        con = sqlite3.connect(URI)
        cur = con.cursor()
        cur.execute("INSERT INTO estadisticas(unidad, transportista, fecha, hora, columna_db, valor_columna) VALUES (?, ?, ?, ?, ?, ?)", (unidad, transportista, fecha, hora, columna, valor))
        con.commit()
        con.close()
        return True
    except Exception, e:
        print "No se pudo insertar estadistica de alttus: " + str(e)
        return False

def obtener_estadisticas_no_enviadas():
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM estadisticas WHERE check_servidor = 'NO' LIMIT 1")
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception, e:
        print "Fallo al obtener todas las estadisticas: " + str(e)

def actualizar_estado_estadistica_check_servidor(estado, id):
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("UPDATE estadisticas SET check_servidor = ? WHERE idMuestreo = ?", (estado,id))
        conexion.commit()
        conexion.close()
        return True
    except Exception, e:
        print "Fallo al actualizar check_servidor de estadisticas: " + str(e)
        return False
    
def obtener_estadisticas_antiguas(fecha_limite):
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM estadisticas WHERE fecha >= '{}'".format(fecha_limite))
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception, e:
        print "Fallo al obtener todas las estadisticas antiguas de mipase: " + str(e)
        
def eliminar_estadisticas_antiguas(fecha_limite):
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM estadisticas WHERE fecha < '{}'".format(fecha_limite))
        conexion.commit()
        conexion.close()
        return True
    except Exception, e:
        print "Fallo al eliminar estadisticas antiguas de mipase: " + str(e)
        return False
    
def obtener_ultima_ACT():
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM estadisticas WHERE columna_db = 'ACT' ORDER BY idMuestreo DESC LIMIT 1")
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception, e:
        print "Fallo al obtener ultima estadistica ACT: " + str(e)
        
def obtener_ultima_ACT_no_enviada():
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM estadisticas WHERE columna_db = 'ACT' AND check_servidor = 'NO' ORDER BY idMuestreo DESC LIMIT 1")
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception, e:
        print "Fallo al obtener ultima estadistica ACT: " + str(e)
        
def eliminar_todas_las_estadisticas_ACT():
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM estadisticas WHERE columna_db = 'ACT' AND check_servidor = 'NO'")
        conexion.commit()
        conexion.close()
        return True
    except Exception, e:
        print "Fallo al eliminar estadisticas ACT: " + str(e)
        return False
        
def obtener_trama_FTP():
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM estadisticas WHERE columna_db = 'FTP' AND check_servidor = 'NO' ORDER BY idMuestreo DESC LIMIT 1")
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception, e:
        print "Fallo al obtener ultima estadistica FTP: " + str(e)
    
#crear_tabla_de_horas()v

##########################################################################################################
##########################################################################################################
##########################################################################################################

def crear_tablas():
    crear_tabla_de_aforos()
    crear_tabla_de_estadisticas()

#crear_tablas()
import sqlite3

URI = "/home/pi/innobusmx/data/db/parametros.db"

tabla_parametros = ''' CREATE TABLE IF NOT EXISTS parametros (
    idTransportista int(4),
    idUnidad int(5),
    puertoSocket int(10),
    enviarDatosAzure int(1)
) '''

def crear_tabla_de_parametros():
    try:
        #Establecemos la conexion con la base de datos
        con = sqlite3.connect(URI)
        cur = con.cursor()
        #Ejecutando la sentencia SQL en la variable `tabla_geocercas_servicios`.
        cur.execute(tabla_parametros)
        con.close()
    except Exception, e:
        print "No se pudo crear la tabla de parametros alttus: " + str(e)

def obtener_parametros():
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM parametros")
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception, e:
        print "Fallo al obtener el puertoSocket: " + str(e)
        
def actualizar_socket(puerto):
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("UPDATE parametros SET puertoSocket = ?", (puerto,))
        conexion.commit()
        conexion.close()
        return True
    except Exception, e:
        print "Fallo al actualizar puertoSocket: " + str(e)
        return False
    
def actualizar_enviarDatosAzure(enviar):
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("UPDATE parametros SET enviarDatosAzure = ?", (enviar,))
        conexion.commit()
        conexion.close()
        return True
    except Exception, e:
        print "Fallo al actualizar enviarDatosAzure: " + str(e)
        return False
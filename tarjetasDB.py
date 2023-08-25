import sqlite3

URI = "/home/pi/innobusmx/data/db/tarjetas.db"

#Creando una tabla llamada geocercas_servicios.
tabla_de_lista = '''CREATE TABLE lista (
    UID TEXT(20) PRIMARY KEY,
    lista BOOLEAN,
    mensaje INT,
    saldo INT
)'''

def crear_tabla_de_lista():
    try:
        #Establecemos la conexion con la base de datos
        con = sqlite3.connect(URI)
        cur = con.cursor()
        #Ejecutando la sentencia SQL en la variable `tabla_geocercas_servicios`.
        cur.execute(tabla_de_lista)
        con.close()
    except Exception, e:
        print "No se pudo crear la lista de tarjetas mipase: " + str(e)
        
def obtener_tarjeta_mipase_por_UID(UID):
    try:
        con = sqlite3.connect(URI)
        cur = con.cursor()
        cur.execute("SELECT * FROM lista WHERE UID = ? LIMIT 1", (UID,))
        operador = cur.fetchone()
        con.close()
        return operador
    except Exception, e:
        print "No se pudo obtener la tarjeta de mipase: " + str(e)
        
def obtener_tarjetas_por_lista(lista):
    try:
        con = sqlite3.connect(URI)
        cur = con.cursor()
        cur.execute("SELECT * FROM lista WHERE lista = ?", (lista,))
        operador = cur.fetchone()
        con.close()
        return operador
    except Exception, e:
        print "No se pudo obtener la lista de tarjetas mipase: " + str(e)
        return None
        
#crear_tabla_de_lista()
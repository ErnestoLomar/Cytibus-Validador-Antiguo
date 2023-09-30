import sqlite3

URI = "/home/pi/innobusmx/data/db/codigoErrores.db"

#Creando una tabla llamada geocercas_servicios.
tabla_de_codigos = '''CREATE TABLE codigos(
    codigo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo INTEGER,
    descripcion TEXT(50)
)'''

def crear_tabla_de_codigos():
    try:
        #Establecemos la conexion con la base de datos
        con = sqlite3.connect(URI)
        cur = con.cursor()
        #Ejecutando la sentencia SQL en la variable `tabla_geocercas_servicios`.
        cur.execute(tabla_de_codigos)
        con.close()
    except Exception, e:
        print "No se pudo crear la tabla de codigos alttus: " + str(e)

def obtener_descripcion_de_codigo(codigo):
    try:
        conexion = sqlite3.connect(URI)
        cursor = conexion.cursor()
        cursor.execute("SELECT * FROM codigos WHERE codigo = ?", (codigo))
        resultado = cursor.fetchall()
        conexion.close()
        return resultado
    except Exception, e:
        print "Fallo al obtener la descripcion del codigo: " + str(e)
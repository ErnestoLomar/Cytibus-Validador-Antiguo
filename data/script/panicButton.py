import RPi.GPIO as GPIO
import time
import sqlite3
import time

#cdDbA = '/home/pi/innobusvalidador/data/db/alarmas'
cdDbA = '/home/pi/innobusmx/data/db/alarmas'

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
    input_state = GPIO.input(17)
    if input_state == False:
        print 'Button Pressed'
        conn = sqlite3.connect(cdDbA)
        c = conn.cursor()
        fecha = time.strftime("%Y-%m-%d %H:%M:%S")
        #Proceso se mantiene para toda la parte comunicacion, en este caso el maestro
        #enviara el SMS :O
        c.execute("INSERT INTO sensor(fechaHora, nameSensor, enviado) VALUES(?, ?, ?)", (fecha, 'Panico', 0))
        conn.commit()
        c.close()
        time.sleep(1)

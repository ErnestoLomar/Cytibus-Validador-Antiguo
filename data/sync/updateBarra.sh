#!/bin/bash

: '
  @utor: Hiram Zúñiga (bender)
  Script que aztualiza el codigo del sistema innobusmx de manera
  automatica, esto es si se realiza una mejora en el codigo de
  alguna funcion del sistema y necesita ser reiniciado el sistema
  realizara las tareas necesarias para que la actualizacion surta
  efecto unaa vez que se realizaron las funciones correspondientes
  durante la actualizacion.
  Falta cambiar el path para que sea barras que se elimine y sea
  baras el que se descargue no el test que estoy haciendo.
  '
#kill -9 'ps -ef|grep -v grep |grep $1| awk '{print $2}''
#cd /home/pi/
cd /home/pi/innobusvalidador/data/script/
pwd
#rm -r /home/pi/prueba/* solo los archivos
rm -r test
#wget http://innothatexais/versiones/barras_current.tar.bz2
wget http://192.168.1.5/test/prueba.tar.gz
tar -xvzf prueba.tar.gz
rm prueba.tar.gz
#cp /home/hiram/Descargas/nuevaOrigen.jpg /home/hiram/sistemaViejo/


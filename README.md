# Cytibus-Validador-Antiguo

- vA2.59X:
  - Se modifico la tarifa.
- vA2.58X:
  - Se agrego el nuevo transportista llamado GPT.
- vA2.57X:
  - Se quito la detección de las tarjetas Mi Pase.
- vA2.54X:
  - Se modificaron las geocercas de inicio/fin de la ruta 11 en la base de datos, pasando de "22.1383949999337, -100.892772674561" a "22.1383252828312, -100.894431363049" de los idRuta 12,13,14,15.
  - Se modificaron las geocercas de inicio/fin de la ruta 25 'Los Gomez' en la base de datos, pasando de "22.1694821826313, -100.877022743225" a "22.1690397426632, -100.82894337072" del idRuta 22.
- vA2.53X:
  - Se modificaron las geocercas de inicio/fin de las tres rutas 14 en la base de datos, pasando de "22.196762204443920,  -100.931326418629100" a "22.196573661187553, -100.9329936364836" de los idRuta 43,54,55.
- vA2.52X:
  - Se modificaron las geocercas de inicio/fin de las tres rutas 5 en la base de datos flota, pasando de "22.138183820109, -100.90083271265" a "22.138506800889100, 22.138506800889100" de los idRuta 49-51.
  - Se modificaron las geocercas de inicio/fin de las tres rutas 14 en la base de datos, pasando de "22.1969019611389, -100.929594039917" a "22.196762204443920,  -100.931326418629100" de los idRuta 43,54,55.
- vA2.51X:
  - Se actualizaron tarifas de aforos, preferente de $5 a $5.75.
- vA2.50X:
  - Se actualizaron tarifas de aforos, preferente de $5.75 a $5.
- vA2.49X:
  - Se actualizaron tarifas de aforos, normal de $11.50 a $11.
- vA2.48X:
  - Se actualizaron tarifas de aforos, normal de $11.50 a $10.50
- vA2.47X:
  - Se actualizaron tarifas de aforos, estudiante de $5 a $5.75, efectivo de $11 a $10 y normal de $10 a $11.50
- vA2.46X:
  - Se comento el envió de tramas RDY.
  - Se fusiono en el software la compatibilidad con cualquier version de tablilla.
- vA2.45h:
  - Se modifico la cantidad de creación de tramas GPS de 3 veces, 1 vez si y 2 veces no.
  - Se quito la creación de tramas pánico.
- vA2.44h:
  - Se arreglo el bug de la duplicidad de las tramas ACT.
  - Se redujo la cantidad de creación de tramas GPS de Cytibus.
- vA2.43V:
  - Variante de la version 2.43h
  - La detección de tarjetas en directamente por autorización de la base de datos del validador.
  - El sonido del zumbador es emitido mediante un GPIO.
- vA2.43h:
  - Ya no se crean las tramas 9.
  - Las ACT se envían cada hora.
- vA2.42h:
  - Se modifico el código de ClModem para que ya no se reinicia el sistema cuando no tiene un GPS conectado.
- vA2.41h:
  - X
- vA2.32h:
  - X
- vA2.31h:
  - Se agregaron 2 bases de datos nuevas, "alttusti" y "tarjetas".
  - El validador ahora puede aceptar tarjetas de Mi Pase.
  - El validador es capaz de comunicarse con el servidor de Cytibus y servidor de Mi Pase.
  - Se agrego un icono en la pantalla principal de *Mi pasee*, que se muestra parpadeando si la conexión es intermitente o la imagen fija cuando tiene buena conexión.
  - El validador es capaz de enviar tramas 9 de estadísticas.
  - El validador es capaz de actualizar su base de datos *tarjetas* todos los días a las 04:37:00.
  - Se puede actualizar el validador a la distancia por FTP desde el servidor Azure.
- v1.14mt:
  - Software original Cytibus de validador antiguo.
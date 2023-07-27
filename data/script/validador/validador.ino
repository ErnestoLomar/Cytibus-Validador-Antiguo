#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN   10    //
#define SS_PIN    9     //

int bien = 5;
int mal = 6;
int mus = 7;

MFRC522 mfrc522(SS_PIN, RST_PIN); // Create MFRC522 instance
MFRC522::MIFARE_Key key;

void setup() {

        Serial.begin(115200);   // Initialize serial communications with the PC

        for (byte i = 0; i < 6; i++) {
          key.keyByte[i] = 0xFF;
        }

         pinMode(bien, OUTPUT);
         pinMode(mal, OUTPUT);
         pinMode(mus, OUTPUT);
         beep(200);
         digitalWrite(bien, HIGH);
         beep(60);
         digitalWrite(bien, LOW);
         digitalWrite(mal, HIGH);
         beep(500);
         digitalWrite(mal, LOW);

        SPI.begin();
        mfrc522.PCD_Init();
}

void loop(){
  // Look for new cards
  if ( ! mfrc522.PICC_IsNewCardPresent())
    return;
  // Select one of the cards
  if ( ! mfrc522.PICC_ReadCardSerial())
    return;

    cobrar(mfrc522.uid.uidByte, mfrc522.uid.size);
  //CSNET();

   mfrc522.PICC_HaltA(); // Halt PICC
   mfrc522.PCD_StopCrypto1();  // Stop encryption on PCD

}

void cobrar(byte *buffer, byte bufferSize) {

    byte ch; // the character that you use to construct the Message
    char msg[16];
    String csn;

      /*
        Eliminarlas despues de probar la ev2
      */
      byte status;
      int inAforo[5];
      String aforo;
      int intAforo;
      const char *noAplico = "No Valida";
      const char *noSaldo = "Sin Saldo";
      const char *aplicado = "Puedes subir";
      const char *TN = "Tarifa Normal";
      const char *TP = "Tarifa Preferencial";
      const char *YC = "Llego un cero";
      const char *NViajes = "Te restan";
      const char *RViajes = "viajes";
      //const char *eLectura = "Error de lectura";



    for (byte i = 0; i < bufferSize; i++) {
      csn += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
      csn += String(mfrc522.uid.uidByte[i], HEX);
    }
    csn.toUpperCase();

    //este if es solo para cuando cae en 7bytes entonces
    //despues borrar este if y obvio el else dejarlo solo
    // osea sin else
    //Serial.print(bufferSize);
    if (bufferSize == 0x07){
      Serial.println(csn);
      //Serial.println("EV2");
    }
    else{
      /*
        Firma digital
        Tipo Tisc
        Fecha
      */
      String firmaUnoS = "";
      String firmaDosS = "";
      String firmaTresS = "";

      String tipoTiscS = "";
      String fechaCaduS = "";

      String tipoTarifaS = "";

      byte firmaUno       = 4;
      byte firmaDos       = 5;
      byte firmaTres      = 6;
      byte trailerFirma   = 7;

      byte tipoTisc       = 8;
      byte fechaCadu      = 10;
      byte traileVali     = 11;

      byte tipoTarifa     = 14;
      byte trailerTarifa  = 15;

      byte blockAddr      = 16;
      byte trailerBlock   = 19;
      byte bufferSaldo[18];
      String saldoS;

      byte status;
      byte bufferFirma[18];
      byte bufferFirmaDos[18];
      byte bufferFirmaTres[18];
      byte size = sizeof(bufferFirma);

      byte bufferTipoTisc[18];
      byte bufferFechaCad[18];
      byte bufferTipoTarifa[18];

      int inAforo[5];
      String aforo;
      int intAforo;
      const char *noAplico = "No Valida";
      const char *noSaldo = "Sin Saldo";
      const char *aplicado = "Puedes subir";
      const char *TN = "Tarifa Normal";
      const char *TP = "Tarifa Preferencial";
      const char *YC = "Llego un cero";
      const char *NViajes = "Te restan";
      const char *RViajes = "viajes";

      unsigned long saldo = 0;
      unsigned long s = 0;  

      //const char *eLectura = "Error de lectura";

      // Authenticate using key A
      //Serial.println(F("Authenticating using key A..."));
      status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerFirma, &key, &(mfrc522.uid));
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("PCD_Authenticate() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00031");
        //errorLectura();
        return;
      }
      // Read data from the block
      status = mfrc522.MIFARE_Read(firmaUno, bufferFirma, &size);
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("MIFARE_Read() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00032");
        ////errorLectura();
        return;
      }

      for (int i = 0; i < 16; i++) {
        firmaUnoS += String(bufferFirma[i], HEX);
      }

      status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerFirma, &key, &(mfrc522.uid));
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("PCD_Authenticate() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00031");
        ////errorLectura();
        return;
      }
      // Read data from the block
      status = mfrc522.MIFARE_Read(firmaDos, bufferFirmaDos, &size);
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("MIFARE_Read() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00032");
        //errorLectura();
        return;
      }

      for (int i = 0; i < 16; i++) {
        firmaDosS += String(bufferFirmaDos[i], HEX);
      }

      status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerFirma, &key, &(mfrc522.uid));
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("PCD_Authenticate() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00031");
        //errorLectura();
        return;
      }
      // Read data from the block
      status = mfrc522.MIFARE_Read(firmaTres, bufferFirmaTres, &size);
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("MIFARE_Read() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00032");
        //errorLectura();
        return;
      }

      for (int i = 0; i < 16; i++) {
        //firmaTresS += String(bufferFirmaTres[i] < 0x10 ? "0" : "");
        firmaTresS += String(bufferFirmaTres[i], HEX);
      }

      firmaUnoS.toUpperCase();
      firmaDosS.toUpperCase();
      firmaTresS.toUpperCase();

      //######################################################################################################

        status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, traileVali, &key, &(mfrc522.uid));
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("PCD_Authenticate() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00031");
        //errorLectura();
        return;
      }
      // Read data from the block
      status = mfrc522.MIFARE_Read(tipoTisc, bufferTipoTisc, &size);
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("MIFARE_Read() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00032");
        //errorLectura();
        return;
      }

      for (int i = 0; i < 2; i++) {
        tipoTiscS += String(bufferTipoTisc[i], HEX);
      }

      status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, traileVali, &key, &(mfrc522.uid));
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("PCD_Authenticate() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00031");
        //errorLectura();
        return;
      }
      // Read data from the block
      status = mfrc522.MIFARE_Read(fechaCadu, bufferFechaCad, &size);
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("MIFARE_Read() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00032");
        //errorLectura();
        return;
      }

      for (int i = 0; i < 6; i++) {
        fechaCaduS += String(bufferFechaCad[i] < 0x10 ? "0" : "");
        fechaCaduS += String(bufferFechaCad[i], HEX);
      }

      tipoTiscS.toUpperCase();
      fechaCaduS.toUpperCase();

      //######################################################################################################
      status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerTarifa, &key, &(mfrc522.uid));
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("PCD_Authenticate() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00031");
        //errorLectura();
        return;
      }
      // Read data from the block
      status = mfrc522.MIFARE_Read(tipoTarifa, bufferTipoTarifa, &size);
      if (status != MFRC522::STATUS_OK) {
        //Serial.print(F("MIFARE_Read() failed: "));
        ////Serial.println(mfrc522.GetStatusCodeName(status));
        //Serial.println("00032");
        //errorLectura();
        return;
      }

      for (int i = 0; i < 2; i++) {
        tipoTarifaS += String(bufferTipoTarifa[i], HEX);
      }

      tipoTarifaS.toUpperCase();

      byte blkSaldo = 16;

      // Authenticate using key A
      //Serial.println(F("Authenticating using key A..."));
      status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerBlock, &key, &(mfrc522.uid));
      if (status != MFRC522::STATUS_OK) {
        Serial.print(F("PCD_Authenticate() failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return;
      }
      // Read data from the block
      status = mfrc522.MIFARE_Read(blkSaldo, bufferSaldo, &size);
      if (status != MFRC522::STATUS_OK) {
        Serial.print(F("MIFARE_Read() failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return;
      }
      delay(10);

      saldo = (unsigned long)bufferSaldo[0];
      saldo = saldo << 8;
      saldo = saldo + (unsigned long)bufferSaldo[1];
      saldo = saldo << 8;
      saldo = saldo + (unsigned long)bufferSaldo[2];
      saldo = saldo << 8;
      saldo = saldo + (unsigned long)bufferSaldo[3];



      //agregando el envio del folio por serial esto es para poder actualizarlo
      byte sector         = 4;
      byte trailerFolio   = 19;
      byte blkFolio = 18;
      //byte status;
      byte bFolio[18];
      int folio;
      byte sFolio = sizeof(bFolio);

      // Authenticate using key A
      //Serial.println(F("Authenticating using key A..."));
      status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerFolio, &key, &(mfrc522.uid));
      if (status != MFRC522::STATUS_OK) {
        Serial.print(F("1 PCD_Authenticate() failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return;
      }
      // Read data from the block
      status = mfrc522.MIFARE_Read(blkFolio, bFolio, &sFolio);
      if (status != MFRC522::STATUS_OK) {
        Serial.print(F("2 MIFARE_Read() failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return;
      }
      folio = word(bFolio[0],bFolio[1]);

      String strFinal = csn+firmaUnoS+firmaDosS+firmaTresS+tipoTiscS+fechaCaduS+tipoTarifaS+"*"+folio+"*";
      //String strFinal = tipoTarifaS;
      String recibir;
      byte inData[6];
      byte index = 0;
      char inChar=-1;

      Serial.print(strFinal);
      Serial.println(saldo);
    }
    delay(120);

  /////////////////////////////////////////////////////////////
  //#########################################################//
  /////////////////////////////////////////////////////////////
  //Espero el aforo para poder cobrar
  byte lenSaldo = 6;
  byte inSaldo[lenSaldo+1];
  byte maxLenSaldo = 5;
  String strSaldo;
  byte buf[18];
  unsigned long s = 0; 

  while (Serial.available() < 5) {} // Wait 'till there are 9 Bytes waiting
  for (int n = 0; n < maxLenSaldo; n++) {
    inSaldo[n] = Serial.read() - '0'; // Then: Get them.
    strSaldo += String(inSaldo[n]);
  }

    String saldoTotalSA = strSaldo + '*';


    if(saldoTotalSA == "11111*"){
      //EV2
      Serial.println("OK");
      digitalWrite(bien, HIGH);
      beep(2000);
      delay(2500);
      //delay(100);
      digitalWrite(bien, LOW);
    }
    if(saldoTotalSA=="99999*"){
      digitalWrite(mal, HIGH);
      beep(60);
      beep(60);
      beep(60);
      beep(60);
      beep(60);
      Serial.println("NO");
      delay(3000);
      digitalWrite(mal, LOW);
    }
    else{
      unsigned long saldo = 0;
      saldo = strSaldo.toInt();
      buf[3] = (unsigned byte)saldo;
      s = saldo >> 8;
      buf[2] = (unsigned byte)s;
      s = saldo >> 16;
      buf[1] = (unsigned byte)s;
      s = saldo >> 24;
      buf[0] = (unsigned byte)s;

      //########
      byte block = 16;
      //########
      status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, block, &key, &(mfrc522.uid));
      if (status != MFRC522::STATUS_OK) {
        Serial.print(F("PCD_Authenticate() failed: 1"));
        //Serial.println(mfrc522.GetStatusCodeName(status));
        return;
      }
      else Serial.print(F(""));

      // Write block
      status = mfrc522.MIFARE_Write(block, buf, 16);
      if (status != MFRC522::STATUS_OK) {
        Serial.print(F("MIFARE_Write() failed: 2"));
        //Serial.println(mfrc522.GetStatusCodeName(status));
        return;
      }
      else Serial.print(F(""));

    // Leer Folio
    byte blkFolio = 18;
    byte bFolio[18];
    byte sFolio = sizeof(bFolio);
    unsigned int folio;

      status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, blkFolio, &key, &(mfrc522.uid));
      if (status != MFRC522::STATUS_OK) {
        Serial.print(F("1 PCD_Authenticate() failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return;
      }
      // Read data from the block
      status = mfrc522.MIFARE_Read(blkFolio, bFolio, &sFolio);
      if (status != MFRC522::STATUS_OK) {
        Serial.print(F("2 MIFARE_Read() failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return;
      }
      folio = word(bFolio[0],bFolio[1]);
      folio++;
      bFolio[0] = highByte(folio);
      bFolio[1] = lowByte(folio);
  
      // Incrementa Folio
      status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, blkFolio, &key, &(mfrc522.uid));
      if (status != MFRC522::STATUS_OK) {
        Serial.print(F("8 PCD_Authenticate() failed: 13"));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return;
      }
      else Serial.print(F(""));
      status = mfrc522.MIFARE_Write(blkFolio, bFolio, 16);
      if (status != MFRC522::STATUS_OK) {
        Serial.print(F("8 MIFARE_Write() failed: 14"));
        Serial.println(mfrc522.GetStatusCodeName(status));
        return;
      }
      else Serial.print(F(""));


      Serial.println("OK");
      digitalWrite(bien, HIGH);
      beep(200);
      delay(2500);
      digitalWrite(bien, LOW);
      delay(200);
    }

  }


void beep(unsigned char delayms){
  digitalWrite(mus, 70);      // Almost any value can be used except 0 and 255
  delay(delayms);          // wait for a delayms ms
  digitalWrite(mus, 0);       // 0 turns it off
  delay(delayms);
}

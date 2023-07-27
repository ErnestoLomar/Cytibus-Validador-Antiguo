#include <SPI.h>
#include <MFRC522.h>
#include <Desfire.h>

#define RST_PIN   10    // 10
#define SS_PIN    9    // 9

int bien = 5;
int mal = 6;
int mus = 7;

DESFire mfrc522(SS_PIN, RST_PIN); // Create MFRC522 instance
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
    
   cobrar();
   //delay(500);
   mfrc522.PICC_HaltA(); // Halt PICC
   mfrc522.PCD_StopCrypto1();  // Stop encryption on PCD
}

void cobrar(){
  int type;
  type = typeOfCard();
  delay(10);
  //Serial.println(type);
  if (type == 1){
    //Serial.print("UL");
    cobrarUL();
  }
  if (type == 2){
    //Serial.print("Calssic");
   cobrarClassic();
  }
  if (type == 3){
   //Serial.print("EV2");
   cobrarEV2();
  }
}

void cobrarUL(){
    byte tipoMifare = 1;
    String csn;
    byte bufferSize = mfrc522.uid.size;
  
    for (byte i = 0; i < bufferSize; i++) {
      csn += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
      csn += String(mfrc522.uid.uidByte[i], HEX);
     }
     csn.toUpperCase();
    
    byte page = 0X0D;
    byte bufferS[18];
    byte byteCount;
    unsigned long saldo = 0;
    byte status;
    
    byteCount = sizeof(bufferS);
    status = mfrc522.MIFARE_Read(page, bufferS, &byteCount);
    if (status != MFRC522::STATUS_OK) {
      Serial.print(F("MIFARE_Read() failed: "));
      Serial.println(mfrc522.GetStatusCodeName(status));
      return;
    }

    saldo = (unsigned long)bufferS[0];
    saldo = saldo << 8;
    saldo = saldo + (unsigned long)bufferS[1];
    saldo = saldo << 8;
    saldo = saldo + (unsigned long)bufferS[2];
    saldo = saldo << 8;
    saldo = saldo + (unsigned long)bufferS[3];

    byte folios = 0X0C;
    byte bufferSS[18];
    byte i;
    byte fW[2];
    byte byteCounts;
    byteCounts = sizeof(bufferSS);
    unsigned int folio;
    status = mfrc522.MIFARE_Read(folios, bufferSS, &byteCounts);
    if (status != MFRC522::STATUS_OK) {
      Serial.print(F("MIFARE_Read() failed: "));
      Serial.println(mfrc522.GetStatusCodeName(status));
      return;
    }

    fW[0] = bufferSS[2];
    fW[1] = bufferSS[3];
   
    folio = word(fW[0],fW[1]);
     //Serial.print("*");
     Serial.print(tipoMifare);
     Serial.print("*");
     Serial.print(csn);
     Serial.print("*");
     Serial.print(saldo);
     Serial.print("*");
     Serial.print(folio);
     Serial.println("*");

     
     
  /////////////////////////////////////////////////////////////
  //#########################################################//
  /////////////////////////////////////////////////////////////
  //Espero el aforo para poder cobrar

  byte lenSaldo = 6;
  byte inSaldo[lenSaldo+1];
  byte maxLenSaldo = 5;
  String strSaldo;
  byte buf[18];
  unsigned long saldoLo = 0;
  unsigned long s = 0;
  
  while (Serial.available() < 5) {} // Wait 'till there are 9 Bytes waiting
  for (int n = 0; n < maxLenSaldo; n++) {
    inSaldo[n] = Serial.read() - '0'; // Then: Get them.
    strSaldo += String(inSaldo[n]);
  }
    //Serial.print(strSaldo);
    
    String saldoTotalSA = strSaldo + '*';

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
    byte bufferSSS[4];
    saldoLo = saldoLo + strSaldo.toInt();
    bufferSSS[3] = (unsigned byte)saldoLo;
    s = saldoLo >> 8;
    bufferSSS[2] = (unsigned byte)s;
    s = saldoLo >> 16;
    bufferSSS[1] = (unsigned byte)s;
    s = saldoLo >> 24;
    bufferSSS[0] = (unsigned byte)s;

    mfrc522.MIFARE_Ultralight_Write(page, bufferSSS, 4);
    if (status != MFRC522::STATUS_OK) {
        Serial.print(F("MIFARE_Write() failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
    }

    byte Lugarfolio = 0X0C;
    byte bufferFolio[18];
    byte fWN[2];
    byte Countss = sizeof(bufferFolio);
    status = mfrc522.MIFARE_Read(Lugarfolio, bufferFolio, &Countss);
    if (status != MFRC522::STATUS_OK) {
      Serial.print(F("MIFARE_Read() failed: "));
      Serial.println(mfrc522.GetStatusCodeName(status));
      return;
    }

    fWN[0] = bufferFolio[2];
    fWN[1] = bufferFolio[3];
   
    folio = word(fWN[0],fWN[1]);
    folio = folio + 1;
    //Serial.print(folio);
    fWN[0] = highByte(folio);
    fWN[1] = lowByte(folio);

    bufferFolio[2] = fWN[0];
    bufferFolio[3] = fWN[1];

    mfrc522.MIFARE_Ultralight_Write(Lugarfolio, bufferFolio,  &Countss);
    if (status != MFRC522::STATUS_OK) {
        Serial.print(F("MIFARE_Write() failed: "));
        Serial.println(mfrc522.GetStatusCodeName(status));
    }
    delay(50);
    Serial.println("OK");
    digitalWrite(bien, HIGH);
    beep(200);
    delay(2800);
    digitalWrite(bien, LOW);
    delay(200);
    }
}

void cobrarEV2(){
    String csn;
    byte bufferSize = mfrc522.uid.size;
    
    byte app[3]           = {0X01,0X00,0X00};
    byte fileOffsetLen[7] = {0X01,0X00,0X00,0X00,0X2F,0X00,0X00};
    byte llaveTipoEstadoIdTipo[47];
    byte sizellaveTipoEstadoIdTipo = 47;
    byte tipoMifare = 3;

    byte appSaldo[3]           = {0X02,0X00,0X00};
    byte fileOffsetLenSaldo[7] = {0X01,0X00,0X00,0X00,0X04,0X00,0X00};
    byte saldo[4];
    byte sizeLen = 7;
    unsigned long saldoL = 0;
     
    byte folio[2];
    unsigned int folioI;

    DESFire::mifare_desfire_tag tag;
    DESFire::StatusCode response;
    tag.pcb = 0x0A;
    tag.cid = 0x00;
    memset(tag.selected_application, 0, 3);
    response.desfire = DESFire::MF_OPERATION_OK;
    byte ats[16];
    byte atsLength = 16;
    response.mfrc522 = mfrc522.PICC_RequestATS(ats, &atsLength);
    if ( ! mfrc522.IsStatusCodeOK(response)) {
      Serial.println(F("Failed to get ATS!"));
      Serial.println(mfrc522.GetStatusCodeName(response));
      Serial.println(response.mfrc522);
      mfrc522.PICC_HaltA();
      return;
    }
    // TODO: Should do checks but since I know my DESFire allows and requires PPS...
    //       PPS1 is ommitted and, therefore, 0x00 is used (106kBd)
    response.mfrc522 = mfrc522.PICC_ProtocolAndParameterSelection(0x00, 0x11);
    if ( ! mfrc522.IsStatusCodeOK(response)) {
      Serial.println(F("Failed to perform protocol and parameter selection (PPS)!"));
      Serial.println(mfrc522.GetStatusCodeName(response));
      mfrc522.PICC_HaltA();
      return;
    }
    mfrc522.MIFARE_DESFIRE_ReadDataInnoParametrosPago(&tag, app, fileOffsetLen, llaveTipoEstadoIdTipo, sizellaveTipoEstadoIdTipo);
    delay(50);

    mfrc522.MIFARE_DESFIRE_ReadDataInnoParametros(&tag, appSaldo, fileOffsetLenSaldo, saldo);
    delay(50);
    
    saldoL = (unsigned long)saldo[0];
    saldoL = saldoL << 8;
    saldoL = saldoL + (unsigned long)saldo[1];
    saldoL = saldoL << 8;
    saldoL = saldoL + (unsigned long)saldo[2];
    saldoL = saldoL << 8;
    saldoL = saldoL + (unsigned long)saldo[3];
    
    for (byte i = 0; i < bufferSize; i++) {
      csn += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
      csn += String(mfrc522.uid.uidByte[i], HEX);
    }
    csn.toUpperCase();


    byte fileOffsetLenFolio[7] = {0X01,0X04,0X00,0X00,0X06,0X00,0X00};
    mfrc522.MIFARE_DESFIRE_ReadDataInnoParametros(&tag, appSaldo, fileOffsetLenFolio, folio);
  
    folioI = word(folio[0],folio[1]);
    folioI++;
    folio[0] = highByte(folioI);
    folio[1] = lowByte(folioI);


    Serial.print(tipoMifare);
    Serial.print(csn);
    for (byte i = 0; i<47; i++){
      Serial.print(llaveTipoEstadoIdTipo[i],HEX);
    }
    Serial.print("*");
    Serial.print(folioI);
    Serial.print("*");
    Serial.print(saldoL);
    Serial.println("*");


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

    //Serial.print(strSaldo);
    String saldoTotalSA = strSaldo + '*';

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
      if (tipoMifare == 3){
        byte fileOffsetLen[7] = {0X01,0X00,0X00,0X00,0X04,0X00,0X00};
        byte saldo[4];
        byte sizeLen = 7;
    
        int maxLenSaldo = 5;
        byte inSaldo[5];
        String saldoS;
        byte bufS[4];
        unsigned long s = 0;
    
        byte folio[2];
        unsigned int folioI;

        unsigned long saldoLo = strSaldo.toInt();

        //Serial.print(saldoLo);
        //delay(10);
    
        bufS[3] = (unsigned byte)saldoLo;
        s = saldoLo >> 8;
        bufS[2] = (unsigned byte)s;
        s = saldoLo >> 16;
        bufS[1] = (unsigned byte)s;
        s = saldoLo >> 24;
        bufS[0] = (unsigned byte)s;
    
        byte fileOffsetLenWriteApp[13] = {0X01,0X00,0X00,0X00,0X06,0X00,0X00,0X00,0X00,0X00,0X00,0X00,0X00};
        byte len = 13;
        
        for(int i=0;i<=3;i++){
          fileOffsetLenWriteApp[7+i] = bufS[i];
        }
        
        byte fileOffsetLenFolio[7] = {0X01,0X04,0X00,0X00,0X06,0X00,0X00};
        mfrc522.MIFARE_DESFIRE_ReadDataInnoParametros(&tag, appSaldo, fileOffsetLenFolio, folio);
      
        folioI = word(folio[0],folio[1]);
        folioI++;
        folio[0] = highByte(folioI);
        folio[1] = lowByte(folioI);
    
        for(int i=0;i<=1;i++){
            fileOffsetLenWriteApp[11+i] = folio[i];
        }
        
        mfrc522.MIFARE_DESFIRE_WriteDataInnoParametros(&tag, appSaldo, fileOffsetLenWriteApp, len);
        delay(100);
        Serial.println("OK");
        digitalWrite(bien, HIGH);
        beep(200);
        delay(2800);
        digitalWrite(bien, LOW);
        delay(200);
      }
    }
}


void cobrarClassic(){
    byte bufferSize = mfrc522.uid.size;
    byte ch; // the character that you use to construct the Message
    char msg[16];
    String csn;
    byte tipoMifare = 2;

      /*
        Eliminarlas despues de probar la ev2
      */
      byte status;
      int inAforo[5];
      String aforo;
      int intAforo;

    for (byte i = 0; i < bufferSize; i++) {
      csn += String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : "");
      csn += String(mfrc522.uid.uidByte[i], HEX);
    }
    csn.toUpperCase();

    if (bufferSize == 0x07){
      Serial.println(csn);
    }
    else{
      /*
        Firma digital
        Tipo Tisc
        Fecha
      */
      String firmaUnoS = "";

      String tipoTiscS = "";
      String fechaCaduS = "";

      String tipoTarifaS = "";

      byte firmaUno       = 4;
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

      firmaUnoS.toUpperCase();

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

  byte sector2         = 3;
  byte blockAddr2      = 12;
  byte trailerBlock2   = 15;
  //byte status;
  byte bufferNombre[18];
  byte size2 = sizeof(bufferNombre);
  String nombre = "";
  int salgo;
  int sinNombre = false;
      
  // Authenticate using key A
  //Serial.println(F("Authenticating using key A..."));
  status = mfrc522.PCD_Authenticate(MFRC522::PICC_CMD_MF_AUTH_KEY_A, trailerBlock2, &key, &(mfrc522.uid));
  if (status != MFRC522::STATUS_OK) {
    Serial.print(F("PCD_Authenticate() failed: "));
    //Serial.println(mfrc522.GetStatusCodeName(status));
    return;
  }
  // Read data from the block
  status = mfrc522.MIFARE_Read(blockAddr2, bufferNombre, &size2);
  if (status != MFRC522::STATUS_OK) {
    Serial.print(F("MIFARE_Read() failed: "));
    //Serial.println(mfrc522.GetStatusCodeName(status));
    return;
  }

    Serial.print(tipoMifare);
    Serial.print(csn);
    Serial.print(firmaUnoS);
    Serial.print(tipoTiscS);
    Serial.print(tipoTarifaS);
     for (byte i = 0; i < 16; i++) {
       Serial.print(bufferNombre[i],HEX);
     }
    Serial.print(fechaCaduS);
    Serial.print("*");
    Serial.print(folio);
    Serial.print("*");
    Serial.print(saldo);
    Serial.println("*");
    
    //String strFinal = tipoTarifaS;
    String recibir;
    byte inData[6];
    byte index = 0;
    char inChar=-1;
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
      delay(2800);
      digitalWrite(bien, LOW);
      delay(200);
    }  
    
}

int typeOfCard(){

 int card = 0;
 if (mfrc522.uid.sak == 0x00) {
    card = 1;
  }
  if (mfrc522.uid.sak == 0x08) {
    card = 2;
  }
  if (mfrc522.uid.sak == 0x18) {
    card = 2;
  }
  if (mfrc522.uid.sak == 0x20) {
    card = 3;
  }
  //Serial.println(card);
  //delay(100);
  return card;
}

void beep(unsigned char delayms){
  digitalWrite(mus, 70);      // Almost any value can be used except 0 and 255
  delay(delayms);          // wait for a delayms ms
  digitalWrite(mus, 0);       // 0 turns it off
  delay(delayms);
}

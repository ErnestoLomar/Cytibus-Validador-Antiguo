/*
  ########################################
           "Consultador 0.02v"
  Create date: 2015/25/09
  Last update: 2017/13/01 -- @HiramZúñiga
  ########################################
*/

#include <SPI.h>
#include <SD.h>
#include <MFRC522.h>
#include <Desfire.h>

#define RST_PIN         10         // Configurable, see typical pin layout above
#define SS_PIN          9         // 10 Configurable, see typical pin layout above
DESFire mfrc522(SS_PIN, RST_PIN);   // Create MFRC522 instance.

MFRC522::MIFARE_Key key;


bool presente = true;
int mensaje = 0;
byte blkSaldo = 16;
int saldo = 0;
int rojo = 2;
int verde = 3;
int azul = A4;
byte blkFolio = 18;

/**
   Inicializar
**/
void setup() {
  
  Serial.begin(115200); // Initialize serial communications with the PC
  SPI.begin();        // Init SPI bus
  mfrc522.PCD_Init(); // Init MFRC522 card
  
  for (byte i = 0; i < 6; i++) {
    key.keyByte[i] = 0xFF;
  }
  
  pinMode(rojo, OUTPUT);
  pinMode(verde, OUTPUT);
  pinMode(azul, OUTPUT);
  
}

/*
  ##################
     Main loop0
  ##################
*/
void loop() {
  // Look for new cards
  mfrc522.PCD_Init(); // Init MFRC522 card
  delay(50);
  if (!mfrc522.PICC_IsNewCardPresent()) {
    if (presente) {
      presente = false;
    }
    else {
      return;
    }
  }
  else {
    if (!presente) {
      //Serial.println("desde");
      enviarDatos();
      delay(200);
      presente = true;
    }
    mensaje = Serial.read();
    if (mensaje == 'c') {
      cobrar();
    }
  }
}

void enviarDatos() {
  int type;
  type = typeOfCard();
  delay(10);
  if (type == 1){
    //cobrarUL();
  }
  if (type == 2){
   //cobrarClassic();
  }
  if (type == 3){
   cobrarEV2();
  }
}

void cobrarEV2(){
  
    String csn;
    byte bufferSize = mfrc522.uid.size;
    
    byte app[3]           = {0X01,0X00,0X00};
    byte fileOffsetLen[7] = {0X01,0X00,0X00,0X00,0X12,0X00,0X00};
    byte llaveTipoEstadoIdTipo[18];
    byte sizellaveTipoEstadoIdTipo = 18;
    byte tipoMifare = 3;


    byte fileOffsetLenET[7] = {0X01,0X18,0X00,0X00,0X01,0X00,0X00};
    byte estadoTarjeta[1];
    byte sizeestadoTarjeta = 1;

    byte fileOffsetLenIdTipo[7] = {0X01,0X20,0X00,0X00,0X02,0X00,0X00};
    byte idTipo[2];
    byte sizellaveTipoEstadoIdTipoID = 2;

    byte fileOffsetLenNombreApellido[7] = {0X01,0X28,0X00,0X00,0X18,0X00,0X00};
    byte nombreApellido[24];
    byte sizeApellido = 24;

    byte fileOffsetLenFecha[7] = {0X01,0X40,0X00,0X00,0X06,0X00,0X00};
    byte fecha[6];
    byte sizeFecha = 6;


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



    mfrc522.MIFARE_DESFIRE_ReadDataInnoParametrosPago(&tag, app, fileOffsetLenET, estadoTarjeta, sizeestadoTarjeta);
    delay(50);

    mfrc522.MIFARE_DESFIRE_ReadDataInnoParametrosPago(&tag, app, fileOffsetLenIdTipo, idTipo, sizellaveTipoEstadoIdTipoID);
    delay(50);

    mfrc522.MIFARE_DESFIRE_ReadDataInnoParametrosPago(&tag, app, fileOffsetLenNombreApellido, nombreApellido, sizeApellido);
    delay(50);

    mfrc522.MIFARE_DESFIRE_ReadDataInnoParametrosPago(&tag, app, fileOffsetLenFecha, fecha, sizeFecha);
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
    //Serial.println("");
    for (byte i = 0; i<18; i++){
      Serial.print(llaveTipoEstadoIdTipo[i],HEX);
    }
    //Serial.println("");
    for (byte i = 0; i<1; i++){
      Serial.print(estadoTarjeta[i],HEX);
    }
    //Serial.println("");
    for (byte i = 0; i<2; i++){
      Serial.print(idTipo[i],HEX);
    }
    //Serial.println("");
    for (byte i = 0; i<21; i++){
      Serial.print(nombreApellido[i],HEX);
    }
    //Serial.println("");
    for (byte i = 0; i<6; i++){
      Serial.print(fecha[i],HEX);
    }
    //Serial.println("");
    Serial.print("*");
    Serial.print(folioI);
    Serial.print("*");
    Serial.print(saldoL);
    Serial.println("*");
    
}

void cobrar (){
   Serial.println("Saludos");
}

int typeOfCard() {
 //Serial.print("tipo");
 int card = 0;
  // Look for new cards
  //if ( ! mfrc522.PICC_IsNewCardPresent()) {
   // return card;
  //}

  // Select one of the cards
  if ( ! mfrc522.PICC_ReadCardSerial()) {
    return card;
  }
  delay(50);

  byte sakl = mfrc522.uid.sak;
  //Serial.println(sakl);
  if (sakl == 24) {
    card = 2;
  }
  if (sakl == 0) {
    card = 1;
  }
  if (sakl == 8) {
    card = 2;
  }
  if (sakl == 32) {
    card = 3;
  }
  //Serial.println(card);
  //Serial.println(mfrc522.uid.sak);
  delay(50);
  return card;
}



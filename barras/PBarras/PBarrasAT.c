#include <stdio.h>
#include <math.h>
#include <string.h>
#include <time.h>
#include <sqlite3.h>
#include <wiringPi.h>
#include <unistd.h>
#include <sys/time.h>
#include <stdlib.h>



//~ //sensores barras 5326
//~ #define PinDE   16 //derecho superior
//~ #define PinDI   6 //izquierdo superior
//~ #define PinDD   21// derecho inferior
//~ #define PinDB   20 //izquierdo inferior

//modelo con sensores en linea cruzada
//~ #define PinDE   6 //derecho superior
//~ #define PinDI   16 //izquierdo superior
//~ #define PinDD   21// derecho inferior
//~ #define PinDB   20 //izquierdo inferior


//~ Pruebas 19/02/19


//~ version mejorada de barras

//~ #define PinDE   16 //derecho superior
//~ #define PinDI   20 //izquierdo superior
//~ #define PinDD   21// derecho inferior
//~ #define PinDB   6 //izquierdo inferior

//~ version mejorada de barras oficina
//~ #define PinDE   6 //derecho superior
//~ #define PinDI   21 //izquierdo superior
//~ #define PinDD   20// derecho inferior
//~ #define PinDB   16 //izquierdo inferior






//sensores barras 5326

//~ #define PinTE   5 //derecho
//~ #define PinTI   13//izquierdo
//~ #define PinTD   19 // derecho
//~ #define PinTB   26 //izquierdo

//~ #define PinTE   13 //derecho
//~ #define PinTI   5//izquierdo
//~ #define PinTD   19 // derecho
//~ #define PinTB   26 //izquierdo


//~ version mejorada de barras
 
#define PinTE   5  //derecho
#define PinTI   26 //izquierda
#define PinTD   19 // derecho 
#define PinTB   13 //izquierdo




// Variables para registro en Base de Datos 
const char *cdDb = "/home/pi/innobusmx/data/db/aforo";
sqlite3 *db;
sqlite3_stmt *stmt;
const char *tail;
char stSQL[250];
char *zErrMsg = 0;
int idUnidad;

// Informacion del Registro del Aforo
static char idBarras[8];
static char aux;
static char puerta;
char dato;
static char fechaHora[20];
static char fechaH[20];
static char fechaHoraB[20];
int enviados = 0;
float duracion = 0;
struct timeval tv,tv2;



float tiempo_tanscurrido ;

double diff_t;

//
// Variables para determinar el nombre del archivo de datos crudos
//
const int cTiempo = 10;   // duracion de cada cuando se van a crear los archivos
struct tm *tmp;

//~ FILE *fd;	// Datos de la barra Delantera
//~ FILE *ft;	// Datos de la barra Trasera
time_t now,stt,sff;
time_t comienzo,final,comienzo1;

int abre_archivo(int fl) {
char *str, stFile[50], stFechaHora[9], stMin[2];


	if (fl) {
		//~ fclose(fd);
		//~ fclose(ft);
	}
	now = time(NULL);
	tmp = localtime(&now);
	snprintf(stMin,sizeof(stMin),"%02d",tmp->tm_min);
	snprintf(stFechaHora,sizeof(stFechaHora),"%02d-%02d%02d",tmp->tm_mday,tmp->tm_hour,tmp->tm_min);
	//~ strcpy(stFile,"/home/pi/innobusmx/data/barras/");
	//~ strcat(stFile,stFechaHora);
	//~ strcat(stFile,"D.txt");
	//~ fd = fopen(stFile,"w");
	strcpy(stFile,"/home/pi/innobusmx/data/barras/");
	strcat(stFile,stFechaHora);
	strcat(stFile,"T.txt");
	//~ ft = fopen(stFile,"w");
	return (tmp->tm_min+cTiempo) % 60;
}

static int callback(void *NotUsed, int argc, char **argv, char **azColName){
   int i;
   for(i=0; i<argc; i++){
      printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
   }
   printf("\n");
   return 0;
}


void insertar_aforo() {
int result;
 if(dato == '0' || dato == '1'|| dato == '3'){
	sprintf(stSQL, "BEGIN TRANSACTION; INSERT INTO barras2 (auxiliar, duracion, puerta, direccion, fechaHora, enviado) VALUES ('%c', %f, '%c', '%c', '%s', %d); COMMIT;", aux, duracion, puerta, dato, fechaHora, enviados);
	do {
		result = sqlite3_open(cdDb, &db);
	} while (result != SQLITE_OK);
	do {
		result = sqlite3_exec(db, stSQL, callback, 0, &zErrMsg);
//		printf("%d  Registro T OK\n",result);
		if (result != SQLITE_OK) {
//			printf("%s",zErrMsg);
			sqlite3_close(db);
			sqlite3_free(zErrMsg);
			do {
				result = sqlite3_open(cdDb, &db);
			} while (result != SQLITE_OK);
			result = 1;
		}
	} while (result != SQLITE_OK);
	sqlite3_close(db);
}
else{
	sprintf(stSQL, "BEGIN TRANSACTION; INSERT INTO barrasExcepciones2 (auxiliar, duracion, puerta, direccion, fechaHora, enviado) VALUES ('%c', %f, '%c', '%c', '%s', %d); COMMIT;", aux, duracion, puerta, dato, fechaHora, enviados);
	do {
		result = sqlite3_open(cdDb, &db);
	} while (result != SQLITE_OK);
	do {
		result = sqlite3_exec(db, stSQL, callback, 0, &zErrMsg);
//		printf("%d  Registro T OK\n",result);
		if (result != SQLITE_OK) {
//			printf("%s",zErrMsg);
			sqlite3_close(db);
			sqlite3_free(zErrMsg);
			do {
				result = sqlite3_open(cdDb, &db);
			} while (result != SQLITE_OK);
			result = 1;
		}
	} while (result != SQLITE_OK);
	sqlite3_close(db);
	}

}


main () {

//~ comienzo = time(NULL);
//~ float tiempo_tanscurrido ;
int i=0, im, iRegD=0, iRegT=0;


// Variables Lectura del Dato de la Barras
//int bus=0;
//static char st[16];


// Variables Barra Delantera
static char stD[5] = "0000\n";
static char stAnt[5] = "";
int flFin = 0;
int aDat[2] = {0,0};
int aRes[2] = {0,0};
int fl111 = 0;
static char sD;


// Variables Barra Trasera
static char stT[5] = "0000\n";
static char stAntT[5] = "";
int flFinT = 0;
int aDatT[2] = {0,0};
int aResT[2] = {0,0};
int fl111T = 0;
static char sT;



/* Abrir Base de Datos */
	int result = sqlite3_open(cdDb, &db);
	if (result != SQLITE_OK) {
		printf("No se pudo abrir la base de datos %s\n\r",sqlite3_errstr(result));
		sqlite3_close(db);
		return;
	}
	result = sqlite3_prepare_v2(db,"SELECT idTransportista, idUnidad FROM configuraSistema", 60, &stmt, &tail);
	if (result != SQLITE_OK) {
		printf("No se pudo obtener informacion de la tabla configuraSistema\n\r",sqlite3_errstr(result));
		sqlite3_close(db);
		return;
	}
	if (sqlite3_step(stmt) == SQLITE_ROW) 
		idUnidad = sqlite3_column_int(stmt,1);
	else
		idUnidad = 0;
	sqlite3_finalize(stmt);
	sqlite3_close(db);

	im = abre_archivo(0);

//        if (wiringPiSetupGpio() < 0) exit (1);
        wiringPiSetupGpio();

        //~ pinMode( PinDE, INPUT );
        //~ pinMode( PinDI, INPUT );
        //~ pinMode( PinDD, INPUT );
        //~ pinMode( PinDB, INPUT );
        
        pinMode( PinTE, INPUT );
        pinMode( PinTI, INPUT );
        pinMode( PinTD, INPUT );
		pinMode( PinTB, INPUT );
		
		
		comienzo = time(NULL);
		comienzo1 = time(NULL);
		
	while (1) {
		//time_t comienzo,final;
		
		now = time(NULL);
		tmp = localtime(&now);
		if (tmp->tm_min == im)
			im = abre_archivo(1);


      		//~ if (digitalRead(PinDE)) 
	        	//~ stD[0] = '1';	        	
		    //~ else
         		//~ stD[0] = '0';
      		//~ if (digitalRead(PinDI)) 
         		//~ stD[1] = '1';
      		//~ else
         		//~ stD[1] = '0';
      		//~ if (digitalRead(PinDD)) 
         		//~ stD[2] = '1';
      		//~ else
         		//~ stD[2] = '0';
         	//~ if (digitalRead(PinDB)) 
         		//~ stD[3] = '1';
      		//~ else
         		//~ stD[3] = '0';	


      		if (digitalRead(PinTE)) 
         		stT[0] = '1';
      		else
         		stT[0] = '0';
      		if (digitalRead(PinTI)) 
         		stT[1] = '1';
      		else
         		stT[1] = '0';
      		if (digitalRead(PinTD)) 
         		stT[2] = '1';
      		else
         		stT[2] = '0';
			if (digitalRead(PinTB)) 
         		stT[3] = '1';
      		else
         		stT[3] = '0';
			
		//st[16]='\0';
		//~ stD[4]='\0';
		stT[4]='\0';
		int i=0;
		
		

// Procesar barra trasera

//    		if ((aResT[0] != 0 || aResT[1] != 0) && (strncmp(stT,"0000",4) != 0 || flFinT == 1) && (strncmp(stAntT,stT,4) != 0) && (strncmp(stAntT,"0000",4) != 0)) {
//			fprintf(ft, "%s [%i,%i], [%i,%i]\n", fechaHora, aDatT[0], aDatT[1], aResT[0], aResT[1]); 
//			printf("%s [%i,%i], [%i,%i]\n", fechaHora, aDatT[0], aDatT[1], aResT[0], aResT[1]); 
//		}
//		if (strncmp(stT,"0000",4) != 0) {
//			fprintf(ft,"%sT\n", stT);
//			printf("%sT\n", stT);
//		}
		if (strncmp(stT,"0000",4) != 0 || flFinT) {
			if (strncmp(stAntT,stT,4) != 0) {
				
				if (strncmp(stT,"0000",4) != 0 && strncmp(stAntT,"0000",4) == 0) {
					//printf("Ant %s  ---  Act %s",stAnt,stD);
					gettimeofday(&tv, NULL);
					
					comienzo1 = time(NULL);
					//~ tmp = localtime(&comienzo);
					//~ sprintf(fechaH,"%d-%02d-%02d %02d:%02d:%02d",tmp->tm_year+1900,tmp->tm_mon+1,tmp->tm_mday,tmp->tm_hour,tmp->tm_min,tmp->tm_sec);
					//~ printf("Inicio %s \n", fechaH); 
				}
				//~ fprintf(ft,"%sT  -- %i\n", stAntT, iRegT);
				iRegT=0;
				strcpy(stAntT,stT);
				if (strncmp(stT,"1111",4) == 0 || strncmp(stT,"0000",4) == 0) {
					if (strncmp(stT,"1111",4) == 0) {
						if (!fl111T) {
							aDatT[0] = aResT[0];
							aDatT[1] = aResT[1];
							aResT[0]= 0;
							aResT[1]= 0;
						}
						fl111T = 1;
					} else {
						gettimeofday(&tv2, NULL); 
						
						now = time(NULL);
						tmp = localtime(&now);
						//sprintf(idBarras,"%02d%02d%02d%d",tmp->tm_hour,tmp->tm_min,tmp->tm_sec,idUnidad);
						sprintf(fechaHora,"%d-%02d-%02d %02d:%02d:%02d",tmp->tm_year+1900,tmp->tm_mon+1,tmp->tm_mday,tmp->tm_hour,tmp->tm_min,tmp->tm_sec);
						//~ fprintf(ft, "%s [%i,%i], [%i,%i]\n", fechaHora, aDatT[0], aDatT[1], aResT[0], aResT[1]); 
						printf("%s [%i,%i], [%i,%i]\n", fechaHora, aDatT[0], aDatT[1], aResT[0], aResT[1]); 
						//~ sprintf(fechaHoraB,"%02d",tmp->tm_sec);
						tiempo_tanscurrido=difftime(now,comienzo1);
						//~ printf("Fin    %s \n", fechaHora); 	
					    //~ printf("tiempo transcurrido : %f\n",tiempo_tanscurrido);
						printf("tiempo transcurrido : %.2f%lu\n",tiempo_tanscurrido,(tv.tv_usec-tv2.tv_usec));
						duracion = tiempo_tanscurrido;
						if (fl111T) {
							puerta = 'T';
							aux = '0';
 							if (aDatT[0]+aResT[1] > aDatT[1]+aResT[0]) {
								//~ stt = time(NULL);
																
								//~ diff_t =difftime(sff,stt);
								//~ printf("Execution time = %f\n", diff_t);
								
								//~ if (diff_t < 5){
								//~ printf(" T B\n");									
								//~ dato = '0';
								//enviados = 1;
									//~ }
									
								//~ else{
								printf(" T S\n");									
								dato = '1';
								//enviados = 0;
									//~ }
								
								
								
							} else if (aDatT[0]+aResT[1] < aDatT[1]+aResT[0]) {
								//~ sff = time(NULL);
								printf(" T B\n");
								//~ fprintf(ft," T B\n");
								dato = '0';
								//enviados = 0;
								
								
							} 
							//~ else if (aDatT[0]+aResT[1] > aDatT[1]+aResT[0] && duracion == 2) {
								//~ printf(" T B\n");
								//~ dato = '0';
								//~ //delay(1000);
								//sleep(.01);
							//~ } 
							else if (aDatT[0]+aResT[1] == aDatT[1]+aResT[0]) {
								puerta = 't';
								if (aDat[0] > aResT[0]) {
									printf("t ss\n");
									//~ fprintf(ft, "t ss\n");
									dato = '1';
									//enviados = 0;
									//sleep(1);
								} else if (aDatT[0] < aResT[0]) {
									printf("  t bb\n");
									//~ fprintf(ft,"  t bb\n");
									dato = '0';
									//sleep(1);
									//enviados = 0;
								} else {
									printf("     te\n");
									//~ fprintf(ft, "     te\n");
									aux = 'e';
									dato = '2';
									aDatT[0] = aResT[0];
									aDatT[1] = aResT[1];
									fl111T = 0;
									//enviados = 0;
									//sleep(1);
								}
							}
							  
							aResT[0]= 0;
							aResT[1]= 0;
						} 
						else {
							if(tiempo_tanscurrido>3.0){
								 printf("     T Bloqueo\n");
								 aux='B';
								 dato = '3';
								// enviados = 0;
								 }	 
							else{
								puerta = 'T';
								printf("     TE\n");
								
								aux = 'E';
								dato = '2';
								aDatT[0] = aResT[0];
								aDatT[1] = aResT[1];
								aResT[0]= 0;
								aResT[1]= 0;
								fl111T = 0;
								//sleep(1);
								//enviados = 0;
								
								}			
							
						}
						aDatT[0]= 0;
						aDatT[1]= 0;
						fl111T = 0;
						//sleep(1);
						insertar_aforo();
					}
				}
			}
			iRegT++;
			
 			//~ if (strncmp(stT,"0000",4) != 0) fprintf(ft,"%sT   %i\n", stT, iRegT);
		}
		if (stT[0] == '1' && stT != "1111")
			aResT[0]++;
		if (stT[1] == '1' && stT != "1111")
			aResT[1]++;
			aResT[1]++;
		if (stT[2] == '1' && stT != "1111")
			aResT[0]++;
			aResT[0]++;
		if (stT[3] == '1' && stT != "1111")
			aResT[1]++;	
			
		if (strncmp(stT, "0000", 4) != 0)
			flFinT = 0;
		else
			flFinT = 1;



	}  // while
	//~ fclose(fd);
	//~ fclose(ft);

}




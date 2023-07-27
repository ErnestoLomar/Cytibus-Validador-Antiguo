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

#define PinDE   16 //derecho superior
#define PinDI   21 //izquierdo superior
#define PinDD   6// derecho inferior
#define PinDB   20 //izquierdo inferior



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

//~ #define PinDE   6 //derecho superior
//~ #define PinDI   20 //izquierdo superior
//~ #define PinDD   21// derecho inferior
//~ #define PinDB   16 //izquierdo inferior

//~ version mejorada de barras oficina
//~ #define PinDE   6 //derecho superior
//~ #define PinDI   21 //izquierdo superior
//~ #define PinDD   20// derecho inferior
//~ #define PinDB   16 //izquierdo inferior



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

static char h[13];
static char h2[13];

//
// Variables para determinar el nombre del archivo de datos crudos
//
const int cTiempo = 10;   // duracion de cada cuando se van a crear los archivos
struct tm *tmp;

double diff_t;

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
	strcpy(stFile,"/home/pi/innobusmx/data/barras/");
	strcat(stFile,stFechaHora);
	strcat(stFile,"D.txt");
	//~ fd = fopen(stFile,"w");
	//~ strcpy(stFile,"/home/pi/innobusmx/data/barras/");
	//~ strcat(stFile,stFechaHora);
	//~ strcat(stFile,"T.txt");
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
	sprintf(stSQL, "BEGIN TRANSACTION; INSERT INTO barras (auxiliar, duracion, puerta, direccion, fechaHora, enviado) VALUES ('%c', %f, '%c', '%c', '%s', %d); COMMIT;", aux, duracion, puerta, dato, fechaHora, enviados);
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
	sprintf(stSQL, "BEGIN TRANSACTION; INSERT INTO barrasExcepciones (auxiliar, duracion, puerta, direccion, fechaHora, enviado) VALUES ('%c', %f, '%c', '%c', '%s', %d); COMMIT;", aux, duracion, puerta, dato, fechaHora, enviados);
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

        pinMode( PinDE, INPUT );
        pinMode( PinDI, INPUT );
        pinMode( PinDD, INPUT );
        pinMode( PinDB, INPUT );
        
       
		
		
		comienzo = time(NULL);
		comienzo1 = time(NULL);
		
	while (1) {
		//time_t comienzo,final;
		
		now = time(NULL);
		tmp = localtime(&now);
		if (tmp->tm_min == im)
			im = abre_archivo(1);


      		if (digitalRead(PinDE)) 
	        	stD[0] = '1';	        	
		    else
         		stD[0] = '0';
      		if (digitalRead(PinDI)) 
         		stD[1] = '1';
      		else
         		stD[1] = '0';
      		if (digitalRead(PinDD)) 
         		stD[2] = '1';
      		else
         		stD[2] = '0';
         	if (digitalRead(PinDB)) 
         		stD[3] = '1';
      		else
         		stD[3] = '0';	


      	
		stD[4]='\0';
		//~ stT[4]='\0';
		int i=0;
		
		
		
		
			
		
		if (strncmp(stD,"0000",4) != 0 || flFin) {
			//~ printf("STD %s",stD);
			if (strncmp(stAnt,stD,4) != 0) {
				
				
				if (strncmp(stD,"0000",4) != 0 && strncmp(stAnt,"0000",4) == 0) {
					//~ printf("Ant %s  ---  Act %s /n",stAnt,stD);
					gettimeofday(&tv, NULL); 
					//~ comienzo=tv.tv_sec;
					
					comienzo = time(NULL);
					
					//~ tmp = localtime(&comienzo);
					//~ sprintf(fechaH,"%d-%02d-%02d %02d:%02d:%02d",tmp->tm_year+1900,tmp->tm_mon+1,tmp->tm_mday,tmp->tm_hour,tmp->tm_min,tmp->tm_sec);
					//~ printf("Inicio %s \n", fechaH); 
				}
				
				//~ fprintf(fd,"%sD  -- %i\n", stAnt, iRegD);
				printf("%sD  -- %i\n", stAnt, iRegD);
				iRegD=0;
				strcpy(stAnt,stD);
				printf("Ant %s  ---  Act %s \n",stAnt,stD);
				if (strncmp(stD,"1111",4) == 0 || strncmp(stD,"0000",4) == 0) {
					if (strncmp(stD,"1111",4) == 0) {
						if (!fl111) {
							aDat[0] = aRes[0];
							aDat[1] = aRes[1];
							aRes[0]= 0;
							aRes[1]= 0;
						}
						fl111 = 1;
					} else {
						gettimeofday(&tv2, NULL); 
					    //~ now=tv2.tv_sec;
					
						now = time(NULL);
						tmp = localtime(&now);
						//sprintf(idBarras,"%02d%02d%02d%d",tmp->tm_hour,tmp->tm_min,tmp->tm_sec,idUnidad);
						sprintf(fechaHora,"%d-%02d-%02d %02d:%02d:%02d",tmp->tm_year+1900,tmp->tm_mon+1,tmp->tm_mday,tmp->tm_hour,tmp->tm_min,tmp->tm_sec);
						sprintf(fechaH,"%d-%02d-%02d %02d:%02d:%02d",tmp->tm_hour,tmp->tm_min,tmp->tm_sec);
						//~ st = time(NULL);
						
						//~ fprintf(fd, "%s [%i,%i], [%i,%i]\n", fechaHora, aDat[0], aDat[1], aRes[0], aRes[1]); 
						printf("%s [%i,%i], [%i,%i]\n", fechaHora, aDat[0], aDat[1], aRes[0], aRes[1]); 	
						//sprintf(fechaHoraB,"%02d",tmp->tm_sec);						
						tiempo_tanscurrido=difftime(now,comienzo);
						//~ tiempo_tanscurrido=((comienzo) * 1000 + (comienzo) / 1000) - ((now) * 1000 + (now) / 1000);
						
						//~ printf("Fin    %s \n", fechaHora); 	
						//~ printf(" took2 %lu\n",tiempo_tanscurrido);
					    printf("tiempo transcurrido : %.2f%lu\n",tiempo_tanscurrido,(tv.tv_usec-tv2.tv_usec));
					    //~ printf("tiempo transcurrido : %f\n",tiempo_tanscurrido);
					    duracion = tiempo_tanscurrido;
						if (fl111) {
							puerta = 'D';
							aux = '0';
							
						    if (aDat[0]+aRes[1]> aDat[1]+aRes[0]){
								//~ sprintf(h, fechaHora);
								printf("D S\n");
								//~ fprintf(fd,"D S\n");
								dato = '1';
								//~ sff = time(NULL);
								//enviados = 0;
								
							}
							//~ else if (aDat[0]+aRes[1] +13000 > aDat[1]+aRes[0] && duracion > 0.1) {
								//~ printf(" D S\n");
								
								//~ dato = '1';
								
								
							//~ }
							else if (aDat[0]+aRes[1] < aDat[1]+aRes[0]){
								
								//~ stt = time(NULL);
								//~ diff_t =difftime(sff,stt);
								//~ printf("Execution time = %f\n", diff_t);
								
								//~ if (diff_t < 5){
								//~ printf(" D S\n");									
								//~ dato = '1';
								//enviados = 1;
									//~ }
									
								//~ else{
								printf(" D B\n");									

								dato = '0';
								//enviados = 0;
									//~ }	
								
								//~ fprintf(fd," D B\n");

								//~ puts(h);
								
								
								
								//Bloque de barras
							}
							//~ else if (aDat[0]+aRes[1] < aDat[1]+aRes[0] && duracion >= 3){
								//~ printf(" D S\n");
								//~ fprintf(fd," D B\n");
								//~ dato = '1';
							
	//enviados = 0;
								
								//Bloque de barras
							//~ }
							//~ else if (aDat[0]+aRes[1] < aDat[1]+aRes[0] && duracion == 1.0){
								//~ printf(" D S\n");
								//~ fprintf(fd," D B\n");
								//~ dato = '1';
								
								
								//~ //Bloque de barras
							//~ }
							 //~ else if (aDat[0]+aRes[1] < aDat[1]+aRes[0] && duracion > 1.9){
								//~ printf(" D S\n");
								
								//~ dato = '1';
								
								//~ //Bloque de barras
							//~ } 
							  else if (aDat[0]+aRes[1] == aDat[1]+aRes[0]) {
								puerta = 'd';
								if (aDat[0] > aRes[0]) {
									printf("d ss\n");
									//~ fprintf(fd, "d ss\n");
									dato = '1';
									//enviados = 0;
									
								} else if (aDat[0] < aRes[0]) {
									printf("  d bb\n");
									//~ fprintf(fd,"  d bb\n");
									dato = '0';
									enviados = 0;
									
								} else {
									printf("     d e\n");
									//~ fprintf(fd, "     d e\n");
									aux = 'e';
									dato = '2';
									//enviados = 0;
									aDat[0] = aRes[0];
									aDat[1] = aRes[1];
									fl111 = 0;
									//sleep(1);
								}
							}
							aRes[0]= 0;
							aRes[1]= 0;
						}
						
						else {
							 
							 
							 puerta = 'D';
							 
							 if(tiempo_tanscurrido>3.0){
								 printf("     D Bloqueo\n");
								 aux='B';
								 dato = '3';
								 //enviados = 0;
								 }	 
							 else{
							 
							 printf("     D E\n");
							 
							 aux = 'E';
							 dato = '2';
							 enviados = 0;
							 aDat[0] = aRes[0];
							 aDat[1] = aRes[1];
							 aRes[0]= 0;
							 aRes[1]= 0;
							 fl111 = 0;
							// sleep(1);
							 
							 
							}
						}
						aDat[0]= 0;
						aDat[1]= 0;
						fl111 = 0;
						//sleep(1);
						insertar_aforo();
						
					}
					
				}
				//sprintf(fechaHoraB,"%d-%02d-%02d %02d:%02d:%02d",tmp->tm_year+1900,tmp->tm_mon+1,tmp->tm_mday,tmp->tm_hour,tmp->tm_min,tmp->tm_sec);
						//printf("%s \n", fechaHoraB); 
						//~ final =time(NULL);
						//~ tiempo_tanscurrido=difftime(final,comienzo);
							 //~ printf("%f\n",tiempo_tanscurrido);
							 //~ //printf("%d\n",++segundos);
			}
			iRegD++;
			//~ fprintf(fd,"%sD   %i\n", stD, iRegD);
		}
		if (stD[0] == '1' && stD != "1111")
			aRes[0]++;
		if (stD[1] == '1' && stD != "1111")
			aRes[1]++;
			aRes[1]++;
		if (stD[2] == '1' && stD != "1111")
			aRes[0]++;
			aRes[0]++;
		if (stD[3] == '1' && stD != "1111")
			aRes[1]++;				
		if (strncmp(stD, "0000", 4) != 0)
			flFin = 0;
		else
			flFin = 1;
		





	}  // while
	//~ fclose(fd);
	//~ fclose(ft);

}




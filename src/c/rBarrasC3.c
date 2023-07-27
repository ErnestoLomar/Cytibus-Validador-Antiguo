#include <stdio.h>
#include <math.h>
#include <string.h>
#include <time.h>
#include <sqlite3.h>
#include <wiringPiI2C.h>

#define ADDRESS_BUS (0x04)

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
int enviados = 0;

//
// Variables para determinar el nombre del archivo de datos crudos
//
const int cTiempo = 10;   // duracion de cada cuando se van a crear los archivos
struct tm *tmp;

FILE *fd;	// Datos de la barra Delantera
FILE *ft;	// Datos de la barra Trasera
time_t now;

int abre_archivo(int fl) {
char *str, stFile[50], stFechaHora[9], stMin[2];


	if (fl) {
		fclose(fd);
		fclose(ft);
	}
	now = time(NULL);
	tmp = localtime(&now);
	snprintf(stMin,sizeof(stMin),"%02d",tmp->tm_min);
	snprintf(stFechaHora,sizeof(stFechaHora),"%02d-%02d:%02d",tmp->tm_mday,tmp->tm_hour,tmp->tm_min);
	strcpy(stFile,"/home/pi/innobusmx/data/barras/");
	strcat(stFile,stFechaHora);
	strcat(stFile,"D.txt");
	fd = fopen(stFile,"w");
	strcpy(stFile,"/home/pi/innobusmx/data/barras/");
	strcat(stFile,stFechaHora);
	strcat(stFile,"T.txt");
	ft = fopen(stFile,"w");
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

	sprintf(stSQL, "BEGIN TRANSACTION; INSERT INTO barras (idBarra, auxiliar, duracion, puerta, direccion, fechaHora, enviado) VALUES ('%s', '%c', %d, '%c', '%c', '%s', %d); COMMIT;", idBarras, aux, 2, puerta, dato, fechaHora, enviados);
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


main () {

int i=0, im;


// Variables Lectura del Dato de la Barras
int bus=0;
static char st[9];


// Variables Barra Delantera
static char stD[4] = "000\n";
static char stAnt[3] = "";
int flFin = 0;
int aDat[2] = {0,0};
int aRes[2] = {0,0};
int fl111 = 0;
static char sD;


// Variables Barra Trasera
static char stT[4] = "000\n";
static char stAntT[3] = "";
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
	bus = wiringPiI2CSetup(ADDRESS_BUS);
	while (1) {
	
		now = time(NULL);
		tmp = localtime(&now);
		if (tmp->tm_min == im)
			im = abre_archivo(1);

		dato = wiringPiI2CRead(bus);
		for (i=7; i>=0; --i, dato >>= 1) {
			st[i] = (dato & 1) + '0';
			if (i != 0 && i != 4) { 
				if (i < 4) 
					stT[i-1] = st[i];
				else 
					stD[i-5] = st[i];
                        }
		}
		st[9]='\0';
		stD[3]='\0';
		stT[3]='\0';
//		printf("lectura: %s   %s\n", stD, stT);

// Procesar barra delantera

//    		if ((aRes[0] != 0 || aRes[1] != 0) && (strncmp(stD,"000",3) != 0 || flFin == 1) && (strncmp(stAnt,stD,3) != 0) && (strncmp(stAnt,"000",3) != 0)) {
//			fprintf(fd, "%s [%i,%i], [%i,%i]\n", fechaHora, aDat[0], aDat[1], aRes[0], aRes[1]); 
//			printf("%s [%i,%i], [%i,%i]\n", fechaHora, aDat[0], aDat[1], aRes[0], aRes[1]); 
//		}
		if (strncmp(stD,"000",3) != 0) {
			fprintf(fd,"%sD\n", stD);
//			printf("%sD\n", stD);
		}
		if (strncmp(stD,"000",3) != 0 || flFin) {
			if (strncmp(stAnt,stD,3) != 0) {
				strcpy(stAnt,stD);
				if (strncmp(stD,"111",3) == 0 || strncmp(stD,"000",3) == 0) {
					if (strncmp(stD,"111",3) == 0) {
						if (!fl111) {
							aDat[0] = aRes[0];
							aDat[1] = aRes[1];
							aRes[0]= 0;
							aRes[1]= 0;
						}
						fl111 = 1;
					} else {
						now = time(NULL);
						tmp = localtime(&now);
						sprintf(idBarras,"%02d%02d%02d%d",tmp->tm_hour,tmp->tm_min,tmp->tm_sec,idUnidad);
						sprintf(fechaHora,"%d-%02d-%02d %02d:%02d:%02d",tmp->tm_year+1900,tmp->tm_mon+1,tmp->tm_mday,tmp->tm_hour,tmp->tm_min,tmp->tm_sec);
						fprintf(fd, "%s [%i,%i], [%i,%i]\n", fechaHora, aDat[0], aDat[1], aRes[0], aRes[1]); 
						printf("%s [%i,%i], [%i,%i]\n", fechaHora, aDat[0], aDat[1], aRes[0], aRes[1]); 	
						if (fl111) {
							puerta = 'D';
							aux = '0';
 							if (aDat[0]+aRes[1] > aDat[1]+aRes[0]) {
								printf("D S\n");
								fprintf(fd,"D S\n");
								dato = '1';
							} else if (aDat[0]+aRes[1] < aDat[1]+aRes[0]) {
								printf(" D B\n");
								fprintf(fd," D B\n");
								dato = '0';
							} else if (aDat[0]+aRes[1] == aDat[1]+aRes[0]) {
								puerta = 'd';
								if (aDat[0] > aRes[0]) {
									printf("d ss\n");
									fprintf(fd, "d ss\n");
									dato = '1';
								} else if (aDat[0] < aRes[0]) {
									printf("  d bb\n");
									fprintf(fd,"  d bb\n");
									dato = '0';
								} else {
									printf("     d e\n");
									fprintf(fd, "     d e\n");
									aux = 'e';
									dato = '0';
									aDat[0] = aRes[0];
									aDat[1] = aRes[1];
									fl111 = 0;
								}
							}
							aRes[0]= 0;
							aRes[1]= 0;
						} else {
							puerta = 'D';
							printf("     D E\n");
							fprintf(fd, "     D E\n");
							aux = 'E';
							dato = '0';
							aDat[0] = aRes[0];
							aDat[1] = aRes[1];
							aRes[0]= 0;
							aRes[1]= 0;
							fl111 = 0;
						}
						aDat[0]= 0;
						aDat[1]= 0;
						fl111 = 0;
						insertar_aforo();
					}
				}
			}
		}
		if (stD[0] == '1' && stD != "111")
			aRes[0]++;
		if (stD[1] == '1' && stD != "111")
			aRes[1]++;
		if (strncmp(stD, "000", 3) != 0)
			flFin = 0;
		else
			flFin = 1;


// Procesar barra trasera

//    		if ((aResT[0] != 0 || aResT[1] != 0) && (strncmp(stT,"000",3) != 0 || flFinT == 1) && (strncmp(stAntT,stT,3) != 0) && (strncmp(stAntT,"000",3) != 0)) {
//			fprintf(ft, "%s [%i,%i], [%i,%i]\n", fechaHora, aDatT[0], aDatT[1], aResT[0], aResT[1]); 
//			printf("%s [%i,%i], [%i,%i]\n", fechaHora, aDatT[0], aDatT[1], aResT[0], aResT[1]); 
//		}
		if (strncmp(stT,"000",3) != 0) {
			fprintf(ft,"%sT\n", stT);
//			printf("%sT\n", stT);
		}
		if (strncmp(stT,"000",3) != 0 || flFinT) {
			if (strncmp(stAntT,stT,3) != 0) {
				strcpy(stAntT,stT);
				if (strncmp(stT,"111",3) == 0 || strncmp(stT,"000",3) == 0) {
					if (strncmp(stT,"111",3) == 0) {
						if (!fl111T) {
							aDatT[0] = aResT[0];
							aDatT[1] = aResT[1];
							aResT[0]= 0;
							aResT[1]= 0;
						}
						fl111T = 1;
					} else {
						now = time(NULL);
						tmp = localtime(&now);
						sprintf(idBarras,"%02d%02d%02d%d",tmp->tm_hour,tmp->tm_min,tmp->tm_sec,idUnidad);
						sprintf(fechaHora,"%d-%02d-%02d %02d:%02d:%02d",tmp->tm_year+1900,tmp->tm_mon+1,tmp->tm_mday,tmp->tm_hour,tmp->tm_min,tmp->tm_sec);
						fprintf(ft, "%s [%i,%i], [%i,%i]\n", fechaHora, aDatT[0], aDatT[1], aResT[0], aResT[1]); 
						printf("%s [%i,%i], [%i,%i]\n", fechaHora, aDatT[0], aDatT[1], aResT[0], aResT[1]); 
						if (fl111T) {
							puerta = 'T';
							aux = '0';
 							if (aDatT[0]+aResT[1] > aDatT[1]+aResT[0]) {
								printf("T S\n");
								fprintf(ft,"T S\n");
								dato = '1';
							} else if (aDatT[0]+aResT[1] < aDatT[1]+aResT[0]) {
								printf(" T B\n");
								fprintf(ft," T B\n");
								dato = '0';
							} else if (aDatT[0]+aResT[1] == aDatT[1]+aResT[0]) {
								puerta = 't';
								if (aDat[0] > aResT[0]) {
									printf("t ss\n");
									fprintf(ft, "t ss\n");
									dato = '1';
								} else if (aDatT[0] < aResT[0]) {
									printf("  t bb\n");
									fprintf(ft,"  t bb\n");
									dato = '0';
								} else {
									printf("     te\n");
									fprintf(ft, "     te\n");
									aux = 'e';
									dato = '0';
									aDatT[0] = aResT[0];
									aDatT[1] = aResT[1];
									fl111T = 0;
								}
							}
							aResT[0]= 0;
							aResT[1]= 0;
						} else {
							puerta = 'T';
							printf("     TE\n");
							fprintf(ft, "     TE\n");
							aux = 'E';
							dato = '0';
							aDatT[0] = aResT[0];
							aDatT[1] = aResT[1];
							aResT[0]= 0;
							aResT[1]= 0;
							fl111T = 0;
						}
						aDatT[0]= 0;
						aDatT[1]= 0;
						fl111T = 0;
						insertar_aforo();
					}
				}
			}
		}
		if (stT[0] == '1' && stT != "111")
			aResT[0]++;
		if (stT[1] == '1' && stT != "111")
			aResT[1]++;
		if (strncmp(stT, "000", 3) != 0)
			flFinT = 0;
		else
			flFinT = 1;
	

	}  // while
	fclose(fd);
	fclose(ft);

}



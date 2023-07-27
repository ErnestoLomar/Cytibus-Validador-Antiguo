#include <stdio.h>
#include <math.h>
#include <string.h>
#include <time.h>
#include <sqlite3.h>
#include <wiringPiI2C.h>

#define ADDRESS_BUS (0x04)

const char *cdDb = "/home/pi/uc-cf-b/db/aforo";

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
	strcpy(stFile,"/home/pi/uc-cf-b/data/barras/");
	strcat(stFile,stFechaHora);
	strcat(stFile,"D.txt");
	fd = fopen(stFile,"w");
	strcpy(stFile,"/home/pi/uc-cf-b/data/barras/");
	strcat(stFile,stFechaHora);
	strcat(stFile,"T.txt");
	ft = fopen(stFile,"w");
	return (tmp->tm_min+cTiempo) % 60;
}



main () {

int i=0, im, idUnidad;

// Variables para registro en Base de Datos 
sqlite3 *db;
sqlite3_stmt *stmt;
const char *tail;
char stSQL[250];

int enviados = 0;
static char puerta;
static char idBarras[8];
static char fechaHora[20];
static char aux;

// Variables Lectura del Dato de la Barras
int bus=0;
char dato;
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
//	printf("Base de datos %s OK\n\r",cdDb);

	result = sqlite3_prepare_v2(db,"SELECT idTransportista, idUnidad FROM configuraSistema", 60, &stmt, &tail);

//	printf("Base de datos %s OK\n\r",cdDb);

	if (result != SQLITE_OK) {
		printf("No se pudo obtener informacion de la tabla configuraSistema\n\r",sqlite3_errstr(result));
		sqlite3_close(db);
		return;
	}
	if (sqlite3_step(stmt) == SQLITE_ROW) 
		idUnidad = sqlite3_column_int(stmt,1);
	else
		idUnidad = 0;
//	printf("Configuraci[on OK idUnidad:%d\n\r",idUni);


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
				if (i < 4) {
					stD[i-1] = st[i];
				} else {
					stT[i-5] = st[i];
                                }
			}
		}
		st[9]='\0';
		stD[3]='\0';
		stT[3]='\0';
//		printf("lectura: %s   %s\n", stD, stT);


// Procesar barra delantera

	    		if ((aRes[0] != 0 || aRes[1] != 0) && (strncmp(stD,"000",3) != 0 || flFin == 1) && (strncmp(stAnt,stD,3) != 0) && (strncmp(stAnt,"000",3) != 0)) {
				fprintf(fd, "%s [%i,%i], [%i,%i]\n", fechaHora, aDat[0], aDat[1], aRes[0], aRes[1]); 
				printf("%s [%i,%i], [%i,%i]\n", fechaHora, aDat[0], aDat[1], aRes[0], aRes[1]); 
			}
			if (strncmp(stD,"000",3) != 0) {
				fprintf(fd,"%sD\n", stD);
				printf("%sD\n", stD);
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
							if (fl111) {
								puerta = 'd';
								aux = '0';
	 							if (aDat[0]+aRes[1] > aDat[1]+aRes[0]) {
									printf("B\n");
									fprintf(fd,"B\n");
									dato = '0';
								} else if (aDat[0]+aRes[1] < aDat[1]+aRes[0]) {
									printf(" S\n");
									fprintf(fd," S\n");
									dato = '1';
								} else if (aDat[0]+aRes[1] == aDat[1]+aRes[0]) {
									if (aDat[0] > aRes[0]) {
										printf("bb\n");
										fprintf(fd, "bb\n");
										dato = '0';
									} else if (aDat[0] < aRes[0]) {
										printf("  ss\n");
										fprintf(fd,"  ss\n");
										dato = '1';
									} else {
										printf("     E\n");
										fprintf(fd, "     E\n");
										aux = 'E';
										dato = '0';
										aDat[0] = aRes[0];
										aDat[1] = aRes[1];
										fl111 = 0;
									}
								}
								aRes[0]= 0;
								aRes[1]= 0;
							} else {
								printf("     e\n");
								fprintf(fd, "     e\n");
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
							now = time(NULL);
							tmp = localtime(&now);
							sprintf(idBarras,"%02d%02d%02d%d",tmp->tm_hour,tmp->tm_min,tmp->tm_sec,idUnidad);
							sprintf(fechaHora,"%d-%02d-%02d %02d:%02d:%02d",tmp->tm_year+1900,tmp->tm_mon+1,tmp->tm_mday,tmp->tm_hour,tmp->tm_min,tmp->tm_sec);
							sprintf(stSQL, "INSERT INTO barras (idBarra, auxiliar, duracion, puerta, direccion, fechaHora, enviado) VALUES ('%s', '%c', %d, '%c', '%c', '%s', %d)", idBarras, aux, 2, puerta, dato, fechaHora, enviados);
							result = sqlite3_prepare_v2(db,stSQL, sizeof(stSQL)+1, &stmt, &tail);
							sqlite3_step(stmt);
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

	    		if ((aResT[0] != 0 || aResT[1] != 0) && (strncmp(stT,"000",3) != 0 || flFinT == 1) && (strncmp(stAntT,stT,3) != 0) && (strncmp(stAntT,"000",3) != 0)) {
				fprintf(ft, "%s [%i,%i], [%i,%i]\n", fechaHora, aDatT[0], aDatT[1], aResT[0], aResT[1]); 
				printf("%s [%i,%i], [%i,%i]\n", fechaHora, aDatT[0], aDatT[1], aResT[0], aResT[1]); 
			}
			if (strncmp(stT,"000",3) != 0) {
				fprintf(ft,"%sT\n", stT);
				printf("%sT\n", stT);
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
							if (fl111T) {
								puerta = 't';
								aux = '0';
	 							if (aDatT[0]+aResT[1] > aDatT[1]+aResT[0]) {
									printf("B\n");
									fprintf(ft,"B\n");
									dato = '1';
								} else if (aDatT[0]+aResT[1] < aDatT[1]+aResT[0]) {
									printf(" S\n");
									fprintf(ft," S\n");
									dato = '0';
								} else if (aDatT[0]+aResT[1] == aDatT[1]+aResT[0]) {
									if (aDat[0] > aResT[0]) {
										printf("bb\n");
										fprintf(ft, "bb\n");
										dato = '1';
									} else if (aDatT[0] < aResT[0]) {
										printf("  ss\n");
										fprintf(ft,"  ss\n");
										dato = '0';
									} else {
										printf("     E\n");
										fprintf(ft, "     E\n");
										aux = 'E';
										dato = '0';
										aDatT[0] = aResT[0];
										aDatT[1] = aResT[1];
										fl111T = 0;
									}
								}
								aResT[0]= 0;
								aResT[1]= 0;
							} else {
								printf("     e\n");
								fprintf(ft, "     e\n");
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
							now = time(NULL);
							tmp = localtime(&now);
							sprintf(idBarras,"%02d%02d%02d%d",tmp->tm_hour,tmp->tm_min,tmp->tm_sec,idUnidad);
							sprintf(fechaHora,"%d-%02d-%02d %02d:%02d:%02d",tmp->tm_year+1900,tmp->tm_mon+1,tmp->tm_mday,tmp->tm_hour,tmp->tm_min,tmp->tm_sec);
							sprintf(stSQL, "INSERT INTO barras (idBarra, auxiliar, duracion, puerta, direccion, fechaHora, enviado) VALUES ('%s', '%c', %d, '%c', '%c', '%s', %d)", idBarras, aux, 2, puerta, dato, fechaHora, enviados);
							result = sqlite3_prepare_v2(db,stSQL, sizeof(stSQL)+1, &stmt, &tail);
							sqlite3_step(stmt);
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



#include <stdio.h>
#include <string.h>
#include <sqlite3.h>
#include <time.h>

const char *cdDb = "/home/pi/uc-cf-b/db/aforo";

static int callback(void *NotUsed, int argc, char **argv, char **azColName){
   int i;
   for(i=0; i<argc; i++){
      printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
   }
   printf("\n");
   return 0;
}

main () {

// Variables para registro en Base de Datos 
sqlite3 *db;
sqlite3_stmt *stmt;
const char *tail;
char stSQL[250];
char *zErrMsg = 0;
static char fechaHora[20];

char dato;
static char st[9];
static char stD[4];
static char stT[4];

int i;
int idUnidad;
time_t now;
struct tm *tmp;


/* Abrir Base de Datos */

	int result = sqlite3_open(cdDb, &db);
	if (result != SQLITE_OK) {
		printf("No se pudo abrir la base de datos %s\n\r",sqlite3_errstr(result));
		sqlite3_close(db);
		return;
	}

	sqlite3_close(db);
	int c = getchar();

	while (c != '.') {
		now = time(NULL);
		tmp = localtime(&now);
		sprintf(fechaHora,"%d-%02d-%02d %02d:%02d:%02d",tmp->tm_year+1900,tmp->tm_mon+1,tmp->tm_mday,tmp->tm_hour,tmp->tm_min,tmp->tm_sec);
		sprintf(stSQL,"INSERT INTO barras (idBarra, auxiliar, duracion, puerta, direccion, fechaHora, enviado) VALUES ('00', 'X', 0, 'X', 'X', '%s', 0)",fechaHora);
		do {
			result = sqlite3_open(cdDb, &db);
		} while (result != SQLITE_OK);
		do {
			result = sqlite3_exec(db, stSQL, callback, 0, &zErrMsg);
			if (result != SQLITE_OK) {
				printf("SQL error: %s  Hora:%s \n",zErrMsg, fechaHora);
				sqlite3_close(db);
				do {
					result = sqlite3_open(cdDb, &db);
				} while (result != SQLITE_OK);
				result = 1;
			}
			else
				printf("Registro Insertado %s \n", fechaHora);
		} while (result != SQLITE_OK);
		sqlite3_close(db);





		c = getchar();
		
	}
	




}
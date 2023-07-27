#include <stdio.h>
#include <string.h>
#include <sqlite3.h>


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


char dato;
static char st[9];
static char stD[4];
static char stT[4];

int i;
int idUnidad;




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
//	sqlite3_close(db);



	
	strcpy(stSQL,"INSERT INTO barras (idBarra, auxiliar, duracion, puerta, direccion, fechaHora, enviado) VALUES ('00', 'X', 0, 'X', 'X', '2012-12-12', 0)");
	result = sqlite3_exec(db, stSQL, callback, 0, &zErrMsg);
	



/*

	printf("st:%s  Del:%s Tras:%s\n", st, stD, stT);
	dato = 'C';
	for (i=7; i>=0; --i, dato >>= 1) {
		st[i] = (dato & 1) + '0';
		if (i != 0 && i != 4) { 
			if (i < 4)
				stD[i-1] = st[i];
			else
				stT[i-5] = st[i];
		}
			
	}
	st[9]='\0';
	stT[3]='\0';
	stD[3]='\0';
	printf("st:%s  Del:%s Tras:%s  Comp:%d\n", st, stD, stT, strncmp("011", stT, 3));

	if (strncmp(stD,"000",3) == 0) {
		printf("ok\n");
	}

*/

}
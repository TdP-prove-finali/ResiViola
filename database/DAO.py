from database.DB_connect import DBConnect
from model.scuola import Scuola
from model.costo_classe import CostoClasse
from model.libro_classe import LibroClasse
from model.classe_isee import ClasseIsee
from model.libro import Libro


class DAO:
    @staticmethod
    def get_scuole() -> list[Scuola]:
        cnx = DBConnect.get_connection()
        result = []
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT codice_scuola, denominazione, tipologia
                   FROM scuola
                   ORDER BY denominazione"""
        cursor.execute(query)
        for row in cursor:
            result.append(Scuola(**row))
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def get_costo_classi(codice_scuola: str | None = None) -> list[CostoClasse]:
        cnx = DBConnect.get_connection()
        result = []
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT a.codice_scuola, a.anno_corso, a.sezione,
                          COUNT(*) AS num_libri,
                          SUM(l.prezzo) AS costo_studente
                   FROM adozione a
                   JOIN libro l ON l.isbn = a.isbn
                   WHERE (%s IS NULL OR a.codice_scuola = %s)
                     AND a.da_acquistare = 1
                     AND l.prezzo IS NOT NULL
                   GROUP BY a.codice_scuola, a.anno_corso, a.sezione
                   ORDER BY a.codice_scuola, a.anno_corso, a.sezione"""
        cursor.execute(query, (codice_scuola, codice_scuola))
        for row in cursor:
            result.append(CostoClasse(**row))
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def get_alunni_per_classe() -> dict[tuple[str, int], float]:
        cnx = DBConnect.get_connection()
        result = {}
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT codice_scuola, anno_corso, alunni / classi AS media
                   FROM studenti
                   WHERE classi > 0"""
        cursor.execute(query)
        for row in cursor:
            result[(row["codice_scuola"], row["anno_corso"])] = float(row["media"])
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def get_alunni_per_classe_citta() -> dict[int, float]:
        cnx = DBConnect.get_connection()
        result = {}
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT anno_corso, SUM(alunni) / SUM(classi) AS media
                   FROM studenti
                   GROUP BY anno_corso"""
        cursor.execute(query)
        for row in cursor:
            result[row["anno_corso"]] = float(row["media"])
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def get_libri_classi() -> list[LibroClasse]:
        cnx = DBConnect.get_connection()
        result = []
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT a.codice_scuola, a.anno_corso, a.sezione, a.isbn, l.prezzo
                   FROM adozione a
                   JOIN libro l ON l.isbn = a.isbn
                   WHERE a.da_acquistare = 1
                     AND l.prezzo IS NOT NULL"""
        cursor.execute(query)
        for row in cursor:
            result.append(LibroClasse(**row))
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def get_libri_scuola(codice_scuola: str) -> list[Libro]:
        cnx = DBConnect.get_connection()
        result = []
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT l.isbn, l.titolo, MAX(a.disciplina) AS disciplina, l.editore, l.prezzo
                   FROM adozione a
                   JOIN libro l ON l.isbn = a.isbn
                   WHERE a.codice_scuola = %s
                     AND a.da_acquistare = 1
                     AND l.prezzo IS NOT NULL
                   GROUP BY l.isbn, l.titolo, l.editore, l.prezzo
                   ORDER BY disciplina, l.titolo"""
        cursor.execute(query, (codice_scuola,))
        for row in cursor:
            result.append(Libro(**row))
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def get_libri() -> dict[str, Libro]:
        cnx = DBConnect.get_connection()
        result = {}
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT l.isbn, l.titolo, MAX(a.disciplina) AS disciplina, l.editore, l.prezzo
                   FROM adozione a
                   JOIN libro l ON l.isbn = a.isbn
                   WHERE a.da_acquistare = 1
                     AND l.prezzo IS NOT NULL
                   GROUP BY l.isbn, l.titolo, l.editore, l.prezzo"""
        cursor.execute(query)
        for row in cursor:
            result[row["isbn"]] = Libro(**row)
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def get_distanze() -> dict[tuple[str, str], float]:
        cnx = DBConnect.get_connection()
        result = {}
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        cursor.execute("SELECT codice_1, codice_2, km FROM distanza")
        for row in cursor:
            result[(row["codice_1"], row["codice_2"])] = float(row["km"])
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def get_quota_nuove_adozioni() -> float:
        cnx = DBConnect.get_connection()
        result = 0.0
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT AVG(nuova_adozione) AS quota
                   FROM adozione
                   WHERE da_acquistare = 1"""
        cursor.execute(query)
        row = cursor.fetchone()
        if row and row["quota"] is not None:
            result = float(row["quota"])
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def get_classi_isee() -> list[ClasseIsee]:
        cnx = DBConnect.get_connection()
        result = []
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT id, descrizione, limite_inf, limite_sup,
                          nuclei_con_minori, nuclei_senza_minori
                   FROM classe_isee
                   ORDER BY limite_inf"""
        cursor.execute(query)
        for row in cursor:
            result.append(ClasseIsee(**row))
        cursor.close()
        cnx.close()
        return result

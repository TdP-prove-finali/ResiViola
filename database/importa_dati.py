import csv
import math
import pathlib
import time

from database.DB_connect import DBConnect

CARTELLA_RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"
FILE_ADOZIONI = CARTELLA_RAW / "ALTPIEMONTE000020260909.csv"
FILE_SCUOLE = CARTELLA_RAW / "SCUANAGRAFESTAT20262720260901.csv"
FILE_STUDENTI = CARTELLA_RAW / "ALUCORSOINDCLASTA20242520250831.csv"
FILE_ISEE = CARTELLA_RAW.parent / "isee_torino_2025.csv"
FILE_COORDINATE = CARTELLA_RAW.parent / "coordinate_scuole.csv"
RAGGIO_TERRA_KM = 6371.0

COMUNE = "TORINO"
GRADI_SECONDARIA_II = ("NO", "NT")


def _leggi_csv(percorso):
    with open(percorso, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _si_no(valore):
    return 1 if valore.strip().upper() == "SI" else 0


def _prezzo(valore):
    try:
        return round(float(valore.replace(",", ".")), 2)
    except ValueError:
        return None


def _limiti_classe_isee(descrizione):
    if descrizione == "nullo":
        return 0.0, 0.0
    numeri = [float(t.replace(",", ".")) for t in descrizione.split() if t[0].isdigit()]
    if descrizione.startswith("oltre"):
        return numeri[0], None
    return numeri[0], round(numeri[1] + 0.01, 2)


def prepara_isee():
    with open(FILE_ISEE, encoding="utf-8", newline="") as f:
        righe = list(csv.DictReader(f, delimiter=";"))
    return [(r["classe_isee"], *_limiti_classe_isee(r["classe_isee"]),
             int(r["nuclei_con_minori"]), int(r["nuclei_senza_minori"]))
            for r in righe]


def _leggi_coordinate():
    if not FILE_COORDINATE.exists():
        return {}
    with open(FILE_COORDINATE, encoding="utf-8", newline="") as f:
        return {r["codice_scuola"]: (float(r["lat"]), float(r["lon"]))
                for r in csv.DictReader(f, delimiter=";") if r["lat"]}


def haversine(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * RAGGIO_TERRA_KM * math.asin(math.sqrt(a))


def prepara_distanze(scuole):
    con_coordinate = [(s[0], s[4], s[5]) for s in scuole if s[4] is not None]
    return [(c1, c2, round(haversine(la1, lo1, la2, lo2), 3))
            for i, (c1, la1, lo1) in enumerate(con_coordinate)
            for (c2, la2, lo2) in con_coordinate[i + 1:]]


def prepara_dati():
    adozioni_raw = _leggi_csv(FILE_ADOZIONI)
    anagrafica = {r["CODICESCUOLA"]: r for r in _leggi_csv(FILE_SCUOLE)
                  if r["DESCRIZIONECOMUNE"] == COMUNE}

    adozioni_torino = [r for r in adozioni_raw
                       if r["TIPOGRADOSCUOLA"] in GRADI_SECONDARIA_II
                       and r["CODICESCUOLA"] in anagrafica]
    codici_scuole = sorted({r["CODICESCUOLA"] for r in adozioni_torino})

    coordinate = _leggi_coordinate()
    scuole = [(c,
               anagrafica[c]["DENOMINAZIONESCUOLA"].strip(),
               anagrafica[c]["INDIRIZZOSCUOLA"].strip(),
               anagrafica[c]["DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA"].strip(),
               *coordinate.get(c, (None, None)))
              for c in codici_scuole]

    libri = {}
    for r in adozioni_torino:
        if r["CODICEISBN"] not in libri:
            libri[r["CODICEISBN"]] = (r["CODICEISBN"], r["TITOLO"].strip(), r["AUTORI"].strip(),
                                      r["EDITORE"].strip(), _prezzo(r["PREZZO"]))

    adozioni = [(r["CODICESCUOLA"], int(r["ANNOCORSO"]), r["SEZIONEANNO"].strip(),
                 r["COMBINAZIONE"].strip(), r["DISCIPLINA"].strip(), r["CODICEISBN"],
                 _si_no(r["DAACQUIST"]), _si_no(r["NUOVAADOZ"]), r["CONSIGLIATO"].strip())
                for r in adozioni_torino]

    codici = set(codici_scuole)
    studenti = [(r["CODICESCUOLA"], int(r["ANNOCORSOCLASSE"]), int(r["CLASSI"]),
                 int(r["ALUNNIMASCHI"]) + int(r["ALUNNIFEMMINE"]))
                for r in _leggi_csv(FILE_STUDENTI)
                if r["CODICESCUOLA"] in codici and r["ORDINESCUOLA"] == "SCUOLA SECONDARIA II GRADO"]

    return scuole, list(libri.values()), adozioni, studenti


def salva_dati(scuole, libri, adozioni, studenti, classi_isee, distanze):
    cnx = DBConnect.get_connection()
    if cnx is None:
        raise RuntimeError("Connessione al database non riuscita: MariaDB e' avviato? "
                           "Hai eseguito schema.sql?")
    cursor = cnx.cursor()

    for tabella in ("distanza", "classe_isee", "adozione", "studenti", "libro", "scuola"):
        cursor.execute(f"DELETE FROM {tabella}")

    cursor.executemany("""INSERT INTO scuola (codice_scuola, denominazione, indirizzo, tipologia,
                                              lat, lon)
                          VALUES (%s, %s, %s, %s, %s, %s)""", scuole)
    cursor.executemany("""INSERT INTO libro (isbn, titolo, autori, editore, prezzo)
                          VALUES (%s, %s, %s, %s, %s)""", libri)
    cursor.executemany("""INSERT INTO adozione (codice_scuola, anno_corso, sezione, combinazione,
                                                disciplina, isbn, da_acquistare, nuova_adozione,
                                                consigliato)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", adozioni)
    cursor.executemany("""INSERT INTO studenti (codice_scuola, anno_corso, classi, alunni)
                          VALUES (%s, %s, %s, %s)""", studenti)
    cursor.executemany("""INSERT INTO classe_isee (descrizione, limite_inf, limite_sup,
                                                   nuclei_con_minori, nuclei_senza_minori)
                          VALUES (%s, %s, %s, %s, %s)""", classi_isee)
    cursor.executemany("""INSERT INTO distanza (codice_1, codice_2, km)
                          VALUES (%s, %s, %s)""", distanze)
    cnx.commit()
    cursor.close()
    cnx.close()


if __name__ == "__main__":
    inizio = time.perf_counter()
    scuole, libri, adozioni, studenti = prepara_dati()
    print(f"Scuole: {len(scuole)}  Libri: {len(libri)}  "
          f"Adozioni: {len(adozioni)}  Righe studenti: {len(studenti)}")
    print(f"Libri senza prezzo (ND): {sum(1 for l in libri if l[4] is None)}")
    classi_isee = prepara_isee()
    print(f"Classi ISEE: {len(classi_isee)}")
    distanze = prepara_distanze(scuole)
    print(f"Sedi con coordinate: {sum(1 for s in scuole if s[4] is not None)}  "
          f"Distanze: {len(distanze)}")
    salva_dati(scuole, libri, adozioni, studenti, classi_isee, distanze)
    print(f"Importazione completata in {time.perf_counter() - inizio:.1f} s")

import csv
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

from database.DB_connect import DBConnect
from database.importa_dati import FILE_SCUOLE

FILE_COORDINATE = pathlib.Path(__file__).resolve().parent.parent / "data" / "coordinate_scuole.csv"
URL_NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "tesi-comodato-libri-torino/1.0 (prova finale Politecnico di Torino)"

CORREZIONI = {
    "VIA S. OTTAVIO 9": "VIA SANT'OTTAVIO 9",
    "VIA G.BIDONE 11": "VIA BIDONE 11",
    "VIA P. DELLA CELLA 3": "VIA PAOLO DELLA CELLA 3",
    "VIA MADONNA DE LA SALETTE 29": "VIA MADONNA DELLA SALETTE 29",
}


def normalizza_indirizzo(indirizzo):
    indirizzo = re.sub(r"([A-Za-z'])(\d)", r"\1 \2", indirizzo.strip())
    indirizzo = re.sub(r"(\d+)\s*/.*$", r"\1", indirizzo)
    return re.sub(r"\s+", " ", indirizzo)


def cerca(via, cap):
    parametri = {"street": via, "city": "Torino", "postalcode": cap, "country": "Italia",
                 "format": "json", "limit": 1}
    richiesta = urllib.request.Request(f"{URL_NOMINATIM}?{urllib.parse.urlencode(parametri)}",
                                       headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(richiesta, timeout=30) as risposta:
        risultati = json.load(risposta)
    time.sleep(1.1)
    if risultati:
        return float(risultati[0]["lat"]), float(risultati[0]["lon"])
    return None


def geocodifica():
    cnx = DBConnect.get_connection()
    cursor = cnx.cursor()
    cursor.execute("SELECT codice_scuola FROM scuola")
    codici = {riga[0] for riga in cursor}
    cursor.close()
    cnx.close()

    with open(FILE_SCUOLE, encoding="utf-8", newline="") as f:
        anagrafica = {r["CODICESCUOLA"]: r for r in csv.DictReader(f) if r["CODICESCUOLA"] in codici}

    righe = []
    for codice in sorted(codici):
        r = anagrafica[codice]
        via = normalizza_indirizzo(r["INDIRIZZOSCUOLA"])
        via = CORREZIONI.get(via, via)
        coordinate = cerca(via, r["CAPSCUOLA"])
        if coordinate is None:
            coordinate = cerca(via, "")
        esito = "trovato" if coordinate else "NON TROVATO"
        print(f"{codice}  {via}, {r['CAPSCUOLA']}  ->  {coordinate} {esito}")
        righe.append({"codice_scuola": codice, "indirizzo_cercato": via, "cap": r["CAPSCUOLA"],
                      "lat": coordinate[0] if coordinate else "",
                      "lon": coordinate[1] if coordinate else ""})

    with open(FILE_COORDINATE, "w", encoding="utf-8", newline="") as f:
        scrittore = csv.DictWriter(f, fieldnames=righe[0].keys(), delimiter=";")
        scrittore.writeheader()
        scrittore.writerows(righe)
    trovate = sum(1 for r in righe if r["lat"] != "")
    print(f"Coordinate trovate: {trovate} su {len(righe)} -> {FILE_COORDINATE}")


if __name__ == "__main__":
    geocodifica()

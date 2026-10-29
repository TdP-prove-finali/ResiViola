OTTIMIZZAZIONE E SIMULAZIONE DI UN SERVIZIO DI COMODATO D'USO DEI LIBRI DI TESTO
PER LE SCUOLE SECONDARIE DI II GRADO DEL COMUNE DI TORINO

Nome dell'applicazione: PrestiTO - Libri di testo in comodato per le scuole superiori di Torino

Prova finale - Laurea in Ingegneria Gestionale, Politecnico di Torino
Corso di riferimento: Tecniche di Programmazione
Studentessa: Viola Resi (s330915)

======================================================================
1. COSA FA L'APPLICAZIONE
======================================================================
PrestiTO e' un'applicazione desktop (Python + Flet) che aiuta dirigenti scolastici ed
enti locali a gestire un servizio di comodato d'uso dei libri di testo. Le cinque
pagine si scelgono dalla barra laterale; in ogni pagina i parametri sono a sinistra e
i risultati a destra.

- Fabbisogno: costo dei libri per classe e fabbisogno per titolo di una scuola.
- Piano: con un budget, sceglie quali classi servire con il kit completo di libri
  (in parte copie usate, in parte nuove). Hanno diritto al comodato gli studenti con
  ISEE fino a una soglia. Algoritmo: problema dello zaino 0/1 risolto con ricorsione e
  backtracking (branch & bound), confrontato con un criterio greedy.
- Simulazione: il servizio della scuola su piu' anni (prestiti, restituzioni, copie
  rovinate e perse, cambi di adozione), con il piano di acquisto ricalcolato ogni anno
  sulle sole copie mancanti. Con gli stessi parametri la simulazione da' sempre gli
  stessi risultati, mostrati in una tabella anno per anno e in due grafici.
- Scenari: le simulazioni salvate (durante la sessione) si confrontano in una
  tabella e in grafici; si confrontano scenari della stessa scuola.
- Rete: grafo (NetworkX) delle scuole collegate da libri in comune, pesato con la
  distanza; gruppi di scuole = componenti connesse tenendo solo le coppie con almeno
  10 libri in comune; trasferimenti delle copie in eccesso: ogni scuola in carenza
  le prende dalla scuola piu' vicina che ne ha in piu'.

======================================================================
2. REQUISITI
======================================================================
- Python 3.12 (le librerie sono le stesse dei laboratori del corso):
    flet 0.22.1, mysql-connector-python 8.3.0, networkx 3.2.1
- MariaDB (testato con MariaDB 12.2) o MySQL
- Facoltativo: DBeaver per eseguire gli script SQL

======================================================================
3. INSTALLAZIONE
======================================================================
1. Creare un ambiente virtuale e installare le dipendenze:
       python -m venv .venv
       .venv\Scripts\activate
       pip install -r requirements.txt

2. Credenziali del database: copiare database\connector_example.cnf in
   database\connector.cnf e inserire utente e password di MariaDB.
   (connector.cnf non va condiviso: contiene la password.)

3. Creare e popolare il database, in uno dei due modi:

   a) Dal dump gia' pronto (consigliato):
          mariadb -u root -p < data\comodato_libri.sql
      oppure in DBeaver: aprire data\comodato_libri.sql ed eseguirlo come script (Alt+X).

   b) Dai dati originali:
      - scaricare i tre CSV indicati nella sezione 5 in data\raw\
      - eseguire database\schema.sql (crea il database e le tabelle vuote)
      - dalla cartella del progetto:  python -m database.importa_dati
      Le coordinate delle scuole (servono per le distanze) sono gia' in
      data\coordinate_scuole.csv; per ricalcolarle (richiede Internet):
      python -m database.geocodifica_scuole

4. Avviare l'applicazione:
       python main.py
   Se MariaDB non e' avviato o le credenziali sono sbagliate, l'applicazione lo
   segnala con un messaggio.

======================================================================
4. COME PROVARE L'APPLICAZIONE
======================================================================
1. Fabbisogno: scegliere una scuola (es. "A. VOLTA") e premere "Per classe" o
   "Per titolo".
2. Piano: lasciare i valori proposti e premere "Calcola piano"; "Confronta algoritmi"
   mostra greedy e branch & bound a confronto (es. BODONI - PARAVIA, TORI013019, con
   budget 5000: il greedy serve 63 studenti, il branch & bound 66).
3. Simulazione: premere "Simula" (5 anni, pochi millisecondi), poi "Salva". Cambiare
   un parametro (es. "Cambi di adozione" = 0), simulare e salvare di nuovo.
4. Scenari: spuntare gli scenari salvati e premere "Confronta".
5. Rete: premere "Tutte" (o spuntare alcune scuole), poi "Grafo e gruppi" oppure
   "Trasferimenti" (con tutte le 74 scuole circa un secondo).

======================================================================
5. DATI: FONTI E LICENZE
======================================================================
- Portale Unico dei Dati della Scuola, Ministero dell'Istruzione e del Merito
  https://dati.istruzione.it/opendata/  - licenza IODL 2.0
    * Adozioni libri di testo, Regione Piemonte (ALTPIEMONTE000020260909.csv)
    * Anagrafica scuole statali, a.s. 2026/27 (SCUANAGRAFESTAT20262720260901.csv)
    * Studenti per anno di corso e classe, a.s. 2024/25 (ALUCORSOINDCLASTA20242520250831.csv)
  I CSV originali (circa 70 MB) non sono inclusi; il database filtrato
  (Comune di Torino, secondaria di II grado) e' in data\comodato_libri.sql.
- INPS, Osservatorio su DSU e ISEE: nuclei familiari per classe di valore ISEE e
  presenza di minori, provincia di Torino, anno 2025 (data\isee_torino_2025.csv).
  Usato per generare richieste di comodato sintetiche ma realistiche.
- Coordinate delle sedi scolastiche: geocodifica degli indirizzi MIM con Nominatim,
  (c) OpenStreetMap contributors, licenza ODbL (data\coordinate_scuole.csv).
- Soglia ISEE di default: voucher scuola della Regione Piemonte, a.s. 2026/27
  (ISEE fino a 15.748,78 euro).

Dati sintetici (non pubblici): richieste di comodato e ISEE dei singoli studenti,
usura e smarrimento delle copie, prezzo e disponibilita' dell'usato. Sono generati o
impostati dall'utente tramite parametri modificabili.

======================================================================
6. STRUTTURA DEL PROGETTO
======================================================================
main.py                     avvio dell'applicazione (pattern MVC)
UI/view.py                  finestra: barra laterale, cinque pagine, area dei risultati
UI/controller.py            eventi, lettura e controllo dei parametri, risultati
UI/grafici.py               grafici a linee
UI/stile.py                 colori ed elementi grafici comuni
model/model.py              logica: fabbisogno, piano di acquisto, simulazione, scenari, grafo
model/zaino.py              problema dello zaino: greedy e branch & bound ricorsivo
                            (la ricorsione completa senza pruning serve solo alle misure)
model/simulatore.py         simulazione pluriennale del servizio di una scuola
model/generatore_richieste.py  richieste sintetiche e graduatoria ISEE
model/*.py                  classi di dominio (dataclass)
database/DAO.py             accesso ai dati (solo query parametrizzate)
database/DB_connect.py      pool di connessioni
database/schema.sql         struttura del database
database/importa_dati.py    importazione e pulizia dei CSV
database/geocodifica_scuole.py  coordinate delle scuole (da eseguire una volta)
data/                       dataset filtrato e dati di supporto

======================================================================
7. DOCUMENTAZIONE E LICENZE
======================================================================
Video dimostrativo: [link YouTube da inserire]

Software: Apache License 2.0 (file LICENSE).
Relazione tecnica: Creative Commons BY-NC-SA 4.0.

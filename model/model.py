import random
import time
from collections import defaultdict
from datetime import datetime

import networkx as nx

from database.DAO import DAO
from model.generatore_richieste import genera_richieste, graduatoria
from model.parametri_piano import ParametriPiano
from model.parametri_simulazione import ParametriSimulazione
from model.piano_acquisto import PianoAcquisto
from model.scenario import Scenario
from model.simulatore import Simulatore
from model.trasferimento import PianoTrasferimenti, Trasferimento
from model.gruppo_classe import GruppoClasse
from model.voce_piano import VocePiano
from model.zaino import Zaino

SOGLIA_GRUPPI = 10


class Model:
    def __init__(self):
        self._scuole = []
        self._alunni_per_classe = {}
        self._media_citta = {}
        self._libri_per_classe = {}
        self._classi_isee = []
        self._distanze = {}
        self._libri = {}
        self._ultima_simulazione = None
        self._scenari = {}
        self._prossimo_id = 0
        self._zaino = Zaino()

    def get_scuole(self):
        if not self._scuole:
            self._scuole = DAO.get_scuole()
        return self._scuole

    def get_nome_scuola(self, codice_scuola):
        for s in self.get_scuole():
            if s.codice_scuola == codice_scuola:
                return s.denominazione
        return codice_scuola

    def get_costo_classi(self, codice_scuola=None):
        classi = DAO.get_costo_classi(codice_scuola)
        self._stima_studenti(classi)
        return classi

    def _stima_studenti(self, classi):
        if not self._alunni_per_classe:
            self._alunni_per_classe = DAO.get_alunni_per_classe()
            self._media_citta = DAO.get_alunni_per_classe_citta()
        for c in classi:
            chiave = (c.codice_scuola, c.anno_corso)
            if chiave in self._alunni_per_classe:
                c.num_studenti = round(self._alunni_per_classe[chiave])
            else:
                c.num_studenti = round(self._media_citta.get(c.anno_corso, 0))
                c.stima_cittadina = True

    def _get_libri_per_classe(self):
        if not self._libri_per_classe:
            libri = defaultdict(list)
            for lc in DAO.get_libri_classi():
                libri[lc.chiave_classe].append((lc.isbn, lc.prezzo))
            self._libri_per_classe = dict(libri)
        return self._libri_per_classe

    def get_fabbisogno_titoli(self, codice_scuola):
        libri_classe = self._get_libri_per_classe()
        classi_per_isbn = defaultdict(list)
        studenti_per_isbn = defaultdict(int)
        for c in self.get_costo_classi(codice_scuola):
            for isbn, _ in libri_classe.get((c.codice_scuola, c.anno_corso, c.sezione), []):
                classi_per_isbn[isbn].append(f"{c.anno_corso}{c.sezione}")
                studenti_per_isbn[isbn] += c.num_studenti
        return [(libro, classi_per_isbn[libro.isbn], studenti_per_isbn[libro.isbn])
                for libro in DAO.get_libri_scuola(codice_scuola)]

    def _get_classi_isee(self):
        if not self._classi_isee:
            self._classi_isee = DAO.get_classi_isee()
        return self._classi_isee

    def get_quota_isee(self, soglia_isee):
        classi_isee = self._get_classi_isee()
        totale = sum(c.nuclei_con_minori for c in classi_isee)
        if totale == 0:
            return 0.0
        sotto = 0.0
        for c in classi_isee:
            if c.limite_sup is None or soglia_isee <= c.limite_inf:
                continue
            if soglia_isee >= c.limite_sup:
                sotto += c.nuclei_con_minori
            else:
                frazione = (soglia_isee - c.limite_inf) / (c.limite_sup - c.limite_inf)
                sotto += c.nuclei_con_minori * frazione
        return sotto / totale

    def get_graduatoria(self, codice_scuola, parametri: ParametriPiano):
        rng = random.Random(f"{parametri.seme}-{codice_scuola}")
        richieste = genera_richieste(self.get_costo_classi(codice_scuola),
                                     parametri.quota_richiedenti, self._get_classi_isee(), rng)
        return richieste, graduatoria(richieste, parametri.soglia_isee)

    @staticmethod
    def _prezzo_medio(prezzo, parametri: ParametriPiano):
        u = parametri.usato_disponibile
        return prezzo * (u * parametri.prezzo_usato + (1 - u))

    def _gruppi_candidati(self, aventi_diritto, parametri: ParametriPiano):
        conteggi = defaultdict(int)
        for r in aventi_diritto:
            conteggi[r.chiave_classe] += 1

        libri_classe = self._get_libri_per_classe()
        gruppi = []
        for chiave, n in sorted(conteggi.items()):
            libri = libri_classe.get(chiave, [])
            if not libri:
                continue
            costo = n * sum(self._prezzo_medio(prezzo, parametri) for _, prezzo in libri)
            gruppi.append(GruppoClasse(*chiave, studenti=n, costo=round(costo, 2),
                                       isbn=[isbn for isbn, _ in libri]))
        return gruppi

    def calcola_piano(self, codice_scuola, parametri: ParametriPiano, metodo="branch_bound"):
        richieste, aventi_diritto = self.get_graduatoria(codice_scuola, parametri)
        candidati = self._gruppi_candidati(aventi_diritto, parametri)
        piano = PianoAcquisto(metodo=metodo, budget=parametri.budget,
                              richiedenti=len(richieste), aventi_diritto=len(aventi_diritto))
        inizio = time.perf_counter()
        indici, piano.nodi_visitati = self._zaino.risolvi([round(g.costo * 100) for g in candidati],
                                                          [g.studenti for g in candidati],
                                                          round(parametri.budget * 100), metodo)
        piano.tempo_s = time.perf_counter() - inizio
        piano.gruppi_serviti = [candidati[i] for i in indici]
        piano.voci = self._voci_piano(codice_scuola, piano.gruppi_serviti, parametri)
        return piano

    def _voci_piano(self, codice_scuola, gruppi_serviti, parametri: ParametriPiano):
        libri = {l.isbn: l for l in DAO.get_libri_scuola(codice_scuola)}
        voci = {}
        for g in gruppi_serviti:
            for isbn in g.isbn:
                voce = voci.setdefault(isbn, VocePiano(libro=libri[isbn]))
                voce.copie_nuove += g.studenti
                voce.classi.add(g.nome_classe)
        for voce in voci.values():
            copie = voce.copie_nuove
            voce.copie_usate = round(copie * parametri.usato_disponibile)
            voce.copie_nuove = copie - voce.copie_usate
            voce.costo = copie * self._prezzo_medio(voce.libro.prezzo, parametri)
        return sorted(voci.values(), key=lambda v: (v.libro.disciplina, v.libro.titolo))

    def confronta_metodi(self, codice_scuola, parametri: ParametriPiano):
        return [self.calcola_piano(codice_scuola, parametri, "greedy"),
                self.calcola_piano(codice_scuola, parametri, "branch_bound")]

    def get_quota_nuove_adozioni(self):
        return DAO.get_quota_nuove_adozioni()

    def simula(self, codice_scuola, parametri: ParametriSimulazione):
        simulatore = Simulatore(self.get_costo_classi(codice_scuola), self._get_libri_per_classe(),
                                self._get_classi_isee(), parametri)
        inizio = time.perf_counter()
        statistiche = simulatore.esegui()
        self._ultima_simulazione = (codice_scuola, parametri, statistiche)
        return statistiche, time.perf_counter() - inizio

    def salva_ultima_simulazione(self, nome):
        if self._ultima_simulazione is None:
            raise ValueError("Esegui prima una simulazione, poi salvala come scenario.")
        codice, p, statistiche = self._ultima_simulazione
        self._prossimo_id += 1
        scenario = Scenario(id=self._prossimo_id, nome=nome, codice_scuola=codice, creato=datetime.now(),
                            budget=p.piano.budget, budget_annuo=p.budget_annuo,
                            quota_richiedenti=p.piano.quota_richiedenti,
                            soglia_isee=p.piano.soglia_isee,
                            prezzo_usato=p.piano.prezzo_usato, usato_disponibile=p.piano.usato_disponibile,
                            p_danno=p.p_danno, p_perdita=p.p_perdita,
                            p_cambio=p.p_cambio, anni=p.anni)
        self._scenari[scenario.id] = (scenario, statistiche)
        return scenario

    def get_scenari(self):
        return sorted((sc for sc, _ in self._scenari.values()), key=lambda sc: sc.creato, reverse=True)

    def elimina_scenari(self, ids):
        for i in ids:
            self._scenari.pop(i, None)

    def get_statistiche_scenario(self, scenario_id):
        return self._scenari[scenario_id][1]

    @staticmethod
    def riepilogo(statistiche):
        serviti = sum(s.valori["studenti_serviti"] for s in statistiche)
        spesa = sum(s.valori["spesa"] for s in statistiche)
        return {
            "serviti_totali": serviti,
            "serviti_ultimo_anno": statistiche[-1].valori["studenti_serviti"],
            "pct_soddisfatte_media": sum(s.valori["pct_soddisfatte"] for s in statistiche) / len(statistiche),
            "spesa_totale": spesa,
            "risparmio_totale": sum(s.valori["risparmio_famiglie"] for s in statistiche),
            "saldo_finale": statistiche[-1].valori["saldo_cumulato"],
            "costo_per_studente": spesa / serviti if serviti else 0.0,
        }

    def _km(self, c1, c2):
        if not self._distanze:
            self._distanze = DAO.get_distanze()
        return self._distanze.get((min(c1, c2), max(c1, c2)), 0.0)

    def _isbn_per_scuola(self, codici):
        codici = set(codici)
        isbn = defaultdict(set)
        for (codice, _, _), libri in self._get_libri_per_classe().items():
            if codice in codici:
                isbn[codice].update(i for i, _ in libri)
        return isbn

    def crea_grafo(self, codici_scuole):
        grafo = nx.Graph()
        isbn = self._isbn_per_scuola(codici_scuole)
        for c in codici_scuole:
            grafo.add_node(c, nome=self.get_nome_scuola(c), titoli=len(isbn[c]))
        codici = sorted(codici_scuole)
        for i, c1 in enumerate(codici):
            for c2 in codici[i + 1:]:
                comuni = len(isbn[c1] & isbn[c2])
                if comuni > 0:
                    grafo.add_edge(c1, c2, km=self._km(c1, c2), libri_comuni=comuni)
        return grafo

    @staticmethod
    def statistiche_grafo(grafo):
        n = grafo.number_of_nodes()
        return {"nodi": n, "archi": grafo.number_of_edges(), "densita": nx.density(grafo),
                "componenti": nx.number_connected_components(grafo) if n else 0,
                "grado_medio": 2 * grafo.number_of_edges() / n if n else 0}

    @staticmethod
    def statistiche_gruppo(grafo, gruppo):
        archi = list(grafo.subgraph(gruppo).edges(data=True))
        if not archi:
            return 0.0, 0.0
        return (sum(d["libri_comuni"] for _, _, d in archi) / len(archi),
                sum(d["km"] for _, _, d in archi) / len(archi))

    @staticmethod
    def gruppi_scuole(grafo, soglia=SOGLIA_GRUPPI):
        forti = nx.Graph()
        forti.add_nodes_from(grafo.nodes)
        forti.add_edges_from((a, b) for a, b, d in grafo.edges(data=True) if d["libri_comuni"] >= soglia)
        return sorted(nx.connected_components(forti), key=len, reverse=True)

    def pianifica_trasferimenti(self, codici_scuole, parametri: ParametriSimulazione):
        inizio = time.perf_counter()
        codici_scuole = sorted(codici_scuole)
        grafo = self.crea_grafo(codici_scuole)
        if not self._libri:
            self._libri = DAO.get_libri()

        per_titolo = defaultdict(dict)
        for codice in codici_scuole:
            simulatore = Simulatore(self.get_costo_classi(codice), self._get_libri_per_classe(),
                                    self._get_classi_isee(), parametri)
            for isbn, valori in simulatore.eccedenze_e_carenze().items():
                per_titolo[isbn][codice] = valori

        piano = PianoTrasferimenti()
        u = parametri.piano.usato_disponibile
        fattore_prezzo = u * parametri.piano.prezzo_usato + (1 - u)
        for isbn, scuole in sorted(per_titolo.items()):
            piano.eccedenze += sum(e for e, _ in scuole.values())
            piano.carenze += sum(c for _, c in scuole.values())
            libro = self._libri.get(isbn.split("#")[0])
            if libro is None:
                continue
            in_eccesso = {c: e for c, (e, _) in scuole.items() if e > 0}
            for codice, (_, carenza) in sorted(scuole.items()):
                if not carenza or not in_eccesso:
                    continue
                vicine = sorted((grafo.edges[codice, v]["km"], v) for v in grafo.neighbors(codice)
                                if in_eccesso.get(v, 0) > 0)
                for km, da in vicine:
                    copie = min(carenza, in_eccesso[da])
                    piano.trasferimenti.append(Trasferimento(da=da, a=codice, libro=libro, copie=copie, km=km))
                    in_eccesso[da] -= copie
                    carenza -= copie
                    piano.copie_ricevute += copie
                    piano.risparmio += copie * libro.prezzo * fattore_prezzo
                    if not carenza:
                        break
        piano.tempo_s = time.perf_counter() - inizio
        return piano

import random
from collections import defaultdict

from model.generatore_richieste import genera_richieste, graduatoria
from model.parametri_simulazione import ParametriSimulazione
from model.statistica_anno import StatisticaAnno
from model.zaino import Zaino


class Simulatore:
    def __init__(self, classi, libri_per_classe, classi_isee, parametri: ParametriSimulazione):
        self._classi = [c for c in classi
                        if libri_per_classe.get((c.codice_scuola, c.anno_corso, c.sezione))]
        self._libri = {self._chiave(c): libri_per_classe[self._chiave(c)] for c in self._classi}
        self._p = parametri
        self._zaino = Zaino()
        u = parametri.piano.usato_disponibile
        self._fattore_prezzo = u * parametri.piano.prezzo_usato + (1 - u)
        self._aventi, self._per_classe = self._richieste(classi_isee)
        self._resti = defaultdict(float)

    @staticmethod
    def _chiave(c):
        return c.codice_scuola, c.anno_corso, c.sezione

    def esegui(self) -> list[StatisticaAnno]:
        adozioni = {k: list(v) for k, v in self._libri.items()}
        magazzino = defaultdict(int)
        dismesse = defaultdict(int)
        self._resti = defaultdict(float)
        saldo = 0.0
        risultati = []
        for anno in range(self._p.anni):
            riga = self._esegui_anno(adozioni, magazzino, dismesse, anno)
            saldo += riga["risparmio_famiglie"] - riga["spesa"]
            riga["saldo_cumulato"] = saldo
            risultati.append(StatisticaAnno(anno=anno, valori=riga))
        return risultati

    def _esegui_anno(self, adozioni, magazzino, dismesse, anno):
        p = self._p
        if anno > 0:
            self._cambi_adozione(adozioni, magazzino, dismesse, anno)

        classi = sorted(k for k in self._per_classe if k in adozioni)
        costi = [self._costo_mancanti(k, adozioni[k], magazzino, self._per_classe[k]) for k in classi]
        budget = p.piano.budget if anno == 0 else p.budget_annuo
        indici, _ = self._zaino.risolvi(costi, [self._per_classe[k] for k in classi], round(budget * 100))

        serviti = copie_acquistate = 0
        risparmio = 0.0
        for i in indici:
            k = classi[i]
            n = self._per_classe[k]
            for isbn, _ in adozioni[k]:
                mancanti = max(0, n - magazzino[(k, isbn)])
                magazzino[(k, isbn)] += mancanti
                copie_acquistate += mancanti
                rovinate = self._copie_intere((k, isbn, "rovinate"), n * p.p_danno)
                perse = self._copie_intere((k, isbn, "perse"), (n - rovinate) * p.p_perdita)
                magazzino[(k, isbn)] -= rovinate + perse
            serviti += n
            risparmio += n * sum(prezzo for _, prezzo in adozioni[k])
        spesa = sum(costi[i] for i in indici) / 100
        aventi = len(self._aventi)
        return {
            "aventi_diritto": aventi,
            "studenti_serviti": serviti,
            "pct_soddisfatte": 100 * serviti / aventi if aventi else 0,
            "spesa": spesa,
            "risparmio_famiglie": risparmio,
            "copie_acquistate": copie_acquistate,
            "copie_magazzino": sum(magazzino.values()),
            "costo_per_studente": spesa / serviti if serviti else 0,
        }

    def _richieste(self, classi_isee):
        piano = self._p.piano
        codice = self._classi[0].codice_scuola if self._classi else ""
        rng = random.Random(f"{piano.seme}-{codice}")
        richieste = genera_richieste(self._classi, piano.quota_richiedenti, classi_isee, rng)
        aventi = graduatoria(richieste, piano.soglia_isee)
        per_classe = defaultdict(int)
        for r in aventi:
            per_classe[r.chiave_classe] += 1
        return aventi, dict(per_classe)

    def _copie_intere(self, chiave, quota):
        self._resti[chiave] += quota
        copie = int(self._resti[chiave] + 0.5)
        self._resti[chiave] -= copie
        return copie

    def _costo_mancanti(self, classe, libri, magazzino, n):
        return round(100 * sum(max(0, n - magazzino[(classe, isbn)]) * prezzo * self._fattore_prezzo
                               for isbn, prezzo in libri))

    def _cambi_adozione(self, adozioni, magazzino, dismesse, anno):
        titoli = sorted({isbn.split("#")[0] for libri in self._libri.values() for isbn, _ in libri})
        quanti = round(len(titoli) * self._p.p_cambio)
        if not quanti:
            return
        inizio = ((anno - 1) * quanti) % len(titoli)
        cambiati = {titoli[(inizio + j) % len(titoli)] for j in range(quanti)}
        for k, libri in adozioni.items():
            for j, (isbn, prezzo) in enumerate(libri):
                if isbn.split("#")[0] in cambiati:
                    dismesse[isbn] += magazzino.pop((k, isbn), 0)
                    libri[j] = (f"{isbn.split('#')[0]}#{anno}", prezzo)

    def eccedenze_e_carenze(self):
        adozioni = {k: list(v) for k, v in self._libri.items()}
        magazzino, dismesse = defaultdict(int), defaultdict(int)
        self._resti = defaultdict(float)
        self._esegui_anno(adozioni, magazzino, dismesse, 0)
        self._cambi_adozione(adozioni, magazzino, dismesse, 1)

        fabbisogno = defaultdict(int)
        for k, n in self._per_classe.items():
            for isbn, _ in adozioni.get(k, []):
                fabbisogno[isbn] += n
        copie = defaultdict(int, dismesse)
        for (_, isbn), n in magazzino.items():
            copie[isbn] += n

        risultato = {}
        for isbn in set(fabbisogno) | set(copie):
            eccedenza = max(0, copie[isbn] - fabbisogno[isbn])
            carenza = max(0, fabbisogno[isbn] - copie[isbn])
            if eccedenza or carenza:
                risultato[isbn] = (eccedenza, carenza)
        return risultato

import flet as ft

from UI.grafici import MAX_SERIE, grafico_linee
from UI.stile import ERRORE, PRIMARIO, tabella, testo_secondario, titolo_risultati
from model.model import SOGLIA_GRUPPI
from model.parametri_piano import ParametriPiano
from model.parametri_simulazione import ParametriSimulazione


def formato(valore, decimali=0):
    return f"{valore:,.{decimali}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def colonna(testo):
    return ft.DataColumn(ft.Text(testo, text_align=ft.TextAlign.CENTER))


def cella(testo):
    return ft.DataCell(ft.Text(testo, no_wrap=True))


def cella_testo(testo, larghezza):
    return ft.DataCell(ft.Text(testo, width=larghezza, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS))


def scorrevole(tabella_dati):
    return ft.Row([tabella_dati], scroll=ft.ScrollMode.AUTO)


class Controller:
    def __init__(self, view, model):
        self._view = view
        self._model = model

    def fill_scuole(self):
        self._view.dd_scuola.options.clear()
        self._view.cb_scuole.clear()
        for s in self._model.get_scuole():
            self._view.dd_scuola.options.append(ft.dropdown.Option(key=s.codice_scuola, text=str(s)))
            self._view.cb_scuole.append(ft.Checkbox(label=str(s), value=False, data=s.codice_scuola,
                                                    label_style=ft.TextStyle(size=13),
                                                    on_change=self.handle_cambio_selezione))
        self._view.lv_scuole.controls = list(self._view.cb_scuole)
        if not self._view.cb_scuole:
            self._mostra_errore("Impossibile leggere i dati delle scuole: controlla che MariaDB sia avviato "
                                "e che database/connector.cnf contenga utente e password corretti, "
                                "poi riavvia l'applicazione.")
        self._view.update_page()

    def _codice_scuola(self):
        codice = self._view.dd_scuola.value
        if not codice:
            self._mostra_errore("Seleziona una scuola.")
        return codice

    def handle_fabbisogno_classi(self, e):
        self._view.txt_result.controls.clear()
        codice = self._codice_scuola()
        if not codice:
            return
        classi = self._model.get_costo_classi(codice)
        self._aggiungi(titolo_risultati("Fabbisogno per classe", self._model.get_nome_scuola(codice)))
        if not classi:
            self._mostra_errore("Nessuna adozione trovata per questa scuola.")
            return
        studenti = sum(c.num_studenti for c in classi)
        totale = sum(c.costo_classe for c in classi)
        self._riepilogo(f"{len(classi)} classi, {formato(studenti)} studenti (stima): costo totale dei libri "
                        f"{formato(totale)} €, in media {formato(totale / studenti, 2)} € per famiglia")
        righe = [ft.DataRow(cells=[
            cella(f"{c.anno_corso}{c.sezione}"), cella(str(c.num_libri)), cella(formato(c.costo_studente, 2)),
            cella(str(c.num_studenti) + (" *" if c.stima_cittadina else "")), cella(formato(c.costo_classe, 2)),
        ]) for c in classi]
        self._aggiungi(scorrevole(tabella(
            [colonna("Classe"), colonna("Libri da\nacquistare"), colonna("Costo per\nstudente €"),
             colonna("Studenti\n(stima)"), colonna("Costo\nclasse €")], righe)))
        if any(c.stima_cittadina for c in classi):
            self._nota("* studenti stimati con la media cittadina (dati della scuola assenti)")
        self._view.update_page()

    def handle_fabbisogno_titoli(self, e):
        self._view.txt_result.controls.clear()
        codice = self._codice_scuola()
        if not codice:
            return
        titoli = self._model.get_fabbisogno_titoli(codice)
        self._aggiungi(titolo_risultati("Fabbisogno per titolo", self._model.get_nome_scuola(codice)))
        self._riepilogo(f"{len(titoli)} titoli da acquistare; se tutti gli studenti li comprassero nuovi, la "
                        f"spesa sarebbe di {formato(sum(l.prezzo * s for l, _, s in titoli))} €")
        righe = [ft.DataRow(cells=[
            cella_testo(libro.titolo, 230), cella_testo(libro.disciplina, 120), cella(formato(libro.prezzo, 2)),
            cella_testo(", ".join(classi), 110), cella(str(studenti)), cella(formato(libro.prezzo * studenti, 2)),
        ]) for libro, classi, studenti in titoli]
        self._aggiungi(scorrevole(tabella(
            [colonna("Titolo"), colonna("Disciplina"), colonna("Prezzo €"), colonna("Classi"),
             colonna("Studenti\n(stima)"), colonna("Costo se tutti\nlo comprano €")], righe)))
        self._view.update_page()

    def _leggi_parametri_piano(self):
        try:
            budget = float(self._view.txt_budget.value.replace(",", "."))
            richiedenti = float(self._view.txt_richiedenti.value.replace(",", ".")) / 100
            soglia = float(self._view.txt_soglia_isee.value.replace(",", "."))
            prezzo_usato = float(self._view.txt_prezzo_usato.value.replace(",", ".")) / 100
            usato = float(self._view.txt_usato_disponibile.value.replace(",", ".")) / 100
        except ValueError:
            self._mostra_errore("Parametri del piano non validi: scrivi numeri senza punti delle migliaia "
                                "(es. 20000).")
            return None
        if budget <= 0 or soglia <= 0 or not 0 < richiedenti <= 1 or not 0 <= prezzo_usato <= 1 \
                or not 0 <= usato <= 1:
            self._mostra_errore("Budget e soglia ISEE devono essere positivi; richiedenti tra 1 e 100%; "
                                "prezzo e copie usate tra 0 e 100%.")
            return None
        return ParametriPiano(budget=budget, quota_richiedenti=richiedenti, soglia_isee=soglia,
                              prezzo_usato=prezzo_usato, usato_disponibile=usato)

    def handle_piano(self, e):
        self._view.txt_result.controls.clear()
        codice = self._codice_scuola()
        parametri = self._leggi_parametri_piano() if codice else None
        if parametri is None:
            return
        piano = self._model.calcola_piano(codice, parametri, "branch_bound")
        quota = 100 * self._model.get_quota_isee(parametri.soglia_isee)
        self._aggiungi(titolo_risultati("Piano di acquisto", f"{self._model.get_nome_scuola(codice)}, budget "
                                                             f"{formato(parametri.budget)} €"))
        self._riepilogo(f"Richiedenti: {piano.richiedenti}, di cui {piano.aventi_diritto} con ISEE sotto "
                        f"{formato(parametri.soglia_isee)} € (aventi diritto)\n"
                        f"Serviti con il kit completo: {piano.studenti_serviti} "
                        f"({formato(piano.pct_soddisfatte, 1)}% degli aventi diritto), spesa "
                        f"{formato(piano.costo_totale)} €\n"
                        f"Copie da acquistare: {piano.copie_usate} usate e {piano.copie_nuove} nuove")
        if piano.aventi_diritto and not piano.studenti_serviti:
            self._mostra_errore("Nessuno studente servito: il budget è inferiore al costo di qualsiasi kit. "
                                "Hai scritto il budget con i punti delle migliaia? (scrivi 20000, non 20.000)")
        self._aggiungi(scorrevole(tabella(
            [colonna("Titolo"), colonna("Disciplina"), colonna("Classi"), colonna("Copie\nusate"),
             colonna("Copie\nnuove"), colonna("Costo €")],
            [ft.DataRow(cells=[
                cella_testo(v.libro.titolo, 230), cella_testo(v.libro.disciplina, 120),
                cella_testo(", ".join(sorted(v.classi)), 110), cella(str(v.copie_usate)),
                cella(str(v.copie_nuove)), cella(formato(v.costo, 2)),
            ]) for v in piano.voci])))
        self._nota(f"Richieste e ISEE sono generati dalla distribuzione INPS delle famiglie con minori "
                   f"(provincia di Torino): il {formato(quota, 1)}% ha un ISEE sotto la soglia")
        self._view.update_page()

    def handle_confronta(self, e):
        self._view.txt_result.controls.clear()
        codice = self._codice_scuola()
        parametri = self._leggi_parametri_piano() if codice else None
        if parametri is None:
            return
        piani = self._model.confronta_metodi(codice, parametri)
        nomi = {"greedy": "Greedy", "branch_bound": "Branch & bound"}
        self._aggiungi(titolo_risultati("Confronto algoritmi", f"{self._model.get_nome_scuola(codice)}, budget "
                                                               f"{formato(parametri.budget)} €"))
        self._aggiungi(scorrevole(tabella(
            [colonna("Algoritmo"), colonna("Studenti\nserviti"), colonna("Spesa €"), colonna("Nodi\nesplorati"),
             colonna("Tempo")],
            [ft.DataRow(cells=[
                cella(nomi[p.metodo]), cella(str(p.studenti_serviti)), cella(formato(p.costo_totale, 2)),
                cella(formato(p.nodi_visitati) if p.metodo != "greedy" else "—"),
                cella(f"{formato(p.tempo_s * 1000, 2)} ms")]) for p in piani])))
        self._nota("Greedy: sceglie le classi con il miglior rapporto studenti/costo finché c'è budget, è veloce "
                   "ma non garantisce la soluzione migliore\n"
                   "Branch & bound: ricorsione con backtracking che scarta in anticipo le combinazioni che non "
                   "possono migliorare il risultato; trova sempre la soluzione ottima")
        self._view.update_page()

    def fill_p_cambio(self):
        self._view.txt_p_cambio.value = f"{self._model.get_quota_nuove_adozioni() * 100:.1f}"
        self._view.update_page()

    def _leggi_parametri_simulazione(self, piano):
        try:
            anni = int(self._view.txt_anni.value)
            budget_annuo = float(self._view.txt_budget_annuo.value.replace(",", "."))
            quote = [float(campo.value.replace(",", ".")) / 100
                     for campo in (self._view.txt_p_danno, self._view.txt_p_perdita, self._view.txt_p_cambio)]
        except ValueError:
            self._mostra_errore("Parametri della simulazione non validi: gli anni sono un numero intero, "
                                "le percentuali numeri tra 0 e 100.")
            return None
        if not 1 <= anni <= 20 or budget_annuo < 0 or not all(0 <= x <= 1 for x in quote):
            self._mostra_errore("Anni tra 1 e 20, budget annuo non negativo, percentuali tra 0 e 100.")
            return None
        p_danno, p_perdita, p_cambio = quote
        return ParametriSimulazione(piano=piano, anni=anni, budget_annuo=budget_annuo, p_danno=p_danno,
                                    p_perdita=p_perdita, p_cambio=p_cambio)

    def handle_simula(self, e):
        self._view.txt_result.controls.clear()
        codice = self._codice_scuola()
        piano = self._leggi_parametri_piano() if codice else None
        p = self._leggi_parametri_simulazione(piano) if piano else None
        if p is None:
            return
        statistiche, tempo = self._model.simula(codice, p)
        r = self._model.riepilogo(statistiche)
        self._aggiungi(titolo_risultati(
            "Simulazione pluriennale",
            f"{self._model.get_nome_scuola(codice)}: budget iniziale {formato(piano.budget)} €, poi "
            f"{formato(p.budget_annuo)} €/anno; ogni anno copie rovinate {formato(100 * p.p_danno)}%, perse "
            f"{formato(100 * p.p_perdita)}%, titoli cambiati {formato(100 * p.p_cambio, 1)}%"))
        self._riepilogo(f"In {p.anni} anni: {formato(r['serviti_totali'])} studenti serviti, spesa della scuola "
                        f"{formato(r['spesa_totale'])} €, risparmio delle famiglie {formato(r['risparmio_totale'])} €\n"
                        f"Saldo (risparmio meno spesa): {formato(r['saldo_finale'])} €; costo per studente servito "
                        f"{formato(r['costo_per_studente'], 2)} € (calcolo in {formato(tempo * 1000)} ms)")

        def c(s, ind, dec=0):
            return cella(formato(s.valori[ind], dec))

        self._aggiungi(scorrevole(tabella(
            [colonna("Anno"), colonna("Aventi\ndiritto"), colonna("Serviti"), colonna("Richieste\nsoddisfatte %"),
             colonna("Spesa\nscuola €"), colonna("Risparmio\nfamiglie €"), colonna("Copie\nacquistate"),
             colonna("Copie in\nmagazzino"), colonna("Costo per\nstudente €")],
            [ft.DataRow(cells=[cella(str(s.anno + 1)), c(s, "aventi_diritto"), c(s, "studenti_serviti"),
                               c(s, "pct_soddisfatte", 1), c(s, "spesa"), c(s, "risparmio_famiglie"),
                               c(s, "copie_acquistate"), c(s, "copie_magazzino"), c(s, "costo_per_studente", 2)])
             for s in statistiche])))
        anni = [s.anno + 1 for s in statistiche]
        self._aggiungi(grafico_linee("Studenti serviti con il kit completo", anni,
                                     [("Studenti serviti", [s.valori["studenti_serviti"] for s in statistiche])]))
        self._aggiungi(grafico_linee("Spesa della scuola e risparmio delle famiglie (€)", anni,
                                     [("Spesa della scuola", [s.valori["spesa"] for s in statistiche]),
                                      ("Risparmio delle famiglie",
                                       [s.valori["risparmio_famiglie"] for s in statistiche])]))
        self._view.btn_salva_scenario.disabled = False
        if not self._view.txt_nome_scenario.value:
            self._view.txt_nome_scenario.value = f"{self._model.get_nome_scuola(codice)[:25]} - scenario"
        self._view.update_page()

    def fill_scenari(self):
        self._view.lv_scenari.controls.clear()
        scenari = self._model.get_scenari()
        for s in scenari:
            self._view.lv_scenari.controls.append(ft.Checkbox(
                label=f"{s} — {self._model.get_nome_scuola(s.codice_scuola)[:25]}", value=False, data=s.id,
                label_style=ft.TextStyle(size=13)))
        if not scenari:
            self._view.lv_scenari.controls.append(testo_secondario(
                "Nessuno scenario: esegui una simulazione e premi Salva", italic=True))
        self._view.update_page()

    def handle_salva_scenario(self, e):
        nome = self._view.txt_nome_scenario.value.strip()
        if not nome:
            self._mostra_errore("Scrivi un nome per lo scenario.")
            return
        try:
            scenario = self._model.salva_ultima_simulazione(nome[:100])
        except ValueError as err:
            self._mostra_errore(str(err))
            return
        self._view.btn_salva_scenario.disabled = True
        self._view.txt_nome_scenario.value = ""
        self._riepilogo(f"Scenario salvato: {scenario}")
        self.fill_scenari()

    def _scenari_selezionati(self):
        return [cb.data for cb in self._view.lv_scenari.controls if isinstance(cb, ft.Checkbox) and cb.value]

    def handle_elimina_scenari(self, e):
        ids = self._scenari_selezionati()
        if not ids:
            self._mostra_errore("Seleziona gli scenari da eliminare.")
            return
        self._model.elimina_scenari(ids)
        self.fill_scenari()

    def handle_confronta_scenari(self, e):
        self._view.txt_result.controls.clear()
        ids = self._scenari_selezionati()
        if not ids:
            self._mostra_errore("Seleziona almeno uno scenario da confrontare.")
            return
        scenari = sorted((s for s in self._model.get_scenari() if s.id in ids), key=lambda s: s.creato)
        if len({s.codice_scuola for s in scenari}) > 1:
            self._mostra_errore("Confronta scenari della stessa scuola.")
            return
        dati = [(s, self._model.get_statistiche_scenario(s.id)) for s in scenari]
        self._aggiungi(titolo_risultati(f"Confronto tra {len(scenari)} scenari",
                                        self._model.get_nome_scuola(scenari[0].codice_scuola)))
        righe = []
        for s, stat in dati:
            r = self._model.riepilogo(stat)
            righe.append(ft.DataRow(cells=[
                cella_testo(s.nome, 150), cella(formato(s.budget_annuo)), cella(formato(100 * s.p_danno)),
                cella(formato(100 * s.p_cambio, 1)), cella(str(s.anni)),
                cella(formato(r["serviti_totali"])), cella(formato(r["pct_soddisfatte_media"], 1)),
                cella(formato(r["spesa_totale"])), cella(formato(r["saldo_finale"])),
                cella(formato(r["costo_per_studente"], 2))]))
        self._aggiungi(scorrevole(tabella(
            [colonna("Scenario"), colonna("Budget\nannuo €"), colonna("Rovinate\n%"), colonna("Cambi di\nadozione %"),
             colonna("Anni"), colonna("Studenti\nserviti"), colonna("Richieste\nsoddisfatte %"),
             colonna("Spesa\ntotale €"), colonna("Saldo\nfinale €"), colonna("Costo per\nstudente €")],
            righe, column_spacing=14)))
        confrontabili = dati[:MAX_SERIE]
        for indicatore, titolo in (("studenti_serviti", "Studenti serviti per anno"),
                                   ("saldo_cumulato", "Saldo cumulato (€): risparmio delle famiglie meno spesa")):
            anni_max = max(len(st) for _, st in confrontabili)
            self._aggiungi(grafico_linee(titolo, list(range(1, anni_max + 1)),
                                         [(s.nome[:30], [x.valori[indicatore] for x in st])
                                          for s, st in confrontabili]))
        self._view.update_page()

    def _codici_rete(self):
        return [cb.data for cb in self._view.cb_scuole if cb.value]

    def handle_cambio_selezione(self, e):
        self._view.txt_num_selezionate.value = f"Scuole selezionate: {len(self._codici_rete())}"
        self._view.update_page()

    def handle_cerca_scuola(self, e):
        testo = self._view.txt_cerca.value.strip().upper()
        self._view.lv_scuole.controls = [cb for cb in self._view.cb_scuole if testo in cb.label.upper()]
        self._view.update_page()

    def handle_seleziona_tutte(self, e):
        for cb in self._view.lv_scuole.controls:
            cb.value = True
        self.handle_cambio_selezione(e)

    def handle_seleziona_nessuna(self, e):
        for cb in self._view.cb_scuole:
            cb.value = False
        self.handle_cambio_selezione(e)

    def _leggi_rete(self):
        codici = self._codici_rete()
        if len(codici) < 2:
            self._mostra_errore("Seleziona almeno due scuole nella rete.")
            return None
        return codici

    def handle_grafo(self, e):
        self._view.txt_result.controls.clear()
        codici = self._leggi_rete()
        if codici is None:
            return
        grafo = self._model.crea_grafo(codici)
        gruppi = self._model.gruppi_scuole(grafo)
        info = self._model.statistiche_grafo(grafo)
        self._aggiungi(titolo_risultati("Grafo della rete", "Due scuole sono collegate se adottano almeno un "
                                                            "libro in comune; il peso è la distanza"))
        self._riepilogo(f"{info['nodi']} scuole, {formato(info['archi'])} collegamenti, "
                        f"{info['componenti']} componenti connesse, in media "
                        f"{formato(info['grado_medio'], 1)} collegamenti per scuola\n"
                        f"Gruppi di scuole con almeno {SOGLIA_GRUPPI} libri in comune: "
                        f"{sum(len(g) > 1 for g in gruppi)}, più {sum(len(g) == 1 for g in gruppi)} "
                        f"scuole isolate")

        veri = [(i + 1, g) for i, g in enumerate(gruppi) if len(g) > 1]
        righe = []
        for numero, gruppo in veri:
            comuni, km = self._model.statistiche_gruppo(grafo, gruppo)
            righe.append(ft.DataRow(cells=[cella(str(numero)), cella(str(len(gruppo))),
                                           cella(formato(comuni, 1)), cella(formato(km, 1))]))
        self._aggiungi(scorrevole(tabella(
            [colonna("Gruppo"), colonna("Scuole"), colonna("Libri in comune\n(media per coppia)"),
             colonna("Distanza\nmedia km")], righe)))
        for numero, gruppo in veri:
            nomi = ", ".join(sorted(self._model.get_nome_scuola(c) for c in gruppo))
            self._aggiungi(ft.Text(spans=[ft.TextSpan(f"Gruppo {numero}: ", ft.TextStyle(weight=ft.FontWeight.BOLD)),
                                          ft.TextSpan(nomi)], size=13))
        self._view.update_page()

    def handle_trasferimenti(self, e):
        self._view.txt_result.controls.clear()
        codici = self._leggi_rete()
        piano = self._leggi_parametri_piano() if codici else None
        p = self._leggi_parametri_simulazione(piano) if piano else None
        if p is None:
            return
        self._riepilogo(f"Calcolo dei trasferimenti tra {len(codici)} scuole in corso...")
        self._view.update_page()
        risultato = self._model.pianifica_trasferimenti(codici, p)
        self._view.txt_result.controls.clear()
        nome = self._model.get_nome_scuola
        km_medi = risultato.copie_km / risultato.copie_ricevute if risultato.copie_ricevute else 0
        self._aggiungi(titolo_risultati(f"Trasferimenti di copie tra {len(codici)} scuole",
                                        "Fine del primo anno: ogni scuola in carenza prende le copie dalla scuola più "
                                        "vicina tra quelle che ne hanno in più"))
        self._riepilogo(f"Copie in più nelle scuole: {formato(risultato.eccedenze)}; copie che mancano: "
                        f"{formato(risultato.carenze)}\n"
                        f"Copie spostate: {formato(risultato.copie_ricevute)} in {formato(len(risultato.viaggi))} "
                        f"viaggi, in media {formato(km_medi, 1)} km per copia; risparmio "
                        f"{formato(risultato.risparmio)} € (copie non ricomprate)")

        trasferimenti = sorted(risultato.trasferimenti, key=lambda t: (-t.copie, t.km))
        self._aggiungi(scorrevole(tabella(
            [colonna("Da"), colonna("A"), colonna("Titolo"), colonna("Copie"), colonna("km")],
            [ft.DataRow(cells=[cella_testo(nome(t.da), 150), cella_testo(nome(t.a), 150),
                               cella_testo(t.libro.titolo, 230), cella(str(t.copie)), cella(formato(t.km, 2))])
             for t in trasferimenti[:200]])))
        if len(trasferimenti) > 200:
            self._nota(f"Primi 200 trasferimenti su {formato(len(trasferimenti))}")
        self._view.update_page()

    def _aggiungi(self, controllo):
        self._view.txt_result.controls.append(controllo)

    def _riepilogo(self, testo):
        self._aggiungi(ft.Container(content=ft.Text(testo, size=14), bgcolor="#e2f0ec", border_radius=8,
                                    padding=ft.padding.symmetric(10, 14),
                                    border=ft.border.only(left=ft.BorderSide(4, PRIMARIO))))

    def _nota(self, testo):
        self._aggiungi(testo_secondario(testo, italic=True))

    def _mostra_errore(self, messaggio):
        self._aggiungi(ft.Text(messaggio, color=ERRORE))
        self._view.update_page()

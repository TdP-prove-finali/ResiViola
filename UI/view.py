import flet as ft

from UI import stile
from UI.stile import ACCENTO, campo, pulsante, pulsante_secondario, sezione, testo_secondario

NOME_APP = "PrestiTO"
SOTTOTITOLO_APP = "Libri di testo in comodato per le scuole superiori di Torino"
LARGHEZZA_COMANDI = 400
CAMPO_META = 174


class View:
    def __init__(self, page: ft.Page):
        self._page = page
        self._page.title = f"{NOME_APP} - Libri di testo in comodato"
        self._page.theme_mode = ft.ThemeMode.LIGHT
        self._page.theme = stile.tema()
        self._page.bgcolor = stile.SFONDO
        self._page.padding = 0
        self._page.window_maximized = True
        self._controller = None

        self.dd_scuola = None
        self.btn_fabbisogno_classi = None
        self.btn_fabbisogno_titoli = None
        self.txt_budget = None
        self.txt_richiedenti = None
        self.txt_soglia_isee = None
        self.txt_prezzo_usato = None
        self.txt_usato_disponibile = None
        self.btn_piano = None
        self.btn_confronta = None
        self.txt_anni = None
        self.txt_budget_annuo = None
        self.txt_p_danno = None
        self.txt_p_perdita = None
        self.txt_p_cambio = None
        self.btn_simula = None
        self.txt_nome_scenario = None
        self.btn_salva_scenario = None
        self.lv_scenari = None
        self.btn_confronta_scenari = None
        self.btn_elimina_scenari = None
        self.txt_cerca = None
        self.lv_scuole = None
        self.cb_scuole = []
        self.txt_num_selezionate = None
        self.btn_tutte = None
        self.btn_nessuna = None
        self.btn_grafo = None
        self.btn_trasferimenti = None

        self.txt_result = None

    def set_controller(self, controller):
        self._controller = controller

    def load_interface(self):
        c = self._controller

        self.dd_scuola = ft.Dropdown(label="Scuola", dense=True, text_size=14, border_radius=8)
        self.btn_fabbisogno_classi = pulsante("Per classe", ft.icons.CLASS_OUTLINED, c.handle_fabbisogno_classi)
        self.btn_fabbisogno_titoli = pulsante_secondario("Per titolo", ft.icons.MENU_BOOK, c.handle_fabbisogno_titoli)

        self.txt_budget = campo("Budget", "20000", "€", width=CAMPO_META)
        self.txt_richiedenti = campo("Richiedenti", "60", "%", width=CAMPO_META)
        self.txt_soglia_isee = campo("Soglia ISEE", "15748.78", "€", width=CAMPO_META)
        self.txt_prezzo_usato = campo("Prezzo usato", "50", "%", width=CAMPO_META)
        self.txt_usato_disponibile = campo("Copie usate", "30", "%", width=CAMPO_META)
        self.btn_piano = pulsante("Calcola piano", ft.icons.CALCULATE, c.handle_piano)
        self.btn_confronta = pulsante_secondario("Confronta algoritmi", ft.icons.COMPARE_ARROWS, c.handle_confronta)

        self.txt_anni = campo("Anni", "5", width=CAMPO_META)
        self.txt_budget_annuo = campo("Budget annuo", "5000", "€", width=CAMPO_META)
        self.txt_p_danno = campo("Copie rovinate", "10", "%", width=CAMPO_META)
        self.txt_p_perdita = campo("Copie perse", "3", "%", width=CAMPO_META)
        self.txt_p_cambio = campo("Cambi di adozione", "", "%", width=CAMPO_META)
        self.btn_simula = pulsante("Simula", ft.icons.PLAY_ARROW, c.handle_simula)
        self.txt_nome_scenario = campo("Nome dello scenario", width=260)
        self.btn_salva_scenario = pulsante_secondario("Salva", ft.icons.SAVE_OUTLINED, c.handle_salva_scenario,
                                                      disabled=True)

        self.lv_scenari = ft.ListView(height=110, spacing=0)
        self.btn_confronta_scenari = pulsante("Confronta", ft.icons.COMPARE_ARROWS, c.handle_confronta_scenari)
        self.btn_elimina_scenari = pulsante_secondario("Elimina", ft.icons.DELETE_OUTLINE, c.handle_elimina_scenari)

        self.txt_cerca = campo("Cerca scuola", on_change=c.handle_cerca_scuola, prefix_icon=ft.icons.SEARCH)
        self.lv_scuole = ft.ListView(height=180, spacing=0)
        self.txt_num_selezionate = testo_secondario("Scuole selezionate: 0")
        self.btn_tutte = ft.TextButton("Tutte", on_click=c.handle_seleziona_tutte)
        self.btn_nessuna = ft.TextButton("Nessuna", on_click=c.handle_seleziona_nessuna)
        self.btn_grafo = pulsante("Grafo e gruppi", ft.icons.HUB, c.handle_grafo)
        self.btn_trasferimenti = pulsante_secondario("Trasferimenti", ft.icons.LOCAL_SHIPPING_OUTLINED,
                                                     c.handle_trasferimenti)

        riga = lambda *controlli: ft.Row(list(controlli), spacing=10)
        self._pagine = [
            ("Fabbisogno", ft.icons.SCHOOL_OUTLINED, "Fabbisogno di libri della scuola", lambda: [
                self.dd_scuola, riga(self.btn_fabbisogno_classi, self.btn_fabbisogno_titoli)]),
            ("Piano", ft.icons.SHOPPING_CART_OUTLINED, "Piano di acquisto", lambda: [
                self.dd_scuola,
                riga(self.txt_budget, self.txt_richiedenti),
                riga(self.txt_soglia_isee, self.txt_prezzo_usato),
                riga(self.txt_usato_disponibile),
                riga(self.btn_piano, self.btn_confronta)]),
            ("Simulazione", ft.icons.AUTO_GRAPH, "Simulazione pluriennale", lambda: [
                self.dd_scuola,
                riga(self.txt_anni, self.txt_budget_annuo),
                riga(self.txt_p_danno, self.txt_p_perdita),
                riga(self.txt_p_cambio),
                testo_secondario("Il primo anno usa budget e parametri della pagina Piano"),
                self.btn_simula,
                riga(self.txt_nome_scenario, self.btn_salva_scenario)]),
            ("Scenari", ft.icons.BOOKMARKS_OUTLINED, "Scenari salvati", lambda: [
                testo_secondario("Seleziona gli scenari da confrontare"),
                self.lv_scenari, riga(self.btn_confronta_scenari, self.btn_elimina_scenari)]),
            ("Rete", ft.icons.HUB_OUTLINED, "Rete di scuole", lambda: [
                self.txt_cerca,
                ft.Container(content=self.lv_scuole, border=ft.border.all(1, stile.BORDO), border_radius=8),
                riga(self.txt_num_selezionate, self.btn_tutte, self.btn_nessuna),
                riga(self.btn_grafo, self.btn_trasferimenti),
                testo_secondario("I trasferimenti usano i parametri delle pagine Piano e Simulazione")]),
        ]

        self.txt_result = ft.ListView(expand=True, spacing=12, padding=ft.padding.only(right=12, bottom=20))
        self._comandi = ft.Column(width=LARGHEZZA_COMANDI, spacing=12, scroll=ft.ScrollMode.AUTO)

        self._rail = ft.NavigationRail(
            selected_index=0, label_type=ft.NavigationRailLabelType.ALL, min_width=96,
            bgcolor=stile.SUPERFICIE, indicator_color=stile.PRIMARIO_CHIARO,
            destinations=[ft.NavigationRailDestination(icon=icona, label=etichetta)
                          for etichetta, icona, _, _ in self._pagine],
            on_change=lambda e: self.vai_a(e.control.selected_index))

        intestazione = ft.Container(
            bgcolor=stile.PRIMARIO_SCURO, padding=ft.padding.symmetric(10, 20),
            content=ft.Row([ft.Icon(ft.icons.AUTO_STORIES, color="#ffffff", size=26),
                            ft.Text(spans=[ft.TextSpan("Presti", ft.TextStyle(color="#ffffff")),
                                           ft.TextSpan("TO", ft.TextStyle(color=ACCENTO))],
                                    size=22, weight=ft.FontWeight.W_800),
                            ft.Text(SOTTOTITOLO_APP, size=13, color="#d6e6e2")], spacing=12))

        self._page.add(ft.Column(expand=True, spacing=0, controls=[
            intestazione,
            ft.Row(expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.STRETCH, controls=[
                self._rail,
                ft.VerticalDivider(width=1, color=stile.BORDO),
                ft.Container(expand=True, padding=16, content=ft.Row(
                    [self._comandi, ft.Container(content=self.txt_result, expand=True)],
                    spacing=16, expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH))])]))

        self.vai_a(0)
        c.fill_scuole()
        c.fill_p_cambio()
        c.fill_scenari()

    def vai_a(self, indice):
        _, icona, titolo, comandi = self._pagine[indice]
        self._rail.selected_index = indice
        self._comandi.controls = [sezione(titolo, icona, comandi())]
        self.txt_result.controls.clear()
        self.update_page()

    def update_page(self):
        self._page.update()

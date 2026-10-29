import flet as ft

PRIMARIO = "#0f6b5c"
PRIMARIO_SCURO = "#0a4a40"
PRIMARIO_CHIARO = "#e2f0ec"
ACCENTO = "#ffc857"
SFONDO = "#f2f6f5"
SUPERFICIE = "#ffffff"
BORDO = "#dde6e3"
TESTO = "#14201e"
TESTO_2 = "#56625f"
ERRORE = "#b3261e"


def tema():
    return ft.Theme(color_scheme_seed=PRIMARIO,
                    color_scheme=ft.ColorScheme(primary=PRIMARIO, on_primary="#ffffff",
                                                primary_container=PRIMARIO_CHIARO, surface_tint=SUPERFICIE))


def testo_secondario(testo, size=12, **kwargs):
    return ft.Text(testo, size=size, color=TESTO_2, **kwargs)


def sezione(titolo, icona, controlli):
    return ft.Container(
        content=ft.Column([ft.Row([ft.Icon(icona, color=PRIMARIO, size=20),
                                   ft.Text(titolo, size=15, weight=ft.FontWeight.W_600, color=TESTO)],
                                  spacing=8)] + controlli,
                          spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
        bgcolor=SUPERFICIE, border_radius=12, border=ft.border.all(1, BORDO), padding=14)


def pulsante(testo, icona, on_click):
    return ft.FilledButton(testo, icon=icona, on_click=on_click,
                           style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))


def pulsante_secondario(testo, icona, on_click, disabled=False):
    return ft.OutlinedButton(testo, icon=icona, on_click=on_click, disabled=disabled,
                             style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))


def campo(etichetta, valore="", suffisso=None, **kwargs):
    return ft.TextField(label=etichetta, value=valore, suffix_text=suffisso, border_radius=8,
                        border_color=BORDO, focused_border_color=PRIMARIO, bgcolor=SUPERFICIE,
                        text_size=14, dense=True, **kwargs)


def tabella(colonne, righe, **kwargs):
    parametri = dict(heading_row_color=PRIMARIO_CHIARO, heading_row_height=52,
                     heading_text_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_600, color=PRIMARIO_SCURO),
                     data_text_style=ft.TextStyle(size=13, color=TESTO), data_row_min_height=40,
                     data_row_max_height=64, border=ft.border.all(1, BORDO), border_radius=8,
                     horizontal_lines=ft.BorderSide(1, "#edf1f0"), column_spacing=18, bgcolor=SUPERFICIE)
    parametri.update(kwargs)
    return ft.DataTable(columns=colonne, rows=righe, **parametri)


def titolo_risultati(testo, sottotitolo=None):
    controlli = [ft.Text(testo, size=18, weight=ft.FontWeight.BOLD, color=TESTO)]
    if sottotitolo:
        controlli.append(testo_secondario(sottotitolo, 13))
    return ft.Column(controlli, spacing=2)

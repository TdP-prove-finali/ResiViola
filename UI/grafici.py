import flet as ft

from UI.stile import BORDO, SUPERFICIE, TESTO

COLORI_SERIE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
MAX_SERIE = len(COLORI_SERIE)
TESTO_SECONDARIO = "#52514e"
GRIGLIA = "#e1e0d9"


def _formato(valore):
    return f"{valore:,.0f}".replace(",", ".")


def _passo(massimo):
    grezzo = max(massimo, 1) / 3
    potenza = 10 ** (len(str(int(grezzo))) - 1)
    for m in (1, 2, 5, 10):
        if grezzo <= m * potenza:
            return m * potenza
    return 10 * potenza


def legenda(voci):
    return ft.Row(wrap=True, spacing=16, run_spacing=6, controls=[
        ft.Row(spacing=6, tight=True, controls=[
            ft.Container(width=12, height=12, bgcolor=colore, border_radius=6),
            ft.Text(testo, size=12, color=TESTO_SECONDARIO)])
        for colore, testo in voci])


def grafico_linee(titolo, anni, serie):
    serie = serie[:MAX_SERIE]
    massimo = max((max(v) for _, v in serie if v), default=0)
    passo = _passo(massimo)
    limite = passo * (int(massimo / passo) + 1)

    dati = [ft.LineChartData(
        data_points=[ft.LineChartDataPoint(x, y) for x, y in zip(anni, valori)],
        stroke_width=3, color=COLORI_SERIE[i], curved=False, stroke_cap_round=True)
        for i, (nome, valori) in enumerate(serie)]

    grafico = ft.LineChart(
        data_series=dati,
        min_x=min(anni), max_x=max(anni), min_y=0, max_y=limite,
        height=170, expand=True,
        horizontal_grid_lines=ft.ChartGridLines(interval=passo, color=GRIGLIA, width=1),
        border=ft.border.only(bottom=ft.BorderSide(1, GRIGLIA)),
        left_axis=ft.ChartAxis(
            labels=[ft.ChartAxisLabel(value=v, label=ft.Text(_formato(v), size=11, color=TESTO_SECONDARIO))
                    for v in range(0, int(limite) + 1, int(passo))],
            labels_size=60),
        bottom_axis=ft.ChartAxis(
            labels=[ft.ChartAxisLabel(value=a, label=ft.Text(f"anno {a}", size=11, color=TESTO_SECONDARIO))
                    for a in anni],
            labels_size=28, labels_interval=1),
        interactive=False,
    )

    controlli = []
    if len(serie) > 1:
        controlli.append(legenda([(COLORI_SERIE[i], nome) for i, (nome, _) in enumerate(serie)]))
    controlli.append(ft.Container(content=grafico, padding=ft.padding.only(right=24, top=4)))
    return ft.Container(
        content=ft.Column([ft.Text(titolo, size=15, weight=ft.FontWeight.W_600, color=TESTO)] + controlli,
                          spacing=6),
        bgcolor=SUPERFICIE, border_radius=12, border=ft.border.all(1, BORDO), padding=14)

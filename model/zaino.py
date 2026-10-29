import math


class Zaino:
    def __init__(self):
        self._costi = []
        self._valori = []
        self._usa_bound = True
        self._best_valore = 0
        self._best_scelte = []
        self._nodi = 0

    def risolvi(self, costi, valori, capacita, metodo="branch_bound"):
        gratuiti = [i for i in range(len(costi)) if costi[i] == 0]
        ordine = sorted((i for i in range(len(costi)) if 0 < costi[i] <= capacita),
                        key=lambda i: valori[i] / costi[i], reverse=True)
        self._costi = [costi[i] for i in ordine]
        self._valori = [valori[i] for i in ordine]

        if metodo == "greedy":
            posizioni = self._greedy(capacita)
            nodi = 0
        else:
            self._usa_bound = metodo in ("branch_bound", "bound_senza_greedy")
            self._best_scelte = self._greedy(capacita) if metodo == "branch_bound" else []
            self._best_valore = sum(self._valori[p] for p in self._best_scelte)
            self._nodi = 0
            self._ricorsione(0, capacita, 0, [])
            posizioni = self._best_scelte
            nodi = self._nodi

        return gratuiti + [ordine[p] for p in posizioni], nodi

    def _greedy(self, capacita):
        scelte = []
        residuo = capacita
        for p in range(len(self._costi)):
            if self._costi[p] <= residuo:
                scelte.append(p)
                residuo -= self._costi[p]
        return scelte

    def _ricorsione(self, i, residuo, valore, parziale):
        self._nodi += 1

        if valore > self._best_valore:
            self._best_valore = valore
            self._best_scelte = list(parziale)

        if i == len(self._costi):
            return

        if self._usa_bound and self._limite_superiore(i, residuo, valore) <= self._best_valore:
            return

        if self._costi[i] <= residuo:
            parziale.append(i)
            self._ricorsione(i + 1, residuo - self._costi[i], valore + self._valori[i], parziale)
            parziale.pop()

        self._ricorsione(i + 1, residuo, valore, parziale)

    def _limite_superiore(self, i, residuo, valore):
        limite = valore
        for j in range(i, len(self._costi)):
            if self._costi[j] <= residuo:
                residuo -= self._costi[j]
                limite += self._valori[j]
            else:
                limite += self._valori[j] * residuo / self._costi[j]
                break
        return math.floor(limite)

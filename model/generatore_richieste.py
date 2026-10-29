from model.richiesta import Richiesta

LIMITE_CLASSE_APERTA = 150000.0


def genera_richieste(classi, quota_richiedenti, classi_isee, rng):
    pesi = [c.nuclei_con_minori for c in classi_isee]
    richieste = []
    for classe in classi:
        num_richiedenti = round(classe.num_studenti * quota_richiedenti)
        estratte = rng.choices(classi_isee, weights=pesi, k=num_richiedenti) if pesi else []
        for c_isee in estratte:
            limite_sup = c_isee.limite_sup if c_isee.limite_sup is not None else LIMITE_CLASSE_APERTA
            isee = rng.uniform(c_isee.limite_inf, limite_sup) if limite_sup > c_isee.limite_inf else 0.0
            richieste.append(Richiesta(id=len(richieste), codice_scuola=classe.codice_scuola,
                                       anno_corso=classe.anno_corso, sezione=classe.sezione,
                                       isee=round(isee, 2)))
    return richieste


def graduatoria(richieste, soglia_isee=None):
    ammesse = [r for r in richieste if soglia_isee is None or r.isee <= soglia_isee]
    return sorted(ammesse, key=lambda r: r.isee)

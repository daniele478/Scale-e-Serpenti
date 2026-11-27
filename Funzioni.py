import random
import sys

# GENERAZIONE PROCEDURALE DEL TABELLONE
def genera_collegamenti_casuali(num_scale: int = 8, num_serpenti: int = 8) -> dict[int, tuple[int, str, str]]:
    """
    Genera casualmente scale e serpenti sul tabellone garantendo:
    1. L'assenza di catene (nessun arrivo coincide con la partenza di un altro collegamento).
    2. L'unicita' delle estremita' (due elementi non possono condividere partenza o arrivo).
    3. La protezione delle caselle critiche 1 (inizio) e 100 (vittoria).

    Restituisce un dizionario nel formato:
        { casella_partenza: (casella_arrivo, tipo, colore) }
    """
    collegamenti: dict[int, tuple[int, str, str]] = {}

    # Insieme per tracciare tutte le caselle gia' impegnate (sia partenze che arrivi).
    caselle_occupate: set[int] = {1, 100}

    # Liste di colori concordate al genere del sostantivo ("scala Rossa", "serpente Rosso")
    colori_scale = ["Rossa", "Gialla", "Verde", "Blu"]
    colori_serpenti = ["Rosso", "Giallo", "Verde", "Blu"]

    # GENERAZIONE SCALE (movimento verso l'alto: partenza < arrivo)
    scale_create = 0
    tentativi = 0
    # Anti-loop infinito: interrompe il ciclo se non ci sono piu' combinazioni libere
    while scale_create < num_scale and tentativi < 1000:
        tentativi += 1
        # Partenza max 89 e salto minimo +5 garantiscono un arrivo valido entro la casella 99
        partenza = random.randint(2, 89)
        arrivo = random.randint(partenza + 5, 99)

        # Verifica che entrambe le estremita' siano completamente libere
        if partenza not in caselle_occupate and arrivo not in caselle_occupate:
            collegamenti[partenza] = (arrivo, "scala", random.choice(colori_scale))
            caselle_occupate.add(partenza)
            caselle_occupate.add(arrivo)
            scale_create += 1

    # GENERAZIONE SERPENTI (movimento verso il basso: partenza > arrivo)
    serpenti_creati = 0
    tentativi = 0
    while serpenti_creati < num_serpenti and tentativi < 1000:
        tentativi += 1
        # Partenza min 12 e discesa minima -5 garantiscono un arrivo valido
        partenza = random.randint(12, 99)
        arrivo = random.randint(2, partenza - 5)

        # Stesso vincolo: evita sovrapposizioni con scale o altri serpenti
        if partenza not in caselle_occupate and arrivo not in caselle_occupate:
            collegamenti[partenza] = (arrivo, "serpente", random.choice(colori_serpenti))
            caselle_occupate.add(partenza)
            caselle_occupate.add(arrivo)
            serpenti_creati += 1

    return collegamenti

# FORMATTAZIONE CLASSIFICA FINALE (CLI)
def genera_podio(classifica: list) -> str:
    """
    Costruisce una stringa formattata con il podio dei primi 3 giocatori
    per la visualizzazione nel terminale (CLI).
    Adatta automaticamente i simboli (emoji vs testo ASCII) in base all'encoding
    del terminale per evitare errori `UnicodeEncodeError` su console Windows legacy.
    """
    # Rileva in sicurezza l'encoding dello stdout (gestendo anche casi None)
    encoding = (getattr(sys.stdout, "encoding", None) or "").lower()
    if "utf" in encoding:
        simboli = [" 🥇 Primo posto", " 🥈 Secondo posto", " 🥉 Terzo posto"]
    else:
        simboli = [" [1°] Primo posto", " [2°] Secondo posto", " [3°] Terzo posto"]

    testo_podio = "\nClassifica Finale\n"

    # Scorre al massimo i primi 3 elementi della classifica tramite [:3]
    for i, giocatore in enumerate(classifica[:3]):
        testo_podio += f"{simboli[i]}: {giocatore.get_nome()} (Casella {giocatore.get_posizione()})\n"

    # Messaggio ironico di chiusura se partecipavano 4 o piu' giocatori
    if len(classifica) > 3:
        testo_podio += "Voi altri: i serpenti vi hanno preso!\n"

    return testo_podio
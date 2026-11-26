import random
import sys

def genera_collegamenti_casuali(num_scale: int = 8, num_serpenti: int = 8) -> dict[int, tuple[int, str, str]]:
    """
    Genera casualmente scale e serpenti garantendo l'assenza di catene 
    (un arrivo che coincide con una partenza) e di caselle di arrivo duplicate.
    """
    # Dizionario finale con struttura -> { casella_partenza: (casella_arrivo, tipo, colore) }
    collegamenti: dict[int, tuple[int, str, str]] = {}
    
    # Traccia tutte le caselle già usate (sia partenze che arrivi).
    # Includiamo subito 1 (partenza dei giocatori) e 100 (vittoria) per lasciarle libere.
    caselle_occupate: set[int] = {1, 100}
    
    colori_scale = ["Rossa", "Gialla", "Verde", "Blu"]
    colori_serpenti = ["Rosso", "Giallo", "Verde", "Blu"]

    # GENERAZIONE SCALE (salgono: partenza < arrivo)
    scale_create = 0
    tentativi = 0
    # Il limite di 1000 tentativi previene un ciclo infinito se si chiedono troppe scale
    while scale_create < num_scale and tentativi < 1000:
        tentativi += 1
        # La partenza arriva al massimo a 89 per lasciare spazio a una salita di almeno 5 caselle
        partenza = random.randint(2, 89)
        arrivo = random.randint(partenza + 5, 99)

        # Il doppio controllo su caselle_occupate impedisce sia le catene che gli arrivi duplicati
        if partenza not in caselle_occupate and arrivo not in caselle_occupate:
            collegamenti[partenza] = (arrivo, "scala", random.choice(colori_scale))
            # Segniamo entrambe le estremità come non più riutilizzabili
            caselle_occupate.add(partenza)
            caselle_occupate.add(arrivo)
            scale_create += 1

    # GENERAZIONE SERPENTI (scendono: partenza > arrivo)
    serpenti_creati = 0
    tentativi = 0
    while serpenti_creati < num_serpenti and tentativi < 1000:
        tentativi += 1
        # La testa del serpente parte almeno dalla 12 per garantire una discesa significativa
        partenza = random.randint(12, 99)
        arrivo = random.randint(2, partenza - 5)

        # Stesso vincolo di unicità delle scale: nessuna sovrapposizione con elementi esistenti
        if partenza not in caselle_occupate and arrivo not in caselle_occupate:
            collegamenti[partenza] = (arrivo, "serpente", random.choice(colori_serpenti))
            caselle_occupate.add(partenza)
            caselle_occupate.add(arrivo)
            serpenti_creati += 1

    return collegamenti

#Funzione per il podio (versione testuale usata dalla CLI)
def genera_podio(classifica: list) -> str:
    encoding = (getattr(sys.stdout, "encoding", None) or "").lower()
    if "utf" in encoding:
        simboli = [" 🥇 Primo posto", " 🥈 Secondo posto", " 🥉 Terzo posto"]
    else:
        simboli = [" [1°] Primo posto", " [2°] Secondo posto", " [3°] Terzo posto"]

    testo_podio = "\nClassifica Finale\n"
    for i, giocatore in enumerate(classifica[:3]):
        testo_podio += f"{simboli[i]}: {giocatore.get_nome()} (Casella {giocatore.get_posizione()})\n"
    if len(classifica) > 3:
        testo_podio += "Voi altri: i serpenti vi hanno preso!\n"
    return testo_podio
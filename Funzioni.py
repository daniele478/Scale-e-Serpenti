from Classi import Giocatore
import random
def genera_tabellone() -> dict:
    # Restituisce {casella_partenza: (casella_arrivo, tipo, colore)}.
    # ATTENZIONE per la grafica: il colore qui e' una STRINGA
    # ("Rossa", "Gialla", "Verde"), non una tupla RGB.
    # Il modulo grafico dovra' avere un dizionario di traduzione
    # stringa -> (R, G, B) per disegnare scale e serpenti.
    collegamenti = {}
    caselle_occupate = set()
    '''
    set qui crea un insieme vuoto 
    per evitare generazione sulla stessa casella
    '''
    configurazioni = [
        ("scala","Rossa",30,39,2),
        ("scala","Gialla",20,29,2),
        ("scala","Verde",10,19,2),
        ("serpente","Rosso",30,39,2),
        ("serpente","Gialla",20,29,2),
        ("serpente","Verde",10,19,2)
    ]

    for tipo, colore, delta_min, delta_max, quantita in configurazioni:
        for _ in range(quantita):
            generato = False
            while not generato:
                delta = random.randint(delta_min,delta_max)

                if tipo == "scala":
                    #niente serpenti su 100
                    #scale fino a 100
                    inizio = random.randint(2, 100-delta)
                    fine = inizio+delta
                else: #serpente
                    inizio = random.randint(1+delta, 99)
                    fine = inizio-delta
                if inizio not in caselle_occupate:
                    caselle_occupate.add(inizio)
                    collegamenti[inizio] = (fine,tipo,colore)
                    generato = True
    return collegamenti

#Funzione per restituire la posizione
def estrai_posizione(giocatore:Giocatore) -> int:
    return giocatore.get_posizione()

#Funzione per il podio (versione testuale usata dalla CLI)
def genera_podio(classifica: list) -> str:
    # Solo i primi 3 salgono sul podio: gli altri non vengono nominati.
    # (La grafica ha la sua resa con i cubi in Grafica.disegna_podio,
    # ma la regola "top 3 + altri" deve restare identica in entrambe.)
    simboli = [" 🥇 Primo posto", " 🥈 Secondo posto", " 🥉 Terzo posto"]
    testo_podio = "\nClassifica Finale\n"
    for i, giocatore in enumerate(classifica[:3]):
        testo_podio += f"{simboli[i]}: {giocatore.get_nome()} (Casella {giocatore.get_posizione()})\n"
    if len(classifica) > 3:
        testo_podio += "Voi altri: i serpenti vi hanno preso!\n"
    return testo_podio
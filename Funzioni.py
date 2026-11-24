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

#Funzione per il podio
def genera_podio(classifica: list) -> str:
    simboli = [" 🥇 Primo posto", " 🥈 Secondo posto", " 🥉 Terzo posto", " Quarto posto"]
    testo_podio = "\nClassifica Finale\n"
    for i, giocatore in enumerate(classifica):
        testo_podio += f"{simboli[i]}: {giocatore.get_nome()} (Casella {giocatore.get_posizione()})\n"
    return testo_podio
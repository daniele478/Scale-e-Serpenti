import time
import random
from Classi import Dado, Tabellone, Partita, GiocatoreUmano, GiocatoreBot
from Funzioni import genera_tabellone, estrai_posizione, genera_podio

#n = numero colori casuali      :int = tipo di dato atteso
def genera_colori(n: int) -> list[tuple[int,int,int]]:
    colori = []
    # uso _ perche' così cicla ma non devo inizializzare 
    # una variabile i che rimarrebe inutilizata
    for _ in range(n):
        colore = (
            random.randint(50,255),
            random.randint(50,255),
            random.randint(50,255)
        )
        colori.append(colore)
    return colori

def configura_partita() -> Partita:
    print("\nBenvenuto in Scale e Serpenti\n")
    #Numero di giocatori
    tot_giocatori = 0
    while tot_giocatori < 2 or tot_giocatori > 26:
        try:
            tot_giocatori = int(input("Inserisci il numero di giocatori (2-26): "))
            if tot_giocatori < 2 or tot_giocatori > 26:
                print("Numero di giocatori non valido. Inserisci un numero tra 2 e 26.")
        except ValueError:
            print("Input non valido. Inserisci un numero intero tra 2 e 26.")
    #Numero umani
    umani = -1
    while umani < 1 or umani > tot_giocatori:
        try:
            umani = int(input(f"Inserisci il numero di giocatori umani (1-{tot_giocatori}): "))
            if umani < 1 or umani > tot_giocatori:
                print(f"Numero di giocatori umani non valido. Inserisci un numero tra 1 e {tot_giocatori}.")
        except ValueError:
            print("Input non valido. Inserisci un numero intero.")
    
    num_bot = tot_giocatori - umani
    giocatori = []
    colori_disponibili = genera_colori(tot_giocatori)

    #Creazione giocatori umani
    for i in range(umani):
        nome = input (f"Inserisci il nome del Giocatore {i+1}: ").strip()
        #.strip rimuove gli spazi iniziali e finali
        if not nome:
            nome = f"Giocatore_{i+1}"
        colore = colori_disponibili[len(giocatori)]
        giocatori.append(GiocatoreUmano(nome=nome, colore=colore))

    #Creazione Giocatori Bot
    for i in range(num_bot):
        nome_bot = f"bot{i+1}"
        colore = colori_disponibili[len(giocatori)]
        giocatori.append(GiocatoreBot(nome=nome_bot, colore=colore))
        print(f"Creato automaticamente {nome_bot}.")

    #Inizializzazione tabelloe + dado
    dati_tabellone = genera_tabellone()
    tabellone = Tabellone(dati_tabellone)
    dado = Dado()
    return Partita(giocatori,tabellone,dado)
def main():
    gioca = True
    while gioca:
        partita = configura_partita()
        print("\nIniziano i giochi, attenzione ai seprenti\n")

        #Ciclo per giocare
        while not partita.is_finita():
            giocatore = partita.get_giocatore_corrente()
            print(f"\nTurno di {giocatore.get_nome()} (Casella attuale:{giocatore.get_posizione()})")
            if not giocatore.is_bot():
                input("Premi [INVIO] per tirare il dado...")
            else:
                print("Il Bot sta tirando...")
                time.sleep(3)
            #Risultato
            esito = partita.esegui_turno()
            print(f"Il tuo tiro è da: {esito}")
            input("Premi [INVIO] per andare avanti...")
        classifica = partita.calcola_classifica()
        print(genera_podio(classifica))

        #Mostra classifica
        print("Ti va di giocare ancora?")
        print("1. Sì, sconfiggerò i serpenti")
        print("2. Voglio scappare dai serpenti")
        scelta = ""
        while scelta not in ["1","2"]:
            scelta = input("Inserisci la tua scelta: ").strip()
            if scelta == "1":
                print("Saliamo su quelle scale")
            else:
                print("Un serpente ti ha inghiottito")
                gioca = False
main()
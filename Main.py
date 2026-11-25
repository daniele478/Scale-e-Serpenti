import time
import random
from Classi import Dado, Tabellone, Partita, GiocatoreUmano, GiocatoreBot
from Funzioni import genera_tabellone, genera_podio
from ReportPDF import genera_report_pdf
from Grafica import avvia_partita_grafica

from Database import(
    crea_tabelle,
    registra_utente,
    verifica_login,
    aggiorna_statistiche_vittoria,
    aggiorna_statistiche_sconfitta,
    salva_eventi,
    ottieni_highscore
)
#n = numero colori casuali      :int = tipo di dato atteso
def genera_colori(n: int) -> list[tuple[int,int,int]]:
    colori = []
    '''
    uso _ perche' così cicla ma non devo inizializzare 
    una variabile i che rimarrebe inutilizata
    '''
    for _ in range(n):
        colore = (
            random.randint(50,255),
            random.randint(50,255),
            random.randint(50,255)
        )
        colori.append(colore)
    return colori

def mostra_highscore() -> None:
    #Recupera i dati dal db e li stampa formato tabella
    print("\n" + "=" * 55)
    print(" CLASSIFICA ")
    print("=" * 55)

    classifica = ottieni_highscore()
    if not classifica:
        print("Nessun utente registrato nel database")
    else:
        print(f"{'UTENTE':<15} | {'GIOCATE':<8} | {'VINTE':<8} | {'RECORD TURNI':<12}")
        print("-" * 55)
        # <x serve ad allineare il testo a sx riservando x caratteri
        for utente, giocate, vinte, record in classifica:
        #spacchettiamo ogni tupla restituita dal db nelle 4 variabili
            testo_record = str(record) if record is not None else "-"
            print(f"{utente:<15} | {giocate:<8} | {vinte:<8} | {testo_record:<12}")
    print("=" * 55 + "\n")

def autentica_giocatore_umano(numero_giocatore: int, utenti_loggati: list[str]) -> str:
    """
    Gestisce il ciclo di login o registrazione per i player.
    Restituisce username quando l'autenticazione va
    """
    while True:
        print(f"\n--- Autenticazione Player {numero_giocatore} ---")
        print("1. Login")
        print("2. Registrati")
        scelta = input("Scegli 1 o 2: ").strip()
        if scelta not in ["1", "2"]:
            print("Scelta non valida. Digita 1(Login) o 2(Registrati)")
            continue #interrompe l'iterazione se si sbaglia a digitare
        username = input("Inserisci Username: ").strip()
        password = input("Inserisci Password: ").strip()

        if not username or not password:
            print("Username e password non possono essere vuoti.")
            continue
        #Controllo 1: vuoti

        if username in utenti_loggati:
            print(f"L'utente '{username}' ha gia' effettutato il login")
            continue
        #Controllo 2: duplice accesso

        if scelta == "1":
            if verifica_login(username, password):
                print(f"Accesso effettuato. Bentornato/a {username}")
                return username
            else: 
                print ("Credenziali errate o utente inesistente")
        #Verifica se username e password corrispondono
        
        elif scelta == "2":
            if registra_utente(username, password):
                print(f"Registrazione completata. Benvenuto/a {username}")
                return username
            else:
                print(f"Username gia' in uso")
        #Verifica se l'username e' libero

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
    utenti_loggati = [] #lista username entrati in partita 
    #Autentica e crea giocatori umani
    for i in range(umani):
        username_autenticato = autentica_giocatore_umano(i + 1, utenti_loggati)
        utenti_loggati.append(username_autenticato)

        colore = colori_disponibili[len(giocatori)]
        giocatori.append(GiocatoreUmano(nome=username_autenticato, colore=colore))

    #Creazione Giocatori Bot
    for i in range(num_bot):
        nome_bot = f"bot{i+1}"
        colore = colori_disponibili[len(giocatori)]
        giocatori.append(GiocatoreBot(nome=nome_bot, colore=colore))
        print(f"Creato automaticamente {nome_bot}.")

    #Inizializzazione tabellone + dado
    dati_tabellone = genera_tabellone()
    tabellone = Tabellone(dati_tabellone)
    dado = Dado()
    return Partita(giocatori,tabellone,dado)

def main():
    crea_tabelle()
    #crea file scale_serpenti.db e relative tabelle nel caso non esistono ancora
    print("  BENVENUTO IN SCALE E SERPENTI  ")
    programma_attivo = True
    while programma_attivo:
        print("\n MENU PRINCIPALE:")
        print("1. Nuova Partita (Login e Gioca)")
        print("2. Visualizza Classifica")
        print("3. Esci dal gioco")

        scelta_menu = input("Seleziona 1-3:").strip()
        if scelta_menu == "2":
            mostra_highscore()
            continue
        elif scelta_menu == "3":
            print("Scappi gia'? I serpenti sentiranno la tua mancanza. A presto!")
            programma_attivo = False
            continue
        elif scelta_menu != "1":
            print("Opzione inesistente")
            continue
        
        #AVVIO PARTITA
        partita = configura_partita()

        modalita = ""
        while modalita not in ["1", "2"]:
            modalita = input("\nScegli modalita di gioco (1 = Testuale CLI, 2 = Grafica): ").strip()
            if modalita not in ["1", "2"]:
                print("Scelta non valida. Digita 1 o 2.")

        print("\nIniziano i giochi, attenzione ai serpenti!\n")

        if modalita == "2":
            turni_giocati = avvia_partita_grafica(partita)
        else:
            turni_giocati = 0
            while not partita.is_finita():
                giocatore = partita.get_giocatore_corrente()
                print(f"\nTurno di {giocatore.get_nome()} (Casella attuale: {giocatore.get_posizione()})")

                if not giocatore.is_bot():
                    input("Premi [INVIO] per sfidare la sorte...")
                else:
                    print(f"{giocatore.get_nome()} sta tirando...")
                    time.sleep(1)

                esito = partita.esegui_turno()
                turni_giocati += 1
                print(f"Esito: {esito}")

        #FINE PARTITA
        classifica = partita.calcola_classifica()
        print(genera_podio(classifica))
        vincitore = partita.get_vincitore()

        #Aggiornamento statistiche 
        for giocatore in classifica:
            if not giocatore.is_bot():
                if giocatore == vincitore:
                    aggiorna_statistiche_vittoria(giocatore.get_nome(), turni_giocati)
                else:
                    aggiorna_statistiche_sconfitta(giocatore.get_nome())
        registro = partita.get_registro_eventi()
        salva_eventi(registro)
        print("\nDb Aggiornato: Applausi per il vincitore!!")

        #Esportazione report PDF di fine partita
        percorso_pdf = genera_report_pdf(classifica, registro, turni_giocati)
        print(f"\nReport PDF salvato in: {percorso_pdf}")

        mostra_highscore()

main()
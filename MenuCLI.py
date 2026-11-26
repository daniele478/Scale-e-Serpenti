import random
from Classi import Dado, Tabellone, Partita, GiocatoreUmano, GiocatoreBot
from Funzioni import genera_collegamenti_casuali
from Database import (
    valida_credenziali,
    registra_utente,
    verifica_login,
    ottieni_highscore,
    ottieni_storico_partite,
    ottieni_eventi_partita,
)
 
def genera_colori(n: int) -> list[tuple[int, int, int]]:
    """Genera una lista di n colori RGB casuali ben visibili sul tabellone."""
    colori = []
    for _ in range(n):
        colore = (
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255),
        )
        colori.append(colore)
    return colori


def mostra_highscore() -> None:
    """Recupera i dati dal database e li stampa in formato tabella."""
    print("\n" + "=" * 55)
    print(" CLASSIFICA ")
    print("=" * 55)

    # Considera solo gli utenti che hanno giocato almeno una partita
    classifica = [riga for riga in ottieni_highscore() if riga[1] > 0]

    if not classifica:
        print("Nessuna partita ancora registrata in classifica.")
    else:
        print(f"{'UTENTE':<15} | {'GIOCATE':<8} | {'VINTE':<8} | {'RECORD GIRI':<12}")
        print("-" * 55)
        for utente, giocate, vinte, record in classifica:
            testo_record = str(record) if (vinte > 0 and record is not None) else "-"
            print(f"{utente:<15} | {giocate:<8} | {vinte:<8} | {testo_record:<12}")
    print("=" * 55 + "\n")

def mostra_storico_partite() -> None:
    """Mostra l'elenco delle partite concluse e permette di ispezionare gli eventi di una partita."""
    while True:
        partite = ottieni_storico_partite()
        print("\n" + "=" * 65)
        print(" STORICO PARTITE ")
        print("=" * 65)

        if not partite:
            print("Nessuna partita ancora registrata.")
            print("=" * 65 + "\n")
            return

        print(f"{'ID':<5} | {'DATA E ORA':<20} | {'VINCITORE':<15} | {'GIRI':<6}")
        print("-" * 65)
        id_validi = set()
        for pid, data_ora, vincitore, turni in partite:
            id_validi.add(pid)
            print(f"{pid:<5} | {data_ora:<20} | {vincitore:<15} | {turni:<6}")
        print("=" * 65)

        scelta = input("Inserisci ID partita per vedere i dettagli (oppure Invio per tornare): ").strip()
        if not scelta:
            return
        if len(scelta) > 8 or not scelta.isdigit() or int(scelta) not in id_validi:
            print("ID partita non valido.")
            continue

        pid_scelto = int(scelta)
        eventi = ottieni_eventi_partita(pid_scelto)
        print(f"\n--- Registro Eventi Partita #{pid_scelto} ---")
        if not eventi:
            print("Nessun evento registrato per questa partita.")
        else:
            for indice, giro, descrizione in eventi:
                print(f"[{indice:03d}] Giro {giro}: {descrizione}")
        input("\nPremi Invio per tornare allo storico...")

def autentica_giocatore_umano(numero_giocatore: int, utenti_loggati: list[str]) -> str:
    """
    Gestisce il ciclo di login o registrazione per un player umano.
    Restituisce lo username canonico quando l'autenticazione riesce.
    """
    while True:
        print(f"\n--- Autenticazione Player {numero_giocatore} ---")
        print("1. Login")
        print("2. Registrati")
        scelta = input("Scegli 1 o 2: ").strip()
        if scelta not in ["1", "2"]:
            print("Scelta non valida. Digita 1 (Login) o 2 (Registrati).")
            continue

        raw_username = input("Inserisci Username (3-16 caratteri, lettere/numeri/_/-): ")
        raw_password = input("Inserisci Password (4-64 caratteri): ")

        # Controllo 1: formato, lunghezza e caratteri ammessi
        try:
            username, password = valida_credenziali(raw_username, raw_password)
        except ValueError as e:
            print(f"Errore: {e}")
            continue

        # Controllo 2: duplice accesso nella stessa partita (case-insensitive)
        if any(u.lower() == username.lower() for u in utenti_loggati):
            print(f"L'utente '{username}' ha gia' effettuato il login.")
            continue

        if scelta == "1":
            username_canonico = verifica_login(username, password)
            if username_canonico:
                print(f"Accesso effettuato. Bentornato/a {username_canonico}!")
                return username_canonico
            else:
                print("Credenziali errate o utente inesistente.")

        elif scelta == "2":
            if registra_utente(username, password):
                print(f"Registrazione completata. Benvenuto/a {username}!")
                return username
            else:
                print(f"Username '{username}' gia' in uso (anche con maiuscole/minuscole diverse).")


def configura_partita() -> Partita:
    """Chiede numero di giocatori/umani, autentica i player e crea la Partita."""
    print("\nBenvenuto in Scale e Serpenti\n")

    tot_giocatori = 0
    while tot_giocatori < 2 or tot_giocatori > 26:
        valore = input("Inserisci il numero di giocatori (2-26): ").strip()
        if len(valore) > 5:
            print("Input non valido. Inserisci un numero intero tra 2 e 26.")
            continue
        try:
            tot_giocatori = int(valore)
            if tot_giocatori < 2 or tot_giocatori > 26:
                print("Numero di giocatori non valido. Inserisci un numero tra 2 e 26.")
        except ValueError:
            print("Input non valido. Inserisci un numero intero tra 2 e 26.")

    umani = -1
    while umani < 1 or umani > tot_giocatori:
        valore = input(f"Inserisci il numero di giocatori umani (1-{tot_giocatori}): ").strip()
        if len(valore) > 5:
            print("Input non valido. Inserisci un numero intero.")
            continue
        try:
            umani = int(valore)
            if umani < 1 or umani > tot_giocatori:
                print(f"Numero di giocatori umani non valido. Inserisci un numero tra 1 e {tot_giocatori}.")
        except ValueError:
            print("Input non valido. Inserisci un numero intero.")

    num_bot = tot_giocatori - umani
    giocatori = []
    colori_disponibili = genera_colori(tot_giocatori)
    utenti_loggati = []

    for i in range(umani):
        username_autenticato = autentica_giocatore_umano(i + 1, utenti_loggati)
        utenti_loggati.append(username_autenticato)
        colore = colori_disponibili[len(giocatori)]
        giocatori.append(GiocatoreUmano(nome=username_autenticato, colore=colore))

    for i in range(num_bot):
        nome_bot = f"bot{i+1}"
        colore = colori_disponibili[len(giocatori)]
        giocatori.append(GiocatoreBot(nome=nome_bot, colore=colore))
        print(f"Creato automaticamente {nome_bot}.")

    dati_tabellone = genera_collegamenti_casuali()
    tabellone = Tabellone(dati_tabellone)
    dado = Dado()
    return Partita(giocatori, tabellone, dado)

def chiedi_azione_menu() -> str:
    """Mostra il menu principale e restituisce la scelta valida ('1', '2', '3' o '4')."""
    while True:
        print("\n MENU PRINCIPALE:")
        print("1. Nuova Partita (Login e Gioca)")
        print("2. Visualizza Classifica")
        print("3. Storico Partite")
        print("4. Esci dal gioco")
        scelta = input("Seleziona 1-4: ").strip()
        if scelta in ["1", "2", "3", "4"]:
            return scelta
        print("Opzione inesistente.")

def chiedi_modalita_gioco() -> str:
    """Chiede all'utente se giocare in CLI ('1') o con interfaccia grafica ('2')."""
    modalita = ""
    while modalita not in ["1", "2"]:
        modalita = input("\nScegli modalita di gioco (1 = Testuale CLI, 2 = Grafica): ").strip()
        if modalita not in ["1", "2"]:
            print("Scelta non valida. Digita 1 o 2.")
    return modalita
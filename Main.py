import time
import sys
from Funzioni import genera_podio
from ReportPDF import genera_report_pdf
from Database import (
    crea_tabelle,
    aggiorna_statistiche_vittoria,
    aggiorna_statistiche_sconfitta,
    salva_eventi,
)
from MenuCLI import (
    mostra_highscore,
    mostra_storico_partite,
    configura_partita,
    chiedi_azione_menu,
    chiedi_modalita_gioco,
)

#CONFIGURAZIONE TERMINALE
#forza UTF-8 su stdout e stderr per evitare errori di stampa con simboli/emoji 
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Modalita' di gioco testuale CLI e chiusura partita
def gioca_partita_cli(partita) -> None:
    """Esegue il ciclo dei turni in modalita' testuale da terminale."""
    while not partita.is_finita():
        giocatore = partita.get_giocatore_corrente()
        print(
            f"\nGiro {partita.get_giri_completati() + 1} - "
            f"Turno di {giocatore.get_nome()} (Casella attuale: {giocatore.get_posizione()})"
        )
        # Attende conferma manuale per gli utenti reali, simula attesa per i bot
        if not giocatore.is_bot():
            input("Premi [INVIO] per sfidare la sorte...")
        else:
            print(f"{giocatore.get_nome()} sta tirando...")
            time.sleep(1)

        esito = partita.esegui_turno()
        print(f"Esito: {esito}")


def finalizza_partita(partita) -> None:
    """
    Gestisce tutte le operazioni post-partita:
    1. Calcola e stampa podio finale
    2. Aggiorna le statistiche dei giocatori umani nel database
    3. Salva lo storico della partita e i singoli eventi nel DB
    4. Genera il report PDF
    """
    # Il record usa il giro reale della vittoria, non i giri completi (la vittoria può arrivare a metà giro)
    giro_vittoria = partita.get_giro_vittoria() or partita.get_giri_completati()
    classifica = partita.calcola_classifica()
    print(genera_podio(classifica))
    vincitore = partita.get_vincitore()

    # I bot non hanno un account registrato: aggiorna solo gli umani
    for giocatore in classifica:
        if not giocatore.is_bot():
            if giocatore == vincitore:
                aggiorna_statistiche_vittoria(giocatore.get_nome(), giro_vittoria)
            else:
                aggiorna_statistiche_sconfitta(giocatore.get_nome())
    #Salva riepilogo partita ed eventi in SQLite
    registro = partita.get_registro_eventi()
    salva_eventi(partita.get_registro_eventi_dettagliato(), vincitore.get_nome(), giro_vittoria)
    print("\nDb Aggiornato: Applausi per il vincitore!!")
    #Esporta il verbale in PDF
    try:
        percorso_pdf = genera_report_pdf(classifica, registro, giro_vittoria)
        print(f"\nReport PDF salvato in: {percorso_pdf}")
    except Exception as e:
        print(f"\nErrore durante la generazione del report PDF: {e}")

    mostra_highscore()

#Menu principale
def main() -> None:
    """Inizializza il database e gestisce il menu principale"""
    crea_tabelle()
    print("  BENVENUTO IN SCALE E SERPENTI  ")

    while True:
        scelta_menu = chiedi_azione_menu()
        if scelta_menu == "2":
            mostra_highscore()
            continue
        if scelta_menu == "3":
            mostra_storico_partite()
            continue
        if scelta_menu == "4":
            print("Scappi gia'? I serpenti sentiranno la tua mancanza. A presto!")
            break

        #Configurazione giocatori/tabellone e scelta interfaccia
        partita = configura_partita()
        modalita = chiedi_modalita_gioco()
        print("\nIniziano i giochi, attenzione ai serpenti!\n")
        #Impostazione grafica: consente l'esecuzione in CLI anche su ambienti in cui pygame non e' installato
        if modalita == "2":
            try:
                from Grafica import avvia_partita_grafica
                avvia_partita_grafica(partita)
            except ImportError:
                print("\nErrore: libreria 'pygame' non installata. Avvio in modalita' CLI...")
                modalita = "1"
            except Exception as errore:
                #Display o risorse grafiche non disponibili: ripiega sulla CLI
                print(f"\nErrore grafico ({errore}). Avvio in modalita' CLI...")
                modalita = "1"

        if modalita == "1":
            gioca_partita_cli(partita)

        # Se l'utente ha chiuso la finestra o interrotto prima della fine
        # evita di salvare partite incomplete o generare report
        if not partita.is_finita():
            print("\nPartita interrotta prima del termine: nessun report generato.")
            continue

        finalizza_partita(partita)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        # gestisce l'interruzione da tastiera ( Ctrl+C / Ctrl + D)
        print("\n\nUscita forzata rilevata. Partita interrotta, a presto!")
import time
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
    configura_partita,
    chiedi_azione_menu,
    chiedi_modalita_gioco,
)


def gioca_partita_cli(partita) -> None:
    """Esegue il ciclo dei turni in modalita' testuale da terminale."""
    while not partita.is_finita():
        giocatore = partita.get_giocatore_corrente()
        print(
            f"\nGiro {partita.get_giri_completati() + 1} - "
            f"Turno di {giocatore.get_nome()} (Casella attuale: {giocatore.get_posizione()})"
        )

        if not giocatore.is_bot():
            input("Premi [INVIO] per sfidare la sorte...")
        else:
            print(f"{giocatore.get_nome()} sta tirando...")
            time.sleep(1)

        esito = partita.esegui_turno()
        print(f"Esito: {esito}")


def finalizza_partita(partita) -> None:
    """Mostra il podio, aggiorna le statistiche nel DB e genera il report PDF."""
    giri_giocati = partita.get_giri_completati()
    classifica = partita.calcola_classifica()
    print(genera_podio(classifica))
    vincitore = partita.get_vincitore()

    for giocatore in classifica:
        if not giocatore.is_bot():
            if giocatore == vincitore:
                aggiorna_statistiche_vittoria(giocatore.get_nome(), giri_giocati)
            else:
                aggiorna_statistiche_sconfitta(giocatore.get_nome())

    registro = partita.get_registro_eventi()
    salva_eventi(registro, vincitore.get_nome(), giri_giocati)
    print("\nDb Aggiornato: Applausi per il vincitore!!")

    try:
        percorso_pdf = genera_report_pdf(classifica, registro, giri_giocati)
        print(f"\nReport PDF salvato in: {percorso_pdf}")
    except Exception as e:
        print(f"\nErrore durante la generazione del report PDF: {e}")

    mostra_highscore()


def main() -> None:
    crea_tabelle()
    print("  BENVENUTO IN SCALE E SERPENTI  ")

    while True:
        scelta_menu = chiedi_azione_menu()
        if scelta_menu == "2":
            mostra_highscore()
            continue
        if scelta_menu == "3":
            print("Scappi gia'? I serpenti sentiranno la tua mancanza. A presto!")
            break

        partita = configura_partita()
        modalita = chiedi_modalita_gioco()
        print("\nIniziano i giochi, attenzione ai serpenti!\n")

        if modalita == "2":
            try:
                from Grafica import avvia_partita_grafica
                avvia_partita_grafica(partita)
            except ImportError:
                print("\nErrore: libreria 'pygame' non installata. Avvio in modalita' CLI...")
                modalita = "1"

        if modalita == "1":
            gioca_partita_cli(partita)

        if not partita.is_finita():
            print("\nPartita interrotta prima del termine: nessun report generato.")
            continue

        finalizza_partita(partita)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nUscita forzata rilevata. Partita interrotta, a presto!")
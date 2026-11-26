import os
import unicodedata              #serve a ispezionare e normalizzare i caratteri Unicode
from datetime import datetime   #importa la classe datetime per leggere la data e l'ora

from fpdf import FPDF           #importa la classe che rappresenta il PDF
from fpdf.fonts import FontFace #importa la classe per personalizzare l'aspetto grafico

CARTELLA_REPORT = "report_partite" #nome cartella dove viene salvato

#Dizionario per sostituire caratteri complessi
SOSTITUZIONI = {
    "\u2018": "'", "\u2019": "'",   # apici singoli
    "\u201c": '"', "\u201d": '"',   # virgolette
    "\u2013": "-", "\u2014": "-",   # trattini
    "\u2026": "...",                # puntini di sospensione
}

def pulisci_testo(testo) -> str:
    """
    Rende una stringa compatibile con i font di fpdf2.
    - à -> a
    - elimina cio' che non è rappresentabile
    """
    if testo is None:
        return "" #restituisce stringa vuota
    testo = str(testo)
    for originale, sostituto in SOSTITUZIONI.items():
        testo = testo.replace(originale, sostituto)                     #scorre e rimpiazza
    testo = unicodedata.normalize("NFKD", testo)                        #scompone gli accenti
    testo = "".join(c for c in testo if not unicodedata.combining(c)) 
    return testo.encode("latin-1", "ignore").decode("latin-1")          #setaccia la parola e toglie il carattere. [c][i][t][t][a]['] -> butta '
                                                                        #ignore elimina emoji e simboli non supportati

def genera_report_pdf(classifica: list, registro_eventi: list[str], giri_totali: int) -> str:
    """
    Genera il report PDF di fine partita. 
    Restituisce il percorso assoluto del file salvato.
    """
    # Cartella di destinazione (sempre accanto a questo file)
    cartella = os.path.join(os.path.dirname(os.path.abspath(__file__)), CARTELLA_REPORT)
    os.makedirs(cartella, exist_ok=True)

    # Nome basato su timestamp (con contatore per evitare sovrascritture)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    percorso = os.path.join(cartella, f"report_partita_{timestamp}.pdf")
    contatore = 1
    while os.path.exists(percorso):
        percorso = os.path.join(cartella, f"report_partita_{timestamp}_{contatore}.pdf")
        contatore += 1

    # Documento
    pdf = FPDF(orientation = "P", unit = "mm", format = "A4")
    pdf.set_auto_page_break(auto=True, margin=15) #salto pagina automatico
    pdf.set_title("Scale e Serpenti - Report partita")
    pdf.add_page()

    # INTESTAZIONE
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "SCALE E SERPENTI", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    data_ora = datetime.now().strftime("%d/%m/%Y alle %H:%M")
    pdf.cell(0, 7, f"Report partita del {data_ora}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, f"Giri totali giocati: {giri_totali}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # CLASSIFICA FINALE
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "CLASSIFICA FINALE", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    stile_vincitore = FontFace(fill_color=(214, 245, 214), emphasis="BOLD") #riga verde per chi ha raggiunto la casella 100
    with pdf.table(
        col_widths=(25, 65, 35, 35),
        text_align="CENTER",
        headings_style=FontFace(emphasis="BOLD", fill_color=(230, 230, 230)),
        line_height=7,
    ) as tabella:
        intestazione = tabella.row()
        for titolo in ("Posizione", "Nome", "Tipologia", "Casella finale"):
            intestazione.cell(titolo)

        for posizione, giocatore in enumerate(classifica, start=1):
            stile = stile_vincitore if giocatore.get_posizione() == 100 else None
            riga = tabella.row()
            riga.cell(f"{posizione}°", style=stile)
            riga.cell(pulisci_testo(giocatore.get_nome()), align="LEFT", style=stile)
            riga.cell("Bot" if giocatore.is_bot() else "Umano", style=stile)
            riga.cell(str(giocatore.get_posizione()), style=stile)

    pdf.ln(8)

    # REGISTRO CRONOLOGICO EVENTI
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "REGISTRO CRONOLOGICO EVENTI", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    if not registro_eventi:
        pdf.multi_cell(0, 6, "Nessun evento registrato.", new_x="LMARGIN", new_y="NEXT")
    else:
        for numero, evento in enumerate(registro_eventi, start=1):
            testo = pulisci_testo(evento)
            pdf.multi_cell(0, 6, f"{numero}. {testo}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

    # Salvataggio su disco
    pdf.output(percorso)
    return percorso

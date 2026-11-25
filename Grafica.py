import math
import random
import pygame

# CONFIGURAZIONE
MARGINE = 25
DIM_CELLA = 60
DIM_TABELLONE = DIM_CELLA *10   
AREA_PARTENZA = 55
LARGHEZZA_PANNELLO = 340
LARGHEZZA_FINESTRA = MARGINE * 3 + DIM_TABELLONE + LARGHEZZA_PANNELLO
ALTEZZA_FINESTRA = MARGINE * 2 + DIM_TABELLONE + AREA_PARTENZA

FPS = 60

# Colori
COLORE_SFONDO = (238,242,246)
COLORE_PANNELLO = (255,255,255)
COLORE_BORDO = (170,182,195)
COLORE_TESTO = (30,38,48)
COLORE_TESTO_TENUE = (100,112,125)          #INFO SECONDARIE
COLORE_CELLA_CHIARA = (255,255,255)
COLORE_CELLA_SCURA = (224,235,247) 
COLORE_BOTTONE = (41,128,185)
COLORE_BOTTONE_CLICCABILE = (31,97,141)     
COLORE_BOTTONE_DISABILITATO = (165,175,185) #NON CLICCABILE

# Mappa colori
MAPPA_COLORI ={
    "rosso": (220,53,69),
    "rossa": (220,53,69),
    "verde": (40,167,69),
    "blu": (0,123,255),
    "giallo":(235,180,15),
    "gialla":(235,180,15),
    "arancione": (243, 156, 18),
    "viola": (142,68,173),
    "ciano": (23,162,184),
    "marrone": (139, 90, 43),
    "rosa": (232, 62, 140),
}

def traduci_colore(nome_colore, default=(100,100,100)) -> tuple[int,int,int]:
    #Converte una stringa colore in una tupla RGB valida per Pygame
    if isinstance(nome_colore, (tuple,list)) and len(nome_colore) >= 3:
        return tuple(nome_colore[:3])
    if isinstance(nome_colore,str):
        chiave = nome_colore.strip().lower()
        if chiave in MAPPA_COLORI:
            return MAPPA_COLORI[chiave]
        #Fallback per i plurali/femminili non presenti nella mappa (es. "Rossa")
        if chiave.endswith("a") and chiave[:-1] + "o" in MAPPA_COLORI:
            return MAPPA_COLORI[chiave[:-1] + "o"]
        return default
    return default

#LETTURA DELLO STATO DELLA PARTITA
#La classe Partita (Classi.py) espone lo stato tramite getter, mentre gli
#oggetti interni restano negli attributi privati (_tabellone, _giocatori, _dado).
#Questi helper provano prima il getter pubblico e poi l'attributo privato,
#cosi' la grafica non dipende da un nome specifico e non va in AttributeError.
def _risolvi_risorsa(oggetto, nomi_getter, nomi_attributi, etichetta):
    for nome in nomi_getter:
        metodo = getattr(oggetto, nome, None)
        if callable(metodo):
            return metodo()
    for nome in nomi_attributi:
        valore = getattr(oggetto, nome, None)
        if valore is not None:
            return valore
    raise AttributeError(
        f"Impossibile ottenere {etichetta} dalla partita: "
        f"mancano i getter {nomi_getter} e gli attributi {nomi_attributi}"
    )

def estrai_tabellone(partita):
    return _risolvi_risorsa(
        partita,
        ("get_tabellone",),
        ("tabellone", "_tabellone"),
        "il tabellone",
    )

def estrai_giocatori(partita) -> list:
    return _risolvi_risorsa(
        partita,
        ("get_giocatori",),
        ("giocatori", "_giocatori"),
        "la lista dei giocatori",
    )

def estrai_dado(partita):
    return _risolvi_risorsa(
        partita,
        ("get_dado",),
        ("dado", "_dado"),
        "il dado",
    )

def estrai_colore_giocatore(giocatore, default="blu"):
    #Giocatore espone il colore con get_colore(); "colore" non esiste
    getter = getattr(giocatore, "get_colore", None)
    if callable(getter):
        return getter()
    return getattr(giocatore, "colore", getattr(giocatore, "_colore", default))

def estrai_raggio_giocatore(giocatore):
    getter = getattr(giocatore, "get_raggio", None)
    if callable(getter):
        return getter()
    return getattr(giocatore, "_raggio", getattr(giocatore, "raggio", None))

#CONVERSIONE CASELLA -> PIXEL
def casella_a_pixel(n:int) -> tuple[int, int]:
    """
    Restituisce le cordinate (x,y) del centro della casella.
    Se n <= 0 restituisce il centro dell'area 'PARTENZA' sotto la casella n1.
    """
    if n <= 0:
        #Area di partenza
        x_start = MARGINE + DIM_CELLA * 1.5
        y_start = MARGINE + DIM_TABELLONE + AREA_PARTENZA // 2 + 4
        return int(x_start), int(y_start)

    n = min(100, n)             #limite massimo
    indice = n - 1              #0-99
    riga = indice // 10         #indice 0-9 = prima riga, 10-19 = seconda riga ...
    colonna = indice % 10   
    if riga % 2 == 1:           #riga dispari
        colonna = 9 - colonna   #la colonna si specchia (effetto del tabellone)

    x = MARGINE + colonna * DIM_CELLA + DIM_CELLA / 2   
    #parte dal margine, si sposta di tante celle (colonna*DIM_CELLA) + mezza cella per puntare al centro
    y = MARGINE + (9 - riga) * DIM_CELLA + DIM_CELLA / 2
    # in pygame l'asse cresce dall'alto 9-riga ribalta l'indice verticale
    return int(x), int (y)

#DISEGNO TABELLONE
def disegna_scala_o_serpente(superficie: pygame.Surface, p1: tuple[int, int], p2: tuple[int,int], tipo: str, rgb: tuple[int,int,int]):
    #Disegna scalao serpente
    x1, y1 = p1             #partenza
    x2, y2 = p2             #arrivo
    dx = x2 - x1            #orizzontale
    dy = y2 - y1            #verticale
    lunghezza = math.hypot(dx,dy)  #calcolo lunghezza della linea retta tra p1 e p2
    if lunghezza == 0:
        return              #se partenza = arrivo, esce

    nx = -dy /lunghezza
    ny = dx / lunghezza     #calcola il verso. serve per spostarsi a dx e sx
    tipo_norm = str(tipo).strip().lower() #normalizza la stringa in minusc e senza spazi
  
   #SCALA
    if "scala" in tipo_norm:
        spessore = 7
        #prima parte scala
        pygame.draw.line(superficie, rgb, (int(x1 - nx * spessore), int(y1 - ny * spessore)), (int(x2 - nx * spessore), int(y2 - ny * spessore)), 4)
        #seconda parte scala
        pygame.draw.line(superficie, rgb, (int(x1 + nx * spessore), int(y1 + ny * spessore)), (int(x2 + nx * spessore), int(y2 + ny * spessore)), 4)
        #calcola quanti pioli disegnare
        num_pioli = max(3, int(lunghezza // 20)) 
        for i in range(1, num_pioli):
            t = i / num_pioli #t=percentuale avanzamento lungo la scala da 0.0 a 1.0
            #calcola punto centrale del piolo
            px = x1 + dx * t
            py = y1 + dy * t
            #disegna il piolo trasversale che divide la scala
            pygame.draw.line(superficie, rgb, (int(px - nx * spessore), int(py - ny * spessore)), (int(px + nx * spessore), int(py + ny * spessore)), 3)

    #SERPENTE
    else:
        punti = []  #lista punti del corpo serpente
        passi = 24  #segmenti in cui dividere il serpente
        for i in range(passi +1):    #Genera i punti da 0 a 24
            t = i / passi 
            #Calcola lo spostamento laterale usando l'onda seno
            #Ampiezza massima ondulazione = 9 pixel
            # 1 - t * 0.4 riduce l'ondulazione man mano che si avvicina alla coda
            onda = math.sin(t * math.pi * 3) * 9 * (1 - t * 0.4)
            # Calcola le coordinate reali del punto spostandosi lungo la retta + l'ondulazione 
            punti.append((int(x1 + dx * t + nx * onda), int(y1 + dy * t + ny * onda)))
            #Disegna il serpente collegando i punti. 5 = spessore 
        pygame.draw.lines(superficie, rgb, False, punti, 5)
        #Disegna la testa
        pygame.draw.circle(superficie, rgb, (int(x1), int(y1)), 8)
        #Disegna un piccolo punto bianco in mezzo alla testa per differenziarla 
        pygame.draw.circle(superficie, (255, 255, 255), (int(x1), int(y1)), 3)

def crea_surface_tabellone(tabellone) -> pygame.Surface:
    """
    Pre-disegna il tabellone (griglia, numeri, area partenza, scale e serpi)
    su un'immagine. In questo modo non deve ridisegnare 100 caselle da zero,
    rendendo l'animazione più fluida. 
    """
    #Crea il foglio vuoto (surface)
    surf = pygame.Surface((MARGINE * 2 + DIM_TABELLONE, ALTEZZA_FINESTRA))
    surf.fill(COLORE_SFONDO) #Lo colora
    #Prepara i due font di sistema
    font_num = pygame.font.SysFont("Arial", 13, bold=True)
    font_label = pygame.font.SysFont("Arial", 14, bold=True)
    #GRIGLIA
    for n in range(1,101):
        #ricava coordinate del centro della casella
        cx, cy = casella_a_pixel(n) 
        #Crea il rettangolo della casella spostandosi dal centro verso l'angolo in alto a sx
        rect = pygame.Rect(cx - DIM_CELLA // 2, cy - DIM_CELLA // 2, DIM_CELLA, DIM_CELLA)
        #Calcola la riga per l'alternare i colori
        riga = (n - 1) // 10
        colore_cella = COLORE_CELLA_CHIARA if (n+riga) % 2 == 0 else COLORE_CELLA_SCURA
        #Disegna l'interno della casella
        pygame.draw.rect(surf, colore_cella, rect)
        #Disegna il bordo sottile attorno alla casella
        pygame.draw.rect(surf, COLORE_BORDO, rect, 1)
        #Trasforma il n della cella in immagine
        txt = font_num.render(str(n), True, COLORE_TESTO_TENUE)
        #Incolla il n nell'angolo in alto a sx della casella
        surf.blit(txt, (rect.x + 4, rect.y + 3))
    #AREA PARTENZA
    #Crea il rettangolo della PARTENZA
    rect_partenza = pygame.Rect(MARGINE, MARGINE + DIM_TABELLONE + 8, DIM_CELLA * 3, AREA_PARTENZA - 12)
    #Disegna sfondo bianco con angoli arrotondati
    pygame.draw.rect(surf, COLORE_PANNELLO, rect_partenza, border_radius=8)
    #Disegna bordo grigio-blu intorno a PARTENZA
    pygame.draw.rect(surf, COLORE_BORDO, rect_partenza, 2, border_radius=8)
    #Scrive l'etichetta "PARTENZA (0)" in alto a sinistra dentro il box
    txt_part = font_label.render("PARTENZA (0)", True, COLORE_TESTO_TENUE)
    surf.blit(txt_part, (rect_partenza.x + 8, rect_partenza.y + 4))
    #COLLEGAMENTI (SCALE E SERPENTI)
    #Chiede al tabellone il dizionario con scale e serpenti.
    #Tabellone lo espone con get_collegamenti(); se un domani cambiasse nome,
    #si usa come riserva l'attributo privato _collegamenti.
    getter_collegamenti = getattr(tabellone, "get_collegamenti", None)
    if callable(getter_collegamenti):
        collegamenti = getter_collegamenti()
    else:
        collegamenti = getattr(tabellone, "_collegamenti", {})
    if not collegamenti:
        return surf
    #Scorre ogni collegamento: {inizio: (fine, tipo, colore_nome)}
    for inizio, info in collegamenti.items():
        #Gestisce entrambi i formati in cui il tabellone può restituire i dati:
        #Caso A: tupla o lista (es. (38, "scala", "verde"))
        if isinstance(info, (tuple, list)) and len(info) >= 2:
            fine, tipo = info[0], info[1]
            nome_colore = info[2] if len(info) > 2 else "rosso"
        #Caso B: oggetto/dizionario con chiavi .fine, .tipo, .colore
        elif isinstance(info, dict):
            fine = info.get("fine", info.get("destinazione", inizio))
            tipo = info.get("tipo", "serpente")
            nome_colore = info.get("colore", "rosso")
        else:
            fine = getattr(info, "fine", getattr(info, "destinazione", inizio))
            tipo = getattr(info, "tipo", "serpente")
            nome_colore = getattr(info, "colore", "rosso")
        #Scarta le voci malformate senza interrompere il disegno dell'intero tabellone
        if not isinstance(inizio, int) or not isinstance(fine, int) or fine == inizio:
            continue
        tipo = str(tipo) if tipo is not None else "serpente"
        #Sceglie un colore di riserva (verde per le scale, rosso per i serpenti) se il nome colore non viene riconosciuto
        default_rgb = (40, 167, 69) if "scala" in tipo.lower() else (220, 53, 69)
        #Traduce il nome del colore nella tupla RGB corrispondente
        rgb = traduci_colore(nome_colore, default=default_rgb)

        #Chiama la funzione aiutante per disegnare la scala o il serpente tra i due centri
        disegna_scala_o_serpente(surf, casella_a_pixel(inizio), casella_a_pixel(fine), tipo, rgb)
    return surf

#DISEGNO PEDINE
def disegna_pedine(screen: pygame.Surface, partita):
    """
    Raggruppa i giocatori per posizione e li dispone in cerchio
    intorno al centro se condividono la stessa casella.
    """
    #Estra la lista giocatori (getter pubblico o attributo privato _giocatori)
    giocatori = estrai_giocatori(partita)
    #Crea diz vuoto che associa ogni casella alla lista dei giocatori presenti
    #es 0: [Giocatore1][Giocatore2][Giocatore3]
    gruppi: dict[int,list] = {}
    #Cicla su tutti i giocatori per raggrupparli in base alla loro casella attuale
    for g in giocatori:
        # setdefault crea una lista vuota se la casella non è ancora nel dizionario, poi aggiunge il giocatore
        gruppi.setdefault(g.get_posizione(), []).append(g)
    #Se ci sono più di 10 giocatori , rimpicciolisce le pedine 
    #in modo che entrino, anche nell'area Partenza all'inizio del gioco
    raggio_ridotto = 8 if len(giocatori) > 10 else 11
    #Cicla su ogni casella occupata e sulla lista dei giocatori che ci stanno sopra
    for pos, lista_g in gruppi.items():
        #Calcola le coordinate del centro esatto di quella casella
        cx, cy = casella_a_pixel(pos)        
        #Conta quanti giocatori condividono questa stessa casella
        tot = len(lista_g)
        #Cicla su ciascun giocatore del gruppo con il suo indice 'idx' (0, 1, 2...)
        for idx, giocatore in enumerate(lista_g):
            #Caso A: c'è un solo giocatore su questa casella
            if tot == 1:
                #Lo posiziona al centro in modo da non coprire il numerino in alto 
                ox, oy = 0, 4 if pos > 0 else 6
                #Caso B: ci sono 2 o più giocatori sulla stessa casella
            else:
                #Sceglie il raggio del cerchio su cui disporre le pedine:
                #13 px casella normale, 18 px nell'area Partenza
                raggio_orbita = 13 if pos > 0 else 18
                #Calcola l'angolo per dividere i 360° (2 * pi greco) in fette uguali tra tutti i giocatori
                angolo = (2 * math.pi * idx) / tot           
                #Converte l'angolo in spostamento orizzontale (coseno) e verticale (seno) rispetto al centro
                ox = math.cos(angolo) * raggio_orbita
                oy = math.sin(angolo) * raggio_orbita + (4 if pos > 0 else 6)
            #Somma lo spostamento (ox, oy) al centro della casella (cx, cy) e converte in numeri interi
            px, py = int(cx + ox), int(cy + oy)
            #Salva il raggio originale del giocatore
            #(Giocatore lo tiene in _raggio: l'attributo pubblico "raggio" non esiste)
            raggio_orig = estrai_raggio_giocatore(giocatore)
            nome_attr_raggio = "_raggio" if hasattr(giocatore, "_raggio") else "raggio"
            rimpicciolito = raggio_orig is not None and len(giocatori) > 10
            #Se ci sono più di 10 giocatori, imposta temporaneamente il raggio ridotto
            if rimpicciolito:
                setattr(giocatore, nome_attr_raggio, raggio_ridotto)
            #Raggio effettivo da usare se il giocatore non ha un proprio disegna()
            raggio_eff = raggio_ridotto if rimpicciolito else (raggio_orig or raggio_ridotto)

            #Se la classe Giocatore ha già il suo metodo disegna(), usa quello
            if hasattr(giocatore, "disegna"):
                giocatore.disegna(screen, px, py)
            #altrimenti disegna direttamente qui un cerchio colorato con un bordo nero sottile
            else:
                colore = traduci_colore(estrai_colore_giocatore(giocatore, default="blu"))
                pygame.draw.circle(screen, colore, (px, py), raggio_eff)
                pygame.draw.circle(screen, (20, 20, 20), (px, py), raggio_eff, 2)

            #Ripristina il raggio originale del giocatore per non alterare in modo permanente l'oggetto
            if raggio_orig is not None:
                setattr(giocatore, nome_attr_raggio, raggio_orig)

#DISEGNA DADO
def disegna_dado(screen: pygame.Surface, rect: pygame.Rect, valore: int, in_animazione: bool):
    #Disegna il dado con i pallini 1-6 
    colore_faccia = (255, 252, 235) if in_animazione else (255, 255, 255)
    #Disegna il corpo quadrato del dado con gli angoli arrotondati 
    pygame.draw.rect(screen, colore_faccia, rect, border_radius=12)
    #Disegna il bordo esterno scuro attorno al dado
    pygame.draw.rect(screen, COLORE_TESTO, rect, 3, border_radius=12)
    #Ricava le coordinate (cx, cy) del centro esatto del dado
    cx, cy = rect.center
    #Calcola la distanza dal centro per posizionare i pallini laterali = off/offset = scostamento
    off = rect.width // 4
    #Dizionario che mappa ogni faaccia alla lista delle coordinate (x,y) dei suoi pallini
    pallini = {
        #Faccia 1
        1: [(cx, cy)],
        #Faccia 2
        2: [(cx - off, cy - off), (cx + off, cy + off)],
        #Faccia 3
        3: [(cx - off, cy - off), (cx, cy), (cx + off, cy + off)],
        #Faccia 4
        4: [(cx - off, cy - off), (cx + off, cy - off), (cx - off, cy + off), (cx + off, cy + off)],
        #Faccia 5
        5: [(cx - off, cy - off), (cx + off, cy - off), (cx, cy), (cx - off, cy + off), (cx + off, cy + off)],
        #Faccia 6
        6: [(cx - off, cy - off), (cx + off, cy - off), (cx - off, cy), (cx + off, cy), (cx - off, cy + off), (cx + off, cy + off)],
    }
    #Controlla se il valore e' compreso tra 1 e 6
    if valore in pallini:
        #Disegna pallino rosso se il valore e' 1
        colore_pallino = (220, 53, 69) if valore == 1 else COLORE_TESTO
        raggio_pallino = 7 if valore == 1 else 5
        #Cicla su tutte le coppie di coordinate (px,py)
        for px, py in pallini[valore]:
            #Disegna ogni pallino
            pygame.draw.circle(screen, colore_pallino, (px, py), raggio_pallino)

def spezza_testo(testo: str, font: pygame.font.Font, max_larghezza: int) -> list[str]:
#Spezza una stringa lunga su più righe per adattarla alla larghezza del pannello
    #Rimuove eventuali caratteri speciali / emoji
    testo_pulito = testo.encode("latin-1", "ignore").decode("latin-1")
    #Divide la frase in una lista di singole parole
    #es "- Mario tira 4" -> ["-", "Mario", "tira", "4"]
    parole = testo_pulito.split()
    righe = []
    riga_corrente = ""  #Variabile d'appoggio
    #Cicla su ogni parola della lista
    for parola in parole:
        #Simula come verrebbe la riga
        prova = f"{riga_corrente} {parola}".strip()
        #Chiede al font: "Quanti pixel di larghezza occupa questa riga di prova?"
        if font.size(prova)[0] <= max_larghezza:
            #Se ci sta ancora dentro il pannello, conferma l'aggiunta della parola alla riga corrente
            riga_corrente = prova
        else:
            #Se aggiungendo questa parola si supererebbe il bordo destro:
            #Salva la riga costruita finora nella lista definitiva
            if riga_corrente:
                righe.append(riga_corrente)
            #Inizia una nuova riga a capo partendo proprio dalla parola che non ci stava
            riga_corrente = parola
    #aggiunge anche l'ultima riga rimasta in memoria
    if riga_corrente:
        righe.append(riga_corrente)
    #Restituisce la lista delle righe pronte
    return righe

def disegna_pannello(
    screen: pygame.Surface,
    partita,
    giocatore_turno,
    turni: int,
    valore_dado: int,
    stato: str,
    rect_pannello: pygame.Rect,
    rect_dado: pygame.Rect,
    rect_bottone: pygame.Rect,
    pos_mouse: tuple[int, int],
    classifica_finale: list = None,
): #Disegna l'intero pannello informativo sulla destra
    #SFONDO E BORDO PANNELLO
    #Disegna il rettangolo bianco di sfondo del pannello 
    pygame.draw.rect(screen, COLORE_PANNELLO, rect_pannello, border_radius=12)
    #Disegna il bordo grigio-blu esterno del pannello
    pygame.draw.rect(screen, COLORE_BORDO, rect_pannello, 2, border_radius=12)
    #Prepara i 4 font con dimensioni e stili diversi 
    font_titolo = pygame.font.SysFont("Arial", 20, bold=True)  #Titolo principale
    font_sub = pygame.font.SysFont("Arial", 15, bold=True)     #Sottotitoli, turno e testo pulsante
    font_testo = pygame.font.SysFont("Arial", 14)              #Informazioni secondarie (turni, posizione)
    font_log = pygame.font.SysFont("Arial", 13)                #Cronologia eventi in piccolo
    #Calcola il margine sinistro interno e la larghezza utile per il testo
    x0 = rect_pannello.x + 18
    larghezza_utile = rect_pannello.width - 36
    
    #INTESTAZIONE E CONTATORE TURNI
    #Stampa il titolo del gioco in alto nel pannello
    screen.blit(font_titolo.render("SCALE E SERPENTI", True, COLORE_TESTO), (x0, rect_pannello.y + 16))
    #Stampa il numero totale di turni completati
    screen.blit(font_testo.render(f"Turni completati: {turni}", True, COLORE_TESTO_TENUE), (x0, rect_pannello.y + 46))

    #INFORMAZIONI SUL GIOCATORE DI TURNO (O VINCITORE)
    #Coordinata di partenza
    y_curr = rect_pannello.y + 78
    #Caso A: la partita è finita -> mostra il vincitore in verde
    if stato == "FINE":
        vincitore = classifica_finale[0] if classifica_finale else partita.calcola_classifica()[0]
        screen.blit(font_sub.render("PARTITA TERMINATA!", True, (40, 167, 69)), (x0, y_curr))
        screen.blit(font_sub.render(f"Vincitore: {vincitore.get_nome()}", True, COLORE_TESTO), (x0, y_curr + 24))
    #Caso B: partita in corso -> mostra pallino colorato, nome, tipologia e casella del giocatore di turno
    else:
        #Traduce in RGB il colore della pedina attuale (get_colore, non "colore")
        colore_g = traduci_colore(getattr(giocatore_turno, "colore", "blu"))
        #Disegna un'anteprima della sua pedina (cerchio colorato + bordo scuro) accanto al nome
        pygame.draw.circle(screen, colore_g, (x0 + 8, y_curr + 9), 8)
        pygame.draw.circle(screen, (20, 20, 20), (x0 + 8, y_curr + 9), 8, 1)
        #Determina l'etichetta ("Bot" o "Umano") e stampa il nome 
        tipo_g = "Bot" if giocatore_turno.is_bot() else "Umano"
        screen.blit(font_sub.render(f"Turno: {giocatore_turno.get_nome()} ({tipo_g})", True, COLORE_TESTO), (x0 + 24, y_curr))
        #Stampa la casella in cui si trova attualmente il giocatore
        screen.blit(font_testo.render(f"Posizione attuale: casella {giocatore_turno.get_posizione()}", True, COLORE_TESTO_TENUE), (x0, y_curr + 24))
        
    #DADO GRAFICO E PULSANTE D'AZIONE
    #Chiama disegna_dado
    disegna_dado(screen, rect_dado, valore_dado, in_animazione=(stato == "ANIMAZIONE_DADO"))
    #Sceglie colore e testo del pulsante in base allo stato del gioco:
    if stato == "FINE":
        #Verde (più chiaro se il mouse ci passa sopra) per chiudere e generare il PDF
        colore_btn = (40, 167, 69) if rect_bottone.collidepoint(pos_mouse) else (33, 136, 56)
        testo_btn = "Continua e Salva Report"
    elif giocatore_turno.is_bot() or stato == "ANIMAZIONE_DADO":
        #Grigio disabilitato quando tocca a un Bot o mentre il dado sta già girando
        colore_btn = COLORE_BOTTONE_DISABILITATO
        testo_btn = "Turno Bot..." if giocatore_turno.is_bot() else "Lancio in corso..."
    else:
        #Blu attivo (più scuro al passaggio del mouse) quando tocca a un giocatore umano
        colore_btn = COLORE_BOTTONE_CLICCABILE if rect_bottone.collidepoint(pos_mouse) else COLORE_BOTTONE
        testo_btn = "Tira dado (SPAZIO)"

    #Disegna il rettangolo arrotondato del pulsante
    pygame.draw.rect(screen, colore_btn, rect_bottone, border_radius=8)
    #Renderizza il testo bianco e lo centra perfettamente dentro rect_bottone
    surf_btn = font_sub.render(testo_btn, True, (255, 255, 255))
    screen.blit(surf_btn, surf_btn.get_rect(center=rect_bottone.center))
    
    #REGISTRO ULTIMI 6 EVENTI
    #Posiziona la sezione cronologia sotto il pulsante
    y_log = rect_bottone.bottom + 22
    #Disegna un separatore visivo
    pygame.draw.line(screen, COLORE_BORDO, (x0, y_log - 8), (x0 + larghezza_utile, y_log - 8), 1)
    #Stampa intestazione
    screen.blit(font_sub.render("Ultimi eventi:", True, COLORE_TESTO), (x0, y_log))
    y_log += 24
    #Prende solo gli ultimi 6 eventi
    ultimi_eventi = partita.get_registro_eventi()[-6:]
    for evento in ultimi_eventi:
        #Spezza l'evento in più righe se è più largo di larghezza_utile
        righe = spezza_testo(f"- {evento}", font_log, larghezza_utile)
        for r in righe:
            #Controlla di non uscire dal bordo inferiore del pannello
            if y_log < rect_pannello.bottom - 18:
                screen.blit(font_log.render(r, True, COLORE_TESTO), (x0, y_log))
                y_log += 18

# NOTA: la vecchia funzione mostra_vincitore() (banner con solo "Vince X!")
# e' stata rimossa: il podio a schermo intero di disegna_podio() la sostituisce.
# Tenerla qui sarebbe stato codice morto e fonte di confusione.

#FUNZIONE PRINCIPALE
def avvia_partita_grafica(partita) -> int:
    """
    Avvia il game loop grafico con macchina a stati:
    ATTESA -> ANIMAZIONE_DADO -> TURNO -> FINE
    Restituisce il numero totale di turni giocati
    """
    # INIZIALIZZAZIONE FINESTRA E RISORSE STATICHE
    pygame.init()
    # Crea finestra principale
    screen = pygame.display.set_mode((LARGHEZZA_FINESTRA, ALTEZZA_FINESTRA))
    # Imposta il titolo
    pygame.display.set_caption("Scale e Serpenti")
    # Crea l'orologio di Pygame per mantenere costante il framerate (60 FPS)
    clock = pygame.time.Clock()
    # Disegna il tabellone una sola volta su una Surface in memoria.
    tabellone = estrai_tabellone(partita)
    surface_tabellone = crea_surface_tabellone(tabellone)

    # DEFINIZIONE DEI RETTANGOLI DELL'INTERFACCIA
    # Rettangolo che delimita la griglia a sinistra
    rect_tabellone = pygame.Rect(MARGINE, MARGINE, DIM_TABELLONE, DIM_TABELLONE)
    # Coordinata X da cui inizia il pannello laterale dx
    pannello_x = MARGINE * 2 + DIM_TABELLONE
    # Rettangolo dell'intero pannello informativo sulla destra
    rect_pannello = pygame.Rect(pannello_x, MARGINE, LARGHEZZA_PANNELLO, ALTEZZA_FINESTRA - MARGINE * 2)
    # Rettangolo del dado, centrato dentro il pannello
    rect_dado = pygame.Rect(pannello_x + (LARGHEZZA_PANNELLO - 76) // 2, MARGINE + 145, 76, 76)
    # Rettangolo cliccabile del pulsante "Tira dado" posizionato subito sotto il dado
    rect_bottone = pygame.Rect(pannello_x + 25, MARGINE + 238, LARGHEZZA_PANNELLO - 50, 44)
    # Rettangolo cliccabile del pulsante "Continua" nella schermata finale del podio
    rect_bottone_podio = None

    # VARIABILI DELLA MACCHINA A STATI
    stato = "ATTESA"
    turni = 0
    valore_dado = 1
    timer_animazione = 0
    timer_bot = pygame.time.get_ticks() + 700

    dado = estrai_dado(partita)
    getter_facce = getattr(dado, "get_facce", None)
    if callable(getter_facce):
        max_facce_dado = getter_facce()
    else:
        max_facce_dado = getattr(dado, "facce", getattr(dado, "_facce", 6))

    in_esecuzione = True
    classifica_finale = []

    # GAME LOOP PRINCIPALE
    while in_esecuzione:
        ora = pygame.time.get_ticks()
        pos_mouse = pygame.mouse.get_pos()

        if hasattr(partita, "get_giocatore_corrente"):
            giocatore_corrente = partita.get_giocatore_corrente()
        else:
            elenco_giocatori = estrai_giocatori(partita)
            indice = getattr(partita, "indice_turno", getattr(partita, "_indice_turno", turni % len(elenco_giocatori)))
            giocatore_corrente = elenco_giocatori[indice]

        # FASE A: GESTIONE EVENTI (TASTIERA, MOUSE, CHIUSURA FINESTRA)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                in_esecuzione = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    in_esecuzione = False
                elif event.key == pygame.K_SPACE:
                    if stato == "FINE":
                        in_esecuzione = False
                    elif stato == "ATTESA" and not giocatore_corrente.is_bot():
                        stato = "ANIMAZIONE_DADO"
                        timer_animazione = ora + 600

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if stato == "FINE":
                    if rect_bottone_podio and rect_bottone_podio.collidepoint(pos_mouse):
                        in_esecuzione = False
                elif rect_bottone.collidepoint(pos_mouse):
                    if stato == "ATTESA" and not giocatore_corrente.is_bot():
                        stato = "ANIMAZIONE_DADO"
                        timer_animazione = ora + 600

        # FASE B: LOGICA DELLA MACCHINA A STATI
        if stato == "ATTESA":
            if partita.is_finita():
                stato = "FINE"
                classifica_finale = partita.calcola_classifica()
            elif giocatore_corrente.is_bot() and ora >= timer_bot:
                stato = "ANIMAZIONE_DADO"
                timer_animazione = ora + 600

        elif stato == "ANIMAZIONE_DADO":
            if ora < timer_animazione:
                valore_dado = random.randint(1, max_facce_dado)
            else:
                stato = "TURNO"

        elif stato == "TURNO":
            partita.esegui_turno()
            turni += 1

            if hasattr(partita, "ultimo_lancio"):
                valore_dado = partita.ultimo_lancio
            elif hasattr(partita, "get_ultimo_lancio"):
                valore_dado = partita.get_ultimo_lancio()

            if partita.is_finita():
                stato = "FINE"
                classifica_finale = partita.calcola_classifica()
            else:
                stato = "ATTESA"
                timer_bot = ora + 750

        # FASE C: DISEGNO DI TUTTI GLI ELEMENTI SULLO SCHERMO
        if stato == "FINE":
            # Pulisce lo schermo e mostra solo il podio finale (aggiornando il pulsante cliccabile)
            screen.fill(COLORE_SFONDO)
            rect_bottone_podio = disegna_podio(
                screen,
                classifica_finale,
                LARGHEZZA_FINESTRA,
                ALTEZZA_FINESTRA,
            )
        else:
            # Incolla l'immagine pre-renderizzata del tabellone
            screen.blit(surface_tabellone, (0, 0))

            # Disegna tutte le pedine nelle loro posizioni aggiornate
            disegna_pedine(screen, partita)

            # Disegna il pannello laterale destro
            disegna_pannello(
                screen,
                partita,
                giocatore_corrente,
                turni,
                valore_dado,
                stato,
                rect_pannello,
                rect_dado,
                rect_bottone,
                pos_mouse,
            )

        # Aggiorna fisicamente la finestra in OGNI stato (anche quando stato == "FINE")
        pygame.display.flip()

        # Mette in pausa il ciclo quanto basta per non superare i 60 FPS
        clock.tick(FPS)

    # CHIUSURA PULITA E RITORNO A MAIN.PY
    pygame.quit()

    # Restituisce il numero totale di turni a main.py per generare classifica, PDF e High Score
    return turni

def disegna_podio(
    screen: pygame.Surface,
    classifica: list,
    larghezza_finestra: int,
    altezza_finestra: int,
):
    # Disegna la schermata del podio finale (top 3 + eventuale riga "altri") centrata nella finestra.
    # Restituisce il rettangolo del pulsante "Continua", che il game loop usa per il click del mouse.
    if not classifica:
        # Caso limite: nessun giocatore. Non c'e' nulla da disegnare ne' un pulsante da cliccare.
        return None

    # Font in stile coerente con il resto del file (Arial): "Helvetica" non e'
    # detto che esista su Windows e pygame ripiegherebbe su un font generico.
    font_titolo = pygame.font.SysFont("Arial", 32, bold=True)
    font_medaglia = pygame.font.SysFont("Arial", 24, bold=True)
    font_info = pygame.font.SysFont("Arial", 15)

    # Titolo in alto
    t_titolo = font_titolo.render("CLASSIFICA FINALE", True, COLORE_TESTO)
    screen.blit(t_titolo, t_titolo.get_rect(center=(larghezza_finestra // 2, 55)))

    # Definizione dei 3 cubi in ordine [2° posto, 1° posto, 3° posto]
    larghezza_cubo = 180
    spazio_tra_cubi = 16
    altezze = [160, 220, 160]  # 2° (sinistra), 1° (centro, più alto), 3° (destra)

    y_base = altezza_finestra - 110
    larghezza_totale = larghezza_cubo * 3 + spazio_tra_cubi * 2
    x_inizio = (larghezza_finestra - larghezza_totale) // 2

    cubi_podio = [
        pygame.Rect(x_inizio, y_base - altezze[0], larghezza_cubo, altezze[0]),                                         # 2° posto (sinistra)
        pygame.Rect(x_inizio + larghezza_cubo + spazio_tra_cubi, y_base - altezze[1], larghezza_cubo, altezze[1]),       # 1° posto (centro)
        pygame.Rect(x_inizio + (larghezza_cubo + spazio_tra_cubi) * 2, y_base - altezze[2], larghezza_cubo, altezze[2]), # 3° posto (destra)
    ]

    # Colori dei cubi (base per 2° e 3°, crema chiaro per il 1° così risalta la medaglia oro)
    colore_base = (210, 220, 230)
    colore_primo = (255, 245, 200)
    colori_cubo = [colore_base, colore_primo, colore_base]

    colori_medaglia = [
        (190, 190, 190),  # Argento 2°
        (241, 196, 15),   # Oro 1°
        (205, 127, 50),   # Bronzo 3°
    ]
    numeri_medaglia = ["2", "1", "3"]
    indici_classifica = [1, 0, 2]  # Mappa ciascun cubo al corrispondente giocatore in classifica

    # Disegna i gradini in ordine 2°, 1°, 3°
    for idx_cubo, idx_class in enumerate(indici_classifica):
        if idx_class >= len(classifica):
            continue  # Gestisce il caso con soli 2 giocatori

        rect = cubi_podio[idx_cubo]
        giocatore = classifica[idx_class]

        # Cubo del podio
        pygame.draw.rect(screen, colori_cubo[idx_cubo], rect, border_top_left_radius=10, border_top_right_radius=10)
        pygame.draw.rect(screen, COLORE_BORDO, rect, 2, border_top_left_radius=10, border_top_right_radius=10)

        # Cerchio medaglia al centro del cubo + bordo + numero
        centro_medaglia = (rect.centerx, rect.centery - 12)
        raggio_medaglia = 30
        pygame.draw.circle(screen, colori_medaglia[idx_cubo], centro_medaglia, raggio_medaglia)
        pygame.draw.circle(screen, (40, 40, 40), centro_medaglia, raggio_medaglia, 3)

        surf_num = font_medaglia.render(numeri_medaglia[idx_cubo], True, (30, 30, 30))
        screen.blit(surf_num, surf_num.get_rect(center=centro_medaglia))

        # Casella raggiunta in basso dentro il cubo
        surf_cas = font_info.render(f"Casella {giocatore.get_posizione()}", True, (40, 40, 40))
        screen.blit(surf_cas, surf_cas.get_rect(center=(rect.centerx, rect.bottom - 24)))

        #Nome giocatore centrato sopra il bordo superiore del cubo + gestione nomi lunghi
        nome = giocatore.get_nome()
        larghezza_max = larghezza_cubo - 12  # Margine laterale di sicurezza

        # 1) Prova a ridurre il font se il nome è troppo largo
        dim_font = 18
        font_nome = pygame.font.SysFont("Arial", dim_font, bold=True)
        while font_nome.size(nome)[0] > larghezza_max and dim_font > 13:
            dim_font -= 1
            font_nome = pygame.font.SysFont("Arial", dim_font, bold=True)

        # 2) Se supera la larghezza del cubo, tronca con "..."
        if font_nome.size(nome)[0] > larghezza_max:
            while len(nome) > 1 and font_nome.size(nome + "...")[0] > larghezza_max:
                nome = nome[:-1]
            nome += "..."

        surf_nome = font_nome.render(nome, True, COLORE_TESTO)
        screen.blit(surf_nome, surf_nome.get_rect(center=(rect.centerx, rect.top - 18)))

        # Pedina del giocatore subito sopra il nome.
        # ATTENZIONE: Giocatore non ha un attributo pubblico "colore" (il campo
        # interno e' _colore e si legge con get_colore()). Usare getattr(..., "colore")
        # faceva cadere sempre sul default "blu", rendendo tutte le pedine blu.
        colore_g = traduci_colore(estrai_colore_giocatore(giocatore, default="blu"))
        pygame.draw.circle(screen, colore_g, (rect.centerx, rect.top - 48), 16)
        pygame.draw.circle(screen, (20, 20, 20), (rect.centerx, rect.top - 48), 16, 2)

    # Eventuale riga "Voi altri" sotto la base del podio.
    # Uso un font dedicato piu' grande e in grassetto (rispetto a font_info,
    # usato per i testi secondari come "Casella N") per dare risalto alla frase.
    font_altri = pygame.font.SysFont("Arial", 22, bold=True)
    y_footer = y_base + 24
    if len(classifica) > 3:
        surf_altri = font_altri.render("Voi altri: i serpenti vi hanno preso", True, COLORE_TESTO_TENUE)
        screen.blit(surf_altri, surf_altri.get_rect(center=(larghezza_finestra // 2, y_footer)))
        # Spazio extra per non far sovrapporre il testo (piu' alto) al pulsante sottostante
        y_footer += 30
    # Istruzione di chiusura
    rect_bottone_podio = pygame.Rect(0, 0, 220, 44)
    rect_bottone_podio.center = (larghezza_finestra // 2, y_footer + 18)

    pygame.draw.rect(screen, COLORE_BOTTONE, rect_bottone_podio, border_radius=8)
    pygame.draw.rect(screen, COLORE_BORDO, rect_bottone_podio, 2, border_radius=8)

    font_btn = pygame.font.SysFont("Arial", 18, bold=True)
    t_btn = font_btn.render("Continua", True, (255, 255, 255))
    screen.blit(t_btn, t_btn.get_rect(center=rect_bottone_podio.center))

    return rect_bottone_podio
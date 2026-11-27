#Librerie
import random
from typing import TYPE_CHECKING
if TYPE_CHECKING:       # permette di utilizzare pygame
    import pygame       # se non è scaricato reindirizza
else:                   # all'utilizzo del sistema CLI
    try:
        import pygame
    except ImportError:
        pygame = None   

#Creo la classe Dado
class Dado:
    def __init__(self, facce: int = 6):
        if isinstance(facce, bool) or not isinstance(facce, int) or facce <= 0:
            raise ValueError("Il numero di facce del dado deve essere un intero maggiore di 0")
        self._facce = facce  # Assegno il numero di facce al dado
    def get_facce(self):
        return self._facce
    def lancia(self):
        # Estrae un numero casuale tra 1 e 6
        return random.randint(1, self._facce)
    def __str__(self):
        return f"Dado da {self._facce} facce"

#Creo la classe Giocatore
class Giocatore:
    contatore_id = 0 #contatore per id univoci
   
    def __init__(self, nome:str, colore:tuple[int,int,int], posizione:int=0,raggio:int=15):
        #[int,int,int] = colore in pygame
        '''
        inizializza un nuovo giocatore

        nome: nome visualizzato
        colore: colore della pedina
        posizione: posizione sul tabellone
        raggio: dimensioni pedina
        '''
        self._nome = nome
        self._colore = colore      # tupla RGB (R, G, B) usata da pygame
        self._posizione = posizione
        self._raggio = raggio
        self._id = Giocatore.contatore_id  #Assegno l'ID univoco corrente
        Giocatore.contatore_id += 1        #Incremento per il prossimo giocatore creato
        self._is_bot = False #distingue umano da bot
    
    #GETTER
    def get_nome(self) -> str:                  
        return self._nome                       
    def get_colore(self) -> tuple[int,int,int]: #Restituisce la tupla RGB assegnata
        return self._colore
    def get_posizione(self) -> int:             #Restituisce la casella sul tabellone
        return self._posizione
    def is_bot(self) -> bool:                   #Restituisce True se il giocatoree e' CPU, False se Umano
        return self._is_bot
    
    #SETTER
    def muovi(self,passi: int) -> None:
        '''
        Sposta il giocatore in un'altra casella. Inclusi monvimenti
        di serpenti o scale. 
        Regola del rimbalzo: se per esempio mi trovo sulla
        casella 97 e tiro 4 (101-100) rimbalzo alla casella 99
        '''
        nuova_pos = self._posizione + passi     #Calcola la posizione sommando i passi alla posizione attuale
        
        #Regola del rimbalzo: se il tiro supera 100, retrocede di tante caselle quante sforate
        if nuova_pos > 100:
            eccesso = nuova_pos - 100
            self._posizione = 100 - eccesso
        else:
            #Movimento normale
            self._posizione = nuova_pos
        return
    
    def reset(self) -> None:
    #Riporta il giocatore alla posizione di partenza (0)
        self._posizione = 0

    #Disegno con pygame
    def disegna(self, superficie: "pygame.Surface", x: int, y: int) -> None:
        '''
        Disegna la pedina come cerchio pieno con bordo nero.
        superficie: Surface su cui disegnare (di solito lo schermo pygame)
        x, y: coordinate in PIXEL del CENTRO della pedina, non della casella.
        La conversione casella -> pixel non spetta a questa classe:
        la fa il livello grafico
        '''
        # Primo cerchio: colore del giocatore.
        if pygame is None:
            raise RuntimeError("Pygame non e' installato")
        # pygame.draw.circle(superficie, colore, centro, raggio)
        pygame.draw.circle(superficie, self._colore, (x, y), self._raggio)

        # Secondo cerchio: contorno nero
        pygame.draw.circle(superficie, (0, 0, 0), (x, y), self._raggio, width=2)

        #Controlli e Rappresentazione
    def vincitore(self) -> bool:
        #Verifica se il giocatore ha vinto
        return self._posizione == 100
        
    def __str__(self) -> str:
        #Restituiscce una descrizione testuale dello stato del giocatore
        return(f"Giocatore(nome='{self._nome}',"
                f"colore={self._colore}, "
                f"posizione={self._posizione}, "
                f"id={self._id}, "
                f"raggio={self._raggio})")
    
class GiocatoreUmano(Giocatore):
    #Giocatore controllato da utente
    def __init__(self, nome:str, colore:tuple[int,int,int], posizione:int=0,raggio:int=15):
        super().__init__(nome, colore, posizione, raggio)
        self._is_bot = False

class GiocatoreBot(Giocatore):
    #Giocatore controllato dal computer
    def __init__(self, nome:str, colore:tuple[int,int,int], posizione:int=0,raggio:int=15):
        super().__init__(nome, colore, posizione, raggio)
        self._is_bot = True

#Creo la classe Tabellone
class Tabellone:
    # Il Tabellone e' solo un MODELLO DATI: non conosce pixel ne' pygame.
    # _collegamenti ha la forma:
    #   { casella_partenza: (casella_arrivo, "scala" | "serpente", "Rossa" | ...) }
    def __init__(self, collegamenti: dict = None):
        self._righe = 10
        self._colonne = 10
        self._totale_caselle = 100
        #se non ci sono collegamenti, inizializza un tabellone vuoto
        self._collegamenti = collegamenti if collegamenti is not None else {}

        #GETTER
    def get_totale_caselle(self) -> int:
        #Restituisce il numero complessivo di caselle del tabellone
        return self._totale_caselle
    def get_collegamenti(self) -> dict:
        #Restituisce il dizionario dei collegamenti (scale e serpenti)
        return self._collegamenti
        
    def valuta_casella(self, posizione:int) -> tuple[bool,int,str,str]:
        '''
        Controlla se su una casella inizia una scala o serpente
        Restituisce: (trovato, nuova_posizone, tipo, colore)
        '''     
        if posizione in self._collegamenti:     #Verifica se sulla casella c'è una scala o un serpente
                nuova_pos, tipo, colore = self._collegamenti[posizione]
                return True, nuova_pos, tipo, colore
                #Nessun collegamento 
        return False, posizione, None, None

#Creo la classe Partita
class Partita:
    '''
    Gestisce l'intera logica di una partita: turni, lanci, effetti del tabellone,
    storico eventi e calcolo classifica.
    Completamente disaccoppiata da CLI o Pygame
    '''
    def __init__(self, giocatori:list[Giocatore], tabellone:Tabellone, dado:Dado):
        self._giocatori = giocatori     # Da 2 a 26
        self._tabellone = tabellone
        self._dado = dado
        self._indice_turno = 0          # Indice del giocatore di turno
        self._giri_completati = 0       # Turno completato da tutti = 1 giro
        self._vincitore = None
        self._partita_finita = False
        self._registro_eventi: list[tuple[int, str]] = []   # Lista di (giro, descrizione)
        self._classifica_finale = []
        self._ultimo_lancio = None

    #GETTER
    def is_finita(self) -> bool:
        #Restituisce True se un giocatore ha raggiunto 100
        return self._partita_finita
    def get_giocatore_corrente(self) -> Giocatore:
        #Restituisce l'istanza del giocatore a cui spetta il turno attuale
        return self._giocatori[self._indice_turno]
    def get_registro_eventi(self) -> list[str]:
        #Restituisce l'elenco testo degli eventi (per PDF e Grafica) 
        return [f"[Giro {giro}] {desc}" for giro, desc in self._registro_eventi]
    def get_registro_eventi_dettagliato(self) -> list[tuple[int, str]]:
        #Restituisce le tuple (giro, descrizione) per il salvataggio su DB
        return list(self._registro_eventi)
    def get_vincitore(self) -> Giocatore:
        #Resituisce il giocatore vincitore
        return self._vincitore
    def get_tabellone(self) -> Tabellone:
        return self._tabellone
    def get_giocatori(self) -> list[Giocatore]:
        #Restituisce la lista dei giocatori partecipanti nell'ordine di turno
        return self._giocatori
    def get_dado(self) -> Dado:
        #Restituisce l'oggetto Dado utilizzato nella partita
        return self._dado
    def get_ultimo_lancio(self) -> int:
        #Restituisce il valore ottenuto nell'ultimo tiro
        return self._ultimo_lancio
    def get_giri_completati(self) -> int:
        #Restituisce il numero di round completi (tutti hanno tirato)
        return self._giri_completati
    
    def esegui_turno(self) -> str:
        '''
        1.lancio
        2.muovo
        3.controllo
        4.vedo se ho vinto
        5.passo il turno
        '''
        #Impedisce ulteriori turni se la partita e' gia' finita
        if self._partita_finita:                    
            return "La partita e' terminata"
        #Raccolta dati di inizio turno: giocatore attivo e lancio del dado
        giocatore = self.get_giocatore_corrente()
        lancio = self._dado.lancia()
        self._ultimo_lancio = lancio
        pos_iniziale = giocatore.get_posizione()
       
        #1.Spostamento sul tabellone + gestione rimbalzo
        giocatore.muovi(lancio)
        pos_intermedia = giocatore.get_posizione()
        if pos_iniziale + lancio > 100:
            messaggio_evento = (
                f"{giocatore.get_nome()} ha tirato {lancio}, supera 100 "
                f"e rimbalza alla casella {pos_intermedia}"
            )
        else:
            messaggio_evento = f"{giocatore.get_nome()} ha tirato {lancio} (da {pos_iniziale} arriva a {pos_intermedia})"

        #2. Valutazione della casella: ci sono scale o serpenti?
        trovato, pos_finale, tipo, colore = self._tabellone.valuta_casella(pos_intermedia)
        if trovato:
            # Apllica la differenza tra arrivo e partenza
            scarto = pos_finale - pos_intermedia #calcolo spostamento
            giocatore.muovi(scarto)
            if tipo == "scala":
                messaggio_evento += f" Sale su una scala {colore} fino alla casella {pos_finale}."
            else:
                messaggio_evento += f" Scivola su un serpente {colore} fino alla casella {pos_finale}."

        # Registrazione dell'evento nel log storico
        giro_corrente = self._giri_completati + 1
        self._registro_eventi.append((giro_corrente, messaggio_evento))
        
        # Controllo condizioni di vittoria
        if giocatore.vincitore():
            self._partita_finita = True
            self._vincitore = giocatore
            self._registro_eventi.append((giro_corrente, f"!!!Vittoria!!! {giocatore.get_nome()} ha raggiunto la casella numero 100"))
        # Avanzamento al giocatore successivo
        self._indice_turno += 1
        if self._indice_turno >= len(self._giocatori):
            self._indice_turno = 0
            self._giri_completati += 1
        
        return messaggio_evento
    
    def calcola_classifica(self) -> list[Giocatore]:
        '''
        Calcola e memorizza la classifica finale.
        Ordina dal punteggio più alto al più basso.
        In caso di parità prevale l'ID minore.
        '''
        # Usa una funzione lambda come chiave di ordinamento:
        # -giocatore.get_posizione(): ordina per casella in modo decrescente
        # -giocatore._id: spareggio a parità di posizione
        classifica = sorted(
            self._giocatori,
            key=lambda giocatore: (-giocatore.get_posizione(), giocatore._id)
        )
    #Reverse=True inverte l'ordine in modo che chi ha 100 finisce a indice 0, senno' sarebbe ultimo
        self._classifica_finale = classifica
        return classifica
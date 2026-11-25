#Librerie
import random
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pygame
else:
    try:
        import pygame
    except ImportError:
        pygame = None

#Creo la classe Dado
class Dado:
    def __init__(self,facce=6):
        self._facce = facce #Assegno il numero di facce al dado
    def get_facce(self):
        return self._facce
    def lancia(self):
        return random.randint(1, self._facce)
    def __str__(self):
        return f"Dado da {self._facce} facce"
#Creo la classe Giocatore
class Giocatore:
    contatore_id = 0 #contatore per id univoci
   
    def __init__(self, nome:str, colore:tuple[int,int,int], posizione:int=0,raggio:int=15):
        #[int,int,int] = colore in pygame
        '''
        nome: nome visualizzato
        colore: colore della pedina
        posizione: posizione sul tabellone
        raggio: dimensioni pedina
        '''
        self._nome = nome
        self._colore = colore      # tupla RGB (R, G, B) usata da pygame
        self._posizione = posizione
        self._raggio = raggio
        self._id = Giocatore.contatore_id  #Assegno ID corrente
        Giocatore.contatore_id += 1        #Incremento contatore per la prossima istanza
        self._is_bot = False #distingue umano da bot
    #GETTER
    def get_nome(self) -> str:
        return self._nome
    def get_colore(self) -> tuple[int,int,int]:
        return self._colore
    def get_posizione(self) -> int:
        return self._posizione
    def is_bot(self) -> bool:
        return self._is_bot
    #SETTER
    def muovi(self,passi: int) -> None:
        '''
        Sposta il giocatore in un'altra casella. Regola del rimbalzo: se per esempio mi trovo sulla
        casella 97 e tiro 4 (101-100) rimbalzo alla casella 99
        '''
        nuova_pos = self._posizione + passi
        if nuova_pos > 100:
            eccesso = nuova_pos - 100
            self._posizione = 100 - eccesso
        else:
            self._posizione = nuova_pos
        return
    def reset(self) -> None:
    #Riporta il giocatore alla posizione di partenza
        self._posizione = 0

    #Disegno con pygame
    def disegna(self, superficie: "pygame.Surface", x: int, y: int) -> None:
        '''
        Disegna la pedina come cerchio pieno con bordo nero.

        superficie: Surface su cui disegnare (di solito lo schermo pygame)
        x, y: coordinate in PIXEL del CENTRO della pedina, non della casella.
              La conversione casella -> pixel non spetta a questa classe:
              la fa il livello grafico, che conosce dimensioni e margini.
        '''
        # Primo cerchio: pieno, del colore del giocatore.
        if pygame is None:
            raise RuntimeError("Pygame non e' installato")
        # pygame.draw.circle(superficie, colore, centro, raggio)
        pygame.draw.circle(superficie, self._colore, (x, y), self._raggio)

        # Secondo cerchio: solo contorno (width=2), per staccare la pedina
        # dallo sfondo. (0,0,0) = nero.
        pygame.draw.circle(superficie, (0, 0, 0), (x, y), self._raggio, width=2)

        # Nota: qui NON si chiama pygame.display.flip().
        # Il flip va fatto una sola volta per frame nel game loop,
        # dopo aver disegnato tabellone, pedine, dado e pannello.

        #Controlli
    def vincitore(self) -> bool:
        return self._posizione == 100
        #Rappresentazione
    def __str__(self) -> str:
        return(f"Giocatore(nome='{self._nome}',"
                f"colore={self._colore}, "
                f"posizione={self._posizione}, "
                f"id={self._id}, "
                f"raggio={self._raggio})")
class GiocatoreUmano(Giocatore):
    def __init__(self, nome:str, colore:tuple[int,int,int], posizione:int=0,raggio:int=15):
        super().__init__(nome, colore, posizione, raggio)
        self._is_bot = False
class GiocatoreBot(Giocatore):
    def __init__(self, nome:str, colore:tuple[int,int,int], posizione:int=0,raggio:int=15):
        super().__init__(nome, colore, posizione, raggio)
        self._is_bot = True
#Creo la classe Tabellone
class Tabellone:
    # Il Tabellone e' solo un MODELLO DATI: non conosce pixel ne' pygame.
    # _collegamenti ha la forma:
    #   { casella_partenza: (casella_arrivo, "scala"/"serpente", "Rossa"/...) }
    # Il livello grafico usera' get_collegamenti() per disegnare le linee
    # e dovra' convertire da solo ogni numero di casella in coordinate pixel.
    def __init__(self, collegamenti: dict = None):
        self._righe = 10
        self._colonne = 10
        self._totale_caselle = 100
        #se non ci sono collegamenti, usiamo un dizionario vuoto
        self._collegamenti = collegamenti if collegamenti is not None else {}

        #GETTER
    def get_totale_caselle(self) -> int:
        return self._totale_caselle
    def get_collegamenti(self) -> dict:
        return self._collegamenti
        
    def valuta_casella(self, posizione:int) -> tuple[bool,int,str,str]:
    #trovato[vero,posizione,scla/seprente,rossa/gialla/verde]
        if posizione in self._collegamenti:
            nuova_pos, tipo, colore = self._collegamenti[posizione]
            return True, nuova_pos, tipo, colore
        #nessun evento
        return False, posizione, None, None

#Creo la classe Partita
class Partita:
    # Anche Partita e' indipendente dalla grafica: non disegna nulla.
    # Un eventuale game loop grafico deve solo:
    #   - leggere lo stato con i getter
    #   - chiamare esegui_turno() quando l'utente/bot lancia il dado
    #   - ridisegnare la scena dopo ogni cambiamento
    def __init__(self, giocatori:list[Giocatore], tabellone:Tabellone, dado:Dado):
        self._giocatori = giocatori     #da 2 a 26
        self._tabellone = tabellone
        self._dado = dado
        self._indice_turno = 0
        self._giri_completati = 0
        self._vincitore = None
        self._partita_finita = False
        self._registro_eventi = []
        self._classifica_finale = []
        self._ultimo_lancio = None

    #GETTER
    def is_finita(self) -> bool:
        return self._partita_finita
    def get_giocatore_corrente(self) -> Giocatore:
        return self._giocatori[self._indice_turno]
    def get_registro_eventi(self) -> list[str]:
        return self._registro_eventi
    def get_vincitore(self) -> Giocatore:
        return self._vincitore
    def get_tabellone(self) -> Tabellone:
        return self._tabellone
    def get_giocatori(self) -> list[Giocatore]:
        return self._giocatori
    def get_dado(self) -> Dado:
        return self._dado
    def get_ultimo_lancio(self) -> int:
        return self._ultimo_lancio
    def get_giri_completati(self) -> int:
        return self._giri_completati
    
    def esegui_turno(self) -> str:
        '''
        1.lancio
        2.muovo
        3.controllo
        4.vedo se ho vinto
        5.passo il turno
        '''
        if self._partita_finita:
            return "la partita e'terminata"
        #Incrementa il giro ogni volta che il turno riparte dal primo giocatore
        if self._indice_turno == 0:
            self._giri_completati += 1
        #Dati inizio turno
        giocatore = self.get_giocatore_corrente()
        lancio = self._dado.lancia()
        self._ultimo_lancio = lancio
        pos_iniziale = giocatore.get_posizione()
       
        #1.lancio e muovo
        giocatore.muovi(lancio)
        pos_intermedia = giocatore.get_posizione()
        if pos_iniziale + lancio > 100:
            messaggio_evento = (
                f"{giocatore.get_nome()} ha tirato {lancio}, supera 100 "
                f"e rimbalza alla casella {pos_intermedia}"
            )
        else:
            messaggio_evento = f"{giocatore.get_nome()} ha tirato {lancio} (da {pos_iniziale} arriva a {pos_intermedia})"

        #2. controllo
        trovato, pos_finale, tipo, colore = self._tabellone.valuta_casella(pos_intermedia)
        if trovato:
            scarto = pos_finale - pos_intermedia #calcolo spostamento
            giocatore.muovi(scarto)
            if tipo == "scala":
                messaggio_evento += f" Sale su una scala {colore} fino alla casella {pos_finale}."
            else:
                messaggio_evento += f" Scivola su un serpente {colore} fino alla casella {pos_finale}."

        # Salvo l'evento
        self._registro_eventi.append(messaggio_evento)
        
        #3. Ho vinto?
        if giocatore.vincitore():
            self._partita_finita = True
            self._vincitore = giocatore
            self._registro_eventi.append(f"!!!Vittoria!!! {giocatore.get_nome()} ha raggiunto la casella numero 100")
        else:
            self._indice_turno += 1
            if self._indice_turno >= len(self._giocatori):
                self._indice_turno = 0
        return messaggio_evento
    def calcola_classifica(self) -> list[Giocatore]:
    #Chi arriva a 100 vince, gli altri sono ordinati in base a dove si trovano
        classifica = sorted(
            self._giocatori,
            key = lambda giocatore: giocatore.get_posizione(),
            reverse = True
        )
    #Reverse=True inverte l'ordine in modo che chi ha 100 finisce a indice 0, senno' sarebbe ultimo
    #lambda?
        self._classifica_finale = classifica
        return classifica
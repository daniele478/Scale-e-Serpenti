#Librerie
import random
import pygame
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
        self._colore = colore
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
            print(f"{self._nome} ha superato il 100 ed e' rimbalzato alla casella {self._posizione}")
        else:
            self._posizione = nuova_pos
        return
    def reset(self) -> None:
    #Riporta il giocatore alla posizione di partenza
        self._posizione = 0

    #Disegno con pygame
    def disegna(self, superficie: pygame.Surface, x: int, y: int) -> None:
        '''
        superficie: oggetto su cui disegnare
        x: coordinata x del centro della pedina
        y: coordinata y del centro della pedina
        '''
        pygame.draw.circle(superficie, self._colore, (x,y), self._raggio)
        pygame.draw.circle(superficie,(0,0,0), (x,y), self._raggio, width=2)
        # (0,0,0) = nero, metto un contorno nero alla pedina per renderla visibile

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
    def __init__(self, giocatori:list[Giocatore], tabellone:Tabellone, dado:Dado):
        self._giocatori = giocatori     #da 2 a 4
        self._tabellone = tabellone
        self._dado = dado
        self._indice_turno = 0
        self._vincitore = None
        self._partita_finita = False
        self._registro_eventi = []
        self._classifica_finale = []

    #GETTER
    def is_finita(self) -> bool:
        return self._partita_finita
    def get_giocatore_corrente(self) -> Giocatore:
        return self._giocatori[self._indice_turno]
    def get_registro_eventi(self) -> list[str]:
        return self._registro_eventi
    def get_vincitore(self) -> Giocatore:
        return self._vincitore

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
        #Dati inizio turno
        giocatore = self.get_giocatore_corrente()
        lancio = self._dado.lancia()
        pos_iniziale = giocatore.get_posizione()
       
        #1.lancio e muovo
        giocatore.muovi(lancio)
        pos_intermedia = giocatore.get_posizione()
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
    #lamba?
        self._classifica_finale = classifica
        return classifica
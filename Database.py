import os
import sqlite3
import hashlib  # serve per creare l'hash della password
import hmac     # serve per confrontare gli hash in modo sicuro
import secrets  # serve per generare un salt casuale
import re       # serve per verificare formato/caratteri dello username
from datetime import datetime
from typing import List, Tuple, Optional
from contextlib import closing

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_nome = os.path.join(BASE_DIR, "scale_serpenti.db")

# Numero di "giri" usati per creare l'hash.
# Piu' e' alto, piu' la password e' difficile da indovinare, ma il login e' piu' lento.
ITERAZIONI_HASH = 260000


def connetti():
    # Crea la connessione al db e abilita le chiavi esterne
    conn = sqlite3.connect(db_nome)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def crea_tabelle() -> None:
    # Crea le tabelle
    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()

        # Tabella Utenti
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS utenti (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                partite_giocate INTEGER DEFAULT 0,
                partite_vinte INTEGER DEFAULT 0,
                record_turni INTEGER DEFAULT NULL
            )
            '''
        )

        # Tabella Partite (storico di tutte le partite concluse)
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS partite (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_ora TEXT NOT NULL,
                vincitore TEXT NOT NULL,
                turni_totali INTEGER NOT NULL
            )
            '''
        )

        # Migrazione dello schema di registro_eventi.
        # Se la tabella esiste ma non ha tutte le colonne richieste (schema
        # vecchio senza indice_evento oppure schema intermedio senza giro),
        # viene ricreata da zero. Gli eventi dei vecchi schemi non sono
        # convertibili in modo affidabile, quindi vengono scartati e i
        # record_turni (legati a quei dati) vengono azzerati.
        cursor.execute("PRAGMA table_info(registro_eventi)")
        colonne = {riga[1] for riga in cursor.fetchall()}
        colonne_richieste = {
            "id",
            "partita_id",
            "indice_evento",
            "giro",
            "descrizione",
            "timestamp",
        }
        if colonne and not colonne_richieste.issubset(colonne):
            cursor.execute("DROP TABLE registro_eventi")
            # Anche lo storico partite dipende dagli eventi scartati: senza
            # questa pulizia resterebbero partite visibili ma senza eventi.
            cursor.execute("DELETE FROM partite")
            cursor.execute("UPDATE utenti SET record_turni = NULL")

        # Tabella Registro Eventi (collegata alla singola partita tramite partita_id)
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS registro_eventi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partita_id INTEGER NOT NULL,
                indice_evento INTEGER NOT NULL,
                giro INTEGER NOT NULL,
                descrizione TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            '''
        )


# GESTIONE UTENTI E LOGIN

# Crea l'hash della password con un salt casuale.
# Il risultato e' una stringa da salvare nel database al posto della password.
def genera_hash(password: str) -> str:
    salt = secrets.token_bytes(16)  # salt casuale di 16 byte
    hash_password = hashlib.pbkdf2_hmac(
        "sha256",                  # algoritmo usato
        password.encode("utf-8"),  # password trasformata in byte
        salt,                      # salt casuale
        ITERAZIONI_HASH            # numero di ripetizioni
    )
    # Salvo algoritmo, iterazioni, salt e hash separati da "$"
    return f"pbkdf2_sha256${ITERAZIONI_HASH}${salt.hex()}${hash_password.hex()}"


# Controlla se la password inserita corrisponde all'hash salvato
def verifica_hash(password: str, hash_salvato: str) -> bool:
    try:
        # Divido la stringa salvata nelle sue 4 parti
        algoritmo, iterazioni, salt_hex, hash_hex = hash_salvato.split("$")

        if algoritmo != "pbkdf2_sha256":
            return False

        # Rifaccio l'hash usando lo stesso salt e le stesse iterazioni
        hash_password = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterazioni)
        )
        # compare_digest confronta i due hash in modo sicuro
        return hmac.compare_digest(hash_password.hex(), hash_hex)

    except (ValueError, TypeError, AttributeError):
        # Se la stringa salvata e' rovinata o nel formato sbagliato
        return False

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,16}$")   
"""
Regola validazione username:
^...$           ---> controlla l'intera stringa
[a-zA-Z0-9_-]   ---> ammette solo lettere,numeri, _, -
{3,16}          ---> lunghezza compresa tra 3 e 16 caratteri
"""

def valida_credenziali(username: str, password: str) -> tuple[str, str]:
    """
    Pulisce gli spazi esterni e verifica:
    - username: 3-16 caratteri (solo lettere, numeri, '_' o '-')
    - password: almeno 4 caratteri, senza spazi
    ValueError messaggio se non valide.
    """
    user_pulito = username.strip()
    pass_pulita = password.strip()

    if not USERNAME_REGEX.match(user_pulito):
        raise ValueError(
            "Username non valido: usa 3-16 caratteri (solo lettere, numeri, '_' o '-')."
        )
    if len(pass_pulita) < 4:
        raise ValueError("Password non valida: deve contenere almeno 4 caratteri.")

    if not (4 <= len(pass_pulita) <= 64):
        raise ValueError("Password non valida: deve contenere tra 4 e 64 caratteri.")
    
    return user_pulito, pass_pulita

def registra_utente(username: str, password: str) -> bool:
    user_pulito, pass_pulita, = valida_credenziali(username,password)
    try:
        with closing(connetti()) as conn, conn:
            cursor = conn.cursor() # oggetto che esegue le query SQL e legge i risultati dalla connessione
            #"Daniele" e "daniele" sono lo stesso utente
            cursor.execute(
                "SELECT 1 FROM utenti WHERE LOWER(username) = LOWER(?)",
                (user_pulito,),
            )
            if cursor.fetchone() is not None:
                return False

            cursor.execute(
                '''
                INSERT INTO utenti (username, password, partite_giocate, partite_vinte, record_turni)
                VALUES (?, ?, 0, 0, NULL)
                ''',
                (user_pulito, genera_hash(pass_pulita)),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def verifica_login(username: str, password: str) -> Optional[str]:
    user_pulito = username.strip()
    pass_pulita = password.strip()
    if not user_pulito or not pass_pulita:
        return None
    
    # Verifica credenziali di accesso
    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT username, password FROM utenti WHERE LOWER(username) = LOWER(?)
            ''',
            (user_pulito,),
        )
        utente = cursor.fetchone()

        # Utente non trovato
        if utente is None:
            return None

        username_canonico, password_salvata = utente
        
        if verifica_hash(pass_pulita, password_salvata):
            return username_canonico
        return None

def aggiorna_statistiche_vittoria(username: str, giri: int) -> None:
    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()

        # Record attuale
        cursor.execute('SELECT record_turni FROM utenti WHERE username = ?', (username,))
        risultato = cursor.fetchone()

        if risultato is None:
            raise ValueError(f"Utente '{username}' non trovato nel database.")
        record = risultato[0]
        nuovo_record = giri if (record is None or giri < record) else record
        cursor.execute(
            '''
            UPDATE utenti
            SET partite_giocate = partite_giocate + 1,
                partite_vinte = partite_vinte + 1,
                record_turni = ?
            WHERE username = ?
            ''',
            (nuovo_record, username),
        )
def aggiorna_statistiche_sconfitta(username: str) -> None:
    """
    Incrementa per i giocatori che hanno perso.
    Restituisce True se l'utente esiste ed e' aggiornato, senno' False
    """
    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            UPDATE utenti
            SET partite_giocate = partite_giocate + 1
            WHERE username = ?
            ''',
            (username,),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Utente '{username}' non trovato nel database")

def salva_eventi(eventi: list, vincitore: str, giri_totali: int) -> None:
    if not eventi:
        return
    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = datetime.now().isoformat(timespec="seconds")

    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO partite (data_ora, vincitore, turni_totali)
            VALUES (?, ?, ?)
            """,
            (data_ora, vincitore, giri_totali),
        )
        partita_id = cursor.lastrowid

        for indice, elemento in enumerate(eventi, start=1):
            if isinstance(elemento, tuple):
                giro, descrizione = elemento
            else:
                giro, descrizione = 0, str(elemento)

            cursor.execute(
                """
                INSERT INTO registro_eventi (partita_id, indice_evento, giro, descrizione, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (partita_id, indice, giro, descrizione, timestamp),
            )


def ottieni_highscore() -> List[Tuple[str, int, int, Optional[int]]]:
    """
    Recupera tutti gli utenti dal db ordinati per:
    1. Maggior numero di vittorie
    2. Minor numero di turni impiegati per vincere
    Restituisce una lista di tuple (username, partite_giocate, partite_vinte, record_turni)
    """
    with closing(connetti()) as conn:
        # crea connessione tra py e db
        cursor = conn.cursor()
        # puntatore che viaggia nel db per eseguire operazioni e riportare i risultati
        cursor.execute(
            '''
            SELECT username, partite_giocate, partite_vinte, record_turni
            FROM utenti
            ORDER BY partite_vinte DESC, COALESCE(record_turni, 999999) ASC
            '''
        )
        # l'ordine scritto in linguaggio SQL
        # COALESCE = trasforma i valori NULL in 999999 per metterli ultimi in posizione
        return cursor.fetchall()

def ottieni_storico_partite(limite: int = 20) -> List[Tuple[int, str, str, int]]:
    """
     Restituisce le ultime `limite` partite concluse:
    [(id, data_ora, vincitore, turni_totali), ...]
    """
    with closing(connetti()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, data_ora, vincitore, turni_totali
            FROM partite
            ORDER BY id DESC
            LIMIT ?
            """,
            (limite,),
        )
        return cursor.fetchall()


def ottieni_eventi_partita(partita_id: int) -> List[Tuple[int, int, str]]:
    """
    Restituisce tutti gli eventi di una specifica partita ordinati cronologicamente:
    [(indice_evento, giro, descrizione), ...]
    """
    with closing(connetti()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT indice_evento, giro, descrizione
            FROM registro_eventi
            WHERE partita_id = ?
            ORDER BY indice_evento ASC
            """,
            (partita_id,),
        )
        return cursor.fetchall()
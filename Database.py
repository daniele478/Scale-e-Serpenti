import os
import sqlite3
import hashlib  # serve per creare l'hash della password
import hmac     # serve per confrontare gli hash in modo sicuro
import secrets  # serve per generare un salt casuale
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

        # Tabella Registro Eventi (collegata alla singola partita tramite partita_id)
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS registro_eventi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partita_id INTEGER NOT NULL,
                indice_evento INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                descrizione TEXT NOT NULL,
                FOREIGN KEY (partita_id) REFERENCES partite(id)
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


def registra_utente(username: str, password: str) -> bool:
    try:
        with closing(connetti()) as conn, conn:
            conn.execute(
                '''
                INSERT INTO utenti (username, password, partite_giocate, partite_vinte, record_turni)
                VALUES (?, ?, 0, 0, NULL)
                ''',
                (username, genera_hash(password)),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def verifica_login(username: str, password: str) -> bool:
    # Verifica credenziali di accesso
    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT password FROM utenti WHERE username = ?
            ''',
            (username,),
        )
        utente = cursor.fetchone()

        # Utente non trovato
        if utente is None:
            return False

        password_salvata = utente[0]

        # Caso vecchio database: password salvata in chiaro (senza "$")
        if "$" not in password_salvata:
            if password == password_salvata:
                # Aggiorno subito la riga con l'hash, cosi' la prossima volta e' protetta
                cursor.execute(
                    'UPDATE utenti SET password = ? WHERE username = ?',
                    (genera_hash(password), username),
                )
                return True
            return False

        # Caso normale: confronto la password inserita con l'hash salvato
        return verifica_hash(password, password_salvata)


def aggiorna_statistiche_vittoria(username: str, turni: int) -> None:
    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()

        # Record attuale
        cursor.execute('SELECT record_turni FROM utenti WHERE username = ?', (username,))
        risultato = cursor.fetchone()

        if risultato is None:
            raise ValueError(f"Utente '{username}' non trovato nel database.")
        record = risultato[0]
        nuovo_record = turni if (record is None or turni < record) else record
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
    # Incrementa per i giocatori che hanno perso
    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()
        conn.execute(
            '''
            UPDATE utenti
            SET partite_giocate = partite_giocate + 1
            WHERE username = ?
            ''',
            (username,),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Utente '{username}' non trovato nel database.")


def salva_eventi(registro_eventi: List[str], vincitore: str = "Sconosciuto", turni_totali: int = 0) -> int:
    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO partite (data_ora, vincitore, turni_totali)
            VALUES (?, ?, ?)
            ''',
            (data_ora, vincitore, turni_totali),
        )
        partita_id = cursor.lastrowid

        righe_eventi = [
            (partita_id, i, data_ora, evento)
            for i, evento in enumerate(registro_eventi, 1)
        ]
        cursor.executemany(
            '''
            INSERT INTO registro_eventi (partita_id, indice_evento, timestamp, descrizione)
            VALUES (?, ?, ?, ?)
            ''',
            righe_eventi,
        )

    return partita_id


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
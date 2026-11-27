import os
import sqlite3
import hashlib  # Genera l'hash crittografico delle password (PBKDF2-HMAC)
import hmac     # Confronta due hash in tempo costante (previene timing attack)
import secrets  # Genera salt crittograficamente sicuri
import re       # Espressioni regolari per validare il formato dell'username
from datetime import datetime
from typing import List, Tuple, Optional
from contextlib import closing

# Percorso assoluto della cartella corrente e del file database SQLite
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_nome = os.path.join(BASE_DIR, "scale_serpenti.db")

# Numero di iterazioni PBKDF2: rallenta gli attacchi brute-force mantenendo il login reattivo
ITERAZIONI_HASH = 260000

# CONNESSIONE E INIZIALIZZAZIONE SCHEMA DATABASE
def connetti():
    """Apre una connessione al database SQLite e attiva i vincoli di chiave esterna."""
    conn = sqlite3.connect(db_nome)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def crea_tabelle() -> None:
    """Crea le tabelle necessarie del database se non esistono ancora."""
    # 'closing(connetti())' garantisce la chiusura della connessione;
    # 'with conn:' gestisce automaticamente commit o rollback della transazione.
    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()

        # Tabella Utenti: credenziali (password hash) e statistiche cumulative
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

        # Tabella Partite: riepilogo delle partite concluse
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

        # Tabella Registro Eventi: log dettagliato dei singoli turni per partita
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS registro_eventi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partita_id INTEGER NOT NULL,
                indice_evento INTEGER NOT NULL,
                giro INTEGER NOT NULL,
                descrizione TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (partita_id) REFERENCES partite(id)
            )
            '''
        )

        # CREATE TABLE IF NOT EXISTS non aggiorna una tabella già esistente:
        # se lo schema è vecchio, avvisa subito invece di fallire a fine partita.
        cursor.execute("PRAGMA table_info(registro_eventi)")
        colonne = {riga[1] for riga in cursor.fetchall()}
        if colonne and not {"indice_evento", "giro", "timestamp"}.issubset(colonne):
            raise RuntimeError(
                "Database obsoleto: elimina scale_serpenti.db e riavvia l'applicazione."
            )

# SICUREZZA PASSWORD E VALIDAZIONE CREDENZIALI
def genera_hash(password: str) -> str:
    """
    Deriva un hash sicuro dalla password in chiaro usando PBKDF2-HMAC-SHA256
    con un salt casuale da 16 byte.
    Restituisce una stringa auto-descrittiva nel formato:
        pbkdf2_sha256$<iterazioni>$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_bytes(16)
    hash_password = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERAZIONI_HASH
    )
    return f"pbkdf2_sha256${ITERAZIONI_HASH}${salt.hex()}${hash_password.hex()}"


def verifica_hash(password: str, hash_salvato: str) -> bool:
    """
    Verifica se 'password' corrisponde all'hash salvato nel database.
    Estrae salt e iterazioni dalla stringa salvata, ricalcola l'hash e lo
    confronta in tempo costante tramite 'hmac.compare_digest'.
    """
    try:
        algoritmo, iterazioni, salt_hex, hash_hex = hash_salvato.split("$")

        if algoritmo != "pbkdf2_sha256":
            return False

        hash_password = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterazioni)
        )
        return hmac.compare_digest(hash_password.hex(), hash_hex)

    except (ValueError, TypeError, AttributeError):
        # Stringa malformata o tipo non valido nel record DB
        return False


# Espressione regolare per l'username:
# ^...$           -> controlla l'intera stringa da inizio a fine
# [a-zA-Z0-9_-]   -> ammette solo lettere, numeri, underscore e trattino
# {3,16}          -> lunghezza minima 3, massima 16 caratteri
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]{3,16}$")


def valida_credenziali(username: str, password: str) -> tuple[str, str]:
    """
    Rimuove gli spazi iniziali/finali e verifica i vincoli di formato:
    - username: 3-16 caratteri alfanumerici, '_' o '-'
    - password: tra 4 e 64 caratteri
    Solleva 'ValueError' con messaggio esplicativo se i dati non sono validi.
    """
    user_pulito = username.strip()
    pass_pulita = password.strip()

    if not USERNAME_REGEX.match(user_pulito):
        raise ValueError(
            "Username non valido: usa 3-16 caratteri (solo lettere, numeri, '_' o '-')."
        )
    if not (4 <= len(pass_pulita) <= 64):
        raise ValueError("Password non valida: deve contenere tra 4 e 64 caratteri.")

    return user_pulito, pass_pulita

# REGISTRAZIONE E AUTENTICAZIONE UTENTI
def registra_utente(username: str, password: str) -> bool:
    """
    Registra un nuovo utente nel database con password hashata.
    Il controllo di unicita' e' case-insensitive ("Daniele" e "daniele" coincidono).
    Restituisce True se la registrazione riesce, False se l'username e' gia' in uso.
    """
    user_pulito, pass_pulita = valida_credenziali(username, password)
    try:
        with closing(connetti()) as conn, conn:
            cursor = conn.cursor()

            # Verifica esistenza case-insensitive prima dell'inserimento
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
    """
    Verifica le credenziali di accesso in modo case-insensitive sullo username.
    Restituisce lo username canonico salvato nel DB se il login ha successo,
    altrimenti None.
    """
    user_pulito = username.strip()
    pass_pulita = password.strip()
    # Limita la lunghezza prima di calcolare l'hash: nessuna password valida supera 64 caratteri
    if not user_pulito or not pass_pulita or len(pass_pulita) > 64:
        return None

    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT username, password FROM utenti WHERE LOWER(username) = LOWER(?)
            ''',
            (user_pulito,),
        )
        utente = cursor.fetchone()

        if utente is None:
            return None

        username_canonico, password_salvata = utente

        if verifica_hash(pass_pulita, password_salvata):
            return username_canonico
        return None

# AGGIORNAMENTO STATISTICHE E SALVATAGGIO PARTITE
def aggiorna_statistiche_vittoria(username: str, giri: int) -> None:
    """
    Incrementa partite giocate e vinte per il vincitore e aggiorna
    'record_turni' se la partita e' stata vinta in meno giri rispetto al record.
    """
    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()

        # Recupera il record attuale (NULL se l'utente non ha mai vinto prima)
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
    Incrementa il contatore 'partite_giocate' per un utente che ha partecipato
    senza vincere. Solleva 'ValueError' se l'utente non esiste nel database.
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


def salva_eventi(eventi: list, vincitore: str, giro_vittoria: int) -> None:
    """
    Salva in un'unica transazione il riepilogo della partita in 'partite'
    e tutti i singoli eventi cronologici in 'registro_eventi'.
    """
    if not eventi:
        return

    data_ora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp = datetime.now().isoformat(timespec="seconds")

    with closing(connetti()) as conn, conn:
        cursor = conn.cursor()

        # Inserisce l'intestazione della partita e recupera l'ID
        cursor.execute(
            """
            INSERT INTO partite (data_ora, vincitore, turni_totali)
            VALUES (?, ?, ?)
            """,
            (data_ora, vincitore, giro_vittoria),
        )
        partita_id = cursor.lastrowid

        # Inserisce ogni singolo evento collegandolo alla partita tramite 'partita_id'
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

# CONSULTAZIONE CLASSIFICA E STORICO
def ottieni_highscore() -> List[Tuple[str, int, int, Optional[int]]]:
    """
    Recupera tutti gli utenti ordinati per:
    1. Numero di vittorie decrescente
    2. Record di giri per vincere crescente (COALESCE sposta i NULL in fondo)
    Restituisce: [(username, partite_giocate, partite_vinte, record_turni), ...]
    """
    with closing(connetti()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT username, partite_giocate, partite_vinte, record_turni
            FROM utenti
            ORDER BY partite_vinte DESC, COALESCE(record_turni, 999999) ASC
            '''
        )
        return cursor.fetchall()


def ottieni_storico_partite(limite: int = 20) -> List[Tuple[int, str, str, int]]:
    """
    Restituisce le ultime 'limite' partite concluse dalla piu' recente:
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
    Restituisce tutti gli eventi di una specifica partita in ordine cronologico:
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
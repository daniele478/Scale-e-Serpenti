import sqlite3
import hashlib  #serve per creare l'hash della password
import hmac     #serve per confrontare gli hash in modo sicuro
import secrets  #serve per generare un salt casuale
from typing import List, Tuple

db_nome="scale_serpenti.db"

#Numero di "giri" usati per creare l'hash.
#Piu' e' alto, piu' la password e' difficile da indovinare, ma il login e' piu' lento.
ITERAZIONI_HASH = 260000
def connetti ():
    #Crea la connessione al db e abilita le chiavi
    conn = sqlite3.connect(db_nome)
    return conn

def  crea_tabelle() -> None:
    #Crea le tabelle
    conn = connetti()
    cursor = conn.cursor()

    #Tabella Utenti
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS utenti (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        partite_giocate INTEGER DEFAULT 0,
        partite_vinte INTEGER DEFAULT 0,
        record_turni INTEGER DEFAULT NULL
        )
    ''')

    #Tabella Registro Eventi
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS registro_eventi(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        turno INTEGER,
        descrizione TEXT
        )
    ''')

    conn.commit()
    conn.close()

#GESTIONE UTENTI E LOGIN

#Crea l'hash della password con un salt casuale.
#Il risultato e' una stringa da salvare nel database al posto della password.
def genera_hash(password: str) -> str:
    salt = secrets.token_bytes(16)  #salt casuale di 16 byte
    hash_password = hashlib.pbkdf2_hmac(
        "sha256",                  #algoritmo usato
        password.encode("utf-8"),  #password trasformata in byte
        salt,                      #salt casuale
        ITERAZIONI_HASH            #numero di ripetizioni
    )
    #Salvo algoritmo, iterazioni, salt e hash separati da "$"
    return f"pbkdf2_sha256${ITERAZIONI_HASH}${salt.hex()}${hash_password.hex()}"

#Controlla se la password inserita corrisponde all'hash salvato
def verifica_hash(password: str, hash_salvato: str) -> bool:
    try:
        #Divido la stringa salvata nelle sue 4 parti
        algoritmo, iterazioni, salt_hex, hash_hex = hash_salvato.split("$")

        if algoritmo != "pbkdf2_sha256":
            return False

        #Rifaccio l'hash usando lo stesso salt e le stesse iterazioni
        hash_password = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterazioni)
        )
        #compare_digest confronta i due hash in modo sicuro
        return hmac.compare_digest(hash_password.hex(), hash_hex)

    except (ValueError, TypeError, AttributeError):
        #Se la stringa salvata e' rovinata o nel formato sbagliato
        return False

def registra_utente(username: str, password: str) -> bool:
    conn = connetti()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO utenti (username, password, partite_giocate, partite_vinte, record_turni) 
        VALUES (?,?,0,0,NULL)   
        ''', (username, genera_hash(password)))
        conn.commit()
        conn.close()
        return  True
    except sqlite3.IntegrityError:
        conn.close()
        return False 

def verifica_login(username: str, password: str) -> bool:
    #Verifica credenziali di accesso
    conn = connetti()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT password FROM utenti WHERE username = ?
    ''', (username,))
    utente = cursor.fetchone()

    #Utente non trovato
    if utente is None:
        conn.close()
        return False

    password_salvata = utente[0]

    #Caso vecchio database: password salvata in chiaro (senza "$")
    if "$" not in password_salvata:
        if password == password_salvata:
            #Aggiorno subito la riga con l'hash, cosi' la prossima volta e' protetta
            cursor.execute(
                'UPDATE utenti SET password = ? WHERE username = ?',
                (genera_hash(password), username)
            )
            conn.commit()
            conn.close()
            return True

        conn.close()
        return False

    #Caso normale: confronto la password inserita con l'hash salvato
    esito = verifica_hash(password, password_salvata)
    conn.close()
    return esito

def aggiorna_statistiche_vittoria(username: str, turni: int) -> None:
    conn = connetti()
    cursor = conn.cursor()

    #Record attuale
    cursor.execute('SELECT record_turni FROM utenti WHERE username = ?', (username,))
    risultato = cursor.fetchone()
    
    if risultato:
        record = risultato[0]
        #Se non ha record o se il record dev'essere aggiornato
        if record is None or turni < record:
            nuovo_record = turni
        else:
            nuovo_record = record

        cursor.execute('''
            UPDATE utenti
            SET partite_giocate = partite_giocate +1,
                partite_vinte = partite_vinte +1,
                record_turni = ?
            WHERE username = ?
        ''', (nuovo_record,username))
        conn.commit()
    conn.close()

def aggiorna_statistiche_sconfitta(username:str) -> None:
    #Incrementa per i giocatori che hanno perso
    conn = connetti()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE  utenti
        SET partite_giocate = partite_giocate + 1
        WHERE username = ?
    ''', (username,)) 
    #la virgola per far capire che mi riferisco a una tupla
    #senza py penserebbe che voglio una stringa 'U''S''E''R'...
    conn.commit()
    conn.close()

def salva_eventi(registro_eventi: List[str]) -> None:
    #Salva cronologia eventi singola partita
    conn = connetti()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM registro_eventi')
    for i, evento in enumerate(registro_eventi, 1):
        cursor.execute('''
            INSERT INTO registro_eventi (turno,descrizione)
            VALUES (?,?)
        ''', (i, evento))
    conn.commit()
    conn.close()

def ottieni_highscore() -> List[Tuple[str, int, int]]:
    """
    Recupera tutti gli utenti dal db ordinati per:
    1. Maggior numero di vittorie
    2. Minor numero di turni impiegati per vincere
    Restituisce una lista di tuple (username, partite_giocate, partite_vinte, record_turni)
    """
    conn = connetti() 
    #crea connessione tra py e db
    cursor = conn.cursor()
    #puntatore che viagga nel db per esguire operazioni e riporare i risultati
    cursor.execute('''
        SELECT username, partite_giocate, partite_vinte, record_turni
        FROM utenti
        ORDER BY partite_vinte DESC, COALESCE(record_turni, 999999) ASC
    ''')
    #l'ordine scritto in linguaggio SQL
    #COALESCE = trasforma i valori NULL in 999999 per metterli ultimi in posizione

    risultati = cursor.fetchall()
    conn.close()

    return risultati
import sqlite3
from typing import List, Tuple

db_nome="scale_serpenti.db"
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
def registra_utente(username: str, password: str) -> bool:
    conn = connetti()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO utenti (username, password, partite_giocate, partite_vinte, record_turni) 
        VALUES (?,?,0,0,NULL)   
        ''', (username, password))
        conn.commit()
        conn.close()
        return  True
    except sqlite3.IntegrityError:
        conn.close()
        return False 

def veerifica_login(username: str, password: str) -> bool:
    #Verifica credenziali di accesso
    conn = connetti()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM utenti WHERE username = ? AND password = ?
    ''', (username, password))
    utente = cursor.fetchone()
    conn.close()
    return utente is not None

def aggiorna_statistiche_vittoria(username: str, turni: int) -> None:
    conn = connetti()
    cursor = conn.cursor()

    #Record attuale
    cursor.execute('SELECT record FROM utenti WHERE username = ?', (username))
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

def aggiorna_statistiche_sconfitta(username:str, turni:int) -> None:
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
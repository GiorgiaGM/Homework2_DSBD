from confluent_kafka import Producer
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import time
import mysql.connector
import yfinance as yf
from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
import os
import json

# Recupera l'host del database da una variabile d'ambiente
MYSQL_HOST = os.getenv('MYSQL_HOST', 'host.docker.internal') 
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'db')
MYSQL_PORT = os.getenv('MYSQL_PORT', 3306) 


# Configurazione del Kafka producer
KAFKA_BROKER = "kafka-broker-1:9092,kafka-broker-2:9092,kafka-broker-3:9092"
KAFKA_TOPIC = "to-alert-system"   # Il topic su cui inviare i messaggi

producer_config = {
    'bootstrap.servers': KAFKA_BROKER,  # Indirizzo del broker Kafka
    'acks': 'all'  # Garantisce che il messaggio venga scritto correttamente
}

producer = Producer(producer_config)  # Crea un'istanza del producer




def get_tickers_from_database():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT ticker FROM users")
    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tickers           # Si crea una lista con i valori, per esempio : ['AAPL', 'TSLA', 'MSFT']

def fetch_data_from_yfinance(ticker):
    stock = yf.Ticker(ticker)     # Crea un oggetto Ticker utilizzando la libreria yfinance
    hist = stock.history(period="1d",interval="1m")
    if hist.empty:
        raise Exception(f"Nessun dato disponibile per {ticker}")
    latest_row = hist.iloc[-1]    # estrae l'ultima riga (la più recente)
    return {
        "value": latest_row["Close"],  # valore di chiusura
        "timestamp": latest_row.name.to_pydatetime()
    }


def store_financial_data_in_database(ticker, timestamp, value):
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT, 
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,  
        database=MYSQL_DATABASE
    )
    cursor = conn.cursor()

    value = float(value)

    cursor.execute("""
        INSERT INTO financial_data (ticker, timestamp, value)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE value = VALUES(value)   
    """, (ticker, timestamp, value))
    conn.commit()
    conn.close()


def send_kafka_notification(topic, message):
    """
    Invia un messaggio JSON a un topic Kafka.
    """
    try:
        # Produce il messaggio sul topic specificato
        producer.produce(topic, json.dumps(message))
        producer.flush()  # Assicura che il messaggio venga inviato
        print(f"Notifica inviata a Kafka topic '{topic}': {message}")
    except Exception as e:
        print(f"Errore nell'invio della notifica Kafka: {e}")



# Inizializzo del Circuit Breaker
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

while True:
    print("Avvio del ciclo di raccolta dati...")
    tickers = get_tickers_from_database()
    for ticker in tickers:
        try:
            data = circuit_breaker.call(fetch_data_from_yfinance, ticker)
            store_financial_data_in_database(ticker, data["timestamp"], data["value"])
            print(f"Dati salvati per {ticker}: {data}")
        except CircuitBreakerOpenException:
            print(f"Circuito aperto per {ticker}. Richiesta saltata.")
        except Exception as e:
            print(f"Errore per {ticker}: {e}")



    # Invia una notifica al topic Kafka "to-alert-system", viene inviato il messaggio alla fine di ogni ciclo dopo aver aggiornato i dati.
    message = {
        "status": "completed",
        "message": "Aggiornamento dei valori ticker completato.",
        "updated_tickers": tickers,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    send_kafka_notification(KAFKA_TOPIC, message)

    print("Fine del ciclo. Aspetto prima del prossimo ciclo...")
    time.sleep(120)  # Aspetta 2 minuti
    
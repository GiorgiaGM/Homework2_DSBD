from confluent_kafka import Consumer, Producer
import mysql.connector
import json
import os

# Configurazione di Kafka per il consumatore e produttore
KAFKA_TOPIC_CONSUMER = 'to-alert-system'
KAFKA_TOPIC_PRODUCER = 'to-notifier'

consumer_config = {
    'bootstrap.servers': "kafka-broker-1:9092,kafka-broker-2:9092,kafka-broker-3:9092",
    'group.id': 'alert-system-group',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'auto.commit.interval.ms': 5000
}

producer_config = {
    'bootstrap.servers': "kafka-broker-1:9092,kafka-broker-2:9092,kafka-broker-3:9092"
}

# Configurazione del database MySQL
MYSQL_HOST = os.getenv('MYSQL_HOST', 'host.docker.internal')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'db')
MYSQL_PORT = os.getenv('MYSQL_PORT', 3306)

# Crea il consumatore e il produttore Kafka
consumer = Consumer(consumer_config)
producer = Producer(producer_config)


def get_ticker_value_from_db(ticker):
    """
    Recupera l'ultimo valore del ticker dal database.
    """
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT
        )
        cursor = conn.cursor()

        # Ottieni l'ultimo valore per il ticker
        cursor.execute("""
            SELECT value 
            FROM financial_data 
            WHERE ticker = %s 
            ORDER BY timestamp DESC LIMIT 1
        """, (ticker,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]  # valore più recente del ticker
        else:
            return None
    except mysql.connector.Error as err:
        print(f"Errore durante il recupero del valore del ticker dal database: {err}")
        return None



def check_profile_and_send_alert(email, ticker,current_value,condition):
    """
    Verifica se il valore del ticker supera le soglie e invia un alert.
    """
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=MYSQL_PORT
        )
        cursor = conn.cursor()

        # Esegui la query per ottenere il valore del ticker e le soglie
        cursor.execute("""
            SELECT ticker, high_value, low_value
            FROM users
            WHERE email = %s
        """, (email,))
        result = cursor.fetchone()

        if result:
            ticker_db, high_value, low_value = result
            # Controlla se il valore supera la soglia
            if ticker_db == ticker:
                if high_value is not None and current_value >= high_value:
                    send_alert(email, ticker, "high-value exceeded")
                elif low_value is not None and current_value <= low_value:
                    send_alert(email, ticker, "low-value exceeded")
            
        conn.close()
    except Exception as e:
        print(f"Errore durante la verifica del profilo: {e}")

def send_alert(email, ticker, condition):
    """
    Invia un messaggio al topic 'to-notifier' con i dettagli dell'alert.
    """
    message = {
        'email': email,
        'ticker': ticker,
        'condition': condition
    }
    producer.produce(KAFKA_TOPIC_PRODUCER, json.dumps(message))
    producer.flush()
    print(f"Alert inviato a {email} per {ticker}: {condition}")

def process_message(msg):
    """
    Processa il messaggio dal topic 'to-alert-system'.
    """
    data = json.loads(msg.value().decode('utf-8'))

    if data.get('status') == 'completed':
        print(f"Fase di aggiornamento completata per i tickers: {data.get('updated_tickers')}")
        return


    # Estrai le informazioni dal messaggio
    email = data.get('email')
    ticker = data.get('ticker')
    
    # Recupera l'ultimo valore del ticker dal database
    current_value = get_ticker_value_from_db(ticker)
    if current_value is not None:
        # Verifica se la condizione è soddisfatta per l'utente
        check_profile_and_send_alert(email, ticker, current_value, "high")
        check_profile_and_send_alert(email, ticker, current_value, "low")
    else:
        print(f"Nessun valore disponibile per il ticker {ticker}.")

def main():
    # Sottoscrivi al topic Kafka
    consumer.subscribe([KAFKA_TOPIC_CONSUMER])

    try:
        while True:
            # Polling dei messaggi da Kafka
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            # Elabora il messaggio ricevuto
            process_message(msg)

    except KeyboardInterrupt:
        print("Alert System interrotto dall'utente.")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()

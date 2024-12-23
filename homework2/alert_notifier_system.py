from confluent_kafka import Consumer
import smtplib
from email.message import EmailMessage
import json

# Kafka consumer configuration
consumer_config = {
    'bootstrap.servers': "kafka-broker-1:9092,kafka-broker-2:9092,kafka-broker-3:9092",  
    'group.id': 'notifier-system-group',  # Consumer group ID
    'auto.offset.reset': 'earliest'  # Start reading from the earliest offset if no committed offset is available
}

consumer = Consumer(consumer_config)
topic = 'to-notifier'  # Kafka topic for notifications
consumer.subscribe([topic])

# Email configuration
SMTP_SERVER = 'smtp.gmail.com'  # SMTP server (example: Gmail)
SMTP_PORT = 587  # SMTP port for TLS
EMAIL_ADDRESS = 'a.barbasola@gmail.com'  # Your email address
EMAIL_PASSWORD = 'password'  # Your email password

def send_email(to_email, subject, body):
    """
    Sends an email using the specified parameters.
    """
    try:
        msg = EmailMessage()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.set_content(body)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Enable TLS
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)  # Login to the SMTP server
            server.send_message(msg)  # Send the email
            print(f"Email sent to {to_email} with subject '{subject}'.")
    except Exception as e:
        print(f"Error sending email to {to_email}: {e}")

def alert_notifier_system():
    """
    Consumes messages from the Kafka topic and sends alerts via email.
    """
    try:
        while True:
            msg = consumer.poll(1.0)  # Poll for new messages (wait up to 1 second)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            # Decode and process the message
            try:
                message_value = json.loads(msg.value().decode('utf-8'))
                email = message_value['email']
                ticker = message_value['ticker']
                condition = message_value['condition']

                # Compose the email
                subject = f"Alert for {ticker}"
                body = f"Condition triggered: {condition}"
                
                # Send the email
                send_email(email, subject, body)
            except Exception as e:
                print(f"Error processing message: {e}")

    except KeyboardInterrupt:
        print("AlertNotifierSystem interrupted by user.")
    finally:
        consumer.close()

if __name__ == "__main__":
    alert_notifier_system()

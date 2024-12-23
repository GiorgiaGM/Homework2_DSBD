from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaConsumer

# Configurazione del broker Kafka
bootstrap_servers = ['localhost:19092', 'localhost:29092', 'localhost:39092']
topic_name = 'to-alert-system'  
num_partitions = 3  
replication_factor = 3  

def list_topics_and_details():
    consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
    topics = consumer.topics()  
    print("\nTopic disponibili e dettagli:")

    for topic in sorted(topics):
        partitions = consumer.partitions_for_topic(topic)
        if partitions:
            print(f"\nTopic: {topic}")
            print(f"  Partizioni: {len(partitions)}")
            print("  Dettagli delle partizioni:")
            for partition in sorted(partitions):
                print(f"    Partizione {partition}")
        else:
            print(f"\nTopic: {topic}")
            print("  Nessuna informazione sulle partizioni disponibile.")

    consumer.close()

def create_topic_if_not_exists(topic_name, num_partitions, replication_factor):
    """Crea un topic se non esiste già."""
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers, client_id='topic-creator')
    consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
    
    if topic_name in consumer.topics():
        print(f"\nIl topic '{topic_name}' esiste già.")
        consumer.close()
        admin_client.close()
        return
    
    # Viene creato il topic
    topic = NewTopic(
        name=topic_name,
        num_partitions=num_partitions,
        replication_factor=replication_factor
    )
    try:
        print(f"\nCreazione del topic '{topic_name}'...")
        admin_client.create_topics(new_topics=[topic], validate_only=False)
        print(f"Topic '{topic_name}' creato con successo con {num_partitions} partizioni e {replication_factor} repliche.")
    except Exception as e:
        print(f"Si è verificato un errore durante la creazione del topic: {e}")
    finally:
        consumer.close()
        admin_client.close()

if __name__ == "__main__":
    list_topics_and_details()

    create_topic_if_not_exists(topic_name, num_partitions, replication_factor)

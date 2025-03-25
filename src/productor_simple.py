from confluent_kafka import Producer

# Callback function to handle delivery reports
def delivery_report(err, msg):
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

# Initialize the Kafka producer
producer = Producer({'bootstrap.servers': 'kafka-server:9092'})

# Produce a message to the Kafka topic
producer.produce('STopic', key='The key', value='The value', callback=delivery_report)
producer.flush()  # Ensure all messages are sent

print("Message sent successfully!")
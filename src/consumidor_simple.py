from confluent_kafka import Consumer, KafkaException

# Initialize the Kafka consumer
consumer = Consumer({
    'bootstrap.servers': 'kafka-server:9092',
    'group.id': 'my-group',
    'auto.offset.reset': 'earliest'
})

# Subscribe to the Kafka topic
consumer.subscribe(['STopic'])

# Consume messages from the Kafka topic
try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                print(f"End of partition reached {msg.partition()}")
            elif msg.error():
                raise KafkaException(msg.error())
        else:
            print(f"Received message. Key= {msg.key().decode('utf-8')}; Value= {msg.value().decode('utf-8')}")
except KeyboardInterrupt:
    pass
finally:
    consumer.close()
from confluent_kafka import Producer
import random
import json
import time
from datetime import datetime

# Configuración del productor de Kafka
conf = {
    'bootstrap.servers': 'kafka-server:9092',  # Cambia esto según tu configuración de Kafka
}

producer = Producer(**conf)

def delivery_report(err, msg):
    """ Callback para reportar la entrega de mensajes """
    if err is not None:
        print(f'Error al entregar el mensaje: {err}')
    else:
        print(f'Mensaje entregado a {msg.topic()} [{msg.partition()}]')

# Generar y enviar mensajes a Kafka
for _ in range(1000):  # Generar 10 mensajes como ejemplo
    num1 = random.randint(1, 100)
    num2 = random.randint(1, 100)
    operation = random.choice(['sum', 'sub'])
    # message = [num1, num2, operation]
    message = {'time':str(datetime.now()), 'operator_1':num1, 'operator_2':num2, 'operation':operation}

    # Convertir el mensaje a formato JSON
    message_json = json.dumps(message)
    
    # Enviar el mensaje al topic "Ops"
    producer.produce('Ops', value=message_json, callback=delivery_report)
    
    # Esperar un poco antes de enviar el siguiente mensaje
    time.sleep(5)

# Esperar a que todos los mensajes sean entregados
producer.flush()
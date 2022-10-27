# kafka_python

Creamos el servidor Kafka, llamado "kafka_server" en la red "kafka-net".

```shell
docker network create kafka-net
docker run -d --name zookeeper --network kafka-net -e ALLOW_ANONYMOUS_LOGIN=yes bitnami/zookeeper
docker run --rm -it --network kafka-net --name kafka_server -e ALLOW_PLAINTEXT_LISTENER=yes -e KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181 bitnami/kafka
```

Se edita kafka_python/config.yaml para que el broker sea kafka_server:9092. El topic, común para productor y consumidor es "python_2". 
```shell
PYTHON_1:
  BROKER: 'kafka_server:9092'
  PRODUCER: 'python_2'

PYTHON_2:
  BROKER: 'kafka_server:9092'
  CONSUMER: 'python_2'
``` 
 
Se reconstruye la imagen con el Dockerfile incluido

```shell
docker build -t 'image_name' .
```

En un terminal ejecutamos el productor

```shell
docker run -it --rm --network kafka-net kafka_python bash
cd src
python python1.py 5 2 sum
```

Y en otro terminal lanzamos el consumidor

```shell
/kafka_python/src# python python2.py 0
Starting Consumer with client id :  0
Received message: b'{"operator_1": "5", "operator_2": "2", "operation": "sum"}'
Going to decode message::  b'{"operator_1": "5", "operator_2": "2", "operation": "sum"}'
Result of operation sum is ::: 7
```

Nota: ha sido necesario cambiar los ficheros
 
Y en src/python1.py, python2.py la línea “topic_list = yaml.load(ymlfile, Loader=yaml.FullLoader” 
 
 
Cosas a mejorar en config.yml

No se entiende bien que sea una lista de topics. En realidad es info de un bróker y un topic común. Podría quedar más sencillo. El cambio supone retocar el código de python1 y python2. 
Si se lanza primero el consumidor, falla porque el topic no existe. Hay que lanzar primero el productor (o ver si se puede crear el topic al lanzar Kafka). 

IMPORTANTE: intentar pasar la información al contenedor cliente usando volúmenes, en vez de tener que cambiar la imagen cada vez. 
 
Repositorio original: https://medium.com/nerd-for-tech/python-and-kafka-message-passing-and-more-44ccb4f1576c 

## PROYECTO: 

Hacer un consumidor MQTT que sea productor KAFKA. Integrarlo con ksqlDB. 


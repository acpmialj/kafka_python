# kafka_python
## Primera fase: clonar el repositorio y construir la imagen Kafka para productor y consumidor
Con el Dockerfile incluido construimos una imagen que servirá tanto para el productor como para el consumidor. Básicamente se parte de una imagen con Python y se le añaden los paquetes necesarios: numpy, confluent-kafka (el cliente de Kafka), PyYAML (para leer ficheros YAML) y requests (para hacer transacciones HTTP).

```shell
docker build -t kafka_python .
```

Durante la construcción de la imagen se incorpora un fichero de configuración para nuestra aplicación, kafka_python/config.yaml. En él facilitamos la dirección del servicio Kafka, tanto al productor como al consumidor (kafka_server:9092). Además establecemos el tema de los eventos que nuestra aplicación va a intercambiar: "My_Topic". 
```shell
PRODUCER:
  BROKER: 'kafka_server:9092'
  TOPIC: 'My_Topic'

CONSUMER:
  BROKER: 'kafka_server:9092'
  TOPIC: 'My_Topic'
``` 

## Segunda fase: lanzar el clúster Kafka 
Creamos un clúster Kafka con un único servidor, llamado "kafka_server" en la red "kafka-net". Para su funcionamiento necesita un clúster ZooKeeper -- en este caso, con un único nodo.

```shell
docker network create kafka-net
docker run --rm -d --name zookeeper --network kafka-net -e ALLOW_ANONYMOUS_LOGIN=yes bitnami/zookeeper
docker run --rm -d --network kafka-net --name kafka_server -e ALLOW_PLAINTEXT_LISTENER=yes -e KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181 bitnami/kafka
```

## Tercera fase: lanzar PRODUCTOR
En otro terminal lanzamos el contenedor que va a producir eventos. Está basado en el contenedor kafka_python creado en la primera fase.

```shell
docker run -it --rm --network kafka-net kafka_python bash
```
Una vez en el shell del productor, lanzamos el programa que genera un evento:

```shell
cd src
python productor.py 5 7 sum
Message produced: b'{"time": "2024-06-14 08:42:56.001910", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
```
El productor termina inmediatamente. El evento con contenido <hora, 5, 7, sum> queda almacenado en Kafka.

## Cuarta fase: lanzar CONSUMIDOR
En un terminal nuevo, ejecutamos el contenedor que va a hacer de consumidor de evento. Está basado en el contenedor kafka_python creado en la primera fase.

```shell
docker run -it --rm --network kafka-net kafka_python bash
```
Una vez estamos en el shell del consumidor, lanzamos el programa que queda a la espera de eventos. Nótese que el programa consumidor, "consumidor.py", necesita un argumento: su identificador de cliente. 

```shell
cd src
python consumidor.py 0
Starting Consumer with client id :  0
```
El consumidor se asocia al terminal. Según vayamos recibiendo eventos irán apareciendo mensajes por el mismo. Si no hemos tardado mucho en lanzarlo, se consumirá de forma inmediata el evento generado por el productor, así que veremos:

```shell
Starting Consumer with client id :  0
Received message: b'{"time": "2024-06-14 08:42:56.001910", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
Going to decode message::  b'{"time": "2024-06-14 08:42:56.001910", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
Result of operation sum is ::: 12
```
NOTA 1: si lanzamos el consumidor antes que el productor se producirá un error debido a que el tema ("My_Topic") aún no existe. 

NOTA 2: si hay mensajes almacenados en el tema "My_topic", el consumidor leerá solamente los nuevos, porque el parámetro "auto.offset.reset" del cliente consumidor se ha establecido como "latest" en el fichero transactions/kafkaConsumer.py. Si queremos procesar los mensajes almacenados, podemos cambiar la línea correspondiente de código para que sea:
```
        'default.topic.config': {'auto.offset.reset': 'earliest'}
```

## Observación de los mensajes en Kafka
Se puede usar el comando kafka-console-consumer.sh en el contenedor kafka_server para observar los mensajes almacenados:
```shell
docker exec -it kafka_server kafka-console-consumer.sh --bootstrap-server kafka_server:9092 --topic My_Topic --from-beginning
```

También se puede lanzar un contenedor "kafdrop" que nos permite examinar el almacén Kafka con una interfaz webUI. Nótese la especificación de la red ("kafka-net") y del servidor Kafka ("kafka_server:9092"). El nombre lo hemos puesto al lanzar Kafka, y el puerto es el usado por omisión. La interfaz de usuario de Kafdrop está en http://localhost:9000 -- esto es, puerto 9000 del anfitrión. 

```shell
docker run -d --rm -p 9000:9000 --name kafdrop --network kafka-net \
    -e KAFKA_BROKERCONNECT=kafka_server:9092 \
    -e JVM_OPTS="-Xms32M -Xmx64M" \
    -e SERVER_SERVLET_CONTEXTPATH="/" \
    obsidiandynamics/kafdrop:latest
```
## Limpieza
Todos los contenedores han sido lanzados con "--rm", por lo tanto se pueden parar con "docker stop" y se eliminan automáticamente. 

Queda creada la red "kafka-net" (ver con "docker network ls"). Se puede eliminar con "docker network rm kafka-net". 

## Comentarios y posibles mejoras:

1. Se podría pasar la información al contenedor cliente (los programas) usando volúmenes, en vez de tener que cambiar la imagen cada vez que se edita un fichero.  

docker run -it --rm --network kafka-net -v $HOME/kafka_python:/kafka_python kafka_python bash

Hecho esto, en el Dockerfile sobraría la línea "ADD ./ /kafka_python"

2. Sería interesante automatizar todo el proceso usando docker compose.
3. Si queremos que el consumidor lea los temas desde el principio, es necesario crear un nuevo grupo de consumidores, 'group_id', y definir en transactions/kafkaConsumer.py que la configuración 'auto.offset.reset' tiene el valor 'earliest' (vs. 'latest'). Es así porque la configuración de offset va ligada al grupo de consumidores, y es al crear el grupo (la primera vez que se usa) cuando se hace esta asociación. En el código, el 'group_id' se define en src/consumidor.py, en la llamada a kafkaConsumer(... 'group1' ...).
 
## Fuente
Repositorio original: https://medium.com/nerd-for-tech/python-and-kafka-message-passing-and-more-44ccb4f1576c 



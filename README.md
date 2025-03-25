# kafka_python
## Primera fase: clonar el repositorio y construir la imagen Kafka para productor y consumidor
Con el Dockerfile incluido construimos una imagen que servirá tanto para el productor como para el consumidor. Básicamente se parte de una imagen con Python y se le añaden los paquetes necesarios: numpy, confluent-kafka (el cliente de Kafka), PyYAML (para leer ficheros YAML) y requests (para hacer transacciones HTTP).

```shell
docker build -t kafka_python .
```

Durante la construcción de la imagen se incorpora un fichero de configuración para nuestra aplicación, kafka_python/config.yaml. En él facilitamos la dirección del servicio Kafka, tanto al productor como al consumidor (kafka_server:9092). Además establecemos el tema de los eventos que nuestra aplicación va a intercambiar: "My_Topic". 
```shell
PRODUCER:
  BROKER: 'kafka-server:9092'
  TOPIC: 'My_Topic'

CONSUMER:
  BROKER: 'kafka-server:9092'
  TOPIC: 'My_Topic'
``` 

## Segunda fase: lanzar el clúster Kafka 
Creamos un clúster Kafka con un único servidor, llamado "kafka_server" en la red "kafka-net". La versión de Kafka que se usa no necesita un servidor ZooKeeper externo (versiones anteriores sí que lo necesitan).

```shell
docker network create kafka-net
docker run -d --name kafka-server --hostname kafka-server \
    --network kafka-net \
    -e KAFKA_CFG_NODE_ID=0 \
    -e KAFKA_CFG_PROCESS_ROLES=controller,broker \
    -e KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
    -e KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \
    -e KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=0@kafka-server:9093 \
    -e KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER \
    bitnami/kafka:latest
```

## Tercera fase: lanzar PRODUCTOR
Lanzamos el contenedor que va a producir eventos. Está basado en el contenedor kafka_python creado en la primera fase.

```shell
docker run -it --rm --network kafka-net kafka_python bash
```
Una vez en el shell del productor, lanzamos el programa que genera un evento, que consta de dos números y una operación ("sum" o "sub").

```shell
cd src
python productor.py 5 7 sum
```
El productor termina inmediatamente. 
```
Message produced: b'{"time": "2025-03-25 13:58:08.965636", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
```
El evento con contenido <5, 7, sum> queda almacenado en Kafka.

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
Received message: b'{"time": "2025-03-25 14:01:45.593731", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
Going to decode message::  b'{"time": "2025-03-25 14:01:45.593731", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
Result of operation sum is ::: 12
```
NOTA: si lanzamos el consumidor antes que el productor se producirá un error debido a que el tema ("My_Topic") aún no existe. 

## Observación de los mensajes en Kafka
Se puede lanzar un contenedor "kafdrop" que nos permite examinar el almacén Kafka. Nótese la especificación de la red ("kafka-net") y del servidor Kafka ("kafka_server:9092"). El nombre lo hemos puesto al lanzar Kafka, y el puerto es el usado por omisión. La interfaz de usuario de Kafdrop está en http://localhost:9000 -- esto es, puerto 9000 del anfitrión. 

```shell
docker run -d --rm -p 9000:9000 --name kafdrop --network kafka-net \
    -e KAFKA_BROKERCONNECT=kafka-server:9092 \
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

2. En el directorio src hay también un "productor_simple.py" y un "consumidor_simple.py" que sirven como ejemplos de operaciones sencillas de envío / suscripción. 

3. Si queremos que un consumidor lea los temas desde el principio, es necesario crear un nuevo grupo de consumidores, 'group_id', y definir en transactions/kafkaConsumer.py que la configuración 'auto.offset.reset' tiene el valor 'earliest' (vs. 'latest'). Es así porque la configuración de offset va ligada al grupo de consumidores, y es al crear el grupo (la primera vez que se usa) cuando se hace esta asociación. En el código, el 'group_id' se define en src/consumidor.py, en la llamada a kafkaConsumer(... 'group1' ...).
 
## Fuente
Repositorio original: https://medium.com/nerd-for-tech/python-and-kafka-message-passing-and-more-44ccb4f1576c 



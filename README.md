# kafka_python
## Primera parte: construir la imagen kafka_python para productor y consumidor

Se edita el fichero de configuración para nuestra aplicación, kafka_python/config.yaml. En él indicamos la dirección del server tanto para el productor como para el consumidor (kafka_server:9092). Además establecemos el tema, "My_Topic". 
```shell
PRODUCER:
  BROKER: 'kafka_server:9092'
  TOPIC: 'My_Topic'

CONSUMER:
  BROKER: 'kafka_server:9092'
  TOPIC: 'My_Topic'
``` 

Con el Dockerfile incluido construimos una imagen que servirá tanto para el productor como para el consumidor. Básicamente se parte de una imagen con Python y se le añaden los paquetes necesarios: numpy, confluent-kafka (el cliente de Kafka), PyYAML (para leer ficheros YAML) y requests (para hacer transacciones HTTP).

```shell
docker build -t kafka_python .
```

## Segunda parte: lanzar el clúster Kafka 
Creamos el servidor Kafka, llamado "kafka_server" en la red "kafka-net". Para su funcionamiento necesita un clúster ZooKeeper -- en este caso, con un único nodo.

```shell
docker network create kafka-net
docker run --rm -d --name zookeeper --network kafka-net -e ALLOW_ANONYMOUS_LOGIN=yes bitnami/zookeeper
docker run --rm -d --network kafka-net --name kafka_server -e ALLOW_PLAINTEXT_LISTENER=yes -e KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181 bitnami/kafka
```
El terminal queda asociado al segundo contenedor (el servidor Kafka), que irá emitiendo "logs". 

## Tercera parte: lanzar PRODUCTOR
En otro terminal lanzamos el contenedor que va a producir eventos:

```shell
docker run -it --rm --network kafka-net kafka_python bash
```
Una vez en el shell del productor, lanzamos el programa que genera un evento:

```shell
cd src
python productor.py 5 7 sum
```
El productor termina inmediatamente. El evento con contenido <5, 7, sum> queda almacenado en Kafka.

## Cuarta parte: lanzar CONSUMIDOR
En un terminal nuevo, ejecutamos el contenedor que va a hacer de consumidor de eventos 

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
Received message: b'{"operator_1": "5", "operator_2": "2", "operation": "sum"}'
Going to decode message::  b'{"operator_1": "5", "operator_2": "2", "operation": "sum"}'
Result of operation sum is ::: 7
```
NOTA: si lanzamos el consumidor antes que el productor se producirá un error debido a que el tema ("My_Topic") aún no existe. 

## Limpieza
Al detener los contenedore productor - consumidor - servidor Kafka, se eliminan. No pasa lo mismo con el servidor ZooKeeper. Hay que pararlo con "docker stop" y eliminarlo con "docker rm". 

Queda crada la red "kafka-net" (ver con "docker network ls"). Se puede eliminar con "docker network rm kafka-net". 

## A mejorar:

1. Pasar la información al contenedor cliente (los programas) usando volúmenes, en vez de tener que cambiar la imagen cada vez que se edita un fichero.  

docker run -it --rm --network kafka-net -v $HOME/kafka_python:/kafka_python kafka_python bash

Hecho esto, en el Dockerfile sobraría la línea "ADD ./ /kafka_python"

2. Lanzar todo con docker compose


 
## Fuente
Repositorio original: https://medium.com/nerd-for-tech/python-and-kafka-message-passing-and-more-44ccb4f1576c 



# kafka_python

## Primera fase: clonar el repositorio y construir la imagen kafka_python para ejecutar aplicaciones Python con la librería confluent-kafka

Clonamos este repositorio y pasamos al directorio kafka_python. También creamos una red docker, que usaremos para interconectar todos los contenedores:
```
git clone https://github.com/acpmialj/kafka_python.git
cd kafka_python
docker network create kafka-net
```
Con el Dockerfile incluido construimos una imagen que servirá tanto para el productor como para el consumidor. Básicamente se parte de una imagen con Python y se le añaden los paquetes necesarios: numpy, confluent-kafka (el cliente de Kafka), PyYAML (para leer ficheros YAML) y requests (para hacer transacciones HTTP). Estos paquetes están listados en "requirements.txt".

```shell
docker build -t kafka_python .
```
Durante la construcción de la imagen se incorpora un fichero de configuración para nuestra aplicación, kafka_python/config.yaml. En él facilitamos la dirección del servicio Kafka, tanto al productor como al consumidor (kafka-server:9092). Además establecemos el tema de los eventos que nuestra aplicación va a intercambiar: "My_Topic". 
```
PRODUCER:
  BROKER: 'kafka-server:9092'
  TOPIC: 'My_Topic'

CONSUMER:
  BROKER: 'kafka-server:9092'
  TOPIC: 'My_Topic'
``` 
Tras esto, se puede lanzar un entorno de ejecución python+kafka con
```
docker run -it --rm --network kafka-net kafka_python bash
```
Si se van a modificar los códigos o configuraciones, en vez de usar los predeterminados al construir la imagen, es preferible lanzar el entorno con
```
docker run -it --rm --network kafka-net -v .:/kafka_python kafka_python bash
```
Si se procede así, en el Dockerfile sobraría la línea "ADD ./ /kafka_python" (no pasa nada si está). Lo bueno es que todo lo que modifiquemos en el host será inmediatamente visible en el contenedor, y viceversa. 

## Segunda fase: lanzar el clúster Kafka 
Creamos un clúster Kafka con un único servidor, llamado "kafka-server" en la red "kafka-net". La versión de Kafka que se usa no necesita un servidor ZooKeeper externo (versiones anteriores sí que lo necesitan).

```shell
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
Lanzamos el contenedor que va a producir eventos. Está basado en el contenedor kafka_python creado en la primera fase. Una vez en el shell del productor, lanzamos el programa que genera un evento, que consta de dos números y una operación ("sum" o "sub").

```shell
docker run -it --rm --network kafka-net -v .:/kafka_python kafka_python bash
cd src
python productor.py 5 7 sum
Message produced: b'{"time": "2025-03-25 13:58:08.965636", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
```
El productor termina tras generar el evento con contenido <5, 7, sum>, que queda almacenado en Kafka.

## Cuarta fase: lanzar CONSUMIDOR
En una ventana terminal nueva, ejecutamos el contenedor que va a hacer de consumidor de evento. Desde el shell del contenedor lanzamos el programa consumidor que queda a la espera de eventos. Nótese que este programa "consumidor.py", necesita un argumento: su identificador de cliente. 

```shell
docker run -it --rm --network kafka-net -v .:/kafka_python kafka_python bash
cd src
python consumidor.py 0
Starting Consumer with client id :  0
```
El consumidor se queda en un bucle de espera infinito, del que se puede salir con Ctrl-C. Podemos, desde la ventana del PRODUCTOR, enviar otro mensaje, y veremos esto en la ventana del CONSUMIDOR:

```shell
Received message: b'{"time": "2025-03-25 14:01:45.593731", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
Going to decode message::  b'{"time": "2025-03-25 14:01:45.593731", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
Result of operation sum is ::: 12
```
NOTA: si lanzamos el consumidor antes que el productor se producirá un error debido a que el tema ("My_Topic") aún no existe. 

El consumidor tiene identificador 0 (se lo hemos pasado como argumento), y pertenece a un grupo de consumidores llamado "group1" (véase la llamada a kafkaConsumer(... 'group1' ...). en el código). Además, vemos en transactions/kafkaConsumer.py que el parámetro 'auto.offset.reset' tiene el valor 'earliest'. Eso significa que, cuando se conecte un cliente del grupo "group1", empezará a recibir eventos almacenados, a partir del último que consumió. Esto puede suponer consumir eventos almacenados previamente. Si se cambiase ese parámetro a 'latest', el consumidor recibirá los mensajes que se vayan recibiendo a partir del momento de la conexión. 

## Observación de los mensajes en Kafka
Podemos observar lo que está almacenado en kafka de diferrentes maneras. De forma visual, podemos usar un contenedor Kafdrop, ejecutado en la red kafka-net y asociado al broker kafka-server:9092. La interfaz de usuario de Kafdrop está en http://localhost:9000 -- esto es, puerto 9000 del anfitrión. 

```shell
docker run -d --rm -p 9000:9000 --name kafdrop --network kafka-net \
    -e KAFKA_BROKERCONNECT=kafka-server:9092 \
    obsidiandynamics/kafdrop:latest
```
Desde Kafdrop se puede observar cómo Kafka almacena información sobre los clientes que acceden a sus datos, así como de los "offsets" de los últimos mensajes leídos. 

## Limpieza
Todos los contenedores han sido lanzados con "--rm", por lo tanto se pueden parar con "docker stop" y se eliminan automáticamente. 

Queda creada la red "kafka-net" (ver con "docker network ls"). Se puede eliminar con "docker network rm kafka-net". 

## Clientes simples

En el directorio src hay también un "productor_simple.py" y un "consumidor_simple.py" que sirven como ejemplos de operaciones sencillas de envío / suscripción al tema "STopic". El productor se lanza desde un bash de un contenedor kafka_python, en el directorio src: 
```
python productor_simple.py
```
y el consumidor con el siguiente comando, del que se sale con Ctrl-C.  
```
python consumidor_simple.py
```
## Uso de RedPanda
Lanzamos el redpanda_compose.yaml de Redpanda. 
```
docker compose -f redpanda_compose.yaml -d up
```
Pone en marcha un clúster de un nodo, y una consola de gestión (http://localhost:8080). Se crea la red "redpanda-quickstart-one-broker_redpanda_network".

Tenemos ya creado el cliente kafka_python de la práctica con kafka. Podemos usarlo, pero modificando los programas python para que usen como broker "redpanda-0". Lo hacemos en el fichero config.yml. 
```
PRODUCER:
  BROKER: 'redpanda-0:9092'
  TOPIC: 'My_Topic'

CONSUMER:
  BROKER: 'redpanda-0:9092'
  TOPIC: 'My_Topic'
```
Tras ello podemos lanzar el consumidor, que quedará en espera. Nótese que "0" es el identificador del cliente, y recordemos que el grupo de consumidores es "group1". 
```
docker run -it --rm --network redpanda-quickstart-one-broker_redpanda_network -v .:/kafka_python kafka_python bash
cd src
python consumidor.py 0
Starting Consumer with client id :  0
```
Desde otra terminal lanzamos el productor:

```
docker run -it --rm --network redpanda-quickstart-one-broker_redpanda_network -v .:/kafka_python kafka_python bash
cd src
python productor.py 5 7 sum
Message produced: b'{"time": "2025-03-25 15:42:03.339875", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
``` 
El mensaje ha sido generado. En la terminal asociada al consumidor veremos que ha sido recibido y procesado correctamente:
```
Received message: b'{"time": "2025-03-25 15:42:03.339875", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
Going to decode message::  b'{"time": "2025-03-25 15:42:03.339875", "operator_1": "5", "operator_2": "7", "operation": "sum"}'
Result of operation sum is ::: 12
```
Podemos ver el mensaje en la consola de gestión, o desde otro terminal, ejecutando

```
docker exec -it redpanda-0 rpk topic consume My_Topic --num 1
{
  "topic": "My_Topic",
  "value": "{\"time\": \"2025-03-25 15:36:56.905323\", \"operator_1\": \"5\", \"operator_2\": \"7\", \"operation\": \"sum\"}",
  "timestamp": 1742917016905,
  "partition": 0,
  "offset": 0
}
```
Como hemos podido comprobar, RedPanda y Kafka se comportan igual de cara a los usuarios. 

Podemos hacer limpieza con
```
docker compose -f redpanda_compose.yaml down
```
### Nota
Se puede crear un contenedor RedPanda directamente, con el nombre kafka-server (para compatibilidad con el código) con este comando:
```
docker run --rm -d --network kafka-net --name kafka-server --hostname kafka-server docker.redpanda.com/redpandadata/redpanda:v24.1.7 redpanda start \
      --kafka-addr internal://0.0.0.0:9092,external://0.0.0.0:19092 \
      --advertise-kafka-addr internal://kafka-server:9092,external://localhost:19092 \
      --schema-registry-addr internal://0.0.0.0:8081,external://0.0.0.0:18081 \
      --rpc-addr kafka-server:33145 \
      --advertise-rpc-addr kafka-server:33145 \
      --mode dev-container \
      --smp 1 \
      --default-log-level=info
```
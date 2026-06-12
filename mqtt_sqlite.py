"""
@file mqtt_sqlite.py
@brief Servicio MQTT para almacenamiento de datos en SQLite.

Este módulo implementa un cliente MQTT que se conecta al broker
Mosquitto local de la Raspberry Pi para recibir los datos enviados
por los ESP32 del sistema de fermentación.

Los mensajes recibidos son procesados y almacenados en una base
de datos SQLite para mantener un registro histórico de las
variables monitoreadas.

Tópicos gestionados:
- fermentador/espExterior/datos
- fermentador/espInterior/datos

Flujo de operación:

ESP32 Exterior ----\
                     \
                      MQTT Broker --> mqtt_sqlite.py --> SQLite
                     /
ESP32 Interior -----/

@author
Fernando Plazas Trujillo

@date 2026
"""

import json
import sqlite3

from paho.mqtt import client as mqtt


## Dirección del broker MQTT.
BROKER = "localhost"

## Puerto MQTT estándar.
PORT = 1883

## Tópico MQTT utilizado por el ESP32 exterior.
TOPIC_EXTERIOR = "fermentador/espExterior/datos"

## Tópico MQTT utilizado por el ESP32 interior.
TOPIC_INTERIOR = "fermentador/espInterior/datos"

## Nombre de la base de datos SQLite.
DB_NAME = "fermentacion.db"


def guardar_exterior(data):
    """
    @brief Almacena datos provenientes del ESP32 exterior.

    Inserta en la tabla 'exterior' los valores de temperatura
    y humedad ambiente junto con su marca temporal.

    @param data Diccionario recibido desde MQTT con los datos
                del sensor exterior.

    Formato esperado:

    {
        "timestamp": "YYYY-MM-DD HH:MM:SS",
        "temp": 25.3,
        "hum": 70.2
    }

    @return None
    """

    timestamp = data["timestamp"]

    fecha, hora = timestamp.split(" ")

    temperatura = data["temp"]
    humedad = data["hum"]

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO exterior
        (
            fecha,
            hora,
            temperatura,
            humedad
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            fecha,
            hora,
            temperatura,
            humedad
        )
    )

    conn.commit()
    conn.close()

    print(
        f"Guardado -> {fecha} {hora} "
        f"T={temperatura} H={humedad}"
    )


def guardar_interior(data):
    """
    @brief Almacena datos provenientes del ESP32 interior.

    Inserta en la tabla 'interior' las variables asociadas al
    proceso de fermentación.

    Variables registradas:
    - Temperatura interna
    - pH
    - Concentración de CO2
    - Valor RAW del sensor MQ-135
    - Voltaje de batería
    - Corriente consumida

    @param data Diccionario recibido desde MQTT.

    @return None
    """

    timestamp = data["timestamp"]

    fecha, hora = timestamp.split(" ")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO interior
        (
            fecha,
            hora,
            temperatura,
            ph,
            co2,
            co2_raw,
            voltaje,
            corriente
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            fecha,
            hora,
            data["temperatura"],
            data["ph"],
            data["co2"],
            data["co2_raw"],
            data["voltaje"],
            data["corriente"]
        )
    )

    conn.commit()
    conn.close()

    print(
        f"Interior -> {fecha} {hora} "
        f"T={data['temperatura']} "
        f"pH={data['ph']} "
        f"CO2={data['co2']}"
    )


def on_connect(client, userdata, flags, rc, properties=None):
    """
    @brief Callback ejecutado al establecer conexión MQTT.

    Una vez conectado al broker, el cliente se suscribe a los
    tópicos utilizados por los ESP32 para la transmisión de datos.

    @param client Instancia del cliente MQTT.
    @param userdata Datos privados asociados al cliente.
    @param flags Indicadores de estado de conexión.
    @param rc Código de resultado de conexión.
    @param properties Propiedades MQTT v5.

    @return None
    """

    print(f"Conectando al broker MQTT ({rc})")

    client.subscribe(TOPIC_EXTERIOR)
    client.subscribe(TOPIC_INTERIOR)

    print("Suscrito a:")
    print(f" - {TOPIC_EXTERIOR}")
    print(f" - {TOPIC_INTERIOR}")


def on_message(client, userdata, msg):
    """
    @brief Procesa los mensajes MQTT recibidos.

    Decodifica el payload JSON recibido y determina el tópico
    de origen para almacenar los datos en la tabla correspondiente.

    Tópicos soportados:
    - TOPIC_EXTERIOR
    - TOPIC_INTERIOR

    @param client Instancia del cliente MQTT.
    @param userdata Datos privados asociados al cliente.
    @param msg Mensaje MQTT recibido.

    @return None
    """

    try:

        payload = msg.payload.decode()

        data = json.loads(payload)

        if msg.topic == TOPIC_EXTERIOR:

            guardar_exterior(data)

        elif msg.topic == TOPIC_INTERIOR:

            guardar_interior(data)

        else:

            print(f"Topic desconocido: {msg.topic}")

    except Exception as e:

        print(f"Error procesando mensaje: {e}")


# ------------------------------------------------------------
# Inicialización del cliente MQTT
# ------------------------------------------------------------

## Cliente MQTT principal.
cliente = mqtt.Client()

## Callback de conexión.
cliente.on_connect = on_connect

## Callback de recepción de mensajes.
cliente.on_message = on_message

## Conexión al broker local.
cliente.connect(BROKER, PORT)

## Bucle principal de recepción MQTT.
cliente.loop_forever()
"""
@file thingspeak_uploader.py
@brief Servicio de sincronización entre SQLite y ThingSpeak.

Este módulo obtiene periódicamente los registros más recientes
almacenados en la base de datos SQLite y los publica en la
plataforma ThingSpeak para monitoreo remoto.

Variables enviadas:

- Temperatura interna
- pH
- Concentración de CO2
- Temperatura exterior
- Humedad exterior

Flujo de operación:

SQLite -> thingspeak_uploader.py -> ThingSpeak Cloud

@author
Fernando Plazas Trujillo

@date 2026
"""
import sqlite3
import requests
import time

## Nombre de la base de datos SQLite.
DB_NAME = "fermentacion.db"

## Clave de escritura del canal ThingSpeak.
THINGSPEAK_API_KEY = "..."

## URL del servicio de actualización ThingSpeak.
THINGSPEAK_URL = "https://api.thingspeak.com/update"

## Último ID enviado desde la tabla interior.
ultimo_id_interior = 0

## Último ID enviado desde la tabla exterior.
ultimo_id_exterior = 0


def obtener_ultimos_datos():
    """
    @brief Obtiene los registros más recientes de la base de datos.

    Consulta las tablas interior y exterior y recupera
    el último registro almacenado en cada una.

    @return Tupla (interior, exterior) con los registros obtenidos.
    """

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, temperatura, ph, co2
        FROM interior
        ORDER BY id DESC
        LIMIT 1
    """)

    interior = cursor.fetchone()

    cursor.execute("""
        SELECT id, temperatura, humedad
        FROM exterior
        ORDER BY id DESC
        LIMIT 1
    """)

    exterior = cursor.fetchone()

    conn.close()

    return interior, exterior


def enviar_thingspeak(interior, exterior):
    """
    @brief Envía datos a la plataforma ThingSpeak.

    Construye el payload HTTP y realiza una solicitud POST
    al canal configurado de ThingSpeak.

    @param interior Registro más reciente de la tabla interior.
    @param exterior Registro más reciente de la tabla exterior.

    @return Código HTTP devuelto por el servidor.
    """

    payload = {
        "api_key": THINGSPEAK_API_KEY,
        "field1": interior[1],  # temperatura interior
        "field2": interior[2],  # ph
        "field3": interior[3],  # co2
        "field4": exterior[1],  # temperatura exterior
        "field5": exterior[2]   # humedad exterior
    }

    respuesta = requests.post(
        THINGSPEAK_URL,
        data=payload,
        timeout=10
    )

    return respuesta.status_code


print("ThingSpeak uploader iniciado")

while True:

    try:

        interior, exterior = obtener_ultimos_datos()

        if interior is None or exterior is None:
            time.sleep(10)
            continue

        id_interior = interior[0]
        id_exterior = exterior[0]

        interior_nuevo = id_interior > ultimo_id_interior
        exterior_nuevo = id_exterior > ultimo_id_exterior

        if interior_nuevo and exterior_nuevo:

            codigo = enviar_thingspeak(
                interior,
                exterior
            )

            if codigo == 200:

                ultimo_id_interior = id_interior
                ultimo_id_exterior = id_exterior

                print(
                    f"Enviado -> "
                    f"INT:{id_interior} "
                    f"EXT:{id_exterior}"
                )

            else:

                print(
                    f"Error ThingSpeak: {codigo}"
                )

        time.sleep(15)

    except Exception as e:

        print(f"Error: {e}")
        time.sleep(15)
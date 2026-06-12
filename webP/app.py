"""
@file app.py
@brief Aplicación web Flask para visualización de datos del sistema.

Este módulo implementa la interfaz web del sistema de monitoreo
de fermentación de café.

Funciones principales:
- Consulta de datos almacenados en SQLite.
- Visualización de variables actuales.
- Generación de históricos para gráficas.
- Renderizado de la página principal mediante Flask.

Variables visualizadas:
- Temperatura interna
- pH
- CO2
- Temperatura exterior
- Humedad exterior

Flujo de operación:

SQLite -> Flask -> Navegador Web

@author
Fernando Plazas Trujillo

@date 2026
"""
from flask import Flask, render_template, jsonify, request
import sqlite3

app = Flask(__name__)

## Ruta de la base de datos SQLite.
DB_NAME = "../fermentacion.db"


@app.route("/")
def index():
    """
    @brief Genera la página principal del sistema.

    Consulta la base de datos SQLite para obtener:

    - Último registro interior.
    - Último registro exterior.
    - Históricos de temperatura interna.
    - Históricos de temperatura exterior.
    - Históricos de pH.
    - Históricos de CO2.
    - Históricos de humedad exterior.

    Los datos obtenidos son enviados a la plantilla
    HTML para su representación gráfica.

    @return Página HTML renderizada.
    """

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM exterior
        ORDER BY id DESC
        LIMIT 1
    """)

    exterior = cursor.fetchone()

    cursor.execute("""
        SELECT *
        FROM interior
        ORDER BY id DESC
        LIMIT 1
    """)

    interior = cursor.fetchone()

    cursor.execute("""
        SELECT hora, temperatura
        FROM interior
        ORDER BY id DESC
        LIMIT 50
    """)

    hist_temp_int = cursor.fetchall()
    hist_temp_int.reverse()

    cursor.execute("""
        SELECT hora, ph
        FROM interior
        ORDER BY id DESC
        LIMIT 50
    """)

    hist_ph = cursor.fetchall()
    hist_ph.reverse()

    cursor.execute("""
        SELECT hora, temperatura
        FROM exterior
        ORDER BY id DESC
        LIMIT 50
    """)

    hist_temp_ext = cursor.fetchall()
    hist_temp_ext.reverse()

    cursor.execute("""
        SELECT hora, co2
        FROM interior
        ORDER BY id DESC
        LIMIT 50
    """)

    hist_co2 = cursor.fetchall()
    hist_co2.reverse()

    cursor.execute("""
        SELECT hora, humedad
        FROM exterior
        ORDER BY id DESC
        LIMIT 50
    """)

    hist_hum_ext = cursor.fetchall()
    hist_hum_ext.reverse()

    conn.close()

    return render_template(
        "index.html",
        exterior=exterior,
        interior=interior,
        hist_temp_int=hist_temp_int,
        hist_ph=hist_ph,
        hist_temp_ext=hist_temp_ext,
        hist_co2=hist_co2,
        hist_hum_ext=hist_hum_ext
    )

# ------------------------------------------------------------
# Inicio del servidor Flask
# ------------------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
from flask import Flask, jsonify
import requests
import threading
import time
import psycopg2

def get_db_conn():
    retry_count = 0
    max_retries = 5
    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(
                host="postgresql-service",
                database="mydatabase",
                user="postgres",
                password="admin",
                port=5432
            )
            with conn.cursor() as cur: #creación de la tabla por si no existe en la bd
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cliente (
                        id INTEGER PRIMARY KEY,
                        edad INTEGER,
                        ingresos_anuales INTEGER,
                        puntuacion_credito INTEGER,
                        importe_deseado INTEGER,
                        aprobacion INTEGER
                    );
                """)
                conn.commit()
            return conn 
        except psycopg2.OperationalError:
            retry_count += 1
            print(f"Intentando conectar a la base de datos... Intento {retry_count}/{max_retries}")
            time.sleep(2)  

    raise Exception("No se pudo conectar a la base de datos después de varios intentos.")
app = Flask(__name__)
last_id = 0 #seguimiento del último ID recuperado
@app.route("/data")
def get_data():
    global last_id
    with get_db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM cliente WHERE id > %s ORDER BY id LIMIT 1", (last_id,))  #selección del siguiente registro
            registro = cur.fetchone()
            if registro:
                last_id = registro[0]  #se actualiza el ID del recuperado
                data = {
                    "id": registro[0],
                    "edad": registro[1],
                    "ingresos_anuales": registro[2],
                    "puntuacion_credito": registro[3],
                    "importe_deseado": registro[4],
                    "aprobacion": registro[5]
                }
                return jsonify(data)
            else:
                last_id = 0  #se reinicia el ID, si se llega al final
                return jsonify({"error": "No se encontraron más registros"}), 404
            
@app.route('/send_to_process', methods=['POST'])  #POST -> send information
def send_to_process():
    global last_id
    while True:  #infinite loop
        try:
            #CAMBIO EN LA SIGUIENTE LINEA. EN LUGAR DE "localhost", se usa el nombre del contenedor "data-gen"
            response = requests.get('http://gen-service:5000/data')  #make a request to itself to get the data from DB
            if response.status_code == 200: #añadí if-elif-else para comprobar respuestas
                data = response.json()  #turn the data to a JSON/dictionary 
                LB_response = requests.post('http://loadbalancer/process', json=data)  #send the data through the LOAD BALANCER
                print(LB_response.json())  #print the status response from LOAD BALANCER
            elif response.status_code == 404:
                print("No se encontraron más registros.") 
                break
            else:
                print(f"Error en la solicitud a /data: {response.status_code}") #fin de if-elif-else
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(10)  # wait N seconds to make another request

if __name__ == "__main__":
    threading.Thread(target=send_to_process).start()  # Thread that sends every N seconds a request with DB data to the LOAD BALANCER
    app.run(host="0.0.0.0")

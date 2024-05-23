from LoanBot import LoanBot  #file LoanBot.py in the same folder that contains the Perceptron
from flask import Flask, request, jsonify
import psycopg2
import time

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
import csv  #module to read .csv files
app = Flask(__name__)
#///////////////////////// TRAIN THE PERCEPTRON
def train_model(loanPerceptron):
        file_name = "training_data.csv"  #training data file inside the project folder
        try:
            with open(file_name, mode = 'r') as f:  #try to open the file searching with the specified filename
                reader = csv.reader(f)
                next(reader) # Skipping header
                data = []
                for line in reader:  #save each line of the file in a list
                    line = [int(item) for item in line]
                    data.append(line)

            loanPerceptron.train(data)  #train the preceptron with the datafile
            print("Training done\n")

        except FileNotFoundError:
            print("The file does not exist.")
        except ValueError:
            print("Some of the data in the file couldn't be converted to integers.")
def print_data(data):
    print(data)
#///////////////////////// RECEIVE DATA, MODIFIES IT AND UPLOAD TO DATABASE
@app.route("/receive_data", methods=['POST'])
def getSendData():
    data = request.json
    try:
        result = loanPerceptron.predict([data["edad"], data["ingresos_anuales"], data["puntuacion_credito"], data["importe_deseado"]], 1)
        # Actualizar la base de datos con el resultado de la predicción
        with get_db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE cliente SET aprobacion = %s WHERE id = %s", (result, data["id"]))
                conn.commit()
        if result == 1:
            print("\n--- Congratulations! You qualify! ---\n")
        else:
            print("\n*** You don't qualify for a loan at this time. *** \n")

        return jsonify({"status": "success"})

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500  # Código de estado 500 para indicar un error interno del servidor
if __name__ == "__main__":
    loanPerceptron = LoanBot()  #create a single layer perceptron (isn't trained yet)
    train_model(loanPerceptron) #before anything, train the model with training data in the folder
    app.run(host="0.0.0.0", port=5000)
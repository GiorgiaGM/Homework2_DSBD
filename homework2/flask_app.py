from flask import Flask, request, jsonify
import grpc
import user_pb2
import user_pb2_grpc
import time
import traceback
app = Flask(__name__)


time.sleep(5)

# Configurazione del canale gRPC
grpc_channel = grpc.insecure_channel('grpc_server:50051')
stub = user_pb2_grpc.UserServiceStub(grpc_channel)

# Endpoint per registrare un nuovo utente
@app.route('/register', methods=['POST'])
def register_user():
    try:
        # Ottieni i dati JSON dalla richiesta HTTP
        data = request.json
        email = data['email']
        ticker = data['ticker']
        high_value = data['high_value']
        low_value = data['low_value']

        # Effettua la chiamata gRPC
        response = stub.RegisterUser(user_pb2.RegisterUserRequest(
            email=email,
            ticker=ticker,
            high_value=high_value,
            low_value=low_value
        ))

        # Restituisci la risposta come JSON
        return jsonify({
            'success': response.success,
            'message': response.message
        }), 200 if response.success else 400
    except Exception as e:
        print("[ERROR] Si è verificato un errore nel server Flask:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# Endpoint per aggiornare il ticker di un utente
@app.route('/update-ticker', methods=['PUT'])
def update_user_ticker():
    try:
        data = request.json
        email = data['email']
        new_ticker = data['ticker']

        response = stub.UpdateUserTicker(user_pb2.UserRequest(
            email=email,
            ticker=new_ticker
        ))

        return jsonify({
            'success': response.success,
            'message': response.message
        }), 200 if response.success else 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint per cancellare un utente
@app.route('/delete', methods=['DELETE'])
def delete_user():
    try:
        email = request.json['email']

        response = stub.DeleteUser(user_pb2.DeleteUserRequest(
            email=email
        ))

        return jsonify({
            'success': response.success,
            'message': response.message
        }), 200 if response.success else 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Endpoint per recuperare l'ultimo valore del ticker
@app.route('/get-latest-value', methods=['GET'])
def get_latest_value():
    try:
        email = request.args.get('email')

        # Effettua la chiamata gRPC
        response = stub.GetLatestValue(user_pb2.UserRequest(
            email=email
        ))

        # Restituisci la risposta come JSON
        if response.success:
            return jsonify({
                'success': True,
                'message': response.message,
                'value': response.value,
                'timestamp': response.timestamp
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': response.message
            }), 400

    except Exception as e:
        print("[ERROR] Si è verificato un errore nel server Flask:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# Endpoint per calcolare la media degli ultimi X valori
@app.route('/calculate-average', methods=['GET'])
def calculate_average():
    try:
        email = request.args.get('email')
        count = int(request.args.get('count'))

        # Effettua la chiamata gRPC
        response = stub.CalculateAverage(user_pb2.AverageRequest(
            email=email,
            count=count
        ))

        # Restituisci la risposta come JSON
        if response.success:
            return jsonify({
                'success': True,
                'message': response.message,
                'average': response.average
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': response.message
            }), 400

    except Exception as e:
        print("[ERROR] Si è verificato un errore nel server Flask:")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500



# Avvia il server Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

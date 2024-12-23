import grpc
import user_pb2
import user_pb2_grpc
import time

time.sleep(5)

def register_user(stub):
    email = input("Inserisci l'email per la registrazione: ")
    ticker = input("Inserisci il ticker: ")
    high_value = float(input("Inserisci il valore massimo (high_value): "))
    low_value = float(input("Inserisci il valore minimo (low_value): "))

    response = stub.RegisterUser(user_pb2.RegisterUserRequest(
        email=email,
        ticker=ticker,
        high_value=high_value,
        low_value=low_value
    ))
    print(f"Risultato della registrazione: Successo={response.success}, Messaggio={response.message}")

def update_user_ticker(stub):
    email = input("Inserisci l'email dell'utente da aggiornare: ")
    new_ticker = input("Inserisci il nuovo ticker: ")

    response = stub.UpdateUserTicker(user_pb2.UserRequest(
        email=email,
        ticker=new_ticker
    ))
    print(f"Risultato dell'aggiornamento: Successo={response.success}, Messaggio={response.message}")

def delete_user(stub):
    email = input("Inserisci l'email dell'utente da cancellare: ")

    response = stub.DeleteUser(user_pb2.DeleteUserRequest(
        email=email
    ))
    print(f"Risultato della cancellazione: Successo={response.success}, Messaggio={response.message}")


# Funzione per ottenere l'ultimo valore del ticker
def get_latest_value(stub):
    email = input("Inserisci l'email dell'utente per recuperare l'ultimo valore del ticker: ")

    # Crea la richiesta per ottenere l'ultimo valore del ticker
    request = user_pb2.EmailRequest(email=email)


    try:
        # Invia la richiesta al server
        response = stub.GetLatestValue(request)
        
        
        print(f"[DEBUG] Risposta dal server: {response}")


        # Gestisce la risposta del server
        if response.success:
            print(f"Ultimo valore per {email}: {response.message}")
            print(f"Valore: {response.value}, Timestamp: {response.timestamp}")
        else:
            print(f"Errore: {response.message}")
    except grpc.RpcError as e:
        # Qui possiamo aggiungere un controllo per i dettagli specifici dell'errore
        print(f"[ERROR] Si è verificato un errore gRPC: {e.code()} - {e.details()}")        
    except Exception as e:
        print(f"[ERROR] Si è verificato un errore generico: {str(e)}")


def calculate_average(stub):
    email = input("Inserisci l'email dell'utente: ")
    count = int(input("Inserisci il numero di ultimi valori da considerare per la media: "))

    # Crea la richiesta al server
    request = user_pb2.AverageRequest(
        email=email,
        count=count
    )
    
    try:
        # Invia la richiesta al server
        response = stub.CalculateAverage(request)
        
        if response.success:
            print(f"Media calcolata: {response.average}")
            print(f"Risposta dal server:{response.message}")
        else:
            print(f"Errore: {response.message}")
    except grpc.RpcError as e:
        print(f"Errore gRPC: {e.code()} - {e.details()}")
    except Exception as e:
        print(f"Errore generale: {str(e)}")


def update_threshold(stub):
    email = input("Inserisci l'email dell'utente da aggiornare: ")
    high_value = float(input("Inserisci il nuovo valore massimo (high_value): "))
    low_value = float(input("Inserisci il nuovo valore minimo (low_value): "))

    response = stub.UpdateThreshold(user_pb2.UpdateThresholdRequest(
        email=email,
        high_value=high_value,
        low_value=low_value
    ))
    print(f"Risultato dell'aggiornamento: Successo={response.success}, Messaggio={response.message}")




if __name__ == "__main__":
     with grpc.insecure_channel('grpc_server:50051') as channel:
        stub = user_pb2_grpc.UserServiceStub(channel)
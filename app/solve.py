
import requests
import json

# 1. Login and get token
login_url = "http://127.0.0.1:8000/auth/login"
login_data = {
    "email": "promoter@datakap.mx",
    "password": "Promoter#2025"
}
try:
    login_response = requests.post(login_url, json=login_data)
    login_response.raise_for_status()  # Raise an exception for bad status codes
    token = login_response.json()["token"]

    print(f"Successfully logged in. Token: {token}")

    # 2. Create registration
    registration_url = "http://127.0.0.1:8000/registrations"
    registration_data = {
        "role": "promoter",
        "requiresPhoto": True,
        "fields": {
            "claveElector": "ABCD1234567890",
            "sexo": "M",
            "nombre": "Juan",
            "apellidoPaterno": "Perez",
            "apellidoMaterno": "Gonzalez",
            "direccion": "Calle Falsa 123",
            "codigoPostal": "12345",
            "vigencia": "2030",
            "estado": "Ciudad de México",
            "municipio": "Coyoacán",
            "localidad": "Del Carmen",
            "telefono": "5512345678",
            "whatsapp": "5512345678"
        }
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    registration_response = requests.post(registration_url, json=registration_data, headers=headers)
    registration_response.raise_for_status()

    print("Successfully created registration.")
    print(registration_response.json())

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    if e.response:
        print(f"Response content: {e.response.text}")


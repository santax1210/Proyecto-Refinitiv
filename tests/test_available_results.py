
import requests
import os
import json

BASE_URL = "http://localhost:5000/api"

def test():
    from dotenv import load_dotenv
    load_dotenv()
    
    username = os.environ.get('APP_USERNAME', 'admin')
    password = os.environ.get('APP_PASSWORD', 'password')
    
    print(f"Tentando login com {username}...")
    try:
        res = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password}, timeout=5)
        if res.status_code == 200:
            token = res.json().get('token')
            print("Login successful")
            
            headers = {"Authorization": f"Bearer {token}"}
            print("Consultando resultados disponibles...")
            res_av = requests.get(f"{BASE_URL}/results/available", headers=headers, timeout=5)
            if res_av.status_code == 200:
                print("Available results:", res_av.json().get('available'))
                return True
            else:
                print(f"Error en available: {res_av.status_code}, {res_av.text}")
        else:
            print(f"Login failed: {res.status_code}, {res.text}")
    except Exception as e:
        print(f"Erro de conexão: {e}")
    return False

if __name__ == "__main__":
    test()

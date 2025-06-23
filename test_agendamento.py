#!/usr/bin/env python3
"""
Test script to verify exam scheduling integration
"""
import requests
import json

# Base URL
BASE_URL = "http://localhost:5000"
session = requests.Session()

def test_agendamento_integration():
    print("=== Testando integração do agendamento ===")
    
    # 1. Armazenar agendamento
    print("1. Armazenando dados de agendamento...")
    agendamento_data = {
        "school": "EMEF Brasília - Centro, Brasília, DF",
        "date": "2025-06-25-14:30"
    }
    
    response = session.post(
        f"{BASE_URL}/store-exam-selection",
        json=agendamento_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 2. Verificar página DAM
    print("\n2. Verificando página DAM...")
    response = session.get(f"{BASE_URL}/pagamento")
    
    if response.status_code == 200:
        content = response.text
        if "EMEF Brasília" in content:
            print("✓ Escola encontrada na página DAM")
        else:
            print("✗ Escola NÃO encontrada na página DAM")
            
        if "25/06/2025" in content or "2025-06-25" in content:
            print("✓ Data encontrada na página DAM")
        else:
            print("✗ Data NÃO encontrada na página DAM")
            
        # Verificar seção específica
        if "Informações da Prova" in content:
            print("✓ Seção 'Informações da Prova' encontrada")
        else:
            print("✗ Seção 'Informações da Prova' NÃO encontrada")
    else:
        print(f"Erro ao acessar página DAM: {response.status_code}")

if __name__ == "__main__":
    test_agendamento_integration()
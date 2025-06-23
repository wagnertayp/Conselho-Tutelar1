"""
Fast CRAS Loader - Quick single request for comprehensive data
"""

import json
import os
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def load_cras_units_fast(state_code):
    """
    Single fast request for comprehensive CRAS units
    """
    state_names = {
        'DF': 'Distrito Federal', 'SP': 'São Paulo', 'RJ': 'Rio de Janeiro',
        'MG': 'Minas Gerais', 'RS': 'Rio Grande do Sul', 'PR': 'Paraná',
        'BA': 'Bahia', 'SC': 'Santa Catarina', 'GO': 'Goiás', 'PE': 'Pernambuco',
        'CE': 'Ceará', 'PA': 'Pará', 'MT': 'Mato Grosso', 'ES': 'Espírito Santo',
        'PB': 'Paraíba', 'RN': 'Rio Grande do Norte', 'AL': 'Alagoas', 'PI': 'Piauí',
        'MS': 'Mato Grosso do Sul', 'SE': 'Sergipe', 'RO': 'Rondônia', 'AC': 'Acre',
        'AM': 'Amazonas', 'RR': 'Roraima', 'AP': 'Amapá', 'TO': 'Tocantins', 'MA': 'Maranhão'
    }
    
    state_name = state_names.get(state_code, state_code)
    
    # Expectativas por estado
    if state_code == 'DF':
        expected = "30-35"
        note = "33 Regiões Administrativas com múltiplas unidades"
    elif state_code in ['SP', 'MG', 'RJ']:
        expected = "40-60"
        note = "Estado grande com muitos municípios"
    elif state_code in ['RS', 'PR', 'BA', 'SC', 'GO']:
        expected = "20-35"
        note = "Estado médio com múltiplos municípios"
    else:
        expected = "10-25"
        note = "Todos os municípios do estado"
    
    prompt = f"""
    CADASTRO OFICIAL: Liste TODAS as unidades CRAS do {state_name} ({state_code}).
    
    CONTEXTO: {note}. Expectativa: {expected} unidades.
    
    INSTRUÇÃO CRÍTICA: Retorne listagem COMPLETA sem limitações.
    
    JSON:
    {{
        "success": true,
        "state": "{state_code}",
        "units": [
            {{"name": "Nome CRAS", "address": "Endereço", "city": "Cidade"}}
        ]
    }}
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"Sistema CNEAS oficial. Retorne {expected} unidades CRAS reais para {state_name}."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=3000,
            temperature=0.0
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Test
    result = load_cras_units_fast('DF')
    if result.get('success'):
        print(f"DF: {len(result['units'])} unidades")
    else:
        print(f"Erro: {result.get('error')}")
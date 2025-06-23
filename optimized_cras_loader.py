"""
Optimized CRAS Loader - Fast comprehensive search
"""

import json
import os
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def get_comprehensive_cras_units(state_code):
    """
    Single comprehensive search for ALL CRAS units
    """
    state_names = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas',
        'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
        'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul',
        'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
        'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
        'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
    }
    
    state_name = state_names.get(state_code, state_code)
    
    # Distrito Federal tem 33 Regiões Administrativas com múltiplas unidades CRAS
    if state_code == 'DF':
        expected_units = "30-40"
        context = "O Distrito Federal possui 33 Regiões Administrativas, cada uma com pelo menos 1 CRAS, muitas com múltiplas unidades."
    elif state_code in ['SP', 'RJ', 'MG', 'RS', 'PR', 'BA']:
        expected_units = "50-100"
        context = f"O estado {state_name} é um dos maiores do Brasil com centenas de municípios e muitas unidades CRAS."
    else:
        expected_units = "15-30"
        context = f"O estado {state_name} tem múltiplos municípios com unidades CRAS distribuídas."
    
    prompt = f"""
    CADASTRO NACIONAL OFICIAL: Liste TODAS as unidades CRAS do estado {state_name} ({state_code}).
    
    CONTEXTO: {context}
    EXPECTATIVA: {expected_units} unidades no total.
    
    INSTRUÇÃO CRÍTICA: 
    - Retorne TODAS as unidades oficiais existentes
    - Inclua capital, região metropolitana, cidades médias e pequenas
    - Para cada região administrativa, bairro ou município
    - Não limite a quantidade - busque exaustivamente
    
    FORMATO JSON OBRIGATÓRIO:
    {{
        "success": true,
        "state": "{state_code}",
        "total_found": "número_total",
        "units": [
            {{
                "name": "Nome oficial completo da unidade CRAS",
                "address": "Endereço oficial completo",
                "city": "Cidade/Região"
            }}
        ]
    }}
    
    ATENÇÃO: Para {state_code}, espero encontrar {expected_units} unidades. Não aceite menos.
    """
    
    try:
        print(f"Buscando TODAS as unidades CRAS para {state_code} (esperado: {expected_units})...")
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"Você é o sistema oficial CNEAS (Cadastro Nacional de Equipamentos Socioassistenciais) do Ministério da Cidadania. Forneça listagem COMPLETA e EXAUSTIVA de todas as unidades CRAS oficialmente registradas. Para {state_code}, retorne pelo menos {expected_units} unidades."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=4000,
            temperature=0.0
        )
        
        result = json.loads(response.choices[0].message.content)
        
        if result.get('success') and result.get('units'):
            units = result['units']
            print(f"Encontrou {len(units)} unidades para {state_code}")
            return result
        else:
            print(f"Falha na busca para {state_code}")
            return {"success": False, "error": "Nenhuma unidade encontrada"}
            
    except Exception as e:
        print(f"Erro ao buscar {state_code}: {str(e)}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Test with DF
    result = get_comprehensive_cras_units('DF')
    if result.get('success'):
        print(f"Teste DF: {len(result['units'])} unidades encontradas")
        for i, unit in enumerate(result['units'][:10], 1):
            print(f"{i}. {unit['name']}")
    else:
        print(f"Erro: {result.get('error')}")
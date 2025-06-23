"""
Comprehensive CRAS Data Loader - Busca ALL unidades CRAS usando múltiplas estratégias
"""

import json
import os
import time
from openai import OpenAI

# OpenAI setup
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def get_all_cras_units_comprehensive(state_code):
    """
    Busca TODAS as unidades CRAS usando múltiplas consultas estratégicas
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
    
    # Estratégia 1: Busca geral por tipo de município
    prompts = [
        f"""
        Liste TODAS as unidades CRAS (Centro de Referência de Assistência Social) da CAPITAL e região metropolitana do estado {state_name} ({state_code}), Brasil.
        
        Procure por unidades OFICIAIS que realmente existem. Para cada unidade:
        - Nome oficial completo da unidade CRAS
        - Endereço completo REAL e verificável
        - Cidade onde está localizada
        
        Inclua TODAS as unidades da capital e cidades da região metropolitana.
        
        Responda APENAS em formato JSON:
        {{
            "success": true,
            "state": "{state_code}",
            "region": "capital_metropolitana",
            "units": [
                {{
                    "name": "Nome oficial completo",
                    "address": "Endereço completo real",
                    "city": "Cidade"
                }}
            ]
        }}
        """,
        
        f"""
        Liste TODAS as unidades CRAS (Centro de Referência de Assistência Social) das CIDADES DO INTERIOR do estado {state_name} ({state_code}), Brasil.
        
        Procure por unidades OFICIAIS em cidades médias e pequenas do interior. Para cada unidade:
        - Nome oficial completo da unidade CRAS
        - Endereço completo REAL e verificável
        - Cidade onde está localizada
        
        Foque em municípios do interior, regiões rurais e cidades médias.
        
        Responda APENAS em formato JSON:
        {{
            "success": true,
            "state": "{state_code}",
            "region": "interior",
            "units": [
                {{
                    "name": "Nome oficial completo",
                    "address": "Endereço completo real",
                    "city": "Cidade"
                }}
            ]
        }}
        """,
        
        f"""
        Liste TODAS as unidades CRAS (Centro de Referência de Assistência Social) das REGIÕES ESPECIAIS e MICRORREGIÕES do estado {state_name} ({state_code}), Brasil.
        
        Procure por unidades em:
        - Regiões administrativas especiais
        - Microrregiões geográficas
        - Áreas de expansão urbana
        - Distritos e subdivisões
        
        Para cada unidade:
        - Nome oficial completo da unidade CRAS
        - Endereço completo REAL e verificável
        - Cidade/região onde está localizada
        
        Responda APENAS em formato JSON:
        {{
            "success": true,
            "state": "{state_code}",
            "region": "especiais",
            "units": [
                {{
                    "name": "Nome oficial completo",
                    "address": "Endereço completo real",
                    "city": "Cidade/Região"
                }}
            ]
        }}
        """
    ]
    
    all_units = []
    unit_names_seen = set()
    
    for i, prompt in enumerate(prompts):
        try:
            print(f"Executando busca {i+1}/3 para {state_code}...")
            
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um especialista em assistência social brasileira com conhecimento abrangente sobre todas as unidades CRAS existentes. Forneça informações precisas sobre unidades reais."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=4000
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if result.get('success') and result.get('units'):
                units = result['units']
                print(f"Encontrou {len(units)} unidades na busca {i+1}")
                
                # Evitar duplicatas baseado no nome
                for unit in units:
                    unit_name = unit.get('name', '').strip()
                    if unit_name and unit_name not in unit_names_seen:
                        unit_names_seen.add(unit_name)
                        all_units.append(unit)
                        
            # Pausa entre requests
            time.sleep(2)
            
        except Exception as e:
            print(f"Erro na busca {i+1}: {str(e)}")
            continue
    
    print(f"Total de unidades únicas encontradas para {state_code}: {len(all_units)}")
    
    return {
        "success": True,
        "state": state_code,
        "units": all_units
    }

if __name__ == "__main__":
    # Teste com DF
    result = get_all_cras_units_comprehensive('DF')
    print(f"Resultado final: {len(result['units'])} unidades")
    for unit in result['units']:
        print(f"- {unit['name']} ({unit['city']})")
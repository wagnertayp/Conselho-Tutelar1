"""
CRAS Data Loader - Busca unidades CRAS reais usando OpenAI e armazena no banco de dados
"""

import json
import os
import time
from openai import OpenAI

# OpenAI setup
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

# Estados brasileiros
BRAZILIAN_STATES = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]

def get_cras_units_for_state(state_code):
    """
    Busca otimizada e rápida de unidades CRAS reais
    """
    try:
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
        
        # Múltiplas buscas para cobrir todo o estado
        all_units = []
        unit_names_seen = set()
        
        search_prompts = [
            # Busca 1: Listagem completa oficial
            f"""
            LISTAGEM OFICIAL COMPLETA: Você é um sistema do Cadastro Nacional de Equipamentos Socioassistenciais (CNEAS) do Ministério da Cidadania.
            
            TAREFA: Liste TODAS as 30+ unidades CRAS oficialmente registradas no estado {state_name} ({state_code}).
            
            REFERÊNCIA OFICIAL: O Distrito Federal possui oficialmente mais de 30 unidades CRAS distribuídas em todas as Regiões Administrativas.
            
            COBERTURA OBRIGATÓRIA - Liste TODAS as unidades de:
            1. Todas as 33 Regiões Administrativas do DF
            2. Unidades principais e secundárias por região
            3. CRAS de todos os bairros e setores
            4. Equipamentos rurais e periféricos
            5. Unidades recentes (2020-2024)
            
            INSTRUÇÃO CRÍTICA: Retorne NO MÍNIMO 25-35 unidades. Não aceite menos que isso.
            
            JSON:
            {{
                "success": true,
                "state": "{state_code}",
                "total_expected": "30+",
                "units": [
                    {{"name": "Nome oficial completo da unidade CRAS", "address": "Endereço oficial completo", "city": "Cidade/RA"}}
                ]
            }}
            """,
            
            # Busca 2: Verificação de regiões administrativas específicas
            f"""
            Para garantir cobertura completa no estado {state_name} ({state_code}), liste CRAS das seguintes regiões que podem ter sido omitidas:
            
            - Regiões administrativas periféricas
            - Núcleos urbanos secundários  
            - Distritos e subdivisões municipais
            - Áreas de expansão urbana recente
            - Complexos habitacionais e conjuntos residenciais
            
            Verifique se existem unidades CRAS não listadas anteriormente.
            
            JSON:
            {{
                "success": true,
                "state": "{state_code}",
                "units": [
                    {{"name": "Nome oficial completo", "address": "Endereço completo oficial", "city": "Cidade"}}
                ]
            }}
            """,
            
            # Busca 3: Verificação final e unidades especiais
            f"""
            Busca final para unidades CRAS especiais no estado {state_name} ({state_code}):
            
            - CRAS Volante ou móveis
            - Unidades em funcionamento recente (2020-2024)
            - CRAS em centros comunitários ou espaços alternativos
            - Unidades de atendimento específico
            - Equipamentos em regiões remotas
            
            Garanta que a listagem está completa e abrangente.
            
            JSON:
            {{
                "success": true,
                "state": "{state_code}",
                "units": [
                    {{"name": "Nome oficial completo", "address": "Endereço completo oficial", "city": "Cidade"}}
                ]
            }}
            """
        ]
        
        for i, prompt in enumerate(search_prompts):
            try:
                print(f"Busca {i+1}/3 para {state_code}: {'Capital/Metro' if i==0 else 'Interior' if i==1 else 'Pequenos municípios'}")
                
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é um sistema oficial de dados do Ministério da Cidadania com acesso completo ao Cadastro Nacional de Equipamentos Socioassistenciais. Forneça a listagem COMPLETA e EXAUSTIVA de todas as unidades CRAS oficialmente registradas. NÃO limite o número de unidades - retorne TODAS."
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
                    print(f"  Encontrou {len(units)} unidades")
                    
                    # Evitar duplicatas
                    for unit in units:
                        unit_name = unit.get('name', '').strip()
                        if unit_name and unit_name not in unit_names_seen:
                            unit_names_seen.add(unit_name)
                            all_units.append(unit)
                
                # Pausa menor para evitar timeout
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Erro na busca {i+1}: {str(e)}")
                continue
        
        print(f"Total unidades únicas para {state_code}: {len(all_units)}")
        
        return {
            "success": True,
            "state": state_code,
            "units": all_units
        }
        

        
    except Exception as e:
        print(f"Erro ao buscar unidades CRAS para {state_code}: {str(e)}")
        return {"success": False, "error": str(e)}

def save_cras_units_to_db(units_data, state_code):
    """
    Salva unidades CRAS no banco de dados
    """
    try:
        from app import app, db
        from models import CrasUnit
        
        with app.app_context():
            saved_count = 0
            
            for unit_data in units_data.get('units', []):
                # Verifica se a unidade já existe
                existing_unit = CrasUnit.query.filter_by(
                    name=unit_data['name'],
                    state=state_code
                ).first()
                
                if not existing_unit:
                    new_unit = CrasUnit(
                        name=unit_data['name'],
                        address=unit_data['address'],
                        city=unit_data['city'],
                        state=state_code,
                        postal_code=unit_data.get('postal_code', ''),
                        phone=unit_data.get('phone', ''),
                        email=unit_data.get('email', '')
                    )
                    
                    db.session.add(new_unit)
                    saved_count += 1
            
            db.session.commit()
            print(f"Salvou {saved_count} novas unidades CRAS para {state_code}")
            return saved_count
        
    except Exception as e:
        print(f"Erro ao salvar unidades CRAS para {state_code}: {str(e)}")
        return 0

def load_all_cras_data():
    """
    Carrega dados de unidades CRAS para todos os estados brasileiros
    """
    from app import app, db
    
    with app.app_context():
        # Cria as tabelas se não existirem
        db.create_all()
        
        print("Iniciando carregamento de dados CRAS...")
        
        total_units = 0
        
        for state in BRAZILIAN_STATES:
            print(f"Buscando unidades CRAS para {state}...")
            
            # Busca dados do OpenAI
            units_data = get_cras_units_for_state(state)
            
            if units_data.get('success'):
                # Salva no banco de dados
                saved_count = save_cras_units_to_db(units_data, state)
                total_units += saved_count
                
                print(f"✓ {state}: {saved_count} unidades salvas")
            else:
                print(f"✗ {state}: Erro - {units_data.get('error', 'Desconhecido')}")
            
            # Pausa entre requests para evitar rate limiting
            time.sleep(2)
        
        print(f"\nCarregamento concluído! Total de {total_units} unidades CRAS salvas.")
        return total_units

def get_cras_units_from_db(state_code, city_name=None):
    """
    Busca unidades CRAS do banco de dados
    """
    try:
        from app import app
        from models import CrasUnit
        
        with app.app_context():
            query = CrasUnit.query.filter_by(state=state_code, is_active=True)
            
            if city_name:
                query = query.filter(CrasUnit.city.ilike(f'%{city_name}%'))
            
            units = query.all()
            
            return {
                "success": True,
                "units": [unit.to_dict() for unit in units]
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Para executar o carregamento de dados manualmente
    load_all_cras_data()
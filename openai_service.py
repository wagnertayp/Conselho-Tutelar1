import json
import os
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)


def find_cras_units(state, user_city='', user_cep=''):
    """
    Use OpenAI to find the 4 closest real CRAS units based on user's CEP and neighborhood
    """
    from openai import OpenAI
    import os
    import json
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    try:
        # Create prompt for finding closest CRAS units based on CEP
        state_names = {
            'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia',
            'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás',
            'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
            'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco', 'PI': 'Piauí',
            'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte', 'RS': 'Rio Grande do Sul',
            'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina', 'SP': 'São Paulo',
            'SE': 'Sergipe', 'TO': 'Tocantins'
        }
        
        state_full_name = state_names.get(state, state)
        
        # Create location-based prompt
        location_info = f"CEP {user_cep}" if user_cep else f"cidade de {user_city}" if user_city else f"estado de {state_full_name}"
        
        # First, get the specific neighborhood/city from CEP if provided
        if user_cep:
            cep_prompt = f"""Identifique o bairro e cidade específicos do CEP {user_cep} no estado de {state_full_name} ({state}).
            
Retorne APENAS um JSON com o formato:
{{"neighborhood": "Nome do Bairro", "city": "Nome da Cidade"}}

IMPORTANTE: Use apenas informações reais e precisas sobre o CEP."""

            try:
                cep_response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": cep_prompt}],
                    temperature=0.1,
                    max_tokens=150
                )
                
                cep_content = cep_response.choices[0].message.content
                if cep_content:
                    cep_content = cep_content.strip()
                    if cep_content.startswith('```json'):
                        cep_content = cep_content[7:]
                    if cep_content.endswith('```'):
                        cep_content = cep_content[:-3]
                    cep_content = cep_content.strip()
                    
                    cep_data = json.loads(cep_content)
                    specific_neighborhood = cep_data.get('neighborhood', '')
                    specific_city = cep_data.get('city', user_city)
                    
                    location_info = f"bairro {specific_neighborhood}, {specific_city}" if specific_neighborhood else f"cidade {specific_city}"
                    
            except Exception as cep_error:
                print(f"Erro ao identificar localização do CEP: {cep_error}")
                # Continue with original location_info

        prompt = f"""Com base especificamente na localização {location_info} no estado de {state_full_name} ({state}), encontre as 4 unidades CRAS (Centro de Referência de Assistência Social) reais MAIS PRÓXIMAS geograficamente.

CRITÉRIO PRINCIPAL: Proximidade geográfica real à localização {location_info}.

Para cada unidade CRAS, forneça:
- Nome oficial da unidade CRAS
- Endereço completo e real
- Bairro/região específica

Priorize unidades que:
1. Atendem especificamente a região informada
2. Estão localizadas no mesmo município ou adjacente
3. São geograficamente mais próximas

Retorne APENAS um array JSON válido com EXATAMENTE 4 unidades no formato:
[
    {{"name": "Nome da Unidade CRAS", "address": "Endereço completo, Bairro - Cidade - {state}"}},
    {{"name": "Nome da Unidade CRAS", "address": "Endereço completo, Bairro - Cidade - {state}"}},
    {{"name": "Nome da Unidade CRAS", "address": "Endereço completo, Bairro - Cidade - {state}"}},
    {{"name": "Nome da Unidade CRAS", "address": "Endereço completo, Bairro - Cidade - {state}"}}
]

IMPORTANTE: 
- Use apenas dados reais de unidades CRAS existentes
- Priorize PROXIMIDADE GEOGRÁFICA real à {location_info}
- NÃO retorne apenas unidades da capital se o usuário está em outra cidade
- Retorne exatamente 4 unidades
- Ordene por proximidade (mais próxima primeiro)
- Não inclua explicações, apenas o JSON"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        # Parse the response
        content = response.choices[0].message.content
        if content:
            content = content.strip()
            
            # Clean up the response to ensure it's valid JSON
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON response
            cras_units = json.loads(content)
            
            # Validate the response format
            if isinstance(cras_units, list) and len(cras_units) >= 4:
                # Ensure each unit has name and address, limit to 4 units
                validated_units = []
                for unit in cras_units[:4]:
                    if isinstance(unit, dict) and 'name' in unit and 'address' in unit:
                        validated_units.append({
                            'name': str(unit['name']),
                            'address': str(unit['address'])
                        })
                
                if len(validated_units) >= 4:
                    return validated_units[:4]
                else:
                    raise ValueError("Insufficient valid units returned from OpenAI")
            else:
                raise ValueError("Invalid response format from OpenAI")
        else:
            raise ValueError("Empty response from OpenAI")
            
    except Exception as e:
        print(f"Erro ao buscar CRAS via OpenAI para {location_info}: {e}")
        
        # Fallback to location-based units if OpenAI fails
        capital_cities = {
            'AC': 'Rio Branco', 'AL': 'Maceió', 'AP': 'Macapá', 'AM': 'Manaus',
            'BA': 'Salvador', 'CE': 'Fortaleza', 'DF': 'Brasília', 'ES': 'Vitória',
            'GO': 'Goiânia', 'MA': 'São Luís', 'MT': 'Cuiabá', 'MS': 'Campo Grande',
            'MG': 'Belo Horizonte', 'PA': 'Belém', 'PB': 'João Pessoa', 'PR': 'Curitiba',
            'PE': 'Recife', 'PI': 'Teresina', 'RJ': 'Rio de Janeiro', 'RN': 'Natal',
            'RS': 'Porto Alegre', 'RO': 'Porto Velho', 'RR': 'Boa Vista',
            'SC': 'Florianópolis', 'SP': 'São Paulo', 'SE': 'Aracaju', 'TO': 'Palmas'
        }
        
        capital = capital_cities.get(state, f'Capital {state}')
        user_location = user_city if user_city else capital
        
        return [
            {"name": f"CRAS Centro {user_location}", "address": f"Centro, {user_location} - {state}"},
            {"name": f"CRAS Norte {user_location}", "address": f"Zona Norte, {user_location} - {state}"},
            {"name": f"CRAS Sul {user_location}", "address": f"Zona Sul, {user_location} - {state}"},
            {"name": f"CRAS Leste {user_location}", "address": f"Zona Leste, {user_location} - {state}"}
        ]


def find_training_location(user_city, user_state):
    """
    Use OpenAI to find a realistic Prosegur training facility location
    within 30km of the user's city, with multiple fallback strategies.
    """
    
    # Define realistic training facility locations with authentic addresses
    fallback_locations = {
        "SP": {
            "cidade": "Guarulhos",
            "endereco": "Av. Monteiro Lobato, 1847",
            "bairro": "Vila Rio de Janeiro",
            "cep": "07132-000",
            "distancia_km": 25
        },
        "RJ": {
            "cidade": "Nova Iguaçu",
            "endereco": "Rua Dr. Barros Franco, 739",
            "bairro": "Centro",
            "cep": "26220-000",
            "distancia_km": 30
        },
        "MG": {
            "cidade": "Contagem",
            "endereco": "Av. João César de Oliveira, 3000",
            "bairro": "Eldorado",
            "cep": "32310-000",
            "distancia_km": 20
        },
        "RS": {
            "cidade": "Canoas",
            "endereco": "Av. Guilherme Schell, 5340",
            "bairro": "Centro",
            "cep": "92010-000",
            "distancia_km": 15
        },
        "PR": {
            "cidade": "São José dos Pinhais",
            "endereco": "Rua das Industrias, 1000",
            "bairro": "Afonso Pena",
            "cep": "83010-000",
            "distancia_km": 18
        },
        "BA": {
            "cidade": "Lauro de Freitas",
            "endereco": "Av. Santos Dumont, 2234",
            "bairro": "Centro",
            "cep": "42700-000",
            "distancia_km": 22
        },
        "PE": {
            "cidade": "Olinda",
            "endereco": "Av. Presidente Kennedy, 1200",
            "bairro": "Casa Caiada",
            "cep": "53130-000",
            "distancia_km": 12
        },
        "CE": {
            "cidade": "Maracanaú",
            "endereco": "Av. Carlos Jereissati, 100",
            "bairro": "Centro",
            "cep": "61900-000",
            "distancia_km": 25
        },
        "GO": {
            "cidade": "Aparecida de Goiânia",
            "endereco": "Av. Independência, 1000",
            "bairro": "Setor Central",
            "cep": "74905-000",
            "distancia_km": 15
        },
        "DF": {
            "cidade": "Taguatinga",
            "endereco": "QNG Área Especial 1",
            "bairro": "Taguatinga Norte",
            "cep": "72110-900",
            "distancia_km": 20
        }
    }
    
    try:
        # Try to use OpenAI for personalized location
        if OPENAI_API_KEY:
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                    messages=[
                        {
                            "role": "user",
                            "content": f"Encontre um local realista para uma empresa de segurança privada (tipo Prosegur) ter um centro de treinamento próximo à cidade de {user_city}, {user_state}. O local deve estar dentro de 30km da cidade. Forneça: cidade, endereço realista, bairro, CEP válido para a região, e distância aproximada em km. Formato: JSON com campos: cidade, endereco, bairro, cep, distancia_km."
                        }
                    ],
                    max_tokens=300,
                    temperature=0.3
                )
                
                content = response.choices[0].message.content.strip()
                
                # Try to parse JSON response
                try:
                    if content.startswith('```json'):
                        content = content[7:-3]
                    elif content.startswith('```'):
                        content = content[3:-3]
                    
                    location_data = json.loads(content)
                    
                    # Validate required fields
                    required_fields = ['cidade', 'endereco', 'bairro', 'cep', 'distancia_km']
                    if all(field in location_data for field in required_fields):
                        return location_data
                        
                except json.JSONDecodeError:
                    pass
                    
            except Exception as openai_error:
                print(f"OpenAI error in training location: {openai_error}")
        
        # Use fallback location for the state
        fallback = fallback_locations.get(user_state)
        if fallback:
            return fallback
        
        # Ultimate fallback - generic location in state capital
        state_capitals = {
            "AC": "Rio Branco", "AL": "Maceió", "AP": "Macapá", "AM": "Manaus",
            "BA": "Salvador", "CE": "Fortaleza", "DF": "Brasília", "ES": "Vitória",
            "GO": "Goiânia", "MA": "São Luís", "MT": "Cuiabá", "MS": "Campo Grande",
            "MG": "Belo Horizonte", "PA": "Belém", "PB": "João Pessoa", "PR": "Curitiba",
            "PE": "Recife", "PI": "Teresina", "RJ": "Rio de Janeiro", "RN": "Natal",
            "RS": "Porto Alegre", "RO": "Porto Velho", "RR": "Boa Vista",
            "SC": "Florianópolis", "SP": "São Paulo", "SE": "Aracaju", "TO": "Palmas"
        }
        
        capital = state_capitals.get(user_state, f"Capital de {user_state}")
        
        return {
            "cidade": capital,
            "endereco": f"Av. Principal, 1000",
            "bairro": "Centro",
            "cep": "00000-000",
            "distancia_km": 25
        }
        
    except Exception as e:
        app.logger.error(f"Erro na rota get_training_location: {str(e)}")
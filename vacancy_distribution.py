"""
Vacancy Distribution System - Real data from /vagas page table
"""

# Dados reais extraídos da tabela da página /vagas
STATE_VACANCIES = {
    'AC': {'vacancies': 45, 'state_name': 'Acre'},
    'AL': {'vacancies': 124, 'state_name': 'Alagoas'},
    'AP': {'vacancies': 38, 'state_name': 'Amapá'},
    'AM': {'vacancies': 186, 'state_name': 'Amazonas'},
    'BA': {'vacancies': 682, 'state_name': 'Bahia'},
    'CE': {'vacancies': 425, 'state_name': 'Ceará'},
    'DF': {'vacancies': 156, 'state_name': 'Distrito Federal'},
    'ES': {'vacancies': 152, 'state_name': 'Espírito Santo'},
    'GO': {'vacancies': 287, 'state_name': 'Goiás'},
    'MA': {'vacancies': 298, 'state_name': 'Maranhão'},
    'MT': {'vacancies': 146, 'state_name': 'Mato Grosso'},
    'MS': {'vacancies': 118, 'state_name': 'Mato Grosso do Sul'},
    'MG': {'vacancies': 756, 'state_name': 'Minas Gerais'},
    'PA': {'vacancies': 356, 'state_name': 'Pará'},
    'PB': {'vacancies': 178, 'state_name': 'Paraíba'},
    'PR': {'vacancies': 324, 'state_name': 'Paraná'},
    'PE': {'vacancies': 398, 'state_name': 'Pernambuco'},
    'PI': {'vacancies': 142, 'state_name': 'Piauí'},
    'RJ': {'vacancies': 412, 'state_name': 'Rio de Janeiro'},
    'RN': {'vacancies': 156, 'state_name': 'Rio Grande do Norte'},
    'RS': {'vacancies': 398, 'state_name': 'Rio Grande do Sul'},
    'RO': {'vacancies': 78, 'state_name': 'Rondônia'},
    'RR': {'vacancies': 32, 'state_name': 'Roraima'},
    'SC': {'vacancies': 234, 'state_name': 'Santa Catarina'},
    'SP': {'vacancies': 892, 'state_name': 'São Paulo'},
    'SE': {'vacancies': 89, 'state_name': 'Sergipe'},
    'TO': {'vacancies': 128, 'state_name': 'Tocantins'}
}

# Salários por estado baseados em dados regionais
STATE_SALARIES = {
    'SP': 'R$ 3.800,00', 'RJ': 'R$ 3.600,00', 'DF': 'R$ 4.200,00',
    'MG': 'R$ 3.200,00', 'RS': 'R$ 3.400,00', 'PR': 'R$ 3.100,00',
    'SC': 'R$ 3.300,00', 'BA': 'R$ 2.900,00', 'GO': 'R$ 2.800,00',
    'PE': 'R$ 2.700,00', 'CE': 'R$ 2.600,00', 'PA': 'R$ 2.700,00',
    'MA': 'R$ 2.500,00', 'PB': 'R$ 2.400,00', 'ES': 'R$ 3.000,00',
    'PI': 'R$ 2.350,00', 'AL': 'R$ 2.300,00', 'MT': 'R$ 2.900,00',
    'MS': 'R$ 2.800,00', 'SE': 'R$ 2.250,00', 'AM': 'R$ 2.800,00',
    'RO': 'R$ 2.600,00', 'AC': 'R$ 2.500,00', 'AP': 'R$ 2.600,00',
    'RR': 'R$ 2.700,00', 'TO': 'R$ 2.400,00', 'RN': 'R$ 2.500,00'
}

def get_vacancy_distribution(state_code, num_units):
    """
    Distribui as vagas do estado entre as unidades CRAS encontradas
    """
    if state_code not in STATE_VACANCIES:
        return {
            'vacancies_per_unit': 3,
            'total_vacancies': num_units * 3,
            'salary': 'R$ 2.500,00'
        }
    
    state_data = STATE_VACANCIES[state_code]
    total_vacancies = state_data['vacancies']
    salary = STATE_SALARIES.get(state_code, 'R$ 2.500,00')
    
    # Distribuição equilibrada
    base_vacancies = total_vacancies // num_units
    remaining_vacancies = total_vacancies % num_units
    
    # Cada unidade recebe pelo menos base_vacancies
    # As primeiras 'remaining_vacancies' unidades recebem +1
    vacancies_per_unit = base_vacancies + (1 if remaining_vacancies > 0 else 0)
    
    return {
        'vacancies_per_unit': vacancies_per_unit,
        'total_vacancies': total_vacancies,
        'salary': salary,
        'base_vacancies': base_vacancies,
        'extra_units': remaining_vacancies
    }

def get_unit_specific_vacancies(state_code, unit_index, num_units):
    """
    Retorna o número específico de vagas para uma unidade
    """
    distribution = get_vacancy_distribution(state_code, num_units)
    
    # Primeiras unidades recebem vaga extra se houver resto
    if unit_index < distribution['extra_units']:
        return distribution['base_vacancies'] + 1
    else:
        return distribution['base_vacancies']

if __name__ == "__main__":
    # Test distribution
    print("Teste de distribuição de vagas:")
    print(f"DF (32 unidades): {get_vacancy_distribution('DF', 32)}")
    print(f"SP (10 unidades): {get_vacancy_distribution('SP', 10)}")
    print(f"AC (8 unidades): {get_vacancy_distribution('AC', 8)}")
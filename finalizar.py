import os
import requests
from datetime import datetime
from flask import current_app, request
from typing import Dict, Any, Optional
import random
import string

class For4PaymentsAPI:
    API_URL = "https://app.for4payments.com.br/api/v1"

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.extra_headers = {}

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            'Authorization': self.secret_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        if self.extra_headers:
            headers.update(self.extra_headers)
            current_app.logger.debug(f"Usando headers personalizados: {headers}")

        return headers

    def _generate_random_email(self, name: str) -> str:
        clean_name = ''.join(e.lower() for e in name if e.isalnum())
        random_num = ''.join(random.choices(string.digits, k=4))
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        domain = random.choice(domains)
        return f"{clean_name}{random_num}@{domain}"

    def _generate_random_phone(self) -> str:
        ddd = str(random.randint(11, 99))
        number = ''.join(random.choices(string.digits, k=9))
        return f"{ddd}{number}"

    def create_pix_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a PIX payment request"""
        # Validation of authentication token
        if not self.secret_key:
            current_app.logger.error("Token de autenticação não fornecido")
            raise ValueError("Token de autenticação não foi configurado")
        elif len(self.secret_key) < 10:
            current_app.logger.error(f"Token de autenticação muito curto ({len(self.secret_key)} caracteres)")
            raise ValueError("Token de autenticação inválido (muito curto)")
        else:
            current_app.logger.info(f"Utilizando token de autenticação: {self.secret_key[:3]}...{self.secret_key[-3:]} ({len(self.secret_key)} caracteres)")

        # Log received data
        safe_data = {k: v for k, v in data.items()}
        if 'cpf' in safe_data:
            safe_data['cpf'] = f"{safe_data['cpf'][:3]}...{safe_data['cpf'][-2:]}" if len(safe_data['cpf']) > 5 else "***"
        current_app.logger.info(f"Dados recebidos para pagamento: {safe_data}")

        # Validate required fields
        required_fields = ['name', 'email', 'cpf', 'amount']
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)

        if missing_fields:
            current_app.logger.error(f"Campos obrigatórios ausentes: {missing_fields}")
            raise ValueError(f"Campos obrigatórios ausentes: {', '.join(missing_fields)}")

        try:
            # Amount validation and conversion
            try:
                amount_in_cents = int(float(data['amount']) * 100)
                current_app.logger.info(f"Valor do pagamento: R$ {float(data['amount']):.2f} ({amount_in_cents} centavos)")
            except (ValueError, TypeError) as e:
                current_app.logger.error(f"Erro ao converter valor do pagamento: {str(e)}")
                raise ValueError(f"Valor de pagamento inválido: {data['amount']}")

            if amount_in_cents <= 0:
                current_app.logger.error(f"Valor do pagamento não positivo: {amount_in_cents}")
                raise ValueError("Valor do pagamento deve ser maior que zero")

            # CPF processing
            cpf = ''.join(filter(str.isdigit, str(data['cpf'])))
            if len(cpf) != 11:
                current_app.logger.error(f"CPF com formato inválido: {cpf} (comprimento: {len(cpf)})")
                raise ValueError("CPF inválido - deve conter 11 dígitos")
            else:
                current_app.logger.info(f"CPF validado: {cpf[:3]}...{cpf[-2:]}")

            # Email validation and generation
            email = data.get('email')
            if not email or '@' not in email:
                email = self._generate_random_email(data['name'])
                current_app.logger.info(f"Email gerado automaticamente: {email}")
            else:
                current_app.logger.info(f"Email fornecido: {email}")

            # Phone processing
            phone = data.get('phone', '')

            if phone and isinstance(phone, str) and len(phone.strip()) > 0:
                phone = ''.join(filter(str.isdigit, phone))

                if len(phone) >= 10:
                    if phone.startswith('55') and len(phone) > 10:
                        phone = phone[2:]
                    current_app.logger.info(f"Telefone do usuário processado: {phone}")
                else:
                    current_app.logger.warning(f"Telefone fornecido inválido (muito curto): {phone}")
                    phone = self._generate_random_phone()
                    current_app.logger.info(f"Telefone gerado automaticamente como fallback: {phone}")
            else:
                phone = self._generate_random_phone()
                current_app.logger.info(f"Telefone não fornecido, gerado automaticamente: {phone}")

            # Prepare payment data for API
            payment_data = {
                "name": data['name'],
                "email": email,
                "cpf": cpf,
                "phone": phone,
                "paymentMethod": "PIX",
                "amount": amount_in_cents,
                "items": [{
                    "title": data.get('description', 'Taxa de Expedição da CNV'),
                    "quantity": 1,
                    "unitPrice": amount_in_cents,
                    "tangible": False
                }]
            }

            current_app.logger.info(f"Dados de pagamento formatados: {payment_data}")
            current_app.logger.info(f"Endpoint API: {self.API_URL}/transaction.purchase")
            current_app.logger.info("Enviando requisição para API For4Payments...")

            try:
                # Generate random headers to avoid blocks
                import time

                user_agents = [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
                    "Mozilla/5.0 (Android 12; Mobile; rv:68.0) Gecko/68.0 Firefox/94.0",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0"
                ]

                languages = [
                    "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                    "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
                    "es-ES,es;q=0.9,pt;q=0.8,en;q=0.7"
                ]

                extra_headers = {
                    "User-Agent": random.choice(user_agents),
                    "Accept-Language": random.choice(languages),
                    "Cache-Control": random.choice(["max-age=0", "no-cache"]),
                    "X-Requested-With": "XMLHttpRequest",
                    "X-Cache-Buster": str(int(time.time() * 1000)),
                    "Referer": "https://prosegur-fed.replit.app/finalizar",
                    "Sec-Fetch-Site": "same-origin",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Dest": "empty"
                }

                headers = self._get_headers()
                headers.update(extra_headers)

                current_app.logger.info(f"Usando headers aleatórios para For4Payments API")

                response = requests.post(
                    f"{self.API_URL}/transaction.purchase",
                    json=payment_data,
                    headers=headers,
                    timeout=30
                )

                current_app.logger.info(f"Resposta recebida (Status: {response.status_code})")
                current_app.logger.debug(f"Resposta completa: {response.text}")

                if response.status_code == 200:
                    response_data = response.json()
                    current_app.logger.info(f"Resposta da API: {response_data}")

                    # Log detailed fields to identify all relevant fields
                    pixcode_fields = []
                    qrcode_fields = []

                    # Check main fields at first level
                    for field in ['pixCode', 'copy_paste', 'code', 'pix_code']:
                        if field in response_data:
                            pixcode_fields.append(f"{field}: {str(response_data.get(field))[:30]}...")

                    for field in ['pixQrCode', 'qr_code_image', 'qr_code', 'pix_qr_code']:
                        if field in response_data:
                            qrcode_fields.append(f"{field}: presente")

                    # Check nested structures (pix)
                    if 'pix' in response_data and isinstance(response_data.get('pix'), dict):
                        pix_data = response_data.get('pix', {})
                        for field in ['code', 'copy_paste', 'pixCode']:
                            if field in pix_data:
                                pixcode_fields.append(f"pix.{field}: {str(pix_data.get(field))[:30]}...")

                        for field in ['qrCode', 'qr_code_image', 'pixQrCode']:
                            if field in pix_data:
                                qrcode_fields.append(f"pix.{field}: presente")

                    current_app.logger.info(f"Campos de código PIX encontrados: {pixcode_fields}")
                    current_app.logger.info(f"Campos de QR code encontrados: {qrcode_fields}")

                    # Format result with support for multiple response formats
                    result = {
                        'success': True,
                        'paymentId': response_data.get('id') or response_data.get('transactionId'),
                        'pixCopyPaste': (
                            response_data.get('pixCode') or 
                            response_data.get('copy_paste') or 
                            response_data.get('code') or 
                            response_data.get('pix_code') or
                            (response_data.get('pix', {}) or {}).get('code') or 
                            (response_data.get('pix', {}) or {}).get('copy_paste')
                        ),
                        'pixQrCode': (
                            response_data.get('pixQrCode') or 
                            response_data.get('qr_code_image') or 
                            response_data.get('qr_code') or 
                            response_data.get('pix_qr_code') or
                            (response_data.get('pix', {}) or {}).get('qrCode') or 
                            (response_data.get('pix', {}) or {}).get('qr_code_image')
                        ),
                        'expiresAt': response_data.get('expiresAt') or response_data.get('expiration'),
                        'status': response_data.get('status', 'pending'),
                        'amount': float(data['amount'])
                    }

                    current_app.logger.info(f"Resposta mapeada para o formato padrão: {result}")

                    transaction_id = result.get('paymentId')
                    current_app.logger.info(f"Transação {transaction_id} processada com sucesso")

                    return result
                elif response.status_code == 401:
                    current_app.logger.error("Erro de autenticação com a API For4Payments")
                    raise ValueError("Falha na autenticação com a API For4Payments. Verifique a chave de API.")
                else:
                    error_message = 'Erro ao processar pagamento'
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict):
                            error_message = error_data.get('message') or error_data.get('error') or '; '.join(error_data.get('errors', []))
                            current_app.logger.error(f"Erro da API For4Payments: {error_message}")
                    except Exception as e:
                        error_message = f'Erro ao processar pagamento (Status: {response.status_code})'
                        current_app.logger.error(f"Erro ao processar resposta da API: {str(e)}")
                    raise ValueError(error_message)

            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"Erro de conexão com a API For4Payments: {str(e)}")
                raise ValueError("Erro de conexão com o serviço de pagamento. Tente novamente em alguns instantes.")

        except ValueError as e:
            current_app.logger.error(f"Erro de validação: {str(e)}")
            raise
        except Exception as e:
            current_app.logger.error(f"Erro inesperado ao processar pagamento: {str(e)}")
            raise ValueError("Erro interno ao processar pagamento. Por favor, tente novamente.")

    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Check the status of a payment"""
        try:
            current_app.logger.info(f"Verificando status do pagamento {payment_id}")
            
            headers = self._get_headers()
            
            response = requests.get(
                f"{self.API_URL}/transaction/{payment_id}",
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': data.get('status', 'pending'),
                    'payment_id': payment_id
                }
            else:
                current_app.logger.error(f"Erro ao verificar status: {response.status_code}")
                return {'status': 'pending', 'payment_id': payment_id}
                
        except Exception as e:
            current_app.logger.error(f"Erro ao verificar status do pagamento: {str(e)}")
            return {'status': 'pending', 'payment_id': payment_id}

    def create_encceja_payment(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a PIX payment for CNV expedition fee"""
        current_app.logger.info(f"Solicitação de pagamento CNV recebida: {user_data}")

        # Validate required data
        if not user_data:
            current_app.logger.error("Dados de usuário vazios")
            raise ValueError("Nenhum dado de usuário fornecido")

        if not user_data.get('nome'):
            current_app.logger.error("Nome do usuário não fornecido")
            raise ValueError("Nome do usuário é obrigatório")

        if not user_data.get('cpf'):
            current_app.logger.error("CPF do usuário não fornecido")
            raise ValueError("CPF do usuário é obrigatório")

        # Use provided amount or default CNV fee
        amount = user_data.get('amount', 82.10)
        current_app.logger.info(f"Valor da taxa CNV: R$ {amount:.2f}")

        try:
            # Format CPF to remove non-numeric characters
            cpf_original = user_data.get('cpf', '')
            cpf = ''.join(filter(str.isdigit, str(cpf_original)))
            if len(cpf) != 11:
                current_app.logger.warning(f"CPF com formato inválido: {cpf_original} → {cpf} ({len(cpf)} dígitos)")
            else:
                current_app.logger.info(f"CPF formatado: {cpf[:3]}...{cpf[-2:]}")

            # Generate random email based on user name
            nome = user_data.get('nome', '').strip()
            email = self._generate_random_email(nome)
            current_app.logger.info(f"Email gerado: {email}")

            # Clean phone if provided, or generate random
            phone_original = user_data.get('phone', user_data.get('telefone', ''))
            phone_digits = ''.join(filter(str.isdigit, str(phone_original)))

            if not phone_digits or len(phone_digits) < 10:
                phone = self._generate_random_phone()
                current_app.logger.info(f"Telefone inválido '{phone_original}', gerado novo: {phone}")
            else:
                phone = phone_digits
                current_app.logger.info(f"Telefone formatado: {phone}")

            current_app.logger.info(f"Preparando pagamento para: {nome} (CPF: {cpf[:3]}...{cpf[-2:]})")

            # Format data for payment
            payment_data = {
                'name': nome,
                'email': email,
                'cpf': cpf,
                'amount': amount,
                'phone': phone,
                'description': user_data.get('description', 'Taxa de Expedição da CNV - Ministério da Justiça')
            }

            current_app.logger.info("Chamando API de pagamento PIX")
            result = self.create_pix_payment(payment_data)

            if result and result.get('success'):
                current_app.logger.info(f"Pagamento CNV criado com sucesso: {result.get('paymentId')}")
                return result
            else:
                error_msg = result.get('error', 'Erro desconhecido') if result else 'Resposta vazia da API'
                current_app.logger.error(f"Falha ao criar pagamento CNV: {error_msg}")
                raise ValueError(f"Erro ao criar pagamento: {error_msg}")

        except Exception as e:
            current_app.logger.error(f"Erro no create_encceja_payment: {str(e)}")
            raise

def create_payment_api(secret_key: Optional[str] = None) -> For4PaymentsAPI:
    """Factory function to create For4PaymentsAPI instance"""
    if secret_key is None:
        secret_key = os.environ.get('FOR4_PAYMENTS_SECRET_KEY')
    
    if not secret_key:
        raise ValueError("FOR4_PAYMENTS_SECRET_KEY não configurada")
    
    return For4PaymentsAPI(secret_key)
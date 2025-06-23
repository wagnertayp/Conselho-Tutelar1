"""
SafeFlow PIX API integration for Conselheiro Tutelar exam payments
"""
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

class SafeFlowAPI:
    """SafeFlow PIX payment API integration"""
    
    BASE_URL = "https://dev.thesafeflow.com/api/v1"
    API_KEY = "pk_5291b0577774dbc817fb4721b076844285e9acff21ae02c1d4c16216cd4ceaee"
    CAMPAIGN_TOKEN = "VKYNPM6O-MBV5YG2Y"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            'x-api-key': self.API_KEY,
            'Content-Type': 'application/json'
        }
    
    def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a PIX payment using SafeFlow API
        
        Args:
            payment_data: Dictionary containing:
                - amount: Payment amount (float)
                - name: Payer name
                - email: Payer email  
                - cpf: Payer CPF
                - phone: Payer phone
        
        Returns:
            Dictionary with payment information or error
        """
        url = f"{self.BASE_URL}/payment/{self.CAMPAIGN_TOKEN}"
        
        # Format data according to SafeFlow API requirements
        payload = {
            "amount": float(payment_data.get('amount', 63.20)),
            "name": payment_data.get('name', '') or payment_data.get('full_name', ''),
            "email": payment_data.get('email', 'damgov@gmail.com'),
            "cpf": payment_data.get('cpf', '').replace('.', '').replace('-', '') if payment_data.get('cpf') else '',
            "phone": payment_data.get('phone', '11999876978').replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
        }
        
        try:
            self.logger.info(f"Creating SafeFlow payment with data: {payload}")
            print(f"SafeFlow URL: {url}")
            print(f"SafeFlow Headers: {self._get_headers()}")
            print(f"SafeFlow Payload: {payload}")
            
            response = requests.post(
                url, 
                json=payload, 
                headers=self._get_headers(),
                timeout=30
            )
            
            self.logger.info(f"SafeFlow API response status: {response.status_code}")
            print(f"SafeFlow Response Status: {response.status_code}")
            print(f"SafeFlow Response Text: {response.text}")
            
            if response.status_code == 201:
                result = response.json()
                self.logger.info(f"Payment created successfully: {result.get('paymentId')}")
                return {
                    'success': True,
                    'paymentId': result.get('paymentId'),
                    'pixCode': result.get('pixCode'),
                    'pixQrCode': result.get('pixQrCode'),
                    'expiresAt': result.get('expiresAt'),
                    'status': result.get('status', 'pending'),
                    'campaign': result.get('campaign', {}),
                    'amount': payload['amount']
                }
            else:
                error_msg = f"SafeFlow API error: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                
                self.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error calling SafeFlow API: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error with SafeFlow API: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Check payment status using SafeFlow API
        
        Args:
            payment_id: Payment ID to check
            
        Returns:
            Dictionary with payment status information
        """
        url = f"{self.BASE_URL}/{self.CAMPAIGN_TOKEN}/status/{payment_id}"
        
        try:
            self.logger.info(f"Checking SafeFlow payment status for: {payment_id}")
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            
            self.logger.info(f"SafeFlow status check response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'paymentId': result.get('paymentId'),
                    'status': result.get('status'),
                    'pixQrCode': result.get('pixQrCode'),
                    'pixCode': result.get('pixCode'),
                    'campaign': result.get('campaign', {})
                }
            else:
                error_msg = f"SafeFlow status check error: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                
                self.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error checking SafeFlow payment status: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Unexpected error checking SafeFlow payment status: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

def create_safeflow_api() -> SafeFlowAPI:
    """Factory function to create SafeFlowAPI instance"""
    return SafeFlowAPI()
"""
Meta Pixel Integration for conversion tracking
Simple pixel tracking using only Pixel IDs for JavaScript-based events
"""

import os
import logging
from typing import Dict, List, Any

class MetaPixelTracker:
    def __init__(self):
        self._pixels_cache = None
        
    @property
    def pixels(self):
        """Lazy load pixels when needed"""
        if self._pixels_cache is None:
            self._pixels_cache = self._load_pixel_configs()
        return self._pixels_cache
        
    def _load_pixel_configs(self) -> List[Dict]:
        """Load pixel configurations from environment variables"""
        pixels = []
        
        for i in range(1, 7):  # Support 6 pixels
            pixel_id = os.environ.get(f'META_PIXEL_{i}_ID')
            
            if pixel_id:
                pixels.append({
                    'id': pixel_id,
                    'name': f'Pixel_{i}'
                })
        
        return pixels
    
    def get_pixel_ids(self) -> List[str]:
        """Get list of configured pixel IDs"""
        return [pixel['id'] for pixel in self.pixels]
    
    def generate_facebook_pixel_code(self) -> str:
        """Generate Facebook Pixel JavaScript code for all configured pixels"""
        if not self.pixels:
            return ""
        
        # Base Facebook Pixel code
        pixel_code = """
<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
"""
        
        # Initialize each pixel
        for pixel in self.pixels:
            pixel_code += f"fbq('init', '{pixel['id']}');\n"
        
        # Track PageView for all pixels
        pixel_code += "fbq('track', 'PageView');\n"
        pixel_code += "</script>\n"
        
        # NoScript fallback for each pixel
        for pixel in self.pixels:
            pixel_code += f"""<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id={pixel['id']}&ev=PageView&noscript=1"
/></noscript>\n"""
        
        pixel_code += "<!-- End Meta Pixel Code -->"
        
        return pixel_code
    
    def generate_purchase_event_js(self, customer_info: Dict, purchase_data: Dict) -> str:
        """Generate JavaScript code to fire Purchase event"""
        if not self.pixels:
            return ""
        
        # Prepare event data
        event_data = {
            'value': purchase_data.get('amount', 0),
            'currency': 'BRL',
            'content_type': 'product',
            'content_ids': [purchase_data.get('transaction_id', 'cnv_payment')],
            'content_name': 'CNV - Carteira Nacional de Vigilante'
        }
        
        # Add customer data if available
        customer_data = {}
        if customer_info.get('email'):
            customer_data['em'] = customer_info['email'].lower().strip()
        if customer_info.get('phone'):
            # Clean phone number
            phone = ''.join(filter(str.isdigit, customer_info['phone']))
            customer_data['ph'] = phone
        if customer_info.get('full_name'):
            name_parts = customer_info['full_name'].strip().lower().split()
            if len(name_parts) >= 1:
                customer_data['fn'] = name_parts[0]
            if len(name_parts) >= 2:
                customer_data['ln'] = name_parts[-1]
        if customer_info.get('city'):
            customer_data['ct'] = customer_info['city'].lower().strip()
        if customer_info.get('state'):
            customer_data['st'] = customer_info['state'].lower().strip()
        if customer_info.get('zip_code'):
            customer_data['zp'] = ''.join(filter(str.isdigit, customer_info['zip_code']))
        
        # Generate JavaScript
        import json
        js_code = f"""
<script>
// Fire Purchase event for all configured pixels
fbq('track', 'Purchase', {json.dumps(event_data)}, {json.dumps(customer_data)});
console.log('Meta Pixel Purchase event fired for {len(self.pixels)} pixels');
</script>
"""
        
        return js_code
    
    def send_purchase_event(self, customer_info: Dict, purchase_data: Dict) -> Dict:
        """
        Generate Purchase event data for client-side firing
        Returns JavaScript code to be executed on the client
        """
        try:
            if not self.pixels:
                return {
                    'success': False,
                    'message': 'Nenhum pixel configurado',
                    'js_code': '',
                    'total_pixels': 0
                }
            
            js_code = self.generate_purchase_event_js(customer_info, purchase_data)
            
            return {
                'success': True,
                'message': f'Evento Purchase preparado para {len(self.pixels)} pixels',
                'js_code': js_code,
                'total_pixels': len(self.pixels),
                'pixel_ids': self.get_pixel_ids()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao preparar evento: {str(e)}',
                'js_code': '',
                'total_pixels': 0
            }
    
    def test_pixel_configuration(self) -> Dict:
        """Test pixel configuration"""
        try:
            pixels = self.pixels
            
            if not pixels:
                return {
                    'success': False,
                    'message': 'Nenhum pixel configurado',
                    'total_pixels': 0,
                    'results': []
                }
            
            results = []
            for pixel in pixels:
                results.append({
                    'pixel_name': pixel['name'],
                    'pixel_id': pixel['id'],
                    'success': True,
                    'message': 'Pixel ID configurado corretamente'
                })
            
            return {
                'success': True,
                'message': f'{len(pixels)} pixels configurados',
                'total_pixels': len(pixels),
                'successful_tests': len(pixels),
                'results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro ao testar configuração: {str(e)}',
                'total_pixels': 0,
                'results': []
            }
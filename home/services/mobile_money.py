# home/services/mobile_money.py
from venv import logger
import requests
from django.conf import settings
from django.core.exceptions import ValidationError

def initier_transaction_mobile_money(montant, numero_telephone, reference):
    """
    Initie une transaction Mobile Money avec les services locaux
    """
    if not settings.MOBILE_MONEY_API_KEY:
        raise ValidationError("Configuration Mobile Money manquante")
    
    payload = {
        'amount': montant,
        'phone': numero_telephone,
        'reference': reference,
        'api_key': settings.MOBILE_MONEY_API_KEY
    }
    
    try:
        response = requests.post(
            settings.MOBILE_MONEY_API_URL,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # En cas d'erreur, enregistrer la tentative
        logger.error(f"Erreur Mobile Money: {str(e)}")
        return {'success': False, 'error': str(e)}
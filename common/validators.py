from django.core.exceptions import ValidationError
import re

def validate_phone_number(value):
    """Validate phone number format"""
    pattern = r'^\+?1?\d{9,15}$'
    if not re.match(pattern, value):
        raise ValidationError('Invalid phone number format')

def validate_pin(value):
    """Validate 4-digit PIN"""
    if not value.isdigit() or len(value) != 4:
        raise ValidationError('PIN must be exactly 4 digits')

def validate_positive_amount(value):
    """Ensure amount is positive"""
    if value <= 0:
        raise ValidationError('Amount must be greater than zero')
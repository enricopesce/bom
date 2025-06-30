"""
Currency utilities for dynamic currency formatting
"""

from typing import Dict


def get_currency_symbol(currency: str) -> str:
    """Get currency symbol for a given currency code"""
    symbols = {
        "EUR": "€",
        "USD": "$",
        "GBP": "£",
        "JPY": "¥",
        "CAD": "C$",
        "AUD": "A$",
        "CHF": "CHF",
        "CNY": "¥",
        "INR": "₹"
    }
    return symbols.get(currency.upper(), currency)


def format_currency(amount: float, currency: str) -> str:
    """Format currency amount with appropriate symbol"""
    symbol = get_currency_symbol(currency)
    return f"{symbol}{amount:,.2f}"


def get_excel_currency_format(currency: str) -> str:
    """Get Excel number format string for currency"""
    symbol = get_currency_symbol(currency)
    return f"{symbol}#,##0.00"


def get_currency_display_name(currency: str) -> str:
    """Get display name for currency in headers and labels"""
    names = {
        "EUR": "Euro",
        "USD": "US Dollar", 
        "GBP": "British Pound",
        "JPY": "Japanese Yen",
        "CAD": "Canadian Dollar",
        "AUD": "Australian Dollar",
        "CHF": "Swiss Franc",
        "CNY": "Chinese Yuan",
        "INR": "Indian Rupee"
    }
    return names.get(currency.upper(), currency)
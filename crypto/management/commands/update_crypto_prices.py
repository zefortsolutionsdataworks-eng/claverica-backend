from django.core.management.base import BaseCommand
from crypto.services import CryptoService

class Command(BaseCommand):
    help = 'Update cryptocurrency prices (mock for development)'

    def handle(self, *args, **options):
        self.stdout.write('Updating crypto prices...')
        
        currencies = CryptoService.update_mock_prices()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated prices for {len(currencies)} cryptocurrencies'
            )
        )
        
        for currency in currencies:
            self.stdout.write(
                f"  {currency.symbol}:  "
                f"({currency.percent_change_24h:+.2f}%)"
            )

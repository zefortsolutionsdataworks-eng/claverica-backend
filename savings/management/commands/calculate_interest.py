from django.core.management.base import BaseCommand
from savings.services import SavingsService

class Command(BaseCommand):
    help = 'Calculate and credit daily interest for all savings accounts'

    def handle(self, *args, **options):
        self.stdout.write('Starting interest calculation...')
        
        results = SavingsService.calculate_interest_for_all_accounts()
        
        success_count = len([r for r in results if r['status'] == 'success'])
        failed_count = len([r for r in results if r['status'] == 'failed'])
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Interest calculation completed: {success_count} successful, {failed_count} failed'
            )
        )
        
        if failed_count > 0:
            self.stdout.write(self.style.WARNING('Failed accounts:'))
            for result in results:
                if result['status'] == 'failed':
                    self.stdout.write(f"  - {result['user']}: {result.get('error', 'Unknown error')}")

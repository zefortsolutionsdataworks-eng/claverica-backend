from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Create initial system data"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Creating initial data...")

        # ✅ Import INSIDE handle (registry is fully ready here)
        from loans.models import LoanProduct

        products = [
            {
                "name": "Personal Loan",
                "interest_rate": 12.50,
                "minimum_amount": 1000,
                "maximum_amount": 100000,
                "minimum_tenure_days": 30,
                "maximum_tenure_days": 365,
                "origination_fee_percentage": 2.0,
                "description": "Standard personal loan product",
            },
            {
                "name": "Business Loan",
                "interest_rate": 10.00,
                "minimum_amount": 5000,
                "maximum_amount": 500000,
                "minimum_tenure_days": 60,
                "maximum_tenure_days": 730,
                "origination_fee_percentage": 1.5,
                "description": "SME and business loan product",
            },
        ]

        created = 0
        for product in products:
            _, was_created = LoanProduct.objects.get_or_create(
                name=product["name"],
                defaults=product,
            )
            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Initial data created successfully ({created} loan products)"
            )
        )

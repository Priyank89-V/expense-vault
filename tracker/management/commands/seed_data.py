from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tracker.seed_data import ensure_default_categories, populate_sample_data


class Command(BaseCommand):
    help = 'Seeds default categories and creates sample demo transactions for a demo user'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Username to assign demo data to')

    def handle(self, *args, **options):
        ensure_default_categories()
        self.stdout.write(self.style.SUCCESS("Default categories created/verified."))

        username = options['username']
        user = User.objects.filter(username=username).first()
        if user:
            populate_sample_data(user)
            self.stdout.write(self.style.SUCCESS(f"Sample transactions populated for user '{username}'!"))
        else:
            self.stdout.write(self.style.WARNING(f"User '{username}' not found. Default categories are initialized. You can register/login in the browser and click 'Load Demo Data'."))

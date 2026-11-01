from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from core.permissions import ROLE_ACADEMIC, ROLE_ADMIN, ROLE_FINANCE


class Command(BaseCommand):
    help = "Create the standard staff role groups used by the website."

    def handle(self, *args, **options):
        for role_name in (ROLE_ADMIN, ROLE_ACADEMIC, ROLE_FINANCE):
            _, created = Group.objects.get_or_create(name=role_name)
            state = "created" if created else "already exists"
            self.stdout.write(f"{role_name}: {state}")

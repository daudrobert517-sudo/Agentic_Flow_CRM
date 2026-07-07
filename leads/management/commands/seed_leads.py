import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker
from leads.models import PipelineStage, Lead, Activity

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Seeds the database with fake leads spread across the last 6 months'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100, help='Number of leads to create')
        parser.add_argument('--clear', action='store_true', help='Clear existing leads before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            Lead.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared existing leads.'))

        count = options['count']
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No user found. Create a user first.'))
            return

        stages = list(PipelineStage.objects.all())
        if not stages:
            self.stdout.write(self.style.ERROR('No pipeline stages found. Run migrate first.'))
            return

        won_stage = next((s for s in stages if s.name == 'Won'), None)
        sources = ['website', 'referral', 'cold_call', 'social_media', 'other']
        activity_types = ['call', 'email', 'meeting', 'note']

        now = timezone.now()
        created_count = 0

        for i in range(count):
            days_ago = random.randint(0, 180)
            created_date = now - timedelta(days=days_ago)

            if won_stage and random.random() < 0.19:
                stage = won_stage
            else:
                non_won = [s for s in stages if s.name != 'Won']
                stage = random.choice(non_won)

            lead = Lead(
                owner=user,
                stage=stage,
                name=fake.name(),
                email=fake.email(),
                phone=fake.phone_number()[:20],
                company=fake.company(),
                source=random.choice(sources),
                value=Decimal(random.randint(500, 50000)),
                notes=fake.sentence(),
                stage_changed_at=created_date,
            )
            lead.save()

            Lead.objects.filter(pk=lead.pk).update(
                created_at=created_date,
                updated_at=created_date,
            )

            for _ in range(random.randint(0, 3)):
                activity_date = created_date + timedelta(days=random.randint(0, min(days_ago, 14)))
                activity = Activity(
                    lead=lead,
                    owner=user,
                    activity_type=random.choice(activity_types),
                    description=fake.sentence(),
                )
                activity.save()
                Activity.objects.filter(pk=activity.pk).update(created_at=activity_date)

            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} leads spread across the last 6 months.'))
from django.core.management.base import BaseCommand
from storyapp.models import Theme


class Command(BaseCommand):
    help = 'Populates the database with initial theme data'

    def handle(self, *args, **kwargs):
        # Define the themes to create
        themes = [
            {
                'name': 'Space Adventure',
                'description': 'An exciting journey through space, encountering alien civilizations and cosmic wonders.',
            },
            {
                'name': 'Fantasy Quest',
                'description': 'A magical adventure in a world of wizards, dragons, and mythical creatures.',
            },
            {
                'name': 'Underwater Exploration',
                'description': 'Discover the mysteries of the deep ocean and the creatures that inhabit it.',
            },
            {
                'name': 'Superhero',
                'description': 'A heroic journey of a character with extraordinary abilities saving the world from villains.',
            },
            {
                'name': 'Jungle Expedition',
                'description': 'An adventure through dense jungles, discovering ancient ruins and exotic wildlife.',
            },
            {
                'name': 'Time Travel',
                'description': 'Journey through different time periods, from dinosaurs to the far future.',
            },
        ]

        # Create themes in the database
        for theme_data in themes:
            theme, created = Theme.objects.get_or_create(
                name=theme_data['name'],
                defaults={'description': theme_data['description']}
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created theme: {theme.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Theme already exists: {theme.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully populated themes'))

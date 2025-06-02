import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Initializes the project by creating necessary directories and running migrations'

    def handle(self, *args, **kwargs):
        # Create media directories if they don't exist
        media_dirs = ['plots', 'responses', 'pdfs']
        for directory in media_dirs:
            path = os.path.join(settings.MEDIA_ROOT, directory)
            if not os.path.exists(path):
                os.makedirs(path)
                self.stdout.write(self.style.SUCCESS(f'Created directory: {path}'))
            else:
                self.stdout.write(f'Directory already exists: {path}')
                
        # Create static directories if they don't exist
        static_dirs = ['css', 'js', 'img']
        for directory in static_dirs:
            path = os.path.join(settings.BASE_DIR, 'static', directory)
            if not os.path.exists(path):
                os.makedirs(path)
                self.stdout.write(self.style.SUCCESS(f'Created directory: {path}'))
            else:
                self.stdout.write(f'Directory already exists: {path}')
                
        # Create templates directories if they don't exist
        template_dirs = ['storyapp']
        for directory in template_dirs:
            path = os.path.join(settings.BASE_DIR, 'templates', directory)
            if not os.path.exists(path):
                os.makedirs(path)
                self.stdout.write(self.style.SUCCESS(f'Created directory: {path}'))
            else:
                self.stdout.write(f'Directory already exists: {path}')
                
        self.stdout.write(self.style.SUCCESS('Project initialized successfully!'))
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Run migrations: python manage.py migrate')
        self.stdout.write('2. Create admin user: python manage.py createsuperuser')
        self.stdout.write('3. Populate themes: python manage.py populate_themes')
        self.stdout.write('4. Add API keys to .env file or settings.py')
        self.stdout.write('5. Run the server: python manage.py runserver')

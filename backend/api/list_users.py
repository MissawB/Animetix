import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')

import django
django.setup()

from django.contrib.auth.models import User

print("Usernames in DB:")
for u in User.objects.all():
    print(f"- '{u.username}'")

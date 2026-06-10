import os
import sys

# The backend directory structure is:
# /backend/
#   /api/
#   /pipeline/
#   /adapters/
# So we need to add the parent 'backend' directory to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(backend_path)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'animetix_project.settings')

import django
django.setup()

from django.contrib.auth.models import User

print("Usernames in DB:")
for u in User.objects.all():
    print(f"- '{u.username}'")

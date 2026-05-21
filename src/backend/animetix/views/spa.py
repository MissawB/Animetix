from django.shortcuts import render
from django.conf import settings
import os

def spa_view(request, path=None):
    """
    Vue catch-all pour servir l'application React.
    Django sert le template index.html, qui pointe vers le bundle React.
    """
    return render(request, 'index.html')

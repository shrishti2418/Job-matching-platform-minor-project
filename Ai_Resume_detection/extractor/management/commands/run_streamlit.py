import os
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
import django

class Command(BaseCommand):
    help = 'Run Streamlit app with Django integration'
    
    def add_arguments(self, parser):
        parser.add_argument('--port', type=int, default=8501, help='Port to run Streamlit on')
        parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    
    def handle(self, *args, **options):
        # Ensure Django is set up
        django.setup()
        
        # Set environment for Streamlit to find Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Ai_Resume_detection.settings')
        
        # Import and run Streamlit
        import streamlit.web.cli as stcli
        import streamlit as st
        
        # Path to your Streamlit app
        app_path = os.path.join(settings.BASE_DIR, 'extractor', 'streamlit_apps', 'main_app.py')
        
        # Run Streamlit
        sys.argv = [
            "streamlit", 
            "run", 
            app_path,
            "--server.port", str(options['port']),
            "--server.address", options['host']
        ]
        
        stcli.main()

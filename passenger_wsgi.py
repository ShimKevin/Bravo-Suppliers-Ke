import sys
import os

# Dynamically set the project directory
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Explicit path insertion (just in case)
sys.path.insert(0, '/home/szchgxxd/bravoshopperske')

# Import your Flask app
from app import app as application

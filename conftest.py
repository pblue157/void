import sys
import os

# Add the project root to sys.path so pytest can resolve
# 'device_simulator', 'pipeline', 'quality' etc. as packages
sys.path.insert(0, os.path.dirname(__file__))
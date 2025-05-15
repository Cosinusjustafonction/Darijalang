import sys
import os

# Add the project root directory to the Python path
# os.path.dirname(__file__) gives the directory of conftest.py (i.e., .../darijaland/tests)
# os.path.join(..., '..') goes one level up to the project root (.../darijaland)
# os.path.abspath ensures it's an absolute path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

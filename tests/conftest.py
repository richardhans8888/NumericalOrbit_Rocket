import sys
import os

# Allow test files to import modules the same way the simulator does
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rocket_sim"))

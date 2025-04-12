#!/usr/bin/env python
"""
Launcher script for the Advanced Trading Bot.
This script runs the main.py file from the src directory.
"""

import sys
import os

def main():
    """Run the main.py file from the src directory."""
    # Get the command line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # Construct the command to run the main.py file
    cmd = [sys.executable, "src/main.py"] + args
    
    # Print the command
    print(f"Running: {' '.join(cmd)}")
    
    # Run the command
    os.execv(sys.executable, cmd)

if __name__ == "__main__":
    main()

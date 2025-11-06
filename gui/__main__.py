"""
Main entry point for MarkItDown GUI.

This module provides the main entry point for running the GUI application.
"""

import sys
from pathlib import Path

# Add parent directory to path to ensure markitdown can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """
    Main entry point for the GUI application.
    
    This function will be called when running:
    - python -m gui
    - markitdown-gui (after installation)
    """
    from gui.core.app import create_app

    # Create and run the application
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()



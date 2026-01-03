"""Main entry point for ROM Duplicate Manager."""

import sys
import os

# Add the parent directory to sys.path so we can import the old module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point - imports and runs the original ROM Duplicate Manager."""
    try:
        # Import the original module (for backwards compatibility during transition)
        import rom_duplicate_manager
        
        # Run the application
        if __name__ == "__main__":
            rom_duplicate_manager.main()
    except ImportError as e:
        print(f"Error importing ROM Duplicate Manager: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running ROM Duplicate Manager: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
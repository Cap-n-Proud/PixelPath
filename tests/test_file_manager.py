# To execute the tests, run the following command from your project root directory:

# python -m unittest discover tests/ -p "test_*.py" -v


import os
import sys
from datetime import datetime
import shutil
from unittest import TestCase

# Add project root to Python's path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from file_manager import FileManager  # Now this import should work


# Debug prints to check paths
print(f"Current working directory: {os.getcwd()}")
project_root = os.path.dirname(os.path.abspath(__file__))
print(f"Project root path: {project_root}")

sys.path.append(project_root)
print("Python's current paths:")
for p in sys.path:
    print(p)

class TestFileManager(TestCase):
    """Unit tests for the FileManager class."""

    def setUp(self) -> None:
        """Set up test environment before each test."""
        self.temp_dir = os.path.join(os.getcwd(), "temp_test")
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def tearDown(self) -> None:
        """Clean up after each test."""
        # Remove all temporary files and directories
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_organize_file_success(self):
        """Test successful organization of a file."""
        # Create sample file
        temp_file = os.path.join(self.temp_dir, "test_image.jpg")
        open(temp_file, 'a').close()

        # Organize the file
        config = {'image_dest': os.path.join(os.getcwd(), 'organized_images')}
        file_manager = FileManager(config)
        result = file_manager.organize_file(temp_file)

        # Verify the file was moved correctly
        dest_path = os.path.join(config['image_dest'], datetime.now().strftime('%Y'), 
                               f"{datetime.now().month:02d}", "test_image.jpg")
        
        self.assertTrue(os.path.exists(dest_path))
        self.assertIn("Moved", result)

    def test_conflict_resolution_rename(self):
        """Test handling of file organization with rename conflict resolution."""
        # Create a sample file and its destination
        temp_file = os.path.join(self.temp_dir, "test_image.jpg")
        open(temp_file, 'a').close()

        dest_folder = os.path.join(os.getcwd(), 'organized_images', 
                                 str(datetime.now().year), f"{datetime.now().month:02d}")
        os.makedirs(dest_folder, exist_ok=True)
        
        existing_file = os.path.join(dest_folder, "test_image.jpg")
        open(existing_file, 'a').close()

        # Organize the file with rename option
        config = {'image_dest': os.path.join(os.getcwd(), 'organized_images'),
                  'conflict_resolution': 'rename',
                  'rename_suffix': '_{counter}'}
        file_manager = FileManager(config)
        result = file_manager.organize_file(temp_file)

        # Check if a new filename was generated
        counter = 1
        while os.path.exists(os.path.join(dest_folder, f"test_image_{counter}.jpg")):
            counter += 1
        new_name = os.path.join(dest_folder, f"test_image_{counter-1}.jpg")
        
        self.assertTrue(os.path.exists(new_name))
        self.assertIn("Renamed", result)

    # Add more test cases as needed

if __name__ == "__main__":
    unittest.main()


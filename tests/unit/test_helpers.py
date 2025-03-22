import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import sanitize_filename, format_size, get_file_size

class TestHelpers(unittest.TestCase):
    
    def test_sanitize_filename(self):
        """Test sanitize_filename function"""
        # Test with normal string
        self.assertEqual(sanitize_filename("test"), "test")
        
        # Test with spaces
        self.assertEqual(sanitize_filename("test file"), "test_file")
        
        # Test with special characters
        self.assertEqual(sanitize_filename("test:file?"), "test_file_")
        
        # Test with non-ASCII characters
        self.assertEqual(sanitize_filename("تست"), "tst")
    
    def test_format_size(self):
        """Test format_size function"""
        # Test with bytes
        self.assertEqual(format_size(500), "500.0 B")
        
        # Test with kilobytes
        self.assertEqual(format_size(1024), "1.0 KB")
        
        # Test with megabytes
        self.assertEqual(format_size(1048576), "1.0 MB")
        
        # Test with gigabytes
        self.assertEqual(format_size(1073741824), "1.0 GB")
    
    def test_get_file_size(self):
        """Test get_file_size function"""
        # Create a temporary file
        with open("test_file.txt", "w") as f:
            f.write("test")
        
        # Test file size
        self.assertEqual(get_file_size("test_file.txt"), 4)
        
        # Clean up
        os.remove("test_file.txt")
        
        # Test non-existent file
        self.assertEqual(get_file_size("non_existent_file.txt"), 0)

if __name__ == "__main__":
    unittest.main()

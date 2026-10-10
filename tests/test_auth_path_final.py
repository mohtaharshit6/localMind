from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from localmind.auth import authorize_folder, revoke_folder

# Create a test directory with spaces
test_dir = Path("C:/Users/mohta/Desktop/Digital Literacy Project")
test_dir.mkdir(parents=True, exist_ok=True)

# Test 1: Absolute path with spaces
ok, msg = authorize_folder(str(test_dir))
print("Test 1 (Raw):", ok, msg)

# Cleanup
revoke_folder(str(test_dir))

# Test 2: Absolute path with surrounding quotes
ok, msg = authorize_folder(f'"{str(test_dir)}"')
print("Test 2 (Quotes):", ok, msg)

# Cleanup
revoke_folder(str(test_dir))
test_dir.rmdir()

# Test 6: Non-existent path
ok, msg = authorize_folder("C:/Users/mohta/Desktop/DOES_NOT_EXIST_XYZ")
print("Test 6 (Non-existent):", ok, msg)


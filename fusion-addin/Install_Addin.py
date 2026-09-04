import os
import shutil
import platform
import sys

def install_addin():
    # Detect OS and set appropriate Fusion 360 add-in path
    user_home = os.path.expanduser('~')
    system = platform.system()
    
    if system == "Darwin":  # macOS
        addin_base_path = os.path.join(user_home, "Library", "Application Support", "Autodesk", "Autodesk Fusion 360", "API", "AddIns")
    elif system == "Windows":
        addin_base_path = os.path.join(os.environ.get('APPDATA', ''), "Autodesk", "Autodesk Fusion 360", "API", "AddIns")
    else:
        # Fallback for Linux or others, although Fusion 360 is mainly Win/Mac
        print(f"Unsupported operating system: {system}")
        sys.exit(1)

    # Determine source folder relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_folder = os.path.join(script_dir, "MCP")
    
    if not os.path.exists(source_folder):
        print(f"Error: Source folder not found at {source_folder}")
        sys.exit(1)

    print(f"Installing add-in from: {source_folder}")
    print(f"To: {addin_base_path}")

    # Ensure destination base path exists
    if not os.path.exists(addin_base_path):
        os.makedirs(addin_base_path, exist_ok=True)

    # The add-in folder name is based on the source folder name
    name = os.path.basename(source_folder)
    destination_folder = os.path.join(addin_base_path, name)

    try:
        # Copy the add-in folder to the Fusion 360 add-in directory
        # dirs_exist_ok=True allows overwriting existing installations (Python 3.8+)
        shutil.copytree(source_folder, destination_folder, dirs_exist_ok=True)
        print(f"Add-in '{name}' installed successfully to {destination_folder}")
        print("You can now restart Autodesk Fusion 360 and enable the add-in in the 'Add-Ins' dialog.")
    except Exception as e:
        print(f"Error during installation: {e}")
        print("\nManual installation hint:")
        print(f"Copy the folder '{source_folder}' to:")
        print(f"'{addin_base_path}'")
        sys.exit(1)

if __name__ == "__main__":
    install_addin()

import subprocess
import sys
import os
import shutil

def delete_env(env_name):
    if os.path.exists(env_name):
        confirm = input(f"Virtual environment folder '{env_name}' exists. Delete it? (y/n): ").strip().lower()
        if confirm == 'y':
            print(f"Deleting '{env_name}' folder...")
            try:
                shutil.rmtree(env_name)
                print("Deleted successfully.")
            except Exception as e:
                print(f"Error deleting folder: {e}")
                sys.exit(1)
        else:
            print("Deletion cancelled.")
            return
    else:
        print(f"No virtual environment folder named '{env_name}' found.")

def create_virtualenv(env_name='venv'):
    print(f"Creating virtual environment '{env_name}'...")
    subprocess.check_call([sys.executable, "-m", "venv", env_name])
    print(f"Virtual environment '{env_name}' created.")

def install_packages(env_name='venv', packages=None):
    default_packages = [
        "numpy",
        "pandas",
        "scikit-learn",
        "matplotlib",
        "tensorflow",
        "jupyter",
        "requests"
    ]
    if not packages:  # If packages is None or empty list
        packages = default_packages

    print(f"Installing packages: {', '.join(packages)}")
    
    if os.name == 'nt':
        pip_path = os.path.join(env_name, 'Scripts', 'pip.exe')
    else:
        pip_path = os.path.join(env_name, 'bin', 'pip')
    
    try:
        subprocess.check_call([pip_path, "install"] + packages)
        print("Packages installed successfully.")
    except subprocess.CalledProcessError:
        print("Failed to install some packages.")

def main():
    print("Type 'exit' or '8080' at any prompt to quit.")
    while True:
        action = input("\nDo you want to create or delete a virtual environment? (create/delete): ").strip().lower()
        if action in ('exit', '8080'):
            print("Exiting program...")
            break
        
        if action not in {'create', 'delete'}:
            print("Invalid option. Please choose 'create' or 'delete'.")
            continue
        
        env_name = input("Enter the virtual environment folder name (default 'venv'): ").strip()
        if env_name in ('exit', '8080'):
            print("Exiting program...")
            break
        if not env_name:
            env_name = "venv"
        
        if action == 'delete':
            delete_env(env_name)
        else:
            # create
            if os.path.exists(env_name):
                print(f"Warning: Virtual environment folder '{env_name}' already exists.")
                overwrite = input("Do you want to delete and recreate it? (y/n): ").strip().lower()
                if overwrite in ('exit', '8080'):
                    print("Exiting program...")
                    break
                if overwrite == 'y':
                    delete_env(env_name)
                else:
                    print("Aborting creation to avoid overwriting existing environment.")
                    continue
            
            extra_packages = input("Enter extra packages to install (space separated, or leave blank): ").strip()
            if extra_packages in ('exit', '8080'):
                print("Exiting program...")
                break
            extra_packages_list = extra_packages.split() if extra_packages else []
            
            try:
                create_virtualenv(env_name)
                install_packages(env_name, extra_packages_list)
            except subprocess.CalledProcessError as e:
                print(f"An error occurred: {e}")
                continue
            
            if os.name == 'nt':
                print(f"\nTo activate the virtual environment, run:\n{env_name}\\Scripts\\activate.bat")
            else:
                print(f"\nTo activate the virtual environment, run:\nsource {env_name}/bin/activate")

if __name__ == "__main__":
    main()

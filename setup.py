"""Author: Andrew Higgins
https://github.com/speckly

Kurokami project setup, for first time users"""

import os
import getpass
import venv
import subprocess

def _venv_req():
    pip = f"{DIRECTORY}/venv/{'bin' if os.name != "nt" else 'Scripts'}/pip"
    try:
        subprocess.check_call([pip, "install", "-r", "requirements.txt"],cwd=DIRECTORY)
    except subprocess.CalledProcessError:
        print("Fatal: Installation of requirements failed!")

DIRECTORY: str = os.path.dirname(os.path.realpath(__file__))

if not os.path.exists('./output'):
    print("Making directory ./output to store results")
    os.makedirs('./output')

if not os.path.exists(f"{DIRECTORY}/.env"):
    token: str = getpass.getpass("\n/.env\nInput Discord token (enter to skip): ")
    if token.strip() != "":
        with open(".env", "w", encoding="utf-8") as env_f:
            env_f.write(f"TOKEN={token}")
        print("Written Discord Token to .env")

if input("Create venv? (Y): ").lower().strip() in ["", "y"]:
    venv.create(f"{DIRECTORY}/venv", with_pip=True)
    print("Creation complete")
if input("Install requirements in venv? (Y): ").lower().strip() in ["", "y"]:
    _venv_req()
elif input("Install requirements without venv? (Y): ").lower().strip() in ["", "y"]:
    os.system("pip install -r requirements.txt")

print("Setup complete!")

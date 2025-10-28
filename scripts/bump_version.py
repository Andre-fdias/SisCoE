import os
import re
import sys
from datetime import datetime

# Adiciona a biblioteca semver, se não estiver presente
try:
    import semver
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "semver"])
    import semver

def get_latest_commit_message():
    """Obtém a mensagem do último commit."""
    return os.popen('git log -1 --pretty=%B').read().strip()

def bump_version(version, commit_message):
    """Incrementa a versão com base no tipo de commit."""
    if commit_message.startswith('feat'):
        return version.bump_minor()
    elif commit_message.startswith('fix'):
        return version.bump_patch()
    elif commit_message.startswith('BREAKING CHANGE') or '\n\nBREAKING CHANGE' in commit_message:
        return version.bump_major()
    return version

def main():
    """Função principal para atualizar a versão."""
    version_file_path = 'VERSION'
    
    try:
        with open(version_file_path, 'r') as f:
            current_version_str = f.read().strip()
            version_info = semver.VersionInfo.parse(current_version_str)
    except FileNotFoundError:
        version_info = semver.VersionInfo(0, 1, 0) # Versão inicial

    commit_message = get_latest_commit_message()
    new_version = bump_version(version_info, commit_message)

    if new_version > version_info:
        with open(version_file_path, 'w') as f:
            f.write(str(new_version))
        print(f"Versão atualizada para {new_version}")
    else:
        print("Nenhuma mudança de versão necessária.")

if __name__ == "__main__":
    main()
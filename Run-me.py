import struct
import os
from pathlib import Path
import stat
import ast
import requests
import win32crypt
import sys


def rotl32(v, n):
    return ((v << n) & 0xFFFFFFFF) | (v >> (32 - n))

def chacha_quarter_round(a, b, c, d):
    a = (a + b) & 0xFFFFFFFF
    d ^= a; d = rotl32(d, 16)
    c = (c + d) & 0xFFFFFFFF
    b ^= c; b = rotl32(b, 12)
    a = (a + b) & 0xFFFFFFFF
    d ^= a; d = rotl32(d, 8)
    c = (c + d) & 0xFFFFFFFF
    b ^= c; b = rotl32(b, 7)
    return a, b, c, d

def chacha_block(key, counter, nonce):
    constants = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
    state = [
        *constants,
        *struct.unpack('<8L', key),
        counter,
        *struct.unpack('<3L', nonce)
    ]
    working_state = state.copy()

    for _ in range(10):  
        for idx in [(0,4,8,12), (1,5,9,13), (2,6,10,14), (3,7,11,15),
                    (0,5,10,15), (1,6,11,12), (2,7,8,13), (3,4,9,14)]:
            a,b,c,d = [working_state[i] for i in idx]
            a,b,c,d = chacha_quarter_round(a,b,c,d)
            for i, val in zip(idx, [a,b,c,d]):
                working_state[i] = val

    return struct.pack('<16L', *[(x + y) & 0xFFFFFFFF for x, y in zip(working_state, state)])

def chacha_decrypt_data(key, nonce, ciphertext):
    plaintext = bytearray()
    for i in range(0, len(ciphertext), 64):
        block = chacha_block(key, i // 64, nonce)
        chunk = ciphertext[i:i+64]
        plaintext.extend([a ^ b for a, b in zip(chunk, block[:len(chunk)])])
    return bytes(plaintext)


def remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def decrypt_file(file_path, key, nonce):
    try:
        with open(file_path, 'rb') as f:
            ciphertext = f.read()
        decrypted = chacha_decrypt_data(key, nonce, ciphertext)
        with open(file_path, 'wb') as f:
            f.write(decrypted)
        return True
    except Exception as e:
        print(f"Error decrypting {file_path}: {str(e)}")
        return False

def decrypt_folder_in_place(folder_path, key, nonce):
    folder_path = Path(folder_path).resolve()
    if not folder_path.exists():
        print(f"Folder '{folder_path}' does not exist")
        return False

    decrypted_files = 0
    failed_files = 0
    print(f"\nDecrypting files in {folder_path}...")

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix != '.katkot':
                continue
            if decrypt_file(file_path, key, nonce):
                file_path.rename(file_path.with_name(file_path.stem))
                decrypted_files += 1
            else:
                failed_files += 1

    print(f"Files decrypted: {decrypted_files}")
    print(f"Files failed: {failed_files}")
    return decrypted_files > 0


def read_file_direct(file_id):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    r = requests.get(url)
    return r.text if r.status_code == 200 else None

def extract_binary_keys(file_content):
    results = {}
    for line in file_content.split('\n'):
        if line.startswith('Instagram:'):
            results['instagram'] = line.split('Instagram:', 1)[1].strip()
        if line.startswith('Package:'):
            results['package'] = line.split('Package:', 1)[1].strip()
    return results

def decrypt_key_dpapi(encrypted: bytes):
    return win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]


if __name__ == "__main__":
    file_id = "1V9GTEpa1y7hVxV2OvD8KzbFESdcj81GF"
    content = read_file_direct(file_id)
    if not content:
        print("Failed to download keys from Google Drive")

    keys = extract_binary_keys(content)
    key_encrypted = keys.get('instagram')
    nonce_encrypted = keys.get('package')

    if not key_encrypted or not nonce_encrypted:
        print("Missing key or nonce in file content")

    try:
        key = decrypt_key_dpapi(ast.literal_eval(key_encrypted))
        nonce = decrypt_key_dpapi(ast.literal_eval(nonce_encrypted))
    except Exception as e:
        print(f"Failed to decrypt key/nonce: {e}")

    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent

    target_folder = base_path / "test folder"
    if decrypt_folder_in_place(target_folder, key, nonce):
        print("\nDecryption successful")
    else:
        print("\nDecryption failed")

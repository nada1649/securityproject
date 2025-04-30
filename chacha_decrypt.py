import struct
import os
from pathlib import Path
import stat

# --- ChaCha20 Core Functions ---
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

def chacha_decrypt_data(key, nonce, ciphertext):
    """Decryption is identical to encryption in ChaCha20"""
    plaintext = bytearray()
    counter = 0

    for i in range(0, len(ciphertext), 64):
        block = chacha_block(key, counter, nonce)
        counter += 1
        chunk = ciphertext[i:i+64]
        decrypted_chunk = bytes(a ^ b for a, b in zip(chunk, block[:len(chunk)]))
        plaintext.extend(decrypted_chunk)

    return bytes(plaintext)

# --- File System Utilities ---
def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def decrypt_file(file_path, key, nonce):
    """Decrypt a single file in place"""
    try:
        with open(file_path, 'rb') as f:
            ciphertext = f.read()

        decrypted_data = chacha_decrypt_data(key, nonce, ciphertext)

        # Write decrypted data back to the same file
        with open(file_path, 'wb') as f:
            f.write(decrypted_data)

        return True
    except Exception as e:
        print(f"Error decrypting {file_path}: {str(e)}")
        return False

# --- Main Decryption Function ---
def decrypt_folder_in_place(folder_path, key, nonce):
    """Decrypt all encrypted files in folder"""
    folder_path = Path(folder_path).resolve()
    if not folder_path.exists():
        print(f"Error: Folder '{folder_path}' does not exist")
        return False

    decrypted_files = 0
    failed_files = 0

    print(f"\nDecrypting files in {folder_path}...")

    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = Path(root) / file

                # Only process files with .encrypted extension
                if file_path.suffix != '.encrypted':
                    continue

                print(f"Decrypting: {file_path}")
                if decrypt_file(file_path, key, nonce):
                    # Remove .encrypted extension
                    original_path = file_path.with_name(file_path.stem)
                    file_path.rename(original_path)
                    decrypted_files += 1
                else:
                    failed_files += 1

        print(f"\n{'='*40}")
        print("Decryption Complete!")
        print(f"Files decrypted: {decrypted_files}")
        print(f"Files failed: {failed_files}")
        print("="*40)

        return decrypted_files > 0

    except Exception as e:
        print(f"\nError during folder decryption: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== In-Place File Decryption ===")
    print("Decrypts .encrypted files in the folder\n")

    # Get security parameters from environment variables
    key_hex = os.environ.get('CHACHA_KEY')
    nonce_hex = os.environ.get('CHACHA_NONCE')

    if key_hex and nonce_hex:
        try:
            key = bytes.fromhex(key_hex)
            nonce = bytes.fromhex(nonce_hex)
            print("Using key and nonce from environment variables.")

            # Automatically target the "test folder" in the same directory as the script
            script_directory = os.path.dirname(os.path.abspath(__file__))
            target_folder = os.path.join(script_directory, "test folder")
            print(f"Attempting to decrypt files in folder: {target_folder}")

            if decrypt_folder_in_place(target_folder, key, nonce):
                print("\nDecryption successful! Files restored to original names.")
            else:
                print("\nDecryption failed. Some files may remain encrypted or no encrypted files were found.")

        except ValueError:
            print("Invalid key or nonce format in environment variables. Must be valid hexadecimal.")
            exit(1)
    else:
        print("Error: Environment variables CHACHA_KEY and CHACHA_NONCE not found. Exiting.")
        print("Ensure these are set when running the script.")
        exit(1)
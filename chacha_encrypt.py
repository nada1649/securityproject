import struct
import os
import zipfile
from pathlib import Path
import tempfile
import shutil
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

# --- File System Utilities ---
def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clean_git_repo(folder_path):
    """Remove .git folder and reset git attributes"""
    git_path = Path(folder_path) / '.git'
    if git_path.exists():
        print("Found Git repository - cleaning metadata...")
        try:
            # Remove git attributes that might cause permission issues
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        os.chmod(file_path, stat.S_IWRITE)
                    except Exception as e:
                        print(f"Warning: Could not modify permissions for {file_path}: {e}")
            
            # Remove .git folder
            shutil.rmtree(git_path, onerror=remove_readonly)
            print("Successfully removed Git metadata")
            return True
        except Exception as e:
            print(f"Warning: Could not fully clean Git repository: {str(e)}")
            return False
    return True

def zip_folder(folder_path, zip_path):
    """Create zip archive while handling special cases"""
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        arcname = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arcname)
                    except Exception as e:
                        print(f"Warning: Skipped {file_path} - {str(e)}")
                        continue
    except Exception as e:
        print(f"Error creating zip file: {str(e)}")
        raise

# --- Main Encryption Function ---
def encrypt_and_clean(folder_path, key, nonce):
    """Enhanced folder encryption with Git handling"""
    folder_path = Path(folder_path).resolve()
    if not folder_path.exists():
        print(f"Error: Folder '{folder_path}' does not exist")
        return False

    # Clean Git repository first
    clean_git_repo(folder_path)

    output_path = folder_path.parent / f"{folder_path.name}.encrypted"
    
    try:
        temp_zip_path = folder_path.parent / f"temp_{folder_path.name}.zip"
        
        print(f"\nCreating zip archive of {folder_path}...")
        zip_folder(folder_path, temp_zip_path)
        
        print("Reading zip content...")
        with open(temp_zip_path, 'rb') as f:
            zip_data = f.read()
        
        print("Encrypting with ChaCha20...")
        encrypted_data = chacha_encrypt_data(key, nonce, zip_data)
        
        print(f"Saving encrypted file to {output_path}...")
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Verify encryption
        if not output_path.exists() or os.path.getsize(output_path) == 0:
            raise Exception("Encrypted file creation failed")
        
        # Delete original folder
        print("\nDeleting original folder...")
        try:
            shutil.rmtree(folder_path, onerror=remove_readonly)
            delete_success = not folder_path.exists()
        except Exception as e:
            print(f"Warning: Could not fully delete original folder: {str(e)}")
            delete_success = False
        
        # Cleanup
        temp_zip_path.unlink(missing_ok=True)
        
        print(f"\n{'='*40}")
        print("Encryption Successful!")
        print(f"Encrypted file: {output_path}")
        if delete_success:
            print(f"Original folder was completely removed")
        else:
            print(f"Warning: Some files remain in original location")
            print("Please delete manually:")
            print(f"  {folder_path}")
        print("="*40)
        
        return True
    except Exception as e:
        print(f"\nError during encryption: {str(e)}")
        temp_zip_path.unlink(missing_ok=True)
        if 'output_path' in locals() and output_path.exists():
            output_path.unlink()
        return False

if __name__ == "__main__":
    print("=== Secure Folder Encryption ===")
    print("Creates [folder].encrypted and removes original\n")
    
    # Security parameters
    key = bytes.fromhex('000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f')
    nonce = bytes.fromhex('000000090000004a00000000')
    
    folder_path = input("Enter path to folder to encrypt: ").strip()
    
    if encrypt_and_clean(folder_path, key, nonce):
        print("\nSECURITY INFORMATION (SAVE THESE):")
        print(f"Key: {key.hex()}")
        print(f"Nonce: {nonce.hex()}")
        print("\nYou MUST save both to decrypt later!")
    else:
        print("\nEncryption failed. Original folder remains unchanged.")
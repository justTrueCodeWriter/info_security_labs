import argparse
from random import randrange

SYMBOLYK_TABLE = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

M = len(SYMBOLYK_TABLE)

INDEX = {ch: i for i, ch in enumerate(SYMBOLYK_TABLE)}

def check_text_chars(text: str):
    bad = [ch for ch in text if ch not in INDEX]
    if bad:
        raise ValueError(f"В тексте есть символы, отсутствующие в алфавите: {set(bad)}")

def generate_key(plaintext: str) -> str:
    plaintext_len = len(plaintext)  
    
    key_symbols = set()
    while len(key_symbols) != plaintext_len:
        i = randrange(0, plaintext_len) 
        key_symbols.add(SYMBOLYK_TABLE[i])

    key = "".join(key_symbols)

    return key

def encrypt(plaintext: str, key: str, start: int):
    
    out_chars = []

    key_len = len(key)

    if start < 0 or start >= key_len:
        raise ValueError("Начальная позиция вне диапазона ключа")

    for i, ch in enumerate(plaintext):
        mi = INDEX[ch]
        ki = INDEX[key[(start+i)%key_len]]
        ci = (mi+ki)%M
        out_chars.append(SYMBOLYK_TABLE[ci])

    cipher_text = "".join(out_chars)

    return cipher_text

def decrypt(encrypted_text: str, key: str, start: int):

    out_chars = []

    key_len = len(key)

    if start < 0 or start >= key_len:
        raise ValueError("Начальная позиция вне диапазона ключа")

    for i, ch in enumerate(encrypted_text):
        ci = INDEX[ch]
        ki = INDEX[key[(start+i)%key_len]]
        mi = (ci-ki)%M
        out_chars.append(SYMBOLYK_TABLE[mi])


    cipher_text = "".join(out_chars)

    return cipher_text

def print_alphabet(key: str, cols: int):
    i = 0
    for character in key:
        if i == cols:
            print("")
            i = 0
        print(character, end=" ")
        i += 1
    print("\n\n-------\n" )

def read_file(filename: str) :
    with open(filename, "r") as file:
        return file.read().rstrip("\n")

def write_file(output: str, filename: str):
    with open(filename, "w") as file:
        return file.write(output)

def cipher_cli():
    parser = argparse.ArgumentParser()

    parser.add_argument("--key", type=str, help="key filename")
    parser.add_argument("--output", type=str, help="output filename")
    parser.add_argument("--pkey", nargs="?", help="print key")
    parser.add_argument("--encrypt", type=str, help="encrypt filename")
    parser.add_argument("--decrypt", type=str, help="decrypt filename")
    parser.add_argument("--genkey", type=str, help="generate key")
    parser.add_argument("--shift", type=int, default=0, help="generate key")

    args = parser.parse_args()

    if args is None:
        parser.print_help()
        return

    if args.genkey:
        plaintext = read_file(args.genkey)
        output_filename = args.output
        key = generate_key(plaintext)

        write_file(key, output_filename)
         
    if args.pkey:
        key = read_file(args.key)
        print_alphabet(key, args.cols)
    
    if args.encrypt:
        plaintext = read_file(args.encrypt)
        key = read_file(args.key)
        output_filename = args.output

        cipher_text = encrypt(plaintext, key, args.shift )
        write_file(cipher_text, output_filename)

    elif args.decrypt:
        encrypted_text = read_file(args.decrypt)
        key = read_file(args.key)
        output_filename = args.output

        decrypted_text = decrypt(encrypted_text, key, args.shift)
        write_file(decrypted_text, output_filename)
      
    return

if __name__ == "__main__":
    cipher_cli()
    # plaintext = 'i wanna know if you ever seen rain'
    # key = generate_key(plaintext)
    # #key = "\"+$!(#%'* &)"
    #
    # cipher_text = encrypt(plaintext, key, 2)
    # print(cipher_text)
    # print(decrypt(cipher_text, key, 2))

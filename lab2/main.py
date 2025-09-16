import argparse
from random import randrange

SYMBOLYK_TABLE = " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"

M = len(SYMBOLYK_TABLE)

INDEX = {ch: i for i, ch in enumerate(SYMBOLYK_TABLE)}

def generate_key(plaintext: str) -> str:
    plaintext_len = len(plaintext)  
    
    key_symbols = set()
    while len(key_symbols) != plaintext_len:
        i = randrange(0, plaintext_len) 
        key_symbols.add(SYMBOLYK_TABLE[i])

    key = "".join(key_symbols)

    return key

def encrypt(plaintext: str, key: str):
    
    out_chars = []

    for i, ch in enumerate(plaintext):
        mi = INDEX[ch]
        ki = INDEX[key[i]]
        ci = (mi+ki)%M
        out_chars.append(SYMBOLYK_TABLE[ci])


    cipher_text = "".join(out_chars)

    return cipher_text

def decrypt(encrypted_text: str, key: str):

    out_chars = []

    for i, ch in enumerate(encrypted_text):
        ci = INDEX[ch]
        ki = INDEX[key[i]]
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
    parser.add_argument("--input", type=str, help="input filename")
    parser.add_argument("--output", type=str, help="output filename")
    parser.add_argument("--pkey", default="", help="print key")
    parser.add_argument("--encrypt", default="", help="encrypt data")
    parser.add_argument("--decrypt", default="", help="decrypt data")
    parser.add_argument("--genkey", default="", help="generate key")

    args = parser.parse_args()

    print(args)

    if args is None:
        parser.print_help()
        return

    if args.genkey:
        print(args.input)
        # plaintext = read_file(args.input)
        # output_filename = args.output
        # print(output_filename)
        #
        # key = generate_key(plaintext)
        # print(key)
        #
        # write_file(plaintext, output_filename)
         
    if args.pkey:
        key = read_file(args.key)
        print_alphabet(key, args.cols)
    
    if args.encrypt:
        plaintext = read_file(args.input)
        key = read_file(args.key)
        output_filename = args.output

        cipher_text = encrypt(plaintext, key)
        write_file(cipher_text, output_filename)

    elif args.decrypt:
        encrypted_text = read_file(args.input)
        key = read_file(args.key)
        output_filename = args.output

        decrypted_text = decrypt(encrypted_text, key)
        write_file(decrypted_text, output_filename)
      
    return

if __name__ == "__main__":
    #cipher_cli()
    plaintext = 'i wanna know if you ever seen rain'
    key = generate_key(plaintext)
    #key = "\"+$!(#%'* &)"
    
    cipher_text = encrypt(plaintext, key)
    print(cipher_text)
    print(decrypt(cipher_text, key))

import argparse

# polybian_square --key key.txt --encrypt plaintext.txt --output encrypted.txt
# polybian_square --key key.txt --decrypt encrypted.txt --output decrypted.txt

#ALPHABET = "ЩС0УФ8ЪЖГ.4ПЯ Р9ЛЗВ,Ь:3ЧШТЁЭ1ОЙД5ЫИ6-НКАБМ2ЦЕЮ7Х"

#assert len(ALPHABET) == 48, f"Ожидалось 48 символов, получили {len(ALPHABET)}"

def encrypt(plaintext: str, key: str, cols: int):
    encrypted_text = ""

    for character in plaintext:
        pos = key.find(character)
        encrypted_text += key[(pos+cols)%len(key)]

    print(*encrypted_text, sep="")
    return encrypted_text


def decrypt(encrypted_text: str, key: str, cols: int):
    decrypted_text = ""
   
    for character in encrypted_text:
        pos = key.find(character)
        decrypted_text += key[(pos-cols)%len(key)]

    print(*decrypted_text, sep="")
    return decrypted_text

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

    parser.add_argument("--key", type=str)
    parser.add_argument("--encrypt", type=str)
    parser.add_argument("--decrypt", type=str)
    parser.add_argument("--output", type=str)
    parser.add_argument("--cols", type=int)
    parser.add_argument("pkey", required=False)

    args = parser.parse_args()

    if args is None:
        parser.print_help()
        return

    if args.pkey:
        key = read_file(args.key)
        print_alphabet(key, args.cols)
    
    if args.encrypt:
        plaintext = read_file(args.encrypt)
        key = read_file(args.key)
        cols = args.cols
        output_filename = args.output

        cipher_text = encrypt(plaintext, key, cols)
        write_file(cipher_text, output_filename)

    elif args.decrypt:
        encrypted_text = read_file(args.decrypt)
        key = read_file(args.key)
        cols = args.cols
        output_filename = args.output

        decrypted_text = decrypt(encrypted_text, key, cols)
        write_file(decrypted_text, output_filename)
      
    return

if __name__ == "__main__":
    cipher_cli()

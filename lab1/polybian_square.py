# polybian_square --key key.txt --encrypt plaintext.txt --output encrypted.txt
# polybian_square --key key.txt --decrypt encrypted.txt --output decrypted.txt

ALPHABET = "ЩС0УФ8ЪЖГ.4ПЯ Р9ЛЗВ,Ь:3ЧШТЁЭ1ОЙД5ЫИ6-НКАБМ2ЦЕЮ7Х"

assert len(ALPHABET) == 48, f"Ожидалось 48 символов, получили {len(ALPHABET)}"

rows = 6
cols = 8

def encrypt(plaintext: str, key: str):
    encrypted_text = ""

    for character in plaintext:
        pos = key.find(character)
        encrypted_text += key[(pos+rows)%len(key)]

    print(*encrypted_text, sep="")
    return encrypted_text


def decrypt(encrypted_text: str, key: str):
    decrypted_text = ""
   
    for character in encrypted_text:
        pos = key.find(character)
        decrypted_text += key[(pos-rows)%len(key)]

    print(*decrypted_text, sep="")
    return decrypted_text

def print_alphabet(key: str):
    i = 0
    for character in key:
        if i == 6:
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

def cypher_cli():
    return


#write_file(encrypt(read_file("plaintext.txt"), read_file("key.txt")), "encrypt.txt")
write_file(decrypt(read_file("encrypt.txt"), read_file("key.txt")), "decrypt.txt")

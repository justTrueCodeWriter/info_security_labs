# ключевое слово: криптекс

import argparse

def create_table(key: str, cols: int):
    n = len(key)

    rows = n // cols
    table = [list(key[r*cols:(r+1)*cols]) for r in range(rows)]
    pos = {}
    for r in range(rows):
        for c in range(cols):
            ch = table[r][c]
            if ch not in pos:
                pos[ch] = (r, c)
    return table, pos, rows, cols

def create_bigrams(plaintext: str, key: str) -> list:
    bigrams = []

    FIRST_OPTION = 0
    SECOND_OPTION = 1
    THIRD_OPTION = 2
    option = FIRST_OPTION
  
    i = 0
    space_pos_plaintext = 0
    last_space_scan = []
    while i < len(plaintext):
        a = plaintext[i]
        if a not in key:
            raise ValueError(f"Symbol '{a}' not in key")
        if i + 1 < len(plaintext):
            b = plaintext[i+1]
            if b not in key:
                raise ValueError(f"Symbol '{b}' not in key")
            
            if a == " " and b == " ":
                option = FIRST_OPTION

            elif a == " ":
                space_pos_plaintext = i
                last_space_scan = bigrams.copy()
                option = THIRD_OPTION

            elif b == " ":
                space_pos_plaintext = i+1
                last_space_scan = bigrams.copy()
                option = SECOND_OPTION

            if a == b and space_pos_plaintext != -1 and space_pos_plaintext != 0:
                print(f"{a=} {b=}")
                print("Space position", space_pos_plaintext, end="\n\n")
                tmp = plaintext[0:space_pos_plaintext] + " " + plaintext[space_pos_plaintext:len(plaintext)] 
                plaintext = tmp

                if option == FIRST_OPTION:
                    i = space_pos_plaintext+2
                elif option == SECOND_OPTION:
                    i = space_pos_plaintext-1
                elif option == THIRD_OPTION:
                    i = space_pos_plaintext

                bigrams = last_space_scan.copy()
                print("Bigrams duplicating ", (a, b))
                space_pos_plaintext = -1

            elif a == b and space_pos_plaintext == 0:
                print(f"{a=} {b=}")
                print("Space position", space_pos_plaintext, end="\n\n")
                tmp = " " + plaintext
                plaintext = tmp
                i = space_pos_plaintext
                bigrams = last_space_scan.copy()
                print("Bigrams duplicating ", (a, b))
                space_pos_plaintext = -1

            else:
                bigrams.append((a, b))
                i += 2
        else:
            bigrams.append((a, " "))
            i += 2

        print(f"{plaintext}", *bigrams, space_pos_plaintext)

    #print(plaintext)
    print(*bigrams, end="\n\n")

    return bigrams

def encrypt(plaintext: str, key: str, cols: int) -> str:

    if len(key) % cols != 0:
        raise ValueError("Incorrect amount of symbols in key")

    bigrams = create_bigrams(plaintext, key)

    table, pos, rows, cols = create_table(key, cols)
    out_chars = []

    for a, b in bigrams:
        r1, c1 = pos[a]
        r2, c2 = pos[b]

        if r1 == r2:
            ca = table[r1][(c1 + 1) % cols]
            cb = table[r2][(c2 + 1) % cols]
        elif c1 == c2:
            ca = table[(r1 + 1) % rows][c1]
            cb = table[(r2 + 1) % rows][c2]
        else:
            ca = table[r1][c2]
            cb = table[r2][c1]

        out_chars.append(ca)
        out_chars.append(cb)

        print(f"{a=} => {ca=}")
        print(f"{b=} => {cb=}", end="\n\n")

    cipher_text = "".join(out_chars)

    print(cipher_text)
    return cipher_text

def decrypt(cipher_text: str, key: str, cols: int) -> str:

    if len(key) % cols != 0:
        print("Incorrect amount of symbols in key")

    table, pos, rows, cols = create_table(key, cols)
    text = list(cipher_text)
    out_chars = []

    for i in range(0, len(text), 2):
        a = text[i]
        b = text[i+1]
        r1, c1 = pos[a]
        r2, c2 = pos[b]
        if r1 == r2:
            da = table[r1][(c1 - 1) % cols]
            db = table[r2][(c2 - 1) % cols]
        elif c1 == c2:
            da = table[(r1 - 1) % rows][c1]
            db = table[(r2 - 1) % rows][c2]
        else:
            da = table[r1][c2]
            db = table[r2][c1]

        out_chars.append(da)
        out_chars.append(db)

        print(f"{a=} => {da=}")
        print(f"{b=} => {db=}", end="\n\n")

    plaintext = "".join(out_chars)

    print(plaintext)
    return plaintext

def print_alphabet(key: str, cols: int):
    table, pos, rows, cols = create_table(key, cols)

    for r in range(rows):
        print(" ".join(table[r]))
    print("\n-------\n")

    return

def read_file(filename: str) :
    with open(filename, "r") as file:
        return file.read().rstrip("\n")

def write_file(output: str, filename: str):
    with open(filename, "w") as file:
        return file.write(output)

def cipher_cli():
    parser = argparse.ArgumentParser()

    parser.add_argument("--key", type=str, help="key filename")
    parser.add_argument("--encrypt", type=str, help="encrypt filename")
    parser.add_argument("--decrypt", type=str, help="decrypt filename")
    parser.add_argument("--output", type=str, help="output filename")
    parser.add_argument("--cols", type=int, help="amount of cols")
    parser.add_argument("pkey", nargs="?", help="print key")

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
    #plaintext = "ТАК ГОВОРИЛА В ИЮЛЕ 1805 ГОДА ИЗВЕСТНАЯ АННА ПАВЛОВНА ШЕРЕР, ФРЕЙЛИНА И ПРИБЛИЖЕННАЯ ИМПЕРАТРИЦЫ МАРИИ ФЕОДОРОВНЫ, ВСТРЕЧАЯ ВАЖНОГО И ЧИНОВНОГО КНЯЗЯ ВАСИЛИЯ, ПЕРВОГО ПРИЕХАВШЕГО НА ЕЕ ВЕЧЕР"
    # plaintext = "У БУРНЫХ ЧУВСТВ НЕИСТОВЫЙ КОНЕЦ"
    #key = "КРИПТЕСАБВГДЁЖЗЙЛМНОУФХЦЧШЩЪЫЬЭЮЯ ,.-:0123456789"
    #
    # print_alphabet(key, 6)
    #cipher_text = encrypt(plaintext, key, 6)
    #decrypt(cipher_text, key, 6)


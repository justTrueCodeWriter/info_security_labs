from typing import List, Tuple

RUS_LETTERS = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"  # 33
ALPHABET = RUS_LETTERS + " " + "," + "." + "-" + ":" + "0123456789"  # total 48

# Проверка длины
assert len(ALPHABET) == 48, f"Ожидалось 48 символов, получили {len(ALPHABET)}"

# ---------------- Polybius (полибианский квадрат) ----------------
class Polybius:
    def __init__(self, alphabet: str, rows: int = 6, cols: int = 8):
        if rows * cols != len(alphabet):
            raise ValueError("rows * cols must equal len(alphabet)")
        self.rows = rows
        self.cols = cols
        self.alphabet = alphabet
        # fill row-major
        self.grid = [[alphabet[r * cols + c] for c in range(cols)] for r in range(rows)]
        # dict for fast lookup
        self.pos = {ch: (r, c) for r in range(rows) for c in range(cols) for ch in [self.grid[r][c]]}

    def encrypt(self, plaintext: str) -> str:
        """Возвращает шифртекст как последовательность пар 'rc' разделённых пробелом, где r,c — 1-based."""
        tokens = []
        for ch in plaintext:
            if ch not in self.pos:
                raise ValueError(f"Символ '{ch}' не в алфавите.")
            r, c = self.pos[ch]
            tokens.append(f"{r+1}{c+1}")  # 1-based indices, например '11'
        return " ".join(tokens)

    def decrypt(self, code: str) -> str:
        """Вход: строки токенов вида 'rc' разделённых пробелом. Возвращает текст."""
        parts = code.strip().split()
        out_chars = []
        for tok in parts:
            if len(tok) != 2 or not tok.isdigit():
                raise ValueError(f"Неверный токен: '{tok}' (ожидается 2 цифры: row col)")
            r = int(tok[0]) - 1
            c = int(tok[1]) - 1
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                raise ValueError(f"Индексы вне диапазона: {tok}")
            out_chars.append(self.grid[r][c])
        return "".join(out_chars)


# ---------------- Playfair (биграммный шифр Плейфейра) ----------------
class Playfair:
    def __init__(self, alphabet: str, key: str, rows: int = 6, cols: int = 8, filler: str = "Х"):
        if rows * cols != len(alphabet):
            raise ValueError("rows * cols must equal len(alphabet)")
        self.rows = rows
        self.cols = cols
        self.alphabet = alphabet
        self.filler = filler
        # Normalize key: uppercase and keep only symbols from alphabet, preserve first occurrence
        key_u = "".join(ch.upper() for ch in key if ch.upper() in alphabet)
        seen = set()
        key_unique = []
        for ch in key_u:
            if ch not in seen:
                key_unique.append(ch)
                seen.add(ch)
        # remaining symbols
        for ch in alphabet:
            if ch not in seen:
                key_unique.append(ch)
                seen.add(ch)
        # build table row-major
        self.table = [list(key_unique[i * cols:(i + 1) * cols]) for i in range(rows)]
        self.pos = {self.table[r][c]: (r, c) for r in range(rows) for c in range(cols)}

    def _choose_filler(self, a: str) -> str:
        # если стандартный filler совпадает с a, выбрать другой символ из алфавита (например 'Ъ' или первый подходящий)
        if self.filler != a:
            return self.filler
        for ch in self.alphabet:
            if ch != a:
                return ch
        return self.filler

    def _prepare_pairs(self, plaintext: str) -> List[Tuple[str, str]]:
        text = "".join(ch.upper() for ch in plaintext if ch.upper() in self.alphabet)
        pairs = []
        i = 0
        while i < len(text):
            a = text[i]
            if i + 1 < len(text):
                b = text[i + 1]
                if a == b:
                    # insert filler between identical letters
                    f = self._choose_filler(a)
                    pairs.append((a, f))
                    i += 1  # advance only by 1 (we'll reprocess second char in next iteration)
                else:
                    pairs.append((a, b))
                    i += 2
            else:
                # last single char -> pair with filler
                f = self._choose_filler(a)
                pairs.append((a, f))
                i += 1
        return pairs

    def encrypt_pair(self, a: str, b: str) -> Tuple[str, str]:
        r1, c1 = self.pos[a]
        r2, c2 = self.pos[b]
        if r1 == r2:
            # same row -> shift right
            return (self.table[r1][(c1 + 1) % self.cols], self.table[r2][(c2 + 1) % self.cols])
        elif c1 == c2:
            # same column -> shift down
            return (self.table[(r1 + 1) % self.rows][c1], self.table[(r2 + 1) % self.rows][c2])
        else:
            # rectangle: swap columns
            return (self.table[r1][c2], self.table[r2][c1])

    def decrypt_pair(self, a: str, b: str) -> Tuple[str, str]:
        r1, c1 = self.pos[a]
        r2, c2 = self.pos[b]
        if r1 == r2:
            # same row -> shift left
            return (self.table[r1][(c1 - 1) % self.cols], self.table[r2][(c2 - 1) % self.cols])
        elif c1 == c2:
            # same column -> shift up
            return (self.table[(r1 - 1) % self.rows][c1], self.table[(r2 - 1) % self.rows][c2])
        else:
            # rectangle: swap columns
            return (self.table[r1][c2], self.table[r2][c1])

    def encrypt(self, plaintext: str) -> str:
        pairs = self._prepare_pairs(plaintext)
        out = []
        for a, b in pairs:
            ca, cb = self.encrypt_pair(a, b)
            out.append(ca)
            out.append(cb)
        return "".join(out)

    def decrypt(self, ciphertext: str) -> str:
        # ciphertext must have even length and contain only alphabet symbols
        text = "".join(ch.upper() for ch in ciphertext if ch.upper() in self.alphabet)
        if len(text) % 2 != 0:
            raise ValueError("Длина шифртекста нечётная; возможно неверный формат.")
        out = []
        for i in range(0, len(text), 2):
            a, b = text[i], text[i + 1]
            da, db = self.decrypt_pair(a, b)
            out.append(da)
            out.append(db)
        return "".join(out)


# ------------------ Пример использования и утилиты ------------------

def example_run():
    print("=== Пример работы для варианта 22 ===")
    # Polybius example
    poly = Polybius(ALPHABET, rows=6, cols=8)
    pt = "ПРОВЕРКА 1,2:3-4."
    print("Полибианский — исходный текст:", pt)
    enc = poly.encrypt(pt)
    print("Полибианский — зашифрован (пары):", enc)
    dec = poly.decrypt(enc)
    print("Полибианский — расшифрован:", dec)
    print()

    # Playfair example
    key = "КЛЮЧПРИМЕР123"
    pf = Playfair(ALPHABET, key, rows=6, cols=8, filler="Х")
    pt2 = "ПРИВЕТ, МИР 2025"
    print("Плейфейр — ключ:", key)
    print("Плейфейр — исходный текст:", pt2)
    enc2 = pf.encrypt(pt2)
    print("Плейфейр — зашифрован:", enc2)
    dec2 = pf.decrypt(enc2)
    print("Плейфейр — расшифрован (без удаления filler'ов):", dec2)
    print("=== Конец примера ===\n")


# Утилиты для чтения/записи файлов (в лабораторной работе требуется хранить файлы)
def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_text_file(path: str, text: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

# Вспомогательная CLI-функция (простая)
def cli_demo():
    import argparse
    parser = argparse.ArgumentParser(description="Lab variant 22: Playfair and Polybius utilities")
    sub = parser.add_subparsers(dest="cmd")

    # poly encrypt/decrypt
    p_enc = sub.add_parser("poly-encrypt")
    p_enc.add_argument("infile")
    p_enc.add_argument("outfile")
    p_enc.add_argument("--rows", type=int, default=6)
    p_enc.add_argument("--cols", type=int, default=8)

    p_dec = sub.add_parser("poly-decrypt")
    p_dec.add_argument("infile")
    p_dec.add_argument("outfile")
    p_dec.add_argument("--rows", type=int, default=6)
    p_dec.add_argument("--cols", type=int, default=8)

    # playfair encrypt/decrypt
    pf_enc = sub.add_parser("pf-encrypt")
    pf_enc.add_argument("key")
    pf_enc.add_argument("infile")
    pf_enc.add_argument("outfile")
    pf_enc.add_argument("--rows", type=int, default=6)
    pf_enc.add_argument("--cols", type=int, default=8)
    pf_enc.add_argument("--filler", type=str, default="Х")

    pf_dec = sub.add_parser("pf-decrypt")
    pf_dec.add_argument("key")
    pf_dec.add_argument("infile")
    pf_dec.add_argument("outfile")
    pf_dec.add_argument("--rows", type=int, default=6)
    pf_dec.add_argument("--cols", type=int, default=8)
    pf_dec.add_argument("--filler", type=str, default="Х")

    args = parser.parse_args()
    if args.cmd is None:
        parser.print_help()
        return

    if args.cmd == "poly-encrypt":
        txt = read_text_file(args.infile)
        poly = Polybius(ALPHABET, args.rows, args.cols)
        enc = poly.encrypt(txt)
        write_text_file(args.outfile, enc)
        print(f"Зашифровано Polybius -> {args.outfile}")
    elif args.cmd == "poly-decrypt":
        code = read_text_file(args.infile)
        poly = Polybius(ALPHABET, args.rows, args.cols)
        dec = poly.decrypt(code)
        write_text_file(args.outfile, dec)
        print(f"Расшифровано Polybius -> {args.outfile}")
    elif args.cmd == "pf-encrypt":
        txt = read_text_file(args.infile)
        pf = Playfair(ALPHABET, args.key, args.rows, args.cols, args.filler)
        enc = pf.encrypt(txt)
        write_text_file(args.outfile, enc)
        print(f"Зашифровано Playfair -> {args.outfile}")
    elif args.cmd == "pf-decrypt":
        txt = read_text_file(args.infile)
        pf = Playfair(ALPHABET, args.key, args.rows, args.cols, args.filler)
        dec = pf.decrypt(txt)
        write_text_file(args.outfile, dec)
        print(f"Расшифровано Playfair -> {args.outfile}")

# Если скрипт запущен напрямую, показать пример
if __name__ == "__main__":
    example_run()
    # Для CLI: раскомментируйте следующую строку и запускайте с аргументами из командной строки
    # cli_demo()


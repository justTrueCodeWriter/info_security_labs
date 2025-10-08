#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from itertools import permutations
import argparse
from typing import List, Tuple, Set

RUS_LETTERS = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
ALPHABET = RUS_LETTERS + " " + "."
if len(ALPHABET) != 35:
    raise RuntimeError("Ожидалось 35 символов в алфавите")

_RUS_FREQ_TABLE_RAW = {
    " ": 0.175, "О": 0.090, "Е": 0.072, "А": 0.062, "И": 0.062, "Н": 0.053, "Т": 0.053,
    "С": 0.045, "Р": 0.040, "В": 0.038, "Л": 0.035, "К": 0.028, "М": 0.026, "Д": 0.025,
    "П": 0.023, "У": 0.021, "Я": 0.018, "Ы": 0.016, "З": 0.016, "Б": 0.014, "Ь": 0.014,
    "Г": 0.013, "Ч": 0.012, "Й": 0.010, "Х": 0.009, "Ж": 0.007, "Ю": 0.006, "Ш": 0.006,
    "Ц": 0.004, "Щ": 0.003, "Э": 0.003, "Ф": 0.002
}
RUS_FREQ_TABLE = {ch: _RUS_FREQ_TABLE_RAW.get(ch, 0.0) for ch in ALPHABET}

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path: str, text: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def normalize_text(s: str, alphabet: str) -> str:
    s_up = s.upper()
    return "".join(ch for ch in s_up if ch in alphabet)

class Trisemus:
    def __init__(self, alphabet: str, key: str, rows: int):
        self.alphabet = alphabet
        self.key = key
        self.rows = int(rows)
        n = len(alphabet)
        if n % self.rows != 0:
            raise ValueError("Длина алфавита должна делиться на rows")
        self.cols = n // self.rows
        self.table = self._build_table(key) 
        self.pos = {}
        for idx, ch in enumerate(self.table):
            if ch not in self.pos:
                self.pos[ch] = idx

    def _build_table(self, key: str) -> List[str]:
        seen = set()
        seq = []
        for ch in key.upper():
            if ch in self.alphabet and ch not in seen:
                seq.append(ch)
                seen.add(ch)
        for ch in self.alphabet:
            if ch not in seen:
                seq.append(ch)
                seen.add(ch)
        return seq

    def encrypt(self, plaintext: str) -> str:
        out = []
        for ch in plaintext:
            if ch not in self.pos:
                raise ValueError(f"Символ '{ch}' не в алфавите.")
            idx = self.pos[ch]
            r, c = divmod(idx, self.cols)
            r2 = (r + 1) % self.rows  
            idx2 = r2 * self.cols + c
            out.append(self.table[idx2])
        return "".join(out)

    def decrypt(self, ciphertext: str) -> str:
        out = []
        for ch in ciphertext:
            if ch not in self.pos:
                raise ValueError(f"Символ '{ch}' не в алфавите.")
            idx = self.pos[ch]
            r, c = divmod(idx, self.cols)
            r2 = (r - 1) % self.rows
            idx2 = r2 * self.cols + c
            out.append(self.table[idx2])
        return "".join(out)

    def print_table(self):
        for r in range(self.rows):
            row_slice = self.table[r*self.cols:(r+1)*self.cols]
            print(" ".join(row_slice))
        print()


def compute_W(text: str, alphabet: str) -> float:
    N = len(text)
    if N == 0:
        return float('inf')
    counts = {ch: 0 for ch in alphabet}
    for ch in text:
        if ch in counts:
            counts[ch] += 1
    W = 0.0
    for ch in alphabet:
        Pobs = counts[ch] / N
        Ptab = RUS_FREQ_TABLE.get(ch, 0.0)
        if (Ptab == 0.0):
            continue
        W += (Pobs - Ptab) ** 2
    return W

def analyze_trisemus_permutations(ciphertext: str, rows: int,
                                  perm_chars: str,
                                  alphabet: str,
                                  key_template: str = None,
                                  top_n: int = 10) -> List[Tuple[float, str, str]]:
    ciphertext = normalize_text(ciphertext, alphabet)
    results: List[Tuple[float, str, str]] = []
    seen: Set[Tuple[str, ...]] = set()

    if key_template:
        if key_template.count('?') != len(perm_chars):
            raise ValueError("Число '?' в key_template должно совпадать с длиной perm_chars")

    permutations_list = set(permutations(perm_chars))
    for perm in permutations_list:
        if perm in seen:
            continue
        seen.add(perm)

        if key_template:
            filled = list(key_template.upper())
            idx = 0
            for i, ch in enumerate(filled):
                if ch == '?':
                    filled[i] = perm[idx]
                    idx += 1
            candidate_key = "".join(filled)
        else:
            candidate_key = "".join(perm)

        try:
            tr = Trisemus(alphabet=alphabet, key=candidate_key, rows=rows)
            pt = tr.decrypt(ciphertext)
        except Exception:
            continue

        W = compute_W(pt, alphabet)
        results.append((W, candidate_key, pt))

    results.sort(key=lambda x: x[0])
    return results[:top_n]

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    tparser = sub.add_parser("trisemus", help="Trisemus encrypt/decrypt/compare by W")
    tparser.add_argument("--mode", choices=["encrypt", "decrypt", "analyze"], required=True)
    tparser.add_argument("--key", help="key filename (string of chars)")
    tparser.add_argument("--key-template", help="key template with ? for unknowns (optional)")
    tparser.add_argument("--perm-chars", help="chars to permute (if key_template omitted, these are entire 6-letter key)")
    tparser.add_argument("--rows", type=int, required=True, help="number of rows in table")
    tparser.add_argument("--in", dest="infile", help="input filename (plaintext or ciphertext)")
    tparser.add_argument("--out", dest="outfile", help="output filename")
    tparser.add_argument("--top", type=int, default=10, help="top N results for analysis")
    tparser.add_argument("--print_key", action="store_true", help="print table for given key")

    args = parser.parse_args()

    if args.cmd == "trisemus":
        if args.mode in ("encrypt", "decrypt"):
            if not args.key or not args.infile or not args.outfile:
                print("Укажите --key, --in и --out для шифрования/дешифрования.")
                return
            key = read_file(args.key).strip()
            txt = read_file(args.infile)
            txt_norm = normalize_text(txt, ALPHABET)
            tr = Trisemus(alphabet=ALPHABET, key=key, rows=args.rows)
            if args.mode == "encrypt":
                ct = tr.encrypt(txt_norm)
                write_file(args.outfile, ct)
                print(f"Зашифровано -> {args.outfile}")
            else:
                pt = tr.decrypt(txt_norm)
                write_file(args.outfile, pt)
                print(f"Расшифровано -> {args.outfile}")

        elif args.mode == "analyze":
            if not args.infile or not args.perm_chars:
                print("Для анализа укажите --in и --perm-chars.")
                return
            cipher_text = read_file(args.infile).strip()
            top_results = analyze_trisemus_permutations(ciphertext=cipher_text,
                                                        rows=args.rows,
                                                        perm_chars=args.perm_chars,
                                                        alphabet=ALPHABET,
                                                        key_template=(args.key_template if args.key_template else None),
                                                        top_n=args.top)
            if not top_results:
                print("Ни одного валидного кандидата не найдено.")
                return
            for i, (W, k, pt) in enumerate(top_results, 1):
                print(f"{i:2d} | W={W:.12e} | key='{k}'")
                print("    Часть текста:", pt[:300].replace("\n", " "), end="\n\n")
            if args.outfile:
                write_file(args.outfile, top_results[0][2])
                print(f"\nЛучший вариант записан в {args.outfile} с ключом {top_results[0][1]}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()


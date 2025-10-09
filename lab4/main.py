#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Лабораторная работа — Вариант 22 (Гаммирование).
Двухступенчатый генератор:
  - 1-я ступень: LCG (mod 2^20) генерирует 7 чисел; их сумма -> стартовое значение для BBS.
  - 2-я ступень: BBS (64-bit modulus) генерирует 5 чисел (каждое 64 бита) -> фрагмент гаммы.
    Затем старшие 20 бит последнего числа передаются в LCG как новое стартовое значение.
Гаммирование текста из 128-символьной таблицы (ASCII 0..127) — 7 бит на символ.

CLI:
  --genkey <file>        : сгенерировать ключ и сохранить (JSON)
  --key <file>           : загрузить ключ (JSON)
  --mode encrypt/decrypt : зашифровать/расшифровать
  --in  <file> --out <file>
  --show                 : печатать на экран бинарные строки (по умолчанию печатает)
Примеры:
  python lab_gammiranje_variant22.py --genkey key.json
  python lab_gammiranje_variant22.py --mode encrypt --key key.json --in plain.txt --out cipher.txt
  python lab_gammiranje_variant22.py --mode decrypt --key key.json --in cipher.txt --out recovered.txt
"""

import json
import os
import sys
import argparse
from typing import List, Tuple
from secrets import randbits, randbelow, choice as secure_choice
import math

# ------------------ константы варианта ------------------
LCG_MOD = 1 << 20  # 2^20
# дефолтные параметры LCG (можно изменить при генерации ключа)
DEFAULT_LCG_A = 1664525
DEFAULT_LCG_B = 1013904223

# ASCII 0..127 -> 128 символов -> 7 бит на символ
BITS_PER_CHAR = 7

# ------------------ вспомогательные функции ------------------
def int_to_bin_str(x: int, bits: int) -> str:
    return format(x, '0{}b'.format(bits))

def text_to_bitstring_7bit(s: str) -> str:
    """Преобразовать текст в битовую строку (7 бит на символ, MSB first)."""
    bits = []
    for ch in s:
        code = ord(ch)
        if code < 0 or code > 127:
            raise ValueError(f"Символ {ch!r} имеет код {code} вне диапазона 0..127")
        bits.append(int_to_bin_str(code, BITS_PER_CHAR))
    return "".join(bits)

def bitstring_to_text_7bit(bits: str) -> str:
    """Преобразовать битовую строку (длина кратна 7) в текст ASCII 0..127."""
    if len(bits) % BITS_PER_CHAR != 0:
        raise ValueError("Длина битовой строки не кратна 7")
    out_chars = []
    for i in range(0, len(bits), BITS_PER_CHAR):
        chunk = bits[i:i+BITS_PER_CHAR]
        code = int(chunk, 2)
        out_chars.append(chr(code))
    return "".join(out_chars)

# ------------------ LCG (первая ступень) ------------------
class LCG:
    def __init__(self, a: int, b: int, m: int, seed: int):
        self.a = a
        self.b = b
        self.m = m
        self.state = seed % m

    def next(self) -> int:
        self.state = (self.a * self.state + self.b) % self.m
        return self.state

    def generate_n(self, n: int) -> List[int]:
        return [self.next() for _ in range(n)]

# ------------------ Miller-Rabin и генерация 32-bit простого ------------------
def is_probable_prime(n: int, k: int = 10) -> bool:
    if n < 2:
        return False
    small_primes = [2,3,5,7,11,13,17,19,23,29]
    for p in small_primes:
        if n % p == 0:
            return n == p
    # write n-1 as d * 2^s
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    import random
    for _ in range(k):
        a = random.randrange(2, n-1)
        x = pow(a, d, n)
        if x == 1 or x == n-1:
            continue
        skip_to_next = False
        for __ in range(s-1):
            x = (x * x) % n
            if x == n-1:
                skip_to_next = True
                break
        if skip_to_next:
            continue
        return False
    return True

def gen_32bit_prime_congruent_3_mod_4() -> int:
    """Сгенерировать 32-битное простое p такое, что p % 4 == 3."""
    while True:
        # 32 бит: от 2^31 до 2^32-1
        # берём случайное 32-битное нечётное число в этом диапазоне
        candidate = randbits(32)
        # ограничим диапазон: убедимся что кандидат >= 2^31
        candidate = (candidate | (1 << 31))  # гарантируем старший бит 1
        candidate |= 1  # нечётный
        # скорректируем до ≡3 mod 4
        rem = candidate % 4
        if rem != 3:
            candidate += (3 - rem) % 4
        if is_probable_prime(candidate, k=10):
            return candidate
        # иначе пробуем снова

# ------------------ BBS (вторая ступень) ------------------
class BBS:
    def __init__(self, p: int, q: int, seed_s: int):
        self.p = p
        self.q = q
        self.m = p * q
        if math.gcd(seed_s, self.m) != 1:
            # выберем другой s, но документ указывает на использование суммы LCG как значение.
            # Для практичности приведём s к взаимно простому: добавим 1 пока gcd !=1.
            s = seed_s
            while math.gcd(s, self.m) != 1:
                s += 1
            seed_s = s
        # инициализация x0 = s^2 mod m
        self.state = pow(seed_s, 2, self.m)

    def next_state(self) -> int:
        self.state = pow(self.state, 2, self.m)
        return self.state

    def outputs(self, count: int) -> List[int]:
        """Вернуть count чисел по 64 бита (целые < m)."""
        out = []
        for _ in range(count):
            x = self.next_state()
            out.append(x & ((1 << 64) - 1))  # берем 64 младших бит
        return out

# ------------------ двухступенчатый процесс генерации гаммы ------------------
def generate_gamma_bits_for_length(lcg: LCG, bbs_params: Tuple[int,int], required_bits: int) -> Tuple[str, List[int]]:
    """Сгенерировать битовую строку гаммы длины required_bits.
       Возвращает (gamma_bits, list_of_bbs_outputs_used)"""
    p, q = bbs_params
    gamma_bits = []
    bbs_outputs_used = []

    # цикл пока не набрали нужную длину
    while len(gamma_bits) < required_bits:
        # 1) LCG: генерируем 7 чисел
        seq7 = lcg.generate_n(7)
        summ = sum(seq7)
        # 2) BBS: инициализация seed = summ, получить 5 чисел (по 64 бита)
        bbs = BBS(p, q, summ)
        outs = bbs.outputs(5)  # 5 * 64 bits produced
        bbs_outputs_used.extend(outs)
        # добавить все 5*64 бит
        for val in outs:
            gamma_bits.append(int_to_bin_str(val, 64))
        # 3) передать старшие 20 бит последнего числа в LCG как новое стартовое значение
        last = outs[-1]
        high20 = (last >> (64 - 20)) & ((1 << 20) - 1)
        # устанавливаем состояние LCG равным high20 (в описании: "передает старшие 20 бит последнего числа ... в качестве порождающего значения")
        lcg.state = high20 % lcg.m
    # обрезаем до required_bits
    gamma_binstr = "".join(gamma_bits)[:required_bits]
    return gamma_binstr, bbs_outputs_used

# ------------------ XOR побитно двух строк '0'/'1' ------------------
def xor_bitstrings(a: str, b: str) -> str:
    if len(a) != len(b):
        raise ValueError("Длины битовых строк не равны")
    return ''.join('1' if a[i] != b[i] else '0' for i in range(len(a)))

# ------------------ ключи: генерация/сохранение/загрузка ------------------
def gen_key_file(path: str, lcg_a:int=DEFAULT_LCG_A, lcg_b:int=DEFAULT_LCG_B):
    # Генерируем p,q 32-битные простые ≡3 mod 4
    p = gen_32bit_prime_congruent_3_mod_4()
    q = gen_32bit_prime_congruent_3_mod_4()
    # случайный стартовый seed для LCG (0..m-1)
    seed = randbelow(LCG_MOD)
    key = {
        "lcg": {"a": lcg_a, "b": lcg_b, "m": LCG_MOD, "seed": seed},
        "bbs": {"p": p, "q": q}
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(key, f, indent=2)
    print(f"Ключ сгенерирован и сохранён в {path}")
    print(f"LCG: a={lcg_a}, b={lcg_b}, m={LCG_MOD}, seed={seed}")
    print(f"BBS primes: p={p}  q={q}")
    return key

def load_key_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        key = json.load(f)
    return key

# ------------------ основной рабочий процесс: encrypt/decrypt ------------------
def encrypt_file(keyfile: str, infile: str, outfile: str, show=True):
    key = load_key_file(keyfile)
    lcg_params = key["lcg"]
    bbs_params = (int(key["bbs"]["p"]), int(key["bbs"]["q"]))
    lcg = LCG(int(lcg_params["a"]), int(lcg_params["b"]), int(lcg_params["m"]), int(lcg_params["seed"]))

    plaintext = open(infile, "r", encoding="utf-8").read()
    # убедимся, что все символы в 0..127
    for ch in plaintext:
        if ord(ch) > 127:
            raise ValueError(f"Символ {ch!r} имеет код {ord(ch)} > 127; текст должен быть ASCII 0..127")

    pt_bits = text_to_bitstring_7bit(plaintext)
    required_bits = len(pt_bits)
    gamma_bits, bbs_outs = generate_gamma_bits_for_length(lcg, bbs_params, required_bits)
    cipher_bits = xor_bitstrings(pt_bits, gamma_bits)
    ciphertext = bitstring_to_text_7bit(cipher_bits)

    # Сохранение: plaintext, plaintext_bits, gamma(hex list), gamma_bits, ciphertext, cipher_bits, key (обновл. LCG seed)
    base = os.path.splitext(outfile)[0]
    write_text = lambda p, s: open(p,"w",encoding="utf-8").write(s)

    write_text(base + "_plaintext.txt", plaintext)
    write_text(base + "_plaintext_bits.txt", pt_bits)
    # gamma outs в hex
    gamma_hex = "\n".join(format(x, '016x') for x in bbs_outs)
    write_text(base + "_gamma_blocks_hex.txt", gamma_hex)
    write_text(base + "_gamma_bits.txt", gamma_bits)
    write_text(base + "_ciphertext.txt", ciphertext)
    write_text(base + "_ciphertext_bits.txt", cipher_bits)
    # обновлённый ключ: сохраним текущее состояние LCG (state) обратно в ключ файл
    key["lcg"]["seed"] = lcg.state
    with open(keyfile, "w", encoding="utf-8") as f:
        json.dump(key, f, indent=2)

    if show:
        print("=== ПРЕДОСТАВЛЕННЫЕ ДАННЫЕ ===")
        print("Plaintext (first 512 chars):")
        print(plaintext[:512])
        print("\nPlaintext bits (first 256 bits):")
        print(pt_bits[:256] + ("..." if len(pt_bits)>256 else ""))
        print("\nGamma blocks (hex, shown first 5 blocks):")
        print("\n".join(gamma_hex.splitlines()[:5]))
        print("\nGamma bits (first 256 bits):")
        print(gamma_bits[:256] + ("..." if len(gamma_bits)>256 else ""))
        print("\nCiphertext (first 512 chars; may contain nonprintables):")
        print(ciphertext[:512])
        print("\nCiphertext bits (first 256 bits):")
        print(cipher_bits := cipher_bits[:256] + ("..." if len(cipher_bits)>256 else ""))
        print("\nФайлы сохранены с префиксом:", base + "_*")
        print("Ключ обновлён (lcg.seed = {}) и перезаписан в {}".format(key["lcg"]["seed"], keyfile))
    return True

def decrypt_file(keyfile: str, infile: str, outfile: str, show=True):
    key = load_key_file(keyfile)
    lcg_params = key["lcg"]
    bbs_params = (int(key["bbs"]["p"]), int(key["bbs"]["q"]))
    lcg = LCG(int(lcg_params["a"]), int(lcg_params["b"]), int(lcg_params["m"]), int(lcg_params["seed"]))

    ciphertext = open(infile, "r", encoding="utf-8").read()
    # проверка диапазона
    for ch in ciphertext:
        if ord(ch) > 127:
            raise ValueError(f"Символ {ch!r} имеет код {ord(ch)} > 127; файл шифртекста должен быть ASCII 0..127")

    ct_bits = text_to_bitstring_7bit(ciphertext)
    required_bits = len(ct_bits)
    gamma_bits, bbs_outs = generate_gamma_bits_for_length(lcg, bbs_params, required_bits)
    pt_bits = xor_bitstrings(ct_bits, gamma_bits)
    plaintext = bitstring_to_text_7bit(pt_bits)

    base = os.path.splitext(outfile)[0]
    write_text = lambda p, s: open(p,"w",encoding="utf-8").write(s)
    write_text(base + "_ciphertext.txt", ciphertext)
    write_text(base + "_ciphertext_bits.txt", ct_bits)
    gamma_hex = "\n".join(format(x, '016x') for x in bbs_outs)
    write_text(base + "_gamma_blocks_hex.txt", gamma_hex)
    write_text(base + "_gamma_bits.txt", gamma_bits)
    write_text(base + "_plaintext.txt", plaintext)
    write_text(base + "_plaintext_bits.txt", pt_bits)

    # обновим seed в ключе
    key["lcg"]["seed"] = lcg.state
    with open(keyfile, "w", encoding="utf-8") as f:
        json.dump(key, f, indent=2)

    if show:
        print("=== ВЫВОД ДЕШИФРОВАНИЯ ===")
        print("Ciphertext (first 512 chars):")
        print(ciphertext[:512])
        print("\nCiphertext bits (first 256 bits):")
        print(ct_bits[:256] + ("..." if len(ct_bits)>256 else ""))
        print("\nGamma blocks (hex, first 5):")
        print("\n".join(gamma_hex.splitlines()[:5]))
        print("\nGamma bits (first 256 bits):")
        print(gamma_bits[:256] + ("..." if len(gamma_bits)>256 else ""))
        print("\nRecovered plaintext (first 512 chars):")
        print(plaintext[:512])
        print("\nPlaintext bits (first 256 bits):")
        print(pt_bits[:256] + ("..." if len(pt_bits)>256 else ""))
        print("\nФайлы сохранены с префиксом:", base + "_*")
        print("Ключ обновлён (lcg.seed = {}) и перезаписан в {}".format(key["lcg"]["seed"], keyfile))
    return True

# ------------------ CLI ------------------
def main():
    parser = argparse.ArgumentParser(description="Лабораторная (Вариант 22). Гаммирование: LCG(2^20) -> BBS(64bit).")
    parser.add_argument("--genkey", help="Сгенерировать ключ и сохранить в файл (JSON). Пример: --genkey key.json")
    parser.add_argument("--key", help="Файл ключа (JSON)")
    parser.add_argument("--mode", choices=["encrypt","decrypt"], help="encrypt / decrypt")
    parser.add_argument("--in", dest="infile", help="Входной файл (plaintext или ciphertext)")
    parser.add_argument("--out", dest="outfile", help="Базовое имя выходных файлов (будут дополняться _plaintext/_gamma_... )")
    parser.add_argument("--no-show", action="store_true", help="Не печатать данные на экран")
    parser.add_argument("--lcg-a", type=int, default=DEFAULT_LCG_A, help="(опционально) параметр a для LCG при генерации ключа")
    parser.add_argument("--lcg-b", type=int, default=DEFAULT_LCG_B, help="(опционально) параметр b для LCG при генерации ключа")

    args = parser.parse_args()

    if args.genkey:
        gen_key_file(args.genkey, lcg_a=args.lcg_a, lcg_b=args.lcg_b)
        return

    if args.mode:
        if not args.key or not args.infile or not args.outfile:
            print("Для режима encrypt/decrypt укажите --key, --in и --out")
            return
        show = not args.no_show
        if args.mode == "encrypt":
            encrypt_file(args.key, args.infile, args.outfile, show=show)
        else:
            decrypt_file(args.key, args.infile, args.outfile, show=show)
        return

    parser.print_help()

if __name__ == "__main__":
    main()


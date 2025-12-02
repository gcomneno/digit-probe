#!/usr/bin/env python3
"""
Scarica tutte le estrazioni Lotto 2025 da estrazionedellotto.it
e genera:

- lotto_2025_digits.txt  : stream di cifre (tutti i numeri zero-padded)
- lotto_2025_numbers.txt : stream di numeri a due cifre separati da spazio

NOTA: non distinguiamo più le singole estrazioni,
prendiamo semplicemente tutti i <li class="ball"> in ordine di pagina.
"""

from __future__ import annotations

from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.estrazionedellotto.it/risultati/archivio-lotto-2025"


def fetch_page(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_all_numbers(html: str) -> list[int]:
    soup = BeautifulSoup(html, "html.parser")

    numbers: list[int] = []

    # Prendiamo TUTTI i <li class="ball"> in ordine di apparizione
    for li in soup.find_all("li", class_="ball"):
        t = li.get_text(strip=True)
        if not t.isdigit():
            continue
        n = int(t)
        # Lotto: 1..90
        if 1 <= n <= 90:
            numbers.append(n)

    return numbers


def main() -> None:
    html = fetch_page(URL)
    all_numbers = parse_all_numbers(html)

    if not all_numbers:
        print("Nessun numero trovato (li.ball). Probabile cambio HTML.")
        return

    print(f"Numeri trovati in totale (li.ball): {len(all_numbers)}")

    # Zero-padding a due cifre
    padded = [f"{n:02d}" for n in all_numbers]
    digits_str = "".join(padded)
    numbers_str = " ".join(padded) + "\n"

    out_digits = Path("lotto_2025_digits.txt")
    out_numbers = Path("lotto_2025_numbers.txt")

    out_digits.write_text(digits_str, encoding="utf-8")
    out_numbers.write_text(numbers_str, encoding="utf-8")

    print(f"Cifre totali: {len(digits_str)}")
    print(f"Scritto: {out_digits} e {out_numbers}")

    # Controllo opzionale di "multiplo di 55" (11 ruote * 5 numeri)
    if len(all_numbers) % 55 != 0:
        print(
            f"ATTENZIONE: {len(all_numbers)} non è multiplo di 55. "
            "Potrebbero esserci numeri extra (es. altro contenuto nella pagina)."
        )


if __name__ == "__main__":
    main()

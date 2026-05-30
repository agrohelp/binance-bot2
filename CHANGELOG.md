# Changelog
Wszystkie istotne zmiany w tym projekcie będą dokumentowane w tym pliku.

Format oparty na Keep a Changelog.
Wersjonowanie zgodne z Semantic Versioning.

---

## [2.3] — 2026-05-30
### Added
- Wprowadzono **ATR PRO Engine**:
  - ATR oparty na EMA.
  - Minimalny i maksymalny próg ATR.
  - Ochrona przed spike’ami danych.
  - Stabilne wartości dla trailing stopu.

- Dodano **dynamiczny trailing stop**:
  - TS nigdy nie spada.
  - TS nie może być poniżej SL.
  - TS nie może być powyżej ceny.
  - TS reaguje na zmienność w sposób kontrolowany.

### Changed
- Zaktualizowano strategię 4H:
  - Poluzowane wejścia BUY (EMA 0.03%, STOCH 0.2, MACD tolerancja).
  - Stabilniejsze wyliczanie wskaźników.
  - Lepsza diagnostyka filtrów BUY/SELL.

- Usprawniono logikę BUY w bot.py:
  - TS inicjalizowany na SL.
  - ATR PRO używany przy wejściu i aktualizacji.

### Fixed
- Poprawiono sanity-checki świec i wskaźników.
- Eliminacja błędów przy konwersji danych z Binance.
- Stabilizacja logów i obsługi wyjątków.

---

## [1.9] — ostatnia wersja przed refaktorem
### Notes
- Ostatni commit obejmujący zakres v1.1–v1.9.
- Zawierał podstawową logikę strategii i bota.
- Brak szczegółowego changeloga dla wcześniejszych wersji.

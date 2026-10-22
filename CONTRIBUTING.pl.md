# Współtworzenie hz432

🇬🇧 [English version](CONTRIBUTING.md)

Dzięki za chęć rozwijania hz432! Zgłoszenia błędów, pomysły i pull requesty są mile widziane.

## Zgłaszanie błędów i propozycji

- Najpierw przeszukaj istniejące issues – być może problem już zgłoszono.
- Korzystaj z szablonów issues. Przy błędach podaj system, wersję Pythona, dokładne polecenie i pełny wynik.
  Przy problemach z wykrywaniem strojenia bardzo pomaga wynik `--analyze-only`.
- **Nie** załączaj plików audio chronionych prawem autorskim. Jeśli chodzi o konkretny utwór – opisz go
  (tytuł, wydanie) albo udostępnij krótki fragment, do którego masz prawa.

## Środowisko deweloperskie

```
git clone <adres twojego forka>
cd hz432
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

Przed otwarciem pull requesta uruchom:

```
ruff check .
pytest
```

Te same sprawdzenia działają w CI na Linuksie i Windows.

## Pull requesty

1. Zrób fork i utwórz gałąź od `main` (np. `fix/ambiguous-detection`).
2. Jedna zmiana (funkcja albo poprawka) na pull request.
3. Dodaj lub zaktualizuj testy w `tests/`. Testy nie mogą wymagać prawdziwych plików muzycznych –
   generuj sygnały syntetyczne (patrz `chord()` w `tests/test_hz432.py`).
4. Zaktualizuj `README.md` i `README.pl.md`, jeśli zmieniasz opcje lub działanie programu.
5. Dodaj wpis w sekcji **[Unreleased]** w `CHANGELOG.md`.
6. Pisz zwięzłe opisy commitów w trybie rozkazującym, po angielsku („Add …”, „Fix …”).

### Zmiany w wykrywaniu strojenia lub polityce decyzji

Wpływają bezpośrednio na wynik każdej konwersji. Opisz w pull requeście, jak zweryfikowano zmianę – najlepiej
zmierzone strojenie przed i po na próbce prawdziwych nagrań oraz wpływ na rozrzut wynikowego A4 wokół celu.

## Wersjonowanie i wydania

Projekt stosuje [Semantic Versioning](https://semver.org/lang/pl/). Wersja jest w jednym miejscu:
`__version__` w `hz432.py`. Wydanie to: podbicie `__version__`, przeniesienie wpisów z **[Unreleased]**
w changelogu pod nową wersję i tag `vX.Y.Z` na commicie.

## Kodeks postępowania

Projekt stosuje [Contributor Covenant](CODE_OF_CONDUCT.md)
([tłumaczenie polskie](https://www.contributor-covenant.org/pl/version/2/1/code_of_conduct/)).
Biorąc udział, zobowiązujesz się go przestrzegać.

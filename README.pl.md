# hz432 – konwerter MP3 do A4 = 432 Hz

[![CI](https://github.com/doitglobal/hz432/actions/workflows/ci.yml/badge.svg)](https://github.com/doitglobal/hz432/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)

🇬🇧 [English README](README.md)

Narzędzie konsolowe, które przestraja pliki MP3 (pojedynczy plik albo cały folder z podfolderami) do **A4 = 432 Hz**.
Najpierw **mierzy rzeczywiste strojenie każdego utworu**, a dopiero potem przelicza, tak by A w nagraniu wypadło
jak najbliżej 432 Hz.

```
setup.bat                                                 # jednorazowo: tworzy .venv i instaluje biblioteki (bezpieczne do powtórzenia)
.venv\Scripts\python hz432.py "C:\Muzyka"                 # folder + podfoldery -> C:\Muzyka_432Hz\ (ta sama struktura)
.venv\Scripts\python hz432.py "C:\Muzyka\a.mp3"           # pojedynczy plik -> "a [432Hz].mp3" obok oryginału
.venv\Scripts\python hz432.py "C:\Muzyka" --analyze-only  # tylko pomiar strojenia, bez zapisu
.venv\Scripts\python hz432.py --version
```

## Instalacja (`setup.bat` / `setup.sh`)
Wymaga Pythona 3.10+ (python.org) i internetu przy pierwszym uruchomieniu. Na Windows uruchom `setup.bat` (dwuklik albo z konsoli w folderze projektu), na Linux/macOS `./setup.sh`:
- jeśli brak folderu `.venv` – tworzy wirtualne środowisko Pythona,
- instaluje biblioteki z `requirements.txt` do `.venv` (nic nie trafia do systemowego Pythona),
- przy kolejnych uruchomieniach tylko dociąga brakujące pakiety – można go odpalać bez obaw.

Folder `.venv` nie jest w repozytorium. Po sklonowaniu repo, przeniesieniu na inny komputer albo usunięciu `.venv` wystarczy ponownie uruchomić skrypt. Alternatywnie: `pip install .` (dodaje polecenie `hz432`).

## Opcje
Przydatne: `-o FOLDER`, `-j N` (wątki), `--mode pitch` (sama wysokość, tempo bez zmian – gdy potrzebna synchronizacja z wideo/tekstem), `--ref-hz 438` (wymuś znane strojenie), `--policy`.
Nie wymaga ffmpeg – MP3 czytane/zapisywane przez `pedalboard`, domyślnie resampling (`speed`), tryb `pitch` używa Rubber Band, tagi ID3 (z okładką) kopiuje `mutagen`.
Pliki już skonwertowane są oznaczone tagiem `HZ432_CONVERTER` i pomijane (nadpisz `--force`).
Komunikaty programu i pomoc (`--help`) są po angielsku.

## Jak zapada decyzja (polityka `auto`)
1. **Pomiar**: szczyty widma → odległość od siatki 440 w centach → histogram → strojenie utworu + „pewność” (0.21 = szum, ~1 = czysta tonalna muzyka).
2. **Pewność < 0.35** (perkusja, elektronika, szum) → zakładam 440 (standard).
3. **Zmierzone w granicy błędu pomiaru od 440 (±1 c ≈ ±0,25 Hz)** → traktuję jak 440 (`--snap-cents`). Pomiar jest powtarzalny do ~0,5 c (ten sam utwór z różnych wydań), a realne nagrania odchodzą od 440 o 1–10 c, więc szersze „przyciąganie” oddalałoby wynik od 432.
4. **Inaczej** → przeliczam matematycznie od zmierzonej wartości (np. 437 → 432, 442 → 432). Powód: celem jest, by *faktyczne* A w nagraniu wypadło na 432; „dociąganie do 440” zostawiłoby utwór 3 Hz za wysoko. Realne nagrania często nie są w 440 (orkiestry 442–443, taśmy analogowe z dryfem prędkości, stare płyty).
5. **~±50 c od 440** (np. 428 / 453) → pomijam: pomiar jest znany tylko modulo półton, więc nie wiadomo w którą stronę korygować. Wtedy `--ref-hz`.
6. Utwory już w ~432 (±1 c) są pomijane.

Tryb domyślny `speed` działa jak zwolnienie płyty: utwór jest o ok. 1,8–2,7% dłuższy (tempo odpowiednio niższe), ale resampling jest praktycznie bezstratny. Tryb `pitch` zachowuje tempo, kosztem drobnych artefaktów algorytmu.

Uwaga: MP3 jest kodowany ponownie (stratnie) – bitrate zostaje taki jak w oryginale; dla archiwum zachowaj oryginały.

## Rozwój
```
pip install -e ".[dev]"
ruff check .
pytest
```
Zasady współpracy: [CONTRIBUTING.pl.md](CONTRIBUTING.pl.md), historia zmian: [CHANGELOG.md](CHANGELOG.md).

## Licencja
[MIT](LICENSE) © DO IT GLOBAL LTD

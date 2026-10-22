# Security Policy

## Supported versions

Only the latest released version receives fixes.

| Version | Supported |
|---|---|
| 1.0.x | ✅ |

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Report it privately through GitHub: open the repository's **Security** tab and click
**Report a vulnerability**. Include a description, steps to reproduce and, if possible, a minimal input file
that triggers the problem.

You should receive a response within 7 days. Once the issue is confirmed, a fix will be prepared and released,
and you will be credited in the changelog unless you prefer otherwise.

hz432 processes local audio files with third-party decoders (`pedalboard`, `librosa`, `mutagen`).
Vulnerabilities in those libraries should also be reported to their maintainers.

---

### 🇵🇱 Zgłaszanie luk bezpieczeństwa

**Nie** zgłaszaj problemów bezpieczeństwa w publicznym issue. Użyj prywatnego zgłoszenia na GitHubie:
zakładka **Security** → **Report a vulnerability**. Podaj opis, kroki odtworzenia i, jeśli to możliwe,
minimalny plik wejściowy wywołujący problem. Odpowiedź w ciągu 7 dni; wspierana jest tylko najnowsza wersja.

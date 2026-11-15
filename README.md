# Email Sorter

Jednoduchý softvér na triedenie e-mailov pomocou IMAP.

## Funkcie
- Pripojenie k IMAP schránke (Gmail, Outlook, atď.)
- Triedenie e-mailov podľa pravidiel (odosielateľ, predmet, kľúčové slová)
- Presúvanie do zložiek
- Konfiguračný súbor pre pravidlá

## Inštalácia

```bash
pip install -r requirements.txt
```

## Konfigurácia

1. Skopíruj `config.example.yaml` na `config.yaml`
2. Vyplň údaje o účte a pravidlá

## Spustenie

```bash
python email_sorter.py
```

## Príklad pravidiel

```yaml
rules:
  - name: "Práca"
    folder: "INBOX/Praca"
    conditions:
      from: ["@firma.sk", "boss@company.com"]
      subject_contains: ["projekt", "meeting"]
  - name: "Newsletter"
    folder: "INBOX/Newsletters"
    conditions:
      from: ["newsletter@", "noreply@"]
```

## Poznámka

Pre Gmail potrebuješ App Password (nie bežné heslo).

Vytvorené pre používateľa pumba145.

#!/usr/bin/env python3
"""
Email Sorter - jednoduchý nástroj na triedenie e-mailov cez IMAP
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import yaml
    from imapclient import IMAPClient
except ImportError:
    print("Chýbajú závislosti. Spusti: pip install -r requirements.txt")
    sys.exit(1)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        logger.error(f"Konfiguračný súbor '{path}' neexistuje.")
        logger.info("Skopíruj config.example.yaml na config.yaml a uprav ho.")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def matches_condition(value: str, patterns: List[str]) -> bool:
    """Skontroluje, či hodnota obsahuje niektorý z patternov (case-insensitive)."""
    if not value or not patterns:
        return False
    value_lower = value.lower()
    return any(p.lower() in value_lower for p in patterns)


def email_matches_rule(msg, rule: Dict[str, Any]) -> bool:
    """Skontroluje, či e-mail zodpovedá pravidlu."""
    conditions = rule.get("conditions", {})

    # From
    from_patterns = conditions.get("from", [])
    if from_patterns:
        from_header = msg.get(b"FROM", b"").decode("utf-8", errors="ignore")
        if not matches_condition(from_header, from_patterns):
            return False

    # Subject contains
    subject_patterns = conditions.get("subject_contains", [])
    if subject_patterns:
        subject = msg.get(b"SUBJECT", b"").decode("utf-8", errors="ignore")
        if not matches_condition(subject, subject_patterns):
            return False

    # Ak sú nejaké podmienky a všetky prešli (alebo žiadne neboli),
    # považujeme to za match (AND logika medzi typmi podmienok)
    return bool(from_patterns or subject_patterns)


def ensure_folder(client: IMAPClient, folder: str) -> None:
    """Vytvorí zložku, ak neexistuje."""
    try:
        client.create_folder(folder)
        logger.info(f"Vytvorená zložka: {folder}")
    except Exception:
        # Zložka už existuje alebo iná chyba – ignorujeme
        pass


def sort_emails(config: Dict[str, Any]) -> None:
    imap_cfg = config["imap"]
    source = config.get("source_folder", "INBOX")
    rules = config.get("rules", [])

    if not rules:
        logger.warning("Žiadne pravidlá nie sú definované.")
        return

    logger.info(f"Pripájam sa na {imap_cfg['host']}:{imap_cfg.get('port', 993)}...")

    with IMAPClient(
        imap_cfg["host"],
        port=imap_cfg.get("port", 993),
        ssl=imap_cfg.get("ssl", True),
    ) as client:
        client.login(imap_cfg["username"], imap_cfg["password"])
        logger.info("Prihlásenie úspešné.")

        client.select_folder(source)
        messages = client.search(["UNSEEN"])  # len neprečítané, alebo ALL
        # Ak chceš všetky: messages = client.search(["ALL"])

        if not messages:
            logger.info("Žiadne e-maily na spracovanie.")
            return

        logger.info(f"Našiel som {len(messages)} e-mailov.")

        # Stiahni hlavičky
        fetch_data = client.fetch(messages, ["ENVELOPE", "BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)]"])

        moved = 0
        for uid, data in fetch_data.items():
            # Zjednodušené získanie FROM a SUBJECT
            headers = data.get(b"BODY[HEADER.FIELDS (FROM SUBJECT)]", b"")
            header_str = headers.decode("utf-8", errors="ignore")

            from_addr = ""
            subject = ""
            for line in header_str.splitlines():
                if line.lower().startswith("from:"):
                    from_addr = line[5:].strip()
                elif line.lower().startswith("subject:"):
                    subject = line[8:].strip()

            # Vytvor pseudo-msg dict pre kompatibilitu
            msg = {
                b"FROM": from_addr.encode("utf-8"),
                b"SUBJECT": subject.encode("utf-8"),
            }

            for rule in rules:
                if email_matches_rule(msg, rule):
                    target_folder = rule["folder"]
                    ensure_folder(client, target_folder)
                    client.move([uid], target_folder)
                    logger.info(
                        f"Presunutý UID {uid} → {target_folder} "
                        f"(pravidlo: {rule.get('name', 'bez názvu')})"
                    )
                    moved += 1
                    break  # prvé zodpovedajúce pravidlo

        logger.info(f"Hotovo. Presunutých e-mailov: {moved}")


def main():
    config = load_config()
    try:
        sort_emails(config)
    except Exception as e:
        logger.exception(f"Chyba pri triedení: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

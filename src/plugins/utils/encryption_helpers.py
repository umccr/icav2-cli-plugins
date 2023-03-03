#!/usr/bin/env python3

"""
Encryption based helpers
"""

from base64 import b64encode
from pathlib import Path
import subprocess

from utils.logger import get_logger

logger = get_logger()


def encrypt_presigned_url_with_public_key(presigned_url: str, public_key: Path) -> str:
    openssl_command_list = [
            "openssl", "pkeyutl",
            "-encrypt",
            "-inkey", str(public_key),
            "-keyform", "PEM",
            "-pubin"
    ]
    openssl_proc = subprocess.run(
        openssl_command_list,
        input=f"{presigned_url}\n".encode("ascii"),
        capture_output=True
    )

    if not openssl_proc.returncode == 0:
        logger.error("Failed to encrypt presigned url")
        logger.error(f"Collected the following stderr message {openssl_proc.stderr.decode()}")

    return str(b64encode(openssl_proc.stdout))


def encrypt_presigned_url_with_keybase(presigned_url: str, keybase_name: str, is_keybase_team=False) -> str:
    keybase_command_list = [
        "keybase", "encrypt",
        "--binary"
    ]

    if is_keybase_team:
        keybase_command_list.append(
            "--team"
        )

    keybase_command_list.append(
        keybase_name
    )

    keybase_proc = subprocess.run(
        keybase_command_list,
        input=f"{presigned_url}\n".encode("ascii"),
        capture_output=True
    )

    if not keybase_proc.returncode == 0:
        logger.error("Failed to encrypt presigned url")
        logger.error(f"Collected the following stderr message {keybase_proc.stderr.decode()}")

    return str(b64encode(keybase_proc.stdout).decode())

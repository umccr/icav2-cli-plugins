#!/usr/bin/env python3
"""
Hybrid encryption for secrets stored in the config file.

Uses hybrid RSA+AES encryption to handle values of arbitrary length:
  1. Generate a random 256-bit AES key
  2. Encrypt the plaintext with AES-256-GCM (authenticated encryption)
  3. Encrypt the AES key with RSA-OAEP/SHA-256
  4. Store: base64(RSA-encrypted-AES-key || nonce || ciphertext || tag)

This approach handles secrets of any size (API keys, JWT tokens, etc.)
while providing authenticated encryption and forward secrecy per value.

Supports optional passphrase protection on private keys.

Key storage location (default): ~/.icav2-cli-plugins/keys/
"""

import os
import sys
from base64 import b64decode, b64encode
from getpass import getpass
from pathlib import Path
from typing import Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# Prefix that marks an encrypted value in the config file
ENCRYPTED_PREFIX = "ENCRYPTED:"

# Default key directory
DEFAULT_KEY_DIR = Path.home() / ".icav2-cli-plugins" / "keys"
DEFAULT_PRIVATE_KEY_PATH = DEFAULT_KEY_DIR / "id_rsa"
DEFAULT_PUBLIC_KEY_PATH = DEFAULT_KEY_DIR / "id_rsa.pub"

# RSA key size
RSA_KEY_SIZE = 4096

# AES key size in bytes (256-bit)
AES_KEY_SIZE = 32

# AES-GCM nonce size in bytes (96-bit, standard for GCM)
AES_NONCE_SIZE = 12


def is_encrypted(value: str) -> bool:
    """Check if a stored value is encrypted."""
    return value.startswith(ENCRYPTED_PREFIX)


def generate_key_pair(
    private_key_path: Path = DEFAULT_PRIVATE_KEY_PATH,
    public_key_path: Path = DEFAULT_PUBLIC_KEY_PATH,
    passphrase: Optional[str] = None,
) -> Tuple[Path, Path]:
    """
    Generate an RSA key pair for secret encryption.

    Args:
        private_key_path: Where to write the private key (PEM format).
        public_key_path: Where to write the public key (PEM format).
        passphrase: Optional passphrase to protect the private key.

    Returns:
        Tuple of (private_key_path, public_key_path).

    Raises:
        FileExistsError: If key files already exist (won't overwrite).
    """
    if private_key_path.exists():
        raise FileExistsError(
            f"Private key already exists at {private_key_path}. "
            f"Remove it first if you want to regenerate."
        )
    if public_key_path.exists():
        raise FileExistsError(
            f"Public key already exists at {public_key_path}. "
            f"Remove it first if you want to regenerate."
        )

    # Generate RSA private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=RSA_KEY_SIZE,
    )

    # Determine encryption for private key storage
    if passphrase:
        encryption = serialization.BestAvailableEncryption(
            passphrase.encode("utf-8")
        )
    else:
        encryption = serialization.NoEncryption()

    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption,
    )

    # Serialize public key
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Write keys to disk with appropriate permissions
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    public_key_path.parent.mkdir(parents=True, exist_ok=True)

    private_key_path.write_bytes(private_pem)
    os.chmod(private_key_path, 0o600)

    public_key_path.write_bytes(public_pem)
    os.chmod(public_key_path, 0o644)

    return private_key_path, public_key_path


def encrypt_secret(
    plaintext: str,
    public_key_path: Path = DEFAULT_PUBLIC_KEY_PATH,
) -> str:
    """
    Encrypt a secret using hybrid RSA+AES-GCM encryption.

    Steps:
      1. Generate a random 256-bit AES key
      2. Encrypt plaintext with AES-256-GCM
      3. Encrypt the AES key with RSA-OAEP/SHA-256
      4. Concatenate: encrypted_aes_key + nonce + ciphertext_with_tag
      5. Base64-encode and prefix with ENCRYPTED:

    Args:
        plaintext: The secret to encrypt (any length).
        public_key_path: Path to the PEM-encoded RSA public key.

    Returns:
        String in format "ENCRYPTED:<base64-encoded-blob>".

    Raises:
        FileNotFoundError: If the public key file doesn't exist.
        ValueError: If the public key file is invalid.
    """
    if not public_key_path.exists():
        raise FileNotFoundError(
            f"Public key not found at {public_key_path}. "
            f"Run 'icav2 configure generate-keys' to create one."
        )

    public_key_pem = public_key_path.read_bytes()

    try:
        public_key = serialization.load_pem_public_key(public_key_pem)
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"Invalid public key at {public_key_path}: {e}"
        ) from e

    # Step 1: Generate random AES key
    aes_key = os.urandom(AES_KEY_SIZE)

    # Step 2: Encrypt plaintext with AES-256-GCM
    nonce = os.urandom(AES_NONCE_SIZE)
    aesgcm = AESGCM(aes_key)
    # AES-GCM appends a 16-byte auth tag to the ciphertext
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    # Step 3: Encrypt the AES key with RSA-OAEP
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    # Step 4: Concatenate — we need to know the RSA ciphertext length for parsing
    # RSA-4096 always produces 512-byte ciphertext
    blob = encrypted_aes_key + nonce + ciphertext_with_tag

    # Step 5: Base64-encode and prefix
    encoded = b64encode(blob).decode("ascii")
    return f"{ENCRYPTED_PREFIX}{encoded}"


# Keep the old name as an alias for backward compatibility
encrypt_api_key = encrypt_secret


def decrypt_secret(
    encrypted_value: str,
    private_key_path: Path = DEFAULT_PRIVATE_KEY_PATH,
    passphrase: Optional[str] = None,
) -> str:
    """
    Decrypt a hybrid-encrypted secret using the RSA private key.

    Steps:
      1. Base64-decode the blob
      2. Split into: encrypted_aes_key (512 bytes for RSA-4096) + nonce (12) + ciphertext_with_tag
      3. Decrypt AES key with RSA-OAEP
      4. Decrypt ciphertext with AES-256-GCM

    Args:
        encrypted_value: String in format "ENCRYPTED:<base64-blob>".
        private_key_path: Path to the PEM-encoded private key.
        passphrase: Passphrase for the private key (if encrypted).

    Returns:
        The decrypted plain-text secret.

    Raises:
        FileNotFoundError: If the private key file doesn't exist.
        ValueError: If the encrypted value format is invalid or decryption fails.
    """
    if not encrypted_value.startswith(ENCRYPTED_PREFIX):
        raise ValueError(
            "Value does not appear to be encrypted (missing ENCRYPTED: prefix)"
        )

    if not private_key_path.exists():
        raise FileNotFoundError(
            f"Private key not found at {private_key_path}. "
            f"Cannot decrypt without the private key."
        )

    # Extract the base64-encoded blob
    b64_blob = encrypted_value[len(ENCRYPTED_PREFIX):]

    try:
        blob = b64decode(b64_blob)
    except Exception as e:
        raise ValueError(
            f"Invalid base64 encoding in encrypted value: {e}"
        ) from e

    # Load private key
    private_key_pem = private_key_path.read_bytes()
    password = passphrase.encode("utf-8") if passphrase else None

    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=password,
        )
    except TypeError:
        # Private key is encrypted but no passphrase provided
        raise ValueError(
            f"Private key at {private_key_path} is passphrase-protected. "
            f"Provide the passphrase to decrypt."
        )
    except (ValueError, Exception) as e:
        raise ValueError(
            f"Cannot load private key at {private_key_path}: {e}"
        ) from e

    # Parse the blob: RSA ciphertext is key_size_bytes (512 for RSA-4096)
    rsa_key_size_bytes = private_key.key_size // 8  # 512 for RSA-4096
    min_blob_size = rsa_key_size_bytes + AES_NONCE_SIZE + 1  # at least 1 byte of ciphertext

    if len(blob) < min_blob_size:
        raise ValueError(
            f"Encrypted blob is too short ({len(blob)} bytes). "
            f"Expected at least {min_blob_size} bytes."
        )

    encrypted_aes_key = blob[:rsa_key_size_bytes]
    nonce = blob[rsa_key_size_bytes:rsa_key_size_bytes + AES_NONCE_SIZE]
    ciphertext_with_tag = blob[rsa_key_size_bytes + AES_NONCE_SIZE:]

    # Decrypt AES key with RSA
    try:
        aes_key = private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as e:
        raise ValueError(
            f"RSA decryption failed. The private key may not match the public key "
            f"used for encryption: {e}"
        ) from e

    # Decrypt data with AES-GCM
    try:
        aesgcm = AESGCM(aes_key)
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
    except Exception as e:
        raise ValueError(
            f"AES-GCM decryption failed. Data may be corrupted or tampered with: {e}"
        ) from e

    return plaintext_bytes.decode("utf-8")


# Keep the old name as an alias for backward compatibility
decrypt_api_key = decrypt_secret


def resolve_api_key(
    stored_value: str,
    private_key_path: Optional[Path] = None,
    passphrase: Optional[str] = None,
) -> str:
    """
    Resolve a secret value from config — decrypts if encrypted, returns as-is if plain text.

    This is the main entry point for the token manager to get a usable secret.

    Args:
        stored_value: The value from the config file (may be plain or encrypted).
        private_key_path: Path to private key (uses default if None).
        passphrase: Passphrase for private key (prompts interactively if needed).

    Returns:
        The plain-text secret ready for use.
    """
    if not is_encrypted(stored_value):
        return stored_value

    key_path = private_key_path or DEFAULT_PRIVATE_KEY_PATH

    try:
        return decrypt_secret(stored_value, key_path, passphrase)
    except ValueError as e:
        if "passphrase-protected" in str(e):
            # Prompt for passphrase interactively
            try:
                prompted_passphrase = getpass(
                    "Enter passphrase for private key: "
                )
                return decrypt_secret(
                    stored_value, key_path, prompted_passphrase
                )
            except (ValueError, EOFError) as inner_e:
                print(
                    f"Error: Could not decrypt: {inner_e}",
                    file=sys.stderr,
                )
                sys.exit(1)
        raise

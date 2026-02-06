"""
Generate encryption key for token encryption
"""
from cryptography.fernet import Fernet

# Generate a new encryption key
key = Fernet.generate_key()
print("Generated Encryption Key (add this to .env):")
print(f"ENCRYPTION_KEY={key.decode()}")


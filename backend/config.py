from dotenv import load_dotenv
import os
from cryptography.fernet import Fernet
import base64

load_dotenv()

class Config:
    DATABASE_FILE = "credentials.db"
    SECRET_KEY = os.getenv("SECRET_KEY")

# Test print om te verifiëren
print("Loaded SECRET_KEY:", Config.SECRET_KEY)

# Deze functie controleert of de sleutel 32 bytes lang en base64-gecodeerd is
def verify_fernet_key(key):
    try:
        decoded_key = base64.urlsafe_b64decode(key)
        return len(decoded_key) == 32
    except Exception as e:
        print("Key is invalid:", e)
        return False

# In config.py toevoegen om de sleutel te controleren
print("Sleutel is geldig:", verify_fernet_key(Config.SECRET_KEY))

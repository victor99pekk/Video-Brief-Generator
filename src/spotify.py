import jwt
import time

TEAM_ID = "YOUR_TEAM_ID"
KEY_ID = "YOUR_KEY_ID"
PRIVATE_KEY_PATH = "AuthKey_YOUR_KEY_ID.p8"

# Load private key
with open(PRIVATE_KEY_PATH, "r") as f:
    private_key = f.read()

# Create token payload
issued_at = int(time.time())
expiration_time = issued_at + (60 * 60 * 24 * 180)  # 180 days

headers = {
    "alg": "ES256",
    "kid": KEY_ID
}

payload = {
    "iss": TEAM_ID,
    "iat": issued_at,
    "exp": expiration_time
}

# Generate JWT
token = jwt.encode(
    payload,
    private_key,
    algorithm="ES256",
    headers=headers
)

print("Your Apple Music Developer Token:\n")
print(token)

"""
Manually verify SCRAM-SHA-256 proof computation.
Compares what pymongo computes vs. the correct SCRAM spec.
Also tests alternative password preprocessing that CosmosDB might expect.
"""
import hashlib
import hmac
import base64


def hi(password_bytes, salt, iterations):
    """PBKDF2-HMAC-SHA256 (Hi function from SCRAM spec)."""
    return hashlib.pbkdf2_hmac("sha256", password_bytes, salt, iterations)


def compute_scram_proof(password_bytes, salt_b64, iterations, client_nonce, server_nonce, username):
    """Compute the full SCRAM-SHA-256 client proof."""
    salt = base64.b64decode(salt_b64)

    # SaltedPassword
    salted_password = hi(password_bytes, salt, iterations)

    # ClientKey, StoredKey
    client_key = hmac.new(salted_password, b"Client Key", hashlib.sha256).digest()
    stored_key = hashlib.sha256(client_key).digest()

    # AuthMessage
    client_first_bare = "n=%s,r=%s" % (username, client_nonce)
    server_first = "r=%s,s=%s,i=%d" % (server_nonce, salt_b64, iterations)
    client_final_without_proof = "c=biws,r=%s" % server_nonce
    auth_message = "%s,%s,%s" % (client_first_bare, server_first, client_final_without_proof)

    # ClientSignature
    client_signature = hmac.new(stored_key, auth_message.encode("utf-8"), hashlib.sha256).digest()

    # ClientProof = ClientKey XOR ClientSignature
    client_proof = bytes(a ^ b for a, b in zip(client_key, client_signature))
    return base64.b64encode(client_proof).decode("ascii")


# Captured values from the SCRAM handshake
USERNAME = "serveradmin"
PASSWORD = "BaosWheels623"
CLIENT_NONCE = "67bj+4/Lrquxw+Crt6PcmrJt3k+JZ62hByHzK9/DjWk="
SERVER_NONCE = "67bj+4/Lrquxw+Crt6PcmrJt3k+JZ62hByHzK9/DjWk=uF"
SALT_B64 = "07ckO2C2iaMWtUTLSHBuWO8WvbdXOiNa/ciMxg=="
ITERATIONS = 4096
PYMONGO_PROOF = "J60QRBLl4c8uk4ekTTxsvq24OHMdfNA+aA/tgSKrTzw="

print("=== Testing different password preprocessing ===\n")

# Test 1: Standard SCRAM-SHA-256 (SASLprep'd password as UTF-8)
proof1 = compute_scram_proof(
    PASSWORD.encode("utf-8"), SALT_B64, ITERATIONS,
    CLIENT_NONCE, SERVER_NONCE, USERNAME
)
print("1. Standard (password as UTF-8):")
print("   Proof: %s" % proof1)
print("   Match pymongo: %s" % (proof1 == PYMONGO_PROOF))
print()

# Test 2: MD5 digest (what SCRAM-SHA-1 uses: md5(user:mongo:password))
md5_pw = hashlib.md5(("%s:mongo:%s" % (USERNAME, PASSWORD)).encode("utf-8")).hexdigest()
proof2 = compute_scram_proof(
    md5_pw.encode("utf-8"), SALT_B64, ITERATIONS,
    CLIENT_NONCE, SERVER_NONCE, USERNAME
)
print("2. MD5 digest (user:mongo:password):")
print("   Proof: %s" % proof2)
print()

# Test 3: Just the raw password bytes (no SASLprep, same for ASCII)
proof3 = compute_scram_proof(
    PASSWORD.encode("ascii"), SALT_B64, ITERATIONS,
    CLIENT_NONCE, SERVER_NONCE, USERNAME
)
print("3. ASCII password:")
print("   Proof: %s" % proof3)
print("   Match standard: %s" % (proof3 == proof1))
print()

# Test 4: SHA256 of password
sha_pw = hashlib.sha256(PASSWORD.encode("utf-8")).hexdigest()
proof4 = compute_scram_proof(
    sha_pw.encode("utf-8"), SALT_B64, ITERATIONS,
    CLIENT_NONCE, SERVER_NONCE, USERNAME
)
print("4. SHA256(password):")
print("   Proof: %s" % proof4)
print()

# Test 5: password with username prefix (user:password)
up = "%s:%s" % (USERNAME, PASSWORD)
proof5 = compute_scram_proof(
    up.encode("utf-8"), SALT_B64, ITERATIONS,
    CLIENT_NONCE, SERVER_NONCE, USERNAME
)
print("5. user:password:")
print("   Proof: %s" % proof5)
print()

# Test 6: Just password lowercase
proof6 = compute_scram_proof(
    PASSWORD.lower().encode("utf-8"), SALT_B64, ITERATIONS,
    CLIENT_NONCE, SERVER_NONCE, USERNAME
)
print("6. Lowercase password:")
print("   Proof: %s" % proof6)
print()

# Test 7: PBKDF2 with SHA-1 instead of SHA-256 (bug possibility)
def hi_sha1(password_bytes, salt, iterations):
    return hashlib.pbkdf2_hmac("sha1", password_bytes, salt, iterations, dklen=32)

salted_pw_sha1 = hi_sha1(PASSWORD.encode("utf-8"), base64.b64decode(SALT_B64), ITERATIONS)
client_key_7 = hmac.new(salted_pw_sha1, b"Client Key", hashlib.sha256).digest()
stored_key_7 = hashlib.sha256(client_key_7).digest()
c1b = "n=%s,r=%s" % (USERNAME, CLIENT_NONCE)
s1 = "r=%s,s=%s,i=%d" % (SERVER_NONCE, SALT_B64, ITERATIONS)
cfnp = "c=biws,r=%s" % SERVER_NONCE
am = "%s,%s,%s" % (c1b, s1, cfnp)
cs7 = hmac.new(stored_key_7, am.encode("utf-8"), hashlib.sha256).digest()
cp7 = bytes(a ^ b for a, b in zip(client_key_7, cs7))
proof7 = base64.b64encode(cp7).decode("ascii")
print("7. Hi=PBKDF2-SHA1 but HMAC=SHA256:")
print("   Proof: %s" % proof7)
print()

print("=== pymongo sent: %s ===" % PYMONGO_PROOF)
print("\nIf test 1 matches pymongo and the server rejects it,")
print("CosmosDB is using a non-standard password preprocessing.")

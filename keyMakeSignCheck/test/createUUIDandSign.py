import base64
import json
from uuid import uuid4
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import Encoding, KeySerializationEncryption, PrivateFormat, PublicFormat, load_pem_private_key, load_pem_public_key

with open('keys.json', 'r') as file:
	keyStrings = json.loads(file.read())

public_bytes = base64.urlsafe_b64decode(keyStrings['public'])
public_key = load_pem_public_key(public_bytes)
private_bytes = base64.urlsafe_b64decode(keyStrings['private'])
private_key = load_pem_private_key(private_bytes, None)

newUUID = str(uuid4())

# SIGN DATA/STRING
signature = private_key.sign(
	data=newUUID.encode('utf-8'),
	padding=padding.PSS(
		mgf=padding.MGF1(hashes.SHA256()),
		salt_length=padding.PSS.MAX_LENGTH
	),
	algorithm=hashes.SHA256()
)
print("UUID:", newUUID)
print("Signature:", base64.urlsafe_b64encode(signature).decode('ASCII'))
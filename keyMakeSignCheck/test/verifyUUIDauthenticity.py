import base64
import json
import time
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.serialization import Encoding, KeySerializationEncryption, PrivateFormat, PublicFormat, load_pem_private_key, load_pem_public_key

with open('keys.json', 'r') as file:
	keyStrings = json.loads(file.read())

public_bytes = base64.urlsafe_b64decode(keyStrings['public'])
public_key = load_pem_public_key(public_bytes)
private_bytes = base64.urlsafe_b64decode(keyStrings['private'])
private_key = load_pem_private_key(private_bytes, None)

plain_text = input('UUID> ')
signature_string = input('Signature> ')
TEST_TIMES = 100000
tic = time.perf_counter()
for i in range(TEST_TIMES):
	signature = base64.urlsafe_b64decode(signature_string)
	try:
		public_key.verify(
			signature=signature,
			data=plain_text.encode('utf-8'),
			padding=padding.PSS(
				mgf=padding.MGF1(hashes.SHA256()),
				salt_length=padding.PSS.MAX_LENGTH
			),
			algorithm=hashes.SHA256()
		)
		is_signature_correct = True
	except InvalidSignature:
		is_signature_correct = False
toc = time.perf_counter()
print("Authenticity:", is_signature_correct)
print(f"Time to complete {TEST_TIMES} tests: {toc-tic}")
print(f"Rate: {1/((toc-tic)/TEST_TIMES)} tests per second")

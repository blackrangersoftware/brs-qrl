import hashlib
import hmac

# sample entropy from OS for true random numbers such as seeds and private keys
from binascii import hexlify

from os import urandom

from qrl.core import logger


def random_key(n=32):  # returns a 256 bit hex encoded (64 bytes) random number
    return hexlify(urandom(n))


def SEED(n=48):  # returns a n-byte binary random string
    return urandom(n)


def GEN(SEED, i, l=32):  # generates l: 256 bit PRF hexadecimal string at position i. Takes >= 48 byte SEED..
    # FIXME: There is no check for the seed size
    if i < 1:
        logger.info('i must be integer greater than 0')
        return
    z = HMAC_DRBG(SEED)
    for x in range(i):
        y = z.generate(l)
    return y


def GEN_range(SEED, start_i, end_i, l=32):  # returns start -> end iteration of hex PRF (inclusive at both ends)
    if start_i < 1:
        logger.info('starting i must be integer greater than 0')
        return
    z = HMAC_DRBG(SEED)
    random_arr = []
    for x in range(1, end_i + 1):
        y = hexlify(z.generate(l))
        if x >= start_i:
            random_arr.append(y)
    return random_arr


def GEN_range_bin(SEED, start_i, end_i, l=32):  # returns start -> end iteration of bin PRF (inclusive at both ends)
    # FIXME: code repetition
    if start_i < 1:
        logger.info('starting i must be integer greater than 0')
        return
    z = HMAC_DRBG(SEED)
    random_arr = []
    for x in range(1, end_i + 1):
        y = z.generate(l)
        if x >= start_i:
            random_arr.append(y)
    return random_arr


def new_keys(seed=None, n=9999):
    """
    four digit pin to separate the public and private by n iterations of PRF (n=9999 0.38s)
    :param seed:
    :param n:
    :return:
    """
    if not seed:
        seed = SEED(48)
    private_SEED = GEN(seed, 1, l=48)
    public_SEED = GEN(seed, n, l=48)
    return seed, public_SEED, private_SEED


class HMAC_DRBG:
    """
    pseudo random function generator (PRF) utilising hash-based message authentication
    code deterministic random bit generation (HMAC_DRBG)
    k, v = key and value..
    """

    def __init__(self, entropy, personalisation_string="",
                 security_strength=256):  # entropy should be 1.5X length of strength..384 bits / 48 bytes
        self.security_strength = security_strength
        self.instantiate(entropy, personalisation_string)

    def hmac(self, key, data):
        return hmac.new(key, data, hashlib.sha256).digest()

    def generate(self, num_bytes, requested_security_strength=256):
        if (num_bytes * 8) > 7500:
            raise RuntimeError("generate cannot generate more than 7500 bits in a single call.")

        if requested_security_strength > self.security_strength:
            raise RuntimeError(
                "requested_security_strength exceeds this instance's security_strength (%d)" % self.security_strength)

        # if self.reseed_counter >= 10001:
        # if self.reseed_counter >= 20001:
        # FIXME: Check the correct value
        if self.reseed_counter >= 80001:
            return None

        temp = b""

        while len(temp) < num_bytes:
            self.V = self.hmac(self.K, self.V)
            temp += self.V

        self.update(None)
        self.reseed_counter += 1

        return temp[:num_bytes]

    def reseed(self):
        self.update(entropy)
        self.reseed_counter = 1
        return

    def instantiate(self, entropy, personalisation_string=""):
        seed_material = entropy + personalisation_string

        self.K = b"\x00" * 32
        self.V = b"\x01" * 32

        self.update(seed_material)
        self.reseed_counter = 1
        return

    def update(self, seed_material=None):
        self.K = self.hmac(self.K, self.V + b"\x00" + (b"" if seed_material is None else seed_material))
        self.V = self.hmac(self.K, self.V)

        if seed_material is not None:
            self.K = self.hmac(self.K, self.V + b"\x01" + seed_material)
            self.V = self.hmac(self.K, self.V)

        return

        # PRF overlay functions

import numpy as np
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from dataclasses import dataclass,field
import logging
import random
from typing import Tuple, List


logger = logging.getLogger("loger")


@dataclass
class RSA:
    '''Base class for CBC and ECB encryption with RSA algorithm'''
    public_key: bytes = None
    private_key: bytes = None
    _encrypted: np.array = None
    _padding: bytes = None
    _original: np.array = None
    added_bytes: int = None
    encrypt_max_block_size: int = 255
    decrypt_max_block_size: int = 256
    image_shape: tuple = field(default_factory=tuple)


    def __post_init__(self) -> None:
        """
        Generate RSA key-pairs upon initialization.
        """
        logger.info("Generating RSA key-pairs..")
        try:
            p = self.generate_large_prime()
            q = self.generate_large_prime()
            n = p * q
            phi_n = (p - 1) * (q - 1)
            e = self.find_coprime(phi_n)
            d = self.mod_inverse(e, phi_n)
            self.public_key = (e, n)
            self.private_key = (d, n)
        except Exception as e:
            logger.error(f"Error generating RSA key-pairs: {e}")

    def generate_large_prime(self, bits=1024) -> int:
        while True:
            num = random.getrandbits(bits)
            if self.is_prime(num):
                return num

    def is_prime(self, n: int, k=128) -> bool:
        """ Miller-Rabin primality test """
        if n == 2 or n == 3:
            return True
        if n <= 1 or n % 2 == 0:
            return False
        s = 0
        r = n - 1
        while r & 1 == 0:
            s += 1
            r //= 2
        for _ in range(k):
            a = random.randrange(2, n - 1)
            x = pow(a, r, n)
            if x != 1 and x != n - 1:
                j = 1
                while j < s and x != n - 1:
                    x = pow(x, 2, n)
                    if x == 1:
                        return False
                    j += 1
                if x != n - 1:
                    return False
        return True

    def find_coprime(self, phi_n: int) -> int:
        while True:
            e = random.randrange(2, phi_n)
            if self.gcd(e, phi_n) == 1:
                return e

    def gcd(self, a: int, b: int) -> int:
        while b != 0:
            a, b = b, a % b
        return a

    def mod_inverse(self, a: int, m: int) -> int:
        m0, x0, x1 = m, 0, 1
        if m == 1:
            return 0
        while a > 1:
            q = a // m
            m, a = a % m, m
            x0, x1 = x1 - q * x0, x0
        if x1 < 0:
            x1 += m0
        return x1

    def get_public_key_bytes(self):
        """
        Convert RSA public key to bytes.
        """
        try:
            e, n = self.public_key
            e_bytes = e.to_bytes((e.bit_length() + 7) // 8, byteorder='big')
            n_bytes = n.to_bytes((n.bit_length() + 7) // 8, byteorder='big')
            public_key_bytes = e_bytes + n_bytes
            return public_key_bytes
        except Exception as e:
            logger.error(f"Error during conversion RSA public-key to bytes: {e}")
            return None
        
    def get_public_key_cryptography(self):
        """
        Convert public key to `cryptography` RSA public key.
        """
        try:
            e, n = self.public_key
            public_numbers = rsa.RSAPublicNumbers(e, n)
            public_key = public_numbers.public_key()
            return public_key
        except Exception as e:
            logger.error(f"Error converting public key to cryptography format: {e}")
            return None
        
    def get_private_key_cryptography(self):
        """
        Convert private key to `cryptography` RSA private key.
        """
        try:
            d, n = self.private_key
            e, _ = self.public_key
            public_numbers = rsa.RSAPublicNumbers(e, n)
            private_numbers = rsa.RSAPrivateNumbers(
                p=1,  # Placeholder, actual values needed for full private key
                q=1,  # Placeholder, actual values needed for full private key
                d=d,
                dmp1=1,  # Placeholder
                dmq1=1,  # Placeholder
                iqmp=1,  # Placeholder
                public_numbers=public_numbers
            )
            private_key = private_numbers.private_key()
            return private_key
        except Exception as e:
            logger.error(f"Error converting private key to cryptography format: {e}")
            return None


    def split_data(self,full_data: np.array, length_of_data_block: int = None) -> np.array:
        '''
        Spliting image data to blocks with size of public RSA key.
        
        Args:
            *full_data -> np.array: whole image IDAT data after decompression and defiltration

        Return:
            *data_blocks -> np.array : data splited into blocks of size which equals length of RSA public keys (bytes)
        '''
        try:
            if length_of_data_block is None:
                number_of_bytes = len(self.get_public_key_bytes())
            else:
                number_of_bytes = length_of_data_block
            logger.info("Performing IDAT Data splitting")

            #we take the original shape and create 1D vector with data
            full_data = np.reshape(full_data,-1)
            idx = 0
            data_blocks = []

            while idx < len(full_data):
                #iterate over the data and split them into blocks
                if idx + number_of_bytes <= len(full_data):    
                    data_blocks.append(full_data[idx:idx+number_of_bytes])
                    idx += number_of_bytes
                else:
                    #if we cannot get full block of data at the end we perform padding and add extra bytes to create full block
                    diff = len(full_data) - idx
                    last_data_bytes = full_data[idx:idx+diff]
                    self.added_bytes = number_of_bytes - diff
                    added_bytes_list = [0 for iter in range(self.added_bytes)]
                    list_sum = np.concatenate((last_data_bytes,added_bytes_list),axis=0)
                    data_blocks.append(list_sum)
                    idx += diff
            logger.info("Data succesfully splitted")
            return np.array(data_blocks,dtype=np.uint8)
        except Exception as e:
            logger.error(f"Error - splitting data: {e}")
            return None, None

@dataclass
class ECB(RSA):
    added_bytes: int = None

    def __post_init__(self) -> None:
        '''
        Generate RSA key-pairs with super function.
        '''
        return super().__post_init__()
    
    def encrypt(self,image_raw_data:np.array) -> Tuple(np.array, List, List):
        '''
        ECB encryption algoritm splits data into blocks of size 255 bytes. Each block is encrypted by RSA private key and as result we get block of 256 bytes.
        We take 255 bytes to keep original shape and remaining bytes are stored in auxiliary variable "padded"


        Args:
            * image_raw_data -> np.array: original image data after decompression and filtering out.
        Return:
            * encrypted -> np.array: array containing encrypted data with original image shape
            * padded -> List: array containing remaing encrypted bytes which are needed to decrypt image
            * int_table ->List: array containing all encrypted image data in int types
        '''
        logger.info("Starting ECB encryption...")
        try:
            e, n = self.public_key
            data_splitted_blocks = self.split_data(image_raw_data,self.encrypt_max_block_size)
            if image_raw_data.ndim != 3:
                length = image_raw_data.shape[0]
            else:
                length = self.image_shape[0] * self.image_shape[1] * self.image_shape[2]
            encrypted_data = bytearray()
            for i in range(len(data_splitted_blocks)):
                data = data_splitted_blocks[i].tobytes()
                integer = int.from_bytes(data,'big')
                decrypted_integer = pow(integer, e, n)
                encrypted_data.extend(decrypted_integer.to_bytes(self.decrypt_max_block_size,'big'))
            int_table = np.frombuffer(encrypted_data,dtype=np.uint8)
            encrypted = int_table[:length]
            padded = int_table[length:]
            return np.array(encrypted).reshape(self.image_shape),padded,int_table
        except Exception as e:
            logger.error(f"ECB encryption failed: {e}")

        
    def decrypt(self,encrypted:np.array):    
        '''
        ECB decryption algorithm works the same as encryption mechanism but it makes use of RSA public key to decode data. Block of data also conatins 256 bytes.
        It is needed to get 255 bytes which is reverse to encryption mechanism.

        Args:
            * encrypted -> np.array: image data after encryption with ECB algorithm
        Return:
            * image_original_data -> np.array: original image data after decryption
        '''
        logger.info("Startin ECB decryption...")
        try:
            d, n = self.private_key
            data_splitted_blocks= self.split_data(encrypted,self.decrypt_max_block_size)
            original_data = bytearray()
            for i in range(len(data_splitted_blocks)):
                data = data_splitted_blocks[i].tobytes()
                integer = int.from_bytes(data,'big')
                decrypted_integer = pow(integer, d, n)
                original_data.extend(decrypted_integer.to_bytes(self.encrypt_max_block_size,'big'))
            int_table = np.frombuffer(original_data,dtype=np.uint8)
            original = int_table[:-self.added_bytes]
            image_original_data = original.reshape(self.image_shape)
            return image_original_data
        except Exception as e:
            logger.error(f"ECB decryption failed: {e}")

    
    def encrypt_with_library(self, image_raw_data: np.array) -> Tuple():
        """
        Encrypt data using RSA keys and `cryptography` library.

        Args:
            *image_raw_data -> np.array: whole image IDAT data after decompression and defiltration

        Return:
            * arr -> List: array with encrypted image data
            * shape -> Tuple: shape of original image
        """
        height, width, bpp = self.image_shape
        data = image_raw_data.tobytes()
        chunk_size = 190  # This allows room for padding

        public_key = self.get_public_key_cryptography()
        if public_key is None:
            raise ValueError("Public key not available for encryption")

        encrypted_data = bytearray()
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            encrypted_chunk = public_key.encrypt(
                chunk,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            encrypted_data.extend(encrypted_chunk)
        
        bytes_data = bytes(encrypted_data)
        int_data = np.frombuffer(bytes_data, dtype=np.uint8)
        total_pixels = len(int_data) // bpp

        new_height = int(np.sqrt(total_pixels))
        new_width = new_height
        size = new_height * new_width * bpp
        final_data = int_data[:size]

        
        shape = (new_height, new_width, bpp)
        arr = final_data.reshape(shape)
        return arr, shape



class CBC(RSA):
    iv: np.array = None

    def __post_init__(self) -> None:
        """
        Generate RSA key-pairs with super function.
        """
        self.base_iv = iv = np.random.randint(0,256,self.encrypt_max_block_size,dtype=np.uint8) 
        return super().__post_init__()
    
    def encrypt(self,image_raw_data:np.array):
        '''
        CBC encryption algoritm splits data into blocks of size 255 bytes. 
        CBC algorithm uses addidional Vector (which at first is generated but later previous encoded block of data is used).
        Fistly we encode block of data with Vector by XOR operation between them. Then this encoded block is futher encrypted with RSA private key as in ECB.
        As result we get block of 256 bytes.
        We take 255 bytes to keep original shape and remaining bytes are stored in auxiliary variable "padded"

        Args:
            * image_raw_data -> np.array: original image data after decompression and filtering out.
        Return:
            * encrypted -> np.array: array containing encrypted data with original image shape
            * padded -> List: array containing remaing encrypted bytes which are needed to decrypt image
            * int_table ->List: array containing all encrypted image data in int types
        '''
        logger.info("Starting CBC encryption...")
        try:
            e, n = self.public_key
            data_splitted_blocks,shape = self.split_data(image_raw_data,self.encrypt_max_block_size)
            length = shape[0] * shape[1] * shape[2]
            encrypted_data = bytearray()
            iv = self.base_iv
            for i in range(len(data_splitted_blocks)):
                XORed_data = np.array([a^b for a,b in zip(data_splitted_blocks[i],iv)])
                data = XORed_data.tobytes()
                integer = int.from_bytes(data,'big')
                encrypted_integer = pow(integer, e, n)
                encrypted_bytes = encrypted_integer.to_bytes(256,'big')
                encrypted_data.extend(encrypted_bytes)
                iv = np.frombuffer(encrypted_bytes[:self.encrypt_max_block_size],dtype=np.uint8)
            int_table = np.frombuffer(encrypted_data,dtype=np.uint8)
            encrypted = int_table[:length]
            padded = int_table[length:]
            return np.array(encrypted).reshape(shape),padded,int_table
        except Exception as e:
            logger.error(f"CBC encryption failed: {e}")


    def decrypt(self, encrypted:np.array):
        '''
        CBC decryption algorithm uses reverse operations in comparistion to encryption mechanism. It makes use of RSA public key to decode data.
        Block of data contains 256 bytes.
        It is needed to get 255 bytes which is reverse to encryption mechanism.

        Args:
            * encrypted -> np.array: image data after encryption with ECB algorithm
        Return:
            * image_original_data -> np.array: original image data after decryption
        '''
        logger.info("Startin CBC decryption...")
        try:
            d, n = self.private_key
            data_splitted_blocks, shape = self.split_data(encrypted,self.decrypt_max_block_size)
            original_data = bytearray()
            iv = self.base_iv
            for i in range(len(data_splitted_blocks)):
                data = data_splitted_blocks[i].tobytes()
                integer = int.from_bytes(data,'big')
                decrypted_integer = pow(integer, d, n)
                bytes_after_rsa = decrypted_integer.to_bytes(self.encrypt_max_block_size,'big')
                int_data = np.frombuffer(bytes_after_rsa,dtype=np.uint8)
                decrypted = [a^b for a,b in zip(int_data,iv)]
                original_data.extend(decrypted)
                iv = np.frombuffer(data, dtype=np.uint8)
            int_table = np.frombuffer(original_data,dtype=np.uint8)
            original = int_table[:-self.added_bytes]
            image_original_data = original.reshape((self.image_shape))
            return image_original_data
        except Exception as e:
            logger.error(f"ECB decryption failed: {e}")

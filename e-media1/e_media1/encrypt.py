import numpy as np
import os
from typing import List
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import sys
import matplotlib.pyplot as plt
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from dataclasses import dataclass
import logging
import random

import math
import sympy

logger = logging.getLogger("loger")


@dataclass
class RSA:
    public_key: bytes = None
    private_key: bytes = None
    _encrypted: np.array = None
    _padding: bytes = None
    _original: np.array = None
    added_bytes: int = None

   # def __post_init__(self) -> None:
    #     """
    #     Generate RSA key-pairs upon initialization.
    #     """
    #     logger.info("Generating RSA key-pairs..")
    #     try:
    #         self.private_key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    #         self.public_key = self.private_key.public_key()
    #     except Exception as e:
    #         logger.error(f"Error generating RSA key-pairs: {e}")
    #     """
    #     Possible alternative:
    #     """
    #     # try:
    #     #     # Generate RSA key pair
    #     #     self.private_key, self.public_key = rsa.newkeys(2048)
    #     # except rsa.pkcs1.CryptoError as e:
    #     #     logger.error(f"Error generating RSA key-pairs: {e}")


    # def get_public_key_bytes(self):
    #     """
    #     Convert RSA public key to bytes.
    #     """
    #     try:
    #         public_key_bytes = self.public_key.public_bytes(
    #             encoding=serialization.Encoding.DER,  # Format DER
    #             format=serialization.PublicFormat.SubjectPublicKeyInfo
    #         )
    #         return public_key_bytes
    #     except Exception as e:
    #         logger.error(f"Error during conversion RSA public-key to bytes")
    #         return None

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
        

    def encrypt(self,image_raw_data:np.array):
        logger.info("! Starting RSA encryption..")
        try:
            e, n = self.public_key
            max_block_size = 255
            data_splitted_blocks,shape = self.split_data(image_raw_data,max_block_size)
            length = shape[0] * shape[1] * shape[2]
            encrypted_data = bytearray()
            for i in range(len(data_splitted_blocks)):
                data = data_splitted_blocks[i].tobytes()
                integer = int.from_bytes(data,'big')
                decrypted_integer = pow(integer, e, n)
                encrypted_data.extend(decrypted_integer.to_bytes(256,'big'))
            int_table = np.frombuffer(encrypted_data,dtype=np.uint8)
            encrypted = int_table[:length]
            padded = int_table[length:]
            return np.array(encrypted).reshape(shape),padded,int_table
        except Exception as e:
            logger.error(f"RSA encryption failed: {e}")
                
    def decrypt(self,encrypted:np.array,_shape):    
        logger.info("! Startin RSA decryption..")
        try:
            d, n = self.private_key
            max_block_size = 256
            data_splitted_blocks, shape = self.split_data(encrypted,max_block_size)
            original_data = bytearray()
            for i in range(len(data_splitted_blocks)):
                data = data_splitted_blocks[i].tobytes()
                integer = int.from_bytes(data,'big')
                decrypted_integer = pow(integer, d, n)
                original_data.extend(decrypted_integer.to_bytes(255,'big'))
            int_table = np.frombuffer(original_data,dtype=np.uint8)
            original = int_table[:-self.added_bytes]
            res = original.reshape((_shape))
            return res
        except Exception as e:
            logger.error(f"RSA decryption failed: {e}")


    def encrypt_with_library(self, image_raw_data: np.array) -> bytes:
        """
        Encrypt data using `cryptography` library.
        """
        height, width, bpp = image_raw_data.shape
        data = image_raw_data.tobytes()
        length = len(data)
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
            shape_tuple = full_data.shape
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
            return np.array(data_blocks,dtype=np.uint8),shape_tuple
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


    def encrypt_and_decrypt_algorithm(self, full_data:np.array) -> np.array:
        '''
        Performing ECB encryption with XOR operation between correspoding bytes in key and data
        XOR function allows us to perform encryption and decryption with the same method :)

        Args:
            * full_data -> np.array: whole image IDAT data after decompression and defiltration
        Return:
            * data_after_operation -> np.array: data encrypted and reshaped to original image shape
        '''
        try:
            public_key_bytes = self.get_public_key_bytes()


            data,shape = self.split_data(full_data)
            data_after_operation = []
            # for every byte in data block we perform XOR operation with corresponding byte in key.
            for block in data:
                for iter in range(len(block)):
                    data_after_operation.append(block[iter] ^ public_key_bytes[iter])
            # if we have additional encrypted data we get rid of it for now - we dont need it to recreate image
            if self.added_bytes is not None:
                data_after_operation = data_after_operation[:-self.added_bytes]
            data_after_operation = np.reshape(data_after_operation,shape)

            return data_after_operation
        except Exception as e:
            logger.error(f"Error - ECB encryption/decryption: {e}")
            return None
    
    def encrypt(self,original_data:np.array) -> np.array:
        '''
        Encryption with ECB
        '''
        logger.info("Starting encryption with ECB algorithm")
        self._encrypted = self.encrypt_and_decrypt_algorithm(original_data)
        logger.info("Encryption with ECB algorithm successful")
        return self._encrypted

    def decrypt(self) -> np.array:
        '''
        Decryption with ECB
        '''
        logger.info("Starting decryption with ECB algorithm")
        self._original = self.encrypt_and_decrypt_algorithm(self._encrypted)
        logger.info("Decryption with ECB algorithm successful")
        return self._original
    
    def encrypt_compressed(self, compressed_data:np.array):
        logger.info("Starting encryption on compressed IDAT data with ECB algorithm")
        try:
            public_key_bytes = self.get_public_key_bytes()

            splitted_data, shape = self.split_data(compressed_data)
            data_after_operation = []
            # for every byte in data block we perform XOR operation with corresponding byte in key.
            for block in splitted_data:
                for iter in range(len(block)):
                    data_after_operation.append(block[iter] ^ public_key_bytes[iter])
                    # print(data_after_operation)
            # if we have additional encrypted data we get rid of it for now - we dont need it to recreate image
            if self.added_bytes is not None:
                data_after_operation = data_after_operation[:-self.added_bytes]
            self._encrypted = np.array(data_after_operation,dtype=np.uint8)
            logger.info("Encryption on compressed IDAT data with ECB algorithm successful")
            return self._encrypted
        except Exception as e:
            logger.error(f"Error - ECB encryption/decryption: {e}")
            return None



class CBC(RSA):
    added_bytes: int = None


    def __post_init__(self) -> None:
        """
        Generate RSA key-pairs with super function.
        """
        return super().__post_init__()
    

    def encrypt(self, full_data: np.array) -> np.array:
        '''
        Encrypt data with CBC algorithm which uses previous encrypted data to encrypt next block

        Args:
            * full_data -> np.array: whole image IDAT data after decompression and defiltration
        Return:
            * _encrypted -> np.array: data encrypted and reshaped to original image shape
        '''
        logger.info("Starting CBC encryption")
        try:
            public_key_bytes = self.get_public_key_bytes()

            data, shape = self.split_data(full_data)
            data_after_operation = []

            previous_block = public_key_bytes
            # Encrypt the first block with the IV
            for block in data:
                # XOR with the previous ciphertext (or key for the first block)
                encrypted_block = [block[iter] ^ previous_block[iter] for iter in range(len(block))]
                data_after_operation.extend(encrypted_block)
                previous_block = encrypted_block

            # If we have additional encrypted data, we get rid of it for now - we don't need it to recreate the image
            if self.added_bytes is not None:
                data_after_operation = data_after_operation[:-self.added_bytes]

            self._encrypted = np.reshape(data_after_operation, shape)

            return self._encrypted
        except Exception as e:
            logger.error(f"Error - CBC encryption: {e}")
            return None
        

    def decrypt(self):
        logger.info("Starting CBC decryption")
        try:
            public_key_bytes = self.get_public_key_bytes()
            data, shape = self.split_data(self._encrypted)
            data_after_operation = []


            previous_block = public_key_bytes

            # Decrypt each block
            for block in data:
                # Decrypt the block by reversing the XOR operation with the key
                decrypted_block = [block[iter] ^ previous_block[iter] for iter in range(len(block))]  # This reverts the XOR with key
                # XOR with the previous ciphertext (or key for the first block)
                data_after_operation.extend(decrypted_block)
                previous_block = block

            # Remove padding if added during encryption
            if self.added_bytes is not None:
                data_after_operation = data_after_operation[:-self.added_bytes]

            data_after_operation = np.reshape(data_after_operation, shape)
            return data_after_operation
        except Exception as e:
            logger.error(f"Error - CBC decryption: {e}")
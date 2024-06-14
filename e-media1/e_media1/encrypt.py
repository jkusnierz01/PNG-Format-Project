from dataclasses import dataclass
import numpy as np
import os
from typing import List
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import sys
import matplotlib.pyplot as plt
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import logging
import png

logger = logging.getLogger("loger")


@dataclass
class RSA:
    public_key: bytes = None
    private_key: bytes = None
    _encrypted: np.array = None
    _original: np.array = None
    added_bytes: int = None

    def __post_init__(self) -> None:
        """
        Generate RSA key-pairs upon initialization.
        """
        logger.info("Generating RSA key-pairs..")
        try:
            self.private_key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
            self.public_key = self.private_key.public_key()
        except Exception as e:
            logger.error(f"Error generating RSA key-pairs: {e}")
        """
        Possible alternative:
        """
        # try:
        #     # Generate RSA key pair
        #     self.private_key, self.public_key = rsa.newkeys(2048)
        # except rsa.pkcs1.CryptoError as e:
        #     logger.error(f"Error generating RSA key-pairs: {e}")


    def get_public_key_bytes(self):
        """
        Convert RSA public key to bytes.
        """
        try:
            public_key_bytes = self.public_key.public_bytes(
                encoding=serialization.Encoding.DER,  # Format DER
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return public_key_bytes
        except Exception as e:
            logger.error(f"Error during conversion RSA public-key to bytes")
            return None


    #NIE DZIAŁA JESZCZE
    # def encrypt_test(self,raw_original_data:np.array):
    #     """
    #     Encrypt image data with RSA

    #     Args:
    #         *raw_original_data -> whole image IDAT data after decompression and defiltration

    #     Returns:
    #         *encrypted -> encrypted image data
    #     """

    #     original_shape = raw_original_data.shape
    #     # data = raw_original_data.tobytes()
    #     # encrypted_data = self.encrypt(data)
    #     encrypted_data = self.encrypt(raw_original_data)

    #     encrypted_array = np.frombuffer(encrypted_data, dtype='uint8')
    #     self._encrypted = np.reshape(encrypted_array, original_shape)

    #     # Display encrypted data as a byte stream (not reshaping to original shape)
    #     # encrypted_array = np.frombuffer(encrypted_data, dtype='uint8')

    #     # This is just to demonstrate the encrypted byte stream visually
    #     # plt.figure(figsize=(10, 2))
    #     # plt.plot(encrypted_data, marker='o', linestyle='None')
    #     # plt.title("Encrypted Data Byte Stream")
    #     # logger.info("plotting...")
    #     # plt.show()

    #     plt.imshow(self._encrypted, cmap='gray')  # Use 'cmap' parameter if the image is grayscale
    #     plt.title("Encrypted Image")
    #     plt.axis('off')  # Hide axis
    #     plt.show()


    # def encrypt(self, original_data: np.array):
    #     logger.info("Encrypting with RSA")
    #     print(original_data.shape)
    #     max_chunk_size = 190
    #     data,shape = self.split_data(original_data,max_chunk_size)
    #     length = (shape[0] * shape[1] * shape[2])
    #     bytes_data = data.tobytes()
    #     print(len(bytes_data))
    #     out_bytes = []
    #     for i in range(data.shape[0]):
    #         chunk = bytes_data[i:i+max_chunk_size]
    #         # logger.info(f"Encrypting block {i}")
    #         encrypted_chunk = self.public_key.encrypt(
    #             chunk,
    #             padding.OAEP(
    #                 mgf=padding.MGF1(algorithm=hashes.SHA256()),
    #                 algorithm=hashes.SHA256(),
    #                 label=None
    #             )
    #         )
    #         out_bytes.append(encrypted_chunk)
    #     s = b''.join(out_bytes)
    #     out_int = []
    #     for i in range(len(s)):
    #         out_int.append(s[i])
    #     encrypted = out_int[:length]
    #     excesive = np.array(out_int[length:]).tobytes()
    #     d = np.array(encrypted).reshape(shape)
    #     return d,excesive


    # def decrypt(self, encrypted_data: np.array, excesive_data: bytes):
    #     logger.info("Decrypting with RSA")
    #     encrypted_chunk_size = self.private_key.key_size // 8  # Rozmiar w bajtach klucza RSA (256 bajtów dla klucza 2048-bitowego)
    #     bytes_data = encrypted_data.tobytes() + excesive_data

    #     decrypted_chunks = []
    #     for i in range(0, len(bytes_data), encrypted_chunk_size):
    #         chunk = bytes_data[i:i + encrypted_chunk_size]
    #         if len(chunk) != encrypted_chunk_size:
    #             logger.error(f"Invalid chunk size at index {i}")
    #             raise ValueError(f"Invalid chunk size at index {i}")
            
    #         try:
    #             decrypted_chunk = self.private_key.decrypt(
    #                 chunk,
    #                 padding.OAEP(
    #                     mgf=padding.MGF1(algorithm=hashes.SHA256()),
    #                     algorithm=hashes.SHA256(),
    #                     label=None
    #                 )
    #             )
    #             decrypted_chunks.append(decrypted_chunk)
    #         except Exception as e:
    #             logger.error(f"Decryption failed for chunk at index {i}: {e}")
    #             raise ValueError(f"Decryption failed for chunk at index {i}")

    #     decrypted_data = b''.join(decrypted_chunks)
    #     original_data = np.frombuffer(decrypted_data, dtype=np.uint8)
    #     original_shape = (len(original_data) // np.prod(encrypted_data.shape[1:]),) + encrypted_data.shape[1:]
    #     return original_data.reshape(original_shape)


# Zakładając, że mamy self.private_key zdefiniowany w klasie


    # def split_data_2(self, data, max_chunk_size):
    #     # Split data into chunks of max_chunk_size
    #     return [data[i:i + max_chunk_size] for i in range(0, len(data), max_chunk_size)]

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
            return np.array(data_blocks),shape_tuple
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
            logger.error(f"Error - CBC encryption/decryption: {e}")
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
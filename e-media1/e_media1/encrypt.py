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
    def encryption(self,raw_original_data:np.array):
        """
        Encrypt image data with RSA

        Args:
            *raw_original_data -> whole image IDAT data after decompression and defiltration

        Returns:
            *encrypted -> encrypted image data
        """

        original_shape = raw_original_data.shape
        data = raw_original_data.tobytes()
        encrypted_data = self.public_key.encrypt(data, padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None))

        # Display encrypted data as a byte stream (not reshaping to original shape)
        encrypted_array = np.frombuffer(encrypted_data, dtype='uint8')

        # This is just to demonstrate the encrypted byte stream visually
        plt.figure(figsize=(10, 2))
        plt.plot(encrypted_array, marker='o', linestyle='None')
        plt.title("Encrypted Data Byte Stream")
        plt.show()

    

    def split_data(self,full_data: np.array) -> np.array:
        '''
        Spliting image data to blocks with size of public RSA key.
        
        Args:
            *full_data -> np.array: whole image IDAT data after decompression and defiltration

        Return:
            *data_blocks -> np.array : data splited into blocks of size which equals length of RSA public keys (bytes)
        '''
        try:
            number_of_bytes = len(self.get_public_key_bytes())
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
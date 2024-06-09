from dataclasses import dataclass
import numpy as np
import os
from typing import List
from cryptography.hazmat.primitives.asymmetric import rsa
import sys
import matplotlib.pyplot as plt
import logging

logger = logging.getLogger("loger")


@dataclass(init=False)
class RSA:

    def __init__(self) -> None:
        RSA.generateRSAKeys()


    @classmethod
    def generateRSAKeys(cls):
        cls.private_key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
        cls.public_key = cls.private_key.public_key()
        

    

@dataclass
class ECB():
    key: bytes = None
    added_bytes: int = None
    _encrypted: np.array = None
    _original: np.array = None


    def __post_init__(self) -> None:
        self.generatekey()

    def generatekey(self ,number_of_bytes: int = 12):
        logger.info("Generating ECB key")
        self.key = os.urandom(number_of_bytes)

    '''
    Funkcja do dzielenia dane z obrazu na bloki. Deafaultowo 12 bajtowe. Dla obrazu RGB będą to 4 piksele.
        * full_data -> np.array: tablica zawierajaca dane IDAT z obrazu po dekompresji i odfiltrowaniu

    Return:
        * 
    '''
    def split_data(self, full_data: np.array, number_of_bytes: int = 12):
        logger.info("Performing IDAT Data splitting")
        #we take the original shape and create 1D vector with data
        shape_tuple = full_data.shape
        full_data = np.reshape(full_data,-1)

        idx = 0
        data_blocks = []
        missing_bytes = None

        while idx <= len(full_data) - 1:
            #iterate over the data and split them into blocks with lenght = number of bytes
            #if we cannot get full block of data at the end we perform padding and add extra bytes to create full block
            if idx + number_of_bytes <= len(full_data):    
                data_blocks.append(full_data[idx:idx+number_of_bytes])
                idx += number_of_bytes
            else:
                diff = len(full_data) - idx
                last_data_bytes = full_data[idx:idx+diff]
                missing_bytes = number_of_bytes - diff
                self.added_bytes = [0 for iter in range(missing_bytes)]
                list_sum = np.concatenate((last_data_bytes,self.added_bytes),axis=0)
                data_blocks.append(list_sum)
                idx += diff
        logger.info("Data succesfully splitted")
        return np.array(data_blocks),shape_tuple, missing_bytes
        
            


    '''
    Funkcja przeprowadzająca szyfrowanie ECB z wykrzystaniem operacji XOR między bajtami w kluczu i danych.
        * full_data -> np.array: tablica zawierajaca dane IDAT z obrazu po dekompresji i odfiltrowaniu lub dane po zaszyfrowaniu
        Operacja XOR pozwala na to ze odszyfrowywanie odbywa sie ta sama metoda
    '''

    def encrypt_and_decrypt_algorithm(self, full_data:np.array):
        data,shape,nr_of_added_bytes = self.split_data(full_data)
        data_after_operation = []
        # for every byte in data block we perform XOR operation with corresponding byte in key.
        for block in data:
            for iter in range(len(block)):
                data_after_operation.append(block[iter] ^ self.key[iter])
        # if we have additional encrypted data we get rid of it for now - we dont need it to recreate image
        if nr_of_added_bytes is not None:
            data_after_operation = data_after_operation[:-nr_of_added_bytes]
        data_after_operation = np.reshape(data_after_operation,shape)

        #we create encrypted image
        # f = plt.figure()
        # plt.imshow(data_after_operation)
        # plt.axis("off")
        # plt.show()

        return data_after_operation
        
    
    def encrypt(self,original_data):
        logger.info("Starting encryption with ECB algorithm")
        self._encrypted = self.encrypt_and_decrypt_algorithm(original_data)
        logger.info("Encryption with ECB algorithm successful")

    def decrypt(self):
        logger.info("Starting decryption with ECB algorithm")
        self._original = self.encrypt_and_decrypt_algorithm(self._encrypted)
        logger.info("Decryption with ECB algorithm successful")


class CTR:

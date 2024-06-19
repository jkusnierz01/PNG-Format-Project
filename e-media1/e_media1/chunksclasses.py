from dataclasses import dataclass, field
from typing import List
import logging
from e_media1.basechunks import *
import zlib
import logging
from e_media1.filtering_methods import ReconstructingMethods
import numpy as np
from e_media1.encrypt import ECB, CBC, RSA
import png
import os
from pathlib import Path
import sys
from PIL import Image as ImagE
import binascii


logger = logging.getLogger("loger")


@dataclass(init=False)
class CriticalChunks:
    '''
    Klasa przechowujaca dane o chunkach krytycznych
    '''
    IHDR: IHDRChunk
    IEND: IENDChunk
    PLTE: PLTEChunk = None
    IDAT: List[IDATChunk] = field(default_factory=list)

    def __init__(self,chunk_list_data):
        self.IHDR = chunk_list_data.pop(0)
        self.IEND = chunk_list_data.pop(-1)
        if self.IHDR.color == 3:
            self.PLTE = chunk_list_data.pop(0)
        self.IDAT = chunk_list_data

    # function zwracająca tablice IDAT w formie bajtow
    def returnIDAT(self) -> bytes:
        IDAT_data = bytearray()
        for chunk in self.IDAT:
            IDAT_data.extend(chunk.ReturnData())
        return bytes(IDAT_data)
    

    def retrieveAllIDATData(self) -> bytes:
        return b''.join([chunk.Data for chunk in self.IDAT])
    
    def decompressData(self) -> bytes:
        concatinatedData = self.retrieveAllIDATData()
        return zlib.decompress(concatinatedData)
    

    def reconstructIDATData(self) -> np.array:
        height = self.IHDR.height
        width = self.IHDR.width
        decompressed_data = self.decompressData()
        bytes_per_pixel = color_type_bytes.get(self.IHDR.color,None)
        expected_IDAT_data_length = height * (1 + width * bytes_per_pixel)
        if(len(decompressed_data) != expected_IDAT_data_length):
            logger.error(f"Decompressed Data Lenght not correct: {len(decompressed_data)} vs expected: {expected_IDAT_data_length}")
        Reconstructed = []
        i = 0
        if bytes_per_pixel is None:
            logger.error("Wrong Color Type")
        for row in range(height):
            filter_method = decompressed_data[i]
            i +=1
            method = filtering_methods.get(filter_method)
            for col in range(width * bytes_per_pixel):
                x = decompressed_data[i]
                i+=1
                reconstructed = method(x, row, col, Reconstructed, width, bytes_per_pixel)
                Reconstructed.append(reconstructed & 0xff)
        Reconstructed = np.array(Reconstructed,dtype=np.uint8).reshape(height,width,bytes_per_pixel)
        return Reconstructed
    
    def createIDAT(self, encrypted_data: bytes, max_chunk_size: int = 65524) -> List[IDATChunk]:
        chunk_type = b'IDAT'     
        total_length = len(encrypted_data)
        chunks = []
        # Debug: Wypisywanie całej struktury bajtów
        # print(f"Bytes structure length: {total_length}")
        for start in range(0, total_length, max_chunk_size):
            end = start + max_chunk_size
            chunk_data = encrypted_data[start:end]
            length = struct.pack("!I", len(chunk_data))
            crc_data = chunk_type + chunk_data
            new_crc = zlib.crc32(crc_data)
            new_crc = struct.pack('>I', new_crc & 0xffffffff)
            idat_chunk = IDATChunk(length, chunk_type, chunk_data, new_crc)
            chunks.append(idat_chunk)

        return chunks



    


    def __str__(self) -> str:
        if self.PLTE is not None:
            return (f"Critical Chunks: {str(self.IHDR), str(self.PLTE), str(self.IDAT[0]),str(self.IEND)}")
        else:
            return (f"Critical Chunks: {str(self.IHDR), str(self.IDAT[0]),str(self.IEND)}")
        

@dataclass
class AncillaryChunks:
    '''
    Klasa przechowujaca dane o chunkach dodatkowych
    '''
    ChunkList: List[Chunk] = field(default_factory=list)


    def returnChunkData(self) -> bytes:
        chunkData = bytearray()
        for chunk in self.ChunkList:
            chunkData.extend(chunk.ReturnData())
        return bytes(chunkData)
    
    def findChunk(self,_type):
        for chunk in self.ChunkList:
            if chunk.Type == _type:
                return Chunk
        return None
    
    def presentChunkData(self):
        for chunk in self.ChunkList:
            chunk.presentData()
    
    def __str__(self) -> str:
        chunk_types = tuple(map(str,self.ChunkList))
        return(f"Ancillary Chunks: {chunk_types}")
       
    


@dataclass(init=False)
class Image:
    criticalChunks: CriticalChunks
    ancillaryChunks: AncillaryChunks
    rawIDATData: np.array #IDAT after decompression and defiltering | SHAPE(height, width, pixel color depth)
    path_to_save: str

    def __init__(self, image_binary_data, save_path: str):
        CriticalChunkList = []
        AncillaryChunkList = []
        self.path_to_save = save_path

        while image_binary_data:
            try:
                # odczytujemy dane z chunka
                _length = image_binary_data.read(4)
                _type = image_binary_data.read(4)
                _data = image_binary_data.read(int.from_bytes(_length))
                _crc = image_binary_data.read(4)

                # jezeli typu nie ma w slowniku inicjowana jest klasa bazowa
                chunk_class = chunk_bytes_parsing.get(_type,Chunk)
                chunk = chunk_class(_length,_type,_data,_crc)
                #checking if chunk is critical (uppercase:critical | lowercase:ancillary)
                first_byte = _type[0:1]
                letter = first_byte.decode() 
                if letter.isupper():
                    CriticalChunkList.append(chunk)
                else:
                    if chunk.Type in chunk_bytes_parsing.keys():
                        AncillaryChunkList.append(chunk)
            except Exception as e:
                logger.error(f"Error during loading chunk {e}")
                continue
            if chunk.Type == b'IEND':
                break
        
        self.criticalChunks = CriticalChunks(CriticalChunkList)
        self.ancillaryChunks = AncillaryChunks(AncillaryChunkList)
        self.rawIDATData = self.criticalChunks.reconstructIDATData()


    def saveImage(self,path:str, filename:str,data:np.array) -> None:
        '''
        Saving Image with encrypted data

        Args:
            *path -> str: path to folder in which output image will be stored
            *filename -> str: name of output image 
            *data -> np.array: encrypted data
        
        Return:
            *None
        '''
        logger.info(f"Saving output image: {filename}")
        try:
            height,width,color = data.shape
            data_reshaped = data.reshape((height,width * color))
            encrypted_list = data_reshaped.tolist()
            if color == 1:
                grayscale = True
                alpha = False
            elif color == 2:
                grayscale = True
                alpha = True
            elif color == 3:
                grayscale = False
                alpha = False
            else:
                grayscale = False
                alpha = True
            writer = png.Writer(width,height,greyscale=grayscale,alpha=alpha)
            #we check if folder exist, if not we crate directory
            if not os.path.exists(path):
                os.mkdir(path)
            full_path = path + '/' + filename
            Full_path = Path(full_path)
            #saving output image
            with open(Full_path, 'wb') as out_file:
                writer.write(out_file,encrypted_list)
        except Exception as e:
            logger.error(f"Saving output image: {filename}")
        
    

    def encryptECB(self,encrypt_compressed:bool = False, library_func:bool = False) -> None:
        try:
            ecb = ECB(image_shape=self.rawIDATData.shape)
            if encrypt_compressed:
                bytes_IDAT_data = self.criticalChunks.retrieveAllIDATData()
                int_IDAT_data = np.frombuffer(bytes_IDAT_data,dtype=np.uint8)
                encrypted_compressed, padding = ecb.encrypt(int_IDAT_data, True)
                self.save_without_decompression(encrypted_compressed, padding)
            else:
                encrypted, padded, int_t = ecb.encrypt(self.rawIDATData)
                self.saveImage(self.path_to_save, filename='ecb_encrypt.png',data=encrypted)
                decrypted = ecb.decrypt(int_t)
                self.saveImage(self.path_to_save, filename='ecb_decrypt.png',data=decrypted)
            if library_func:
                encrypted,shape = ecb.encrypt_with_library(self.rawIDATData)
                self.saveImage(self.path_to_save, filename='ecb_encrypt_library.png',data=encrypted)
        except Exception as e:
            logger.error(f"Error in encryptECB function: {e}")

    def encryptCBC(self):
        try:
            cbc = CBC()
            encrypted,padded,int_data = cbc.encrypt(self.rawIDATData)
            self.saveImage(self.path_to_save, filename='cbc_encrypt.png', data=encrypted)
            decrypted = cbc.decrypt(int_data)
            self.saveImage(self.path_to_save, filename='cbc_decrypt.png', data=decrypted)
        except Exception as e:
            logger.error(f"Error in encryptCBC function: {e}")


    def restoreImage(self, img_binary_file:bytes, signature:bytes, exclude_ancillary:bool, replace_idat:np.array = None):
        img_binary_file.write(signature)
        img_binary_file.write(self.criticalChunks.IHDR.ReturnData())
        if exclude_ancillary is False:
            img_binary_file.write(self.ancillaryChunks.returnChunkData())
        if self.criticalChunks.PLTE is not None:
            img_binary_file.write(self.criticalChunks.PLTE.ReturnData())
        img_binary_file.write(self.criticalChunks.returnIDAT())
        img_binary_file.write(self.criticalChunks.IEND.ReturnData())
        return img_binary_file
    
    def save_without_decompression(self, encrypted_data: np.array, padding_to_be_save_after_IEND:np.array = None):
        logger.info("Saving encrypted Image data without decompression")
        try:
            signature = b'\x89PNG\r\n\x1a\n'
            with open("../output_images/without_decompression.png",'wb') as output_file:
                output_file.write(signature)
                output_file.write(self.criticalChunks.IHDR.ReturnData())
                if self.criticalChunks.PLTE is not None:
                    output_file.write(self.criticalChunks.PLTE.ReturnData())
                self.criticalChunks.IDAT = self.criticalChunks.createIDAT(encrypted_data)
                output_file.write(self.criticalChunks.returnIDAT())
                output_file.write(self.criticalChunks.IEND.ReturnData())
                if padding_to_be_save_after_IEND is not None:
                    custom_type = b'cnKS'  # Custom chunk type, 4 bytes, must be uppercase
                    custom_data_bytes = padding_to_be_save_after_IEND  # Your custom data
                    custom_length = struct.pack('>I', len(custom_data_bytes))  # Length of the data
                    custom_crc = struct.pack('>I', zlib.crc32(custom_type + custom_data_bytes) & 0xffffffff)  # CRC
                    chunk = Chunk(custom_length,custom_type,custom_data_bytes,custom_crc)
                    output_file.write(chunk.ReturnData())
        except Exception as e:
            logger.error(f"Saving encrypted Image data without decompression FAILED")

            
            

    def displayChunks(self):
        print(str(self.criticalChunks))
        print(str(self.ancillaryChunks))

    def displayImageData(self):
        logger.info("Displaying Image Data")
        self.criticalChunks.IHDR.DecodeData()
        self.ancillaryChunks.presentChunkData()
        self.displayChunks()
        if self.criticalChunks.PLTE is not None:
            self.criticalChunks.PLTE.show_palette()



        


chunk_bytes_parsing = {
    b'IHDR':IHDRChunk,
    b'IEND':IENDChunk,
    b'PLTE':PLTEChunk,
    b'IDAT':IDATChunk,
    b'cHRM':cHRMChunk,
    b'gAMA':gAMAChunk,
    b'eXIf':eXIFChunk,
}


color_type_bytes = {
    0:1,
    2:3,
    3:1,
    4:2,
    6:4
}

filtering_methods = {
    0:ReconstructingMethods.none,
    1:ReconstructingMethods.Sub,
    2:ReconstructingMethods.Up,
    3:ReconstructingMethods.Average,
    4:ReconstructingMethods.Paeth
}
    
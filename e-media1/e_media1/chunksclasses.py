from dataclasses import dataclass, field
from typing import List
import logging
from e_media1.basechunks import *
from e_media1.filtering_methods import ReconstructingMethods
from e_media1.encrypt import ECB, CBC
from e_media1.additional_data import *
import numpy as np
import png
import zlib
import logging
import os
from pathlib import Path


logger = logging.getLogger("loger")


@dataclass(init=False)
class CriticalChunks:
    '''
    Class storing critical chunks of PNG
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
    def return_whole_IDAT(self) -> bytes:
        '''
        Function returning whole IDAT Chunk data (Lenght, Type, Data, CRC) as sequence of bytes 
        '''
        IDAT_data = bytearray()
        for chunk in self.IDAT:
            IDAT_data.extend(chunk.ReturnData())
        return bytes(IDAT_data)
    

    def return_only_IDAT_data(self) -> bytes:
        '''
        Function returning only Data from IDAT Chunk as sequence of bytes
        '''
        return b''.join([chunk.Data for chunk in self.IDAT])
    
    def decompress_IDAT_data(self) -> bytes:
        '''
        Function used to decompress whole IDAT Data which is in sequence of bytes form
        '''
        concatinatedData = self.return_only_IDAT_data()
        return zlib.decompress(concatinatedData)
    

    def reconstruct_IDAT_data(self) -> np.array:
        '''
        Function used to reconstruct IDAT Data from compressed form.
        Data is not only compressed but also filtered so we need to inverse it and filter it out.

        Return:
            *Reconstructed -> List: List storing filtered out data
        '''
        height = self.IHDR.height
        width = self.IHDR.width
        decompressed_data = self.decompress_IDAT_data()
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
            i += 1
            method = filtering_methods.get(filter_method)
            for col in range(width * bytes_per_pixel):
                x = decompressed_data[i]
                i+=1
                reconstructed = method(x, row, col, Reconstructed, width, bytes_per_pixel)
                Reconstructed.append(reconstructed & 0xff)
        Reconstructed = np.array(Reconstructed,dtype=np.uint8).reshape(height,width,bytes_per_pixel)
        return Reconstructed
    
    def create_IDAT_Chunk(self, encrypted_data: bytes, max_chunk_size: int = 65524) -> List[IDATChunk]:
        '''
        Function recreating IDAT data chunk with encrypted data

        Args:
            * encrypted_data -> bytes: Data to be stored in IDAt Chunk (Data after encryption with ECB or CBC algorythm)
            * max_chunk_size -> int = 65524: number of bytes which can be stored in single IDAT Chunk
        Return:
            *Reconstructed -> List: List storing IDAT Chunks
        '''
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
    Class storing data about Ancillary Chunks: cHRM, eXIF, gAMA etc.
    '''
    ChunkList: List[Chunk] = field(default_factory=list)


    def return_chunk_data(self) -> bytes:
        '''
        Function returning whole Chunk data (Lenght, Type, Data, CRC) as sequence of bytes
        '''
        chunkData = bytearray()
        for chunk in self.ChunkList:
            chunkData.extend(chunk.ReturnData())
        return bytes(chunkData)

    
    def present_ancillary_chunk_data(self):
        for chunk in self.ChunkList:
            chunk.presentData()
    
    def __str__(self) -> str:
        chunk_types = tuple(map(str,self.ChunkList))
        return(f"Ancillary Chunks: {chunk_types}")
       
    


@dataclass(init=False)
class Image:
    '''
    Class storing information about all PNG Chunks with additional filtered out IDAT Data
    '''
    criticalChunks: CriticalChunks
    ancillaryChunks: AncillaryChunks
    rawIDATData: np.array
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
        self.rawIDATData = self.criticalChunks.reconstruct_IDAT_data()

    def recreate_png_with_chunks(self, img_binary_file:bytes, exclude_ancillary:bool) -> bytes:
        '''
        Function used to create PNG image with both Critical and Ancillary chunks or only with Critical chunks

        Args:
            *img_binary_file -> bytes: stream of bytes where PNG data will be stored
            *exclude_ancillary -> bool: flag used to determine whether ancillary chunks will be saved or not
        
        Return:
            * img_binary_file -> bytes: stream of bytes where PNG data is stored
        '''
        
        img_binary_file.write(SIGNATURE)
        img_binary_file.write(self.criticalChunks.IHDR.ReturnData())
        if exclude_ancillary is False:
            img_binary_file.write(self.ancillaryChunks.return_chunk_data())
        if self.criticalChunks.PLTE is not None:
            img_binary_file.write(self.criticalChunks.PLTE.ReturnData())
        img_binary_file.write(self.criticalChunks.return_whole_IDAT())
        img_binary_file.write(self.criticalChunks.IEND.ReturnData())
        return img_binary_file



    def saveImage(self,path:str, filename:str,data:np.array) -> None:
        '''
        Saving Image with encrypted data using external library png

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
        
    

    def encrypt_image_using_ecb(self, library_func:bool = False) -> None:
        '''
        Encrypt image data with ECB algorithm

        Args:
            *encrypt_compressed -> bool = False: If True compressed IDAT data is encrypted (we skip process of filtering out the data)
            *library_func -> bool = False: If True we use external library function to perform encryption (crypthography library)
        
        Return:
            *None
        '''
        try:
            ecb = ECB(image_shape=self.rawIDATData.shape)
            encrypted, _, int_t = ecb.encrypt(self.rawIDATData)
            self.saveImage(self.path_to_save, filename='ecb_encrypt.png',data=encrypted)
            decrypted = ecb.decrypt(int_t)
            self.saveImage(self.path_to_save, filename='ecb_decrypt.png',data=decrypted)
            if library_func:
                encrypted,shape = ecb.encrypt_with_library(self.rawIDATData)
                self.saveImage(self.path_to_save, filename='ecb_encrypt_library.png',data=encrypted)
        except Exception as e:
            logger.error(f"Error in encrypt_image_using_ecb function: {e}")

    def encrypt_image_using_cbc(self):
        '''
        Encrypt image data with CBC algorithm

        Args:
            *None
        
        Return:
            *None
        '''
        try:
            cbc = CBC()
            encrypted,_,int_data = cbc.encrypt(self.rawIDATData)
            self.saveImage(self.path_to_save, filename='cbc_encrypt.png', data=encrypted)
            decrypted = cbc.decrypt(int_data)
            self.saveImage(self.path_to_save, filename='cbc_decrypt.png', data=decrypted)
        except Exception as e:
            logger.error(f"Error in encrypt_image_using_cbc function: {e}")


    def displayChunks(self):
        '''Function used for printing content of Critical and Ancillary chunk classes'''
        print(str(self.criticalChunks))
        print(str(self.ancillaryChunks))

    def displayImageData(self):
        '''Function used for printing content of chunks present in PNG image'''
        logger.info("Displaying Image Data")
        self.criticalChunks.IHDR.DecodeData()
        self.ancillaryChunks.present_ancillary_chunk_data()
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


filtering_methods = {
    0:ReconstructingMethods.none,
    1:ReconstructingMethods.Sub,
    2:ReconstructingMethods.Up,
    3:ReconstructingMethods.Average,
    4:ReconstructingMethods.Paeth
}
    
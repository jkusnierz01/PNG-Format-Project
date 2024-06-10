from dataclasses import dataclass, field
from typing import List
import logging
from tabulate import tabulate
from e_media1.basechunks import *
import zlib
import logging
from e_media1.filtering_methods import ReconstructingMethods
import numpy as np
import sys
import matplotlib.pyplot as plt
from e_media1.encrypt import ECB


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
            logger.error("Decompressed Data Lenght not correct")
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
        Reconstructed = np.array(Reconstructed).reshape(height,width,bytes_per_pixel)
        return Reconstructed


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
    rawIDATData: List[int] #IDAT after decompression and defiltering

    def __init__(self, image_binary_data):
        CriticalChunkList = []
        AncillaryChunkList = []
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
                logging.error(f"Error during loading chunk {e}")
                continue
            if chunk.Type == b'IEND':
                break
        self.criticalChunks = CriticalChunks(CriticalChunkList)
        self.ancillaryChunks = AncillaryChunks(AncillaryChunkList)
        self.rawIDATData = self.criticalChunks.reconstructIDATData()
        # out_arr = []
        # for iter in range(int(len(self.rawIDATData)/x)):
        #     tab = self.rawIDATData[iter * x:iter*x + x]
        #     out_arr.append(tab)
        # y = np.array(out_arr)
        # plt.figure(3)
        # plt.imshow(y.reshape(self.criticalChunks.IHDR.height,self.criticalChunks.IHDR.width,x))
        # plt.axis('off')
        # plt.show()

    def encryptImage(self):
        ecb = ECB()
        ecb.encrypt(self.rawIDATData)
        ecb.decrypt()




    def restoreImage(self, img_binary_file:bytes, signature:bytes, exclude_ancillary:bool):
        img_binary_file.write(signature)
        img_binary_file.write(self.criticalChunks.IHDR.ReturnData())
        if exclude_ancillary is False:
            img_binary_file.write(self.ancillaryChunks.returnChunkData())
        if self.criticalChunks.PLTE is not None:
                img_binary_file.write(self.criticalChunks.PLTE.ReturnData())
        img_binary_file.write(self.criticalChunks.returnIDAT())
        img_binary_file.write(self.criticalChunks.IEND.ReturnData())
        return img_binary_file
        

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
    
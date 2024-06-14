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
from PIL import Image as pilimg


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
    rawIDATData: np.array #IDAT after decompression and defiltering | SHAPE(height, width, pixel color depth)
    excesive_iend_data: bytes = b''
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
        # if read_after_exif:
        #     while True:
        #         remaining_data = image_binary_data.read(1024)  # Read in chunks of 1024 bytes
        #         if not remaining_data:
        #             break
        #         self.excesive_iend_data += remaining_data
        
        self.criticalChunks = CriticalChunks(CriticalChunkList)
        self.ancillaryChunks = AncillaryChunks(AncillaryChunkList)
        self.rawIDATData = self.criticalChunks.reconstructIDATData()



    # def save_image_using_pillow(self, data, excesive_data:bytes, filename, path):
    #     logger.info(f"Saving output image: {filename}")
    #     try:
    #         height, width, color = data.shape

    #         data_normalized = (data-np.min(data))/(np.max(data) - np.min(data))

    #         data_rescaled = np.array(255*data_normalized,dtype='uint8')

    #         # Determine the image mode based on the color channels
    #         if color == 1:
    #             mode = "L"  # Grayscale
    #         elif color == 2:
    #             mode = "LA"  # Grayscale with alpha
    #         elif color == 3:
    #             mode = "RGB"  # RGB
    #         else:
    #             mode = "RGBA"  # RGB with alpha

    #         # Create a PIL Image from the data
    #         image = pilimg.fromarray(data_rescaled, mode=mode)

    #         if not os.path.exists(path):
    #             os.mkdir(path)
    #         full_path = Path(path) / filename


    #         output_io = io.BytesIO()
    #         image.save(output_io, format="PNG")
    #         png_data = output_io.getvalue()

    #         iend_index = png_data.rfind(b'\x49\x45\x4E\x44\xAE\x42\x60\x82')
    #         if iend_index == -1:
    #             raise ValueError("IEND chunk not found in PNG data")

    #         # Split the data at the end of the IEND chunk
    #         end_of_iend = iend_index + 8
    #         png_data_with_hidden_bytes = png_data[:end_of_iend] + excesive_data + png_data[end_of_iend:]

    #         # Append the excessive bytes after the IEND chunk
    #         png_data_with_excessive_bytes = png_data_with_hidden_bytes

    #         # Write the final PNG data to the output file
    #         with open(full_path, 'wb') as f:
    #             f.write(png_data_with_excessive_bytes)

    #         # Check if the folder exists, if not, create directory
            

    #         # Save the image
    #         # image.save(full_path)
    #         logger.info(f"Image saved successfully: {full_path}")
    #     except Exception as e:
    #         logger.error(f"Error saving output image: {filename}, Error: {e}")



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
            

    def encrytpRSA(self):
        pass
        # rsa = RSA()
        # encrypted, excesive = rsa.encrypt(self.rawIDATData)
        # self.save_image_using_pillow(encrypted,excesive,'rsa_encrypt.png', self.path_to_save)
        # data,excesive = self.readImage()
        # d = rsa.decrypt(data,excesive)
        # f = plt.figure()
        # plt.imshow(f)
        # plt.show()
        

                



        # try:
        #     rsa = RSA()
        #     encrypted = rsa.encrypt(self.rawIDATData)
        #     self.saveImage(self.path_to_save, filename='rsa_encrypt.png',data=encrypted)
        #     decrypted = rsa.decrypt()
        #     self.saveImage(self.path_to_save, filename='rsa_decrypt.png',data=decrypted)
        # except Exception as e:
        #     logger.error(f"Error in encryptRSA function: {e}")




    def encryptECB(self) -> None:
        try:
            ecb = ECB()
            encrypted = ecb.encrypt(self.rawIDATData)
            self.saveImage(self.path_to_save, filename='ecb_encrypt.png',data=encrypted)
            decrypted = ecb.decrypt()
            self.saveImage(self.path_to_save, filename='ecb_decrypt.png',data=decrypted)
        except Exception as e:
            logger.error(f"Error in encryptECB function: {e}")

    def encryptCBC(self):
        try:
            cbc = CBC()
            encrypted = cbc.encrypt(self.rawIDATData)
            self.saveImage(self.path_to_save, filename='cbc_encrypt.png', data=encrypted)
            decrypted = cbc.decrypt()
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
    
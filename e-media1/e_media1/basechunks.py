from dataclasses import dataclass
import io
import logging
import struct
from tabulate import tabulate
import pprint
from typing import Tuple,Dict
import matplotlib.pyplot as plt
from e_media1.additional_data import EXIF_TAGS, data_format_bytes


logger = logging.getLogger("loger")




@dataclass
class Chunk():
    '''
    Klasa bazowa dla kazdego chunka w obrazie PNG
    '''

    Lenght: bytes
    Type: bytes
    Data: bytes
    CRC: bytes

    def __init__(self,lenght,type,data,crc):
        self.Lenght = lenght
        self.Type = type
        self.Data = data
        self.CRC = crc

    def __str__(self) -> str:
        return self.Type.decode()



    def get_all_chunk_bytes(self) -> bytes:
        '''
        Returns all chunk data as sequence of bytes in required line-up
        '''
        return bytes(self.Lenght + self.Type + self.Data + self.CRC)
    
    def get_chunk_data_bytes(self) -> bytes:
        return bytes(self.Data)
    
class IHDRChunk(Chunk):
    def __init__(self, lenght,type,data,crc):
        super().__init__(lenght,type,data,crc)
        self.width = int.from_bytes(self.Data[0:4])
        self.height = int.from_bytes(self.Data[4:8])
        self.depth = int.from_bytes(self.Data[8:9])
        self.color = int.from_bytes(self.Data[9:10])
        self.compression = int.from_bytes(self.Data[10:11])
        self.filtration = int.from_bytes(self.Data[11:12])
        self.interlace = int.from_bytes(self.Data[12:13])


    def DecodeData(self):
        '''
        Prints IHDR data in tabular format
        '''
        table = tabulate(
            [[self.width,self.height,self.depth,self.color,self.compression,self.filtration,self.interlace]],
            headers=['Width','Height','Bit Depth','Color Type', 'Compression Method', 'Filter Method', 'Interlance Method'])
        print(f'\nDecoding Header:\n{table}\n')


    def __str__(self) -> str:
        return super().__str__()


class IENDChunk(Chunk):
    def __init__(self, lenght, type, data, crc):
        super().__init__(lenght, type, data, crc)

    def __str__(self) -> str:
        return super().__str__()

   
class PLTEChunk(Chunk):
    def __init__(self, lenght, type, data, crc):
        super().__init__(lenght, type, data, crc)
        lenght_digit = int.from_bytes(lenght)
        pallete_list = []
        for i in range(0,lenght_digit, 3):
            color = int.from_bytes((data[i:i+3]))
            pallete_list.append(color)
        self.palette = pallete_list


    def __str__(self) -> str:
        return super().__str__()
    
    def show_palette(self):
        '''
        Shows color palette of image
        '''
        fig, ax = plt.subplots(figsize=(8, 2))
        ax.imshow([self.palette], aspect='auto')
        ax.axis('off')
        plt.show()


class IDATChunk(Chunk):
    def __init__(self, lenght, type, data, crc):
        super().__init__(lenght, type, data, crc)
    
    def __str__(self) -> str:
        return super().__str__()
    
    

class gAMAChunk(Chunk):
    def __init__(self, lenght, type, data, crc):
        super().__init__(lenght, type, data, crc)
        self.gamma = int.from_bytes(data,'big') / 100000

    # def __str__(self) -> str:
    #     return self.gamma
    def __str__(self) -> str:
        return super().__str__()
    
    def presentData(self):
        print(f"Gama Data: {self.gamma}")


class eXIFChunk(Chunk):
    def __init__(self, lenght, type, data, crc):
        super().__init__(lenght, type, data, crc)

    def readEXIF(self) -> Tuple[Dict,Dict]:
        '''
            Read eXIF data from all IFDs existing

            Args:
                *None
            
            Return:
                * entries -> dict: containing eXIF data corespoding to certain MAIN tags read from primary file directory
                * sub_entries -> dict: containing eXIF data corespoding to certain SUB_MAIN tags read from additional file directory
            '''
        logger.info("Starting process of reading eXIF data chunk..")
        stream = io.BytesIO(self.Data)

        # checking byte align: MM - big endian | II - small endian
        byte_align = stream.read(2)
        endian = '>' if byte_align == b'MM' else '<'

        # offset to first File Directory
        _tag_mark = stream.read(2)
        First_IFD_Offset = int.from_bytes(stream.read(4))

        # reading first IFD
        try:
            entries, next_ifd_offset = eXIFChunk.read_ifd(stream,First_IFD_Offset,endian)

            # if next_if_offest exist we also read it
            while next_ifd_offset != 0:
                next_entries, next_ifd_offset = eXIFChunk.read_ifd(stream,next_ifd_offset,endian)  
                entries.update(next_entries)  
        except Exception as e:
            logging.error(f"Exception during IFD Read: {e}")


        try:
            # reading sub_exif - helpful data about camera etc.
            sub_entries, _ = eXIFChunk.read_ifd(stream,entries['ExifOffset'],endian)
        except Exception as e:
            logging.error(f"Exception during SUB-IFD read: {e}")

        return entries,sub_entries

    @staticmethod
    def read_ifd(stream: io.BytesIO, offset: bytes, endian: str) -> Tuple[Dict,int]:
            '''
            Read eXIF data from single IFD

            Args:
                *stream -> BytesIO: stream from which function will read data
                *offset -> bytes: bytes which are localization of File Directory
                *endian -> str: type of byte align
            
            Return:
                * entries -> dict: containing eXIF data corespoding to certain tags
                * next_ifd_offset -> long: contating offset to next File Directory. Can be 0 if next directory does not exists.
            '''
            stream.seek(offset)

            # number of "catalogues" with IFD Data.
            num_entries = struct.unpack(endian + 'H', stream.read(2))[0]  
            entries = dict()

            # each catalogue has 12 bytes of data
            for _ in range(num_entries):
                '''
                Structure:
                    - Tag (informacja o danej - co oznacza) - 2 bajty
                    - Data Format (informacja o typie/formacie danej) - 2 bajty
                    - Components Number (Ilosc komponentow) - 4 bajty -> (Data Format * Components Number) daja ilosc bajtow jakie zajmuja dane w pamieci:
                        * jezeli powyzej 4 bajtow to *Values* zawiera offset do obszaru pamieci z faktycznymi danymi
                        * jezeli 4 bajty lub mniej *Values* ma faktyczne dane
                    - Values (obszar gdzie zawieraja sie fizyczne dane pod powyzszym warunkiem)
                '''
                entry = stream.read(8)  
                tag, data_format, count = struct.unpack(endian + 'HHL', entry)
                number_of_bytes = data_format_bytes.get(data_format) * count

                if number_of_bytes > 4:
                    offset_value = int.from_bytes(stream.read(4))
                    position = stream.tell()
                    stream.seek(offset_value)
                    data_stream = stream.read(number_of_bytes)
                    stream.seek(position)
                else:
                    data_stream = stream.read(number_of_bytes)
                    x = stream.read(4-number_of_bytes)
                try:
                    # sprawdzamy typ taga zeby wiedziec jak go dekodowac
                    if EXIF_TAGS[tag][1] == 'string':
                        data = data_stream.rstrip(b'\x00').decode()
                    elif EXIF_TAGS[tag][1] == 'rational':
                        nominator,denominator = struct.unpack(endian + "LL", data_stream)
                        data = nominator / denominator
                    else:
                        data = int.from_bytes(data_stream)

                    entries[EXIF_TAGS[tag][0]] = data
                except Exception as e:
                    logger.error(f"Error reading IFD catalogue: {e}")

            #offset do nastepnego IFD
            next_ifd_offset = struct.unpack(endian + 'L', stream.read(4))[0]  
            return entries, next_ifd_offset
    
    def __str__(self) -> str:
        return super().__str__()
    
    def presentData(self):
        '''
        Prints eXIF data read from two IFD's (MAIN and SUB)
        '''
        main_ifd, sub_ifd = self.readEXIF()
        print("\nEXIF Data")
        pprint.pprint(main_ifd)
        pprint.pprint(sub_ifd)


class cHRMChunk(Chunk):
    def __init__(self, lenght, type, data, crc):
        super().__init__(lenght, type, data, crc)
        stream = io.BytesIO(data)
        self.white_point_x = int.from_bytes(stream.read(4)) / 100000.0
        self.white_point_y = int.from_bytes(stream.read(4)) / 100000.0
        self.red_x = int.from_bytes(stream.read(4)) / 100000.0
        self.red_y = int.from_bytes(stream.read(4)) / 100000.0
        self.green_x = int.from_bytes(stream.read(4)) / 100000.0
        self.green_y = int.from_bytes(stream.read(4)) / 100000.0
        self.blue_x = int.from_bytes(stream.read(4)) / 100000.0
        self.blue_y = int.from_bytes(stream.read(4)) / 100000.0

        
    def presentData(self) -> None:
        '''
        Prints cHRM data in tabular format
        '''
        table = tabulate([
            ["WhitePoint",self.white_point_x,self.white_point_y],
            ["Red",self.red_x,self.red_y],
            ["Green",self.green_x,self.green_y],
            ["Blue",self.blue_x,self.blue_y]],headers=["Type","XValue","YValue"])
        print(f"cHRM Chunk Data: \n{table}\n")

    def __str__(self) -> str:
        return super().__str__()
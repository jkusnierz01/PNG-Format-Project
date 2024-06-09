from dataclasses import dataclass
import io
import logging
import struct
from tabulate import tabulate
import pprint
import matplotlib.pyplot as plt

logger = logging.getLogger("loger")

EXIF_TAGS = {
    270: ['ImageDescription', 'string'],
    271: ['Make', 'string'],
    272: ['Model', 'string'],
    274: ['Orientation', 'digit'],
    282: ['XResolution', 'rational'],
    283: ['YResolution', 'rational'],
    296: ['ResolutionUnit', 'digit'],
    305: ['Software', 'string'],
    306: ['DateTime', 'string'],
    318: ['WhitePoint', 'rational'],
    319: ['PrimaryChromaticities', 'rational'],
    529: ['YCbCrCoefficients', 'rational'],
    531: ['YCbCrPositioning', 'digit'],
    532: ['ReferenceBlackWhite', 'rational'],
    33432: ['Copyright', 'string'],
    34665: ['ExifOffset', 'digit'],      
    # SUB TAGS
    33434: ['ExposureTime', 'rational'],
    33437: ['FNumber', 'rational'],
    34850: ['ExposureProgram', 'digit'],
    34855: ['ISOSpeedRatings', 'digit'],
    36864: ['ExifVersion', 'string'],
    36867: ['DateTimeOriginal', 'string'],
    36868: ['DateTimeDigitized', 'string'],
    37121: ['ComponentsConfiguration', 'string'],
    37122: ['CompressedBitsPerPixel', 'rational'],
    37377: ['ShutterSpeedValue', 'rational'],
    37378: ['ApertureValue', 'rational'],
    37379: ['BrightnessValue', 'rational'],
    37380: ['ExposureBiasValue', 'rational'],
    37381: ['MaxApertureValue', 'rational'],
    37382: ['SubjectDistance', 'rational'],
    37383: ['MeteringMode', 'digit'],
    37384: ['LightSource', 'digit'],
    37385: ['Flash', 'digit'],
    37386: ['FocalLength', 'rational'],
    37510: ['UserComment', 'string'],
    40960: ['FlashPixVersion', 'string'],
    40961: ['ColorSpace', 'digit']         # 0xaa001
}

data_format_bytes = {
    1: 1,  # unsigned byte
    2: 1,  # ascii strings
    3: 2,  # unsigned short
    4: 4,  # unsigned long
    5: 8,  # unsigned rational
    6: 1,  # signed byte
    7: 1,  # undefined
    8: 2,  # signed short
    9: 4,  # signed long
    10: 8, # signed rational
    11: 4, # single float
    12: 8  # double float
}






@dataclass
class Chunk:
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

    def ReturnData(self):
        return bytes(self.Lenght + self.Type + self.Data + self.CRC)
    
    
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

    def readEXIF(self):
        stream = io.BytesIO(self.Data)

        # sprawdzenie ukladu bajtow: MM - big endian | II - small endian
        byte_align = stream.read(2)
        if byte_align == b'MM':
            endian = '>'
        else:
            endian = '<'
        _tag_mark = stream.read(2)

        # offset do 1 File Directory
        First_IFD_Offset = int.from_bytes(stream.read(4))

        # odczytujemy 1 IFD
        try:
            entries, next_ifd_offset = eXIFChunk.read_ifd(stream,First_IFD_Offset,endian)

            # jezeli jest offset do kolejnego to odczytujemy
            if next_ifd_offset != 0:
                next_entries, next_ifd_offset = eXIFChunk.read_ifd(stream,next_ifd_offset,endian)     
        except Exception as e:
            logging.error(f"Exception during IFD Read: {e}")
        try:
            # odczytujemy sub_exif - dane na temat czasu naswietlania/ekspozycji itd.
            sub_entries, sub_next_ifd_offset = eXIFChunk.read_ifd(stream,entries['ExifOffset'],endian)
        except Exception as e:
            logging.error(f"No SUB_EXIF Chunk")

        return entries,sub_entries

    @staticmethod
    def read_ifd(stream: io.BytesIO, offset, endian):
            stream.seek(offset)

            # ilosc "katalogow" z danymi w naszym IFD
            num_entries = struct.unpack(endian + 'H', stream.read(2))[0]  
            entries = dict()

            # kazdy katalog ma 12 bajtow danych
            for _ in range(num_entries):
                '''
                struktura:
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
                except KeyError as e:
                    pass

            #offset do nastepnego IFD
            next_ifd_offset = struct.unpack(endian + 'L', stream.read(4))[0]  
            return entries, next_ifd_offset
    
    def __str__(self) -> str:
        return super().__str__()
    
    def presentData(self):
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
        table = tabulate([
            ["WhitePoint",self.white_point_x,self.white_point_y],
            ["Red",self.red_x,self.red_y],
            ["Green",self.green_x,self.green_y],
            ["Blue",self.blue_x,self.blue_y]],headers=["Type","XValue","YValue"])
        print(f"cHRM Chunk Data: \n{table}\n")

    def __str__(self) -> str:
        return super().__str__()
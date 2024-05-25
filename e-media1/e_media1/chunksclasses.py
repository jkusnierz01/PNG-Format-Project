from dataclasses import dataclass, field
from typing import List
import io
import logging
import struct
from tabulate import tabulate


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

    def __init__(self,binary_file_data):
        self.Lenght = binary_file_data.read(4)
        decimalLenght = int.from_bytes(self.Lenght)
        self.Type = binary_file_data.read(4)
        self.Data = binary_file_data.read(decimalLenght)
        self.CRC = binary_file_data.read(4)

    def ReturnData(self):
        return bytes(self.Lenght + self.Type + self.Data + self.CRC)
    

    @staticmethod
    def decode_bytes(bytes_data):
        try:
            data = bytes_data.decode()
        except:
            data = int.from_bytes(bytes_data)
        return data
    
class IHDRChunk(Chunk):
    def __init__(self, binary_file_data):
        super().__init__(binary_file_data)
        self.width = int.from_bytes(self.Data[0:4])
        self.height = int.from_bytes(self.Data[4:8])
        self.depth = int.from_bytes(self.Data[8:9])
        self.color = int.from_bytes(self.Data[9:10])
        self.compression = int.from_bytes(self.Data[10:11])
        self.filtration = int.from_bytes(self.Data[11:12])
        self.interlace = int.from_bytes(self.Data[12:13])



class IEND(Chunk):
    pass

class IDAT(Chunk):
    pass


@dataclass
class CriticalChunks:
    '''
    Klasa przechowujaca dane o chunkach krytycznych
    '''
    IHDR: IHDRChunk
    IEND: Chunk
    IDAT: List[Chunk] = field(default_factory=list)

    def __init__(self,chunk_list_data):
        self.IHDR = chunk_list_data.pop(0)
        self.IEND = chunk_list_data.pop(-1)
        self.IDAT = chunk_list_data

    def DecodeHeader(self):
        width = int.from_bytes(self.IHDR.Data[0:4])
        height = int.from_bytes(self.IHDR.Data[4:8])
        depth = int.from_bytes(self.IHDR.Data[8:9])
        color = int.from_bytes(self.IHDR.Data[9:10])
        compression = int.from_bytes(self.IHDR.Data[10:11])
        filtration = int.from_bytes(self.IHDR.Data[11:12])
        interlace = int.from_bytes(self.IHDR.Data[12:13])
        print("HEADER")
        print(f"Width x Height: {width} x {height}\nColor depth: {depth} bits; Color type: {color}; Compression: {compression}; Filtration: {filtration}; Interlace method: {interlace}\n")

    def returnChunkData(self) -> bytes:
        IHDR_data = self.IHDR.ReturnData()
        IEND_data = self.IEND.ReturnData()
        IDAT_data = bytearray()
        for chunk in self.IDAT:
            IDAT_data.extend(chunk.ReturnData())
        return bytes(IHDR_data + IDAT_data + IEND_data)
        

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
    

    def showChunks(self):
        for chunk in self.ChunkList:
            print(chunk.Type)


    @staticmethod
    def readCHRM(chunk_data):
        stream = io.BytesIO(chunk_data)
        white_point_x = int.from_bytes(stream.read(4)) / 100000.0
        white_point_y = int.from_bytes(stream.read(4)) / 100000.0
        red_x = int.from_bytes(stream.read(4)) / 100000.0
        red_y = int.from_bytes(stream.read(4)) / 100000.0
        green_x = int.from_bytes(stream.read(4)) / 100000.0
        green_y = int.from_bytes(stream.read(4)) / 100000.0
        blue_x = int.from_bytes(stream.read(4)) / 100000.0
        blue_y = int.from_bytes(stream.read(4)) / 100000.0
        table = tabulate([
            ["WhitePoint",white_point_x,white_point_y],
            ["Red",red_x,red_y],
            ["Green",green_x,green_y],
            ["Blue",blue_x,blue_y]],headers=["Type","XValue","YValue"])
        print(f"cHRM Chunk Data: \n{table}\n")
        # print("CHRM")
        # print(f"White Point: {white_point_x}, {white_point_y}\nRed: {red_x}, {red_y}| Green: {green_x} | {green_y}| Blue: {blue_x} | {blue_y}\n")

    @staticmethod
    def readPHYS(chunk_data):
        unit_dict = {0:"not specified", 1:"meters"}
        stream = io.BytesIO(chunk_data)
        pixels_X_axis = int.from_bytes(stream.read(4))
        pixels_Y_axis = int.from_bytes(stream.read(4))
        unit_specifier = int.from_bytes(stream.read(1))
        # table = tabulate([pixels_X_axis,pixels_Y_axis,unit_dict[unit_specifier]],headers=[])
        print("PHYS")
        print(f"PIXELS X: {pixels_X_axis} | PIXELS Y: {pixels_Y_axis} | UNIT: {unit_dict[unit_specifier]}\n")

    @staticmethod
    def readEXIF(chunk_data):
        def read_ifd(stream: io.BytesIO, offset, endian):
            stream.seek(offset)
            num_entries = struct.unpack(endian + 'H', stream.read(2))[0]  # Read number of entries (2 bytes)
            entries = dict()
            for _ in range(num_entries):
                entry = stream.read(8)  # Each entry is 12 bytes
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
            next_ifd_offset = struct.unpack(endian + 'L', stream.read(4))[0]  # Read offset to next IFD (4 bytes)
            return entries, next_ifd_offset


        stream = io.BytesIO(chunk_data)
        byte_align = stream.read(2)
        if byte_align == b'MM':
            endian = '>'
        else:
            endian = '<'
        _tag_mark = stream.read(2)
        First_IFD_Offset = int.from_bytes(stream.read(4))
        entries, next_ifd_offset = read_ifd(stream,First_IFD_Offset,endian)
        print(entries)
        if next_ifd_offset != 0:
            next_entries, next_ifd_offset = read_ifd(stream,next_ifd_offset,endian)
        try:
            sub_entries, sub_next_ifd_offset = read_ifd(stream,entries['ExifOffset'],endian)
            print(sub_entries)
        except Exception as e:
            logging.error(f"Error during loading chunk {e}")
        
        

    
    
    def read3Chunks(self):
        chunk1 = b'eXIf'
        chunk2 = b'cHRM'
        chunk3 = b'pHYs'
        for chunk in self.ChunkList:
            if chunk.Type == chunk1:
                self.readEXIF(chunk.Data)
            elif chunk.Type == chunk2:
                self.readCHRM(chunk.Data)
            elif chunk.Type == chunk3:
                self.readPHYS(chunk.Data)
                



@dataclass
class Image:
    criticalChunks: CriticalChunks
    ancillaryChunks: AncillaryChunks


    def __init__(self, image_binary_data):
        CriticalChunkList = []
        AncillaryChunkList = []
        while image_binary_data:
            try:
                chunk_bytes_parsing.get()
                chunk = Chunk(image_binary_data)
                first_byte = chunk.Type[0:1]
                letter = first_byte.decode() #checking if chunk is critical (uppercase:critical | lowercase:ancillary)
                if letter.isupper():
                    CriticalChunkList.append(chunk)
                else:
                    AncillaryChunkList.append(chunk)
            except Exception as e:
                logging.error(f"Error during loading chunk {e}")
                continue
            if chunk.Type == b'IEND':
                break
        self.criticalChunks = CriticalChunks(CriticalChunkList)
        self.ancillaryChunks = AncillaryChunks(AncillaryChunkList)
        

    def restoreImage(self, img_binary_file:bytes, signature:bytes, exclude_ancillary:bool):
        img_binary_file.write(signature)
        img_binary_file.write(self.criticalChunks.returnChunkData())
        if exclude_ancillary:
            return img_binary_file
        else:
            img_binary_file.write(self.ancillaryChunks.returnChunkData())
            return img_binary_file
        

    def displayChunks(self):
        print(f"Critical Chunks: {self.criticalChunks.IHDR.Type}, {self.criticalChunks.IDAT[0].Type}, {self.criticalChunks.IEND.Type}")
        print(f"Ancillary Chunks: {[chunk.Type for chunk in self.ancillaryChunks.ChunkList]}")
        


chunk_bytes_parsing = {
    b'IHDR':IHDRChunk,
    b'IEND':IENDChunk,
    b'IDAT':IDATChunk,
}   
    
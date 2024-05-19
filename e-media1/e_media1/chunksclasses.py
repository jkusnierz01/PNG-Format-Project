from dataclasses import dataclass, field
from typing import List
import io
import sys
import logging

EXIF_TAGS = {
    b'\x01\x0e': "ImageDescription",
    b'\x01\x0f': "Make",
    b'\x01\x10': "Model",
    b'\x01\x12': "Orientation",
    b'\x01\x1a': "XResolution",
    b'\x01\x1b': "YResolution",
    b'\x01\x28': "ResolutionUnit",
    b'\x01\x31': "Software",
    b'\x01\x32': "DateTime",
    b'\x01\x3e': "WhitePoint",
    b'\x01\x3f': "PrimaryChromaticities",
    b'\x02\x11': "YCbCrCoefficients",
    b'\x02\x13': "YCbCrPositioning",
    b'\x02\x14': "ReferenceBlackWhite",
    b'\x82\x98': "Copyright",
    b'\x87\x69': "ExifOffset"
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


@dataclass
class CriticalChunks:
    IHDR: Chunk
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
        print(f"Width x Height: {width} x {height}\nColor depth: {depth} bits; Color type: {color}; Compression: {compression}; Filtration: {filtration}; Interlace method: {interlace}")

    def returnChunkData(self) -> bytes:
        IHDR_data = self.IHDR.ReturnData()
        IEND_data = self.IEND.ReturnData()
        IDAT_data = bytearray()
        for chunk in self.IDAT:
            IDAT_data.extend(chunk.ReturnData())
        return bytes(IHDR_data + IDAT_data + IEND_data)
        

@dataclass
class AncillaryChunks:
    ChunkList: List[Chunk] = field(default_factory=list)

    def returnChunkData(self) -> bytes:
        chunkData = bytearray()
        for chunk in self.ChunkList:
            chunkData.extend(chunk.ReturnData())
        return bytes(chunkData)
    

    def showChunks(self):
        for chunk in self.ChunkList:
            print(chunk.Type)

    def readEXIF(self):
        
        type = b'eXIf'
        for chunk in self.ChunkList:
            if type == chunk.Type:
                stream = io.BytesIO(chunk.Data)
                byte_align = stream.read(2)
                print(byte_align)
                tag_mark = stream.read(2)
                First_IFD_Offset = int.from_bytes(stream.read(4))
                stream.seek(First_IFD_Offset)
                while True:
                    number_of_dir = stream.read(2)
                    for ifd_dir in range(int.from_bytes(number_of_dir)):
                        tag_number = stream.read(2)
                        data_format = stream.read(2)
                        components_number = stream.read(4)
                        data = stream.read(4)
                        print(tag_number.hex())
                        print(EXIF_TAGS[tag_number])
                        print(int.from_bytes(components_number))
                        print(int.from_bytes(data_format))
                    next_offset = stream.read(4)
                    if next_offset == b'\x00\x00\x00\x00':
                        break

@dataclass
class Image:
    criticalChunks: CriticalChunks
    ancillaryChunks: AncillaryChunks


    def __init__(self, image_binary_data):
        CriticalChunkList = []
        AncillaryChunkList = []
        while image_binary_data:
            try:
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
    
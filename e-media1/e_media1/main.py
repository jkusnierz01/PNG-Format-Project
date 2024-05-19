import PIL
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

parser = argparse.ArgumentParser(description="path to PNG file")
parser.add_argument('path',help = 'Path to PNG file')
args = parser.parse_args()


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
        return self.Lenght + self.Type + self.Data + self.CRC


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



@dataclass
class AncillaryChunks:
    ChunkList: List[Chunk] = field(default_factory=list)


def loadChunks(image_binary_data):
    critical_chunks_types = [b'IHDR',b'IDAT',b'IEND']
    CriticalChunkList = []
    AncillaryChunkList = []
    while True:
        try:
            chunk = Chunk(image_binary_data)
            if chunk.Type in critical_chunks_types:
                CriticalChunkList.append(chunk)
            else:
                AncillaryChunkList.append(chunk)
        except:
            print("Error during loading chunk")
            break
        if chunk.Type == b'IEND':
            break
    AncChunks = AncillaryChunks(AncillaryChunkList)
    CritChunks = CriticalChunks(CriticalChunkList)
    return CritChunks, AncChunks
    




def main():
    if Path(args.path).is_file():
        with open(args.path,'rb') as image_binary:
            signature = image_binary.read(8)
            if signature == b'\x89PNG\r\n\x1a\n':
                criticalChunks, ancillaryChunks = loadChunks(image_binary)
                criticalChunks.DecodeHeader()
            else:
                print("Wrong file format!")
    else:
        print("Invalid path to file!")


if __name__ == '__main__':
    main()

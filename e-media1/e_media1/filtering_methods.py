import zlib
from dataclasses import dataclass
from typing import List
from e_media1.basechunks import IDATChunk, IHDRChunk
from io import BytesIO
import logging
import math

logger = logging.getLogger("loger")

class ReconstructingMethods:

    @staticmethod
    def Reconstruct_a(row,col,ReconstructedList, width, bytes_number):
        if col >= bytes_number:
            return ReconstructedList[row * (width * bytes_number) + col - bytes_number]
        else:
            return 0
            
    @staticmethod
    def Reconstruct_b(row,col,ReconstructedList, width, bytes_number):
        if row >= 1:
            return ReconstructedList[(row -1) * width * bytes_number + col]
        else:
            return 0
            
    @staticmethod     
    def Reconstruct_c(row,col,ReconstructedList, width, bytes_number):
        if row >= 1 and col >=bytes_number:
            return ReconstructedList[(row-1) * width * bytes_number + col - bytes_number]   
        else:
            return 0 

    @staticmethod
    def none(x,row,col,ReconstructedList, width, bytes_number):
        return x

    @staticmethod
    def Sub(x,row,col,ReconstructedList, width, bytes_number):
        return x + ReconstructingMethods.Reconstruct_a(row,col,ReconstructedList, width, bytes_number)

    @staticmethod
    def Up(x,row,col,ReconstructedList, width, bytes_number):
        return x + ReconstructingMethods.Reconstruct_b(row,col,ReconstructedList, width, bytes_number)


    @staticmethod
    def Average(x,row,col,ReconstructedList, width, bytes_number):
        a = ReconstructingMethods.Reconstruct_a(row,col,ReconstructedList, width, bytes_number)
        b = ReconstructingMethods.Reconstruct_b(row,col,ReconstructedList, width, bytes_number)
        return x + math.floor(( a + b) / 2) 

    @staticmethod
    def Paeth(x,row,col,ReconstructedList, width, bytes_number):
        a = ReconstructingMethods.Reconstruct_a(row,col,ReconstructedList, width, bytes_number)
        b = ReconstructingMethods.Reconstruct_b(row,col,ReconstructedList, width, bytes_number)
        c = ReconstructingMethods.Reconstruct_c(row,col,ReconstructedList, width, bytes_number)
        return x + ReconstructingMethods.PaethPredictor(a,b,c)
    
    @staticmethod
    def PaethPredictor(a, b, c):
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)
        if pa <= pb and pa <= pc:
            Pr = a
        elif pb <= pc:
            Pr = b
        else:
            Pr = c
        return Pr




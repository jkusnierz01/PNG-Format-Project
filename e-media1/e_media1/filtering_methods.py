import logging
import math
import numpy as np

logger = logging.getLogger("loger")

class ReconstructingMethods:

    @staticmethod
    def Reconstruct_a(row, col, ReconstructedList, width, bytes_number) -> int:
        '''
        Reconstructs the value from the previous column in the same row.

        Args:
            * row (int): The current row index.
            * col (int): The current column index.
            * ReconstructedList (list): The list containing reconstructed values.
            * width (int): The width of the image in bytes.
            * bytes_number (int): The number of bytes per pixel.

        Returns:
            * int: The reconstructed value from the previous column in the same row or 0 if it doesn't exist.
        '''
        if col >= bytes_number:
            return ReconstructedList[row * (width * bytes_number) + col - bytes_number]
        else:
            return 0
            
    @staticmethod
    def Reconstruct_b(row, col, ReconstructedList, width, bytes_number) -> int:
        '''
        Reconstructs the value from the same column in the previous row.

        Args:
            * row (int): The current row index.
            * col (int): The current column index.
            * ReconstructedList (list): The list containing reconstructed values.
            * width (int): The width of the image in bytes.
            * bytes_number (int): The number of bytes per pixel.

        Returns:
            * int: The reconstructed value from the same column in the previous row or 0 if it doesn't exist.
        '''
        if row >= 1:
            return ReconstructedList[(row - 1) * width * bytes_number + col]
        else:
            return 0
            
    @staticmethod     
    def Reconstruct_c(row, col, ReconstructedList, width, bytes_number) -> int:
        '''
        Reconstructs the value from the previous column in the previous row.

        Args:
            * row (int): The current row index.
            * col (int): The current column index.
            * ReconstructedList (list): The list containing reconstructed values.
            * width (int): The width of the image in bytes.
            * bytes_number (int): The number of bytes per pixel.

        Returns:
            * int: The reconstructed value from the previous column in the previous row or 0 if it doesn't exist.
        '''
        if row >= 1 and col >= bytes_number:
            return ReconstructedList[(row - 1) * width * bytes_number + col - bytes_number]   
        else:
            return 0 

    @staticmethod
    def none(x, row, col, ReconstructedList, width, bytes_number) -> int:
        '''
        Returns the original value without any modification.

        Args:
            * x (int): The original value.
            * row (int): The current row index.
            * col (int): The current column index.
            * ReconstructedList (list): The list containing reconstructed values.
            * width (int): The width of the image in bytes.
            * bytes_number (int): The number of bytes per pixel.

        Returns:
            * int: The original value.
        '''
        return x

    @staticmethod
    def Sub(x, row, col, ReconstructedList, width, bytes_number) -> int:
        '''
        Applies the Sub filter which adds the value from the previous column to the current value.

        Args:
            * x (int): The original value.
            * row (int): The current row index.
            * col (int): The current column index.
            * ReconstructedList (list): The list containing reconstructed values.
            * width (int): The width of the image in bytes.
            * bytes_number (int): The number of bytes per pixel.

        Returns:
            * int: The filtered value.
        '''
        return x + ReconstructingMethods.Reconstruct_a(row, col, ReconstructedList, width, bytes_number)

    @staticmethod
    def Up(x, row, col, ReconstructedList, width, bytes_number) -> int:
        '''
        Applies the Up filter which adds the value from the previous row to the current value.

        Args:
            * x (int): The original value.
            * row (int): The current row index.
            * col (int): The current column index.
            * ReconstructedList (list): The list containing reconstructed values.
            * width (int): The width of the image in bytes.
            * bytes_number (int): The number of bytes per pixel.

        Returns:
            * int: The filtered value.
        '''
        return x + ReconstructingMethods.Reconstruct_b(row, col, ReconstructedList, width, bytes_number)

    @staticmethod
    def Average(x, row, col, ReconstructedList, width, bytes_number) -> int:
        '''
        Applies the Average filter which adds the average of the values from the previous column and the previous row to the current value.

        Args:
            * x (int): The original value.
            * row (int): The current row index.
            * col (int): The current column index.
            * ReconstructedList (list): The list containing reconstructed values.
            * width (int): The width of the image in bytes.
            * bytes_number (int): The number of bytes per pixel.

        Returns:
            * int: The filtered value.
        '''
        a = ReconstructingMethods.Reconstruct_a(row, col, ReconstructedList, width, bytes_number)
        b = ReconstructingMethods.Reconstruct_b(row, col, ReconstructedList, width, bytes_number)
        return x + math.floor((a + b) / 2)

    @staticmethod
    def Paeth(x, row, col, ReconstructedList, width, bytes_number) -> int:
        '''
        Applies the Paeth filter which uses a predictor to add a value based on the values from the previous column, the previous row, and the previous column in the previous row to the current value.

        Args:
            * x (int): The original value.
            * row (int): The current row index.
            * col (int): The current column index.
            * ReconstructedList (list): The list containing reconstructed values.
            * width (int): The width of the image in bytes.
            * bytes_number (int): The number of bytes per pixel.

        Returns:
            * int: The filtered value.
        '''
        a = ReconstructingMethods.Reconstruct_a(row, col, ReconstructedList, width, bytes_number)
        b = ReconstructingMethods.Reconstruct_b(row, col, ReconstructedList, width, bytes_number)
        c = ReconstructingMethods.Reconstruct_c(row, col, ReconstructedList, width, bytes_number)
        return x + ReconstructingMethods.PaethPredictor(a, b, c)
    
    @staticmethod
    def PaethPredictor(a, b, c) -> int:
        '''
        The Paeth predictor function which computes the best predictor based on the values from the previous column, the previous row, and the previous column in the previous row.

        Args:
            * a (int): The value from the previous column.
            * b (int): The value from the previous row.
            * c (int): The value from the previous column in the previous row.

        Returns:
            * int: The predicted value.
        '''
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


class FilteringMethods:


    @staticmethod
    def NoneFilter(encrypted_data:np.array):

        try:  
            height, width, _ = encrypted_data.shape
            filtered_data = bytearray()

            # PNG filter type 0 (None)
            for row in range(height):
                filtered_data.append(0)  # Filter type byte
                filtered_data.extend(encrypted_data[row].flatten().tobytes())

            return filtered_data
        except Exception as e:
            logger.error(f"Applying None Filter Failed: {e}")
            return None
        









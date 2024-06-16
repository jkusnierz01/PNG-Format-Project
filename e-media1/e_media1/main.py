import PIL
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
from chunksclasses import Image
from fourier import createFourierPlots
from encrypt import ECB
from logger_setup import setup_color_logging
import png
import struct
import zlib
import os

parser = argparse.ArgumentParser(description="Process PNG File")
parser.add_argument('path',help = 'Path to PNG file')
parser.add_argument('-r','--removeAll', action='store_true', required=False, dest='remove_all',help="Remove all Ancillary Chunks from file")
parser.add_argument('-e', '--ecbencrypt', action='store_true',required=False,dest ='ECBencrypt',help="Encrypt Image with ECB algorithm")
parser.add_argument('-c', '--cbcencrypt', action='store_true',required=False,dest ='CBCencrypt',help="Encrypt Image with CBC algorithm")
parser.add_argument('-rsa', '--rsaencrypt', action='store_true',required=False,dest ='RSAencrypt',help="Encrypt Image with RSA algorithm")
parser.add_argument('-compressed', action='store_true', required=False, dest='encryptcompressed',help='Encrypt Compressed Image Data')


args = parser.parse_args()


def test():
    # Define the path to the uploaded file
    file_path = Path("/Users/jedrzejkusnierz/Desktop/programowanie/E-Media-Project1/e-media1/e_media1/output.png")

    # Read the binary data of the file
    with open(file_path, 'rb') as f:
        png_data = f.read()

    # Check the PNG signature
    png_signature = png_data[:8]
    expected_signature = b'\x89PNG\r\n\x1a\n'
    if png_signature != expected_signature:
        print("Invalid PNG signature.")
    else:
        print("Valid PNG signature.")

    # Function to read and verify chunks
    def read_chunks(data):
        index = 8  # Start after the signature
        chunks = []

        while index < len(data):
            # Read the chunk length (4 bytes, big-endian)
            length = struct.unpack('!I', data[index:index+4])[0]
            index += 4

            # Read the chunk type (4 bytes)
            chunk_type = data[index:index+4]
            index += 4

            # Read the chunk data (length bytes)
            chunk_data = data[index:index+length]
            index += length

            # Read the CRC (4 bytes)
            crc = struct.unpack('!I', data[index:index+4])[0]
            index += 4

            # Validate CRC
            calculated_crc = zlib.crc32(chunk_type + chunk_data) & 0xffffffff
            if crc != calculated_crc:
                print(f"CRC mismatch for chunk {chunk_type}: {crc} != {calculated_crc}")
            else:
                print(f"Valid CRC for chunk {chunk_type}")

            chunks.append((chunk_type, chunk_data, crc))

            # Stop if we reach the IEND chunk
            if chunk_type == b'IEND':
                break

        return chunks

    # Read and verify the chunks
    chunks = read_chunks(png_data)

    # Print chunk types
    for chunk_type, _, _ in chunks:
        print(f"Chunk type: {chunk_type}")




def image_plot(encrypted:Image):
    f = plt.figure()
    plt.imshow(encrypted)
    # plt.show()
    height, width, depth = encrypted.shape
    encrypted = encrypted.reshape((height, width * depth))
    w = png.Writer(width, height, greyscale=False, alpha=True)
    return w

def main():
    #setting up logger
    logger = setup_color_logging()
    logger.info("Starting the application")

    #sprawdzenie czy istnieje plik pod podana sciezka
    if Path(args.path).is_file():

        # odczytanie i transformacja do grayscale 
        img = plt.imread(args.path)
        grayscale_image = img[:, :, :3].mean(axis=2)

        # tworzenie / upewnienie sie o istnieniu folderu do zapisu obrazow wyjsciowych
        save_path:str = os.path.dirname(os.path.abspath(__file__))+"/../output_images/"
        os.makedirs(save_path, exist_ok=True)

        with open(args.path,'r+b') as image_binary:

            # sprawdzenie sygnatury
            signature = image_binary.read(8)
            if signature == b'\x89PNG\r\n\x1a\n':
                image = Image(image_binary, save_path)
                # image.displayImageData()
                # createFourierPlots(grayscale_image)
                if(args.ECBencrypt):
                    image.encryptECB(args.encryptcompressed)
                if(args.CBCencrypt):
                    image.encryptCBC()
                if(args.RSAencrypt):
                    image.encrytpRSA(True)
                # zapisanie zdjecia koncowego - z usunietymi wszystkimi chunkami dodatkowymi lub z pozostawionymi 3
                with open(save_path+"/restored.png",'wb') as out_image:
                    out_image = image.restoreImage(out_image, signature, args.remove_all)
            else:
                logger.error("Wrong file format!")
    else:
        logger.error(f"Invalid path to file! - {Path(args.path)}")


if __name__ == '__main__':
    main()

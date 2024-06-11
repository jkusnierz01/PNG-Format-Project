import PIL
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
from chunksclasses import Image
from fourier import createFourierPlots
from encrypt import ECB
from logger_setup import setup_color_logging
import png
import os

parser = argparse.ArgumentParser(description="Process PNG File")
parser.add_argument('path',help = 'Path to PNG file')
parser.add_argument('-r','--removeAll', action='store_true', required=False, dest='remove_all',help="Remove all Ancillary Chunks from file")
parser.add_argument('-e', '--ecbencrypt', action='store_true',required=False,dest ='ECBencrypt',help="Encrypt Image with ECB algorithm")
parser.add_argument('-c', '--cbcencrypt', action='store_true',required=False,dest ='CBCencrypt',help="Encrypt Image with CBC algorithm")
parser.add_argument('-rsa', '--rsaencrypt', action='store_true',required=False,dest ='RSAencrypt',help="Encrypt Image with RSA algorithm")


args = parser.parse_args()


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

        with open(args.path,'r+b') as image_binary:

            # sprawdzenie sygnatury
            signature = image_binary.read(8)
            if signature == b'\x89PNG\r\n\x1a\n':
                image = Image(image_binary)
                # image.displayImageData()
                # createFourierPlots(grayscale_image)
                if(args.ECBencrypt):
                    image.encryptECB()
                if(args.CBCencrypt):
                    image.encryptCBC()
                if(args.RSAencrypt):
                    image.encrytpRSA()
                # zapisanie zdjecia koncowego - z usunietymi wszystkimi chunkami dodatkowymi lub z pozostawionymi 3
                os.makedirs(os.path.dirname(os.path.abspath(__file__))+"/../output_images/", exist_ok=True)
                with open(os.path.dirname(os.path.abspath(__file__))+"/../output_images/restored.png",'wb') as out_image:
                    out_image = image.restoreImage(out_image, signature, args.remove_all)
            else:
                logger.error("Wrong file format!")
    else:
        logger.error(f"Invalid path to file! - {Path(args.path)}")


if __name__ == '__main__':
    main()

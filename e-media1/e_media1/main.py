import argparse
from pathlib import Path
import matplotlib.pyplot as plt
from e_media1.chunksclasses import Image
from e_media1.fourier import createFourierPlots
from e_media1.encrypt import ECB
from e_media1.additional_data import *
from e_media1.logger_setup import setup_color_logging
import os

parser = argparse.ArgumentParser(description="Process PNG File")
parser.add_argument('path',help = 'Path to PNG file')
parser.add_argument('-d','--displayImageData', action='store_true', required=False, dest='display_data',help="Display Image Data stored in chunks")
parser.add_argument('-r','--removeAnc', action='store_true', required=False, dest='remove_anc',help="Remove all Ancillary Chunks from file")
parser.add_argument('-e', '--ecbencrypt', action='store_true',required=False,dest ='ECBencrypt',help="Encrypt Image with ECB algorithm")
parser.add_argument('-c', '--cbcencrypt', action='store_true',required=False,dest ='CBCencrypt',help="Encrypt Image with CBC algorithm")
args = parser.parse_args()



def main():
    #setting up logger
    logger = setup_color_logging()
    logger.info("Starting the application")

    #sprawdzenie czy istnieje plik pod podana sciezka
    if Path(args.path).is_file():

        # odczytanie i transformacja do grayscale 
        img = plt.imread(args.path)
        grayscale_image = img[:, :, :3].mean(axis=2)

        # creating directory for images
        save_path:str = os.path.dirname(os.path.abspath(__file__))+"/../output_images/"
        os.makedirs(save_path, exist_ok=True)

        with open(args.path,'r+b') as image_binary:
            image = Image(image_binary, save_path)
            if(args.display_data):
                image.displayImageData()
                createFourierPlots(grayscale_image)
            if(args.ECBencrypt):
                image.encrypt_and_decrypt_image_using_ecb(library_func=True)
            if(args.CBCencrypt):
                image.encrypt_and_decrypt_image_using_cbc()
            with open(save_path+"/restored.png",'wb') as out_image:
                out_image = image.recreate_png_with_chunks(out_image, args.remove_anc)
    else:
        logger.error(f"Invalid path to file! - {Path(args.path)}")


if __name__ == '__main__':
    main()

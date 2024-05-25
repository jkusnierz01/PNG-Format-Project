import PIL
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
from e_media1.chunksclasses import Image
from e_media1.fourier import createFourierPlots

parser = argparse.ArgumentParser(description="Process PNG File")
parser.add_argument('path',help = 'Path to PNG file')
parser.add_argument('-r','--removeAll',action='store_true',required=False,dest='remove_all',help="Remove all Ancillary Chunks from file")
args = parser.parse_args()


def main():
    #sprawdzenie czy istnieje plik pod podana sciezka
    if Path(args.path).is_file():
        # odczytanie i transformacja do grayscale 
        img = plt.imread(args.path)
        grayscale_image = img[:, :, :3].mean(axis=2)
        with open(args.path,'r+b') as image_binary:
            # sprawdzenie sygnatury
            signature = image_binary.read(8)
            if signature == b'\x89PNG\r\n\x1a\n':
                #odczytanie danych z PNG - stworzenie dwoch podklas na chunki krytyczne i opcjonalne
                image = Image(image_binary)
                image.displayImageData()
                createFourierPlots(grayscale_image)

                # zapisanie zdjecia koncowego - z usunietymi wszystkimi chunkami dodatkowymi lub z pozostawionymi 3
                with open("output.png",'wb') as out_image:
                    out_image = image.restoreImage(out_image, signature, args.remove_all)
            else:
                print("Wrong file format!")
    else:
        print("Invalid path to file!")


if __name__ == '__main__':
    main()

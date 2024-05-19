import PIL
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import sys
from e_media1.chunksclasses import Chunk, CriticalChunks, AncillaryChunks, Image

parser = argparse.ArgumentParser(description="path to PNG file")
parser.add_argument('path',help = 'Path to PNG file')
parser.add_argument('-r','--removeAll',action='store_true',required=False,dest='remove_all',help="Remove all Ancillary Chunks from file")
args = parser.parse_args()






def performFourierTransform(img):
    ft = np.fft.fftshift(img)
    ft = np.fft.fft2(ft)
    return np.fft.fftshift(ft)

def performInverseFourierTransform(ft):
    ift = np.fft.ifftshift(ft)
    ift = np.fft.ifft2(ift)
    ift = np.fft.fftshift(ift)
    ift = ift.real
    return ift

def CompareTransformResults(base_img: np.array,img_after_transformations: np.array):
    diff = np.mean(np.abs(base_img-img_after_transformations))
    print(f"Diff: {round(diff,3)}")









def main():
    if Path(args.path).is_file():
        img = plt.imread(args.path)
        _image = img[:, :, :3].mean(axis=2)
        plt.set_cmap("gray")
        with open(args.path,'r+b') as image_binary:
            signature = image_binary.read(8)
            if signature == b'\x89PNG\r\n\x1a\n':
                image = Image(image_binary)
                image.criticalChunks.DecodeHeader()
                image.ancillaryChunks.readEXIF()
                with open("output.png",'wb') as out_image:
                    out_image = image.restoreImage(out_image,signature,args.remove_all)
                ft = performFourierTransform(_image)
                reversed_img = performInverseFourierTransform(ft)
                CompareTransformResults(_image,reversed_img)
                plt.subplot(131)
                plt.imshow(_image)
                plt.axis("off")
                plt.subplot(132)
                plt.imshow(np.log(abs(ft)))
                plt.axis("off")
                plt.subplot(133)
                plt.imshow(reversed_img)
                plt.axis("off")
                plt.show()      
            else:
                print("Wrong file format!")
    else:
        print("Invalid path to file!")


if __name__ == '__main__':
    main()

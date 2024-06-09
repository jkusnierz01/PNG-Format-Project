import numpy as np
import matplotlib.pyplot as plt
from e_media1.chunksclasses import Image
import logging

logger = logging.getLogger("loger")

def performFourierTransform(img:np.array) -> np.fft.fftshift:
    ft = np.fft.fftshift(img)
    ft = np.fft.fft2(ft)
    return np.fft.fftshift(ft)

def performInverseFourierTransform(ft:np.fft.fftshift) -> np.array:
    ift = np.fft.ifftshift(ft)
    ift = np.fft.ifft2(ift)
    ift = np.fft.fftshift(ift)
    ift = ift.real
    return ift

def CompareTransformResults(base_img: np.array,img_after_transformations: np.array) -> int:
    diff = np.mean(np.abs(base_img-img_after_transformations))
    return diff


def createFourierPlots(grayscale_img:np.array) -> None:
    logger.info("Creating Fourier Plots")
    ft = performFourierTransform(grayscale_img)
    reversed_img = performInverseFourierTransform(ft)
    diff = CompareTransformResults(grayscale_img,reversed_img)
    magnitude = 20*np.log10(np.abs(ft))
    phase = np.angle(ft)

    f1 = plt.figure(1)
    #oryginaly obraz w grayscale
    plt.subplot(131), plt.imshow(grayscale_img, cmap='gray'), plt.axis("off"),plt.title("Original Image")
    #magnitude fft
    plt.subplot(132),plt.imshow(magnitude, cmap='gray'),plt.axis("off"),plt.title("FFT Magnitude")
    #faza fft
    plt.subplot(133),plt.imshow(phase, cmap='gray'),plt.axis("off"),plt.title("FFT Phase")

    f2 = plt.figure(2)
    #oryginaly obraz w grayscale
    plt.subplot(121), plt.imshow(grayscale_img, cmap='gray'), plt.axis("off"),plt.title("Original Image")
    #obraz po odwrotnej transformacie fouriera
    plt.subplot(122),plt.imshow(reversed_img, cmap='gray'),plt.axis("off"), plt.title("Inversed FFT")
    # sprawdzenie rezultatów - porównanie wartości miedzy obrazem oryginalnym i po odwrotnej transformacie
    plt.figtext(x = 0.35, y=0.9,s = f"Difference between images: {np.around(diff,4)}")
    
    plt.show() 
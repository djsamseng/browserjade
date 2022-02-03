
import cv2
import numpy as np
from numba import cuda
from typing import Dict, NamedTuple
import generate


def generate_test_png():
    im = cv2.imread("./test.png")
    memory_shape = (1000, *im.shape)
    memory = np.zeros(memory_shape)
    generate.kernel(memory, chrome_video=im)
    np.testing.assert_array_equal(
        memory[0],
        im
    )

def generate_test_png_jit():
    im = cv2.imread("./test.png")
    memory_shape = (1000, *im.shape)
    memory = np.zeros(memory_shape)
    
    memory = cuda.to_device(memory)
    im = cuda.to_device(im)
    generate.kernel[32, 32](memory, im)

def non_jit_tests():
    generate_test_png()

def jit_tests():
    generate_test_png_jit()


def unit_test_main():
    # grab a picture of something and see if it can recreate it
    # using the state
    non_jit_tests()
    generate.do_jit()
    jit_tests()
    

if __name__ == "__main__":
    unit_test_main()

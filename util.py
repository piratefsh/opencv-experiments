import random

import cv2 
import numpy as np


def show(img, window_name='main'):
    # destroy existing window
    destroy(window_name)

    # show it
    cv2.imshow(window_name, img)

    # wait for key, then destroy it
    cv2.waitKey(0)
    destroy(window_name)

    return window_name

def destroy(window_name):
    cv2.destroyWindow(window_name)

# (Stolen) utility code from 
# http://git.io/vGi60A
def rectify(h):
    try:
        h = h.reshape((4,2))
    except ValueError:
        return np.array([None])
    hnew = np.zeros((4,2),dtype = np.float32)

    add = h.sum(1)
    hnew[0] = h[np.argmin(add)]
    hnew[2] = h[np.argmax(add)]

    diff = np.diff(h,axis = 1)
    hnew[1] = h[np.argmin(diff)]
    hnew[3] = h[np.argmax(diff)]

    return hnew

# draw contour on empty image
def draw_contour(c, i, h=500, w=300):
    dest = np.zeros((h,w), np.float32)
    cv2.drawContours(dest, c, i, 255, cv2.FILLED)
    return dest

def resize(src, shape):
    dest = cv2.resize(src, (shape[1], shape[0]))
    return dest

# get grayscale and slightly blurred image to remove noise
def preprocess(img):
    # grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # gaussian blur to remove noise
    blur = cv2.GaussianBlur(gray, ksize=(5, 5), sigmaX=0)

    return blur

    # inspired by http://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
def random_color_palette(n, BGR=True):
    """Generates a random, aesthetically pleasing set of n colors (list of BGR tuples - because opencv is silly - if BGR; else HSV)"""
    SATURATION = 0.6
    VALUE = 0.95
    GOLDEN_RATIO_INVERSE = 0.618033988749895

    # see: https://en.wikipedia.org/wiki/HSL_and_HSV#Converting_to_RGB
    def hsv2bgr(hsv):
        h, s, v = hsv
        # compute chroma
        c = v*s
        h_prime = h*6.0
        x = c*( 1 - abs(h_prime %2 - 1) )
        if h_prime >= 5: rgb = (c,0,x)
        elif h_prime >= 4: rgb = (x,0,c)
        elif h_prime >= 3: rgb = (0,x,c)
        elif h_prime >= 2: rgb = (0,c,x)
        elif h_prime >= 1: rgb = (x,c,0)
        else: rgb = (c,x,0)
        m = v-c
        rgb = tuple( 255.0*(val+m) for val in rgb )
        # flip tuple to return (B,G,R)
        return rgb[::-1]

    # random float in [0.0, 1.0)
    hue = random.random()
    l_hues = [hue]

    for i in range(n-1):
        # generate evenly distributed hues by random walk using the golden ratio!
        # (mod 1, to stay within hue space)
        hue += GOLDEN_RATIO_INVERSE
        hue %= 1
        l_hues.append(hue)

    if not BGR:
        return [ (h, SATURATION, VALUE) for h in l_hues ]

    return [ hsv2bgr((h, SATURATION, VALUE)) for h in l_hues ]


import sys

import cv2
#import cv2.cv as cv
import numpy as np 

from util import show, destroy


CARD_SIZE_WIDTH = 64 
CARD_SIZE_HEIGHT = 89
CARD_SIZE_RATIO = CARD_SIZE_WIDTH/CARD_SIZE_HEIGHT

test = 2

def canny(img):
    blurred = cv2.GaussianBlur(img, ksize=(5,5), sigmaX=0)
    edges = cv2.Canny(blurred, threshold1=200, threshold2=30)

    return edges 

def hough(edges, output, threshold):

    lines = cv2.HoughLines(edges, 1, np.pi/180, threshold)

    points = []

    if lines is None or len(lines) < 1:
        return points

    for rho, theta in lines[0]:
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a * rho 
        y0 = b * rho 

        x1 = int(x0 + 1000*(-b))
        y1 = int(y0 + 1000*(a))

        x2 = int(x0 - 1000*(-b))
        y2 = int(y0 - 1000*(a))

        # cv2.line(output, (x1,y1), (x2,y2), (0,0,255), 1)
        points.append((x1,y1,x2,y2))
    return points

def hough_p(edges, output, threshold, min_line_length, max_line_gap):

    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold, \
        min_line_length, max_line_gap)

    if lines is not None and len(lines) > 0:
        return lines[0]
    return []


def test(t, ml, mg):
    destroy('canny')
    # filename = 'images/brooklyn-bridge.jpg'
    filename = 'images/shapes.png'

    img = cv2.imread(filename, 0)
    print(img)
    color_img = cv2.imread(filename)
    canny_edges = canny(img)
    c = cv2.cvtColor(canny_edges, cv2.COLOR_GRAY2RGB)

    hough(canny_edges, c, t)
    lines, l_sum, l_avg = hough_p(canny_edges, c, t, ml, mg)
    print 'threshold: %d, min_line_len, %d, max_gap: %d\n%d lines found' \
        % (t, ml, mg, lines)
    print 'sum is %d' % l_sum
    print 'avg is %d' % l_avg

    show(c, 'canny')



def get_video(smoothing=5):

    lines_queue = []

    cv2.namedWindow('preview')
    vc = cv2.VideoCapture(0)

    if vc.isOpened():
        rval, frame = vc.read()
    else:
        rval = false

    while rval:
        key = cv2.waitKey(20)
        if key == 27:
            break

        canny_edges = canny(frame)

        f = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        f = cv2.addWeighted(f,0.7,canny_edges,0.3,0)
        f = cv2.cvtColor(f, cv2.COLOR_GRAY2RGB)

        # h = hough_p(canny_edges, f, 100, 10, 30)
        h = hough(canny_edges, f, 100)
        
        lines_queue.append(h)

        lines_img = np.zeros(canny_edges.shape, np.uint8) 

        # while we have less than 5 sets of lines in buffer, move on
        if len(lines_queue) < smoothing:
            continue
        else:

            # take last five frames
            for lines in lines_queue:
                for x1,y1,x2,y2 in lines:
                    cv2.line(lines_img, (x1,y1), (x2,y2), (255,255,255), 2)

            lines_queue.pop(0)

        cleaned_lines = cv2.bitwise_and(lines_img, canny_edges)
        cleaned_with_original = cv2.addWeighted(cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY), 0.3, cleaned_lines, 0.7, 0)

        cv2.imshow('preview', cleaned_with_original)
        rval, frame = vc.read()

    cv2.destroyWindow('preview')
    vc.release()



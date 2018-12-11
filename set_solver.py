import os
import sys

import cv2
#from cv2 import cv
import numpy as np

import util as util
import code
import set_constants as sc

#reload(util)

def resize_image(img, new_width=600):
    """Given cv2 image object and maximum dimension, returns resized image such that height or width (whichever is larger) == max dimension"""
    h, w, _ = img.shape
    
    new_height = int((1.0 * h/w) * new_width)
    resized = cv2.resize(img, (new_width, new_height))

    return resized

def get_card_properties(cards, training_set=None):
    if training_set == None:
        training_set = get_training_set()
    properties = []
    for img in cards:
        num = get_card_number(img)
        color = get_card_color(img)
        shape = get_card_shape(img, training_set)
        texture = get_card_texture(img)
        p = (num, color, shape, texture)
        if None not in p:
            properties.append(p) 
    return properties

def pretty_print_properties(properties):
    for p in properties:
        num, color, shape, texture = p
        print('%d %s %s %s' % (num, sc.PROP_COLOR_MAP[color],
                               sc.PROP_SHAPE_MAP[shape],
                               sc.PROP_TEXTURE_MAP[texture]))

def detect_cards(img, draw_rects=False, return_contours=False):
    if img is None:
        return None

    img_binary = get_canny(img)
    contours = get_contour_info(img_binary, discard=False, num=-1)[0]
    #contours = find_contours(img_binary)
    num_cards = get_dropoff([cv2.contourArea(c)
                             for c in contours], maxratio=1.5)
    cards = transform_cards(img, contours, num_cards, draw_rects=draw_rects)
    transformed_cards = transform_cards(img, contours, num_cards, draw_rects=draw_rects)

    if return_contours:
        return contours, transformed_cards
    else:
        return transformed_cards

def transform_cards(img, contours, num, draw_rects=False):
    cards = []
    for i in range(num):
        if i > len(contours) - 1:
            continue
        card = contours[i]

        # get bounding rectangle
        rect = cv2.minAreaRect(card)
        #r = cv.BoxPoints(rect)
        r = cv2.boxPoints(rect)

        # convert to ints
        r = [(int(x), int(y)) for x, y in r]

        if draw_rects:
            cv2.rectangle(img, r[0], r[2], sc.COLOR_RED)

        try:
            transformed = transform_card(card, img)
        except:
            # print('Error processing card!! :o')
            continue

        if transformed is not None:
            cards.append(transformed)

    return cards


def transform_card(card, image):
    # find out if card is rotated
    x, y, w, h = cv2.boundingRect(card)
    card_shape = [[0, 0], [sc.SIZE_CARD_W, 0], [
        sc.SIZE_CARD_W, sc.SIZE_CARD_H], [0, sc.SIZE_CARD_H]]

    # get poly of contour
    approximated_poly = get_approx_poly(card, do_rectify=True)

    if approximated_poly is None:
        # could not find card poly 
        return None

    dest = np.array(card_shape, np.float32)

    # do transformatiom
    transformation = cv2.getPerspectiveTransform(approximated_poly, dest)
    warp = cv2.warpPerspective(image, transformation, sc.SIZE_CARD)

    # rotate card back up
    if (w > h):
        return util.resize(np.rot90(warp), (sc.SIZE_CARD_H, sc.SIZE_CARD_W))

    return warp

def get_approx_poly(card, do_rectify=True, image=None):
    perimeter = cv2.arcLength(card, True)

    approximated_poly = cv2.approxPolyDP(card, 0.1*perimeter, True)

    # TODO: deal with case where approximated_poly does not have 4 points (3 or 5)
    #kl = len(approximated_poly)
    # kif l != 4:
    # kfor p in approximated_poly:
    #kcv2.circle(image, (p[0][0], p[0][1]), 3, (255,0,0), 5)
    # kutil.show(image)
    # k# get rectified points in clockwise order

    if do_rectify:
        reapproximated_poly = util.rectify(approximated_poly)
        if reapproximated_poly.all():
            approximated_poly = reapproximated_poly
        else:
            #print 'Not rectified!'
            return None
    return approximated_poly


def find_contours(bin_img, num=-1, return_area=False):
    _, contours, hierarchy = cv2.findContours(
        bin_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    if num > 0:
        return contours[:num]

    return contours


def get_binary(img, thresh=150):
    preprocessed = util.preprocess(img)
    _, threshold = cv2.threshold(
        preprocessed, thresh=thresh, maxval=255, type=cv2.THRESH_BINARY)
    return threshold


def get_canny(img):
    preprocessed = util.preprocess(img)
    canny = cv2.Canny(preprocessed, threshold1=200, threshold2=50)
    dilated = cv2.dilate(canny, (10, 10))
    return dilated


def get_card_color(card):
    card = get_shape_only(card)

    if card is None:
        return None

    #blue = [pix[0] for row in card for pix in row]
    #green = [pix[1] for row in card for pix in row]
    #red = [pix[2] for row in card for pix in row]
    #blue, green, red = zip(*(pix for row in card for pix in row)) 

    bgr = [min(_) for _ in zip(*(pix for row in card for pix in row))]
    #bgr = (min(blue), min(green), min(red))
    b, g, r = bgr
    # if mostly green
    if max(bgr) == g:
        return sc.PROP_COLOR_GREEN

    # if a lot more red than blue, is probably red
    if b != 0 and r/b > 2:
        return sc.PROP_COLOR_RED

    # else, probably purple
    return sc.PROP_COLOR_PURPLE


def get_card_shape(card, training_set, thresh=150):
    # binary = get_binary(card, thresh=thresh)
    binary = get_canny(card)
    contours = find_contours(binary)

    # if canny doesn't give enough contours, fallback to binary
    if len(contours) < 2:
        binary = get_binary(card)
        contours = find_contours(binary)
        # if still not enough contours, consider invalid
        if len(contours) < 2:
            return None

    poly = get_approx_poly(contours[1], do_rectify=False)

    # for each card in trainings set, find one with most similarity
    diffs = []
    this_shape = get_shape_contour(card)
    for i, that_shape in training_set.items():

        # resize image
        this_shape_res = util.resize(this_shape, that_shape.shape)

        # find diff and its sum
        d = cv2.absdiff(this_shape_res, that_shape)
        sum_diff = np.sum(d)

        diffs.append(sum_diff)

    # return index of shape that has minimum difference
    return diffs.index(min(diffs)) + 1

# get bounding rect coords
def get_shape_bounding_rect(img):
    binary = get_canny(img)
    contours = find_contours(binary)

    # if canny doesn't give enough contours, fallback to binary
    if len(contours) < 2:
        binary = get_binary(img)
        contours = find_contours(binary)
        if len(contours) < 2:
            return None

    shape_contour = contours[1]
    x, y, w, h = cv2.boundingRect(shape_contour)
    return (y, y+h, x, x+w, contours)

# cropped out contour of shape
def get_shape_contour(img):
    rect = get_shape_bounding_rect(img)

    if rect is None:
        return None

    y1, y2, x1, x2, contours = rect
    shape_img = util.draw_contour(contours, 1)
    cropped = shape_img[y1:y2, x1:x2]
    return cropped

# cropped out image of shape
def get_shape_only(img):
    rect = get_shape_bounding_rect(img)

    if rect is None:
        return None

    y1, y2, x1, x2, _ = rect
    cropped = img[y1:y2, x1:x2]
    return cropped

def get_training_set():
    # train cards
    shape_diamond = cv2.imread('images/training/diamond.jpg')
    shape_oblong = cv2.imread('images/training/oblong.jpg')
    shape_squiggle = cv2.imread('images/training/squiggle.jpg')
    training_set = do_training([shape_diamond, shape_oblong, shape_squiggle])
    return training_set


def do_training(imgs):
    # train for shapes, return contours of shapes
    training_set = {}
    for i in range(len(imgs)):
        img = imgs[i]
        shape = get_shape_contour(img)
        training_set[i] = shape
    return training_set


def get_dropoff(array, maxratio=1.1):
    """
    Given array of values, return the index of the element
    where the ratio of each elem to the next drops off (assuming sorted input)
    """

    array = [e for e in array if e > 0]

    ratios = np.divide(array, array[1:] + [1])

    count = 1

    for r in ratios:
        if r > maxratio:
            break
        else:
            count += 1

    return count


def get_card_number(card):
    binary = get_binary(card, thresh=180)
    contours = find_contours(binary)

    if len(contours) < 2:
        return None

    poly = get_approx_poly(contours[1], do_rectify=False)

    # forget about first outline of card
    contours_area = [cv2.contourArea(c) for c in contours][1:]

    return get_dropoff(contours_area, maxratio=1.1)


def get_card_texture(card, square=20):

    binary = get_binary(card, thresh=150)
    contours = find_contours(binary)

    if len(contours) < 2:
        return None

    contour = contours[1]

    # get bounding rectangle
    rect = cv2.boundingRect(contour)
    x, y, w, h = rect

    rect = cv2.getRectSubPix(card, (square, square), (x+w/2, y+h/2))

    gray_rect = cv2.cvtColor(rect, cv2.COLOR_RGB2GRAY)
    pixel_std = np.std(gray_rect)

    if pixel_std > 4.5:
        return sc.PROP_TEXTURE_STRIPED

    elif np.mean(gray_rect) > 150:
        return sc.PROP_TEXTURE_EMPTY

    else:
        return sc.PROP_TEXTURE_SOLID

def get_binary_from_hsv(card):
    # convert from BGR colorspace to HSV colorspace
    hsv = cv2.cvtColor(card, cv2.COLOR_BGR2HSV)

    # separate hue, saturation, and value into three images
    hue, sat, val = [np.array( [[col[i] for col in row] for row in hsv] )
                     for i in range(3)]

    # get binary representation of saturation image
    # higher threshold = less white
    _, bin_sat = cv2.threshold(np.array(sat), thresh=55, maxval=255,
        type=cv2.THRESH_BINARY)
    #bin_sat = cv2.GaussianBlur(bin_sat, ksize=(5, 5), sigmaX=0)

    # get binary representation of value image
    # higher threshold = more white
    _, bin_val = cv2.threshold(np.array(val), thresh=140, maxval=255,
        type=cv2.THRESH_BINARY_INV)

    bin_sat_val = cv2.bitwise_or(bin_sat, bin_val)

    # erosion followed by morphological opening to erase noise and fill gaps
    # in shapes
    kernel_e = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2,2))
    kernel_d = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(8,8))
    bin_sat_val = cv2.erode(bin_sat_val, kernel_e)
    bin_sat_val = cv2.morphologyEx(bin_sat_val, cv2.MORPH_CLOSE, kernel_d)

    return bin_sat_val, hue, sat, val

def get_contour_info(bin_img, remove_dups=True, discard=True, num=4):
    # find contours and get area
    contours = find_contours(bin_img, num)
    contour_areas = [cv2.contourArea(c) for c in contours]

    # if we've selected the outline of the card as a contour, discard
    if discard and contour_areas[0] > sc.SIZE_CARD_W * sc.SIZE_CARD_H * .9:
        contours = contours[1:]
        contour_areas = contour_areas[1:]

    # get bounding box and center point of each contour
    contour_boxes = [cv2.boundingRect(c) for c in contours]
    contour_centers = [(x+w/2, y+h/2) for x, y, w, h in contour_boxes]

    # remove duplicates (similar center point)
    # this is kinda poorly written, but basically we want to compare the
    # center-point of each contour to make sure we're not double-counting
    # any shapes. Might rewrite this later but probably won't
    if remove_dups:
        i = 0
        while i < len(contour_centers):

            c = contour_centers[i]
            found_dup = False

            for center in contour_centers[:i]:
                x_dist = abs(center[0] - c[0])
                y_dist = abs(center[1] - c[1])
                if np.sqrt(x_dist**2 + y_dist**2) < 30:
                    found_dup = True
                    break

            if found_dup:
                contours.pop(i)
                contour_areas.pop(i)
                contour_boxes.pop(i)
                contour_centers.pop(i)
            else:
                i += 1

    return contours, contour_areas, contour_boxes, contour_centers

def get_color_from_hue(hue):
    # get histogram of hue values
    hist, _ = np.histogram(hue, 15, (0, 255))

    if hist[3]+hist[4] > 1200:
        return sc.PROP_COLOR_GREEN
    elif hist[8]+hist[9] > 250:
        return sc.PROP_COLOR_PURPLE
    else:
        return sc.PROP_COLOR_RED


    # if sum(hist[130:181]) > 750:
    #     return sc.PROP_COLOR_PURPLE
    # elif sum(hist[40:81]) > 750:
    #     return sc.PROP_COLOR_GREEN
    # else:
    #     return sc.PROP_COLOR_RED

def get_texture_from_hue(hue, contour_box):
    # for convenience
    card_w = sc.SIZE_CARD_W
    card_h = sc.SIZE_CARD_H

    # uppack bounding box of contour
    x, y, w, h = contour_box

    # get a 20x20 square from each of the corners of the card, average values
    hue_bg = np.mean([
        hue[0:20, 0:20], hue[card_h-20:card_h, card_w-20:card_w],
        hue[0:20, card_w-20:card_w], hue[card_h-20:card_h, 0:20]])

    # get a 20x20 square from the center of the shape, average values
    hue_center = np.mean(hue[int(y+h/2-10):int(y+h/2+10),
                             int(x+w/2-10):int(x+w/2+10)])

    # guess texture based on ratio of inside to outside hues
    hue_ratio = max(hue_bg, hue_center) / min(hue_bg, hue_center)
    if hue_ratio < 1.3:
        return sc.PROP_TEXTURE_EMPTY
    elif hue_ratio < 2.8:
        return sc.PROP_TEXTURE_STRIPED
    else:
        return sc.PROP_TEXTURE_SOLID

def get_shape_from_contour(contour, contour_box):
    # uppack bounding box of contour
    x, y, w, h = contour_box

    # list of contours (only contains the first contour, really) shifted so
    # that they can be drawn in a box the size of the bounding box
    contours_shifted = [np.array(
        [[[j[0]-x, j[1]-y] for j in i] for i in contour])]

    # create image with filled contour
    shape_img = util.draw_contour(contours_shifted, 0, h, w)

    # for each card in trainings set, find one with most similarity
    diffs = []
    training_set = get_training_set()
    for i, shape_ref in training_set.items():

        # resize image
        shape_img_res = util.resize(shape_img, shape_ref.shape)

        # find diff and its sum
        d = cv2.absdiff(shape_img_res, shape_ref)
        sum_diff = np.sum(d)

        diffs.append(sum_diff)

    return diffs.index(min(diffs)) + 1

def get_card_properties_v2(card, debug=False):

    # convert to HSV colorspace and get binary representation of image
    bin_sat_val, hue, sat, val = get_binary_from_hsv(card)
    binary = cv2.bitwise_or(bin_sat_val, get_canny(card))

    # get contours from binary image
    contours, contour_areas, \
    contour_boxes, contour_centers = get_contour_info(binary, True)

    # crop image so we're only looking at the bounding rectangle
    x, y, w, h = contour_boxes[0]
    hue_crop = hue[y:y+h, x:x+w]

    #prop_num = get_number_from_contours(contour_areas, contour_centers)
    prop_num = get_dropoff([b[2]*b[3] for b in contour_boxes], maxratio=1.2)
    prop_col = get_color_from_hue(hue_crop)
    prop_shp = get_shape_from_contour(contours[0], contour_boxes[0])
    prop_tex = get_texture_from_hue(hue, contour_boxes[0])

    if debug:
        pretty_print_properties([(prop_num, prop_col, prop_shp, prop_tex)])
        util.show(card)

    return (prop_num, prop_col, prop_shp, prop_tex)

def get_cards_properties(cards):
    # if training_set == None:
    #     training_set = get_training_set()

    properties = []
    for card in cards:
        p = get_card_properties_v2(card)
        if None not in p:
            properties.append(p) 

    return properties

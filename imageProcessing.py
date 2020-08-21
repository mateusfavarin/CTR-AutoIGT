import cv2
import numpy as np

# CTR digit constants
DIGIT_WIDTH = 13
DIGIT_HEIGHT = 22
DIGIT_MULTIPLIER = 3
DIGIT_SIZE = (DIGIT_WIDTH, DIGIT_HEIGHT)
DIGIT_SIZE_HIGH = (DIGIT_WIDTH * DIGIT_MULTIPLIER, DIGIT_HEIGHT * DIGIT_MULTIPLIER)
KERNEL = np.ones((4, 4), np.uint8)

# Color constants
BLACK = 0
WHITE = 255
GRAY = 127

def detect_edges(img):
    ''' Detects edges from pictures of CTR digits.
        @param img: image of the CTR digit '''

    height, width = img.shape
    # Get the average color of the grayscale image
    color_mean = np.mean(img)
    color_mean *= 1.05

    # Loop every pixel
    for i in range(height):
        for j in range(width):
            # Select the darkest pixels as edges and color them black
            if img[i, j] >= color_mean:
                img[i, j] = WHITE
            else:
                img[i, j] = BLACK

    return img


def add_border(img):
    ''' Add a black border surrounding the digit, removing noise.
        @param img: image of the CTR digit '''

    height, width = img.shape

    # Calculating the mean distance of the border to the
    # black pixels surrounding the number
    left_mean = 0
    right_mean = 0
    # Number of valid black pixels detected
    right_row = 0
    left_row = 0

    # Looping every height
    # since we're starting with the right and left border
    for i in range(height):
        visited_left = False
        visited_right = False

        # Looping half of the width pixels to prevent
        # detecting black pixels in case of the image having holes
        # surrounding the edges of the number
        for j in range(width // 2):

            # If a black pixel is detected, j is its distance to the border
            # Lock the loop from detecting further pixels
            # by toogling the visited boolean
            if not visited_right and img[i, width - 1 - j] == BLACK:
                right_mean += j
                right_row += 1
                visited_right = True

            if not visited_left and img[i, j] == BLACK:
                left_mean += j
                left_row += 1
                visited_left = True

            # If both blacks were found, we can go to the next height
            if visited_left and visited_right:
                break

    # Same code as before, but now for the up and down sides
    up_mean = 0
    up_row = 0
    down_mean = 0
    down_row = 0
    for i in range(width):
        visited_up = False
        visited_down = False

        for j in range(height // 2):
            if not visited_down and img[height - 1 - j, i] == BLACK:
                down_mean += j
                down_row += 1
                visited_down = True

            if not visited_up and img[j, i] == BLACK:
                up_mean += j
                up_row += 1
                visited_up = True

            if visited_down and visited_up:
                break

    # We're safe to assume that the entire rectangle from the border
    # to the average value of the first black pixel is noise.
    # Thus, we remove it by making the entire rectangle be black.

    # Left and right sides
    for i in range(height):
        for j in range(max(right_mean // right_row, 1)):
            img[i, width - 1 - j] = BLACK
        for j in range(max(left_mean // left_row, 1)):
            img[i, j] = BLACK

    # Up and down sides
    for i in range(width):
        for j in range(max(down_mean // down_row, 1)):
            img[height - 1 - j, i] = BLACK
        for j in range(max(up_mean // up_row, 1)):
            img[j, i] = BLACK

    return img


def paint_colored_area(img, pixel, color_area, color_paint, diagonal=True):
    ''' Gets the colored area in a picture starting at pixel.
        @param img: image that you want to detect the area.
        @param pixel: tuple of the coordinates starting pixel.
        @param color_area: color of the areas that you want to find.
        @param color_paint: color that you want to paint the area.
        @param diagonal: set to True if you want to consider pixels in
        surrounding the diagonals as neighbors '''

    # Coordinates of the starting pixel
    (i, j) = pixel
    # Stack holds every single pixel that could have neighbors
    stack = []
    # Every pixel coordinates found in the area
    pixels = []

    # Paint the start pixel in order to avoid it being detected again
    img[i, j] = color_paint
    # Add start pixel to the stack, so you can start searching for neighbors
    stack.append((i, j))

    # While there are unverified pixels left
    while len(stack) > 0:
        # Get the next element to search for neighbors
        (i, j) = stack.pop(0)
        # Insert this pixel in the total
        # number of pixels in this area
        pixels.append((i, j))

        # Find more neighbors and store them in the stack
        if img[i - 1, j] == color_area:
            img[i - 1, j] = color_paint
            stack.append((i - 1, j))

        if img[i + 1, j] == color_area:
            img[i + 1, j] = color_paint
            stack.append((i + 1, j))

        if img[i, j - 1] == color_area:
            img[i, j - 1] = color_paint
            stack.append((i, j - 1))

        if img[i, j + 1] == color_area:
            img[i, j + 1] = color_paint
            stack.append((i, j + 1))

        if diagonal:
            if img[i + 1, j + 1] == color_area:
                img[i + 1, j + 1] = color_paint
                stack.append((i + 1, j + 1))

            if img[i - 1, j + 1] == color_area:
                img[i - 1, j + 1] = color_paint
                stack.append((i - 1, j + 1))

            if img[i + 1, j - 1] == color_area:
                img[i + 1, j - 1] = color_paint
                stack.append((i + 1, j - 1))

            if img[i - 1, j - 1] == color_area:
                img[i - 1, j - 1] = color_paint
                stack.append((i - 1, j - 1))

    return pixels


def detect_colored_areas(img, color_area, color_paint, color_rejected, size=150, diagonal=True):
    ''' Detects colored areas in a picture. This function doesn't check the pixels
        in the border of the picture.
        @param img: image that you want to extract the areas.
        @param color_area: color of the areas that you want to find.
        @param color_paint: color that you want to paint the area.
        @param color_rejected: color to paint every area that has color_area, but
        is less than your threshold size.
        @param size: minimum number of pixels required to be considered an area.
        @param diagonal: set to True if you want to consider pixels in
        surrounding the diagonals as neighbors '''

    height, width = img.shape
    # If the digit size is small, use a smaller threshold
    if height == DIGIT_HEIGHT:
        size = 20

    areas = []
    # Loop every single pixel in the image
    for i in range(1, height):
        for j in range(1, width):
            # If a good pixel was found
            if img[i, j] == color_area:
                # Detect the pixels in that area
                pixels = paint_colored_area(img, (i, j), color_area, color_paint, diagonal)

                # Once you have the area, if the size of it is less
                # than your threshold, then paint every pixel as rejected
                if len(pixels) < size:
                    for (pix_i, pix_j) in pixels:
                        img[pix_i, pix_j] = color_rejected
                else:
                    # Append pixels of that area to the total areas found
                    areas.append(pixels)

    return areas


def remove_noisy_areas(img):
    ''' Removes small white pixel areas from the picture.
        @param img: image of the CTR digit.
        @param size: size of the area. '''

    height, width = img.shape

    # Remove the smaller areas of the image. Default threshold is 150 pixels.
    # Areas too small usually are just noise, so removing helps cleaning up the image,
    # which helps predicting the right number.
    areas = detect_colored_areas(img, WHITE, GRAY, BLACK)
    for area in areas:
        paint_colored_area(img, area[0], GRAY, WHITE)

    # Dilate each white part of the picture. This helps witH glueing parts of the number
    # which are separated by a few black pixels, and also removes a bit of remaining noise.
    img = cv2.dilate(img, KERNEL, iterations=1)

    # If the height is the height of a digit that will be used for prediction
    if height != DIGIT_HEIGHT:

        # Adding a black border to the image
        for i in range(width):
            img[0, i] = BLACK
            img[height - 1, i] = BLACK
        for i in range(height):
            img[i, 0] = BLACK
            img[i, width - 1] = BLACK

        # Our dataset consists of CTR digits, which are unique and never changes.
        # However, depending on the capture card quality, the alligment of the Y axis
        # does change from video to video. So, in order to fix it and help getting a more
        # accurate prediction, I'm alligning the number with the top of the picture.

        # Variable to store the distance from the first WHITE pixel in the Y axis
        fix_height = 0
        # Looping every pixel, ignoring the border
        for i in range(1, height):
            found = False
            for j in range(1, width - 1):

                # Whenever you find a white pixel, the distance from where you start will be
                # y = the current height - 1, since we ignore the border
                if img[i, j] == WHITE:
                    fix_height = i - 1
                    found = True
                    break

            if found:
                break

        # If the distance from the first white pixel needs to be adjusted
        if fix_height > 0:

            # Move all pixels up, ignoring the border
            for i in range(1, height - fix_height):
                for j in range(1, width - 1):
                    img[i, j] = img[i + fix_height, j]

            # Erase the remaining pixels by painting them as BLACK
            for i in range(height - fix_height, height):
                for j in range(width):
                    img[i, j] = BLACK

    return img


def process_digit(digit):
    ''' Does all the pre-processing of a grayscale CTR digit.
        @param digit: grayscale image of a CTR digit '''

    digit = detect_edges(digit)
    digit = add_border(digit)
    digit = remove_noisy_areas(digit)

    return digit
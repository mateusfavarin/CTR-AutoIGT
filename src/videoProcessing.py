import cv2
import numpy as np
import pickle
from pywinauto import application

from imageProcessing import *

def in_range(n, a, b):
    ''' Checks if number is n in ]a, b[ '''

    if n > a and n < b:
        return True
    return False

def mean_hsv(v):
    ''' Calculates the mean color of a HSV picture.
        @param v: cv2 HSV picture. '''

    mean = 0
    for i in range(len(v)):
        for j in range(len(v[i])):
            mean += v[i][j][0]
    return mean / (len(v) * len(v[0]))

def load_video(file_path):
    ''' Opens a video using OpenCV2 library.
        @param file_path: path of the video file.'''

    # Loading the speedrun
    video = cv2.VideoCapture(file_path)
    # Reading the first frame for the first time
    status, original_frame = video.read()
    # Creating a grayscale copy
    frame = cv2.cvtColor(original_frame, cv2.COLOR_BGR2GRAY)
    # Getting information about the original height and width
    height, width = frame.shape

    return video, original_frame, frame, height, width

def close_video(video):
    ''' Closes a OpenCV2 video, as well as any cv2 window opened.
        @param video: cv2 video. '''

    video.release()
    cv2.destroyAllWindows()

def crop_video(file_path):
    ''' This function executes an user interface responsible for
        cropping the video file.
        @param file_path: path of the video file. '''

    video, original_frame, _, height, width = load_video(file_path)
    window_name = "Crop the game"

    # The idea is to bring the OpenCV2 window to focus
    # However, there's no native way of doing it inside OpenCV2's library
    # To achieve the same result, there's a hacky way using pywinauto
    # If I create a blank window, I can search for its name and focus it
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # Setting this blank window on focus
    app = application.Application()
    app.connect(title_re=window_name)
    app_dialog = app.top_window()
    app_dialog.set_focus()

    # The blank window always gets maximized when focused again.
    # To fix that, for some reason destroying the opencv2 window and
    # creating a new one will fix the window resolution, and also
    # create a new window already focused
    cv2.destroyAllWindows()

    # Values used to store the sub-window of the video window
    h1, h2, w1, w2 = 0, height, 0, width

    # Loop until user is done with cropping the speedrun
    done = False
    while not done:

        # Reset the video window to its original size
        h1, h2, w1, w2 = 0, height, 0, width
        while True:

            # Displays the updated version of the video file
            cv2.imshow(window_name, original_frame[h1:h2, w1:w2])
            key = cv2.waitKey(0) & 0xFF

            # User can crop the video file by using the keys WASD
            if key == ord('a') or key == ord('A'):
                w1 += 1
            if key == ord('w') or key == ord('W'):
                h1 += 1
            if key == ord('s') or key == ord('S'):
                h2 -= 1
            if key == ord('d') or key == ord('D'):
                w2 -= 1

            # User can quit the program using Q
            if key == ord('q') or key == ord('Q'):
                video.release()
                cv2.destroyAllWindows()
                quit()

            # User can reset the video window by pressing ESC
            if key == 27:
                cv2.destroyWindow(window_name)
                break

            # Pressing ENTER submits the cropping
            if key == 10 or key == 13:
                done = True
                cv2.destroyWindow(window_name)
                break

    close_video(video)

    return h1, h2, w1, w2

def process_video(file_path, h1, h2, w1, w2, version, category, stdscr):

    # Constants
    NUMBER_ONE_COORD = (
        (25, 35, 75, 85), # NTSC-U
        (30, 40, 75, 85), # PAL
        (25, 35, 75, 85), # NTSC-J
    )
    DIGIT_COORD = (
        ((10, 24), (9, 23), (10, 24)), # First digit; NTSC-U, PAL, NTSC-J
        ((35, 48), (32, 45), (30, 43)), # Second digit; NTSC-U, PAL, NTSC-J
        ((50, 63), (44, 57), (43, 56)), # Third digit; NTSC-U, PAL, NTSC-J
        ((74, 87), (65, 78), (64, 77)), # Fourth digit; NTSC-U, PAL, NTSC-J
        ((89, 102), (76, 91), (77, 90)), # Fifth digit; NTSC-U, PAL, NTSC-J
    )
    ROW_COORD = (
        (6, 28, 6, 28, 6, 28), # NTSC-U
        (5, 26, 4, 25, -1, 20), # PAL
        (6, 28, 6, 28, 6, 28), # NTSC-J
    )
    GAME_SIZE = (435, 323)
    X_BUTTON_COORD = (
        (290, 300, 170, 180), # NTSC-U
        (280, 290, 170, 180), # PAL
        (290, 300, 170, 180), # NTSC-J
    )
    IGT_COORD = (
        (10, 103, 288, 420), # NTSC-U
        (10, 93, 288, 407), # PAL
        (10, 103, 288, 420), # NTSC-J
    )
    HEIGHT_FIX = 0
    WIDTH_FIX = 0

    # Load video
    video, original_frame, frame, height, width = load_video(file_path)
    # Saving cropped frame
    original_frame = original_frame[h1:h2, w1:w2]
    # Saving cropped grayscale copy
    frame = frame[h1:h2, w1:w2]
    # Resize to match pixel positions
    original_frame = cv2.resize(original_frame, GAME_SIZE)
    frame = cv2.resize(frame, GAME_SIZE)
    # Update height and width
    height, width = frame.shape
    # Load machine learning model to predict the CTR digits
    model = pickle.load(open("CTR_digits.knn", 'rb'))
    # Variable that adjusts the cropping in the first race
    first_race = True
    # Variables to store the returning values
    igt = []
    times = []

    # Time set to ignore impossible frames between races, loads and hub movement
    timeout = 2100
    # Setting number of races of the speedrun
    num_races = 0
    if category == 0:
        num_races = 21
    elif category == 1:
        num_races = 16

    # Number of in game time screens found in the game
    igt_found = 0

    # While there are still in game time screens to be found
    while igt_found < num_races:

        # If you're in a timeout, ignore the frames
        if timeout > 0:
            status, original_frame = video.read()
            timeout -= 1
            # If the timeout is over
            if timeout == 0:
                # Apply transformations, since the last frame of the timeout
                # will be checked in the next iteration
                original_frame = original_frame[h1:h2, w1:w2]
                frame = cv2.cvtColor(original_frame, cv2.COLOR_BGR2GRAY)
                # Resize to match pixel positions
                original_frame = cv2.resize(original_frame, GAME_SIZE)
                frame = cv2.resize(frame, GAME_SIZE)
            continue

        # If the screen flashed white, the next frames may contain an in game time screen
        if np.mean(frame[0:50, 0:50]) > 200 and np.mean(frame[height - 50 : height, width - 50 : width]) > 200:

            # Store possible in game time images
            cache = []

            has_checked = False
            frame_window = 10
            # Check the next frames in the frame_window
            while True:

                # Crop the area of the blue X button
                x_continue = original_frame[X_BUTTON_COORD[version][0] : X_BUTTON_COORD[version][1], X_BUTTON_COORD[version][2] : X_BUTTON_COORD[version][3]]
                # Transform to HSV, so we can measure how blue the image is
                x_continue_hsv = cv2.cvtColor(x_continue, cv2.COLOR_BGR2HSV_FULL)
                # Calculate the mean value of the "h" (color)
                x_mean = mean_hsv(x_continue_hsv)

                # Crop the area of the top of the "1" number
                number_one = original_frame[NUMBER_ONE_COORD[version][0]: NUMBER_ONE_COORD[version][1], NUMBER_ONE_COORD[version][2] : NUMBER_ONE_COORD[version][3]]
                # Transform to HSV, so we can measure how yellow the image is
                number_one_hsv = cv2.cvtColor(number_one, cv2.COLOR_BGR2HSV_FULL)
                # Calculate the mean value of the "h" (color)
                one_mean = mean_hsv(number_one_hsv)

                # If the average color of the x button is blue enough AND
                # the average color of the top of the "1" is yellow enough
                if in_range(x_mean, 150, 200) and in_range(one_mean, 25, 55):

                    # You found a finish level screen
                    # Add the IGT crop to the cache
                    cache.append(frame[IGT_COORD[version][0] : IGT_COORD[version][1], IGT_COORD[version][2] : IGT_COORD[version][3]])

                status, original_frame = video.read()
                # Checking end of video
                if status == False:
                    break

                # Read new frame, crop and make a grayscale copy
                original_frame = original_frame[h1:h2, w1:w2]
                frame = cv2.cvtColor(original_frame, cv2.COLOR_BGR2GRAY)
                # Resize to match pixel positions
                original_frame = cv2.resize(original_frame, GAME_SIZE)
                frame = cv2.resize(frame, GAME_SIZE)

                frame_window -= 1
                # If you've checked every frame
                if frame_window == 0:

                    # If you already checked the next ten seconds, you're done in this loop
                    if has_checked:
                        break

                    # If you found an IGT match, you're done in this loop
                    if len(cache) > 0:
                        break

                    # If you didn't, check the next ten seconds,
                    # since some people may wait in the end without mashing X
                    frame_window = 300
                    has_checked = True

            # If you found any possible IGT match
            if (len(cache) > 0):

                # Find the "darkest" IGT image
                minimum = 160
                for img in cache:
                    if np.mean(img) < minimum and np.mean(img) > 70:
                        minimum = np.mean(img)
                        in_game_time = img

                # Set a timeout, you won't need to check end of race in the next 1:10
                timeout = 2100
                # Increase the number of IGT screens found
                igt_found += 1
                # Update the progress to the user
                stdscr.addstr(igt_found, 0, str(igt_found)+"/"+str(num_races)+" IGT screens found.")
                stdscr.refresh()

                # Crop the rows from the IGT screen
                rows = []
                for i in range(3):
                    # Variables to adjust the height of the rows
                    HEIGHT_FIX = 0
                    fixed_height = False

                    while True:

                        # Crop the row
                        row = in_game_time[26 * i + HEIGHT_FIX + ROW_COORD[version][2 * i] : 26 * i + HEIGHT_FIX + ROW_COORD[version][2 * i + 1], 0:]
                        # Crop the first digit of the row and process it
                        digit = row[0:, WIDTH_FIX + DIGIT_COORD[0][version][0] : WIDTH_FIX + DIGIT_COORD[0][version][1]]
                        digit = cv2.resize(digit, DIGIT_SIZE)
                        digit = process_digit(digit)

                        # The idea is to measure the distance from the borders of the
                        # digit to the first non black pixels of the number, and then
                        # try to allign the number. Width check is only done on the
                        # very first race, since having a 1 minute start lap will break
                        # this allignment algorithm.
                        # This fixes small misallignment in different capture card outputs

                        if not first_race:
                            # Calculating the distance from the up and down sides
                            dist_up = DIGIT_HEIGHT
                            dist_down = DIGIT_HEIGHT
                            for y in range(DIGIT_WIDTH):
                                visited_up = False
                                visited_down = False
                                for x in range(DIGIT_HEIGHT):
                                    if not visited_down and digit[DIGIT_HEIGHT - x - 1, y] != BLACK:
                                        dist_down = min(dist_down, x)
                                        visited_down = True

                                    if not visited_up and digit[x, y] != BLACK:
                                        dist_up = min(dist_up, x)
                                        visited_up = True

                                    if visited_down and visited_up:
                                        break

                            # Getting the maximum distance, i.e the side that needs
                            # to be corrected
                            temp = max(dist_up, dist_down)
                            fixed_height = True
                            # If the maximum distance is greater than this threadhold
                            if temp > 2:
                                # Adjust the height when cropping the digits
                                if temp == dist_up:
                                    HEIGHT_FIX = dist_up - 2
                                else:
                                    HEIGHT_FIX = 2 - dist_down

                        # If it's the first race, do a width check.
                        # Same code as for the up and down sides, except that this time
                        # we calculate the average distance of the pixels, instead of using
                        # the very first non black pixel as the total distance.

                        # I used different algorithms for the sides because they proved to
                        # be more effective after testing with multiple runs.
                        if first_race:
                            first_race = False

                            dist_right = DIGIT_WIDTH
                            dist_left = DIGIT_WIDTH
                            valid_right = 0
                            valid_left = 0

                            # Ignoring pixels too close to the border, since they usually are
                            # always black, which messes up with the average distance of the
                            # pixels that represents the number

                            for x in range(DIGIT_HEIGHT // 3, (DIGIT_HEIGHT * 2 // 3) + 1):
                                visited_right = False
                                visited_left = False
                                for y in range(DIGIT_WIDTH // 2):
                                    if not visited_left and digit[x, DIGIT_WIDTH - 1 - y] != BLACK:
                                        dist_left += y
                                        valid_left += 1
                                        visited_left = True

                                    if not visited_right and digit[x, y] != BLACK:
                                        dist_right += y
                                        valid_right += 1
                                        visited_right = True

                                    if visited_left and visited_right:
                                        break

                            # Calculating tyhe average distance
                            dist_right = dist_right // valid_right
                            dist_left = dist_left // valid_left

                            if dist_right > 2:
                                WIDTH_FIX = dist_right - 2
                            elif dist_left > 2:
                                WIDTH_FIX = 2 - dist_left

                        row = in_game_time[26 * i + HEIGHT_FIX + ROW_COORD[version][2 * i] : 26 * i + HEIGHT_FIX + ROW_COORD[version][2 * i + 1], 0:]

                        if fixed_height:
                            rows.append(row)
                            break

                # List to store each predicted digit
                lap_times = []
                for i in range(3):
                    for j in range(5):
                        digit = rows[i][0:, WIDTH_FIX + DIGIT_COORD[j][version][0] : WIDTH_FIX + DIGIT_COORD[j][version][1]] 
                        # Resizing each digit to make them bigger,
                        # and also make sure that they will have the same size for the KNN input.
                        digit = cv2.resize(digit, DIGIT_SIZE_HIGH)
                        # Process the digit before predicting
                        digit = process_digit(digit)
                        # Predict the number and store it
                        n = model.predict(np.reshape(digit, (1, digit.shape[0] * digit.shape[1])))
                        lap_times.append(n[0])

                # Storing final values
                times.append(lap_times)
                igt.append(in_game_time)

        # Read new frame, apply transformations and check the status of the video
        status, original_frame = video.read()
        if status == False:
            break
        original_frame = original_frame[h1:h2, w1:w2]
        frame = cv2.cvtColor(original_frame, cv2.COLOR_BGR2GRAY)

        # Resize to match pixel positions
        original_frame = cv2.resize(original_frame, GAME_SIZE)
        frame = cv2.resize(frame, GAME_SIZE)

    close_video(video)
    return times, igt
import curses
from cv2 import imshow, destroyAllWindows, waitKey

from sys import argv

from videoProcessing import *


def update_menu(stdscr, question, menu, index):
    ''' Refreshes and prints the current state of the menu in the terminal.
        @param stdscr: standart screen of curses.
        @param question: string to show on top of the selection.
        @param menu: possible options for the use to choose.
        @param index: current position of the menu '''

    stdscr.clear()
    stdscr.addstr(0, 0, question)
    x_text = 0
    for i in range(len(menu)):
        if i == index:
            stdscr.addstr(2, x_text, menu[i], curses.A_REVERSE)
        else:
            stdscr.addstr(2, x_text, menu[i])
        x_text += len(menu[i]) + 5

    stdscr.refresh()


def open_menu(stdscr, question, menu):
    ''' Creates a new selection menu.
        @param stdscr: standart screen of curses.
        @param question: string to show on top of the selection.
        @param menu: possible options for the use to choose. '''

    index = 0
    update_menu(stdscr, question, menu, index)
    while True:
        key = stdscr.getch()
        if key == curses.KEY_RIGHT:
            index = (index + 1) % len(menu)
            update_menu(stdscr, question, menu, index)
        elif key == curses.KEY_LEFT:
            index = (index - 1) % len(menu)
            update_menu(stdscr, question, menu, index)
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return index


def update_verification(stdscr, lap_times, index):
    ''' Refreshes the menu for verifying the in game time.
        @param stdscr: standart screen of curses.
        @param lap_times: array of the lap times predicted.
        @param index: current index in the menu '''

    y_text = 2
    x_text = 7
    for i in range(len(lap_times)):
        if i % 5 == 1 or i % 5 == 3:
            stdscr.addstr(y_text, x_text, ":")
            x_text += 2
        if i % 5 == 0:
            y_text += 1
            x_text = 7
        if i == index:
            stdscr.addstr(y_text, x_text, str(lap_times[i]), curses.A_REVERSE)
        else:
            stdscr.addstr(y_text, x_text, str(lap_times[i]))
        x_text += 2
    stdscr.refresh()


def verify_igt(stdscr, times, igt):
    ''' Menu for verifying the in game time of the run.
        @param stdscr: standart screen of curses.
        @param times: return of process_video()
        @param igt: return of process_video() '''

    DIGITS_PER_IGT = 15
    DIGITS_PER_LAP = 5
    numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    stdscr.clear()
    stdscr.addstr(0, 0, "Please verify each in game time screen. You can replace a number at any time.\nPress ENTER to submit the time. Hold Q to open and close the in game time picture.")
    stdscr.addstr(3, 0, "Lap 1:")
    stdscr.addstr(4, 0, "Lap 2:")
    stdscr.addstr(5, 0, "Lap 3:")
    index = 0

    # Looping every time found in the speedrun
    for i in range(len(times)):
        first_update = True
        while True:
            if first_update:
                first_update = False
                update_verification(stdscr, times[i], index)

            key = stdscr.getch()
            # If user press Q, the image appears. Q toggles to close as well.
            if key == ord('q') or key == ord('Q'):
                while True:
                    imshow("IGT", igt[i])
                    q_key = waitKey(5) & 0xFF
                    if q_key == ord('q') or q_key == ord('Q'):
                        destroyAllWindows()
                        break
            # Movement in the menu using the arrow keys.
            elif key == curses.KEY_RIGHT:
                index = (index + 1) % DIGITS_PER_IGT
                update_verification(stdscr, times[i], index)
            elif key == curses.KEY_LEFT:
                index = (index - 1) % DIGITS_PER_IGT
                update_verification(stdscr, times[i], index)
            elif key == curses.KEY_UP:
                index = (index - DIGITS_PER_LAP) % DIGITS_PER_IGT
                update_verification(stdscr, times[i], index)
            elif key == curses.KEY_DOWN:
                index = (index + DIGITS_PER_LAP) % DIGITS_PER_IGT
                update_verification(stdscr, times[i], index)
            # ENTER confirm the changes and submits
            elif key == curses.KEY_ENTER or key in [10, 13]:
                break
            # Digit keys are used to change the predictions in the menu
            for j in range(len(numbers)):
                if key == ord(numbers[j]):
                    times[i][index] = j
                    update_verification(stdscr, times[i], index)

    return times


def calculate_igt(stdscr, times):
    hours = 0
    minutes = 0
    seconds = 0
    miliseconds = 0
    for lap_times in times:
        for i in range(3):
            miliseconds += lap_times[4 + i * 5] + (10 * lap_times[3 + i * 5])
            if miliseconds > 99:
                miliseconds = miliseconds % 100
                seconds += 1
            seconds += lap_times[2 + i * 5] + (10 * lap_times[1 + i * 5])
            if seconds > 59:
                seconds = seconds % 60
                minutes += 1
            minutes += lap_times[0 + i * 5]
            if minutes > 59:
                minutes = minutes % 60
                hours += 1

    stdscr.clear()
    zero_minute = "" if minutes > 9 else "0"
    zero_second = "" if seconds > 9 else "0"
    zero_milisecond = "" if miliseconds > 9 else "0"
    if hours == 0:
        stdscr.addstr(0, 0, "Your in game time is: "+zero_minute+str(minutes)+":"+zero_second+str(seconds)+"."+zero_milisecond+str(miliseconds))
    else:
        stdscr.addstr(0, 0, "Your in game time is: "+str(hours)+zero_minute+str(minutes)+":"+zero_second+str(seconds)+"."+zero_milisecond+str(miliseconds))

def main(stdscr):

    # Getting the path of the speedrun file
    try:
        run_path = argv[1]

    except IndexError:

        # If there is no file, show error and tell user how to fix the issue
        stdscr.addstr(0, 0, "ERROR: No file was passed as an argument. Please call this program with the path to the speedrun video, or drag the video in the executable.\n\nPress ENTER to quit the program.")
        stdscr.refresh()

        # Waits for user to quit the program
        while True:
            key = stdscr.getch()
            if key == curses.KEY_ENTER or key in [10, 13]:
                return

    curses.curs_set(0)
    # If there is a file, display the main screen of the software
    # and instruction of how to proceed
    stdscr.addstr(0, 0, "╔═╗╔╦╗╦═╗   ╔═╗┬ ┬┌┬┐┌─┐╦╔═╗╔╦╗\n║   ║ ╠╦╝───╠═╣│ │ │ │ │║║ ╦ ║\n╚═╝ ╩ ╩╚═   ╩ ╩└─┘ ┴ └─┘╩╚═╝ ╩ v1.0\n\nPress ENTER to start cropping the game. Use the WASD keys to adjust the game window.\nIf you need to reset the window, press ESC at any time. Once you're done, press ENTER to submit.\nQ quits the program.")
    stdscr.refresh()

    while True:
        key = stdscr.getch()

        # When the user chooses to proceed
        if key == curses.KEY_ENTER or key in [10, 13]:

            # Open the interface to crop the game in the speedrun
            h1, h2, w1, w2 = crop_video(run_path)
            # Open the menu to select the game region
            version = open_menu(stdscr, "What version was this run played on?", ("NTSC-U", "PAL", "NTSC-J"))
            # Open the menu to select the run category
            category = open_menu(stdscr, "What is the category of this speedrun?", ("Any%", "All Cups"))
            # Tell the user that you're trying to find the in game time
            stdscr.clear()
            stdscr.addstr(0, 0, "Analizing the speedrun...")
            stdscr.refresh()
            # Get every single in game time and predict the digits
            times, igt = process_video(run_path, h1, h2, w1, w2, version, category, stdscr)
            # Open the menu for the user to verify the IGT
            times = verify_igt(stdscr, times, igt)
            # Calculate and displays the final in game time on the terminal
            calculate_igt(stdscr, times)

            stdscr.addstr(2, 0, "Press ESC to close the program.")
            stdscr.refresh()
            while True:
                key = stdscr.getch()
                if key == 27:
                    break
            curses.curs_set(1)
            return

        if key == ord('q') or key == ord('Q'):
            curses.curs_set(1)
            return


curses.wrapper(main)
# CTR-AutoIGT
The goal of this program is to automate the process of finding the in game time of a Crash Team Racing [speedrun](https://speedrun.com/ctr). Using a speedrun video file as an input, the software searches for blueprints of the end of race. When they match, the program captures the in game time screen and detects every single digit of the every lap time. After doing some image processing of each digit, the software uses machine learning to predict what number each digit represents. Once that's done, the user can verify and edit the results, and finally calculate the final time.

The machine learning algorithm used was k-nearest neighbors, and it was trained using a dataset of 756 digits among 6 different runs. The dataset, the labels and the training algorithm are in the `MachineLearning/` folder.

## Usage

Run the main script, giving the path to the speedrun video file as an argument.
> python main.py path/to/speedrun.mp4
The video quality needs to be at least 360p. Alternatively, you can use the latest release, drag and drop the video file in the executable.

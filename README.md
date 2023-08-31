# Fusion

Visible and Thermal Camera Fusion

## Table of Contents

- [Project Description](#project-description)
- [Features](#features)
- [User Set Up](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Usage](#usage)
- [Developer Set Up](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Usage](#usage)
- [Known issues](#knownissues)
- [Contact](#contact)

## Project Description

This application serves as a platform where users can seamlessly combine the outputs of two cameras – one capturing visible light and the other capturing thermal imagery. Within this platform, users have the ability to adjust the transparency of each camera's view, as well as experiment with features such as contouring, coloring, and other filters. Additionally, the application offers practical functions like saving snapshots and recording videos to enhance the overall user experience.

## Features

- Connect to various cameras which are supported by OpenCV platform.
- Contour objects seen by visible camera (Countour visible).
- Contour objects seen by thermal camera (Contour thermal).
- Enhance the gray scale thermal view by applying realistic color mapping (Color thermal).
- Extract only warm objects, color them and overlap the imagery on visible camera (ThermaVue).
- Take a snapshot of the live view and save it.
- Take a video of the live view and save it.
- Choose a directory where you want your files to be saved to.
- Choose the prefix of the file name.
- Choose a color theme (various modes for dark and light themes).

## User Set Up 

To use this program simply open the main.exe file. The program should be up and running in a few seconds. If the program crashes or does not load, it is most likely due to firewall settings, so make sure you give all permissions needed to run an executable file.

### Usage
The interface is quite easy to use and understand. Note that you first need to connect both cameras if you want to use any controls. You can use Contour Thermal and Contour Visible buttons at the same time. If you want so take a snapshot or record a video and save it, you first need to select the folder it is going to be saved to. However, you do not have to enter a file name prefix, if you leave it blanck, the imagery is going to be saved with a default name either fusionCapture or fusionVideoCapture. Moreover, you can switch anytime between color themes. For trouble shooting go to Known Issues section.

## Developer Set Up

To edit or develop this project further you will be required to install some libraries and run it on Windows. Run the program from the command line with "python main.py".

### Prerequisites

- Make sure you have configured python and pip on your computer.
- pip install PyQt5
- pip install qt-material
- pip install opencv-python
- pip install numpy


### Usage

- main.py: the driver of the whole application. It has two classes, one for creating and updating a video label and another one for managing the main window. The VideoLabel class has all the functionality needed to start a live camera stream, apply contouring and coloring algorithms. The MainWindow class sets up the PyQt window, packs all widgets and establishes a layout. Functions in this class have few basic purposes: create/update buttons, create/update trackbars, create/update labels, create combo boxes. The __init__ function of this class is the main function which is called for set up.
- variables.py: holds the global variables needed to run and update the main window. It is the bridge between the two classes (VideoLabel and MainWindow), thus enables communication.
- white.png: a light version of the logo picture.
- black.png: a dark version of the logo picture.

You can find notes for a developer by searching for "DEVELOPER NOTE" in main.py. Nevertheless, the code is well commented and should be more or less straight forward.

## Known Issues
- Camera support: this application only works for cameras supported by OpenCV platform. Usually these are the cameras, which appear under Imaging Devices in Device Manager. Any camera which runs on USB3 is probably not going to connect to this interface. In case you really need to connect a camera which is not supported currently you should modify the code, to connect to the mentioned camera through its official SDK or API and convert it to an OpenCV frame.
- File saving: usually should work fine, but if you can't find the files in the folder they were supposed to be saved to - it is most likely an internal issue with how an exe file is run and what permissions it has. If this happens, you can try searching for your files in  C:\VTRoot\HarddiskVolume4.
- Camera alignment: the cameras should be aligned physically and this could take a while. Take a warm object as a target and try to make them match. The code itself doesn't apply any transformations for the cameras like zooming, cutting, moving it by x/y points, except for a horizonal flip for one of the cameras which can be found and modified in main.py under DEVELOPER NOTE.
- Video speed: due to some internal processing missmatch with FPS of the cameras, the recorded video is played at around 1.25x its speed.
## Contact

E-mail: guoda.laurinaviciute@student.manchester.ac.uk | guodala@gmail.com 

GitHub: LaGuoda


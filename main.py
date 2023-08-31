"""
Author: Guoda Laurinaviciute
Date: 2023 - 08

Description: an interface which fuses thermal and visible cameras.

"""

from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5.QtMultimedia import QCameraInfo 
import numpy as np
from qt_material import apply_stylesheet
from PyQt5.QtCore import QTimer
import variables
import random
import string

''' Global variables for button flags and opacity trackbar value.
'''
variables.opacity = 50
variables.termo_flag = False
variables.vue_flag = False
variables.visible_flag =  False
variables.map_flag = False
variables.record_flag = False
variables.folder = None
variables.file_name = None
variables.picture = None
variables.termo = None
variables.visible = None
variables.start = False


class VideoLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        '''Initialises the video label. Connects to the cameras, sets the size of the window. 
        '''
        super(VideoLabel, self).__init__(parent)
        self.disply_width = 900
        self.display_height = 680
        self.setFixedSize(self.disply_width, self.display_height)
        self.setStyleSheet("background-color: #3e4147;")

        self.check_camera_timer = QtCore.QTimer(self)
        self.check_camera_timer.timeout.connect(self.check_camera_variables)
        self.check_camera_timer.start(10)
        
        self.termoCamera = None
        self.visibleCamera = None
        
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def check_camera_variables(self):
        '''Check the camera variables and connect to cameras if available.
        '''
        if variables.termo is not None and variables.visible is not None:
            self.termoCamera, self.visibleCamera = self.connectToCameras()
            self.check_camera_timer.stop()  
            self.timer.start(10)  

    def connectToCameras(self):
        '''Connects to the cameras.
        Output: camera1 and camera2.
        Note: if it does not connect to the correct cameras, change the CAM1 and CAM2 constants to other indexes.
        '''
        visible = cv2.VideoCapture(variables.termo, cv2.CAP_DSHOW)
        termo = cv2.VideoCapture(variables.visible, cv2.CAP_DSHOW)
        return visible, termo

    def isCapturingFrames(self, ret1, ret2):
        '''Checks if frames are captured correctly after obtaining a camera connection.
        Gives an error message if there is a problem with camera captures.
        '''

        if not ret1 or not ret2:
            error_message = "Failed to capture frames. One or both of the cameras are not connected properly."
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText(error_message)
            msg_box.setStandardButtons(QMessageBox.Close)
            msg_box.buttonClicked.connect(lambda button: QApplication.quit())
            
            msg_box.exec_()
            sys.exit(1)

    def highPassFilter(self, frame):
        '''High pass filter to contour the live video feed. It first applies Gaussian blur with 3x3 kernel, then applies the Sobel filter in x and y directions and calculates the square root of sum of squares. 
        Input: a single frame
        Output: a modified frame.
        '''
        yuvFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        gaussianFrame = cv2.GaussianBlur(yuvFrame, (5, 5), 0)
        sobel_x = cv2.Sobel(gaussianFrame, cv2.CV_64F, 1, 0, ksize = 3)
        sobel_y = cv2.Sobel(gaussianFrame, cv2.CV_64F, 0, 1, ksize = 3)
        squaredSobel = np.sqrt( sobel_x**2 + sobel_y**2 )
        squaredSobel = cv2.convertScaleAbs(squaredSobel)
        res = cv2.cvtColor(squaredSobel, cv2.COLOR_BGR2RGB)
        return res

    def applyThermalColorMap(self, frame):
        '''Applies the termal color mapping function from openCV to a current frame. The coloring is done based on pixel intensity.
        Input: current frame.
        Returns: colored frame.
        '''
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        colormap = cv2.applyColorMap(gray_frame, cv2.COLORMAP_JET)
        # colormap = 255 - colormap
        colormap = cv2.GaussianBlur(colormap, (3, 3), 0)
        return colormap

    def pureThermalOnVisible(self, frame):
        '''Thresholds a frame to achieve an image where the background is black and the objects are originally colored.
        '''
        '''DEVELOPER NOTE: threshold value for ThermaVue function is in this code snippet. The current value is a 100. Adjust it if needed. cv2.threshold(gray_frame, VALUE, 255, cv2.THRESH_BINARY)[1]
        '''
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mask = cv2.threshold(gray_frame, 100, 255, cv2.THRESH_BINARY)[1]
        inverted_mask = cv2.bitwise_not(mask)
        black_background = np.zeros_like(frame)
        result_frame = cv2.bitwise_and(frame, frame, mask = inverted_mask) + black_background
        return result_frame

    def toTransparentBackground(self, frame):
        '''Replaces the black background with a transparent background.
        '''
        temp = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, alpha = cv2.threshold(temp, 255, 0, cv2.THRESH_BINARY)
        b, g, r = cv2.split(frame)
        rgba = [b, g, r, alpha]
        dst = cv2.merge(rgba)
        return dst

    def convert4Channel(self, frame):
        '''Converts a 3-channel frame to a 4-channel frame. The 4th channel is required to regulate the opacity of the frame. 
        '''
        b, g, r = cv2.split(frame)
        alpha = np.full_like(b, 255, dtype = np.uint8)
        return cv2.merge((b, g, r, alpha))

    def toColoredObjects(self, frame):
        '''Color maps the non-black/non-transparent pixels. Uses a JET color map for a realistic 'thermal' view.
        '''
        b, g, r, a = cv2.split(frame)
        mask = np.any(frame[:, :, :3] != 0, axis = -1)
        jet_colormap = cv2.applyColorMap(np.arange(256, dtype=np.uint8), cv2.COLORMAP_JET)
        jet_colormap = jet_colormap
        jet_colormap = cv2.GaussianBlur(jet_colormap, (5, 5), 0)
        colored_pixels = jet_colormap[frame[:, :, 0], 0]

        r[mask] = colored_pixels[mask, 2]
        g[mask] = colored_pixels[mask, 1]
        b[mask] = colored_pixels[mask, 0]
        result_frame = cv2.merge((b, g, r, a))
        
        return result_frame

    def update_frame(self):
        '''Main logic of the program, controls the buttons and the view displayed on the video label.
        '''
        self.setStyleSheet("")
        variables.start = True
     
        # Read the camera stream
        ret1, visibleFrame = self.visibleCamera.read()
        ret2, termoFrame = self.termoCamera.read()
        
        # Check if the frames are being captured
        self.isCapturingFrames(ret1, ret2)

        ''' DEVELOPER NOTE:
            A horizontal flip for a visible camera, adjust as needed. Examples: 
                visibleFrame = cv2.flip(visibleFrame, 1)  - horizontal flip for visible camera
                termoFrame = cv2.flip(termoFrame, 1)  - horizontal flip for termo camera
                termoFrame = cv2.flip(termoFrame, 0)  - vertical flip flip for termo camera   
        '''
        visibleFrame = cv2.flip(visibleFrame, 1)
        

        # Resize both frames to 640x480
        termoFrame = cv2.resize(termoFrame, (640, 480))
        visibleFrame = cv2.resize(visibleFrame, (640, 480))

        # Creates two new frames with HPF applied. 
        visibleHPFFrame = self.highPassFilter(visibleFrame) 
        termoHPFFrame = self.highPassFilter(termoFrame)  

        # Adjust the color space, so they all match each other
        visibleFrame = cv2.cvtColor(visibleFrame, cv2.COLOR_BGR2RGB)
        termoFrame = cv2.cvtColor(termoFrame, cv2.COLOR_BGR2RGB)
        termoHPFFrame = cv2.cvtColor(termoHPFFrame, cv2.COLOR_BGR2RGB)

        # Get the value of the opacity from the trackbar
        opacity = variables.opacity / 100.0

        # If thermaVue mode is of
        if variables.vue_flag == False:
            # If no buttons are pressed
            if not variables.termo_flag and not variables.visible_flag and not variables.map_flag:
                fusedFrame = cv2.addWeighted(visibleFrame, 1 - opacity, termoFrame, opacity, 0)
            # If if map button is pressed
            elif not variables.termo_flag and not variables.visible_flag and variables.map_flag:
                mappedFrame = self.applyThermalColorMap(termoFrame)
                fusedFrame = cv2.addWeighted(visibleFrame, 1 - opacity, mappedFrame, opacity, 0)
            # If visible contouring is on
            elif not variables.termo_flag and variables.visible_flag and not variables.map_flag:
                fusedFrame = cv2.addWeighted(visibleHPFFrame, 1 - opacity, termoFrame, opacity, 0)
            # If visible contour and color mapping is on at the same time
            elif not variables.termo_flag and variables.visible_flag and variables.map_flag:
                mappedFrame = self.applyThermalColorMap(termoFrame)
                fusedFrame = cv2.addWeighted(visibleHPFFrame, 1 - opacity, mappedFrame, opacity, 0)
            # If contour termo is on
            elif variables.termo_flag and not variables.visible_flag and not variables.map_flag:
                fusedFrame = cv2.addWeighted(visibleFrame, 1 - opacity, termoHPFFrame, opacity, 0)
            # If contour termo and color mapping is on at the same time
            elif variables.termo_flag and not variables.visible_flag and variables.map_flag:
                fusedFrame = cv2.addWeighted(visibleFrame, 1 - opacity, termoHPFFrame, opacity, 0)
                fusedFrame = self.applyThermalColorMap(fusedFrame)
                fusedFrame = 255 - fusedFrame
            # If both termo and visible contouring is on at the same time
            elif variables.termo_flag and variables.visible_flag and not variables.map_flag:
                fusedFrame = cv2.addWeighted(visibleHPFFrame, 1 - opacity, termoHPFFrame, opacity, 0)
            # If all three buttons are on at the same time
            elif variables.termo_flag and variables.visible_flag and variables.map_flag:
                fusedFrame = cv2.addWeighted(visibleHPFFrame, 1 - opacity, termoHPFFrame, opacity, 0)
                fusedFrame = self.applyThermalColorMap(fusedFrame)
                fusedFrame = 255 - fusedFrame
        # If thermaVue mode is on
        elif variables.vue_flag == True:
            bwFrame = self.pureThermalOnVisible(255 - termoFrame)
            coloredBWFrame = self.applyThermalColorMap(bwFrame)  
            transparentColoredBWFrame = self.toTransparentBackground(coloredBWFrame)
            transparentBWFrame = self.toTransparentBackground(bwFrame) 
            transparentRED = self.toColoredObjects(transparentBWFrame)
            op1 = self.convert4Channel(visibleFrame)
            op2 = transparentRED
            fused = cv2.addWeighted(op2, 1, op1, 1, 0)
            fusedFrame =  cv2.cvtColor(fused, cv2.COLOR_BGR2RGB)
        
        # Convert the image from openCV format, to a format which can be processed with PyQT5
        qt_img = self.convert_cv_qt(fusedFrame)
        #Display the frame
        self.setPixmap(qt_img)
        variables.picture = qt_img

    def convert_cv_qt(self, cv_img):
        '''Convert from an opencv image to QPixmap'''
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)



class MainWindow(QtWidgets.QMainWindow):
    def trackbar_changed(self, value):
        '''Trackbar callback function. Displays the value of the trackbar on the status bar.
        Also updates the global opacity value variable. '''
        if not self.ter_connected or not self.vi_connected:
            self.status.showMessage("Cameras are not connected. Please connect before using controls.")
        else:
            self.status.showMessage(f'Trackbar Value: {value}')
            variables.opacity = value

    def termo_clicked(self):
        ''' Thermo button callback function. Updates the on/off flag and appearance'''
        if not self.ter_connected or not self.vi_connected:
            self.status.showMessage("Cameras are not connected. Please connect before using controls.")
            self.button_termo.setChecked(False)
        else:    
            variables.termo_flag = not variables.termo_flag
            self.button_termo.setChecked(variables.termo_flag)
   
    def visible_clicked(self):
        ''' Visible button callback function. Updates the on/off flag and appearance'''
        if not self.ter_connected or not self.vi_connected:
            self.status.showMessage("Cameras are not connected. Please connect before using controls.")
            self.button_visible.setChecked(False)
        else:
            variables.visible_flag = not variables.visible_flag
            self.button_visible.setChecked(variables.visible_flag)

    def map_clicked(self):
        ''' Map colour button callback function. Updates the on/off flag and appearance'''

        if not self.ter_connected or not self.vi_connected:
            self.status.showMessage("Cameras are not connected. Please connect before using controls.")
            self.button_map.setChecked(False)
        else:
            variables.map_flag = not variables.map_flag
            self.button_map.setChecked(variables.map_flag)

            # Disable other buttons
            self.button_termo.setEnabled(not variables.map_flag)
            self.button_visible.setEnabled(not variables.map_flag)
            self.button_vue.setEnabled(not variables.map_flag)
            self.button_termo.setChecked(False)
            self.button_visible.setChecked(False)

    def vue_clicked(self):
        ''' ThermaVue button callback function. Updates the on/off flag and appearance'''
        if not self.ter_connected or not self.vi_connected:
            self.status.showMessage("Cameras are not connected. Please connect before using controls.")
            self.button_vue.setChecked(False)
        else:
            variables.vue_flag = not variables.vue_flag
            self.button_vue.setChecked(variables.vue_flag)

            # Disable the trackbar
            self.trackbar.setEnabled(not variables.vue_flag) 
            self.trackbar.setStyleSheet("padding:10px 227px 10px 227px; QSlider::sub-page:disabled { background-color: gray; }")

            # Disable other buttons
            self.button_termo.setEnabled(not variables.vue_flag)
            self.button_visible.setEnabled(not variables.vue_flag)
            self.button_map.setEnabled(not variables.vue_flag)
            self.button_termo.setChecked(False)
            self.button_visible.setChecked(False)

    def save_picture(self):
        ''' Saves the snapshot to specified directory + file name. If the directory is not specified a user gets propmpted with an error message. If a user doesn't update the file prefix, the picture is saved with a default name.
        '''
        if not self.ter_connected or not self.vi_connected:
            self.status.showMessage("Cameras are not connected. Please connect before using controls.")
        else:
            file_path = variables.folder
            file_name = variables.file_name
            picture = variables.picture

            characters =  string.digits
            random_string = ''.join(random.choice(characters) for _ in range(4))

            if file_path == None:

                message_box = QMessageBox()
                message_box.setWindowTitle("Error")
                message_box.setText("Please select the directory where you want the file to be saved")
                message_box.setIcon(QMessageBox.Warning)
                message_box.exec_()
                
            else:
                if file_name == None:
                    file_name = "fusionCapture" + "_" + random_string
                    
                else:
                    file_name = file_name + "_" + random_string
                full_file_path = f"{file_path}/{file_name}.png"
        
                picture.save(full_file_path, "PNG")
                message_box = QMessageBox()
                message_box.setWindowTitle("Picture Saved")
                message_box.setText(f"Picture saved at:\n{full_file_path}")
                message_box.setIcon(QMessageBox.Information)
                message_box.exec_()

    def create_buttons(self, controls_layout):
        ''' Creates 3 buttons for thermo countouring, visible contouring and ThermaVue. Also adds them to a layout to be displayed on the screen.
        '''
        self.button_termo = QtWidgets.QPushButton("Contour Thermal") 
        self.button_termo.setFixedSize(200, 50)
        self.button_termo.setCheckable(True)  
        self.button_termo.setChecked(variables.termo_flag)  
        self.button_termo.clicked.connect(self.termo_clicked) 

        self.button_visible = QtWidgets.QPushButton("Contour Visible")
        self.button_visible.setFixedSize(200, 50)
        self.button_visible.setCheckable(True)
        self.button_visible.setChecked(variables.visible_flag)
        self.button_visible.clicked.connect(self.visible_clicked)

        self.button_map = QtWidgets.QPushButton("Color Thermal")
        self.button_map.setFixedSize(200, 50)
        self.button_map.setCheckable(True)
        self.button_map.setChecked(variables.map_flag)
        self.button_map.clicked.connect(self.map_clicked)

        self.button_vue = QtWidgets.QPushButton("ThermaVue")
        self.button_vue.setFixedSize(200, 50)
        self.button_vue.setCheckable(True)
        self.button_vue.setChecked(variables.vue_flag)
        self.button_vue.clicked.connect(self.vue_clicked)

        controls_layout.addWidget(self.button_termo)
        controls_layout.addWidget(self.create_spacer(10, 3))
        controls_layout.addWidget(self.button_visible)
        controls_layout.addWidget(self.create_spacer(10, 3))
        controls_layout.addWidget(self.button_map)
        controls_layout.addWidget(self.create_spacer(10, 3))
        controls_layout.addWidget(self.button_vue)

    def create_control_buttons(self, save_rec_layout):
        ''' Creates two more buttons for saving a snapshot and recording a video.
        '''
        self.button_save = QtWidgets.QPushButton("Save")
        self.button_save.setFixedSize(70, 70)
        self.button_save.clicked.connect(self.save_picture)

        self.button_record = QtWidgets.QPushButton("Rec")
        self.button_record.setFixedSize(70, 70)
        self.button_record.setCheckable(True)
        self.button_record.setChecked(variables.record_flag)
        self.button_record.clicked.connect(self.toggle_video_recording)

        save_rec_layout.addWidget(self.button_save)
        save_rec_layout.addWidget(self.button_record)

    def create_logo_label(self, controls_layout):
        ''' Creates a logo label which displayes Ados-Tech logo from an image image.jpg
        '''
        self.logo_image = QtGui.QPixmap("white.png")
        self.logo_label = QtWidgets.QLabel()
        self.logo_label.setPixmap(self.logo_image)
        self.logo_label.setFixedSize(200, 37)
        controls_layout.addWidget(self.logo_label)

    def create_a_trackbar(self, bottom_layout):
        ''' Creates a trackbar to change the opacity of each camera. 
        '''
        self.trackbar = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.trackbar.setRange(0, 100)
        self.trackbar.setValue(50)
        self.trackbar.setStyleSheet("padding:10px 227px 10px 227px;")
        self.trackbar.valueChanged.connect(self.trackbar_changed) 
        bottom_layout.addWidget(self.trackbar)

    def create_a_statusbar(self, bottom_layout):
        ''' Creates a status bar (the one on the bottom of the screen) 
        '''
        self.status = QtWidgets.QStatusBar()
        self.status.setStyleSheet("color : gray;")
        self.setStatusBar(self.status)
        self.status.showMessage('Waiting for camera connection..')
        bottom_layout.addWidget(self.status)

    def create_spacer(self, w, h):
        ''' A function to get a universal spacer. Makes an empty label of the dimentions w - width, h - height. 
        '''
        spacer = QtWidgets.QLabel()
        spacer.setFixedSize(w, h)
        # spacer.setStyleSheet("background-color: #a5a5a5;")
        return spacer

    def change_logo_image(self, new_image_path):
        new_pixmap = QtGui.QPixmap(new_image_path)
        self.logo_label.setPixmap(new_pixmap)

    def combo_box_selected(self, index):
        ''' A callback function for a combo box. Reads in the option that has been selected and updates the color theme according to it. 
        '''
        selected_option = self.sender().currentText()
    
        # Change the empty video_label appearance & logo according to theme (light/dark)
        if selected_option[0] ==  "D":
            self.video_label.setStyleSheet("background-color: #3e4147;")
            self.change_logo_image("white.png")

        elif selected_option[0] == "L":
            self.video_label.setStyleSheet("background-color: #c4c4c4;")
            self.change_logo_image("black.png")

        else:
            print("Error in handling the video_label adjustment according to theme setting.")


        if selected_option == "Dark Amber":
            apply_stylesheet(self, theme = 'dark_amber.xml')

        elif selected_option == "Dark Blue":
            apply_stylesheet(self, theme = 'dark_blue.xml')

        elif selected_option == "Dark Light Green":
            apply_stylesheet(self, theme = 'dark_lightgreen.xml')

        elif selected_option == "Dark Pink":
            apply_stylesheet(self, theme = 'dark_pink.xml')

        elif selected_option == "Dark Purple":
            apply_stylesheet(self, theme = 'dark_purple.xml')

        elif selected_option == "Dark Red":
            apply_stylesheet(self, theme = 'dark_red.xml')

        elif selected_option == "Dark Teal":
            apply_stylesheet(self, theme = 'dark_teal.xml')

        elif selected_option == "Dark Yellow":
            apply_stylesheet(self, theme = 'dark_yellow.xml')

        elif selected_option == "Light Amber":
            apply_stylesheet(self, theme = 'light_amber.xml')

        elif selected_option == "Light Blue":
            apply_stylesheet(self, theme = 'light_blue.xml')

        elif selected_option == "Light Cyan":
            apply_stylesheet(self, theme = 'light_cyan.xml')

        elif selected_option == "Dark Cyan":
            apply_stylesheet(self, theme = 'dark_cyan.xml')

        elif selected_option == "Light Light Green":
            apply_stylesheet(self, theme = 'light_lightgreen.xml')

        elif selected_option == "Light Pink":
            apply_stylesheet(self, theme = 'light_pink.xml')

        elif selected_option == "Light Purple":
            apply_stylesheet(self, theme = 'light_purple.xml')

        elif selected_option == "Light Red":
            apply_stylesheet(self, theme = 'light_red.xml')

        elif selected_option == "Light Teal":
            apply_stylesheet(self, theme = 'light_teal.xml')

        elif selected_option == "Light Yellow":
            apply_stylesheet(self, theme = 'light_yellow.xml')

    def choose_theme(self, other_info):
        ''' Creates a combo box which allows the user to choose from various color themes. 
        '''
        combo_box = QComboBox()
        combo_box.setFixedSize(200, 30)
        combo_box.setStyleSheet("QComboBox { color: gray; } QComboBox QAbstractItemView { color: gray; } QComboBox::item:selected { background-color: gray; }")


        combo_box.addItem("Dark Amber")
        combo_box.addItem("Dark Blue")
        combo_box.addItem("Dark Cyan")
        combo_box.addItem("Dark Light Green")
        combo_box.addItem("Dark Pink")
        combo_box.addItem("Dark Purple")
        combo_box.addItem("Dark Red")
        combo_box.addItem("Dark Teal")
        combo_box.addItem("Dark Yellow")
        combo_box.addItem("Light Amber")
        combo_box.addItem("Light Blue")
        combo_box.addItem("Light Cyan")
        combo_box.addItem("Light Light Green")
        combo_box.addItem("Light Pink")
        combo_box.addItem("Light Purple")
        combo_box.addItem("Light Red")
        combo_box.addItem("Light Teal")
        other_info.addWidget(combo_box)
        combo_box.currentIndexChanged.connect(self.combo_box_selected)
    
    def theme_label(self, other_info, name):
        ''' A label for color theme combo box.
        '''
        label = QtWidgets.QLabel(name)
        label.setFixedSize(200, 20)
        other_info.addWidget(label)

    def choose_file_path(self, other_info):
        self.file_path_input = QLineEdit(self)
        self.file_path_input.setFixedSize(200, 30)
        other_info.addWidget(self.file_path_input)

        browse_button = QPushButton("Browse", self)
        browse_button.setFixedSize(100, 30)
        browse_button.clicked.connect(self.handle_folder_input)
        other_info.addWidget(browse_button)
        
    def handle_folder_input(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        variables.folder = folder_path
        if folder_path:
            self.file_path_input.setText(folder_path)

    def choose_file_name(self, other_info):
        self.file_name = QLineEdit()
        self.file_name.setFixedSize(200, 30)
        self.file_name.setPlaceholderText("Enter file name")
        self.file_name.textChanged.connect(self.handle_file_input)
        other_info.addWidget(self.file_name)

    def handle_file_input(self, new_file):
        variables.file_name = new_file
        
    def combo_box_for_termo(self, other_info):
        combo_box = QComboBox()
        combo_box.setStyleSheet("QComboBox { color: gray; } QComboBox QAbstractItemView { color: gray; } QComboBox::item:selected { background-color: gray; }")
        combo_box.setFixedSize(200, 30)
        available_cameras = QCameraInfo.availableCameras()
        combo_box.addItem("")
        if available_cameras:
            for idx, camera in enumerate(available_cameras):
                camera_name_with_index = f"{idx + 1}: {camera.description()}"
                combo_box.addItem(camera_name_with_index, camera)
        else:
            combo_box.addItem("No cameras found")
        
        other_info.addWidget(combo_box)
        combo_box.currentIndexChanged.connect(self.handle_termo)

    def combo_box_for_visible(self, other_info):
        combo_box = QComboBox()
        combo_box.setStyleSheet("QComboBox { color: gray; } QComboBox QAbstractItemView { color: gray; } QComboBox::item:selected { background-color: gray; }")
        combo_box.setFixedSize(200, 30)
        available_cameras = QCameraInfo.availableCameras()
        combo_box.addItem("")
        if available_cameras:
            for idx, camera in enumerate(available_cameras):
                camera_name_with_index = f"{idx + 1}: {camera.description()}"
                combo_box.addItem(camera_name_with_index, camera)
        else:
            combo_box.addItem("No cameras found")
        
        other_info.addWidget(combo_box)
        combo_box.currentIndexChanged.connect(self.handle_visible)

    def handle_visible(self, index):
        self.vi_connected = True
        selected_option = self.sender().currentText()
        if selected_option != "":
            if self.ter_connected == False:
                self.status.showMessage('Connected to Visible Camera. Cameras connected 1/2 ...')
            else:
                self.status.showMessage('Connection to both cameras is successful.')
            variables.visible = int(selected_option[0]) - 1

    def handle_termo(self):
        self.ter_connected = True
        selected_option = self.sender().currentText()
        if selected_option != "":
            if self.vi_connected == False:
                self.status.showMessage('Connected to Thermal Camera. Cameras connected 1/2 ...')
            else:
                self.status.showMessage('Connection to both cameras is successful.')
            variables.termo = int(selected_option[0]) - 1

    def record_frame(self):
        current_frame = variables.picture 
        self.frames.append(current_frame)

    def toggle_video_recording(self):
        if not self.ter_connected or not self.vi_connected:
            self.status.showMessage("Cameras are not connected. Please connect before using controls.")
            self.button_record.setChecked(False)
        else:
            if variables.folder == None:
                if self.button_record.isChecked():
                    self.button_record.setChecked(False)
                message_box = QMessageBox()
                message_box.setWindowTitle("Error")
                message_box.setText("Please select the directory where you want the file to be saved")
                message_box.setIcon(QMessageBox.Warning)
                message_box.exec_()
            
            else:
                if self.button_record.isChecked():
                    self.start_video_recording()
                    self.button_record.setText("Stop")

                else:
                    self.stop_video_recording()
                    self.button_record.setText("Rec")

    def stop_video_recording(self):
        self.recording = False
        file_path = variables.folder
        file_name = variables.file_name

        characters =  string.digits
        random_string = ''.join(random.choice(characters) for _ in range(4))

        if file_name == None:
                file_name = "fusionVideoCapture" + "_" + random_string
                
        else:
            file_name = file_name + "_" + random_string

        full_file_path = f"{file_path}/{file_name}.mp4"
    
        if len(self.frames) > 0:
            height, width = self.frames[0].height(), self.frames[0].width()
    
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(full_file_path, fourcc, 24, (width, height))
            for frame in self.frames:
                frame_np = self.qPixmapToMat(frame)
                out.write(frame_np)

            out.release()

        message_box = QMessageBox()
        message_box.setWindowTitle("Picture Saved")
        message_box.setText(f"Picture saved at:\n{full_file_path}")
        message_box.setIcon(QMessageBox.Information)
        message_box.exec_()     

    def qPixmapToMat(self, pixmap):
        qimage = pixmap.toImage()
        width, height = qimage.width(), qimage.height()
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        arr = np.array(ptr).reshape(height, width, 4)  
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR) 

    def start_video_recording(self):
        self.recording = True
        self.frames = [] 
        self.video_timer.start(int(1000 /24))  
        
    def __init__(self):
        ''' Main function where all the layout is determined. 
        '''
        self.vi_connected = False
        self.ter_connected = False

        super(MainWindow, self).__init__()
        self.setWindowTitle("Fusion")
        apply_stylesheet(self, theme='dark_cyan.xml')

        # Create a central widget for the main window
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)

        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.record_frame)
        self.recording = False
        self.frames = []

        # Create layouts for the main window
        main_layout = QtWidgets.QVBoxLayout()
        top_layout = QtWidgets.QHBoxLayout()
        bottom_layout = QtWidgets.QVBoxLayout()
        save_rec_layout = QtWidgets.QHBoxLayout()
        controls_layout = QtWidgets.QVBoxLayout()
        other_info = QtWidgets.QVBoxLayout()

        # save_rec layout
        self.video_label = VideoLabel(central_widget)
        self.create_control_buttons(save_rec_layout)

        # other_info layout
        self.theme_label(other_info, "SELECT THERMO CAMERA")
        self.combo_box_for_termo(other_info)
        other_info.addWidget(self.create_spacer(200, 10))

        self.theme_label(other_info, "SELECT VISIBLE CAMERA")
        self.combo_box_for_visible(other_info)
        other_info.addWidget(self.create_spacer(200, 10))

        self.theme_label(other_info, "FILE SAVE PATH")
        self.choose_file_path(other_info)
        other_info.addWidget(self.create_spacer(200, 10))

        self.theme_label(other_info, "FILE NAME PREFIX") 
        self.choose_file_name(other_info)
        other_info.addWidget(self.create_spacer(200, 20))

        other_info.addLayout(save_rec_layout)
        other_info.addWidget(self.create_spacer(200, 20))

        self.theme_label(other_info, "COLOR THEME")
        self.choose_theme(other_info)
        other_info.addWidget(self.create_spacer(200, 160))
       
        # Controls layout
        self.create_logo_label(controls_layout)
        controls_layout.addWidget(self.create_spacer(200, 390))
        self.create_buttons(controls_layout)
      
        # Top section
        top_layout.addWidget(self.create_spacer(5, 50))  
        top_layout.addLayout(other_info)
        top_layout.addWidget(self.create_spacer(5, 50))  
        top_layout.addWidget(self.video_label)
        top_layout.addWidget(self.create_spacer(5, 50))  
        top_layout.addLayout(controls_layout)
        top_layout.addWidget(self.create_spacer(5, 50))
        
        # Bottom section
        self.create_a_trackbar(bottom_layout)
        self.create_a_statusbar(bottom_layout)
        
        # Main layout
        main_layout.addWidget(self.create_spacer(100, 20))
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)
        central_widget.setLayout(main_layout)
        self.setFixedSize(self.sizeHint())

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

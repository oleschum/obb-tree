# OBB Tree for Contour Estimation

A Python project that utilizes Pyside6 for the GUI, numpy, skimage and pycuda for some calculations, and implements connected component analysis and OBB-Tree algorithm for contour estimation.

It is planned to replace some CPU calculation with GPU ones by increasing the usage of pycuda.

##Installation

1. Clone the repository or download the ZIP file and extract it.

    `git clone https://github.com/oleschum/obb-tree.git`

2. Navigate to the project directory.
   
    `cd obb-tree`

3. Create a virtual environment
    `python -m venv obb_venv`
   
4. Activate the virtual environment.
    `source obb_venv/bin/activate`

5. Install the required packages
   
    `pip install -r requirements.txt`

6. Run the application.

    `python main.py`

##Usage

Upon running the application, the main GUI window will appear.
Draw on the first widget using the provided drawing tools.
Click the "Connected Component Analysis" button to segment the drawing. The resulting segmentation will be shown in the second widget.
Click the "Oriented Bounding Boxes" button to estimate the contour using the OBB-Tree algorithm.
The estimated contours will be drawn on top of the segmentation.

##Algorithms
###Connected Component Analysis

Connected component analysis is a process of grouping pixels or voxels in an image based on their connectivity. In this project, it is used to segment the drawing into separate regions.

###OBB-Tree Algorithm

The oriented bounding box (OBB) tree is a data structure used to represent the geometry of a 3D model. In this project, the OBB-Tree algorithm is used for contour estimation. It works by recursively subdividing a 3D object into smaller bounding boxes until the desired level of detail is achieved. The resulting contours are then extracted from the OBBs.

##Credits

This project was created by Ole Schumann. If you have any questions or suggestions, please feel free to create an issue.

##License

This project is licensed under the MIT License. See the LICENSE file for more information.
import matplotlib

matplotlib.use('TkAgg')
import numpy as np
from matplotlib.path import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class OBB:
    corners: np.ndarray
    width: float
    height: float
    depth: Optional[int]


def get_indices_for_segment(image, segment_value):
    # Find the indices of all pixels in the segment
    indices = np.argwhere(image == segment_value)
    return indices


def oriented_bounding_box_py(indices):

    if len(indices) == 1:
        idx = indices[0]
        corners = np.array([[idx[0]-0.5, idx[1] - 0.5],
                            [idx[0]+0.5, idx[1] - 0.5],
                            [idx[0]+0.5, idx[1] + 0.5],
                            [idx[0]-0.5, idx[1] + 0.5]])
        width, height = 1, 1
        return OBB(corners=corners, width=width, height=height, depth=None)

    # Compute the mean of the indices to get the centroid of the segment
    centroid = np.mean(indices, axis=0)

    # Compute the covariance matrix of the indices
    covariance_matrix = np.cov(indices.T)

    # Compute the eigenvalues and eigenvectors of the covariance matrix
    eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)

    # Sort the eigenvectors by decreasing eigenvalue
    sort_indices = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, sort_indices]

    # Compute the angle of rotation from the first eigenvector
    angle = np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])

    # Create a rotation matrix for the angle
    rotation_matrix = np.array([[np.cos(angle), np.sin(angle)],
                                [-np.sin(angle), np.cos(angle)]])

    # Rotate the indices by the angle
    rotated_indices = np.dot(rotation_matrix, (indices - centroid).T).T

    # Compute the minimum and maximum x and y values of the rotated indices
    min_x = np.min(rotated_indices[:, 0])
    max_x = np.max(rotated_indices[:, 0])
    min_y = np.min(rotated_indices[:, 1])
    max_y = np.max(rotated_indices[:, 1])

    # Compute the four corners of the bounding box
    corners = np.array([[min_x, min_y],
                        [max_x, min_y],
                        [max_x, max_y],
                        [min_x, max_y]])

    # Rotate the corners back to the original orientation
    rotated_corners = np.dot(rotation_matrix.T, corners.T).T

    # Translate the corners back to the original position
    translated_corners = rotated_corners + centroid

    # Compute the width and height of the bounding box
    width = max_y - min_y
    height = max_x - min_x

    return OBB(corners=translated_corners, width=width, height=height, depth=None)


def create_sub_parts(indices, corners):
    # given initial coordinates of a segment by the indices array (N,2) and an array giving the corners
    # of a rectangle, create two new indices arrays. These are given by cutting the rectangle in half at the longer
    # side and associating the indices with one of the two parts

    # Compute the midpoint of the longest side of the bounding box
    l1 = corners[1] - corners[0]
    l2 = corners[2] - corners[1]
    if np.dot(l1, l1) > np.dot(l2, l2):
        intersection1 = (corners[0] + corners[1]) / 2
        intersection2 = intersection1 + corners[2] - corners[1]
    else:
        intersection1 = (corners[1] + corners[2]) / 2
        intersection2 = intersection1 + corners[3] - corners[2]

    # compute the direction vector of the intersection line
    direction = intersection2 - intersection1

    # compute vector from all indices to first intersection point (we need just one point on the intersection line,
    # any point would do
    diffs = indices - intersection1

    # compute the cross product of each diff element with the direction vector to decide if point is left or right from
    # half-line of the rectangle
    cross = np.cross(diffs, direction)

    # comptue the masks
    m1 = cross > 0
    m2 = cross <= 0
    return indices[m1], indices[m2]


def create_obb_tree(indices, depth=0, max_depth=3, min_pixels=10):
    """

    :param indices:
    :param depth:
    :param min_pixels:
    :return:
    - obb tree of current level
    - list if obb trees of children
    """
    # Compute the oriented bounding box for the segment
    obb = oriented_bounding_box_py(indices)
    obb.depth = depth

    # If the segment has too few pixels or the tree depth limit is reached, return the bounding box as a leaf node
    if indices.shape[0] < min_pixels or depth == max_depth:
        return obb, []

    # Create sub-segments by applying the mask to the image
    sub_segments = create_sub_parts(indices, obb.corners)

    # image = np.zeros((100, 100))
    # image[indices[:, 0], indices[:, 1]] = 1
    # image[sub_segments[0][:, 0], sub_segments[0][:, 1]] = 2
    # image[sub_segments[1][:, 0], sub_segments[1][:, 1]] = 3
    # plt.imshow(image)
    # plt.show()

    # Recursively create obb trees for each sub-segment
    obb_trees = []
    for sub_segment in sub_segments:
        if len(sub_segment) > 0:
            sub_obb, sub_trees = create_obb_tree(sub_segment, depth + 1, max_depth=max_depth, min_pixels=min_pixels)
            obb_trees.append((sub_obb, sub_trees))

    return obb, obb_trees


def visualize_bounding_box(segment_value, image):
    # Compute the bounding box
    corners, width, height = oriented_bounding_box_py(image, segment_value)
    print(corners)

    # Create a figure and axis object
    fig, ax = plt.subplots(1)

    # Plot the image
    ax.imshow(image, cmap='gray')

    ax.plot(np.mean(np.argwhere(image == 1), axis=0)[1], np.mean(np.argwhere(image == 1), axis=0)[0], 'ro')

    # Plot the bounding box
    rect = plt.Polygon(corners, fill=None, edgecolor='r', linewidth=2)
    ax.add_patch(rect)

    # Set the axis limits and aspect ratio
    ax.set_xlim([0, image.shape[1]])
    ax.set_ylim([image.shape[0], 0])
    ax.set_aspect('equal')

    # Show the plot
    plt.show()


def obb_tree_test():
    import numpy as np
    import matplotlib.pyplot as plt
    from skimage.draw import polygon, polygon_perimeter

    # Define image size and create empty image
    image_size = 100
    image = np.zeros((image_size, image_size))

    # Draw triangle and circle in image
    triangle_coords = np.array([[25, 75], [75, 75], [50, 25]])
    rr, cc = polygon_perimeter(triangle_coords[:, 1], triangle_coords[:, 0])
    image[rr, cc] = 1

    SHOW_ONLY_LEVEL = 0
    SHOW_ONLY_ACIVE = False

    # Define function to plot oriented bounding box
    def plot_obb(obb):
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                  "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
        color = colors[obb.depth % len(colors)]
        corners = obb.corners.copy()
        corners = corners[:, ::-1]
        if SHOW_ONLY_ACIVE and obb.depth != SHOW_ONLY_LEVEL:
            return
        plt.plot([corners[0, 0], corners[1, 0]], [corners[0, 1], corners[1, 1]], color)
        plt.plot([corners[1, 0], corners[2, 0]], [corners[1, 1], corners[2, 1]], color)
        plt.plot([corners[2, 0], corners[3, 0]], [corners[2, 1], corners[3, 1]], color)
        plt.plot([corners[3, 0], corners[0, 0]], [corners[3, 1], corners[0, 1]], color)

    # Compute the oriented bounding box tree
    indices = get_indices_for_segment(image, 1)
    root, sub_trees = create_obb_tree(indices, depth=4)

    # Plot the image with the oriented bounding boxes
    plt.imshow(image, cmap='gray')
    # plt.axis('off')
    plot_obb(root)

    def traverse_tree(tree):
        if len(tree) > 0:
            for obb, sub_t in tree:
                plot_obb(obb)
                traverse_tree(sub_t)

    traverse_tree(sub_trees)
    # if obb_tree[3] is not None:
    #     for i, (corners, width, height, subtrees) in enumerate(obb_tree[3]):
    #         plot_obb(corners, color='C' + str(i))
    #         if subtrees:
    #             for j, (sub_corners, sub_width, sub_height, sub_trees) in enumerate(subtrees):
    #                 plot_obb(sub_corners, color='C' + str(i) + str(j))
    plt.show()


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from scipy.ndimage import rotate

    obb_tree_test()

    # # Create a test image with a diagonal line segment
    # image = np.zeros((200, 200))
    # image[50:150, 50:150] = 1
    # image[150:190, 50:150] = 1
    # image = np.round(rotate(image, angle=-130, reshape=False), decimals=1).astype(np.int32)
    #
    # print(np.unique(image))
    # # Visualize the bounding box of the line segment
    # visualize_bounding_box(1, image)

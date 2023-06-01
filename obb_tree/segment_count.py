import pycuda.driver as cuda
import pycuda.autoinit
import numpy as np
import os


def count_pixels_per_segment(image: np.ndarray):
    """
    Counts the number of times each pixel value occurs.
    A value of 0 is treated as background.
    :param image: Segmented image as numpy integer array.
    :return:
    segment_counts: Number of pixels per segment as numpy array The numpy array has length num_segments.
     At index idx of the array is the number of times the given value occurs
    num_segments: number of segments
    """
    current_folder = os.path.dirname(os.path.abspath(__file__))
    mod = cuda.module_from_file(os.path.join(current_folder, "segment_count.cubin"))
    count_pixel_kernel = mod.get_function("count_pixels_per_segment")

    width = image.shape[0]
    height = image.shape[1]

    segment_counts = np.zeros(width // 2 * height // 2, dtype=np.int32)
    segment_counts_gpu = cuda.to_device(segment_counts)

    num_segments = np.zeros(1, dtype=np.int32)
    num_segments_gpu = cuda.to_device(num_segments)

    block = (32, 32, 1)
    grid = ((width + block[0] - 1) // block[0], (height + block[1] - 1) // block[1])

    count_pixel_kernel(cuda.to_device(image.flatten()), segment_counts_gpu, num_segments_gpu, np.int32(width),
                       np.int32(height), block=block, grid=grid)

    cuda.memcpy_dtoh(segment_counts, segment_counts_gpu)
    cuda.memcpy_dtoh(num_segments, num_segments_gpu)

    return segment_counts[:num_segments[0]], num_segments[0]


def compare_results():
    width, height = 512, 512
    image = np.random.randint(0, 40, (width, height), dtype=np.int32)

    import time

    t0 = time.perf_counter()
    labels, counts = np.unique(image, return_counts=True)
    t1 = time.perf_counter()
    segment_counts, num_segments = count_pixels_per_segment(image)
    t2 = time.perf_counter()
    print(t1 - t0, t2 - t1)

    assert len(labels) == num_segments

    for c, idx in zip(counts, labels):
        assert c == segment_counts[idx]

    print(count_pixels_per_segment(image))


if __name__ == '__main__':
    compare_results()

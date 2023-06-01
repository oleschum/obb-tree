// nvcc -cubin -arch=sm_50 segment_count.cu

extern "C"
__global__ void count_pixels_per_segment(int* image, int* segment_counts, int* num_segments, int width, int height)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;

    if (x < width && y < height)
    {
        int segment = image[y * width + x];
        int prevCount = atomicAdd(&segment_counts[segment], 1);
        if (prevCount == 0)
        {
            atomicAdd(num_segments, 1);
        }
    }
}
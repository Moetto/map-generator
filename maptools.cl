
uchar 	calculate_gradient_value(int4 start_rgb, int4 end_rgb, value, channel, min_value, max_value) {
	float percentage = (float)(value - min_value) / (float)(max_value - min_value);
	if (channel == 0) {
		return (uchar) start_rgb.s0 * (1 - percentage) + end_rgb.s0 * percentage;
	}
	if (channel == 1) {
		return (uchar) start_rgb.s1 * (1 - percentage) + end_rgb.s1 * percentage;
	}
	if (channel == 2) {
		return (uchar) start_rgb.s2 * (1 - percentage) + end_rgb.s2 * percentage;
	}
}


kernel void ColoredMap(
	__global	float*	inputImage,
	__global	uchar* 	outputImage,
				int 	channel,
				float	sea_level,
				int4	sea_start_rgb,
				int4	sea_end_rgb,
				int4	start_rgb,
				int4	end_rgb,
				int		width,
				int		height) {
	int x = get_global_id(1);
	int y = get_global_id(0);

	float value = inputImage[x + width * y];
	uchar color;
	if(value <= sea_level){
		color =  calculate_gradient_value(sea_start_rgb, sea_end_rgb, value, channel, 0, (int)sea_level);
	} else {
		color =  calculate_gradient_value(start_rgb, end_rgb, value, channel, (int)sea_level, 255);
	}
	outputImage[(x + y * width)] = color;
}


__kernel void calculate_mean (
    __global float* input,
    __global float* output,
    int window_size,
    int width,
    int height
    ) {
    int x = get_global_id(1);
    int y = get_global_id(0);

    float mean = 0;
    int y_final;
    int x_final;
    for (int y1 = - window_size; y1 <= window_size ; y1++) {
        for (int x1 = -window_size ; x1 <= window_size ; x1++) {
        	y_final = min(max(0, y + y1), height);
        	x_final = min(max(0, x + x1), width);
            mean += input[y_final * width + x_final];
        }
    }

    float val = (mean / ((2*window_size+1)*(2*window_size+1)));
    output[y * width + x] = val;
}

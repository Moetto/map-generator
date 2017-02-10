#define NORTH 0
#define EAST 2
#define SOUTH 4
#define WEST 6

#define NORTH_EAST 1
#define SOUTH_EAST 3
#define SOUTH_WEST 5
#define NORTH_WEST 7

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


__kernel void gradient_direction (
	__global float* x_value,
	__global float* y_value,
	__global uchar* output,
			 int	width
			 ) {
	int x = get_global_id(1);
	int y = get_global_id(0);

	int coord = x + y * width;

	float x_val = x_value[coord];
	float y_val = y_value[coord];

	double angle = atan2(x_val, y_val);
	char direction;

	if (angle < (-M_PI * 7 / 8) || angle >= (M_PI * 7 / 8)) {
		direction = NORTH;
	} else if (angle >= (-M_PI * 7 / 8) && angle < (-M_PI * 5 / 8)) {
		direction = NORTH_EAST;
	} else if (angle >= (-M_PI * 5 / 8) && angle < (-M_PI * 3 / 8)) {
		direction = EAST;
	} else if (angle >= (-M_PI * 3 / 8) && angle < (-M_PI * 1 / 8)) {
		direction = SOUTH_EAST;
	} else if (angle >= (-M_PI * 1 / 8) && angle < (M_PI * 1 / 8)) {
		direction = SOUTH;
	} else if (angle >= (M_PI * 1 / 8) && angle < (M_PI * 3 / 8)) {
		direction = SOUTH_WEST;
	} else if (angle >= (M_PI * 3 / 8) && angle < (M_PI * 5 / 8)) {
		direction = WEST;
	} else if (angle >= (M_PI * 5 / 8) && angle < (M_PI * 7 / 8)) {
		direction = NORTH_WEST;
	}
	output[coord] = direction;
}


__kernel void generate_rivers(
	__global uchar* gradient_direction,
	__global int* 	output,
	__global int*	start_points_x_buf,
	__global int*	start_points_y_buf,
			 int	width,
			 int	height
			 ) {
	int i = get_global_id(0);
	int x = start_points_x_buf[i];
	int y = start_points_y_buf[i];

	int coord_index = x + y * width;

  	uchar direction = gradient_direction[coord_index];
  	int prev_val = 0;

  	while (1) {
		if (direction == NORTH) {
			y++;
		} else if (direction == NORTH_EAST) {
			x++;
			y++;
		} else if (direction == EAST) {
			x++;
		} else if (direction == SOUTH_EAST) {
			x++;
			y--;
		} else if (direction == SOUTH) {
			y--;
		} else if (direction == SOUTH_WEST) {
			x--;
			y--;
		} else if (direction == WEST) {
			x--;
		} else if (direction == NORTH_WEST) {
			x--;
			y++;
		}
		if (x < 0 || x >= width || y < 0 || y >= height) {
			return;
		}
		coord_index = x + y * width;
		if(coord_index >= width * height) {
			return;
		}

		if (atomic_inc(&output[coord_index]) > 10) {
			return;
		}
		direction = gradient_direction[coord_index];
  	}
}

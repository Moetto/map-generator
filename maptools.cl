#define NORTH 0
#define EAST 2
#define SOUTH 4
#define WEST 6

#define NORTH_EAST 1
#define SOUTH_EAST 3
#define SOUTH_WEST 5
#define NORTH_WEST 7

uchar 	calculate_gradient_value(int4 start_rgb, int4 end_rgb, float value, uint channel, float min_value, float max_value) {
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
	__global	float*	heightMap,
	__global	uchar* 	red,
	__global	uchar* 	green,
	__global	uchar* 	blue,
				float	start,
				float	end,
				int4	start_rgb,
				int4	end_rgb,
				int		width,
				int		height) {
	int x = get_global_id(1);
	int y = get_global_id(0);
	uint coord = x + y * width;

	float value = heightMap[x + width * y];
	uchar color;
	if(value > start && value <= end){
		uchar r, g, b;
		red[coord] = calculate_gradient_value(start_rgb, end_rgb, value, 0, start, end);
		green[coord] = calculate_gradient_value(start_rgb, end_rgb, value, 1, start, end);
		blue[coord] = calculate_gradient_value(start_rgb, end_rgb, value, 2, start, end);
	}
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
			 int	width,
			 int	height
			 ) {
	int x = get_global_id(1);
	int y = get_global_id(0);

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

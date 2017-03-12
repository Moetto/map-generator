__kernel void filter (
    __global float* map,
    int width,
    int height
    ) {
    int x = get_global_id(1);
    int y = get_global_id(0);

	int center_x = (int)width / 2;
	int center_y = (int)height / 2;

	float distance = sqrt(pow(x - center_x, 2.0f) + pow(y - center_y, 2.0f));
	float max_distance = sqrt(pow(center_x, 2.0f) + pow(center_y, 2.0f));
	float multiplier = (max_distance - distance) / max_distance / 2 + 0.5;

	float original = map[y * width + x];

    map[y * width + x] = multiplier * original;
}

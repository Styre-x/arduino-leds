#include <pulse/simple.h>
#include <pulse/error.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#include <fftw3.h>
#include <time.h>

#define SAMPLE_RATE 44100
#define CHANNELS 1
#define BUFF_SIZE 1024
#define RESTING 0.2
#define ROTATING 0

double normal_max = 1;
double brightness = 1;
double rotator = 0;

int open_serial(const char *device){
	int fd = open(device, O_RDWR | O_NOCTTY);
	if (fd == -1){
		return -1;
	}
	struct termios options;
	tcgetattr(fd, &options);

	cfsetispeed(&options, 200000);
	cfsetospeed(&options, 200000);

	options.c_cflag &= ~PARENB;
	options.c_cflag &= ~CSTOPB;
	options.c_cflag &= ~CSIZE;
	options.c_cflag |= CS8;

	options.c_cflag &= ~CRTSCTS;
	options.c_cflag |= CREAD | CLOCAL;

	options.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
	options.c_iflag &= ~(IXON | IXOFF | IXANY);
	options.c_oflag &= ~OPOST;

	tcsetattr(fd, TCSANOW, &options);
 
	sleep(2);

	return fd;
}

void normalize(double *value){
	if (*value > normal_max){
		normal_max = *value;
	}
	*value = (*value) / normal_max;
	if (ROTATING == 1){
		*value = fmod((*value + rotator), 1.0);
		rotator += 0.00075;
		if (rotator >= 1){
			rotator = 0;
		}
	} else {
		*value = fmod((*value + RESTING), 1.0);
	}
}

void process_audio(int16_t *buffer, int *r, int *g, int *b){
	double *in = fftw_malloc(sizeof(double) * BUFF_SIZE);
	fftw_complex *out = fftw_malloc(sizeof(fftw_complex) * (BUFF_SIZE/2 + 1));
	fftw_plan plan = fftw_plan_dft_r2c_1d(BUFF_SIZE, in, out, FFTW_ESTIMATE);

	for (int i = 0; i < BUFF_SIZE; i++){
		double window = 0.5 * (1 - cos(2 * M_PI * i / (BUFF_SIZE - 1)));
		in[i] = buffer[i] * window;
	}

	fftw_execute(plan);


	double bass = 0, mid = 0, high = 0;
	int bass_count = 0, mid_count = 0, high_count = 0;

	for (int i = 0; i < BUFF_SIZE/2; i++) {
		double freq = (double)i * SAMPLE_RATE / BUFF_SIZE;
		double magnitude = sqrt(out[i][0]*out[i][0] + out[i][1]*out[i][1]);
        
		if (freq >= 20 && freq < 250) {
			bass += magnitude;
			bass_count++;
		} else if (freq >= 250 && freq < 2000) {
			mid += magnitude;
			mid_count++;
		} else if (freq >= 2000 && freq < 20000) {
			high += magnitude;
			high_count++;
		}
	}
	double raw = (bass/bass_count) + (mid/mid_count)  + ((high/high_count)*1.5);
	normalize(&raw);

	// HSV conversion

	double S = 1.0;
	double V = brightness;

	int i = (int)(raw * 6);
	double f = (raw * 6) - (double)(i);
	double p = V * (1-S);
	double q = V * (1 - S * f);
	double t = V * (1-S*(1-f));

	i %= 6;

	switch (i){
		case 0:
			*r = (int)(V*255);
			*g = (int)(t*255);
			*b = (int)(p*255);
			break;
		case 1:
			*r = (int)(q*255);
			*g = (int)(V*255);
			*b = (int)(p*255);
			break;
		case 2:
			*r = (int)(p*255);
			*g = (int)(V*255);
			*b = (int)(t*255);
			break;
		case 3:
			*r = (int)(p*255);
			*g = (int)(q*255);
			*b = (int)(V*255);
			break;
		case 4:
			*r = (int)(t*255);
			*g = (int)(p*255);
			*b = (int)(V*255);
			break;
		case 5:
			*r = (int)(V*255);
			*g = (int)(p*255);
			*b = (int)(q*255);
			break;
	}

	fftw_destroy_plan(plan);
	fftw_free(in);
	fftw_free(out);

	printf("%i %i %i \r", *r, *g, *b);
	fflush(stdout);
}

int main(int argc, char *argv[]){
	if (argc < 2){
		printf("usage: %s <arduino> <listening device> <brightness 0-255>\n", argv[0]);
		return 1;
	}

	if (argc > 3){
		brightness = (double)(atoi(argv[3]))/255;
	}

	int arduinofd = open_serial(argv[1]);
	if (arduinofd == -1){
		printf("could not open arduino\n");
		return 1;
	}

	pa_buffer_attr buffer_attr;
	buffer_attr.maxlength = (uint32_t) -1;  // Use default
	buffer_attr.fragsize = 32 * sizeof(int16_t) * CHANNELS;

	pa_simple* stream;
	pa_sample_spec format;
	int error = 0;

	int16_t buffer[BUFF_SIZE];

	format.format = PA_SAMPLE_S32LE;
	format.rate = 44100;
	format.channels = 2;
	

	const char *device = NULL;
	device = argv[2];

	stream = pa_simple_new(
			NULL,
			"LED-Stream",
			PA_STREAM_RECORD,
			device, // NULL FOR DEFAULT, GIVEN ARGV FOR OTHER
			"Monitor for Arduino",
			&format,
			NULL,
			&buffer_attr,
			&error
		);

	if (!stream){
		printf("could not open stream %s\n", pa_strerror(error));
		close(arduinofd);
		return 1;
	}

	int stream_err;

	int r,g,b;
	char rgbstring[48];

	while (1){
		stream_err = pa_simple_read(stream, 
				buffer,
				sizeof(buffer),
				&error
			);
		if (stream_err != 0){
			printf("stream error %i", stream_err);
			break;
		}


		process_audio(buffer, &r, &g, &b);

		snprintf(rgbstring, sizeof(rgbstring), "%d,%d,%d,1\n", r,g,b);

		write(arduinofd, rgbstring, strlen(rgbstring));
	}

	pa_simple_free(stream);
	close(arduinofd);

	return 0;
}

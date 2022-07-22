from cmath import log, nan
from collections import deque
from cv2 import repeat
from pyarinst import ArinstDevice
import numpy as np
import cv2
import argparse
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button, Slider
from collections import deque
from time import sleep
from math import sin, cos, pow, pi

SAMPLES = 100

AMPLITUDE_HIGH = -90
AMPLITUDE_LOW = -130

GRADIENT_STEPS = 100

def mhz2hz(mhz):
    return int(mhz * 10e5)

def get_amp_data( start, stop, step, attenuation=0):
    data = device.get_scan_range(start, stop, step, attenuation=attenuation)
    if data is None:
        data = [0 for _ in range(steps)]
    else:
        for amplitude_index in range(steps):
            if amplitude_index >= len(data):
                data.append(0)
    return data


class AmplitudeMesh:
    def __init__(self, data = None, display_len = 50, vmin=-110, vmax=-70, cmap='jet'):
        
        self.readmode = False
        self.display_len = display_len
        self.data = deque([])
        self.buff = []
        
        if data is not None:
            self.readmode = True
            self.data = deque(data)
        else:
            self.buff = [[0 for _ in range(steps)] for _ in range(display_len)]
            self.readmode = False

        # set up the plot
        self.fig, ax = plt.subplots()
        self.mesh = ax.matshow(self.buff, vmin=vmin, vmax=vmax, cmap=cmap, origin='upper')
        self.fig.colorbar(self.mesh)

        # setup the animation
        self.cur_frame = 0
        self.frames = 0
        self.anim = animation.FuncAnimation(self.fig, self._update,
                                            interval=10.0,
                                            blit=True)

        # setup the animation control
        self.anim_running = True

    def _add_to_data(self, data, val):
        data.append(val)
        self.frames = len(self.data)
        
    def _update_buf(self, buf, frame):
        if self.frames >= self.display_len:
            for i in range(self.display_len):
                buf[i] = self.data[frame+self.display_len-1-i]
        else:
            for i in range(0, self.frames):
                buf[i] = self.data[-i]
            for i in range(self.frames, self.display_len):
                buf[i] = [0 for _ in range(len(self.data[0]))]
        

        #buf = self.data[frame:frame+self.display_len]

    def _update(self, frame):
        frame = self.cur_frame
        if self.readmode == False:
            self._add_to_data(self.data, get_amp_data(start, stop, step))
            
        #self._update_buf(self.buff, self.cur_frame)
        
        
        self.time_slider.ax.set_ylim(self.frames, self.time_slider.valmin)
        self.time_slider.valmax = self.frames

            
        # fig.canvas.draw_idle()
        #self.ax.set_xticklabels((str(frame), str(frame+self.display_len)))
        
        if self.cur_frame == self.frames - 1:
            self.cur_frame += 1
            self.time_slider.set_val(self.cur_frame)
            #self.fig.canvas.draw_idle()
            
            self.mesh.set_array(self.buff)
            
            
        
        
        sleep(0.01)
        return self.mesh

    def _pause(self):
        if self.anim_running:
            self.anim.event_source.stop()
            self.anim_running = False
        else:
            self.anim.event_source.start()
            self.anim_running = True

    # def _reset(self):
    #     self._set_val(0)

    def _slider_update(self, val=0)


    def _set_frame(self, frame=0):
        frame = int(frame)
        #self.cur_frame = 0
        if self.frames < self.display_len:
            frame = 0
        elif frame > self.frames - self.display_len:
            frame = self.frames - self.display_len
        elif frame < 0:
            frame = 0
        self.cur_frame = frame
        self._update_buf(self.buff, frame)
        
        
        
        #self.anim.event_source.stop()
        # self.anim = animation.FuncAnimation(self.fig, self._update,
        #                                     interval=100.0)
        # self.anim_running = True

    def animate(self):
        # pause_ax = self.fig.add_axes((0.7, 0.025, 0.1, 0.04))
        # pause_button = Button(pause_ax, 'pause', hovercolor='0.975')
        # pause_button.on_clicked(self._pause)

        # reset_ax = self.fig.add_axes((0.8, 0.025, 0.1, 0.04))
        # reset_button = Button(reset_ax, 'reset', hovercolor='0.975')
        # reset_button.on_clicked(self._reset)

        #transform = matplotlib.transforms.Affine2D().rotate_deg(180)
        #helper = floating_axes.GridHelperCurveLinear(transform, plot_extents)

        slider_ax = self.fig.add_axes((0.05, 0.1, 0.045, 0.8))
        
        self.time_slider = Slider(slider_ax,
                                  label='Time',
                                  valmin=0, 
                                  valmax=1,
                                  valinit=0,
                                  valstep=1.0,
                                  orientation='vertical'
                                  )
        #flipping slider upside-down
        self.time_slider.ax.set_ylim(self.time_slider.valmax, self.time_slider.valmin)

        #self.time_slider.poly = slider_ax.axhspan(self.time_slider.valinit, self.time_slider.valmax, .25, .75)
        self.time_slider.on_changed(self._set_frame)

        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", help="start MHz", type=float, default=2300)
    parser.add_argument("--stop", help="stop MHz", type=float, default=2500)
    parser.add_argument("--step", help="step MHz", type=float, default=4)
    parser.add_argument("--att", help="signal attenuation in range -30 to 0", type=float, default=0)
    args = parser.parse_args()

    start = mhz2hz(args.start)
    stop = mhz2hz(args.stop)
    step = mhz2hz(args.step)
    steps = int(abs(args.stop-args.start)/args.step) + 1
    attenuation = args.att

    device = ArinstDevice()

    amplitude_data = [[None for _ in range(steps)] for _ in range(SAMPLES)]

    # for i in range(SAMPLES):
    #     amplitude_data.pop(0)
    #     amplitude_data.append(get_amp_data(start, stop, step))
    amp_mesh = AmplitudeMesh()
    amp_mesh.animate()

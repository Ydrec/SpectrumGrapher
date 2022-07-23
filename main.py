from datetime import datetime
from pyarinst import ArinstDevice
import numpy as np
import argparse
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button, Slider
from time import sleep

DISPLAY_LENGH = 100

AMPLITUDE_HIGH = -90
AMPLITUDE_LOW = -130

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

def get_data_artificial_seq(low = 0, high = 1, lengh = 100):
    data = []
    data = np.random.randint(low, high, lengh)
    return data


class AmplitudeMesh:
    def __init__(self, data = None, display_len = 50, vmin=-110, vmax=-60, cmap='jet'):
        
        self.readmode = False
        self.display_len = display_len
        self.data = []
        
        self.buff = []
        
        if data is not None:
            self.data = data
            self.readmode = True
            self.scanning = False
        else:
            self.buff = [[-200 for _ in range(steps)] for _ in range(display_len)]
            self.readmode = False
            self.scanning = True

        # set up the plot
        self.fig, self.ax0 = plt.subplots()
        #self.ax0.set_aspect(1,"datalim")
        #self.ax0.set_adjustable("datalim")
        #self.ax0.set_adjustable("datalim")
        #self.ax0.set_xlim(0, steps)
        #self.ax0.set_ylim(0, display_len)
        #self.ax0.set_aspect(1)

        self.mesh = self.ax0.matshow(self.buff, vmin=vmin, vmax=vmax, cmap=cmap, origin='upper', aspect='auto')
        self.ax0.set_position((0.2, 0.1, 0.65, 0.75))
        self.ax0.grid(False)

        self.ax1 = self.fig.add_axes((0.9, 0.1, 0.03, 0.75))
        self.fig.colorbar(self.mesh, cax=self.ax1)

        # set up frequncy axis
        self.ax0.set_title('Frequences')
        self.ax0.set_xticks(np.linspace(0,steps-1,num=5))
        self.ax0.set_xticks(np.linspace(0,steps-1,num=9),minor=True)
        self.ax0.set_xticklabels(np.linspace(args.start,args.stop,num=5))
        


        # setup the animation
        self.cur_frame = 0
        self.frames = len(self.data)
        self.anim = animation.FuncAnimation(self.fig, self._update,
                                            interval=10.0,
                                            blit=True)

        # setup the animation control
        self.anim_running = True

    def _add_to_data(self, data, val):
        #adding timestamp
        val = [val,datetime.now()]
        data.append(val)
        self.frames = len(self.data)
        
    def _update_buf(self, buf, frame):
        for i in range(self.display_len):
            if i < self.frames-frame:
                if self.frames < frame+self.display_len:
                    buf[i] = self.data[frame+self.frames-1-i][0]
                else:
                    buf[i] = self.data[frame+self.display_len-1-i][0]
            else:
                buf[i] = [-200 for _ in range(len(self.data[0][0]))]

    def _update(self, frame):
        if self.readmode == False:
            if self.scanning == True:
                #self._add_to_data(self.data, get_amp_data(start, stop, step))
                self._add_to_data(self.data,get_data_artificial_seq(-110,-70,steps))
                if self.frames > self.display_len:
                    self.time_slider.ax.set_ylim(self.time_slider.valmin, self.frames - self.display_len)
                    self.time_slider.valmax = self.frames - self.display_len
        
        self.ax0.set_yticks(np.linspace(0,self.display_len-1,num=5))
        #self.ax0.set_yticks(np.linspace(0,self.display_len-1,num=9),minor=True)
        last_visible_frame = self.cur_frame + self.display_len

        timestamps = [None for _ in range(5)]
        time_points = np.linspace(self.cur_frame + self.display_len, self.cur_frame, num=5, dtype='int16')
        itr1 = 0
        itr2 = 0
        while itr1 < 5:
            if time_points[itr1] <= self.frames:
                if self.frames <= self.display_len:
                    if itr2 * int(self.display_len/5) <= self.frames:
                        timestamp = str(self.data[self.frames - 1 - (itr2 * int(self.display_len/5))][1])
                else:
                    timestamp = str(self.data[time_points[itr1]][1])
                timestamp = timestamp[timestamp.index(' ')+1:timestamp.index('.')+2]
                timestamps[itr2] = timestamp
                itr2 += 1
            itr1 += 1

        
        self.ax0.set_yticklabels(timestamps)
        
        if self.anim_running == True and self.cur_frame <= self.frames:
            self.cur_frame += 1
            self.time_slider.eventson = False
            self.time_slider.set_val(self.cur_frame)
            self.time_slider.eventson = True
            self._set_frame(self.cur_frame)
            self.fig.canvas.draw_idle()
        return self.mesh

    def _pause(self, event):
        if self.anim_running:
            self.anim_running = False
            self.pause_button.label.set_text("Resume")
            #self.anim.event_source.stop()
        else:
            self.pause_button.label.set_text("Pause")
            #self.anim.event_source.start()
            self.anim_running = True

    def _reset(self, event):
        self.anim_running = False
        if self.readmode == False:
            self.data = []
            self.frames = 0
        self.cur_frame = 0
        self.anim_running = True
        
    def _toggle_scan(self, event):
        if self.scanning:
            self.scanning = False
            self.pause_scan_button.label.set_text("Resume scan")
        else:
            self.scanning = True
            self.pause_scan_button.label.set_text("Stop scan")

    def _slider_update(self, val=0):
        if val < 0:
            val = 0
        elif val > self.frames - self.display_len:
            val = self.frames - self.display_len
        self.cur_frame = val
        self._set_frame(self.cur_frame)

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
        self.mesh.set_array(self.buff)

    def animate(self):
        pause_ax = self.fig.add_axes((0.5, 0.025, 0.1, 0.04))
        self.pause_button = Button(pause_ax, 'Pause', hovercolor='0.975')
        self.pause_button.on_clicked(self._pause)

        reset_ax = self.fig.add_axes((0.6, 0.025, 0.1, 0.04))
        self.reset_button = Button(reset_ax, 'Reset', hovercolor='0.975')
        self.reset_button.on_clicked(self._reset)
        
        slider_ax = self.fig.add_axes((0.02, 0.1, 0.045, 0.8))
        self.time_slider = Slider(slider_ax,
                                  label='Time',
                                  valmin=0, 
                                  valmax=1,
                                  valinit=1,
                                  valstep=1.0,
                                  orientation='vertical'
                                  )
        #flipping slider upside-down
        #self.time_slider.ax.set_ylim(self.time_slider.valmax, self.time_slider.valmin)
        self.time_slider.on_changed(self._slider_update)
        
        #Unnecessary and causes bugs with reset
        # if self.readmode == False:
        #     pause_scan_ax = self.fig.add_axes((0.7, 0.025, 0.15, 0.04))
        #     self.pause_scan_button = Button(pause_scan_ax, 'Stop scan', hovercolor='0.975')
        #     self.pause_scan_button.on_clicked(self._toggle_scan)

        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", help="start MHz", type=float, default=2300)
    parser.add_argument("--stop", help="stop MHz", type=float, default=2500)
    parser.add_argument("--step", help="=step MHz", type=float, default=2)
    args = parser.parse_args()

    start = mhz2hz(args.start)
    stop = mhz2hz(args.stop)
    step = mhz2hz(args.step)
    steps = int(abs(args.stop-args.start)/args.step) + 1

    #device = ArinstDevice(device='/dev/ttyACM0')

    amp_mesh = AmplitudeMesh(display_len=DISPLAY_LENGH)
    amp_mesh.animate()

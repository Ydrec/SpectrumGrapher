from datetime import datetime
from pyarinst import ArinstDevice
import numpy as np
import argparse
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button, Slider
from os import path
from time import sleep

#Длинна в строках выводимого изоброжения
DISPLAY_LENGH = 100

#Величины амплитуд относительно которых градируется цвет на изображении
AMPLITUDE_HIGH = -60
AMPLITUDE_LOW = -110

#Папка в которую будут сохраняеться логи
LOGS_PATH = 'logs/'

#Перевод МГц в Гц
def mhz2hz(mhz):
    return int(mhz * 10e5)

#Запрос данных от прибора, с проверкой на неполные или пустые массивы
def get_amp_data( start, stop, step, attenuation=0):
    #Получение массива амплитуд функцией библиотеки pyarinst
    data = device.get_scan_range(start, stop, step)

    #Проверка на пустую строку и замена такой на пустые значения
    if data is None:
        data = [-200 for _ in range(steps)]
    else:
    #Если массив неполный дозаполнить его пустыми значениями
        for amplitude_index in range(steps):
            if amplitude_index >= len(data):
                data.append(-200)
    return data

#Тестовая функция имитирующая получение массива с данными
def get_data_artificial_seq(low = 0, high = 1, lengh = 100):
    data = np.random.randint(low, high, lengh)
    return data

#Класс ответсвенный за все связанное с выводимым окном
class AmplitudeMesh:
    #Аргументы: data - данные из лога в виде таблицы амплитуд, display_len - длина в строках изображения
    #vmin/vmax - минимальное и максимальное значения силы амплитуды для цветовой градации,
    #cmap - используемый градиент, список нативных градиентов https://matplotlib.org/stable/tutorials/colors/colormaps.html#classes-of-colormaps
    def __init__(self, data = None, display_len = 100, vmin=-110, vmax=-60, cmap='jet'):
        #Определяем если нам надо читать из файла или работать с прибором
        if data is not None:
            #Если читаем из файла, присваиваем себе таблицу
            #Создаем буффер изображения, ширина = количеству точек в 1 миссиве амплитуд, длина = количество строк display_len
            #Устанавливает флаги чтения из файла и отсутсвия подготовки буффера
            self.data = data
            #Буфферу нужно изначально задавать размеры при создании через функцию matshow или она будет давать ошибку
            self.buff = [[-200 for _ in range(len(self.data[0][0]))] for _ in range(display_len)]
            self.readmode = True
            self.scanning = False
            self.setup = False
        else:
            #Если работаем с прибором то создаем пустой массив данных для записи в него
            #Создаем пустой буффер, ширина = расчетное количество точек получаемых от прибора
            #устанавливаем флаги не чтения из файла и подготовки буффера
            #Подготовка используеться тк изначально таблица данных пустая(< размера буффера) и для вывода нужно менять код
            self.data = []
            self.buff = [[-200 for _ in range(steps)] for _ in range(display_len)]
            self.readmode = False
            self.scanning = True
            self.setup = True

        self.display_len = display_len

        #Создаем окно fig и основной участок ax0
        self.fig, self.ax0 = plt.subplots()

        #В окне создается матрица пикселей из буффера с пустыми значениями для задания правильного размера
        self.mesh = self.ax0.matshow(self.buff, vmin=vmin, vmax=vmax, cmap=cmap, origin='upper', aspect='auto')
        #Смешения участка ax0, смешение вправо, вверх, ширина, высота
        self.ax0.set_position((0.21, 0.1, 0.65, 0.75))
        self.ax0.grid(False)

        #Создание участка ax1 для цветовой линии
        self.ax1 = self.fig.add_axes((0.88, 0.1, 0.03, 0.75))
        #Цветовая линия привязаная к self.mesh на учаcтке ax1
        self.fig.colorbar(self.mesh, cax=self.ax1)

        #Создание оси частот, название, 5 подписанных четр, 9 малых
        self.ax0.set_title('Frequences')
        self.ax0.set_xticks(np.linspace(0,steps-1,num=5))
        self.ax0.set_xticks(np.linspace(0,steps-1,num=9),minor=True)
        #Для подписей равно делиться диапазон мин и макс сканируемой частоты на 5 меток
        self.ax0.set_xticklabels(np.linspace(args.start,args.stop,num=5))

        # Создание кнопок, участок, объект кнопки, вызываемая функция
        pause_ax = self.fig.add_axes((0.5, 0.025, 0.1, 0.04))
        self.pause_button = Button(pause_ax, 'Pause', hovercolor='0.975')
        self.pause_button.on_clicked(self._pause)

        reset_ax = self.fig.add_axes((0.6, 0.025, 0.1, 0.04))
        self.reset_button = Button(reset_ax, 'Reset', hovercolor='0.975')
        self.reset_button.on_clicked(self._reset)

        # Создание ползуна, участок, объект кнопки, вызываемая функция
        slider_ax = self.fig.add_axes((0.02, 0.1, 0.045, 0.8))
        self.time_slider = Slider(slider_ax,
                                  label='Time',
                                  valmin=0,
                                  valmax=1,
                                  # valinit=1,
                                  valstep=1.0,
                                  orientation='vertical'
                                  )
        self.time_slider.on_changed(self._slider_update)
        # Возможен переворот ползуна
        # self.time_slider.ax.set_ylim(self.time_slider.valmax, self.time_slider.valmin)
        if self.readmode:
            #Если читаем из файла сразу устанавливаем макс значение ползуна
            self.time_slider.ax.set_ylim(self.time_slider.valmin, self.frames - self.display_len - 1)
            self.time_slider.valmax = self.frames - self.display_len - 1

        #Переключатель опроса прибора, ненужен и не доработан
        # if self.readmode == False:
        #     pause_scan_ax = self.fig.add_axes((0.7, 0.025, 0.15, 0.04))
        #     self.pause_scan_button = Button(pause_scan_ax, 'Stop scan', hovercolor='0.975')
        #     self.pause_scan_button.on_clicked(self._toggle_scan)

        #Устанавливает первый кадр, находим полную длинну таблицы, запускаем анимацию
        self.cur_frame = 0
        self.frames = len(self.data)
        #Анимация приндлежит окну fig и вызывет каждый свой цикл self._update
        self.anim = animation.FuncAnimation(self.fig, self._update,
                                            interval=10.0,
                                            blit=True)

        #Флаг для контроля анимации
        self.anim_running = True

    def _add_to_data(self, data, val):
        #Получаем значение и добавляем его в таблицу данных
        #Вторым обектом после каждого массива амплитуд добавляем временную метку
        val = [val,datetime.now()]
        data.append(val)
        self.frames = len(self.data)
        
    def _update_buf(self, buf, frame = 1):
    #Буффер должен быть матрицей скаляров амплитуд одинакового размера или matshow бросает ошибку
        if self.setup:
        #Если данных недостаточно чтобы заполнить буффер, то вначале добавить что возможно в буффер
        #Затем добавить массивы пустых данных
        #буффер заполняется из данных в обратном порядке чтобы последнее полученное значение было в начале буффера
            for i in range(self.frames):
                buf[i] = self.data[-i][0]
            for i in range(self.frames+1,self.display_len):
                buf[i] = [-200 for _ in range(len(self.data[0][0]))]
        else:
        #Если таблица данных больше размера буффера то заполнить буффер со смешением на кол строк
            for i in range(self.display_len):
                buf[i] = self.data[frame + self.display_len - 1 - i][0]

    def _update(self, *frame):
        if self.readmode and self.scanning:
            #try чтобы программа не крашнулась если отключить прибор, не тестировалось
            try:
                #Добавляем данные в таблицу, get_amp_data гарантирует одинаковую длинну массивов
                self._add_to_data(self.data, get_amp_data(start, stop, step))
                #Тестовая функция
                #self._add_to_data(self.data, get_data_artificial_seq(-110, -70, steps))
                #Проверка что  размер таблицы уже больше размера буфеера
                if self.frames > self.display_len:
                    #Отключаем режим подготовки
                    #Меняем максимальное значение ползуна времени
                    self.setup = False
                    self.time_slider.ax.set_ylim(self.time_slider.valmin, self.frames - self.display_len)
                    self.time_slider.valmax = self.frames - self.display_len
            except FileNotFoundError:
                self.scanning = False
        else:
            #Если читаем данные из файла, проверяем достижение конца файла и останавливаем прокрутку
            if self.anim_running and self.cur_frame >= (self.frames - self.display_len):
                    self._pause()

        #Первая версия привязки меток времени к оси
        # timestamps = [None for _ in range(5)]
        # time_points = np.linspace(self.cur_frame + self.display_len, self.cur_frame, num=5, dtype='int16')
        # itr1 = 0
        # itr2 = 0
        # while itr1 < 5:
        #     if time_points[itr1] <= self.frames:
        #         if self.frames <= self.display_len:
        #             if itr2 * int(self.display_len/5) <= self.frames:
        #                 timestamp = str(self.data[self.frames - 1 - (itr2 * int(self.display_len/5))][1])
        #         else:
        #             timestamp = str(self.data[time_points[itr1]][1])
        #         try:
        #             while True:
        #                 timestamp = timestamp[timestamp.index(' '):]
        #         except ValueError:
        #             pass
        #         timestamp = timestamp[:timestamp.index('.')+2]
        #         timestamps[itr2] = timestamp
        #         itr2 += 1
        #     itr1 += 1
        # self.ax0.set_yticklabels(timestamps)

        #создаем черточки для оси времени каждые 20 линий
        timeticks = []
        for i in range(self.cur_frame % 20 + 1, self.display_len, 20):
            timeticks.append(i)
        self.ax0.set_yticks(timeticks)

        timestamps = []
        if self.setup:
        #Сдался пытаться привязывать время к черточкам во время подготовки буффера
            pass
        else:
            for i in timeticks:
                #Для нужным линий получем сохраненую метку времени, cur_frame отстает от последней линии на display_len
                #чтобы не нужно было работать с неполным буффером
                timestamp = str(self.data[self.cur_frame + self.display_len - i][1])
                #Удаляем дату, проверка для чтения из файла тк там дата уже удалена в строках
                try:
                    while True:
                        timestamp = timestamp[timestamp.index(' ')+1:]
                except ValueError:
                    pass
                #Удаляем лишнии фракции секунды
                timestamp = timestamp[:timestamp.index('.')+3]
                timestamps.append(timestamp)
        self.ax0.set_yticklabels(timestamps)

        #Прокрутка изображения и обновление ползуна
        if self.anim_running and self.cur_frame <= self.frames:
            self._set_frame(self.cur_frame)

            #Отключаем вызовы от изменения значения ползуна чтобы они не вызывались циклично
            self.time_slider.eventson = False
            self.time_slider.set_val(self.cur_frame)
            self.time_slider.eventson = True

            self.fig.canvas.draw_idle()
            self.cur_frame += 1
        return self.mesh

    def _pause(self, *event):
        if self.anim_running:
            self.anim_running = False
            self.pause_button.label.set_text("Resume")
            #эта функция останавливает сам объект анимации, но тогда она перестает опрашивать прибор пока остановлена
            #self.anim.event_source.stop()
        else:
            self.anim_running = True
            self.pause_button.label.set_text("Pause")
            # self.anim.event_source.start()

    def _reset(self, *event):
        #Если работаем с прибором обнуляем все значения, если читаем файл просто идем на начало файла
        if self.readmode == False:
            self.data = []
            self.frames = 0
            self.setup = True
        self.cur_frame = 0
        if not self.anim_running:
            self._pause()

    #Функция должна позволять переключать опрос прибора, не используется
    # def _toggle_scan(self, event):
    #     if self.scanning:
    #         self.scanning = False
    #         self.pause_scan_button.label.set_text("Resume scan")
    #     else:
    #         self.scanning = True
    #         self.pause_scan_button.label.set_text("Stop scan")

    def _slider_update(self, val=0):
    #Вызываеться при изменении значения ползуна
    #Позволяет прокруткой менять кадр, проверка на мин и макс значения и смена кадра
        if val < 0:
            val = 0
        elif val > self.frames - self.display_len:
            val = self.frames - self.display_len
        self.cur_frame = val
        self._set_frame(self.cur_frame)

    def _set_frame(self, frame=0):
    #Смена кадра, проверяем на макс/мин разрешенный кадр
        frame = int(frame)
        #Проверка чтобы предотвратить прокрутку при подготовке (буффер>данные)
        if self.frames <= self.display_len:
            frame = 0
        elif frame < 0:
            frame = 0
        elif frame > self.frames - self.display_len:
            frame = self.frames - self.display_len
        self.cur_frame = frame
        self._update_buf(self.buff, frame)
        self.mesh.set_array(self.buff)

    def animate(self):
    #Выводит окно и запускает анимацию
        plt.show()


if __name__ == '__main__':
    #Обозначаем аргументы и описания
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="file to read from", type=str, default=None)
    parser.add_argument("--start", help="start MHz", type=float, default=2300)
    parser.add_argument("--stop", help="stop MHz", type=float, default=2500)
    parser.add_argument("--step", help="=step MHz", type=float, default=2)
    args = parser.parse_args()

    #Переводим МГц в Гц для передачи прибору
    start = mhz2hz(args.start)
    stop = mhz2hz(args.stop)
    step = mhz2hz(args.step)
    #Находим количество точек в диапазоне
    steps = int(abs(args.stop-args.start)/args.step) + 1
    file = args.file

    #Если файл существует открыть дял чтения, если путь не указан, подключить прибор
    if file:
        try:
            file = open(file, "r")
        except FileNotFoundError:
            print('File not found')
            exit()
    else:
        device = ArinstDevice(device='/dev/ttyACM0')

    #Если файл существует вынимаем из него данные и форматируем в таблицу вида [[массив амплитуд][метка времени]]
    if file:
        #Считываем файл в таблицу строк
        filedata = file.readlines()
        data = []
        #Игнорируем первые две строки тк они информационные без амплитуд
        for line in filedata[2:]:
            #Вынимаем строку без последнего символа (\n)
            line = line[:-1]
            #Разделяем строку в таблицу 'фраз' без пробелов
            line = line.split(' ')
            amp_data = []
            #Собираем массив амплитуд, без первых 2 фраз тк 1 это индекс 2 это метка времени
            for i in range(2,len(line)):
                amp_data.append(int(line[i]))
            #Добавляем метку времени
            data.append([amp_data, line[1]])
        amp_mesh = AmplitudeMesh(data=data, vmin=AMPLITUDE_LOW, vmax=AMPLITUDE_HIGH, display_len=DISPLAY_LENGH)
    else:
    #Если файл не указан запускаем анимацию без указания данных для чтения
        amp_mesh = AmplitudeMesh(vmin=AMPLITUDE_LOW, vmax=AMPLITUDE_HIGH, display_len=DISPLAY_LENGH)
    #Показ окна и запуск анимации, функция plt.show блокирует выполнение кода пока окно не закроеться
    #mathplotlib нативно закрываеться по крестику или при нажатии q
    amp_mesh.animate()

    #Проверяем что мы получали данные от прибора чтобы не перезаписывать уже существующие данные
    if not amp_mesh.readmode:
        #Получаем начальную метку времени, меняет символы на разрешенные в пути файла
        start_time = str(amp_mesh.data[0][1])
        start_time = start_time.replace(' ','_')
        start_time = start_time.replace(':', '-')
        #Избавляемся от фракций секунды
        start_time = start_time[:start_time.index('.')]

        #Собираем путь/имя файла
        logpath = LOGS_PATH + "log_" + start_time

        #Проверка то что файла с таким именем не существует и подбор уникального имени
        if path.exists(logpath):
            itr = 1
            while path.exists(logpath + "_" + str(itr)):
                itr += 1
            logpath += "_" + str(itr)

        logfile = open(logpath, "w")
        #Собираем начало записи, метка времени и использованые аргументы второй строкой
        loghead = "Log start:" + start_time + "\r\n"
        loghead += "args:" + " start " + str(start) + " stop " + str(stop) + " step " + str(step) + "\r\n"
        #Сборка тела записи
        logbody = ''
        for i1 in range(len(amp_mesh.data)):
            linehead = ''
            linedata = ''
            #Преобразуем метку времени, удаляем дату и лишнии фракции
            timestamp = str(amp_mesh.data[i1][1])
            timestamp = timestamp[timestamp.index(' ') + 1:timestamp.index('.') + 3]
            # Создаем начало линии "Индекс" + " " + "метка времени"
            linehead += str(i1) + " " + timestamp
            #Собираем тело строки с амплитудами, разделитель пробел
            for i2 in range(len(amp_mesh.data[i1][0])):
                linedata += " " + str(amp_mesh.data[i1][0][i2])
            #Собираем строку
            logbody += linehead + linedata + "\r\n"
            #Запись и закрытие файла
        logfile.write(loghead + logbody)
        logfile.close

import re
import time
import datetime

class MPPDatBDK2():
    def __init__(self, data="", type="mpp"):
        self.str_data = data
        self.type = type
        self.channel_number = 0
        self.pulse_time = 0
        self.pulse_duration = 0
        self.zero_crossing_number = 0
        self.pulse_maximum = 0
        self.pulse_power = 0
        self.pulse_mean = 0
        self.pulse_noise = 0
        self.row_sec_time = "0000 0000"
        self.parcer(data=self.str_data)
        pass

    def parcer(self, data="", mpp_type="mpp", init_time=[0]):
        self.type=mpp_type
        self.str_data = data
        if data:
            pattern = re.compile(r"([A-F0-9]{4})")
            data_list = pattern.findall(data.replace(" ", "").upper())
            data_int = []
            for var in data_list:
                data_int.append(int(var, 16))
            if len(data_int) >= 13:
                self.channel_number = data_int[0] & 0xFF
                self.row_sec_time = " ".join(data_list[1:3])
                self.pulse_time = self.time_calc(init_time, list_to_int(data_int[1:5]))
                self.pulse_duration = list_to_int(data_int[5:7]) * 0.025E-6
                self.zero_crossing_number = data_int[7]
                self.pulse_maximum = adc_to_voltage_bdk2(data=data_int[8], number=self.channel_number, type=self.type)
                self.pulse_power = adc_to_voltage_bdk2(data=list_to_int(data_int[9:11]), number=self.channel_number, type="mpp") * 0.025E-6
                self.pulse_mean = adc_to_voltage_bdk2(data=data_int[11], number=self.channel_number, type=self.type)
                self.pulse_noise = adc_to_voltage_bdk2(data=data_int[12] / (2 ** 4), number=self.channel_number, type=self.type)
                pass
            else:
                # raise ValueError("Incorrect data length")
                pass
        else:
            # raise ValueError("Incorrect data for process")
            pass

    def time_calc(self, init_time, frame_time):
        init_time.sort()
        frame_time_s = frame_time >> 32
        if len(init_time) == 1:
            time = (frame_time >> 32) * 1 + (frame_time & 0xFFFFFFFF) * 1E-6
        else:
            for i in range(len(init_time)-1):
                if init_time[i] <= frame_time_s < init_time[i+1]:
                    time = init_time[i]*1 + (frame_time - (init_time[i] << 32)) * 1E-6
                    break
                else:
                    us_additional_time = (frame_time - (init_time[len(init_time)-1] << 32)) * 1E-6
                    time = init_time[len(init_time)-1]*1 + us_additional_time
        if (frame_time_s == 0x20DA5C8D or frame_time_s == 0x20dbfb93) and self.channel_number == 4:
            pass
        return time

    def __str__(self):
        output_string = "ch_num = {:d}; time = {:.6f}s; duration = {:.3e}s; zero_cross = {:d}; " \
                        "max = {:.3f}V; power = {:.3E}V*s; mean = {:.3}V; noise = {:.3f}V".format\
                        (self.channel_number, self.pulse_time, self.pulse_duration, self.zero_crossing_number,
                         self.pulse_maximum, self.pulse_power, self.pulse_mean, self.pulse_noise)
        return output_string.replace(".", ",")

    def data(self):
        output_string = "{:d}\t {:.6f}\t {:.3E}\t {:d}\t " \
                        "{:.3f}\t {:.3E}\t {:.3f}\t {:.3f}\n".format \
            (self.channel_number, self.pulse_time, self.pulse_duration, self.zero_crossing_number,
             self.pulse_maximum, self.pulse_power, self.pulse_mean, self.pulse_noise)
        return output_string.replace(".", ",")

    def title(self):
        output_string = "Номер канала\tВремя,с\tДлительность,с\tКол-во переходов через 0\t" \
                        "Максимум,В\tМощность,В*с\tСреднее значение,В\tШум,В\n"
        return output_string.replace(".", ",")


class MPPDatBKAP():
    def __init__(self, data=""):
        self.str_data = data
        self.type = type
        self.number = 0
        self.offset = 0
        self.row_sec_time_full = ""
        self.pulse_time = 0.0
        self.pulse_time_full = ""
        self.pulse_duration = 0
        self.zero_crossing_number = 0
        self.pulse_maximum = 0
        self.pulse_power = 0
        self.pulse_mean = 0
        self.pulse_noise = 0
        self.row_sec_time = 0
        self.mdd_data_old = ["", "", ""]
        self.pulse_time_2 = 0
        self.pulse_time_full_2 = ""
        self.pulse_duration_2 = 0
        self.zero_crossing_number_2 = 0
        self.pulse_maximum_2 = 0
        self.pulse_power_2 = 0
        self.pulse_mean_2 = 0
        self.pulse_noise_2 = 0
        self.est_num = 0
        # self.parcer(data=self.str_data)
        pass

    def parcer(self, data=""):
        self.str_data = data
        if data:
            pattern = re.compile(r"([A-F0-9]{4})")
            data_list = pattern.findall(data.replace(" ", "").upper())
            data_int = []
            for var in data_list:
                data_int.append(int(var, 16))
            if len(data_int) >= 17:
                self.number = (data_int[0] & 0xF) - 1
                self.row_sec_time = list_to_int(data_int[2:4])
                self.row_sec_time_full = self.time_calc(list_to_int(data_int[2:4]))
                self.offset = adc_to_voltage_bkap(data_int[4] & 0xFFFF, number=self.number)
                self.pulse_time = list_to_int(data_int[5:7]) + list_to_int(data_int[7:9])*10E-6
                self.pulse_time_full = self.time_calc(list_to_int(data_int[5:7]))
                self.pulse_duration = list_to_int(data_int[9:11]) * 0.025E-6
                self.zero_crossing_number = data_int[11]
                self.pulse_maximum = adc_to_voltage_bkap(data_int[12], number=self.number)
                self.pulse_power = adc_to_voltage_bkap(data=list_to_int(data_int[13:15])) * 0.025E-6
                self.pulse_mean = adc_to_voltage_bkap(data=data_int[15], number=self.number, type="mean")
                self.pulse_noise = adc_to_voltage_bkap(data=data_int[16] / (2 ** 4), number=self.number)
                #
                self.est_num = data_int[17]
                #
                self.pulse_time_2 = list_to_int(data_int[18:20]) + list_to_int(data_int[20:22])*10E-6
                self.pulse_time_full_2 = self.time_calc(list_to_int(data_int[18:20]))
                self.pulse_duration_2 = list_to_int(data_int[22:24]) * 0.025E-6
                self.zero_crossing_number_2 = data_int[24]
                self.pulse_maximum_2 = adc_to_voltage_bkap(data_int[25], number=self.number)
                self.pulse_power_2 = adc_to_voltage_bkap(data=list_to_int(data_int[26:28])) * 0.025E-6
                self.pulse_mean_2 = adc_to_voltage_bkap(data=data_int[28], number=self.number, type="mean")
                self.pulse_noise_2 = adc_to_voltage_bkap(data=data_int[29] / (2 ** 4), number=self.number)
                pass
            else:
                # raise ValueError("Incorrect data length")
                pass
        else:
            # raise ValueError("Incorrect data for process")
            pass

    def time_calc(self, time_s):
        start_time = time.strptime("2000", "%Y")
        start_time_s = time.mktime(start_time)
        work_time_s = time_s + start_time_s
        work_time = datetime.datetime.fromtimestamp(work_time_s)
        return work_time

    def __str__(self):
        output_string = "ch_num={:d}; offset={:.2E}; frame_time={: 9d}_s; time={:.6f}_s; duration={:.2E}_s; " \
                        "zero_cross={: 5d}; max={:.2E}_V; power={:.2E}_V*s; mean={:.2E}_V; noise={:.2E}_V\n" \
                        "ch_num={:d}; estnum={: 8d}; frame_time={: 9d}_s; time={:.6f}_s; duration={:.2E}_s; " \
                        "zero_cross={: 5d}; max={:.2E}_V; power={:.2E}_V*s; mean={:.2E}_V; noise={:.2E}_V".format\
                        (self.number, self.offset, self.row_sec_time, self.pulse_time, self.pulse_duration,
                         self.zero_crossing_number, self.pulse_maximum, self.pulse_power, self.pulse_mean, self.pulse_noise,
                         self.number, self.est_num, self.row_sec_time, self.pulse_time_2, self.pulse_duration_2,
                         self.zero_crossing_number_2, self.pulse_maximum_2, self.pulse_power_2, self.pulse_mean_2, self.pulse_noise_2)
        return output_string.replace(".", ",")

    def data(self):
        output_string = "{:d}\t{:s}\t{:d}\t{:s}\t{:.6f}\t{:.3E}\t{:d}\t" \
                        "{:.3f}\t{:.3E}\t{:.3f}\t{:.3f}\n".format(
             self.number, self.row_sec_time_full, self.row_sec_time, self.pulse_time_full, self.pulse_time, self.pulse_duration, self.zero_crossing_number,
             self.pulse_maximum, self.pulse_power, self.pulse_mean, self.pulse_noise)
        return output_string.replace(".", ",")

    def data_num(self):
        output_list = [self.number, self.row_sec_time_full, self.row_sec_time, self.pulse_time_full, self.pulse_time, self.pulse_duration, self.zero_crossing_number,
             self.pulse_maximum, self.pulse_power, self.pulse_mean, self.pulse_noise]
        return output_list

    def data_num_2(self):
        output_list = [self.number, self.row_sec_time_full, self.row_sec_time, self.pulse_time_full_2, self.pulse_time_2, self.pulse_duration_2,
                       self.zero_crossing_number_2, self.pulse_maximum_2, self.pulse_power_2, self.pulse_mean_2,
                       self.pulse_noise_2]
        return output_list

    def title(self):
        output_string = "Номер канала\tВремя кадра\tВремя кадра,с\tВремя\tВремя,с\tДлительность,с\tКол-во переходов через 0\t" \
                        "Максимум,В\tМощность,В*с\tСреднее значение,В\tШум,В\n"
        return output_string.replace(".", ",")


class InfBKAP():
    def __init__(self, data=""):
        self.i_1 = 0
        self.i_2 = 0
        self.i_3 = 0
        self.i_4 = 0
        self.i_5 = 0
        self.i_2V5 = 0
        self.i_0V0 = 0
        self.str_data = ""
        pass

    def parcer(self, data):
        self.str_data = data
        if data:
            pattern = re.compile(r"([A-F0-9]{4})")
            data_list = pattern.findall(data.replace(" ", "").upper())
            data_int = []
            for var in data_list:
                data_int.append(int(var, 16))
            if len(data_int) >= 13:
                self.i_2V5 = data_int[22]
                self.i_0V0 = data_int[21]
                self.i_1 = self.current(data_int[4], r_sh=4.7, r_os=10)
                self.i_2 = self.current(data_int[5], r_sh=4.7, r_os=10)
                self.i_3 = self.current(data_int[6], r_sh=4.7, r_os=10)
                self.i_4 = self.current(data_int[7], r_sh=1.8, r_os=10)
                self.i_5 = self.current(data_int[8], r_sh=4.7, r_os=10)
                pass
            else:
                # raise ValueError("Incorrect data length")
                pass
        else:
            # raise ValueError("Incorrect data for process")
            pass

    def __str__(self):
        output_string = "i_1 = {:.1f}; i_2 = {:.1f}; i_3 = {:.1f}; i_4 = {:.1f}; i_5 = {:.1f}; " \
                        "0v = {:d}; 2v5 = {:d};".format\
                        (self.i_1, self.i_2, self.i_3, self.i_4, self.i_5,
                         self.i_0V0, self.i_2V5)
        return output_string.replace(".", ",")

    def current(self, adc,  r_sh=4.7, r_os=10.0):
        try:
            curr = (adc - self.i_0V0)*(2.5 * 1000)/((self.i_2V5 - self.i_0V0)*r_os*r_sh)
        except ZeroDivisionError:
            curr = 0
        return curr


def frame_search(data_str):
    frame_pattern = re.compile(r"(?<=0F0F )0C[01][234] "
                               r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                               r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                               r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                               r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                               r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                               r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                               r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                               r"[A-FB0-9]{4} [A-FB0-9]{4}"
                               )
    frame_list = re.findall(frame_pattern, data_str)
    if frame_list:
        return frame_list[0]
    else:
        return None


def adc_to_voltage_bkap(data, number=0, type="others"):
    if type == "mean":
        if number == 2:
            b = -7.1106
        elif number == 1:
            b = -2.1029
        elif number == 3:
            b = -2.0696
        else:
            b = 0
    else:
        b = 0
    if number == 2:
        return 0.0365 * data + b
    elif number == 1:
        return 0.0108 * data + b
    elif number == 3:
        return 0.001 * data + b
    else:
        return 0.00365 * data + b
    pass


def adc_to_voltage_bdk2(data, number=0, type="mpp")-> float:
    if type == "mpp":
        if number == 1:
            return 0.01 * data - 0.0
        elif number == 2:
            return 0.001 * data - 0.0
        elif number == 3:
            return 0.01 * data - 0.0
        elif number == 4:
            return 0.01 * data - 0.0
        elif number == 5:
            return 0.035 * data - 0.0
        elif number == 6:
            return 0.035 * data - 0.0
        else:
            return 0.035 * data - 0.0
    elif type == "rp":
        if number == 1:
            return 0.001 * data - 0.0
        elif number == 2:
            return 0.001 * data - 0.0
        else:
            return 0.001 * data - 0.0
    return 0


def list_to_int(data_list):
    final_var = 0
    for i in range(len(data_list)):
        final_var += data_list[i] << (len(data_list) - 1 - i)*16
    return final_var

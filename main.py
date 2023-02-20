import ta1_mko as mko
import os
import time
import crc16
import additional_parcing
import re
#
import bkap_tests
import ske_luna_tests
import bdk2_tests
import mbkap_tests
import bdd_mk_tests
import kvv_tests
import ekkd_tests

self_version = "0.3.3"

ta1 = mko.Device()

polling_time = 0
stop_change_interval = 0
stop_change_bdd_pointers = 0
archcount = 1
osc_start = 0

normal_mode = 1
test_mode = 0

log_dir_name = str(os.getcwd()) + "\\" + "Log Files\\" + time.strftime("%Y_%m_%d", time.localtime())
mpp_log_name = str(os.getcwd()) + "\\" + "Log MPP Files\\" + time.strftime("%Y_%m_%d", time.localtime())
log_file = None
mpp_log_file = None
# задание программы
mko_cyclogram = kvv_tests.dv_test

#
mko_polling = mko.PollingProgram(program=mko_cyclogram)
mpp = additional_parcing.MPPDatBKAP()
inf = additional_parcing.InfBKAP()


# параметры для тестирования кол-ва неответов
class FramesError:
    def __init__(self):
        self.busy_cnt = 0
        self.crc_bad_cnt = 0
        self.total_cnt = 0
        self.crc_bad_prc = 0
        self.busy_prc = 0

    def reset(self):
        self.busy_cnt = 0
        self.crc_bad_cnt = 0
        self.total_cnt = 0
        self.crc_bad_prc = 0
        self.busy_prc = 0

    def __str__(self):
        try:
            self.crc_bad_prc = (self.crc_bad_cnt / self.total_cnt)*100
            self.busy_prc = (self.busy_cnt / self.total_cnt)*100
        except ZeroDivisionError:
            self.crc_bad_prc = 0
            self.busy_prc = 0
        repr_str = "crc_bad_prc = %.3f, busy_prc = %.3f, total=%d, crc_bad=%d, busy_cnt=%d" % \
                    (self.crc_bad_prc,
                    self.busy_prc,
                    self.total_cnt,
                    self.crc_bad_cnt,
                    self.busy_cnt
                    )
        return repr_str

    def __repr__(self):
        return str(self)


def create_log_file(file, dir_name="noname", prefix=""):
    try:
        os.makedirs(dir_name)
    except (OSError, AttributeError) as error:
        # print(error)
        pass
    try:
        file.close()
    except (OSError, NameError, AttributeError) as error:
        # print(error)
        pass
    finally:
        pass
    # os.chdir(dir_name)
    file_name = dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ", time.localtime()) + "Лог МКО_" + prefix + ".txt"
    file = open(file_name, 'w')
    return file, file_name

def _calc_tr_res(u_ref, u_sign, r_1):
    if ((u_ref - u_sign) == 0):
        return 0.0
    return r_1 * (u_sign/(u_ref - u_sign))

def _linear_interpolation(x):
    array_x = [803.1, 842.7, 882.2, 921.6, 960.9, 1000.0, 1039.0, 1077.9, 1116.7, 1155.4, 1194.0, 1385, 1758.4, 1758.4, 1758.4, 1758.4]
    array_y = [-50, -40, -30. -20, -10, -00, +10, +20, +30, +40, +50, +100, +200, +200, +200, +200]
    length = len(array_x)
    if x < array_x[0]:
        return array_y[0]
    if x > array_x[length-1]: 
        return array_y[length-1]
    # проходим каждый из отрезков, для определения того, куда попадает X
    for n in range(length):
        if (x >= array_x[n]) & (x <= array_x[n+1]):
            y = array_y[n] + (array_y[n+1] - array_y[n])*((x - array_x[n])/(array_x[n+1] - array_x[n]))
            return y
    return 0

def additional_parcing(data_list):
    p_str = ""
    if mko_cyclogram[0] == "Прямой опрос DV":
        adc_list = [data_list[4], data_list[5]]
        vout_list = [(adc*3.3/4096) for adc in adc_list]
        ptres_list = [_calc_tr_res(5.0, v, 1E3) for v in vout_list]
        t_list = [_linear_interpolation(res) for res in ptres_list]
        p_str += f"\tt1 = ;{adc_list[0]:04X}; v1 = ;{vout_list[0]:.3f};V r1 = ;{ptres_list[0]:.3f}; Ohm T = ;{t_list[0]:.3f};°C;"
        p_str += f"\tt2 = ;{adc_list[1]:04X}; v2 = ;{vout_list[1]:.3f};V r2 = ;{ptres_list[1]:.3f}; Ohm T = ;{t_list[0]:.3f};°C"
    return p_str


def read_and_save(device, i_addr, i_subaddr, i_leng, file):
    global frames
    data_list = device.read_from_rt(i_addr, i_subaddr, i_leng)
    data_str = ""
    i = 0
    for i in range(50):
        # print("%04X" % device.answer_word)
        if (device.answer_word & 0xF800 == device.command_word & 0xF800) & ((device.answer_word & 0x0008) == 0):
            break
        else:
            data_str = "{:.3f}; R; ".format(time.perf_counter()) \
                       + "CW 0x{:04X}; ".format(device.command_word & 0xFFFF) \
                       + "AW 0x{:04X}; ".format(device.answer_word & 0xFFFF) + "RT busy %d times\t" % (i+1)
            data_list = device.read_from_rt(i_addr, i_subaddr, i_leng)
            time.sleep(0.05)
    # busy check
    if "RT busy" in data_str:
        frames.busy_cnt += 1
    #
    crc16_new = crc16.calc(data_list[0: len(data_list) - 1], len(data_list) - 1, endian="big")
    crc16_old = data_list[len(data_list) - 1]
    crc16_state = "CRC OK" if crc16_new == crc16_old else "CRC BAD"
    # CRC_BAD check
    if crc16_new != crc16_old:
        frames.crc_bad_cnt += 1
    # total_calc
    frames.total_cnt += 1
    data_str += "{:.3f}; R; ".format(time.perf_counter()) \
               + "CW 0x{:04X}; ".format(device.command_word & 0xFFFF) + "AW 0x{:04X}: ".format(device.answer_word & 0xFFFF)
    for var in data_list:
        data_str += "{:04X} ".format(var)
    data_str += "; {1:04X}; {0:s};".format(crc16_state, crc16_new)
    # additional parsing
    data_str += additional_parcing(data_list)
    data_str += "\n"
    #
    if file:
        file.write(data_str)
    return data_str[0:len(data_str)-1], data_list


def send_and_save(device, i_addr, i_subaddr, i_data, i_leng, file):
    device.send_to_rt(i_addr, i_subaddr, i_data, i_leng)
    data_str = ""
    for i in range(50):
        if (device.answer_word & 0xF800 == device.command_word & 0xF800) & (device.answer_word & 0x0008) == 0:
            break
        else:
            data_str = "{:.3f}; R; ".format(time.perf_counter()) \
                       + "CW 0x{:04X}; ".format(device.command_word & 0xFFFF) \
                       + "AW 0x{:04X}; ".format(device.answer_word & 0xFFFF) + "RT busy %d times\n" % (i+1)
            device.send_to_rt(i_addr, i_subaddr, i_data, i_leng)
            time.sleep(0.05)
    data_str += "{:.3f}; W; ".format(time.perf_counter()) + "CW 0x{:04X}; ".format(
        device.command_word & 0xFFFF) + "AW 0x{:04X}: ".format(device.answer_word & 0xFFFF)
    for var in i_data:
        data_str += "{:04X} ".format(var)
    data_str += "\n"
    #
    if file:
        file.write(data_str)
    return data_str[0:len(data_str)-1]


def work_interval(start_time):
    return time.perf_counter() - start_time


log_file, log_file_name = create_log_file(log_file, dir_name=log_dir_name, prefix=mko_cyclogram[0])
frames = FramesError()

# цикл опроса
number = 0
data_old = 0
repeat_counter = 0
channel = 0

while 1:
    # ta1.disconnect()
    state = ta1.init()
    if state == 0:
        input("Press Enter to continue...\n")
        time_start = time.perf_counter()
        time_tmp = time_start + mko_polling.cycle[number][0]
        start_cycle_time = time.strftime("%Y_%m_%d %H-%M-%S", time.localtime())
        cycle_leng = mko_polling.cycle[len(mko_polling.cycle) - 1][0]
        stop_cycle_time = time.strftime("%Y_%m_%d %H-%M-%S", time.localtime(time.time() + cycle_leng))
        if normal_mode:
            head_str = f"MKO polling ver {self_version}\n"
            head_str += f"Polling start with cycle <{mko_cyclogram[0]}>, len: {len(mko_polling.cycle)}\n"
            head_str += "Start at {0:s}, finish at {1:s}\n".format(start_cycle_time, stop_cycle_time)
            print(head_str)
            with open(log_file_name, 'a', encoding="utf-8") as l_f:
                l_f.write(head_str + "\n")
        break
    else:
        print("MKO not opened")
    time.sleep(2)
# тестирование
if test_mode:
    start_test_time = time.perf_counter()
    test_result = []
    send_and_save(ta1, 13, 17, [0x000B, 0x0001, 0x01FF, 0x0000], 4, log_file)  # ускоренный режим
    time.sleep(0.1)
    # команда на старт сеанса съема информации
    send_and_save(ta1, 13, 17, [0x0007, 0x0000, 0x0000, 0x0000], 4, log_file)  # старт сеанса съема информации
    for time_out in range(60, 140, 20):
        start_cycle_time = time.strftime("%Y_%m_%d %H-%M-%S", time.localtime())
        print("%.3f: Timeout = %dms" % (work_interval(start_test_time), time_out))
        frames.reset()
        for cnt in range(3000):
            send_and_save(ta1, 13, 18, [0, 0, 0, 0], 4, log_file)
            time.sleep(time_out/1000)
            data_str = read_and_save(13, 14, 32, log_file)
            if cnt % 300 == 0 or "BAD" in data_str[0] or "RT busy" in data_str[0]:
                print("%.3f: Result: %s  %s" % (work_interval(start_test_time), frames, data_str[0]))
        print("%.3f: Result: %s" % (work_interval(start_test_time), frames))
        test_result.append([time_out, frames.crc_bad_prc, frames.busy_prc])
    for var in test_result:
        print("Timeout = %03d, crc_bad=%03.2f, busy=%03.2f" % (var[0], var[1], var[2]))
    pass
# нормальная работа
if normal_mode:

    while 1:
        # цикл проверки подключения МКО
        while 1:
            state = ta1.init()
            if state == 0:
                break
            else:
                print("MKO not opened")
            time.sleep(2)
        time.sleep(0.01)
        if time_tmp <= time.perf_counter():
            # заполняем поля
            addr = mko_polling.cycle[number][1]
            subaddr = mko_polling.cycle[number][2]
            direction = mko_polling.cycle[number][3]
            data = mko_polling.cycle[number][4]
            leng = mko_polling.cycle[number][5]
            log_file = open(log_file_name, "a")
            if direction == 0:
                report_str = send_and_save(ta1, addr, subaddr, data, leng, log_file)
                print(report_str)
                pass
            else:
                report_str, data_list = read_and_save(ta1, addr, subaddr, leng, log_file)
                print(report_str)
                pass
            pass
            log_file.close()
            # сдвигаем номер цикла
            number += 1
            # запоминаем новое время
            if number < len(mko_polling.cycle):
                time_tmp = time_start + mko_polling.cycle[number][0]
            else:
                break
    print(frames)
ta1.disconnect()

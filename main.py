import mko
import os
import time
import crc16
import mpp_data
import re
import bkap_tests
import ske_luna_tests
import bdk2_tests
import mbkap_tests


ta1 = mko.Device()
ta1.disconnect()
state = ta1.connect()
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
mko_cyclogram = ske_luna_tests.all_test

#
mko_polling = mko.PollingProgram(program=mko_cyclogram)
mpp = mpp_data.MPPDatBKAP()
inf = mpp_data.InfBKAP()


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
    os.chdir(dir_name)
    file_name = dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ", time.localtime()) + "Лог МКО_" + prefix + ".txt"
    file = open(file_name, 'w')
    return file, file_name


def read_and_save(i_addr, i_subaddr, i_leng, file):
    global frames
    data_list = ta1.read_from_rt(i_addr, i_subaddr, i_leng)
    data_str = ""
    i = 0
    for i in range(50):
        # print("%04X" % ta1.answer_word)
        if (ta1.answer_word & 0xF800 == ta1.command_word & 0xF800) & ((ta1.answer_word & 0x0008) == 0):
            break
        else:
            data_str = "{:.3f}; R; ".format(time.clock()) \
                       + "CW 0x{:04X}; ".format(ta1.command_word & 0xFFFF) \
                       + "AW 0x{:04X}; ".format(ta1.answer_word & 0xFFFF) + "RT busy %d times\t" % (i+1)
            data_list = ta1.read_from_rt(i_addr, i_subaddr, i_leng)
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
    data_str += "{:.3f}; R; ".format(time.clock()) \
               + "CW 0x{:04X}; ".format(ta1.command_word & 0xFFFF) + "AW 0x{:04X}: ".format(ta1.answer_word & 0xFFFF)
    for var in data_list:
        data_str += "{:04X} ".format(var)
    data_str += "; {1:04X}; {0:s};\n".format(crc16_state, crc16_new)
    #
    if file:
        file.write(data_str)
    return data_str[0:len(data_str)-1], data_list


def send_and_save(i_addr, i_subaddr, i_data, i_leng, file):
    ta1.send_to_rt(i_addr, i_subaddr, i_data, i_leng)
    data_str = ""
    for i in range(50):
        if (ta1.answer_word & 0xF800 == ta1.command_word & 0xF800) & (ta1.answer_word & 0x0008) == 0:
            break
        else:
            data_str = "{:.3f}; R; ".format(time.clock()) \
                       + "CW 0x{:04X}; ".format(ta1.command_word & 0xFFFF) \
                       + "AW 0x{:04X}; ".format(ta1.answer_word & 0xFFFF) + "RT busy %d times\n" % (i+1)
            ta1.send_to_rt(i_addr, i_subaddr, i_data, i_leng)
            time.sleep(0.05)
    data_str += "{:.3f}; W; ".format(time.clock()) + "CW 0x{:04X}; ".format(
        ta1.command_word & 0xFFFF) + "AW 0x{:04X}: ".format(ta1.answer_word & 0xFFFF)
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
    state = ta1.init()
    if state == 0:
        input("Press Enter")
        time_start = time.clock()
        time_tmp = time_start + mko_polling.cycle[number][0]
        start_cycle_time = time.strftime("%Y_%m_%d %H-%M-%S", time.localtime())
        cycle_leng = mko_polling.cycle[len(mko_polling.cycle) - 1][0]
        stop_cycle_time = time.strftime("%Y_%m_%d %H-%M-%S", time.localtime(time.time() + cycle_leng))
        if normal_mode:
            print("Polling start with cycle, len = {:d}".format(len(mko_polling.cycle)))
            print("Start in {0:s}, finish in {1:s}".format(start_cycle_time, stop_cycle_time))
        break
    else:
        print("MKO not opened")
    time.sleep(2)
# тестирование
if test_mode:
    start_test_time = time.perf_counter()
    test_result = []
    send_and_save(13, 17, [0x000B, 0x0001, 0x01FF, 0x0000], 4, log_file)  # ускоренный режим
    time.sleep(0.1)
    # команда на старт сеанса съема информации
    send_and_save(13, 17, [0x0007, 0x0000, 0x0000, 0x0000], 4, log_file)  # старт сеанса съема информации
    for time_out in range(60, 140, 20):
        start_cycle_time = time.strftime("%Y_%m_%d %H-%M-%S", time.localtime())
        print("%.3f: Timeout = %dms" % (work_interval(start_test_time), time_out))
        frames.reset()
        for cnt in range(3000):
            send_and_save(13, 18, [0, 0, 0, 0], 4, log_file)
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
            state = ta1.connect()
            if state == 1:
                break
            else:
                print("MKO not opened")
            time.sleep(2)
        time.sleep(0.01)
        if time_tmp <= time.clock():
            # заполняем поля
            addr = mko_polling.cycle[number][1]
            subaddr = mko_polling.cycle[number][2]
            direction = mko_polling.cycle[number][3]
            data = mko_polling.cycle[number][4]
            leng = mko_polling.cycle[number][5]
            log_file = open(log_file_name, "a")
            if direction == 0:
                report_str = send_and_save(addr, subaddr, data, leng, log_file)
                print(report_str)
                pass
            else:
                report_str, data_list = read_and_save(addr, subaddr, leng, log_file)
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

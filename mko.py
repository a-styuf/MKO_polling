from WDMTMKv2 import *
import time


#  класс работы с МКО #
class Device:
    """
    Device- класс устройства для общения по МКО/МПИ. Необходимо создавать по шаблону:
    метода на запись: send_to_rt(self, addr, subaddr, data, leng), возвращает ответное слово
    метода на чтение: read_from_rt(self, addr, subaddr, leng), возвращает данные с подадреса
    метода на запись команды управления: send_cntrl_command(self, addr, subaddr, leng), возвращает ответное слово
    метода на получение данных для отображения: get_mko_data(self), возвращает: command_word, answer_word, data
    метода на подключение: connect(self)
    метода на отключение: disconnect(self)

    параметр ответное слово: answer_word
    параметр командное слово: command_word

    параметр имени устройства: name
    параметр состояние устройства: state - 0-устройство подключилось,
                                           1-устройство не подключено,
                                           2-устройство не подключено к МКО ОУ
    параметр состояние устройства: bus_state -  0-неопределено,
                                                1-используется основная шина,
                                                2-используется резервная шина

    при каждой транзакции необходимо сбрасывать значение командого и ответного слова и данные на значение 0xFEFE
    """
    def __init__(self):
        self.name = "TA1-USB"
        self.bus = BUS_1
        self.bus_state = 0
        self.TTml_obj = TTmkEventData()
        self.state = 1
        self.frame = []

    def init(self):
        self.state = TmkOpen()  # функция подключает драйвер к вызвавшему функцию процессу
        tmkdone(ALL_TMKS)
        tmkconfig(0)
        bcreset()
        bcgetstate()
        bcdefbase(1)
        bcgetbase()
        bcdefbus(self.bus)
        bcgetbus()
        tmkgethwver()
        return self.state

    read_status = 0x0000
    answer_word = 0xFFFF
    command_word = 0x0000

    def connect(self):
        self.init()
        if self.state == 0:
            return 1
        else:
            return 0

    def disconnect(self):
        TmkClose()
        self.state = 1
        return 1  # нет способа проверить успешность отключения

    def change_bus(self):
        if self.bus == BUS_2:
            self.bus = BUS_1
        else:
            self.bus = BUS_2
        # print(self.bus)
        bcdefbus(self.bus)

    def send_to_rt(self, addr, subaddr, data, leng):
        self.bus_state = 0
        self.change_bus()
        if subaddr <= 0:
            subaddr = 1
        for i in range(36):
            bcputw(i, 0xFAFA)
        control_word = ((addr & 0x1F) << 11) + (0x00 << 10) + ((subaddr & 0x1F) << 5) + (leng & 0x1F)
        bcdefbus(self.bus)
        bcputw(0, control_word)
        for i in range(leng):
            bcputw(i+1, data[i])
        bcstart(1, DATA_BC_RT)
        time.sleep(0.001)
        self.command_word = bcgetw(0)
        self.answer_word = bcgetansw(DATA_BC_RT) & 0xFFFF
        # self.print_base()
        # print("cw = %04X; aw = %04X; alt_aw = %04X" % (self.command_word, bcgetw(1+leng), bcgetansw(DATA_BC_RT) & 0xFFFF))
        if (self.answer_word & 0xF800) != (self.command_word & 0xF800):
            self.bus_state = 1 if self.bus == BUS_1 else 2
            self.change_bus()
            bcputw(0, control_word)
            bcstart(1, DATA_BC_RT)
            time.sleep(0.001)
            self.command_word = bcgetw(0)
            self.answer_word = bcgetansw(DATA_BC_RT) & 0xFFFF
            # self.print_base()
            # print("cw = %04X; aw = %04X; alt_aw = %04X" % (self.command_word, bcgetw(1+leng), self.answer_word))
        if (self.answer_word & 0xF800) != (self.command_word & 0xF800):
            self.state = 2
        return self.answer_word

    def send_cntrl_command(self, addr, subaddr, leng):
        self.bus_state = 0
        self.change_bus()
        control_word = ((addr & 0x1F) << 11) + (0x00 << 10) + ((subaddr & 0x1F) << 5) + (leng & 0x1F)
        bcputw(0, control_word)
        bcstart(1, CTRL_C_A)
        time.sleep(0.001)
        self.command_word = bcgetw(0)
        self.answer_word = bcgetansw(CTRL_C_A) & 0xFFFF
        if (self.answer_word & 0xF800) != (self.command_word & 0xF800):
            self.state = 2
        return self.answer_word

    def read_from_rt(self, addr, subaddr, leng):
        self.bus_state = 0
        self.change_bus()
        if subaddr <= 0:
            subaddr = 1
        for i in range(36):
            bcputw(i, 0xFAFA)
        control_word = ((addr & 0x1F) << 11) + (0x01 << 10) + ((subaddr & 0x1F) << 5) + (leng & 0x1F)
        bcdefbus(self.bus)
        bcputw(0, control_word)
        bcstart(1, DATA_RT_BC)
        time.sleep(0.001)
        self.command_word = bcgetw(0)
        self.answer_word = bcgetansw(DATA_RT_BC) & 0xFFFF
        # print("cw = %04X; aw = %04X; alt_aw = %04X" % (self.command_word, bcgetw(1), bcgetansw(DATA_RT_BC) & 0xFFFF))
        if (self.answer_word & 0xF800) != (self.command_word & 0xF800):
            self.bus_state = 1 if self.bus == BUS_1 else 2
            self.change_bus()
            bcputw(0, control_word)
            bcstart(1, DATA_RT_BC)
            time.sleep(0.001)
            self.command_word = bcgetw(0)
            self.answer_word = bcgetansw(DATA_RT_BC) & 0xFFFF
            # print("cw = %04X; aw = %04X; alt_aw = %04X" % (self.command_word, bcgetw(1), bcgetansw(DATA_RT_BC) & 0xFFFF))
        if (self.answer_word & 0xF800) != (self.command_word & 0xF800):
            self.state = 2
        self.frame = []
        for i in range(2, 2+leng):
            word = bcgetw(i)
            self.frame.append(word)
        return self.frame

    def get_mko_data(self):
        # print("%04X" % self.answer_word)
        return self.command_word, self.answer_word, self.frame

    def print_base(self):
        print_str = ""
        for i in range(35):
            print_str += "%04X " % bcgetw(i)
        print(print_str)
        pass

# класс для разбора подпрограмм для создания циклограмм
# циклограмма согласно данному шаблону
# ["Name", [[Address, Subaddress, Wr/R, [Data], Data leng, Start time, Finish time, Interval, Delay], [...], [...]]]
#    |          |          |        |      |         |          |           |          |         |
#    |          |          |        |      |         |          |           |          |         -- Задержка отправки
#    |          |          |        |      |         |          |           |          --- Интервал отправки
#    |          |          |        |      |         |          |           - Время остановки посылок
#    |          |          |        |      |         |          --- Время старта отправки от запуска программы
#    |          |          |        |      |         --- Длина данных для приема/отправки
#    |          |          |        |      ------------- Данные для отправки (при приеме не имеет значения)
#    |          |          |        -------------------- Отправка - "0", Прием - "1"
#    |          |          ----------------------------- Подадрес
#    |          ---------------------------------------- Адрес ОУ
#    --------------------------------------------------- Имя циклограммы

class PollingProgram:
    def __init__(self, program=[]):
        program_def = ["None", [0, 0, 0, [0], 0, 0, 0, 0.1, 0]]
        self.program = program if program else program_def
        self.name = self.program[0]
        self.cycle = []
        self.parcer()

    def parcer(self):
        for i in range(len(self.program[1])):
            start_time = self.program[1][i][5]
            stop_time = self.program[1][i][6]
            interval = self.program[1][i][7]
            delay = self.program[1][i][8]
            try:
                tr_number = int((stop_time - start_time)//interval)
            except ZeroDivisionError:
                tr_number = 1
            for j in range(tr_number):
                time = start_time + j*interval + delay
                addr = self.program[1][i][0]
                subaddr = self.program[1][i][1]
                direct = self.program[1][i][2]
                data = self.program[1][i][3]
                leng = self.program[1][i][4]
                data_set = [time, addr, subaddr, direct, data, leng]
                # print(data_set)
                self.cycle.append(data_set)
        self.cycle.sort()
        # print(self.cycle)
        pass

        pass


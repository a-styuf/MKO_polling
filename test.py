import mko
import time

test_program = ["Test", [[19, 4,  0, [0, 0, 0],  3,  0.0, 20.0, 0.5, 0.00],
                         [19, 12, 1, [0],        32, 0.0, 20.0, 0.5, 0.05]]]

mko_polling = mko.PollingProgram(program=test_program)
ta1 = mko.TA1()
state = ta1.init()
while 1:
    if state == 1:
        state = ta1.init()
        if state == 0:
            print("MKO opened")
            break
        else:
            print("MKO not opened")
    time.sleep(2)


number = 0
time_start = time.clock()
time_tmp = time_start + mko_polling.cycle[number][0]
while number < len(mko_polling.cycle):
    time.sleep(0.001)
    if time_tmp <= time.clock():
        time_tmp = time_start + mko_polling.cycle[number][0]
        # заполняем поля
        addr = mko_polling.cycle[number][1]
        subaddr = mko_polling.cycle[number][2]
        direction = mko_polling.cycle[number][3]
        data = mko_polling.cycle[number][4]
        leng = mko_polling.cycle[number][5]
        # отладка
        print("{:.3f}".format(time.clock()), addr, subaddr, data, leng, direction)
        # отправка команды
        if direction == 0:
            ta1.SendToRT(addr, subaddr, leng)
            pass
        else:
            ta1.ReadFromRT(addr, subaddr, data, leng)
            pass
        pass
        # сдвигаем номер цикла
        number += 1




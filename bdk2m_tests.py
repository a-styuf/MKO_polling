# класс для разбора подпрограмм для создания циклограмм
# циклограмма согласно данному шаблону
# ["Name", [[Address, Subaddress, Wr/R, [Data], Data leng, Start time, Finish time, Interval, Delay], [...], [...]]]
#    |          |          |        |      |         |          |           |          |         |
#    |          |          |        |      |         |          |           |          |         -- Задержка отправки
#    |          |          |        |      |         |          |           |          --- Интервал отправки, c
#    |          |          |        |      |         |          |           - Время остановки посылок, c
#    |          |          |        |      |         |          --- Время старта отправки от запуска программы, c
#    |          |          |        |      |         --- Длина данных для приема/отправки
#    |          |          |        |      ------------- Данные для отправки (при приеме не имеет значения)
#    |          |          |        -------------------- Отправка - "0", Прием - "1"
#    |          |          ----------------------------- Подадрес
#    |          ---------------------------------------- Адрес ОУ
#    --------------------------------------------------- Имя циклограммы

# Загатовка под чтение данных МРИНД

def mrind_req_ans_form(offset=2010, num=0, leng_wd = 16, delay_ms = 100, full_leng=512, time_s = 10.0):
    mko_addr = 13
    tech_sa = 30
    tech_sa_ib_cmd = 5
    mrind_ib_id = 10
    addr = num*leng_wd + offset
    #
    if (addr - offset) < full_leng:
        pass
    else:
        raise ValueError("address is greater than maximum address")
    # формирование массива на отправку в МКО
    word_array = []
    word_array.append(tech_sa_ib_cmd)  # set cmd number
    word_array.append((mrind_ib_id << 8) | (0x03 << 0))  # set internal bus id & set F-code для чтения данных
    word_array.append(addr)  # set register address
    word_array.append(leng_wd)  # set internal bus id    
    #
    return [mko_addr, tech_sa, 0, word_array, len(word_array), time_s, time_s, 0.0, 0.0], [mko_addr, tech_sa, 1, [], 32, time_s, time_s, 0.0, delay_ms] 

start_time, step = 20, 0.5
mrind_osc_cmds = []
reg_num = 16
full_leng = 512
for i in range(0, full_leng//reg_num):
    mrind_osc_cmds.extend(mrind_req_ans_form(num = i, leng_wd=reg_num, delay_ms=200, full_leng=full_leng,  time_s = start_time + step*i))

mrind_osc = ["Вычитывание осциллограммы МРИНД", [
    # Инициализация КВВ
    [13, 17, 0, [0x0002, 0x0000, 0x0000, 0x0000], 4, 0, 0, 0.0, 0.0],
    # Установка времени
    [13, 17, 0, [0x0001, 0x0000, 0x0000, 0x003C], 4, 0, 0, 0.0, 15.0],
]]
mrind_osc[1].extend(mrind_osc_cmds)

if __name__ == "__main__":
    print(mrind_osc[0])
    for cmd in mrind_osc[1]:
        print(cmd)



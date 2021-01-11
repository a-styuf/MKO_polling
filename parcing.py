import re


input_file_name = "D:\YandexDisk\Work\Python\MKO_polling_#03\Лог МКО БЭ БДК2 _Polling_ от 2018_05_22 17-12-43.txt"
output_file_name = input_file_name.split(".")[0] + "_DIR_ADC_.csv"
input_file = open(input_file_name, "r")
output_file = open(output_file_name, "a")
file_list = input_file.read().split("\n")


def inf_read_and_print_bkap(mko_string):
    inf_pattern = re.compile(r"(?<=0F0F )0C[01][1] "
                             r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                             r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                             r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                             r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                             r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                             r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                             r"[A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} [A-FB0-9]{4} "
                             r"[A-FB0-9]{4} [A-FB0-9]{4}"
                             )
    inf_list = re.findall(inf_pattern, mko_string)
    dir_list = []
    if inf_list:
        pattern = re.compile(r"([A-F0-9]{4})")
        data_list = pattern.findall(inf_list[0].replace(" ", "").upper())
        data_int = []
        for v in data_list:
            data_int.append(int(v, 16))
        dir_list = [(data_int[2] << 16) + (data_int[3] << 0)]
        dir_list.extend(data_int[23:29])
    return dir_list


for var in file_list:
    data_dir = inf_read_and_print_bkap(var)
    if data_dir:
        print(data_dir)
        str = ""
        for var in data_dir:
            str += "{:d};".format(var)
            pass
        str += "\n"
        output_file.write(str)

input_file.close()
output_file.close()
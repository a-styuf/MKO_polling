import time
import crc16


def podorognik(file_name):
    old_f = open(file_name, "r")
    print("ok")
    line_num = 0
    new_f = open(file_name[:len(file_name)-4] + "_repaired.txt", "w")
    for line in old_f:
        line_num += 1
        line_words = line.split(" ")
        if line_words[7] == "0F0F":
            line_time = line_words[0]
            cw = line_words[5]
            aw = line_words[6]
            crc = crc16.calc_str(" ".join(line_words[7:7+31]))
            frame = " ".join(line_words[7:7+31]) + " " + "{:04X}".format(crc)
            new_line = line_time + " CW: " + cw + " AW: " + aw + " : " + frame
            new_f.write(new_line + "\n")
            print("ok", crc,  line_num, new_line)
    pass


def obrezanie(file_name):
    old_f = open(file_name, "r")
    print("ok")
    line_num = 0
    new_f = open(file_name[:len(file_name)-4] + "_repaired.txt", "w")
    for line in old_f:
        line_num += 1
        if line.find("BAD") == -1:
            new_line = line
        else:
            new_line = "CHIK-CHIK"
        new_f.write(new_line)
        print(line_num, new_line)
    pass


if __name__ == "__main__":
    # obrezanie("Log Files\\2017_09_09\\Лог МКО БЭ БДК2 от 2017_09_09 16-04-15.txt")
    podorognik("Log Files\\2017_09_10\\Лог МКО БЭ БДК2 от 2017_09_10 13-11-01.txt")

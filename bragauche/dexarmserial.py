import serial
import serial.tools.list_ports


class DexArmSerial:

    BAUDS = 115200

    @staticmethod
    def list_ports():
        return list(serial.tools.list_ports.comports())

    def __init__(self):
        self.status = False

    def open(self, port, bauds=None):
        if not bauds:
            bauds = self.BAUDS
        self.port = port
        try:
            self.ser_v = serial.Serial(port, bauds, timeout=3000)
            if self.ser_v.is_open:
                self.status = True
            else:
                self.status = False
        except Exception as err:
            self.status = False
            print(err, self.port)
        else:
            self.port = port
            self.bauds = bauds
        return self.status

    def close(self):
        self.ser_v.close()
        self.status = False
        print(f"Closing {self.port}")

    def send(self, data):
        if self.status:
            # Ensure input is empty of leftovers
            self.ser_v.reset_input_buffer()
            self.ser_v.write(data.encode("ascii"))
            print("==>", str(data.encode("ascii")))
            while True:
                resp = self.ser_v.read_until()
                print("<==", resp)
                if b"ok" in resp:
                    return
                elif b"Unknown command" in resp:
                    print("=!=", str(resp), "send error")
                    self.ser_v.write(data.encode("ascii"))
                    print("=!>", str(data.encode("ascii")))

    def read(self):
        # status = False
        # while status:
        #     data = self.ser_v.read_until()
        #     print(data)
        #     if "ok\\" in str(data):
        #         print(str(data))
        #         return
        pass


class Gcode(object):

    MAX_HIGH = [0, 295, 167]

    def __init__(self, serial: DexArmSerial):
        self.serial = serial

    def init(self):
        return self.serial.send("M1112\r\n")

    def home(self):
        return self.XYZ(self.MAX_HIGH[0], self.MAX_HIGH[1], self.MAX_HIGH[2])

    def Z(self, z):
        return self.serial.send(f"G0Z{z}\r\n")

    def X(self):
        return False

    def Y(self):
        return False

    def XYZ(self, x, y, z):
        return self.serial.send(f"G0X{x}Y{y}Z{z}F10000\r\n")

    def XY(self, x, y):
        return self.serial.send(f"G0X{x}Y{y}\r\n")

    def M100x(self, x):
        return self.serial.send(f"M100{x}\r\n")

    def speed(self, val):
        return self.serial.send(f"G0F{val}\r\n")

    def wait(self):
        return self.serial.send("M400\r\n")

    def init_rotary(self):
        self.serial.send("M888 P6\r\n")
        return self.serial.send("M2100\r\n")

    def rotate(self, r):
        return self.serial.send(f"M2101 R{r}\r\n")

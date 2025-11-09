import serial, time

ser = serial.Serial("COM5", 9600, timeout=1)

end = time.time() + 3
while time.time() < end:
    data = ser.read(40)
    if data:
        print(data.hex(" "))

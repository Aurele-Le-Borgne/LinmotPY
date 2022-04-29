from os import times
import sys
from time import sleep
import serial

sys.path.append('.')
from C1100 import C1100

DEVICE_ID = 0x04
COMMUNICATION_SPEED = 9600
#NUMBER_OF_MESSAGE = 1000

ser = serial.Serial(
    port = 'COM5',
    baudrate=COMMUNICATION_SPEED,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=0)

token = '01'
PositionVector = [0x01, 0x00, 0x15, 0x02, 0x00, 0x02, 0x03, 0x01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
WarnFlagsTags = ["Motor Hot Sensor","Motor Short Time Overload","Motor Supply Voltage Low","Motor Supply Voltage High","Position Lag Always","Reserved","Drive Hot","Motor Not Homed","PTC Sensor 1 Hot","PTC Sensor 2 Hot","RR Hot Calculated","Reserved","Reserved","Reserved","Interface Warn Flag","Application Warn Flag"]
CtrlFlagsTags = ["Switch On","STO","/Quick Stop","Enable Operation","/Abort","/Freeze","Go To Position","Error Acknowledge","Jog Move+","Jog Move-","Special Mode","Home","Clearance Check","Go To Initial Position","Linearizing","Phase Search"]
CtrlWord = 0
CountNibble = 0

timeStep = 0.1
nbMesures = 50

def Init():
    WriteControlWord([])
    return
def Run():
    count = 0
    while(1):
        count += 1
        Request = [0x01, 0x11, 0x05, 0x02, 0x00, 0x01, 0x3F, 0x00, 0x04]
        ser.write(Request)
        ser.flush()
        response = ser.read(16)
        ser.flushInput()
        
        if (len(response)==16):
            print("> ok")
            txt = ""
            for i in range(len(response)):
                txt += hex(response[i]) + ", "
            print(txt)
            return 0
        if (count >= 100):
            print("> failure")
            return -1

def Unlock():
    WriteControlWord(["STO","/Quick Stop", "Enable Operation","/Abort","/Freeze"])
    printControlWord()
    return
def WriteControlWord(flags):
    global CtrlWord
    CtrlWord = 0
    for i in range(len(flags)):
        CtrlWord |= (1<<CtrlFlagsTags.index(flags[i]))

    CtrlWrdLow = 0
    CtrlWrdHigh = 0
    CtrlWrdLow |= CtrlWord & 0x00FF
    CtrlWrdHigh |= (CtrlWord >> 8)
    
    Request = [0x01, 0x00, 0x05, 0x02, 0x00, 0x01, CtrlWrdLow, CtrlWrdHigh, 0x04]
    CtrlWord = CtrlWrdHigh<<8 | CtrlWrdLow
    ser.write(Request)
    ser.flush()
    sleep(0.02)
    response = ser.read(16)
    txt=""
    for i in range(len(response)):
        txt += hex(response[i]) + "\n"
    return response
def Home():
    return WriteControlWord(["Switch On","STO","/Quick Stop", "Enable Operation","/Abort","/Freeze","Home"])
def ErrorAck():
    return WriteControlWord(["Switch On","STO","/Quick Stop", "Enable Operation","/Abort","/Freeze","Error Acknowledge"])
def goToPosition(distance):
    WriteControlWord(["Switch On","STO","/Quick Stop","Enable Operation","/Abort","/Freeze"])
    global CountNibble

    CountNibble = (CountNibble+1)&0x0F
    print("eirbfzirbfi: " + hex(CountNibble))
    Request = [0x01, 0x00, 0x09, 0x02, 0x00, 0x02, CountNibble, 0x02, 0x00, 0x00, 0x00, 0x00, 0x04]
    #Request = [0x01, 0x00, 0x15, 0x02, 0x00, 0x02, 0x03, 0x01, 0xF0, 0x49, 0x02, 0x00, 0x40, 0x42, 0x0F, 0x00, 0x40, 0x42, 0x0F, 0x00, 0x40, 0x42, 0x0F, 0x00, 0x04]
    distance = int(distance) *10000
    
    Request[8] = distance & 0x000000FF
    Request[9] = (distance & 0x0000FF00) >> 8
    Request[10] = (distance & 0x00FF0000) >> 16
    Request[11] = (distance & 0xFF000000) >> 24

    ser.write(Request)
    ser.flush()
    sleep(0.05)
    response = ser.read(16)
    ser.flushInput()
    return response

def goToPosition2(targetPosition, maximalVelocity, acceleration, deceleration):
    WriteControlWord(["Switch On","STO","/Quick Stop","Enable Operation","/Abort","/Freeze"])
    for i in range(4):
        var = 0x00
        if (i==0):
            var = targetPosition
        if (i==1):
            var = maximalVelocity
        if (i==2):
            var = acceleration
        if (i==3):
            var = deceleration
        
        PositionVector[(i*4)+8] = (var & 0xff)
        PositionVector[(i*4)+9] = ((var >> 8) & 0xff)
        PositionVector[(i*4)+10] = ((var >> 16) & 0xff)
        PositionVector[(i*4)+11] = ((var >> 24) & 0xff)
    
    PositionVector[24] = 0x04
    txt = "> TX: "
    for i in range(len(PositionVector)):
        txt += hex(PositionVector[i]) + ", "
    print(txt)
    ser.write(PositionVector)
    sleep(2)
    response = ser.read(16)
    return response


def getNibble():
    Request = [0x01,0x00,0x05,0x02,0x00,0x03,(0x1DB0 & 0x00FF),(0x1DB0 >>8),0x04]
    ser.write(Request)
    ser.flush()
    sleep(0.05)
    response = ser.read(20)
    ser.flushInput()
    global CountNibble
    if (len(response)==20):
        CountNibble = response[15] & 0x0F
        return(CountNibble)
    else: return -1
def getCurrent():
    """ Old code not using C1100 class
    Request = [0x01,0x00,0x05,0x02,0x00,0x03,(0x1B93 & 0x00FF),(0x1B93 >>8),0x04]
    ser.write(Request)
    ser.flush()
    response = ser.read(20)
    ser.flushInput()
    if (len(response)==20):
        val = response[15] | (response[16]<<8) | (response[17]<<16) | (response[18]<<24)
        val -= (val & 0x80000000) << 1
        val = val/1000
        return(val)
    else: return
    """
    global controler
    return controler.getCurrent()

def getPosition():
    """ Old code not using C1100 class
    RequestDefaultResponse = [0x01 , 0x00 , 0x03 , 0x02, 0x01, 0x00, 0x04]
    ser.write(RequestDefaultResponse)
    ser.flush()
    response = ser.read(16)
    ser.flushInput()
    if (len(response)==16):
        val = response[11] | (response[12]<<8) | (response[13]<<16) | (response[14]<<24)
        val -= (val & 0x80000000) << 1
        val = val/10000
        return(val)
    else: return -666"""
    global controler
    return controler.getPosition()

def getWarning():

    """ Old code not using C1100 class
    req = [0x01, 0x00, 0x03, 0x02, 0x03, 0x00, 0x04]
    ser.write(req)
    ser.flush()
    ser.flushOutput()
    resp = ser.read(20)
    ser.flushInput()
    if (len(resp)==20):
        word = resp[15] | (resp[16]<<8)
        return word
    else:
        print("error in warning detail response (len:"+str(len(resp))+")")
        return -1"""
    global controler
    return controler.getWarning
        
def getStatusWord():
    req = [0x01, 0x00, 0x03, 0x02, 0x01, 0x00, 0x04]
    ser.write(req)
    ser.flush()
    resp = ser.read(16)
    ser.flushInput()
    if (len(resp) == 16):
        word = resp[7] | (resp[8]<<8)
        return word
    else:
        print("no response from status word request")
        return -1    

def printStatusWord():
    word = getStatusWord()
    if(word == -1):
        print("Error")
        return

    else:
        print('\033[1m' + "Status: " + hex(word) + '\033[0m')
        table = ["Operation Enabled","Switch On Active","Enable Operation","Error","Safety Volt Enable","/Quick Stop","Switch On Locked","Warning","Event Handler Active","Special Motion Active","In Target Position","Homed","Fatal Error","Motion Active","Range Indicator 1","Range Indicator 2"]
        txt = ""
        for i in range(len(table)):
            txt += str(i)+"\t"
            if (word&(1<<i) != 0):
                txt += '\033[1m' + "1\t" + table[i] + '\033[0m\n'
            else:
                txt += "0\t" + table[i] + "\n"
        print(txt)
        if (word & (1<<7)!=0) | (word & (1<<3)!=0):
            sleep(0.3)
            output = getWarning()
            if (output!=-1):
                printWarning(output)
        return

def printWarning(word):
    print('\033[1m\033[1;33;40m' + "Warning code : " + hex(word) + '\033[1;33;40m\033[0m\n')
    txt = ""
    for i in range(16):
        txt += str(i)+"\t"
        if (word&(1<<i) != 0):
            txt += '\033[1m\033[1;33;40m' + "1\t" + WarnFlagsTags[i] + '\033[1;33;40m\033[0m\n'
        else:
            txt += "0\t" + WarnFlagsTags[i] + "\n"
    print(txt)
    return

def printDefaultRespTable(trame):
    text = "Byte\t|Value\t|Description\n"
    text += "0\t|" + hex(trame[0]) + "\t|Fix ID telegram start\n"
    text += "1\t|" + hex(trame[1]) + "\t|MACID\n"
    text += "2\t|" + hex(trame[2]) + "\t|Data length\n"
    text += "3\t|" + hex(trame[3]) + "\t|Fix ID start data\n"
    text += "4\t|" + hex(trame[4]) + "\t|Sub ID: Default Response\n"
    text += "5\t|" + hex(trame[5]) + "\t|Main ID: Response Message\n"
    text += "6\t|" + hex(trame[6]) + "\t|Communication State OK\n"
    text += "7\t|" + hex(trame[7]) + "\t|Status Word Low Byte\n"
    text += "8\t|" + hex(trame[8]) + "\t|Status Word High Byte\n"
    text += "9\t|" + hex(trame[9]) + "\t|State Var Low Byte\n"
    text += "10\t|" + hex(trame[10]) + "\t|State Var High Byte (MainState)\n"
    text += "11\t|" + hex(trame[11]) + "\t|Actual Position Low Word Low Byte\n"
    text += "12\t|" + hex(trame[12]) + "\t|Actual Position Low Word High Byte\n"
    text += "13\t|" + hex(trame[13]) + "\t|Actual Position High Word Low Byte\n"
    text += "14\t|" + hex(trame[14]) + "\t|Actual Position High Word High Byte\n"
    text += "15\t|" + hex(trame[15]) + "\t|Fix ID telegram end"
    print(text)
    print("\n\n\n")

def printControlWord():
    print('\033[1m' + "Control Word: " + hex(CtrlWord) + '\033[0m')
    txt = ""
    for i in range(len(CtrlFlagsTags)):
        txt += str(i) + "\t"
        if (CtrlWord&(1<<i)!=0):
            txt += '\033[1m' + "1\t" + CtrlFlagsTags[i] + '\033[0m'+ "\n"
        else:
            txt += "0\t" + CtrlFlagsTags[i] + "\n"
    print(txt)
    return


# Debut Main
controler = C1100()
controler.InitControler()

if (ser.isOpen()==False):
    print("Echec de l'ouverture du port")

else:
    CountNibble = getNibble()
    print("Port ouvert")
    print("[ENTERING MAIN...]")
    while(1):
        command = input()
        if (command == "getPos"):
            print(">getPos")
            print(getPosition())
            sleep(0.5)
        elif (command == "home"):
            print(">home")
            Home()
            sleep(0.5)
        elif (command == "status"):
            print(">status")
            printStatusWord()
            sleep(0.5)
        elif (command == "ctrlWord"):
            print(">ctrlWord: " + hex(CtrlWord))
            printControlWord()
            sleep(0.5)
        elif (command.find("goToPos")!=-1):
            val = command.replace("goToPos","")
            val = val.replace(" ","")
            val = int(val) * 10000
            print(">goToPos")
            resp = goToPosition(val)
            txt = ""
            for i in resp:
                txt += hex(i) + ", "
            print(txt)
            sleep(0.5)
        elif (command.find("moveTo")!=-1):
            val = command.replace("moveTo","")
            val = val.replace(" ","")
            print(">moveTo: " + val)
            resp = goToPosition2(int(val)*10000, 0x000F4240, 0x000F4240, 0x000F4240)
            txt = "> RX: "
            for i in range(len(resp)):
                txt += hex(resp[i]) + ", "
            print(txt)
            print("Default response ? -> test:")
            printDefaultRespTable(resp)
            sleep(0.5)

        elif (command == "batchGetPos"):
            for i in range(50):
                sleep(0.05)
                print(" " + str(i+1) + "\t" + str(getPosition()))
            sleep(0.5)
        elif (command == "exit"):
            break
        elif (command == "ack"):
            print(">ack")
            ErrorAck()
            sleep(0.05)
        elif (command == "init"):
            print(">init")
            Init()
            sleep(0.05)
        elif (command == "unlock"):
            print(">unlock: "  + hex(CtrlWord))
            Unlock()
            sleep(0.05)
        elif (command == "getCurrent"):
            print(">getCurrent")
            print(getCurrent())
            sleep(0.5)
        elif (command == "batchGetCurrent"):
            for i in range(50):
                sleep(0.05)
                print(" " + str(i+1) + "\t" + str(getCurrent()))
            sleep(0.5)
        elif (command == "run"):
            print(">run")
            Run()
            sleep(0.05)
        elif (command == "help"):
            print("Commandes:")
            print(" init")
            print(" unlock")
            print(" home")
            print(" status")
            print(" ctrlWord")
            print(" getPos")
            print(" getCurrent")
            print(" batchGetPos")
            print(" batchGetCurrent")
            print(" goToPos 'x'")
            print(" moveTo 'x'")
            print(" ack")
            print(" exit")
            print(" run")
        else: print("type help for help")
            
        command = ""
    
    print("[CLOSING]")
    ser.close()

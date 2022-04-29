from time import sleep
import serial

class C1100:
    """Classe du contrôleur linmot"""

    DEVICE_ID = 0x04
    COMMUNICATION_SPEED = 9600
    COM = serial.Serial(
        port = 'COM5',
        baudrate=COMMUNICATION_SPEED,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0)

    CountNibble = 0 # = PositionVector[6]
    PositionVector = [0x01, 0x00, 0x15, 0x02, 0x00, 0x02, 0x00, 0x01,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    WarnFlagsTags = ["Motor Hot Sensor","Motor Short Time Overload","Motor Supply Voltage Low","Motor Supply Voltage High","Position Lag Always","Reserved","Drive Hot","Motor Not Homed","PTC Sensor 1 Hot","PTC Sensor 2 Hot","RR Hot Calculated","Reserved","Reserved","Reserved","Interface Warn Flag","Application Warn Flag"]
    CtrlFlagsTags = ["Switch On","STO","/Quick Stop","Enable Operation","/Abort","/Freeze","Go To Position","Error Acknowledge","Jog Move+","Jog Move-","Special Mode","Home","Clearance Check","Go To Initial Position","Linearizing","Phase Search"]
    CtrlWord = 0

    def __init__(self):
        if (self.COM.isOpen()==False):
            print("Echec de l'ouverture du port")
            return -1

    def WriteControlWord(self,flags):
        self.CtrlWord = 0
        for i in range(len(flags)):
            self.CtrlWord |= (1<<self.CtrlFlagsTags.index(flags[i]))

        CtrlWrdLow = 0
        CtrlWrdHigh = 0
        CtrlWrdLow |= self.CtrlWord & 0x00FF
        CtrlWrdHigh |= (self.CtrlWord >> 8)
        
        Request = [0x01, 0x00, 0x05, 0x02, 0x00, 0x01, CtrlWrdLow, CtrlWrdHigh, 0x04]
        self.CtrlWord = CtrlWrdHigh<<8 | CtrlWrdLow
        self.COM.write(Request)
        self.COM.flush()
        response = self.COM.read(16)
        return response

    def InitControler(self):
        self.CountNibble = self.getNibble()
        return self.WriteControlWord([])

    def UnlockMotor(self):
        self.WriteControlWord(["STO","/Quick Stop", "Enable Operation","/Abort","/Freeze"])
        return
   
    def printTrame(self, trame):
        txt = "["
        for i in range(len(trame)):
            txt += hex(trame[i])
            if (i<len(trame)-1):
                txt += ", "
        txt += "]"
        print(txt)
        return

    def Home(self):
        return self.WriteControlWord(["Switch On","STO","/Quick Stop", "Enable Operation","/Abort","/Freeze","Home"])
    
    def ErrorAck(self):
        return self.WriteControlWord(["Switch On","STO","/Quick Stop", "Enable Operation","/Abort","/Freeze","Error Acknowledge"])

    def goToPosition(self,targetPosition, maximalVelocity, acceleration, deceleration):
        """targetPosition (mm)"""
        targetPosition = targetPosition * 10000
        self.WriteControlWord(["Switch On","STO","/Quick Stop","Enable Operation","/Abort","/Freeze"])
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

            self.CountNibble = (self.CountNibble+1)&0x0F
            self.PositionVector[6] = self.CountNibble
            self.PositionVector[(i*4)+8] = (var & 0xff)
            self.PositionVector[(i*4)+9] = ((var >> 8) & 0xff)
            self.PositionVector[(i*4)+10] = ((var >> 16) & 0xff)
            self.PositionVector[(i*4)+11] = ((var >> 24) & 0xff)
        
        self.PositionVector[24] = 0x04
        self.COM.write(self.PositionVector)
        response = self.COM.read(16)
        return response

    def getStatusWord(self):
        req = [0x01, 0x00, 0x03, 0x02, 0x01, 0x00, 0x04]
        self.COM.write(req)

        resp = self.COM.read(16)
        if (len(resp) == 16):
            word = resp[7] | (resp[8]<<8)
            return word
        else:
            return -1   

    def getWarning(self):
        req = [0x01, 0x00, 0x03, 0x02, 0x03, 0x00, 0x04]
        self.COM.write(req)
        
        resp = self.COM.read(20)
        if (len(resp)==20):
            word = resp[15] | (resp[16]<<8)
            return word
        else:
            return -1

    def getPosition(self):
        """Please put 0.05s delay at least between two requests"""
        RequestDefaultResponse = [0x01 , 0x00 , 0x03 , 0x02, 0x01, 0x00, 0x04]
        self.COM.write(RequestDefaultResponse)
        self.COM.flush()
        response = self.COM.read(16)
        self.COM.flushInput()
        if (len(response)==16):
            val = response[11] | (response[12]<<8) | (response[13]<<16) | (response[14]<<24)
            val -= (val & 0x80000000) << 1
            val = val/10000
            return(val)
        
        else: return None

    def getCurrent(self):
        Request = [0x01,0x00,0x05,0x02,0x00,0x03,(0x1B93 & 0x00FF),(0x1B93 >>8),0x04]
        self.COM.write(Request)
        self.COM.flush()
        response = self.COM.read(20)
        self.COM.flushInput()
        if (len(response)==20):
            val = response[15] | (response[16]<<8) | (response[17]<<16) | (response[18]<<24)
            val -= (val & 0x80000000) << 1
            val = val/1000
            return(val)
        
        else: return

    def getNibble(self):
        Request = [0x01,0x00,0x05,0x02,0x00,0x03,(0x1DB0 & 0x00FF),(0x1DB0 >>8),0x04]
        self.COM.write(Request)

        response = self.COM.read(20)
        if (len(response)==20):
            self.CountNibble = response[15] & 0x0F
            return(self.CountNibble)
        else: return -1
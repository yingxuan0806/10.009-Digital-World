import RPi.GPIO as GPIO
from libdw import pyrebase
import smbus
from statistics import stdev
from libdw import sm
import time
import mfrc522
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from twilio.rest import Client

#Firebase Settings

# URL to Firebase Database
url = "https://dw-1d-12da9.firebaseio.com/"

# Unique token used for authentication        
apikey = "AIzaSyBNDNhK3ReJ1574poKc-C7ATXAgw5sMSAU"

config = {
    "apiKey": apikey,
    "databaseURL": url,
}

firebase = pyrebase.initialize_app(config)
# Create a new real-time database to monitor the availability of washers
availability_db = firebase.database()                   



#Twilio SMS API Settings

# Account SID from twilio.com/console
account_sid = "AC394534c5c1696384fd7dec0b13852832"

# Auth Token from twilio.com/console
auth_token  = "ea9d07abbc14f75bb6e1f3a9356608df"
sender_number = "+12037699120"
  
# Use a service account
cred = credentials.Certificate('dw_1d.json')
firebase_admin.initialize_app(cred)

# Create a new cloud-based student database which stores the RFID tag numbers 
# of students' cards and their corresponding details
student_db = firestore.client()

doc = student_db.collection(u'testtest').document("hYWWynIfTE5FG7CeAadK").get()
user_dict = doc.to_dict()



# Accelerometer Operations  
     
# Power management registers
power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c

def read_word(adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
    val = (high << 8) + low
    return val

def read_word_2c(adr):
    val = read_word(adr)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

#Ensure that SPI is enabled on RPi
bus = smbus.SMBus(1)

# This is the address value read via the i2cdetect command
address = 0x68

# Wake the Accelerometer MP6050 up as it starts in sleep mode
bus.write_byte_data(address, power_mgmt_1, 0)



# Get status of accelerometer

def get_accel_status(accel_list):
    # Read accelerometer data on the x-axis every second
    accel_xout = read_word_2c(0x3b)    
    
    # Append new reading to the accelerometer list containing 5 values
    accel_list.append(accel_xout)  
    
    # Delete the first value in the accelerometer list
    # This procedure updates the list every second 
    del accel_list[0] 
    
    # To check list of output values of accelerometer
    print("Accel List: ", accel_list)
    
    # Calculate the standard deviation
    std_dev=stdev(accel_list)
    
    # To check standard deviation of the values in the list
    print("Standard Deviation: ", std_dev)
    
    # Determine whether the washer is vibrating or not according to the
    # standard deviation of the list.
    # This value must be calibrated according to the surface and amount of 
    # vibrating the accelerometer is subjected to.
    # Read documentation for calibration procedures.
    if std_dev<800:
        print("Not Vibrating")
        vibrate = False
    else:
        print("Vibrating")
        vibrate = True
    return vibrate



# Get status of door
    
def get_door_status():
    # Door closed
    if GPIO.input(21) == GPIO.LOW: 
        print("Closed")
        door = True        
        
    # Door opened
    if GPIO.input(21) == GPIO.HIGH: 
        print("Opened")
        door = False
    return door



# State Machine
class Washing_Machine(sm.SM):
    
    # Initialising
    
    def __init__(self):
        self.start_state = 0
        self.details = ''
        self.name = ''
        self.scanned = False
        self.client = Client(account_sid, auth_token) 
        # Create an object of the class MFRC522
        self.MIFAREReader = mfrc522.MFRC522()



    # Updating states according to input
    
    def get_next_values(self, state, inp):
        
        # State 0 and RFID card has not been scanned  
        if state == 0 and not self.scanned:
            # Scan for RFID cards
            self.rfid_scanning()
            output = "Available"
            
        # Dictionary of door, accelerometer and RFID status
        to_check = {'door': inp[0], 'vibrate' : inp[1], 'scanned' : self.scanned}
        
        # State 0
        if state == 0:
            # Check that door closed, machine is vibrating and RFID card
            # has been scanned.
            if all(to_check.values()):
                next_state = 1
                output = "Not Available"    
            else:                       
                next_state = 0
                output = "Available"
                
        # State 1
        elif state == 1: 
            # Check if washer is still vibrating               
            if to_check['vibrate']:     
                next_state = 1
                output = "Not Available"
            else:                       
                next_state = 2          
                output = "Not Available"
                # Send SMS
                self.rfid_sms()
                
        # State 2
        else:   
            # Check if door is still closed
            if to_check['door']:        
                next_state = 2
                output = "Not Available"          
            else:   
                # Return to initial state                    
                next_state = 0          
                output = "Available"
                self.scanned = False
                
        assert(next_state in (0,1,2))
        return next_state, output



    # Check for any RFID cards scanned
    
    def rfid_scanning(self):       
        # Welcome message
        print("Looking for cards")
        print("Press Ctrl-C to stop.")
        
        # Scan for cards
        (status,TagType) = self.MIFAREReader.MFRC522_Request(self.MIFAREReader.PICC_REQIDL)
             
        # Get the UID of the card
        (status,uid) = self.MIFAREReader.MFRC522_Anticoll()
             
        # If we have the UID, continue
        if status == self.MIFAREReader.MI_OK:

            # Print UID
            print("UID: "+str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3]))
            user_uid = str(uid[0])+","+str(uid[1])+","+str(uid[2])+","+str(uid[3])
            time.sleep(2)
            
            # Check that user is in the student database
            try:
                # Retrieve user name
                self.name = user_dict[user_uid]['Name']
                print("Name: ", self.name)
                
                # Retrieve user phone number
                self.details = user_dict[user_uid]['HP']
                print("Phone Number:", self.details)
                
                # Update RFID status
                self.scanned = True
                
            except:
                print("No such user found")                      


       
    # Send SMS to user
    
    def rfid_sms(self):
        message = self.client.messages.create(
            to=self.details,
            from_=sender_number,
            body= "Hi " + self.name + ", your laundry is ready!")
        print(message)



# Main Code
def main():
    #GPIO Settings
    # Use the BCM GPIO numbers as the numbering scheme.
    GPIO.setmode(GPIO.BCM)

    # Set GPIO 21 as input with pull-down resistor.
    GPIO.setup(21, GPIO.IN, GPIO.PUD_DOWN)
    
    # Create an object of the class Washing_Machine
    wm=Washing_Machine()
    wm.start()
    
    # Initial accelerometer list which should be changed during calibration.
    # Read documentation for calibration procedures.
    accel_list=[-1828, -1936, -1944, -1904, -1912]
    
    while True:
        # Retrieve boolean status of door
        door=get_door_status()
        
        # Retrieve boolean status of accelerometer
        vibrate=get_accel_status(accel_list)
        
        # Input both door and accelerometer status into state machine
        inp=(door, vibrate)
        wm.step(inp)
        
        # Update availability on firebase based on output of state machine
        availability_db.child("Washer 2").set(wm.step(inp))

if __name__ == '__main__':
    main()

F08 Group 8
Laundry App

Members:
Lim Xin Yi
Looi Siao Si
Vanessa Kwok Yong Yi
Yeo Ying Xuan



Real-time Firebase
url = "https://dw-1d-12da9.firebaseio.com/"       
apikey = "AIzaSyBNDNhK3ReJ1574poKc-C7ATXAgw5sMSAU"


Cloud-based Database
Refer to dw_1d.json for details.


Twilio SMS Account
account_sid = "AC394534c5c1696384fd7dec0b13852832"
auth_token  = "ea9d07abbc14f75bb6e1f3a9356608df"
sender_number = "+12037699120"


Follow the following steps to set up.

1. Run Washer_1.py and Washer_2.py
2. Run Kivy.py
3. Calibrate accelerometer in Washer_1.py and Washer_2.py (If it has not been calibrated on a new surface)
- Place accelerometer on flat and non-vibrating surface where it is intended to be installed on.
- Run Step 1 and wait for accelerometer list values to stabilise.
- Stop runnning after about 15 seconds and look through the printed outputs for the lowest standard deviation.
- Copy the corresponding accelerometer list and replace the accel_list in the main code.
- Go to the get_accel_status function and modify the standard deviation condition accordingly (eg. std_dev<400)


Notes:
- The .csv files store data collected over a week for machine learning and are used in Kivy.py to train the data model
- Kivy.py refers to Main.kv which is written in Kivy language
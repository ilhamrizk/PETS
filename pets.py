import pynmea2
import serial
import influxdb
import string
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
from time import sleep
from datetime import datetime
import os

HOST = 'localhost'
PORT = '8086'
USER = 'action'
PASSWORD = 'action'
DBNAME = 'PETS'
f=open("/usr/local/etc/yate/tmsidata.conf")
tmsi = f.read()

def init_gps():
    port="/dev/ttyACM0"
    ser = serial.Serial(port, baudrate = 9600, timeout = 5)
    return ser

def parse_data_gps(serial):
    try:
        while 1:
            data = serial.readline().decode('utf-8')
            print(data)
            if data[0:6] == '$GPGGA':
                print("locate")
                msg = pynmea2.parse(data)
                if (msg.lat_dir == 'S'):
                    lat = (-1*float(msg.lat)/100.0) - 0.3562548
                else:
                    lat = (float(msg.lat)/100.0) + 0.3562548
                if (msg.lon_dir == 'W'):
                    lon = (-1*float(msg.lon)/100.0) - 0.2441379
                else:
                    lon = (float(msg.lon)/100.0) + 0.2441379
                print('write location!')
                return {"latitude":lat , "longitude": lon}
    except:
        print("inevitable")
        return {"latitude": 0.0, "longitude": 0.0}

def returnValidCoordinate(gps_data):
    # get last coordinate from database
    queryString = "select * from coordinate group by * order by desc limit 1"
    try:
        client = InfluxDBClient(HOST, PORT, USER, PASSWORD, DBNAME)
    except:
        print("membuat client tidak terberhasilkan")
    print('test1')
    result = client.query(queryString)
    print('test')
    points = result.get_points(tags={'hostname': 'action'})
    if gps_data.get('latitude') == 0.0 and gps_data.get('longitude') == 0.0:
        for coordinate in points:
            print(coordinate)
            return {"latitude": coordinate['latitude'],
                    "longitude": coordinate['longitude'],"korban":coordinate['korban']}
    else:
            return gps_data
    

def sendGPSData(gpsData,subscriber):
    now = datetime.now()
    time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    metric = "coordinate"
    hostname = "action"
    print(gpsData)
    pointValue = [{
            "time": time,
            "measurement": metric,
            "fields":  {
                "latitude": gpsData.get('latitude'),
                "longitude": gpsData.get('longitude'),
                "korban": subscriber
            },
            'tags': {
                "hostname": hostname
            }
        }]
    
    print(pointValue)
 
    try:
        client = InfluxDBClient(HOST, PORT, USER, PASSWORD, DBNAME)
    except:
        print("membuat client tidak terberhasilkan")

    if (client.write_points(pointValue)):
        print('berhasil')
        
    sleep(1)

def cektmsidata():
    print('cektmsi')
    f=open("/usr/local/etc/yate/tmsidata.conf")
    print('bukafile')
    tmsitemp = f.read()
    global tmsi
    if (tmsitemp != tmsi):
        subscriber='warning'
        tmsi = tmsitemp
        print('warning')
        return subscriber  
    else:
        subscriber='ok'
        print('ok')
        return subscriber


def gpsDataHandler():
    while True:
        sleep(30)
        try:
             os.system("sudo sh /home/action/mesh.sh")
             gps_data_unfiltered = parse_data_gps(init_gps())
             print('parsedatagps')
             gps_data = returnValidCoordinate(gps_data_unfiltered)
             print('validcoordinate')
             sendGPSData(gps_data,cektmsidata())
             print('sendgpsdata')
        except:
             print("tidak bisa")

          
                
if __name__=='__main__':
    gpsDataHandler()
    

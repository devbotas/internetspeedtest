import os
import subprocess
import time
import json
import paho.mqtt.client as mqtt

class speedtest():
    def test(self):
        args = ['./speedtest', '-a', '-f', 'json', '--accept-license', '--accept-gdpr']

        if os.environ.get('SERVER_ID') != None:
            args.append('-s')
            args.append(os.environ.get('SERVER_ID'))

        p = subprocess.Popen(args , shell=False, stdout=subprocess.PIPE)
        response = p.communicate()
        result = json.loads(response[0])
        print ("Timestamp = " + str(result['timestamp']))
        print ("Down = " + str(result['download']['bandwidth']))
        print ("Up = " + str(result['upload']['bandwidth']))
        print ("Latency = " + str(result['ping']['latency']))
        print ("Jitter = " + str(result['ping']['jitter']))
        print ("Interface = " + str(result['interface']))
        print ("Server = " + str(result['server']))
        return result

speedtest = speedtest()
frequency = os.environ.get('FREQUENCY') or 3600
broker_address = os.environ.get('MQTT_BROKER') or "localhost"
teltonika_address = os.environ.get('TELTONIKA_BROKER') or "localhost"


client = mqtt.Client("1")


signal = 0
teltonikaClient = mqtt.Client("bybis")

def on_message(mqttc, obj, msg):
    global signal 
    signal = float(msg.payload.decode())
    print("signal is: "+str(signal))
    
teltonikaClient.on_message = on_message

while True:
    client.connect(broker_address)
    teltonikaClient.connect(teltonika_address)
    teltonikaClient.loop_start()
    teltonikaClient.subscribe("router/1104097390/signal", 1)
    teltonikaClient.publish("get/1104097390/command", "signal")
    result = speedtest.test()
  

    json_body = [
        {
            "measurement": "download",
            "time": str(result['timestamp']),
            "fields": {
                "value": int(str(result['download']['bandwidth'])),
                "up": int(result['upload']['bandwidth']),
                "latency": float(result['ping']['latency']),
                "jitter": float(result['ping']['jitter']),
                "interface": str(result['interface']['name']),
                "server": str(result['server']['host']),
                "signal": signal
            }
        }
    ]

    print("JSON body = " + str(json_body))
    msg_info = client.publish("sensors",json.dumps(json_body))
    if msg_info.is_published() == False:
            msg_info.wait_for_publish()
    client.disconnect()
    teltonikaClient.loop_stop()
    teltonikaClient.disconnect()
    time.sleep(int(frequency))





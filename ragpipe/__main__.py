from dynaconf import Dynaconf
import paho.mqtt.client as mqtt

from .config import VALIDATORS

settings = Dynaconf(
    envvar_prefix="RAGPIPE",
    settings_files=["settings.yml", "secrets.yml"],
    validators=VALIDATORS,
)

print(settings.to_dict())


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe("$SYS/#")


def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect("mqtt.eclipseprojects.io", 1883, 60)

mqttc.loop_forever()

from dynaconf import Validator

VALIDATORS = [
    Validator("GENERAL.LOG_LEVEL", default="info"),  # error, warning, info, debug
    Validator("MQTT.BROKER", default="mqtt.eclipseprojects.io"),
    Validator("MQTT.PORT", default=1883, cast=int),
    Validator("MQTT.KEEPALIVE", default=60, cast=int),
    Validator("MQTT.USERNAME", default=None),
    Validator("MQTT.PASSWORD", default=None),
]

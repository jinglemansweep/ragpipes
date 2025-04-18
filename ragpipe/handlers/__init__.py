from .text import text_handler


def handler(topic, payload):
    if topic == "ragpipe/loader/text":
        return text_handler(payload)

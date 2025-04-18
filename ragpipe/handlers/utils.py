from pydantic import ValidationError


def validate_payload(model, payload):
    try:
        options = model.model_validate(payload)
    except ValidationError as e:
        print("ERROR", e)
        return
    return options

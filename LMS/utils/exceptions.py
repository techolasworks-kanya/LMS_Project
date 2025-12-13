from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError

def custom_exception_handler(exc, context):
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # We only care about ValidationError (from serializers)
        if isinstance(exc, ValidationError):
            # Extract the "message" value, even if deeply nested
            data = response.data

            def extract_message(obj):
                if isinstance(obj, dict):
                    if "message" in obj:
                        msg = obj["message"]
                        return msg[0] if isinstance(msg, list) else msg
                    for value in obj.values():
                        result = extract_message(value)
                        if result is not None:
                            return result
                elif isinstance(obj, list) and obj:
                    return obj[0]
                return None

            message = extract_message(data)

            if message:
                response.data = {"message": message}
            else:
                response.data = {"message": "Invalid data provided."}

    return response
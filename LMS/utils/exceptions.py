# from rest_framework.views import exception_handler
# from rest_framework.exceptions import ValidationError

# def custom_exception_handler(exc, context):
#     # Call DRF's default exception handler first
#     response = exception_handler(exc, context)

#     if response is not None:
#         # We only care about ValidationError (from serializers)
#         if isinstance(exc, ValidationError):
#             # Extract the "message" value, even if deeply nested
#             data = response.data

#             def extract_message(obj):
#                 if isinstance(obj, dict):
#                     if "message" in obj:
#                         msg = obj["message"]
#                         return msg[0] if isinstance(msg, list) else msg
#                     for value in obj.values():
#                         result = extract_message(value)
#                         if result is not None:
#                             return result
#                 elif isinstance(obj, list) and obj:
#                     return obj[0]
#                 return None

#             message = extract_message(data)

#             if message:
#                 response.data = {"message": message}
#             else:
#                 response.data = {"message": "Invalid data provided."}

#     return response

# exceptions.py

from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError

def custom_exception_handler(exc, context):
    # Let DRF's default handler create the response first
    response = exception_handler(exc, context)

    if response is not None:
        # Only customize for ValidationError (serializer validation failures)
        if isinstance(exc, ValidationError):
            original_data = response.data

            # Case 1: You raised ValidationError({"message": "..."}) → becomes non_field_errors
            if isinstance(original_data, dict):
                # Look for common keys: non_field_errors, detail, or direct "message"
                message = None

                if "non_field_errors" in original_data:
                    err = original_data["non_field_errors"]
                    message = err[0] if isinstance(err, list) else str(err)

                elif "detail" in original_data:
                    detail = original_data["detail"]
                    message = detail[0] if isinstance(detail, list) else str(detail)

                elif "message" in original_data:
                    msg = original_data["message"]
                    message = msg[0] if isinstance(msg, list) else str(msg)

                # Fallback: search in any field
                else:
                    for value in original_data.values():
                        if isinstance(value, list) and value:
                            message = value[0]
                            break
                        elif isinstance(value, str):
                            message = value
                            break

            # Case 2: You raised ValidationError("plain string")
            elif isinstance(original_data, list) and original_data:
                message = original_data[0]

            elif isinstance(original_data, str):
                message = original_data

            else:
                message = None

            # Final response: always return {"message": "..."}
            if message:
                response.data = {"message": str(message)}
            else:
                response.data = {"message": "Invalid data provided."}

    return response  # ← Fixed typo!
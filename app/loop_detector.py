import email.message

LOOP_HEADER = "X-Sig-Applied"


def is_signed(message: email.message.Message) -> bool:
    return message.get(LOOP_HEADER) == "1"


def mark_as_signed(message: email.message.Message) -> None:
    if LOOP_HEADER in message:
        del message[LOOP_HEADER]
    message[LOOP_HEADER] = "1"

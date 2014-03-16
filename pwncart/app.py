import pwnableapp
import hashlib


app = pwnableapp.Flask('pwncart')
app.config.from_object('pwncart.config')
app.init_logging()

# CTF Flags
flags = {
    'free_cart': 'free_as_in_b33r',
    'account_credit': 'some_cash_machine_in_bumsville_idaho',
}
get_flag = flags.get

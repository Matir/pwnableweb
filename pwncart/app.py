import flask
import hashlib


app = flask.Flask(__name__)
app.config.from_object('config')

# CTF Flags
flags = {
    'free_cart': 'free_as_in_b33r',
    'account_credit': 'some_cash_machine_in_bumsville_idaho',
}
get_flag = flags.get

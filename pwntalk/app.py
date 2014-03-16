import hashlib
import pwnableapp


app = pwnableapp.Flask('pwntalk')
app.config.from_object('pwntalk.config')

# CTF Flags
flags = {
    'user_profile_edited': 'electronic_army_rides_again',
    'dom_based_xss': 'crash_and_burn',
    'larry_pass': 'LanaiHawaii',
    'admin_console': 'SETEC_ASTRONOMY',
}
get_flag = flags.get

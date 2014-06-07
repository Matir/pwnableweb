# Copyright 2014 David Tomaschik <david@systemoverlord.com>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import pwnableapp


app = pwnableapp.Flask('pwntalk')
app.config.from_object('pwntalk.config')
app.init_logging()

# CTF Flags
flags = {
    'user_profile_edited': 'electronic_army_rides_again',
    'dom_based_xss': 'crash_and_burn',
    'larry_pass': 'LanaiHawaii',
    'admin_console': 'SETEC_ASTRONOMY',
}
get_flag = flags.get

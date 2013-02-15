## About

A transmission chatter!

## Requirements

Python 2.6

## How to get running

Update config.py to updated following variables according to the account that is going to your gtalk bot:

BOT_IDENTITY 	- The bot details.

BOT_ADMINS 	- Mention your self email id, should be gmail id.

TRANSMISSION_SERVER: The hostname/ip address.

TRANSMISSION_SERVER_PORT: The port on which transmission is available.

TRANSMISSION_SERVER_RPC: Transmission RPC URL.

TORRENT_USER: Username through which the transmission server can be logged onto.

TORRENT_PASSWORD: Password for transmission server.


Execute following commands, the commands require python-pip to be installed hence:

sudo apt-get install python-pip

then proceed as below:

cd err

sudo pip install -r requirements.txt

Once above is done, return back to the parent folder  and execute following command

./dockstar-gtalk.sh

This command will immediately return indicating the process has become daemon. You can check the status by looking at gtalk.log

## Commands:

.help 

## Copyright

Released under the GPLv3 license, see [COPYING] for details.


## Contact

Feel free to request new features or provide bug reports.  

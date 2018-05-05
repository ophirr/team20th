# Team20

This is an integration for Nest IQ outdoor cameras and PagerDuty

To use:

# Load dependencies
pip install -r requirements.txt

# Update config file with Nest API Token and PD Routing Key
vi config.txt

# Run poller in screen
./start-poll

# To see the logging
screen -ls

There are screens on:
	26437.team20th	(05/05/2018 05:08:04 PM)	(Attached)

# choose relevant screen e.g.
screen -r 26[TAB]

# Control A D
# To detach  from the screen (control C will quit)
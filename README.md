# pokemon-cafe-bot

This is far from a polished set of scripts and was mostly hacking stuff together to try and get reservations at the notoriously difficult Pokemon Cafe in Tokyo.
* Attempt one, the "original bot", was to attempt to achieve super-human clickops right at release time for newly opened reservation windows 30 days in advance
    * This bot needs significant refinement and while functional, it doesn't handle well cases where the server gets overloaded
* Attempt two, the "cancellations bot", is the backup option that will check with specified regularity for any openings for the specified date(s) of interest and notify 2 users
    * This bot is much more robust and feature-rich; I successfully used it to snag a reservation for our trip to Japan! I felt especially cool when I was still getting the notifications from Pushover (described below) while in Japan via my workhorse machine back in the States that was actually running the bot.

## dependency management

I used `pyenv` to isolate my development environment for this project

Specifically, I used Python 3.11.9

You could also use `conda`, `uv`, or some other manager

After activating your chosen environment, run the following to install the necessary dependencies for this project
```
pip3 install pytz selenium webdriver-manager
```

## original bot (`pcafe.py`)
The first bot I built is currently only configured to be run manually when a new date is recently released for the cafe (30 days in advance, IIRC). It's intended to automate the clickops needed to get to the actual booking page on a given day. It is currently configured to automatically pick a time in the middle of the array of available times for the selected booking day, though this can be modified.

Example command:
`python pcafe.py --day_of_month=20 --num_of_guests=4 --max_attempts=10`

With some more work (and maybe adapting some of the server overload logic from the cancellations bot), this bot could be a powerful way of jumping onto the website at precisely the time of opening.

Note as well that the "cart" for reservations seems to last about 15 minutes, and from my experience any incomplete carts are released back into the pool precisely every 20 minutes. That is, if you're not successful right at 6:00 PM (JST) then try this bot again at 6:20, 6:40, etc. until the pool is truly exhausted.

## cancellations bot (`pcafe_cancellations.py`)

If the original bot above fails to meet your needs, you can instead rely on the cancellations bot (which I successufully used for our trip to Japan in Oct 2024!). You can set this script to run via a scheduled cron job at regular intervals (e.g. every hour). If any openings are found for your selected date(s), you can configure Pushover (a separate app available for iOS and Android) to send you a push notification. Currently the notifications are set to notify you even when there aren't openings (i.e. the notification will say 0 openings).

If you want to just test the functionality of the script itself (i.e. without scheduling jobs or receiving notification pushes) you can just call the script directly from the terminal and see the output in the terminal:
```
python pcafe_cancellations.py --num_of_guests=4 --max_attempts=70 --desired_dates 10-1 10-2 10-3 10-4 10-5 10-6 10-7 10-8
```

Note that this is simply a notification bot; you still have to manually access the booking site and complete the booking for your desired date. It just helps you find the openings. Act quickly. Openings tend to fill quickly as I suspect there is some business that has commercialized a similar bot.

### cron job scheduler

Add a line like the following to your `crontab` file (for Linux, unsure for other platforms) to tell your machine to call the cancellation bot every hour:
```
0 */1 * * * DISPLAY=:1 /home/taylorhansen/scripts/pcafe_cancellations_checker.sh >> /home/taylorhansen/scripts/pcafe_cancellations_cron_log.txt 2>&1
```
Obviously update the directories to wherever your version of `pcafe_cancellations_checker.sh` is located. Everything after and including `>>` is the command to store the logs for the script execution to a location of your choosing (and yes, the `2>&1` is important for this purpose)
* In my opinion these logs are very helpful for debugging

#### Notes on `pcafe_cancellations_checker.sh`
The code is pasted in its entirety below (for explanatory purposes):
```
#!/usr/bin/env bash

/home/taylorhansen/.pyenv/versions/pcafe/bin/python /home/taylorhansen/scripts/pcafe_cancellations.py --num_of_guests=4 --max_attempts=70 --desired_dates 10-4 10-5 10-6 10-7 10-8
```

* Line 1 (the shebang) specifies the shell to run the script
* `/home/taylorhansen/.pyenv/versions/pcafe/bin/python` tells the script the location of the `pyenv` virtual environment is (and therefore the python version to use)
    * update this to point to whichever python version is applicable in your case
* `/home/taylorhansen/scripts/pcafe_cancellations.py` tells the script where the `pcafe_cancellations.py` file is located
* the rest of the command are flags for `pcafe_cancellations.py`; in particular note the formatting of the desired_dates
    * will need to manually update `pcafe_cancellations.py` to use a different search year (if not running in 2024)

#### configuring Pushover notifications:
* My scripts above are currently configured to notify exactly two users of any cancellations
    * if you want fewer or more users notified, please update `pushover_setup.py` accordingly
* Download the Pushover app and create an account
* Grab the Pushover User Key (found in the app settings)
* Save this to your environment variables as `PUSHOVER_PUSH_USER` for later use by `pushover_setup.py`
    * e.g. `PUSHOVEVER_PUSH_USER='12345678abcdefg'`
    * on my Linux machine these environmental variables are found under `/etc/environment`
* Repeat this process for the 2nd Pushover user:
    * this time name the variable `PUSHOVER_PUSH_USER_2`
* Finally, add the token for the cancellations bot Pushover app to this same `/etc/environment` file:
    * `PUSHOVER_PUSH_TOKEN='a2sczq9yobu7w6pxpuc4941rriy7t7'`

# weekend flights monitoring bot

## Why it's needed? 
Very simple, none of the available platforms (Skyscanner, Kiwi) gives the functionality that I need - fly for a weekend only and search for flights for weekends only.

So because of that I wrote this tool. It's very simple, just getting the dates of all the weekends in the following few months, and then searching for a flights in the same dates. 

Only **DIRECT** flights. For some airlines booking link is also provided!
If you want to buy the found flight - press the link or proceed to the airline's website.
* always buy tickets directly from the airline.

You can also provide a Telegram `Bot Token` and `Chat ID` and get reports to your telegram channel/group. 
* For example, this is my channel for flights from Tel Aviv airport - https://t.me/+3skjYH7n_WViYjg0

## How To ?

The bot gets the configuration from environment variables, configuration example is - 
```bash
KIWI_API_KEY=<kiwi_tequilla_api>
TELEGRAM_BOT_TOKEN=<telegram_bot_id>
TELEGRAM_CHAT_ID=-<main_telegram_chat_id>
ADDITIONAL_CHAT_IDS=<destination_code>;<chat_id>;<flight_max_price>|<destination_code>;<chat_id>;<flight_max_price>
```
* `ADDITIONAL_CHAT_IDS` configuration is for creating a destination specific telegram chats and get flights per destination
  * The chats are seperated by `|` and every chat should contain - 
    * `dest_country_code` - for example - CZ, HU, AM, IL, US etc.
    * `chat_id` - telegram chat id
    * `flight_max_price` - the maximum price for the round flight (by default ILS
    * there fields should be seperated by `;` (as you can see in configuration example above)
    

* You can read about kiwi API here - `https://tequila.kiwi.com/portal/docs/tequila_api/search_api`

You can run it by - 
```bash
apt-get install -y libappindicator1 fonts-liberation wget python3 python3-pip
apt-get install -f 

wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt install -y ./google-chrome-stable_current_amd64.deb

python3 -m pip install -r requirements.txt

python3 main.py
```

Or you can build (or use a prebuild) docker image and run it this way - 
```bash
sudo docker run --env-file configfile public.ecr.aws/v7h5e2i7/kiwi_flights_bot
```

Link for the prebuild image - [public.ecr.aws/v7h5e2i7/kiwi_flights_bot](public.ecr.aws/v7h5e2i7/kiwi_flights_bot) 



## Additional Features 
* The tool calculates the number of the days off the work, using very simple logic - (Day off is needed for flights in Thursday before 17:00 and for Sundays after 10:00)
* Search for some specific countries - you can change the configuration to change the countries that you are interested in.
* There is also a `Dockerfile` that you can use to create docker image and run the code inside a container (recommended)

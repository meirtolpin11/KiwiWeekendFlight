# A tool to search weekend (only) flights using KIWI rest api

## Why it's needed? 
Very simple, none of the available platforms (Skyscanner, Kiwi, Greatescape) gives the functionality that I need - fly for a weekend only and search for flights for weekends only.

So because of that I wrote this tool. It's very simple, just getting the dates of all the weekends in the following few months, and then searching for a flights in the same dates. 

Only **DIRECT** flights. No link for booking is provided!, if you want to buy the found flight - proceed to the airline's website.
* always but tickets directly from the airline.

You can also provide a Telegram `Bot Token` and `Chat ID` and get reports to your telegram channel/group. 
* For example, this is my channel for flights from Tel Aviv airport - https://t.me/+3skjYH7n_WViYjg0

## Additional Features 
* The tool calculates the number of the days off the work, using very simple logic - (Day off is needed for flights in Thursday before 17:00 and for Sundays after 10:00)
* Search for some specific countries - you can change the configuration inside the code to change the countries that you are intrested in.

## Notes 

* You can read about kiwi API here - `https://tequila.kiwi.com/portal/docs/tequila_api/search_api`

## TODO
* External configuration
* Price drop notifications
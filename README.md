# Hearthstone Card Change Lookup
This is a tool to conveniently generate ALL changed content for a Hearthstone patch. Including in-game data which are not mentioned by Blizzard in official patch notes. Uses HearthstoneJSON's data to compare patch contents.

## Setup
Clone this repository with `git clone https://github.com/vghost01/hearthstone-card-change-lookup` or [download it as a zip](https://github.com/vghost01/hearthstone-card-change-lookup/archive/refs/heads/main.zip).

You need to have [python](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/installation/) installed on your computer.

The program needs a working internet connection. Connects to HearthstoneJSON's site.

## Configuration
Before running anything, adjust `config.ini` in Notepad or a similar app.

* `PREVIOUS_BUILD`: The build number of the previous build to compare to.
* `NEW_BUILD`: The build number of the new build to compare to.

For example, by using the values `20457` for `PREVIOUS_BUILD` and `20970` for `NEW_BUILD`, which are patches `9.0.0.20457` and `9.1.0.20970`, the program will generate changes that happened between patches 9.0 and 9.1 (the build number is the final 5-6 digit string at the end of the patch version). To find the correct build number for a patch, you can either:
* Check your Battle.net app, where it says the Hearthstone version on the bottom left (e.g. Version: 31.4.2.216149)
* Use Hearthstone Wiki's [patch template page](https://hearthstone.wiki.gg/wiki/Template:Patches) to find build numbers for previous patches

You should always use adjacent patches, not jump over ones. For example, don't compare patch 30.0 to 30.4 since this will include changes that may have happened in the other patches between those.

* `LOCALE`: The language you want texts to appear in the resulting file. By default it's enUS for English, but it can be changed to any language Hearthstone is localized in. Older patches might not have localized data for all languages.
* `SCALE`: Type either `basic` or `full`. `basic` will generate fewer card change types, mostly what a regular user might care about. `full` will generate every single card change type for a patch.

## Usage
If it's your first time using the program, run `init.bat` first. This only needs to be run once.

Then after configuring, run `CardChangeLookup.bat` for the process itself.

Alternatively on Mac/Linux, you can direclty run `python3 src/process.py` from terminal.

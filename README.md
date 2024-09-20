# Hearthstone Card Change Lookup
This is a tool to conveniently generate ALL changed content for a Hearthstone patch. Including in-game data which are not mentioned by Blizzard in official patch notes. Uses HearthstoneJSON's data to compare patch contents.

## Setup
`git clone https://github.com/vghost01/hearthstone-card-change-lookup`

Needs a working internet connection. Connects to HearthstoneJSON's site.

## Configuration
Before running anything, adjust `config.ini` in Notepad or a similar app.

* `PREVIOUS_BUILD`: The build number of the previous build to compare to.
* `NEW_BUILD`: The build number of the new build to compare to.

For example, by using the values `20457` and `20970`, which are patches `9.0.0.20457` and `9.1.0.20970`, the program will generate changes that happened between patches 9.0 and 9.1. To find the correct build number for a patch, you can use e.g. Hearthstone Wiki's [patch template page](https://hearthstone.wiki.gg/wiki/Template:Patches).

* `LOCALE`: The language you want texts to appear in the resulting file. By default it's enUS for English, but it can be changed to any language Hearthstone is localized in. Older patches might not have localized data for all languages.
* `SCALE`: Type either `basic` or `full`. `basic` will generate fewer card change types, mostly what a regular user might care about. `full` will generate every single card change type for a patch.

## Usage
Simply run `HearthstoneCardChangeLookup.bat`.

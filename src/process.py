import sqlite3
import os
import os.path
import requests
import configparser
import time

def create_tables(db, prev, cur, allowed_types):
    db.execute("""
    CREATE TABLE OldCards(
    armor INTEGER,
    artist TEXT,
    attack INTEGER,
    battlegroundsBuddyDbfId INTEGER,
    battlegroundsDarkmoonPrizeTurn INTEGER,
    battlegroundsHero INTEGER,
    battlegroundsNormalDbfId INTEGER,
    battlegroundsPremiumDbfId INTEGER,
    battlegroundsSkinParentId INTEGER,
    cardClass TEXT,
    classes TEXT,
    collectible INTEGER,
    collectionText TEXT,
    cost INTEGER,
    countAsCopyOfDbfId INTEGER,
    dbfId INTEGER,
    durability INTEGER,
    elite INTEGER,
    faction TEXT,
    flavor TEXT,
    hasDiamondSkin INTEGER,
    health INTEGER,
    heroPowerDbfId INTEGER,
    hideCost INTEGER,
    hideStats INTEGER,
    howToEarn TEXT,
    howToEarnGolden TEXT,
    id TEXT,
    isBattlegroundsBuddy INTEGER,
    isBattlegroundsPoolMinion INTEGER, 
    isBattlegroundsPoolSpell INTEGER,
    isMiniSet INTEGER,
    mechanics TEXT,
    mercenariesAbilityCooldown INTEGER,
    mercenariesRole INTEGER,
    multiClassGroup INTEGER,
    name TEXT,
    overload INTEGER,
    puzzleType INTEGER,
    questReward TEXT,
    race TEXT,
    races TEXT,
    rarity TEXT,
    referencedTags TEXT,
    "set" TEXT,
    spellDamage INTEGER,
    spellSchool TEXT,
    targetingArrowText TEXT, 
    techLevel INTEGER,
    "text" TEXT,
    type TEXT  
    )""")

    db.execute("""
    CREATE TABLE NewCards(
    armor INTEGER,
    artist TEXT,
    attack INTEGER,
    battlegroundsBuddyDbfId INTEGER,
    battlegroundsDarkmoonPrizeTurn INTEGER,
    battlegroundsHero INTEGER,
    battlegroundsNormalDbfId INTEGER,
    battlegroundsPremiumDbfId INTEGER,
    battlegroundsSkinParentId INTEGER,
    cardClass TEXT,
    classes TEXT,
    collectible INTEGER,
    collectionText TEXT,
    cost INTEGER,
    countAsCopyOfDbfId INTEGER,
    dbfId INTEGER,
    durability INTEGER,
    elite INTEGER,
    faction TEXT,
    flavor TEXT,
    hasDiamondSkin INTEGER,
    health INTEGER,
    heroPowerDbfId INTEGER,
    hideCost INTEGER,
    hideStats INTEGER,
    howToEarn TEXT,
    howToEarnGolden TEXT,
    id TEXT,
    isBattlegroundsBuddy INTEGER,
    isBattlegroundsPoolMinion INTEGER, 
    isBattlegroundsPoolSpell INTEGER,
    isMiniSet INTEGER,
    mechanics TEXT,
    mercenariesAbilityCooldown INTEGER,
    mercenariesRole INTEGER,
    multiClassGroup INTEGER,
    name TEXT,
    overload INTEGER,
    puzzleType INTEGER,
    questReward TEXT,
    race TEXT,
    races TEXT,
    rarity TEXT,
    referencedTags TEXT,
    "set" TEXT,
    spellDamage INTEGER,
    spellSchool TEXT,
    targetingArrowText TEXT, 
    techLevel INTEGER,
    "text" TEXT,
    type TEXT
    )""")

    def insert_cards(table_name, cards):
        columns = [f'"{changeType}"' if changeType in ["set", "text"] else changeType for changeType in allowed_types]
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})"
        values_batch = []
        
        for card in cards:
            values = []
            for changeType in allowed_types:
                if changeType in card:
                    value = card[changeType]
                    if isinstance(value, int):
                        values.append(str(value))
                    elif isinstance(value, list):
                        values.append(",".join(value))
                    else:
                        values.append(value)
                else:
                    values.append(None)
                
            values_batch.append(tuple(values))
            if len(values_batch) >= 1000:
                db.executemany(sql, values_batch)
                print(f"{len(values_batch)} cards added to {table_name}")
                values_batch.clear()

        if values_batch:
            db.executemany(sql, values_batch)
            print(f"{len(values_batch)} cards added to {table_name}")

    # Insert OldCards
    print(f"Creating table OldCards with {len(prev)} cards")
    insert_cards("OldCards", prev)

    # Insert NewCards
    print(f"Creating table NewCards with {len(cur)} cards")
    insert_cards("NewCards", cur)

    print("Finished creating tables")

def check_changes(db, excluded_dbfIds, allowed_types, compare_type):
    with open("result/CardChanges.txt", "w", encoding="utf-8") as CardChanges:
        # Search for added cards
        sql = f"""SELECT NewCards.{compare_type}, NewCards.id, NewCards.name
                FROM NewCards
                LEFT JOIN OldCards
                ON NewCards.{compare_type} = OldCards.{compare_type}
                WHERE (OldCards.{compare_type} IS NULL);"""
        result = db.execute(sql).fetchall()
        has_cards = False
        for row in result:
            if row[0] != None:
                has_cards = True
        if has_cards:
            CardChanges.write("##############################\nThe folowing cards were added:\n##############################\n\n")
        for row in result:
            if row[0] == None:
                continue
            if compare_type == "dbfId":
                line = str(row[2]) + " (dbfId " + str(row[0]) + ", id " + str(row[1]) + ")\n"
            else:
                line = str(row[2]) + " (id " + str(row[1]) + ")\n"
            excluded_dbfIds.add(row[0])
            CardChanges.write(line)
        CardChanges.write("\n")

        #Search for removed cards
        sql = f"""SELECT OldCards.{compare_type}, OldCards.id, OldCards.name
                FROM OldCards
                LEFT JOIN NewCards
                ON OldCards.{compare_type} = NewCards.{compare_type}
                WHERE (NewCards.{compare_type} IS NULL);"""
        result = db.execute(sql).fetchall()
        has_cards = False
        for row in result:
            if row[0] != None:
                has_cards = True
        if has_cards:
            CardChanges.write("###############################\nThe folowing cards were removed:\n###############################\n\n")
        for row in result:
            if row[0] == None:
                continue
            if compare_type == "dbfId":
                line = str(row[2]) + " (dbfId " + str(row[0]) + ", id " + str(row[1]) + ")\n"
            else:
                line = str(row[2]) + " (id " + str(row[1]) + ")\n"
            excluded_dbfIds.add(row[0])
            CardChanges.write(line)
        CardChanges.write("\n")

        #Search for changed cards
        CardChanges.write("####################################\nThe folowing cards received changes:\n####################################\n\n")
        for key in allowed_types:
            key_fixed = key if key != "set" and key != "text" else "\"" + key + "\""
            sql = f"""SELECT OldCards.{compare_type}, OldCards.""" + key_fixed + """, NewCards.""" + key_fixed + f""", OldCards.name, OldCards.id
            FROM OldCards
            LEFT JOIN NewCards
            ON OldCards.{compare_type} = NewCards.{compare_type}
            WHERE (NOT OldCards.""" + key_fixed + """=NewCards.""" + key_fixed + """) OR (OldCards.""" + key_fixed + """ IS NULL AND NOT NewCards.""" + key_fixed + """ IS NULL);"""
            result = db.execute(sql).fetchall()
            for row in result:
                row1 = str(row[1])
                row2 = str(row[2])
                if (row1 == "None"):
                    row1 = ""
                if (row2 == "None"):
                    row2 = ""
                if (row1 == row2):
                    continue
                if compare_type == "dbfId":
                    line1 = str(row[3]) + " (dbfId " + str(row[0]) + ", id " + str(row[4]) + ") - Type: " + key + "\n"
                else:
                    line1 = str(row[3]) + " (id " + str(row[4]) + ") - Type: " + key + "\n"
                CardChanges.write(line1)
                line2 = "* Previous: " + ("NULL" if len(row1) == 0 else row1.replace('\n', '\\n')) + "\n"
                CardChanges.write(line2)
                line3 = "* New: " + ("NULL" if len(row2) == 0 else row2.replace('\n', '\\n')) + "\n"
                CardChanges.write(line3)
                CardChanges.write("\n")

def true_to_1(data):
    if isinstance(data, dict):
        return {key: (1 if value is True else true_to_1(value)) for key, value in data.items()}
    elif isinstance(data, list):
        return [true_to_1(item) for item in data]
    else:
        return data
    
def get_prev_data(prev_build, locale):
    url = f"https://api.hearthstonejson.com/v1/{prev_build}/{locale}/cards.json"
    response = requests.get(url)
    response.encoding = 'utf-8'

    if response.status_code == 200:
        data = response.json()
        fixed_data = true_to_1(data)
    else:
        print(f"Failed to retrieve data from HearthstoneJSON for build {prev_build}! Most likely you typed incorrect build numbers at config.ini. Error code: {response.status_code}")
        return False
    
    return fixed_data

def get_current_data(current_build, locale):
    url = f"https://api.hearthstonejson.com/v1/{current_build}/{locale}/cards.json"
    response = requests.get(url)
    response.encoding = 'utf-8'

    if response.status_code == 200:
        data = response.json()
        fixed_data = true_to_1(data)
    else:
        print(f"Failed to retrieve data from HearthstoneJSON for build {current_build}! Most likely you typed incorrect build numbers at config.ini. Error code: {response.status_code}")
        return False
    
    return fixed_data

def main():
    start_time = time.time()
    config = configparser.ConfigParser()
    try:
        config.read("config.ini")
    except:
        print("Error: Could not find config.ini file.")
    settings = config["SETTINGS"]
    try:
        prev_build = settings.getint('PREVIOUS_BUILD')
        current_build = settings.getint('NEW_BUILD')
        locale = settings.get("LOCALE")
        scale = settings.get("SCALE")
    except:
        print("Error: could not get contents of config.ini")

    try:
        test = prev_build, current_build
    except UnboundLocalError:
        print("Error: config.ini was not setup correctly. The values of PREVIOUS_BUILD and CURRENT_BUILD must be numbers with no other text!")
        return
    
    if prev_build == 0 or current_build == 0:
        print("Error: You forgot to set up config.ini! Read the README.md again to proceed.")
        return
    
    if locale not in ["deDE", "enUS", "esES", "esMX", "frFR", "itIT", "jaJP", "koKR", "plPL", "ptBR", "ruRU", "thTH", "zhCN", "zhTW"]:
        print("Error: LOCALE is invalid at config.ini. Must be one of the values specified in the file.")
        return
    
    if scale not in ["basic", "full"]:
        print("Error: SCALE is invalid at config.ini. Must be basic or full.")
        return
    
    if prev_build < 18336:
        compare_type = "id"
    else:
        compare_type = "dbfId"

    if os.path.exists("src/cards.db"):
        os.remove("src/cards.db")

    db = sqlite3.connect("src/cards.db")
    db.isolation_level = None

    excluded_dbfIds = set()

    if scale == "basic":
        allowed_types = ['cost', 'techLevel',  'attack', 'health',  'text', 'durability', 'armor', 'race', 'races', 'spellSchool',  
                        'isBattlegroundsPoolMinion', 'isBattlegroundsPoolSpell', 'mercenariesAbilityCooldown', 'mercenariesRole', 
                        'artist', 'cardClass', 'collectible', 'name', 'dbfId', 'id', 'elite', 'flavor', 'howToEarn', 'howToEarnGolden', 
                        'mechanics', 'referencedTags', 'rarity', 'set', 'type', 'targetingArrowText']
    else:
        allowed_types = ['armor', 'artist', 'attack', 'battlegroundsBuddyDbfId', 'battlegroundsDarkmoonPrizeTurn', 
                        'battlegroundsHero', 'battlegroundsNormalDbfId', 'battlegroundsPremiumDbfId', 'battlegroundsSkinParentId', 
                        'cardClass', 'classes', 'collectible', 'collectionText', 'cost', 'countAsCopyOfDbfId', 'dbfId', 
                        'durability', 'elite', 'faction', 'flavor', 'hasDiamondSkin', 'health', 'heroPowerDbfId', 
                        'hideCost', 'hideStats', 'howToEarn', 'howToEarnGolden', 'id', 'isBattlegroundsBuddy', 
                        'isBattlegroundsPoolMinion', 'isBattlegroundsPoolSpell', 'isMiniSet', 'mechanics', 
                        'mercenariesAbilityCooldown', 'mercenariesRole', 'multiClassGroup', 'name', 'overload', 
                        'puzzleType', 'questReward', 'race', 'races', 'rarity', 'referencedTags', 'set', 'spellDamage', 
                        'spellSchool', 'targetingArrowText', 'techLevel', 'text', 'type']
    
    allowed_types_set = set(allowed_types)
    
    print("Fetching data from HearthstoneJSON...")
    if get_prev_data(prev_build, locale):
        prev_build_data = get_prev_data(prev_build, locale)
    else:
        return
    if get_current_data(current_build, locale):
        current_build_data = get_current_data(current_build, locale)
    else:
        return
    print("Creating tables...")
    create_tables(db, prev_build_data, current_build_data, allowed_types_set)
    print("Checking changes...")
    check_changes(db, excluded_dbfIds, allowed_types, compare_type)
    print(f"Done! Program finished in {int((time.time() - start_time))} seconds. The result can be viewed at result/CardChanges.txt")

if __name__ == "__main__":
    main()
import sqlite3
import os
import requests
import configparser
import time

def create_tables(db, prev, cur, allowed_types):
    print("Creating tables...")
    def make_table(table_name):
        db.execute(f"""
        CREATE TABLE {table_name}(
        armor INTEGER,
        artist TEXT,
        attack INTEGER,
        battlegroundsBuddyDbfId INTEGER,
        battlegroundsDarkmoonPrizeTurn INTEGER,
        battlegroundsHero BOOLEAN,
        battlegroundsNormalDbfId INTEGER,
        battlegroundsPremiumDbfId INTEGER,
        battlegroundsSkinParentId INTEGER,
        cardClass TEXT,
        classes TEXT,
        collectible BOOLEAN,
        collectionText TEXT,
        cost INTEGER,
        countAsCopyOfDbfId INTEGER,
        dbfId INTEGER,
        durability INTEGER,
        elite BOOLEAN,
        faction TEXT,
        flavor TEXT,
        hasDiamondSkin BOOLEAN,
        health INTEGER,
        heroPowerDbfId INTEGER,
        hideCost BOOLEAN,
        hideStats BOOLEAN,
        howToEarn TEXT,
        howToEarnGolden TEXT,
        id TEXT,
        isBattlegroundsBuddy BOOLEAN,
        isBattlegroundsPoolMinion BOOLEAN, 
        isBattlegroundsPoolSpell BOOLEAN,
        isMiniSet BOOLEAN,
        mechanics TEXT,
        mercenariesAbilityCooldown INTEGER,
        mercenariesRole INTEGER,
        multiClassGroup TEXT,
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

    make_table("OldCards")
    make_table("NewCards")

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
                        values.append(str(value))
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

    print(f"Creating table OldCards with {len(prev)} cards")
    insert_cards("OldCards", prev)

    print(f"Creating table NewCards with {len(cur)} cards")
    insert_cards("NewCards", cur)

    print("Finished creating tables")

def check_changes(db, excluded_dbfIds, allowed_types, compare_type, prev_build, current_build):
    print("Checking changes...")
    with open(f"result/CardChanges_{prev_build}-{current_build}.txt", "w", encoding="utf-8") as CardChanges:
        # Search for added cards
        sql = f"""SELECT NewCards.{compare_type}, NewCards.id, NewCards.name
                FROM NewCards
                LEFT JOIN OldCards
                ON NewCards.{compare_type} = OldCards.{compare_type}
                WHERE (OldCards.{compare_type} IS NULL);"""
        result = db.execute(sql).fetchall()
        has_cards = False
        for row in result:
            if row[0]:
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
            if row[0]:
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
                line2 = "* Old: " + ("NULL" if len(row1) == 0 else row1.replace('\n', '\\n')) + "\n"
                CardChanges.write(line2)
                line3 = "* New: " + ("NULL" if len(row2) == 0 else row2.replace('\n', '\\n')) + "\n"
                CardChanges.write(line3)
                CardChanges.write("\n")

def load_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    
    settings = config["SETTINGS"]
    try:
        prev_build = settings.getint("PREVIOUS_BUILD")
        current_build = settings.getint("NEW_BUILD")
        locale = settings.get("LOCALE")
        scale = settings.get("SCALE")
    except:
        print("Error: Could not load contents of config.ini. Check that all values are correctly formatted.")
        return None

    if (prev_build == 0 and current_build == 0) or (prev_build >= current_build):
        print("Error: Invalid build numbers in config.ini. Must be non-0 and PREVIOUS_BUILD must be smaller than CURRENT_BUILD.")
        return None
    if locale not in ["deDE", "enUS", "esES", "esMX", "frFR", "itIT", "jaJP", "koKR", "plPL", "ptBR", "ruRU", "thTH", "zhCN", "zhTW"]:
        print("Error: Invalid LOCALE in config.ini.")
        return None
    if scale not in ["basic", "full"]:
        print("Error: Invalid SCALE in config.ini.")
        return None
    
    return prev_build, current_build, locale, scale

def fetch_json(build, locale):
    url = f"https://api.hearthstonejson.com/v1/{build}/{locale}/cards.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data for build {build}. Double-check your build numbers and locale in config.ini. Status code: {response.status_code}")
        return None

def setup_db(db_path="src/cards.db"):
    if os.path.exists(db_path):
        os.remove(db_path)
    db = sqlite3.connect(db_path)
    db.isolation_level = None
    return db

def set_types(scale):
    if scale == "basic":
        return ['cost', 'techLevel',  'attack', 'health',  'text', 'durability', 'armor', 'race', 'races', 'spellSchool',  
                'isBattlegroundsPoolMinion', 'isBattlegroundsPoolSpell', 'mercenariesAbilityCooldown', 'mercenariesRole', 
                'artist', 'cardClass', 'collectible', 'name', 'dbfId', 'id', 'elite', 'flavor', 'howToEarn', 'howToEarnGolden', 
                'mechanics', 'referencedTags', 'rarity', 'set', 'type', 'targetingArrowText']
    else:
        return ['armor', 'artist', 'attack', 'battlegroundsBuddyDbfId', 'battlegroundsDarkmoonPrizeTurn', 
                'battlegroundsHero', 'battlegroundsNormalDbfId', 'battlegroundsPremiumDbfId', 'battlegroundsSkinParentId', 
                'cardClass', 'classes', 'collectible', 'collectionText', 'cost', 'countAsCopyOfDbfId', 'dbfId', 
                'durability', 'elite', 'faction', 'flavor', 'hasDiamondSkin', 'health', 'heroPowerDbfId', 
                'hideCost', 'hideStats', 'howToEarn', 'howToEarnGolden', 'id', 'isBattlegroundsBuddy', 
                'isBattlegroundsPoolMinion', 'isBattlegroundsPoolSpell', 'isMiniSet', 'mechanics', 
                'mercenariesAbilityCooldown', 'mercenariesRole', 'multiClassGroup', 'name', 'overload', 
                'puzzleType', 'questReward', 'race', 'races', 'rarity', 'referencedTags', 'set', 'spellDamage', 
                'spellSchool', 'targetingArrowText', 'techLevel', 'text', 'type']


def main():
    start_time = time.time()

    config = load_config()
    if not config:
        return
    prev_build, current_build, locale, scale = config

    print("Fetching data from HearthstoneJSON...")
    prev_build_data = fetch_json(prev_build, locale)
    current_build_data = fetch_json(current_build, locale)
    if not prev_build_data or not current_build_data:
        return
    
    db = setup_db()
    
    allowed_types = set_types(scale)
    create_tables(db, prev_build_data, current_build_data, allowed_types)
    compare_type = "dbfId" if prev_build >= 18336 else "id"
    check_changes(db, set(), allowed_types, compare_type, prev_build, current_build)
    elapsed_time = int(time.time() - start_time)
    print(f"Done! Finished in {elapsed_time // 60} min {elapsed_time % 60} s. Results in result/CardChanges_{prev_build}-{current_build}.txt")

if __name__ == "__main__":
    main()
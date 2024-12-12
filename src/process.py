import sqlite3
import os
import requests
import configparser
import time
from print_colors import printInfo, printError, printDebug

def create_tables(db, prev_build_data, current_build_data, allowed_types):
    printInfo("Creating tables...")
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
        columns = [f'"{change_type}"' if change_type in ["set", "text"] else change_type for change_type in allowed_types]
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?'] * len(columns))})"
        values_batch = []
        
        values_batch = [
            tuple(
                str(card.get(change_type)) if isinstance(card.get(change_type), (int, str))
                else ",".join(card[change_type]) if isinstance(card.get(change_type), list)
                else None
                for change_type in allowed_types
            )
            for card in cards
        ]

        db.executemany(sql, values_batch)
        printDebug(f"{len(values_batch)} cards added to {table_name}")

    printInfo(f"Creating table OldCards with {len(prev_build_data)} cards")
    insert_cards("OldCards", prev_build_data)

    printInfo(f"Creating table NewCards with {len(current_build_data)} cards")
    insert_cards("NewCards", current_build_data)

    printInfo("Finished creating tables")

def check_changes(db, excluded_dbfIds, allowed_types, compare_type, prev_build, current_build, locale, added_msg, removed_msg, changed_msg, type_txt, old_txt, new_txt):
    printInfo("Checking changes...")
    with open(f"result/CardChanges_{prev_build}-{current_build}_{locale}.txt", "w", encoding="utf-8") as CardChanges:
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
            CardChanges.write(f"{'#' * len(added_msg[locale])}\n{added_msg[locale]}\n{'#' * len(added_msg[locale])}\n\n")
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
            CardChanges.write(f"{'#' * len(removed_msg[locale])}\n{removed_msg[locale]}\n{'#' * len(removed_msg[locale])}\n\n")
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
        CardChanges.write(f"{'#' * len(changed_msg[locale])}\n{changed_msg[locale]}\n{'#' * len(changed_msg[locale])}\n\n")
        for key in allowed_types:
            key_fixed = key if key != "set" and key != "text" else "\"" + key + "\""
            sql = f"""SELECT OldCards.{compare_type}, OldCards.{key_fixed}, NewCards.{key_fixed}, OldCards.name, OldCards.id
                FROM OldCards
                LEFT JOIN NewCards
                ON OldCards.{compare_type} = NewCards.{compare_type}
                WHERE (NOT OldCards.{key_fixed} = NewCards.{key_fixed}) 
                    OR (OldCards.{key_fixed} IS NULL AND NOT NewCards.{key_fixed} IS NULL);"""
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
                    line1 = f"{row[3]} (dbfId {row[0]}, id {row[4]}) - {type_txt[locale]} {key}\n"
                else:
                    line1 = f"{row[3]} (id {row[4]}) - {type_txt[locale]} {key}\n"
                CardChanges.write(line1)
                line2 = f"* {old_txt[locale]} " + ("NULL" if len(row1) == 0 else row1.replace('\n', '\\n')) + "\n"
                CardChanges.write(line2)
                line3 = f"* {new_txt[locale]} " + ("NULL" if len(row2) == 0 else row2.replace('\n', '\\n')) + "\n"
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
        printError("Could not load contents of config.ini. Check that all values are correctly formatted.")
        return None

    if (prev_build == 0 and current_build == 0) or (prev_build >= current_build):
        printError("Invalid build numbers in config.ini. Must be non-0 and PREVIOUS_BUILD must be smaller than CURRENT_BUILD.")
        return None
    if locale not in ["deDE", "enUS", "esES", "esMX", "frFR", "itIT", "jaJP", "koKR", "plPL", "ptBR", "ruRU", "thTH", "zhCN", "zhTW"]:
        printError("Invalid LOCALE in config.ini.")
        return None
    if scale not in ["basic", "full"]:
        printError("Invalid SCALE in config.ini.")
        return None
    
    return prev_build, current_build, locale, scale

def fetch_json(build, locale):
    url = f"https://api.hearthstonejson.com/v1/{build}/{locale}/cards.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        printError(f"Failed to fetch data for build {build}. Double-check your build numbers and locale in config.ini. Status code: {response.status_code}")
        return None

def setup_db():
    db = sqlite3.connect(":memory:")
    dbCur = db.cursor()
    return dbCur

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

def set_locale_texts():
    added_msg = {
        "deDE": "Die folgenden Karten wurden hinzugefügt:",
        "enUS": "The following cards were added:",
        "esES": "Se añadieron las siguientes cartas:",
        "esMX": "Se agregaron las siguientes cartas:",
        "frFR": "Les cartes suivantes ont été ajoutées :",
        "itIT": "Le seguenti carte sono state aggiunte:",
        "jaJP": "次のカードが追加されました：",
        "koKR": "다음 카드가 추가되었습니다:",
        "plPL": "Dodano następujące karty:",
        "ptBR": "Foram adicionados os seguintes cards:",
        "ruRU": "Были добавлены следующие карты:",
        "thTH": "พิ่มการ์ดต่อไปนี้:",
        "zhCN": "添加了以下卡片：",
        "zhTW": "添加了以下卡片："
    }

    removed_msg = {
        "deDE": "Die folgenden Karten wurden entfernt:",
        "enUS": "The following cards were removed:",
        "esES": "Se eliminaron las siguientes cartas:",
        "esMX": "Se quitaron las siguientes cartas:",
        "frFR": "Les cartes suivantes ont été supprimées :",
        "itIT": "Le seguenti carte sono state rimosse:",
        "jaJP": "次のカードが削除されました：",
        "koKR": "다음 카드가 제거되었습니다:",
        "plPL": "Usunięto następujące karty:",
        "ptBR": "Foram removidos os seguintes cards:",
        "ruRU": "Были удалены следующие карты:",
        "thTH": "ลบการ์ดต่อไปนี้:",
        "zhCN": "移除了以下卡片：",
        "zhTW": "移除了以下卡片："
    }    

    changed_msg = {
        "deDE": "Die folgenden Karten wurden geändert:",
        "enUS": "The following cards received changes:",
        "esES": "Las siguientes cartas recibieron cambios:",
        "esMX": "Las siguientes cartas recibieron cambios:",
        "frFR": "Les cartes suivantes ont reçu des modifications :",
        "itIT": "Le seguenti carte hanno ricevuto modifiche:",
        "jaJP": "次のカードに変更が加えられました：",
        "koKR": "다음 카드가 변경되었습니다:",
        "plPL": "Następujące karty zostały zmienione:",
        "ptBR": "Os seguintes cards receberam alterações:",
        "ruRU": "Следующие карты были изменены:",
        "thTH": "การ์ดต่อไปนี้ได้รับการเปลี่ยนแปลง:",
        "zhCN": "以下卡片已被更改：",
        "zhTW": "以下卡片已被更改："
    }

    type_txt = {
        "deDE": "Typ:",
        "enUS": "Type:",
        "esES": "Tipo:",
        "esMX": "Tipo:",
        "frFR": "Type :",
        "itIT": "Tipo:",
        "jaJP": "タイプ：",
        "koKR": "유형:",
        "plPL": "Typ:",
        "ptBR": "Tipo:",
        "ruRU": "Тип:",
        "thTH": "ประเภท:",
        "zhCN": "类型：",
        "zhTW": "类型："
    }

    old_txt = {
        "deDE": "Alt:",
        "enUS": "Old:",
        "esES": "Antes:",
        "esMX": "Antes:",
        "frFR": "Précédemment :",
        "itIT": "Prima:",
        "jaJP": "旧：",
        "koKR": "변경 전:",
        "plPL": "Stara wersja:",
        "ptBR": "Antes:",
        "ruRU": "Было:",
        "thTH": "เก่า:",
        "zhCN": "旧版：",
        "zhTW": "舊版："
    }

    new_txt = {
        "deDE": "Neu:",
        "enUS": "New:",
        "esES": "Ahora:",
        "esMX": "Ahora:",
        "frFR": "Maintenant :",
        "itIT": "Ora:",
        "jaJP": "新：",
        "koKR": "변경 후:",
        "plPL": "Nowa wersja:",
        "ptBR": "Agora:",
        "ruRU": "Стало:",
        "thTH": "ใหม่:",
        "zhCN": "类型：",
        "zhTW": "新版："
    }

    return added_msg, removed_msg, changed_msg, type_txt, old_txt, new_txt

def main():
    start_time = time.time()

    config = load_config()
    if not config:
        return
    prev_build, current_build, locale, scale = config

    added_msg, removed_msg, changed_msg, type_txt, old_txt, new_txt = set_locale_texts()

    printInfo("Fetching data from HearthstoneJSON...")
    prev_build_data = fetch_json(prev_build, locale)
    current_build_data = fetch_json(current_build, locale)
    if not prev_build_data or not current_build_data:
        return
    
    db = setup_db()
    
    allowed_types = set_types(scale)
    create_tables(db, prev_build_data, current_build_data, allowed_types)
    compare_type = "dbfId" if prev_build >= 18336 else "id"
    check_changes(db, set(), allowed_types, compare_type, prev_build, current_build, locale, added_msg, removed_msg, changed_msg, type_txt, old_txt, new_txt)
    elapsed_time = int(time.time() - start_time)
    printInfo(f"Done! Finished in {elapsed_time // 60} min {elapsed_time % 60} s. Results in result/CardChanges_{prev_build}-{current_build}_{locale}.txt")

if __name__ == "__main__":
    main()
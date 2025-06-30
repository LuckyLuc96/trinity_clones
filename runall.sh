#!/bin/bash
set -e  # Exit on error

DB="trinity_world"


# Prompt for password once, hide input
read -s -p "Enter MySQL password: " MYSQL_PASS
echo

echo "Step 1: Export creature_template with exp=2"
mysql --max_allowed_packet=1G -u root -p$MYSQL_PASS --column-names -e "SELECT * FROM creature_template WHERE exp = 2;" $DB > npc_export_template.csv

echo "Step 2: Export joined creature and creature_template"
mysql --max_allowed_packet=1G -u root -p$MYSQL_PASS -B -e "SELECT c.*, ct.* FROM creature c JOIN creature_template ct ON c.id = ct.entry WHERE ct.exp = 2;" $DB > npc_export_map.csv

echo "Step 3: Generate duplicated_templates.sql"
python3 duplicate.py --input-csv npc_export_template.csv --new-id-start 900000 --output-sql duplicated_templates.sql --npc

echo "Step 4: Export duplicated NPCs"
mysql --max_allowed_packet=1G -u root -p$MYSQL_PASS $DB < duplicated_templates.sql

echo "Step 5: Generate duplicated_creatures.sql"
mysql --max_allowed_packet=1G -u root -p$MYSQL_PASS -B --column-names -e "SELECT * FROM creature_template WHERE entry >= 900000;" $DB > duplicated_npcs.csv

echo "Step 6: Create duplicated NPCs"
python3 duplicate.py --input-csv npc_export_map.csv --template-csv duplicated_npcs.csv --new-id-start 2000000 --output-sql duplicated_creatures.sql --creature

echo "Step 7: Import duplicated_creatures.sql"
mysql --max_allowed_packet=1G -u root -p$MYSQL_PASS $DB < duplicated_creatures.sql

echo "Finished"

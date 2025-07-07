This is free and open source software and uses the GPL-3 license.

The python script works alongside the trinity core mySQL database to duplicate all NPCs with the tag exp=2 or expansion level 2. From there it Duplicates their statistics across 20x NPCs that are identical in everyway 3xcept a new surname which indicates the intended phase value. The script then places these cloned NPCs into the world via the Creature table in 20x phases. The phases number 1 through 20 and use the value of 2 to the power of the desired phase, starting at zero. 2^0 = 1 and so on,and these phases are totally independent from each other. Game objects are not yet implemented in this script.

Many quests utlize various phases,and those phases are skipped, which is why there is a gap between phase 1 and phase 2 in the file.


Known Issues:

creature_data Table Missing
    - NPC duplication does not include the creature_data table, causing missing NPC attributes.

Solution: Additional function similar to the others in duplication.py (estimated 2–6 hours of work) See comment in code "TODO".

Phase Pollution (Phases 2–256):
    - NPCs between phases 2–256 have been cloned, polluting Phase 1–20 (1, 512+) with quest mobs that shouldn't be in the open world.

Solution: Partial logic exists but is  not yet implemented into the functions.


Installation:
On line 4 in both duplicate.py and in runall.sh (if you use the script to install) you'll want to replace the variable "DB" with the name of your database. The variable I use is "trinity_world".
Security Note: Using runall.sh stores your MySQL password in plaintext in your bash history.

**Option 1: Quick Setup (Less Secure)**
bash runall.sh

**Option 2: Manual Steps (More Secure)**

*Step 0: Login to mysql and set a variable*
SET GLOBAL max_allowed_packet=1073741824; -- 1GB buffer

exit mysql and continue:

*Step 1: Export NPC Templates:*
bash
mysql --max_allowed_packet=1G -u root -p -e "SELECT * FROM creature_template WHERE exp = 2;" trinity_world > npc_export_template.csv

*Step 2: Export NPC Map Data:*
mysql --max_allowed_packet=1G -u root -p trinity_world -B -e "SELECT c.*, ct.* FROM creature c JOIN creature_template ct ON c.id = ct.entry WHERE ct.exp = 2;" > npc_export_map.csv

*Step 3: Duplicate Templates:*
python3 duplicate.py --input-csv npc_export_template.csv --new-id-start 900000 --output-sql duplicated_templates.sql --npc
mysql --max_allowed_packet=1G -u root -p trinity_world < duplicated_templates.sql

*Step 4: Generate & Apply Creature Duplicates:*
mysql --max_allowed_packet=1G -u root -p -B --column-names -e "SELECT * FROM creature_template WHERE entry >= 900000;" trinity_world > duplicated_npcs.csv

python3 duplicate.py --input-csv npc_export_map.csv --template-csv duplicated_npcs.csv --new-id-start 2000000 --output-sql duplicated_creatures.sql --creature

mysql --max_allowed_packet=1G -u root -p trinity_world < duplicated_creatures.sql

**Further Development:**

The fastest way to test the generated SQL data is to drop your trinity_world database (or world if using TrinityCore).

The worldserver will regenerate it automatically.

**Support:**
For questions, contact:
  Discord: Judgefae
  Email: djhxiurr1@mozmail.com

Last Updated: 30 June 2025
Known Issues:

    creature_data Table Missing:

        NPC duplication does not include the creature_data table, causing missing NPC attributes.

        Solution Required: Additional code in duplication.py (estimated 2–6 hours of work).

    Phase Pollution (Phases 2–256):

        NPCs between phases 2–256 have been cloned, polluting Phase 1–20 (1, 512+) with quest mobs that shouldn't be in the open world.

        Status: Partial logic exists but is incomplete.

Installation:

⚠️ Security Note: Using runall.sh stores your MySQL password in plaintext in your bash history.
Option 1: Quick Setup (Less Secure)
bash.

bash runall.sh

Option 2: Manual Steps (More Secure)

    Increase MySQL Buffer (Run Once):
    sql

SET GLOBAL max_allowed_packet=1073741824; -- 1GB buffer

Export NPC Templates:
bash

mysql --max_allowed_packet=1G -u root -p -e "SELECT * FROM creature_template WHERE exp = 2;" trinity_world > npc_export_template.csv

Export NPC Map Data:
bash

mysql --max_allowed_packet=1G -u root -p trinity_world -B -e "SELECT c.*, ct.* FROM creature c JOIN creature_template ct ON c.id = ct.entry WHERE ct.exp = 2;" > npc_export_map.csv

Duplicate Templates:
bash

python3 duplicate.py --input-csv npc_export_template.csv --new-id-start 900000 --output-sql duplicated_templates.sql --npc
mysql --max_allowed_packet=1G -u root -p trinity_world < duplicated_templates.sql

Generate & Apply Creature Duplicates:
bash

    mysql --max_allowed_packet=1G -u root -p -B --column-names -e "SELECT * FROM creature_template WHERE entry >= 900000;" trinity_world > duplicated_npcs.csv
    python3 duplicate.py --input-csv npc_export_map.csv --template-csv duplicated_npcs.csv --new-id-start 2000000 --output-sql duplicated_creatures.sql --creature
    mysql --max_allowed_packet=1G -u root -p trinity_world < duplicated_creatures.sql

Testing Changes:

    The fastest way to test SQL generation is to drop your trinity_world database (or world if using vanilla TrinityCore).

    The worldserver will regenerate it automatically.

Support:

For questions, contact:

    Discord: Judgefae

    Email: djhxiurr1@mozmail.com

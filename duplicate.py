import csv
import argparse

'''
Simply two commands now: Login to mysql as root and run:
SET GLOBAL max_allowed_packet=1073741824;

In BASH not mysql run: bash runall.sh
OR
do the following 1 at a time:

mysql --max_allowed_packet=1G -u root -p -e "SELECT * FROM creature_template WHERE exp = 2;" trinity_world > npc_export_template.csv
mysql --max_allowed_packet=1G -u root -p trinity_world -B -e "SELECT c.*, ct.* FROM creature c JOIN creature_template ct ON c.id = ct.entry WHERE ct.exp = 2;" > npc_export_map.csv
python3 duplicate.py --input-csv npc_export_template.csv --new-id-start 900000 --output-sql duplicated_templates.sql --npc
mysql --max_allowed_packet=1G -u root -p trinity_world > duplicated_templates.sql
mysql --max_allowed_packet=1G -u root -p -B --column-names -e "SELECT * FROM creature_template WHERE entry >= 900000;" trinity_world > duplicated_npcs.csv
python3 duplicate.py --input-csv npc_export_map.csv --template-csv duplicated_npcs.csv --new-id-start 2000000 --output-sql duplicated_creatures.sql --creature
mysql --max_allowed_packet=1G -u root -p trinity_world < duplicated_creatures.sql
'''

PHASES = {
    1: 1,
    2: 512,
    3: 1024,
    4: 2048,
    5: 4096,
    6: 8192,
    7: 16384,
    8: 32768,
    9: 65536,
    10: 131072,
    11: 262144,
    12: 524288,
    13: 1048576,
    14: 2097152,
    15: 4194304,
    16: 8388608,
    17: 16777216,
    18: 33554432,
    19: 67108864,
    20: 134217728
}
# Phases to explicitly SKIP (1-255)
SKIP_PHASE_MASK = 0x1FF  # Binary mask covering phases 1 through 255

def parse_phase(subname):
    if "(" in subname:
        return int(subname.split("(")[1].split(",")[0])
    else:
        return int(subname.split(" ")[1])

def should_duplicate_npc(original_phase_mask):
    """
    Returns True only if NPC should be duplicated
    (Not in skipped phases and meets other criteria)
    """
    # Skip if in phases 1-255
    if original_phase_mask & SKIP_PHASE_MASK:
        return False

    # Add other exclusion logic as needed
    if original_phase_mask in [256, 512, 1024]:  # Example specific exclusions
        return False

    return True
#Mob data in the database
CREATURE_TEMPLATE_COLUMNS = [
    'entry', 'difficulty_entry_1', 'difficulty_entry_2', 'difficulty_entry_3',
    'KillCredit1', 'KillCredit2', 'modelid1', 'modelid2', 'modelid3', 'modelid4',
    'name', 'subname', 'IconName', 'gossip_menu_id', 'minlevel', 'maxlevel',
    'exp', 'faction', 'npcflag', 'speed_walk', 'speed_run', 'scale', 'rank',
    'dmgschool', 'BaseAttackTime', 'RangeAttackTime', 'BaseVariance', 'RangeVariance',
    'unit_class', 'unit_flags', 'unit_flags2', 'dynamicflags', 'family', 'type',
    'type_flags', 'lootid', 'pickpocketloot', 'skinloot', 'PetSpellDataId',
    'VehicleId', 'mingold', 'maxgold', 'AIName', 'MovementType', 'HoverHeight',
    'HealthModifier', 'ManaModifier', 'ArmorModifier', 'DamageModifier',
    'ExperienceModifier', 'RacialLeader', 'movementId', 'RegenHealth',
    'mechanic_immune_mask', 'spell_school_immune_mask', 'flags_extra',
    'ScriptName', 'StringId', 'VerifiedBuild'
]
#Mob data placed in the world
CREATURE_COLUMNS = ["guid" ,"id" ,"map" ,"zoneId" ,"areaId" ,"spawnMask" ,"phaseMask"
    ,"modelid" ,"equipment_id" ,"position_x" ,"position_y" ,"position_z" ,"orientation"
    ,"spawntimesecs" ,"wander_distance" ,"currentwaypoint" ,"curhealth" ,"curmana"
    ,"MovementType" ,"npcflag" ,"unit_flags" ,"dynamicflags" ,"ScriptName" ,"StringId"
    ,"VerifiedBuild"]

def get_default_value(column):
    defaults = {
        'entry': '0',
        'difficulty_entry_1': '0',
        # ... all other default values ...
        'VerifiedBuild': 'NULL'
    }
    return defaults.get(column, 'NULL')

def generate_npc_templates(input_csv: str, new_id_start: int, output_sql: str) -> None:
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        npc_data = list(reader)

    sql_commands = [
        "-- Auto-generated NPC TEMPLATE clones for all wrath of the lich king NPCs",
        "USE trinity_world;",
        "DELETE FROM creature_template WHERE entry >= 900000 AND subname LIKE 'Phase %';",
        "START TRANSACTION;"
    ]
    current_id = new_id_start
    all_value_rows = []

    for npc in npc_data:
        if npc.get('exp', '').strip() != '2':
            continue

        for phase_num in PHASES.items():
            new_npc = {}
            for col in CREATURE_TEMPLATE_COLUMNS:
                if col == 'entry':
                    new_npc[col] = str(current_id)
                elif col == 'subname':
                    new_npc[col] = f"Phase {phase_num[0]}"
                elif col == 'name':
                    new_npc[col] = npc.get(col, '')
                else:
                    new_npc[col] = npc.get(col, get_default_value(col))

            values = []
            for col in CREATURE_TEMPLATE_COLUMNS:
                val = new_npc[col]
                if val == 'NULL':
                    values.append('NULL')
                elif val.replace('.', '', 1).isdigit():
                    values.append(val)
                else:
                    escaped = val.replace('"', r'\"')
                    values.append(f'"{escaped}"')

            all_value_rows.append(f"({', '.join(values)})")
            current_id += 1

    escaped_columns_template = ', '.join(f'`{col}`' for col in CREATURE_TEMPLATE_COLUMNS)
    sql_commands.append(f"INSERT INTO creature_template ({escaped_columns_template}) VALUES")
    sql_commands.append(",\n".join(all_value_rows) + ";")
    sql_commands.append("COMMIT;")

    with open(output_sql, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_commands))

    print(f"Generated {len([n for n in npc_data if n.get('exp') == '2']) * len(PHASES)} NPC clones in {output_sql}")

def generate_creature(template_csv: str, original_csv: str, new_id_start: int, output_sql: str) -> None:
    # Load templates: map (name, phase) -> entry
    template_lookup = {}
    with open(template_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            if row.get("exp", '').strip() != '2':
                continue
            name = row.get("name", "").strip()
            subname = row.get("subname", "").strip()
            if subname.startswith("Phase "):
                phase_num = parse_phase(subname) #Required to make both CSV files compatible for cross referencing.
                template_lookup[(name, phase_num)] = row["entry"]

    # Load original creature data
    with open(original_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        original_creatures = list(reader)

    columns_with_backticks = [f'`{col}`' for col in CREATURE_COLUMNS]
    sql_commands = [
        "-- Auto-generated creature placements for all wrath NPCs across 20 phases",
        "USE trinity_world;",
        "DELETE FROM creature WHERE guid >= 2000000;",
        "START TRANSACTION;",
        f"INSERT INTO creature ({', '.join(columns_with_backticks)}) VALUES"
    ]

    current_guid = new_id_start
    all_value_rows = []
    for npc in original_creatures:
        if npc.get("exp", '').strip() != '2':
            continue
        name = npc.get("name", "").strip()
        for phase_num, phase_mask in PHASES.items():
            entry = template_lookup.get((name, phase_num))
            if not entry:
                continue

            new_row = {}
            for col in CREATURE_COLUMNS:
                if col == 'guid':
                    new_row[col] = str(current_guid)
                elif col == 'phaseMask':
                    new_row[col] = str(phase_mask)
                elif col == 'id':
                    new_row[col] = entry
                else:
                    new_row[col] = npc.get(col, get_default_value(col))

            formatted_values = []
            for col in CREATURE_COLUMNS:
                val = new_row[col]
                if val == 'NULL':
                    formatted_values.append('NULL')
                elif val.replace('.', '', 1).lstrip('-').isdigit():
                    formatted_values.append(val)
                else:
                    escaped = val.replace('"', r'\"')
                    formatted_values.append(f'"{escaped}"')

            all_value_rows.append(f"({', '.join(formatted_values)})")
            current_guid += 1

    sql_commands.append(",\n".join(all_value_rows) + ";")
    sql_commands.append("COMMIT;")

    with open(output_sql, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_commands))

    print(f"Generated {current_guid - new_id_start} creature placements in {output_sql}")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-csv", help="CSV of generated templates", required=False)
    parser.add_argument("--input-csv", help="Original creature placement CSV", required=True)
    parser.add_argument("--new-id-start", type=int, required=True)
    parser.add_argument("--output-sql", required=True)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--npc", action='store_true', help="Run NPC template generation")
    group.add_argument("--creature", action='store_true', help="Run creature placement generation")

    args = parser.parse_args()

    if args.npc:
        if not args.input_csv:
            raise ValueError("--input-csv is required when using --npc")
        generate_npc_templates(
            input_csv=args.input_csv,
            new_id_start=args.new_id_start,
            output_sql=args.output_sql
        )
    elif args.creature:
        if not args.template_csv:
            raise ValueError("--template-csv is required when using --creature")
        generate_creature(
            template_csv=args.template_csv,
            original_csv=args.input_csv,
            new_id_start=args.new_id_start,
            output_sql=args.output_sql
        )
VALASKA_PRESET_ID = "valaska"

VALASKA_SYSTEM_PROMPT = (
    "Setting name: Valaska, Tone: Grimdark high Fantasy. Valaska is an empty and inhospitable land of rolling hills, "
    "frozen wastes, meager grasslands, and open tundra with sporadic farms and the occasional wandering monster. "
    "It is always cold, with icy and dry winds blowing off the Evermore Glacier to the north, and boxed in by the "
    "Green Mountains to the south. The winters bring deep freezes, and in the summers, fog blankets the land and "
    "frigid waters from melting ice turn much of the tundra into boggy mud that is better traversed with sleds than "
    "wagons. As a result of the harsh environment, the Valaskan people are known to be a tough and close-knit folk, "
    "ever suspicious of outsiders. For much of its existence, Valaska was largely unclaimed and lawless outside of a "
    "few close-knit communities, and even when controlled by one kingdom or another, much of the land was devoid of "
    "civilization, save for scattered frontier towns occasionally defended by a keep or abbey. The realm was "
    "conquered and ruled for a 100 years by the tyrannical Witch-King Tholvrom Icebane before returning to its "
    "frontier status for another 50, and then becoming a barony of the Kingdom of Highbanner, ruled by King Garric "
    "Highbanner and his sons. The game always starts in the small town of Moosehearth, population 300, the largest "
    "settlement in Valaska. The user chooses one of six adventures within one day's horse ride and players normally "
    "arrive at the adventure location at dusk."
)

DEFAULT_IMAGE_FILE = "default-image.jpg"
MAP_IMAGE_FILE = "Valaska-Map.png"
ADVENTURE_SELECTION_IMAGE_FILE = "Adventure-selection.png"

PLAYER_ORDER = ["Joe", "Annie", "Tammey", "Rick", "Beau", "Sam", "Tom", "Jannet"]
CLASS_ORDER = ["Fighter", "Barbarian", "Rogue", "Ranger", "Paladin", "Cleric", "Druid", "Wizard"]

PLAYERS = {
    "Joe": {
        "player_id": "Joe",
        "name": "Joe",
        "archetype": "Orphan",
        "gender": "Male",
        "race": "Dwarf",
        "irl_job": "Social worker",
        "keywords": ["Protective", "Cautious", "Compassionate"],
        "display_text": (
            "You play cautiously but compassionately. You gravitate toward wounded NPCs, moral gray areas, and "
            "underdogs. You ask about consequences before charging ahead and you suggest mercy, negotiation, or "
            "protection of the vulnerable. Mechanically, you favor defensive positioning, resource preservation, and "
            "keeping the party safe rather than chasing glory. In roleplay, you are grounded and earnest, sometimes a "
            "little self-deprecating, and you portray quiet resilience. You do not hog the spotlight, but when "
            "someone is being mistreated in-game, you step forward firmly. You treat the game seriously but warmly."
        ),
    },
    "Annie": {
        "player_id": "Annie",
        "name": "Annie",
        "archetype": "Hero",
        "gender": "Female",
        "race": "Elf",
        "irl_job": "Retail",
        "keywords": ["Bold", "Inspiring", "Dramatic"],
        "display_text": (
            "You play boldly and decisively. You love cinematic moments, heroic speeches, and dramatic sacrifices. "
            "When tension rises, you lean in rather than pulling back. You are quick to volunteer your character for "
            "risk if it serves the party's honor or the story's momentum. Mechanically, you prioritize high-impact "
            "actions and visible contributions in combat. In roleplay, you enjoy emotional stakes and clear moral "
            "lines. At the table, you are enthusiastic, energetic, and visibly invested when the dice roll big."
        ),
    },
    "Tammey": {
        "player_id": "Tammey",
        "name": "Tammey",
        "archetype": "Caregiver",
        "gender": "Female",
        "race": "Half-Elf",
        "irl_job": "Nurse",
        "keywords": ["Supportive", "Steady", "Empathetic"],
        "display_text": (
            "You focus on keeping the group stable and supported. You track party health, resources, and emotional "
            "tone. Mechanically, you prioritize healing, buffs, and protective positioning. You enjoy scenes where "
            "your character offers comfort, guidance, or steady reassurance. In roleplay, you lean into empathy, "
            "mediation, and conflict resolution within the party."
        ),
    },
    "Rick": {
        "player_id": "Rick",
        "name": "Rick",
        "archetype": "Explorer",
        "gender": "Male",
        "race": "Human",
        "irl_job": "Park Ranger",
        "keywords": ["Curious", "Practical", "Observant"],
        "display_text": (
            "You are curious first, cautious second. You love discovering hidden paths, environmental details, and "
            "lore clues. You ask about terrain, weather, tracks, smells, and distant landmarks. Mechanically, you "
            "value scouting, mobility, and awareness. In roleplay, you are practical, observant, and outdoorsy in tone."
        ),
    },
    "Beau": {
        "player_id": "Beau",
        "name": "Beau",
        "archetype": "Rebel",
        "gender": "non-binary",
        "race": "Elf",
        "irl_job": "Human Resources",
        "keywords": ["Defiant", "Clever", "Disruptive"],
        "display_text": (
            "You challenge authority instinctively. When an NPC makes demands, you question motives. You look for "
            "systems of control and enjoy subverting them. Mechanically, you like clever tactics, exploiting "
            "weaknesses, and bending rules creatively. In roleplay, you lean into sarcasm, dry wit, and subtle "
            "defiance without descending into chaos for its own sake."
        ),
    },
    "Sam": {
        "player_id": "Sam",
        "name": "Sam",
        "archetype": "Jester",
        "gender": "Male",
        "race": "Gnome",
        "irl_job": "Customer Service",
        "keywords": ["Playful", "Expressive", "Unpredictable"],
        "display_text": (
            "You play for joy, chaos-light, and table laughter, but you are smarter than you appear. You make jokes "
            "in tense moments, use humor to diffuse conflict, and sometimes exaggerate your character's reactions for "
            "comedic effect. When stakes rise dramatically, you can pivot into surprising sincerity."
        ),
    },
    "Tom": {
        "player_id": "Tom",
        "name": "Tom",
        "archetype": "Magician",
        "gender": "Male",
        "race": "Human",
        "irl_job": "Engineer",
        "keywords": ["Analytical", "Strategic", "Precise"],
        "display_text": (
            "You approach the game like a system to understand and optimize. You analyze mechanics, probabilities, "
            "and synergies. You enjoy clever spell usage, layered tactics, and long-term strategic planning. In "
            "roleplay, you play characters who are thoughtful, analytical, and fascinated by how the world works."
        ),
    },
    "Jannet": {
        "player_id": "Jannet",
        "name": "Jannet",
        "archetype": "Ruler",
        "gender": "Female",
        "race": "Human",
        "irl_job": "School Principle",
        "keywords": ["Decisive", "Organized", "Authoritative"],
        "display_text": (
            "You naturally coordinate the group. You summarize plans, assign roles, and push toward decision closure. "
            "In roleplay, you lean into leadership, diplomacy, and structured negotiation. Mechanically, you prefer "
            "abilities that control space, influence allies, or establish order."
        ),
    },
}

CLASSES = {
    "Fighter": {
        "class_id": "Fighter",
        "name": "Fighter",
        "role": "Frontline combat specialist focused on weapon mastery, battlefield control, and durability.",
        "ability_scores": {"STR": 16, "DEX": 13, "CON": 15, "INT": 11, "WIS": 13, "CHA": 9},
        "hp_max": 12,
        "armor_class": 18,
        "speed": 30,
        "features": ["Fighting Style - Protection", "Second Wind"],
        "weapons": ["Longsword", "Handaxe"],
        "inventory": ["Chain mail", "Shield", "Longsword", "Handaxe x2", "Explorer's pack"],
        "doctrine": [
            "Hold the frontline.",
            "Protect weaker allies.",
            "Maintain control of enemy positioning.",
            "Sustain through longer fights.",
        ],
    },
    "Barbarian": {
        "class_id": "Barbarian",
        "name": "Barbarian",
        "role": "Shock trooper who absorbs damage and delivers devastating melee attacks.",
        "ability_scores": {"STR": 16, "DEX": 14, "CON": 15, "INT": 9, "WIS": 13, "CHA": 11},
        "hp_max": 15,
        "armor_class": 15,
        "speed": 30,
        "features": ["Rage", "Unarmored Defense"],
        "weapons": ["Greataxe", "Handaxes"],
        "inventory": ["Greataxe", "Handaxe x2", "Explorer's pack", "Javelins x4"],
        "doctrine": ["Charge dangerous enemies.", "Draw enemy attention.", "Break enemy lines through aggression."],
    },
    "Rogue": {
        "class_id": "Rogue",
        "name": "Rogue",
        "role": "Precision striker specializing in stealth, positioning, and exploiting enemy vulnerabilities.",
        "ability_scores": {"STR": 9, "DEX": 16, "CON": 13, "INT": 15, "WIS": 11, "CHA": 14},
        "hp_max": 9,
        "armor_class": 15,
        "speed": 30,
        "features": ["Sneak Attack", "Expertise", "Thieves' Cant"],
        "weapons": ["Rapier", "Shortbow"],
        "inventory": ["Leather armor", "Rapier", "Shortbow", "Arrows x20", "Thieves' tools", "Burglar pack"],
        "doctrine": ["Avoid direct confrontation.", "Strike distracted enemies.", "Exploit positioning."],
    },
    "Ranger": {
        "class_id": "Ranger",
        "name": "Ranger",
        "role": "Mobile tracker and ranged skirmisher who controls space through awareness and mobility.",
        "ability_scores": {"STR": 13, "DEX": 16, "CON": 14, "INT": 11, "WIS": 15, "CHA": 9},
        "hp_max": 12,
        "armor_class": 15,
        "speed": 30,
        "features": ["Favored Enemy", "Natural Explorer"],
        "weapons": ["Longbow", "Shortswords"],
        "inventory": ["Scale mail", "Longbow", "Arrows x20", "Shortswords x2", "Explorer's pack"],
        "doctrine": ["Fight at range when possible.", "Use terrain advantage.", "Track enemies and scout."],
    },
    "Paladin": {
        "class_id": "Paladin",
        "name": "Paladin",
        "role": "Armored champion who protects allies and destroys powerful enemies through divine strength.",
        "ability_scores": {"STR": 16, "DEX": 11, "CON": 15, "INT": 9, "WIS": 13, "CHA": 14},
        "hp_max": 12,
        "armor_class": 18,
        "speed": 30,
        "features": ["Divine Sense", "Lay on Hands"],
        "weapons": ["Longsword", "Javelins"],
        "inventory": ["Chain mail", "Shield", "Longsword", "Javelins x5", "Explorer's pack", "Holy symbol"],
        "doctrine": ["Stand beside the fighter in melee.", "Protect allies.", "Deliver decisive blows."],
    },
    "Cleric": {
        "class_id": "Cleric",
        "name": "Cleric",
        "role": "Divine support who heals allies, enhances party capability, and maintains battlefield stability.",
        "ability_scores": {"STR": 13, "DEX": 11, "CON": 14, "INT": 10, "WIS": 16, "CHA": 15},
        "hp_max": 10,
        "armor_class": 18,
        "speed": 30,
        "features": ["Spellcasting", "Divine Domain"],
        "weapons": ["Mace"],
        "inventory": ["Chain mail", "Shield", "Mace", "Holy symbol", "Priest pack"],
        "doctrine": ["Sustain the party.", "Heal injured allies.", "Maintain buffs."],
    },
    "Druid": {
        "class_id": "Druid",
        "name": "Druid",
        "role": "Nature caster who controls terrain and adapts between support, control, and offense.",
        "ability_scores": {"STR": 11, "DEX": 13, "CON": 14, "INT": 10, "WIS": 16, "CHA": 15},
        "hp_max": 10,
        "armor_class": 14,
        "speed": 30,
        "features": ["Spellcasting", "Druidic"],
        "weapons": ["Scimitar", "Quarterstaff"],
        "inventory": ["Hide armor", "Scimitar", "Druidic focus", "Explorer's pack"],
        "doctrine": ["Control battlefield space.", "Support allies.", "Disrupt enemy movement."],
    },
    "Wizard": {
        "class_id": "Wizard",
        "name": "Wizard",
        "role": "Arcane strategist who manipulates the battlefield through versatile spells and tactical control.",
        "ability_scores": {"STR": 9, "DEX": 14, "CON": 13, "INT": 16, "WIS": 12, "CHA": 11},
        "hp_max": 8,
        "armor_class": 12,
        "speed": 30,
        "features": ["Spellcasting", "Arcane Recovery"],
        "weapons": ["Quarterstaff"],
        "inventory": ["Spellbook", "Quarterstaff", "Component pouch", "Scholar pack"],
        "doctrine": ["Avoid direct melee combat.", "Control the battlefield.", "Use spells strategically."],
    },
}

MONSTERS = {
    "Animated Armor": {"monster_id": "Animated Armor", "ac": 18, "hp": 33, "attack_bonus": 4, "attack_text": "Slam 1d6+2"},
    "Bandit": {"monster_id": "Bandit", "ac": 12, "hp": 11, "attack_bonus": 3, "attack_text": "Scimitar 1d6+1 or Light Crossbow 1d8+1"},
    "Bandit Captain": {"monster_id": "Bandit Captain", "ac": 15, "hp": 65, "attack_bonus": 5, "attack_text": "Scimitar 1d6+3 (multiattack)"},
    "Berserker": {"monster_id": "Berserker", "ac": 13, "hp": 67, "attack_bonus": 5, "attack_text": "Greataxe 1d12+3"},
    "Ghast": {"monster_id": "Ghast", "ac": 13, "hp": 36, "attack_bonus": 5, "attack_text": "Bite 2d8+3, Claws 2d6+3 + paralysis"},
    "Giant Boar": {"monster_id": "Giant Boar", "ac": 12, "hp": 42, "attack_bonus": 5, "attack_text": "Tusk 2d6+3"},
    "Gibbering Mouther": {"monster_id": "Gibbering Mouther", "ac": 9, "hp": 67, "attack_bonus": 2, "attack_text": "Bite 5d6"},
    "Gray Ooze": {"monster_id": "Gray Ooze", "ac": 8, "hp": 22, "attack_bonus": 3, "attack_text": "Pseudopod 1d6+1 + acid"},
    "Guard": {"monster_id": "Guard", "ac": 16, "hp": 11, "attack_bonus": 3, "attack_text": "Spear 1d6+1"},
    "Mastiff": {"monster_id": "Mastiff", "ac": 12, "hp": 5, "attack_bonus": 3, "attack_text": "Bite 1d6+1 + knock prone"},
    "Minotaur Skeleton": {"monster_id": "Minotaur Skeleton", "ac": 12, "hp": 67, "attack_bonus": 6, "attack_text": "Greataxe 2d12+4"},
    "Orc": {"monster_id": "Orc", "ac": 13, "hp": 15, "attack_bonus": 5, "attack_text": "Greataxe 1d12+3"},
    "Priest": {"monster_id": "Priest", "ac": 13, "hp": 27, "attack_bonus": 2, "attack_text": "Mace 1d6 | Spellcaster"},
    "Scout": {"monster_id": "Scout", "ac": 13, "hp": 16, "attack_bonus": 4, "attack_text": "Shortsword 1d6+2 or Longbow 1d8+2"},
    "Shadow": {"monster_id": "Shadow", "ac": 12, "hp": 16, "attack_bonus": 4, "attack_text": "Strength Drain 2d6"},
    "Skeleton": {"monster_id": "Skeleton", "ac": 13, "hp": 13, "attack_bonus": 4, "attack_text": "Shortsword 1d6+2 or Shortbow 1d6+2"},
    "Swarm of Insects": {"monster_id": "Swarm of Insects", "ac": 12, "hp": 22, "attack_bonus": 3, "attack_text": "Swarm Bite 4d4"},
    "Thug": {"monster_id": "Thug", "ac": 11, "hp": 32, "attack_bonus": 4, "attack_text": "Mace 1d6+2 (multiattack)"},
    "Warhorse": {"monster_id": "Warhorse", "ac": 11, "hp": 19, "attack_bonus": 6, "attack_text": "Hooves 2d6+4"},
    "Warhorse Skeleton": {"monster_id": "Warhorse Skeleton", "ac": 13, "hp": 22, "attack_bonus": 6, "attack_text": "Hooves 2d6+4"},
    "Zombie": {"monster_id": "Zombie", "ac": 8, "hp": 22, "attack_bonus": 3, "attack_text": "Slam 1d6+1"},
}

ADVENTURES = {
    "icebane-castle": {
        "adventure_id": "icebane-castle",
        "title": "Treasure Hunting the Ruins of Icebane Castle",
        "description": (
            "The long-frozen fortress of Icebane Castle has begun to thaw along its southern face, revealing "
            "collapsed vaults and exposed relic chambers long sealed by ice. Local rumors speak of ancestral "
            "artifacts and forgotten war spoils buried beneath centuries of frost and ruin. Competing interests may "
            "already be moving toward the site. Discretion and speed are advised."
        ),
        "objectives": [
            {"id": "obj-1", "description": "Locate and recover at least one significant artifact or treasure from within the castle ruins.", "status": "pending"},
            {"id": "obj-2", "description": "Survive environmental hazards and any hostile forces occupying the site.", "status": "pending"},
            {"id": "obj-3", "description": "Exit the ruins with proof of recovery.", "status": "pending"},
        ],
        "monsters": ["Gray Ooze", "Orc", "Scout", "Shadow", "Thug", "Swarm of Insects"],
    },
    "east-marsh-raid": {
        "adventure_id": "east-marsh-raid",
        "title": "Midnight Raid of the East Marsh Orcs",
        "description": (
            "Scouting reports confirm that a band of orcs has established a temporary encampment in the East Marsh, "
            "staging raids against nearby trade routes. A covert nighttime strike could disrupt their operations and "
            "weaken future assaults. Stealth and coordination will determine success."
        ),
        "objectives": [
            {"id": "obj-1", "description": "Infiltrate or approach the orc encampment under cover of darkness.", "status": "pending"},
            {"id": "obj-2", "description": "Neutralize the war leader, supply cache, or primary threat source.", "status": "pending"},
            {"id": "obj-3", "description": "Withdraw before dawn with minimal civilian casualties or collateral damage.", "status": "pending"},
        ],
        "monsters": ["Orc", "Scout", "Thug", "Bandit Captain", "Giant Boar"],
    },
    "telas-wagons": {
        "adventure_id": "telas-wagons",
        "title": "Escort of the Telos Supply Wagons along the King's Way",
        "description": (
            "A caravan carrying critical provisions for the frontier settlement of Moosehearth must travel the King's "
            "Way to Glockstead, a route increasingly plagued by bandits and winter storms. The wagons are slow, "
            "vulnerable, and essential. Reliable escorts are needed to ensure safe delivery."
        ),
        "objectives": [
            {"id": "obj-1", "description": "Protect the supply wagons from hostile attacks or sabotage during transit.", "status": "pending"},
            {"id": "obj-2", "description": "Resolve at least one major complication during the journey.", "status": "pending"},
            {"id": "obj-3", "description": "Deliver the majority of supplies safely from Moosehearth to Glockstead.", "status": "pending"},
        ],
        "monsters": ["Scout", "Thug", "Bandit", "Bandit Captain", "Berserker"],
    },
    "old-people-barrow": {
        "adventure_id": "old-people-barrow",
        "title": "Tombrobbing the Old-People's Barrow",
        "description": (
            "An ancient burial mound known as the Old-People's Barrow has been partially unearthed by shifting frost. "
            "Local superstition warns against disturbing it, yet scholars and collectors believe it may contain relics "
            "from a pre-kingdom civilization. Enter at your own risk."
        ),
        "objectives": [
            {"id": "obj-1", "description": "Successfully enter and navigate the interior chambers of the barrow.", "status": "pending"},
            {"id": "obj-2", "description": "Recover at least one relic of historical or monetary value.", "status": "pending"},
            {"id": "obj-3", "description": "Escape the barrow alive, resolving any awakened guardians or curses.", "status": "pending"},
        ],
        "monsters": ["Zombie", "Shadow", "Animated Armor", "Skeleton", "Gibbering Mouther"],
    },
    "collecting-taxes": {
        "adventure_id": "collecting-taxes",
        "title": "Collecting 'Taxes' Along the King's Road",
        "description": (
            "Comely triads men pass along The King's Way road without paying their proper taxes to the local baron. "
            "Your mission is to make sure those taxes get paid, and who is to say if the gold really finds its way to "
            "the local baron or not."
        ),
        "objectives": [
            {"id": "obj-1", "description": "Engage with at least three trade convoys along The King's Way.", "status": "pending"},
            {"id": "obj-2", "description": "Secure agreed tribute in coin, goods, or binding contracts.", "status": "pending"},
            {"id": "obj-3", "description": "Maintain enough order that trade along the road continues without collapse.", "status": "pending"},
        ],
        "monsters": ["Bandit", "Guard", "Mastiff", "Warhorse", "Priest"],
    },
    "endless-glacier-undead": {
        "adventure_id": "endless-glacier-undead",
        "title": "Putting to Rest the Undead Along the Endless Glacier",
        "description": (
            "Travelers report restless dead wandering the ice fields of the Endless Glacier, drawn perhaps by "
            "forgotten battlefields beneath the snow. These undead threaten caravans and isolated outposts. A "
            "cleansing expedition is required to end the disturbance and restore safe passage."
        ),
        "objectives": [
            {"id": "obj-1", "description": "Report to Father Balgart at the Everflame Abbey.", "status": "pending"},
            {"id": "obj-2", "description": "Defeat or lay to rest the primary undead threat.", "status": "pending"},
            {"id": "obj-3", "description": "Ensure the glacier region is safe for travel.", "status": "pending"},
        ],
        "monsters": ["Warhorse Skeleton", "Zombie", "Skeleton", "Minotaur Skeleton", "Ghast"],
    },
}

PLAYER_NARRATIVE_LENSES = {
    "Joe": "Joe's narrative lens is protective, cautious, and compassionate. He pays close attention to harm, vulnerability, consequences, and the emotional cost of events. He notices who was endangered, who was protected, who was ignored, and who suffered quietly. He does not glorify violence for its own sake. He prefers grounded, humane storytelling over flashy spectacle.",
    "Annie": "Annie's narrative lens is bold, inspiring, and dramatic. She wants the adventure to feel heroic, cinematic, and emotionally charged. She is drawn to moments of courage, decisive action, sacrifice, and triumph under pressure. She prefers strong pacing, vivid action, and clear emotional stakes.",
    "Tammey": "Tammey's narrative lens is supportive, steady, and empathetic. She cares about the emotional state of the group, the bonds between characters, and the importance of keeping people safe and together. She notices reassurance, cooperation, tenderness, mediation, healing, and how stress affects people over time.",
    "Rick": "Rick's narrative lens is curious, practical, and observant. He is deeply interested in terrain, weather, movement, clues, physical details, and how people navigate the world around them. He values discovery over drama and enjoys stories that make the setting feel tangible and real.",
    "Beau": "Beau's narrative lens is defiant, clever, and disruptive. Beau notices power, control, hypocrisy, manipulation, status games, and cracks in authority. They enjoy irony, tension, and subtle subversion. They are drawn to scenes where rules are bent, pretension is punctured, and unjust systems are challenged.",
    "Sam": "Sam's narrative lens is playful, expressive, and unpredictable. He enjoys lively scenes, vivid reactions, sharp banter, comic relief, and absurd little details that make the world feel alive. When events become truly serious, his voice can pivot into sincerity and heart.",
    "Tom": "Tom's narrative lens is analytical, strategic, and precise. He is interested in causality, tactical decisions, problem solving, magical logic, and how one event leads to another. He values coherence, clarity, and the satisfaction of watching a plan succeed, fail, or adapt under pressure.",
    "Jannet": "Jannet's narrative lens is decisive, organized, and authoritative. She values structure, pacing, leadership, coordination, and clear narrative progression. She notices who took charge, how decisions were made, where the group hesitated, and how order was restored or broken.",
}

NARRATIVE_BASE_PROMPT = (
    "You are the Narrative Agent writing the completed adventure chapter. Hold these invariant rules: third-person past "
    "tense, include all major events, no contradiction of canon, no meta commentary, preserve chronology unless "
    "deliberately reordering for clarity, and output a polished chapter rather than a summary blob. The selected lens "
    "controls emphasis, tone, rhythm, and descriptive preferences. Write the chapter as continuous prose with clear "
    "paragraphs and no headings, bullet points, or meta labels."
)


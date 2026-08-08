from save.inspector.pal_identity import (
    extract_ref,
    all_refs,
    find_by_instance_id,
    find_by_exact_nickname,
    find_by_character_id_substring,
)


def make_entry(instance_id: str, character_id: str, nickname: str = "", is_player: bool = False, level: int | None = None):
    return {
        "key": {
            "PlayerUId": {"value": "00000000-0000-0000-0000-000000000001"},
            "InstanceId": {"value": instance_id},
            "DebugName": {"value": ""},
        },
        "value": {
            "RawData": {
                "value": {
                    "object": {
                        "SaveParameter": {
                            "value": {
                                "CharacterID": {"value": character_id},
                                "NickName": {"value": nickname},
                                "IsPlayer": {"value": is_player},
                                **({"Level": {"value": {"value": level}}} if level is not None else {}),
                            }
                        }
                    }
                }
            }
        },
    }


def test_extract_ref_basic_fields():
    entry = make_entry("guid-1", "Penguin", nickname="Waddles", level=5)
    ref = extract_ref(entry)
    assert ref.instance_id == "guid-1"
    assert ref.character_id == "Penguin"
    assert ref.nickname == "Waddles"
    assert ref.level == 5
    assert ref.is_player is False


def test_find_by_instance_id_is_exact_and_unique():
    refs = [extract_ref(make_entry("guid-1", "Penguin")), extract_ref(make_entry("guid-2", "Penguin"))]
    found = find_by_instance_id(refs, "guid-2")
    assert found is not None
    assert found.instance_id == "guid-2"
    assert find_by_instance_id(refs, "guid-missing") is None


def test_find_by_exact_nickname_returns_all_duplicates():
    """Per the identification hierarchy, nickname uniqueness must never be
    assumed -- two Pals can share a nickname."""
    refs = [
        extract_ref(make_entry("guid-1", "Penguin", nickname="Buddy")),
        extract_ref(make_entry("guid-2", "Sheepball", nickname="Buddy")),
        extract_ref(make_entry("guid-3", "Penguin", nickname="Other")),
    ]
    matches = find_by_exact_nickname(refs, "Buddy")
    assert {m.instance_id for m in matches} == {"guid-1", "guid-2"}


def test_find_by_character_id_returns_every_instance_of_the_species():
    """CharacterID identifies the species, not an individual -- this must
    surface every instance, never silently pick one."""
    refs = [
        extract_ref(make_entry("guid-1", "BOSS_Umihebi_Fire")),
        extract_ref(make_entry("guid-2", "BOSS_Umihebi_Fire")),
        extract_ref(make_entry("guid-3", "BOSS_Umihebi")),
    ]
    matches = find_by_character_id_substring(refs, "umihebi_fire")
    assert {m.instance_id for m in matches} == {"guid-1", "guid-2"}


def test_all_refs_walks_full_character_map():
    parsed = {
        "properties": {
            "worldSaveData": {
                "value": {
                    "CharacterSaveParameterMap": {
                        "value": [make_entry("guid-1", "Penguin"), make_entry("guid-2", "Sheepball")]
                    }
                }
            }
        }
    }
    refs = all_refs(parsed)
    assert len(refs) == 2
    assert {r.instance_id for r in refs} == {"guid-1", "guid-2"}

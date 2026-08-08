from save.inspector.pal_identity import extract_ref
from save.normalization.pal_mapper import map_pal_entry_to_instance


def byte_prop(value):
    return {"id": None, "value": {"type": "None", "value": value}, "type": "ByteProperty"}


def leaf(prop_type, value):
    return {"id": None, "value": value, "type": prop_type}


def array_prop(array_type, values):
    return {"array_type": array_type, "id": None, "value": {"values": values}, "type": "ArrayProperty"}


def make_pal_entry(
    instance_id="guid-1",
    character_id="Penguin",
    nickname="",
    level=5,
    rank=None,
    soul_hp=None,
    hp_raw=1000000,
):
    sp = {
        "CharacterID": leaf("NameProperty", character_id),
        "NickName": leaf("StrProperty", nickname),
        "Gender": {"id": None, "type": "EnumProperty", "value": {"type": "EPalGenderType", "value": "EPalGenderType::Male"}},
        "Level": byte_prop(level),
        "Exp": leaf("Int64Property", 12345),
        "PassiveSkillList": array_prop("NameProperty", ["Skill_A", "Skill_B"]),
        "EquipWaza": array_prop("EnumProperty", ["EPalWazaID::Foo"]),
        "MasteredWaza": array_prop("EnumProperty", ["EPalWazaID::Foo", "EPalWazaID::Bar"]),
        "Talent_HP": byte_prop(80),
        "Talent_Shot": byte_prop(70),
        "Talent_Defense": byte_prop(60),
        "IsPlayer": {"id": None, "value": False, "type": "BoolProperty"},
        "Hp": {
            "struct_type": "FixedPoint64",
            "id": None,
            "type": "StructProperty",
            "value": {"Value": leaf("Int64Property", hp_raw)},
        },
        "OwnerPlayerUId": leaf("StructProperty", "00000000-0000-0000-0000-000000000001"),
        "OldOwnerPlayerUIds": {
            "id": None,
            "type": "StructProperty",
            "prop_name": "OldOwnerPlayerUIds",
            "value": {"values": ["00000000-0000-0000-0000-000000000001"]},
        },
        "SlotId": {
            "id": None,
            "type": "StructProperty",
            "value": {
                "ContainerId": {
                    "id": None,
                    "type": "StructProperty",
                    "value": {"ID": leaf("StructProperty", "container-guid")},
                },
                "SlotIndex": leaf("IntProperty", 3),
            },
        },
        "FriendshipPoint": leaf("IntProperty", 100),
        "FriendshipOtomoSec": leaf("IntProperty", 10),
        "FriendshipActiveOtomoSec": leaf("IntProperty", 5),
        "FriendshipBasecampSec": leaf("IntProperty", 20),
    }
    if rank is not None:
        sp["Rank"] = byte_prop(rank)
    if soul_hp is not None:
        sp["Rank_HP"] = byte_prop(soul_hp)

    entry = {
        "key": {
            "PlayerUId": {"value": "00000000-0000-0000-0000-000000000001"},
            "InstanceId": {"value": instance_id},
            "DebugName": {"value": ""},
        },
        "value": {"RawData": {"value": {"object": {"SaveParameter": {"value": sp}}}}},
    }
    return entry


def test_maps_basic_identity_and_stats():
    ref = extract_ref(make_pal_entry(instance_id="guid-1", character_id="Penguin", level=5))
    pal = map_pal_entry_to_instance(ref)
    assert pal.instance_id == "guid-1"
    assert pal.species_id == "Penguin"
    assert pal.is_player is False
    assert pal.level == 5
    assert pal.experience == 12345
    assert pal.potential_hp == 80
    assert pal.potential_shot == 70
    assert pal.potential_defense == 60


def test_maps_skills():
    ref = extract_ref(make_pal_entry())
    pal = map_pal_entry_to_instance(ref)
    assert pal.passive_skills == ("Skill_A", "Skill_B")
    assert pal.equipped_active_skills == ("EPalWazaID::Foo",)
    assert pal.mastered_active_skills == ("EPalWazaID::Foo", "EPalWazaID::Bar")


def test_hp_scaling_applied():
    ref = extract_ref(make_pal_entry(hp_raw=5244000))
    pal = map_pal_entry_to_instance(ref)
    assert pal.hp == 5244.0


def test_condensation_rank_absent_by_default():
    ref = extract_ref(make_pal_entry())
    pal = map_pal_entry_to_instance(ref)
    assert pal.condensation_rank is None


def test_condensation_rank_and_soul_are_independent_fields():
    ref = extract_ref(make_pal_entry(rank=5, soul_hp=20))
    pal = map_pal_entry_to_instance(ref)
    assert pal.condensation_rank == 5
    assert pal.soul_hp == 20
    # not condensation-derived: the other three souls remain unset
    assert pal.soul_attack is None
    assert pal.soul_defence is None
    assert pal.soul_work_speed is None


def test_slot_and_ownership():
    ref = extract_ref(make_pal_entry())
    pal = map_pal_entry_to_instance(ref)
    assert pal.slot.container_id == "container-guid"
    assert pal.slot.slot_index == 3
    assert pal.owner_player_uid == "00000000-0000-0000-0000-000000000001"


def test_friendship_stats():
    ref = extract_ref(make_pal_entry())
    pal = map_pal_entry_to_instance(ref)
    assert pal.friendship.points == 100
    assert pal.friendship.otomo_seconds == 10
    assert pal.friendship.active_otomo_seconds == 5
    assert pal.friendship.basecamp_seconds == 20

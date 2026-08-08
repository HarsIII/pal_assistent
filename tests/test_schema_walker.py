from save.inspector.schema_walker import (
    SchemaWalker,
    count_by_top_level_array_or_map,
    summarize_top_level,
)


def leaf(prop_type: str, value):
    return {"id": None, "type": prop_type, "value": value}


def struct_nested(struct_type: str, children: dict):
    return {"id": None, "type": "StructProperty", "struct_type": struct_type, "value": children}


def struct_raw(struct_type: str, value):
    return {"id": None, "type": "StructProperty", "struct_type": struct_type, "value": value}


def array_of_values(array_type: str, values: list):
    return {"id": None, "type": "ArrayProperty", "array_type": array_type, "value": {"values": values}}


def array_custom_decoded(array_type: str, decoded: dict):
    return {"id": None, "type": "ArrayProperty", "array_type": array_type, "value": decoded}


def map_property(key_type: str, value_type: str, entries: list):
    return {
        "id": None,
        "type": "MapProperty",
        "key_type": key_type,
        "value_type": value_type,
        "value": entries,
    }


def test_walks_leaf_properties():
    walker = SchemaWalker()
    walker.walk_properties({"Level": leaf("IntProperty", 5)})
    assert "Level" in walker.paths
    assert walker.paths["Level"].occurrences == 1


def test_walks_nested_struct():
    walker = SchemaWalker()
    props = {
        "Hp": struct_nested("FixedPoint64", {"Value": leaf("Int64Property", 776000)}),
    }
    walker.walk_properties(props)
    assert "Hp.Value" in walker.paths
    assert walker.paths["Hp.Value"].example == 776000


def test_walks_raw_struct_as_leaf_like():
    walker = SchemaWalker()
    props = {"Position": struct_raw("Vector", {"x": 1.0, "y": 2.0, "z": 3.0})}
    walker.walk_properties(props)
    assert "Position" in walker.paths
    assert any("raw" in s for s in walker.paths["Position"].shapes_seen)


def test_walks_array_with_values():
    walker = SchemaWalker()
    props = {"PassiveSkillList": array_of_values("NameProperty", ["Skill_A", "Skill_B"])}
    walker.walk_properties(props)
    assert "PassiveSkillList[]" in walker.paths
    assert walker.paths["PassiveSkillList[]"].occurrences == 2


def test_walks_custom_decoded_array_recursively():
    """This is the exact shape that tripped up the first implementation:
    a rawdata custom decoder replaces {"values": [...]} with its own dict,
    e.g. RawData -> {"object": {...}}. Must recurse, not treat as opaque leaf.
    """
    walker = SchemaWalker()
    props = {
        "RawData": array_custom_decoded(
            "ByteProperty",
            {"object": {"SaveParameter": struct_nested("PalX", {"Level": leaf("ByteProperty", 10)})}},
        )
    }
    walker.walk_properties(props)
    assert "RawData.object.SaveParameter.Level" in walker.paths
    assert walker.paths["RawData.object.SaveParameter.Level"].example == 10


def test_walks_map_property_by_key():
    walker = SchemaWalker()
    props = {
        "CharacterSaveParameterMap": map_property(
            "StructProperty",
            "StructProperty",
            [
                {"key": {"value": "guid-1"}, "value": {"CharacterID": leaf("NameProperty", "Penguin")}},
                {"key": {"value": "guid-2"}, "value": {"CharacterID": leaf("NameProperty", "Sheepball")}},
            ],
        )
    }
    walker.walk_properties(props)
    assert "CharacterSaveParameterMap{}.CharacterID" in walker.paths
    assert walker.paths["CharacterSaveParameterMap{}.CharacterID"].occurrences == 2


def test_summarize_top_level():
    props = {"Level": leaf("IntProperty", 5), "Name": leaf("StrProperty", "x")}
    assert summarize_top_level(props) == {"Level": "IntProperty", "Name": "StrProperty"}


def test_count_by_top_level_array_or_map():
    props = {
        "Items": array_of_values("IntProperty", [1, 2, 3]),
        "worldSaveData": struct_nested(
            "PalWorldSaveData",
            {"BaseCampSaveData": map_property("Guid", "StructProperty", [{"key": {"value": "a"}, "value": {}}])},
        ),
    }
    counts = count_by_top_level_array_or_map(props)
    assert counts["Items"] == 3
    assert counts["worldSaveData.BaseCampSaveData"] == 1

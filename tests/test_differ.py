from save.differential.differ import diff_properties, ChangeType


def leaf(prop_type: str, value):
    return {"id": None, "type": prop_type, "value": value}


def struct_nested(struct_type: str, children: dict):
    return {"id": None, "type": "StructProperty", "struct_type": struct_type, "value": children}


def map_property(key_type: str, value_type: str, entries: list):
    return {
        "id": None,
        "type": "MapProperty",
        "key_type": key_type,
        "value_type": value_type,
        "value": entries,
    }


def array_of_values(array_type: str, values: list):
    return {"id": None, "type": "ArrayProperty", "array_type": array_type, "value": {"values": values}}


def changes_by_path(changes):
    return {c.path: c for c in changes}


def test_leaf_value_changed():
    before = {"Level": leaf("IntProperty", 47)}
    after = {"Level": leaf("IntProperty", 48)}
    changes = diff_properties(before, after)
    assert len(changes) == 1
    assert changes[0].path == "Level"
    assert changes[0].change_type is ChangeType.CHANGED
    assert changes[0].before == 47
    assert changes[0].after == 48


def test_leaf_unchanged_produces_no_diff():
    before = {"Level": leaf("IntProperty", 47)}
    after = {"Level": leaf("IntProperty", 47)}
    assert diff_properties(before, after) == []


def test_property_added_and_removed():
    before = {"A": leaf("IntProperty", 1)}
    after = {"B": leaf("IntProperty", 2)}
    changes = changes_by_path(diff_properties(before, after))
    assert changes["A"].change_type is ChangeType.REMOVED
    assert changes["B"].change_type is ChangeType.ADDED


def test_nested_struct_field_changed():
    before = {"Hp": struct_nested("FixedPoint64", {"Value": leaf("Int64Property", 100)})}
    after = {"Hp": struct_nested("FixedPoint64", {"Value": leaf("Int64Property", 200)})}
    changes = changes_by_path(diff_properties(before, after))
    assert "Hp.Value" in changes
    assert changes["Hp.Value"].before == 100
    assert changes["Hp.Value"].after == 200


def test_indexed_array_change_and_growth():
    before = {"Skills": array_of_values("NameProperty", ["A", "B"])}
    after = {"Skills": array_of_values("NameProperty", ["A", "C", "D"])}
    changes = changes_by_path(diff_properties(before, after))
    assert changes["Skills[]#1"].change_type is ChangeType.CHANGED
    assert changes["Skills[]#1"].before == "B"
    assert changes["Skills[]#1"].after == "C"
    assert changes["Skills[]#2"].change_type is ChangeType.ADDED
    assert changes["Skills[]#2"].after == "D"


def test_keyed_map_tracks_identity_not_position():
    before = {
        "CharacterSaveParameterMap": map_property(
            "Guid",
            "StructProperty",
            [
                {"key": {"value": "pal-1"}, "value": {"Level": leaf("ByteProperty", 5)}},
                {"key": {"value": "pal-2"}, "value": {"Level": leaf("ByteProperty", 9)}},
            ],
        )
    }
    # Reordered, and pal-1 leveled up -- a keyed diff should not be fooled by order.
    after = {
        "CharacterSaveParameterMap": map_property(
            "Guid",
            "StructProperty",
            [
                {"key": {"value": "pal-2"}, "value": {"Level": leaf("ByteProperty", 9)}},
                {"key": {"value": "pal-1"}, "value": {"Level": leaf("ByteProperty", 6)}},
            ],
        )
    }
    changes = changes_by_path(diff_properties(before, after))
    assert len(changes) == 1
    key = next(iter(changes))
    assert "pal-1" in key
    assert changes[key].before == 5
    assert changes[key].after == 6


def test_map_entry_added_and_removed():
    before = {
        "M": map_property("Guid", "IntProperty", [{"key": {"value": "x"}, "value": leaf("IntProperty", 1)}])
    }
    after = {
        "M": map_property("Guid", "IntProperty", [{"key": {"value": "y"}, "value": leaf("IntProperty", 2)}])
    }
    changes = changes_by_path(diff_properties(before, after))
    assert any(c.change_type is ChangeType.REMOVED for c in changes.values())
    assert any(c.change_type is ChangeType.ADDED for c in changes.values())

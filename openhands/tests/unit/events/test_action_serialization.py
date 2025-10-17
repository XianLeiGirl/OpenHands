def serialization_deserialization(
    original_action_dict, cls, max_message_chars: int = 10000
):
    action_instance = event_from_dict(original_action_dict)
    assert isinstance(action_instance, Action), (
        'The action instance should be an instance of Action.'
    )
    assert isinstance(action_instance, cls), (
        'The action instance should be an instance of Action.'
    )

    serialized_action_dict = event_to_dict(action_instance)

    serialized_action_dict.pop('message')

    assert serialized_action_dict == original_action_dict, (
        'The action instance should be an instance of Action.'
    )    
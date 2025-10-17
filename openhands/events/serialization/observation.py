observations = (
    NullObservation,
    CmdOutputObservation,
    IPythonRunCellObservation,
    BrowserOutputObservation,
    FileReadObservation,
    FileWriteObservation,
    FileEditObservation,
    AgentDelegateObservation,
    SuccessObservation,
    ErrorObservation,
    AgentStateChangedObservation,
    UserRejectObservation,
    AgentCondensationObservation,
    AgentThinkObservation,
    RecallObservation,
    MCPObservation,
    FileDownloadObservation,
    TaskTrackingObservation,
)

OBSERVATION_TYPE_TO_CLASS = {
    observation_class.observation: observation_class 
    for observation_class in observations
}

def _update_cmd_output_metadata(
    metadata: dict[str, Any] | CmdOutputMetadata | None, **kwargs: Any
) -> dict[str, Any] | CmdOutputMetadata:
    if metadata is None:
        return CmdOutputMetadata(**kwargs)
    if isinstance(metadata, dict):
        metadata.update(kwargs)
    elif isinstance(metadata, CmdOutputMetadata):
        for key, value in kwargs.items():
            setattr(metadata, key, value)
    return metadata

def handle_observation_deprecated_extras(extras: dict) -> dict:
    if 'exit_code' in extras:
        extras['metadata'] = _update_cmd_output_metadata(
            extras.get('metadata', None), exit_code=extras.pop('exit_code')
        )
    if 'command_id' in extras:
        extras['metadata'] = _update_cmd_output_metadata(
            extras.get('metadata', None), pid=extras.pop('command_id')
        )    

    if 'formatted_output_and_error' in extras:
        extras.pop('formatted_output_and_error')
    return extras    


def observation_from_dict(observation: dict) -> Observation:
    observation = observation.copy()
    if 'observation' not in observation:
        raise KeyError(f"'observation' key is not found in {observation=}")
    observataion_class = OBSERVATION_TYPE_TO_CLASS.get(observation['observation'])
    if observataion_class is None:
        raise KeyError(
            f"'{observation['observation']=}' is not defined. Available observations: {OBSERVATION_TYPE_TO_CLASS.keys()}"
        )
    observation.pop('observation')
    observation.pop('message', None)
    content = observation.pop('content', '')
    extras = copy.deepcopy(observation.pop('extras', {}))

    extras = handle_observation_deprecated_extras(extras)
    
    if observation_class is CmdOupputObservation:
        if 'metadata' in extras and isinstance(extras['metadata'], dict):
            extras['metadata'] = CmdOutputMetadata(**extras['metadata'])
        elif 'metadata' in extras and isinstance(extras['metadata'], CmdOutputMetadata):
            pass
        else:
            extras['metadata'] = CmdOutputMetadata()

    if observation_class is RecallObservation:
        if 'recall_type' in extras:
            extras['recall_type'] = RecallType(extras['recall_type'])

        if 'microagent_knowledge' in extras and isinstance(
            extras['microagent_knowledge'], list
        ):
            extras['microagent_knowledge'] = [
                MicroagentKnowledge(**item) if isinstance(item, dict) else item
                for item in extras['microagent_knowledge']
            ]

    obs = observataion_class(content=content, **extras)
    assert isinstance(obs, Observation)
    return obs

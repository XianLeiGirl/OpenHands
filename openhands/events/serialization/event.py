from dataclasses import asdict
from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from openhands.events import Event

TOP_KEYS = [
    'id',
    'timestamp',
    'source',
    'message',
    'cause',
    'action',
    'observation',
    'tool_call_metadata',
    'llm_metrics',
]

def event_to_dict(event: 'Event') -> dict: # LOOK: Event的attr键是怎么从属性转过来的？recall_type
    props = asdict(event)

    d = {}
    for key in TOP_KEYS:
        if hasattr(event, key) and getattr(event, key) is not None:
            d[key] = getattr(event, key)
        elif hasattr(event, f'_{key}') and getattr(event, f'_{key}') is not None:
            d[key] = getattr(event, f'_{key}')
        if key == 'id' and d.get('id') == -1:
            d.pop('id', None)
        if key == 'timestamp' and 'timestamp' in d:
            if isinstance(d['timestamp'], datetime):
                d['timestamp'] = d['timestamp'].isoformat()
        if key == 'source' and 'source' in d:
            d['source'] = d['source'].value
        if key == 'recall_type' and 'recall_type' in d:
            d['recall_type'] = d['recall_type'].value
        if key == 'tool_call_metadata' and 'tool_call_metadata' in d:
            d['tool_call_metadata'] = d['tool_call_metadata'].model_dump() # LOOK: model_dump什么时候能用？
        if key == 'llm_metrics' and 'llm_metrics' in d:
            d['llm_metrics'] = d['llm_metrics'].get()
        props.pop(key, None)

    if 'security_risk' in props and props['security_risk'] is None:
        props.pop('security_risk')

    if 'task_completed' in props and props['task_completed'] is None:
        props.pop('task_completed')
    if 'action' in d:
        if 'security_risk' in props:
            props['security_risk'] = props['security_risk'].value
        d['args'] = props  
        if event.timeout is not None:
            d['timeout'] = event.timeout
    elif 'observation' in d:
        d['content'] = props.pop('content', '')
        d['extras'] = {
            k: (v.value if isinstance(v, Enum) else _convert_pydantic_to_dict(v))
            for k, v in props.items()
        }
        if hasattr(event, 'success'):
            d['success'] = event.success
    else:
        raise ValueError(f'Event must be either action or observation. has: {event}')
    return d            

def _convert_pydantic_to_dict(obj: BaseModel | dict) -> dict:
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    return obj    


###########pratice asdict############
def asdict(obj, *, dict_factory: dict):
    if not _is_dataclass_instance(obj):
        raise TypeError("asdict() should be called on dataclass instances")
    return _asdict_inner(obj, dict_factory)    

_FIELDS = '__dataclass_fields__'
_ATOMIC_TYPES = frozenset({
    types.NoneType,
    bool, 
    
})

def _is_dataclass_instance(obj):
    return hasattr(type(obj), _FIELDS)

def _asdict_inner(obj, dict_factory):
    if type(obj) in 
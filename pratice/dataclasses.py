import types
import copy

###########pratice asdict############
# TODO: 所以最后出来是啥？

_FIELDS = '__dataclass_fields__'
_ATOMIC_TYPES = frozenset({
    types.NoneType,
    bool, 
    int,
    float,
    str,
    complex,
    bytes,
    types.EllipsisType,
    types.NotImplementedType,
    types.CodeType,
    types.BuiltinFunctionType,
    types.FunctionType,
    type,
    range,
    property,
})

class _FIELD_BASE:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name    

_FIELD = _FIELD_BASE('_FIELD')

def asdict(obj, *, dict_factory: dict):
    if not _is_dataclass_instance(obj):
        raise TypeError("asdict() should be called on dataclass instances")
    return _asdict_inner(obj, dict_factory)    
    
def _is_dataclass_instance(obj):
    return hasattr(type(obj), _FIELDS)

def fields(class_or_instance):
    try:
        fields = getattr(class_or_instance, _FIELDS)
    except AttributeError:
        raise TypeError('must be called with a dataclass type or instance') from None

    return tuple(f for f in fields.values() if f._field_type is _FIELD)       

def _asdict_inner(obj, dict_factory):
    if type(obj) in _ATOMIC_TYPES:
        return obj
    elif _is_dataclass_instance(obj):
        if dict_factory is dict:
            return {
                f.name: _asdict_inner(getattr(obj, f.name), dict)
                for f in fields(obj)
            }
        else:
            result = []
            for f in fields(obj):
                value = _asdict_inner(getattr(obj, f.name), dict_factory)
                result.append((f.name, value))
                return dict_factory(result)
    elif isinstance(obj, tuple) and hasattr(obj, '_fields'): 
        return type(obj)(*[_asdict_inner(v, dict_factory) for v in obj])
    elif isinstance(obj, (list, tuple)):
        return type(obj)([_asdict_inner(v, dict_factory) for v in obj])
    elif isinstance(obj, dict):
        if hasattr(obj, 'default_factory'):
            result = type(obj)(getattr(obj, 'default_factory'))
            for k, v in obj.items():
                result[_asdict_inner(k, dict_factory)] = _asdict_inner(v, dict_factory)
            return result
        return type(obj)((_asdict_inner(k, dict_factory),
                        _asdict_inner(v, dict_factory)
                        for k, v in obj.items()))    

    else:
        return copy.deepcopy(obj)

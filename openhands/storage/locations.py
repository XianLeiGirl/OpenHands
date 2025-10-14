CONVERSATION_BASE_DIR = 'sessions'

def get_conversion_dir(sid: str, user_id: str | None = None) -> str:
    if user_id:
        return f"users/{user_id}/conversations/{sid}/"
    else:
        return f'{CONVERSATION_BASE_DIR}/{sid}/'    

def get_conversation_events_dir(sid: str, user_id: str | None = None) -> str:
    return f'{get_conversion_dir(sid, user_id)}events/'

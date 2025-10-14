from openhands.storage.files import FileStore

class EventStore(EventStoreABC):
    sid: str
    file_store: FileStore
    user_id: str | None
    cache_size: int = 25
    _cur_id: int | None = None

    @property
    def cur_id(self) -> int:
        if self._cur_id is None:
            self._cur_id = self._calculate_cur_id()
        return self._cur_id

    @cur_id.setter
    def cur_id(self, value: int) -> None:
        self._cur_id = value   

    def _calculate_cur_id(self) -> int:
        events = []
        try:
            events_dir = get_conversation_events_dir(self.sid, self.user_id)
            events = self.file_store.list(events_dir)
        except FileNotFoundError:
            logger.debug(f'No events found for session {self.sid} at {events_dir}')

        if not events:
            return 0

        max_id = -1
        for event_str in events:
            id = self._get_id_from_filename(event_str)
            if id >= max_id:
                max_id = id
        return max_id + 1


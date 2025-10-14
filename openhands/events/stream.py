from openhands.storage.locations import get_conversation_events_dir
from openhands.storage.files import FileStore
from openhands.events.event_store import EventStore
from enum import Enum


class EventStreamSubscriber(str, Enum):
    AGENT_CONTROLLER = 'agent_controller'
    RESOLVER = 'openhands_resolver'
    SERVER = 'server'
    RUNTIME = 'runtime'
    MEMORY = 'memory'
    MAIN = 'main'
    TEST = 'test'

class EventStream(EventStore):
    secrets: dict[str, str]
    _subscribers: dict[str, dict[str, Callable]]
    _lock: threading.Lock
    _queue: queue.Queue[Event]
    _queue_thread: threading.Thread
    _queue_loop: asyncio.AbstractEventLoop | None
    _thread_pools: dict[str, dict[str, ThreadPoolExecutor]]
    _thread_loops: dict[str, dict[str, asyncio.AbstractEventLoop]]
    _write_page_cache: list[dict]

    def __init__(self, sid: str, file_store: FileStore, user_id: str | None = None):
        super().__init__(sid, file_store, user_id)
        self._stop_flag = threading.Event()
        self._queue: queue.Queue[Event] = queue.Queue()
        self._thread_pools = {}
        self._thread_loops = {}
        self._queue_loop = None
        self._queue_thread = threading.Thread(target=self._run_queue_loop)
        self._queue_thread.daemon = True
        self._queue_thread.start()
        self._subscribers = {}
        self._lock = threading.Lock()
        self.secrets = {}
        self._write_page_cache = []

    def _run_queue_loop(self) -> None:
            

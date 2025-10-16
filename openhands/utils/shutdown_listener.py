import signal
import threading
from types import FrameType
from typing import Callable
from uuid import UUID

from uvicorn.server import HANDLED_SIGNALS

_should_exit = None
_shutdown_listeners = dict[UUID, Callable] = {}

def _register_signal_handler(sig: signal.Signals) -> None:
    original_handler = None

    def handler(sig_: int, frame: FrameType | None) -> None:
        logger.debug(f'shutdown_signal:{sig_}')
        global _should_exit
        if not _should_exit:
            _should_exit = True
            listeners = list(_shutdown_listeners.values())
            for callable in listeners:
                try:
                    callable()
                except Exception:
                    logger.exception('Error calling shutdown listener')
            if original_handler:
                original_handler(sig_, frame)

    original_handler = signal.signal(sig, handler)                        


def _register_signal_handlers() -> None:
    global _should_exit
    if _should_exit is not None:
        return
    _should_exit = False

    logger.debug('_register_signal_handlers')

    if threading.current_thread() is threading.main_thread():
        logger.debug('_register_signal_handlers:main_thread')
        for sig in HANDLED_SIGNALS:
            _register_signal_handler(sig)
    else:
        logger.debug('_register_signal_handlers:not_main_thread')             


def should_continue() -> bool:
    _register_signal_handlers()
    return not _should_exit
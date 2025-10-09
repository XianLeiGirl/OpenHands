from sre_parse import State


class AgentController:
    id: str
    agent: Agent
    max_iterations: int
    event_stream: EventStream
    state: State
    confirmation_mode: bool
    agent_to_llm_config: dict[str, LLMConfig]
    agent_config: dict[str, AgentConfig]
    parent: 'AgentController | None'= None
    delegate: 'AgentController | None'= None
    _pending_action_info: tuple[Action, float] | None = None
    _close: bool = False
    _cached_first_usage_message: MessageAction | None = None

    def __init__(
        self,
        agent: Agent,
        event_stream: EventStream,
        conversion_stats: ConversionStats,
        iteration_delta: int,
        budget_per_task_delta: float | None = None,
        agent_to_llm_config: dict[str, LLMConfig] | None = None,
        agent_configs: dict[str, AgentConfig] | None = None,
        sid: str | None = None,
        file_store: FileStore | None = None,
        user_id: str | None = None,
        confirmation_mode: bool = False,
        initial_state: State | None = None,
        is_delegate: bool = False, # DN
        headless_mode: bool = True,
        status_callback: Callable | None = None,
        replay_events: list[Event] | None = None,
        security_analyzer: 'SecurityAnalyzer | None' = None,
        ):
            self.id = sid or event_stream.id
            self.user_id = user_id
            self.file_store = file_store
            self.agent = agent
            self.headless_mode = headless_mode
            self.is_delegate = is_delegate
            self.conversion_stats = conversion_stats

            self.event_stream = event_stream

            if not self.is_delegate:
                self.event_stream.subscribe(
                    EventStreamSubscriber.AGENT_CONTROLLER, self.on_event, self.id
                )
            self.state_tracker = StateTracker(sid, file_store, user_id)

            self.set_initial_state(
                state=initial_state,
                conversation_stats=conversion_stats,
                max_iterations=max_iterations,
                max_budget_per_task=budget_per_task_delta,
                confirmation_mode=confirmation_mode,
            )    

            self.state = self.state_tracker.state

            self.agent_to_llm_config = agent_to_llm_config if agent_to_llm_config else {}
            self.agent_configs = agent_configs if agent_configs else {}
            self._initial_max_iterations = iteration_delta
            self._initial_max_budget_per_task = budget_per_task_delta

            self._stuck_detector = StuckDetector(self.state)
            self.status_callback = status_callback

            self._replay_manager = ReplayManager(replay_events)

            self.confirmation_mode = confirmation_mode

            self.security_analyzer = security_analyzer

            self._add_system_message()


    async def _handle_security_analyzer(self, action: Action) -> None:
        if self.security_analyzer:
            try:
                if (
                    hasattr(action, 'security_risk')
                    and action.security_risk is not None
                ):
                    logger.debug(f'Original security risk for {action}: {action.security_risk}')
                        
                if hasattr(action, 'security_risk'):
                    action.security_risk = await self.security_analyzer.security_risk(action)
                    logger.debug(f'[Security Analyzer: {self.security_analyzer.__class__}] Override security risk for {action}: {action.security_risk}')
            except Exception as e:
                logger.warning(f'failed to analyze security risk for {action}: {e}')
                if hasattr(action, 'security_risk'):
                    action.security_risk = ActionSecurityRisk.UNKNOWN
        else:
            logger.debug(f'No security analyzer configured, setting UNKNOWN risk for action: {action}')   
            if hasattr(action, 'security_risk'):
                action.security_risk = ActionSecurityRisk.UNKNOWN
        

    def _add_system_message(self):
        for event in self.event_stream.search_events(start_id=self.state.start_id):
            if isinstance(event, MessageAction) and event.source == EventSource.USER:
                return

            if isinstance(event, SystemMessageAction):
                return

        system_message = self.agent.get_system_message()
        if system_message and system_message.content:
            preview = (
                system_message.content[:50] + "..."
                if len(system_message.content) > 50 else system_message.content
            )
            logger.debug(f'System message: {preview}')
            self.event_stream.add_event(system_message, EventSource.AGENT) # LOOK

    async def close(self, set_stop_state: bool = True) -> None:
        if set_stop_state:
            await self.set_agent_state_to(AgentState.STOPPED)

        self.state_tracker.close(self.event_stream) # LOOK 为啥要关闭，会单独起进程来监控吗？

        if not self.is_delegate:
            self.event_stream.unsubscribe(EventStreamSubscriber.AGENT_CONTROLLER, self.id) # LOOK

        self._close = True

    def log(self, level: str, message: str, extra: dict | None = None) -> None:
        message = f'[AgentController: {self.id}] {message}'
        if extra is None:
            extra = {}
        extra_merged = {'session_id': self.id, **extra}
        getattr(logger, level)(message, extra=extra_merged, stacklevel=2)    

    
    async def _reaction_to_exception(self, e: Exception) -> None:
        self.state.last_error = f'{type(e).__name__}: {str(e)}'

        if self.status_callback is not None: # LOOK
            runtime_status = RuntimeStatus.ERROR
            if isinstance(e, AuthenticationError): # LOOK
                runtime_status = RuntimeStatus.ERROR_LLM_AUTHENTICATION
                self.state.last_error = runtime_status.value
            elif isinstance(
                e, 
                (
                    ServiceUnavailableError,
                    APIConnectionError,
                    APIError,
                )
            ):
                runtime_status = RuntimeStatus.ERROR_LLM_SERVICE_UNAVAILABLE
                self.state.last_error = runtime_status.value
            elif isinstance(e, InternalServiceError):
                runtime_status = RuntimeStatus.ERROR_LLM_INTERNAL_SERVICE_ERROR
                self.state.last_error = runtime_status.value
            elif isinstance(e, BadRequestError) and 'ExceededBudget' in str(e):
                runtime_status = RuntimeStatus.ERROR_LLM_OUT_OF_CREDITS
                self.state.last_error = runtime_status.value
            elif isinstance(e, ContentPolicyViolationError) or (
                isinstance(e, BadRequestError) and 'ContentPolicyViolation' in str(e)
            ):
                runtime_status = RuntimeStatus.ERROR_LLM_CONTENT_POLICY_VIOLATION
                self.state.last_error = runtime_status.value
            elif isinstance(e, RateLimitError):
                if (
                    hasattr(e, "retry_attempt")
                    and hasattr(e, "max_retries")
                    and e.retry_attempt >= e.max_retries
                ):
                    self.last_error = RuntimeStatus.AGENT_RATE_LIMITED_STOPPED_MESSAGE.value
                    await self.set_agent_state_to(AgentState.ERROR)
                else:
                    await self.set_agent_state_to(AgentState.RATE_LIMITED) # LOOK 为啥RATE_LIMITED还继续？
                return        
            self.status_callback('error', runtime_status, self.state.last_error)    

        await self.set_agent_state_to(AgentState.ERROR)  

    def step(self) -> None:
        asyncio.create_task(self._step_with_exception_handling())

    async def _step_with_exception_handling(self) -> None:
        try:
            await self._step()
        except Exception as e:
            self.log(
                'error',
                f'Error while running the agent (session ID: {self.id}): {e}',
                f'Traceback: {traceback.format_exc()}'
            )    
            reported = RuntimeError(
                f'There was an unexcepted error while running the agent: {e.__class__.__name__}. You can refresh the page or ask the agent to try again.'
            )
            if (
                isinstance(e, Timeout)
                or isinstance(e, APIError)
                or isinstance(e, BadRequestError)
                or isinstance(e, NotFoundError)
                or isinstance(e, InternalServerError)
                or isinstance(e, AuthenticationError)
                or isinstance(e, RateLimitError)
                or isinstance(e, ContentPolicyViolationError)
                or isinstance(e, LLMContextWindowExceedError)
            ):
                reported = e
            else:
                self.log(
                    'warning',
                    f'Unknown exception type while running the agent: {type(e).__name__}'
                )    
            await self._reaction_to_exception(reported)

    def should_step(self, event: Event) -> bool:
        if self.delegate is not None:
            return False


    def run(self):
        pass
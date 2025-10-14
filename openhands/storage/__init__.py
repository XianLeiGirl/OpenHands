from openhands.storage.files import FileStore


# LOOK: 除了LocalFileStore其他不懂
def get_file_store(
    file_store_type: str,
    file_store_path: str | None = None,
    file_store_web_hook_url: str | None = None,
    file_store_web_hook_headers: dict | None = None,
    file_store_web_hook_batch: bool = False,
) -> FileStore:
    store: FileStore
    if file_store_type == 'local':
        if file_store_path is None:
            raise ValueError('file_store_path is required for local file store')
        store = LocalFileStore(file_store_path)
    elif file_store_type == 's3':
        store = S3FileStore(file_store_path)
    elif file_store_type == 'google_cloud':
        store = GoogleCloudFileStore(file_store_path)
    else:
        store = InMemoryFileStore()
    if file_store_web_hook_url:
        if file_store_web_hook_headers is None:
            file_store_web_hook_headers = {}
            if os.getenv('SESSION_API_KEY'):
                file_store_web_hook_headers['X-SESSION-API-KEY'] = os.getenv('SESSION_API_KEY')

        client = httpx.Client(headers=file_store_web_hook_headers or {})

        if file_store_web_hook_batch:
            store = BatchedWebHookFileStore(
                store,
                file_store_web_hook_url,
                client,
            )
        else:
            store = WebHookFileStore(
                store,
                file_store_web_hook_url,
                client,
            )
    return store


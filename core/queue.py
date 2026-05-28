import asyncio
import logging
from urllib.parse import urlparse

from cache.store import CacheEntry, cookie_store
from core.browser import browser_manager
from core.solver import solve
from core.validator import check_cookie_validity

logger = logging.getLogger(__name__)


class SolveJob:
    def __init__(self, url: str) -> None:
        self.url = url
        self.future: asyncio.Future = asyncio.get_event_loop().create_future()


class SolverQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[SolveJob] = asyncio.Queue()
        self._domain_locks: dict[str, asyncio.Lock] = {}
        self._worker_task: asyncio.Task | None = None

    def _get_domain(self, url: str) -> str:
        return urlparse(url).netloc

    def _get_lock(self, domain: str) -> asyncio.Lock:
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()
        return self._domain_locks[domain]

    async def submit(self, url: str) -> tuple[str, float]:
        """Submit a solve job and wait for result."""
        logger.debug("Enqueuing solve job for URL: %s", url)
        job = SolveJob(url)
        await self._queue.put(job)
        return await job.future

    async def _process(self, job: SolveJob) -> None:
        domain = self._get_domain(job.url)
        lock = self._get_lock(domain)

        async with lock:
            logger.info("Processing job for domain: %s", domain)
            try:
                cached = cookie_store.get(domain)

                if cached:
                    logger.debug("Cache hit for domain %s", domain)
                    tab = await browser_manager.new_tab()
                    try:
                        valid = await check_cookie_validity(tab, job.url)
                    finally:
                        await browser_manager.close_tab(tab)

                    if valid:
                        job.future.set_result((cached.cookie_string, 0.0))
                        return

                    cookie_store.invalidate(domain)
                    logger.debug("Invalidated cache for domain %s", domain)

                # Solve
                logger.debug("Opening tab to solve: %s", job.url)
                tab = await browser_manager.new_tab()
                try:
                    cookie_string, solve_seconds = await solve(tab, job.url)
                finally:
                    await browser_manager.close_tab(tab)

                cookie_store.set(domain, CacheEntry(
                    cookie_string=cookie_string,
                    domain=domain,
                ))

                job.future.set_result((cookie_string, solve_seconds))

            except Exception as e:
                logger.exception("Error processing job for %s", job.url)
                job.future.set_exception(e)

    async def _worker(self) -> None:
        while True:
            job = await self._queue.get()
            try:
                await self._process(job)
            except Exception as e:
                logger.error(f"Worker error: {e}")
            finally:
                self._queue.task_done()

    def start_worker(self) -> None:
        self._worker_task = asyncio.create_task(self._worker())

    async def stop_worker(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass


solver_queue = SolverQueue()
import asyncio
import time
import logging
from urllib.parse import urlparse

from pydoll.protocol.network.types import Cookie


logger = logging.getLogger(__name__)


async def wait_for_turnstile(tab, timeout: int = 60) -> bool:
    """Wait until Turnstile challenge is resolved in DOM."""
    start = time.time()

    while time.time() - start < timeout:
        try:
            token = await tab.execute_script("""
                const el = document.querySelector('[name="cf-turnstile-response"]');
                return el ? el.value : null;
            """)
            if token:
                return True

            spinner_visible = await tab.execute_script("""
                const frames = document.querySelectorAll('iframe');
                for (const f of frames) {
                    if (f.src && f.src.includes('challenges.cloudflare.com')) {
                        return true;
                    }
                }
                return false;
            """)
            if not spinner_visible:
                return True

        except Exception:
            pass

        await asyncio.sleep(1)

    return False


async def wait_for_turnstile_cookie(tab, timeout: int = 60) -> bool:
    """Wait until _as_turnstile cookie appears in the browser cookie jar."""
    start = time.time()

    while time.time() - start < timeout:
        try:
            cookies: list[Cookie] = await tab.get_cookies()
            for cookie in cookies:
                if cookie["name"] == "_as_turnstile":
                    return True
        except Exception:
            pass

        await asyncio.sleep(1)

    return False


def build_cookie_string(cookies: list[Cookie]) -> str:
    """Convert cookie list to a single cookie header string."""
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


async def solve(tab, url: str, timeout: int = 60) -> tuple[str, float]:
    """
    Solve Turnstile for the given URL.
    Returns (cookie_string, solve_seconds).
    """
    start = time.time()

    parsed = urlparse(url)
    logger.debug("Solving URL: %s (scheme=%s, host=%s)", url, parsed.scheme, parsed.hostname)
    if parsed.scheme == 'https':
        logger.debug("Target uses HTTPS: %s", url)

    await tab.enable_auto_solve_cloudflare_captcha()
    logger.debug("Auto-solve enabled on tab")
    await tab.go_to(url)
    logger.debug("Navigation command sent to tab: %s", url)

    await wait_for_turnstile(tab, timeout=timeout)
    await tab.disable_auto_solve_cloudflare_captcha()
    logger.debug("Auto-solve disabled on tab")

    await wait_for_turnstile_cookie(tab, timeout=timeout)

    cookies: list[Cookie] = await tab.get_cookies()
    cookie_string = build_cookie_string(cookies)
    solve_seconds = round(time.time() - start, 2)
    logger.info("Solved %s in %.2fs, cookies=%d", url, solve_seconds, len(cookies))

    return cookie_string, solve_seconds
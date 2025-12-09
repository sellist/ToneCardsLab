import time
from tcl_api.config import get_logger

logger = get_logger("middleware.logging")


class LoggingMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        # Extract request info from scope
        method = scope["method"]
        path = scope["path"]
        client_host = scope.get("client", [None])[0] if scope.get("client") else "unknown"
        query_string = scope.get("query_string", b"").decode()
        headers = dict(scope.get("headers", []))

        logger.info(f"Incoming request: {method} {path} from {client_host}")

        if query_string:
            logger.debug(f"Query string: {query_string}")

        logger.debug(f"Request headers: {headers}")

        # Custom send wrapper to capture response info
        response_info = {"status_code": None}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_info["status_code"] = message["status"]
                # Add process time header
                process_time = time.time() - start_time
                headers = list(message.get("headers", []))
                headers.append([b"x-process-time", str(process_time).encode()])
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)

        process_time = time.time() - start_time
        logger.info(
            f"Response: {method} {path} -> {response_info['status_code']} ({process_time:.4f}s)"
        )

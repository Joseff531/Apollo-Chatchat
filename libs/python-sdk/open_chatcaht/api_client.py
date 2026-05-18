import contextlib
import inspect
import json
import logging
import os
from typing import *

from open_chatcaht._constants import API_BASE_URI
from open_chatcaht.utils import set_httpx_config, get_httpx_client, get_variable, get_function_default_params, \
    merge_dicts
from functools import wraps
from typing import Type, get_type_hints

import httpx
import requests
from pydantic import BaseModel

set_httpx_config()

CHATCHAT_API_BASE = get_variable(os.getenv('CHATCHAT_API_BASE'), 'http://127.0.0.1:8000')
CHATCHAT_CLIENT_TIME_OUT = get_variable(os.getenv('CHATCHAT_CLIENT_TIME_OUT'), 60)
CHATCHAT_CLIENT_DEFAULT_RETRY_COUNT = get_variable(os.getenv('CHATCHAT_CLIENT_DEFAULT_RETRY'), 3)
CHATCHAT_CLIENT_DEFAULT_RETRY_INTERVAL = get_variable(os.getenv('CHATCHAT_CLIENT_DEFAULT_RETRY_INTERVAL'), 60)


class ApiClient:
    """
    Wrapper for api.py calls (synchronous mode) that simplifies the way the API is invoked
    """

    def __init__(
            self,
            base_url: str = API_BASE_URI,
            timeout: float = 60,
            use_async: bool = False,
            use_proxy: bool = False,
            proxies=None,
            log_level: int = logging.INFO,
            retry: int = 3,
            retry_interval: int = 1,
    ):
        if proxies is None:
            proxies = {}
        self.base_url = get_variable(base_url, CHATCHAT_API_BASE)
        self.timeout = get_variable(timeout, CHATCHAT_CLIENT_TIME_OUT)
        self._use_async = use_async
        self.use_proxy = use_proxy
        self.default_retry_count = get_variable(retry, CHATCHAT_CLIENT_DEFAULT_RETRY_COUNT)
        self.default_retry_interval = get_variable(retry_interval, CHATCHAT_CLIENT_DEFAULT_RETRY_INTERVAL)
        self.proxies = proxies
        self._client = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

    @property
    def client(self):
        if self._client is None or self._client.is_closed:
            self._client = get_httpx_client(
                base_url=self.base_url, use_async=self._use_async, timeout=self.timeout
            )
        return self._client

    def _get(
            self,
            url: str,
            params: Union[Dict, List[Tuple], bytes] = None,
            retry: int = 3,
            stream: bool = False,
            **kwargs: Any,
    ) -> Union[httpx.Response, Iterator[httpx.Response], None]:
        while retry > 0:
            try:
                if stream:
                    return self.client.stream("GET", url, params=params, **kwargs)
                else:
                    return self.client.get(url, params=params, **kwargs)
            except Exception as e:
                msg = f"error when get {url}: {e}"
                self.logger.error(f"{e.__class__.__name__}: {msg}")
                retry -= 1

    def _post(
            self,
            url: str,
            data: Dict = None,
            json: Dict = None,
            retry: int = 3,
            stream: bool = False,
            **kwargs: Any,
    ) -> Union[httpx.Response, Iterator[httpx.Response], None]:
        while retry > 0:
            try:
                # print(kwargs)
                if stream:

                    return self.client.stream(
                        "POST", url, data=data, json=json, **kwargs
                    )
                else:
                    self.logger.debug(f"post {url} with data: {data}")
                    return self.client.post(url, data=data, json=json, **kwargs)
            except Exception as e:
                msg = f"error when post {url}: {e}"
                self.logger.error(f"{e.__class__.__name__}: {msg}")
                retry -= 1

    def _delete(
            self,
            url: str,
            data: Dict = None,
            json: Dict = None,
            retry: int = 3,
            stream: bool = False,
            **kwargs: Any,
    ) -> Union[httpx.Response, Iterator[httpx.Response], None]:
        while retry > 0:
            try:
                if stream:
                    return self.client.stream(
                        "DELETE", url, data=data, json=json, **kwargs
                    )
                else:
                    return self.client.delete(url, data=data, json=json, **kwargs)
            except Exception as e:
                msg = f"error when delete {url}: {e}"
                self.logger.error(f"{e.__class__.__name__}: {msg}")
                retry -= 1

    def _httpx_stream2generator(
            self,
            response: contextlib._GeneratorContextManager,
            as_json: bool = False,
    ):
        """
        Convert the GeneratorContextManager returned by httpx.stream into a regular generator
        """

        async def ret_async(response, as_json):
            try:
                async with response as r:
                    chunk_cache = ""
                    async for chunk in r.aiter_text(None):
                        if not chunk:  # fastchat api yield empty bytes on start and end
                            continue
                        if as_json:
                            try:
                                if chunk.startswith("data: "):
                                    data = json.loads(chunk_cache + chunk[6:-2])
                                elif chunk.startswith(":"):  # skip sse comment line
                                    continue
                                else:
                                    data = json.loads(chunk_cache + chunk)

                                chunk_cache = ""
                                yield data
                            except Exception as e:
                                msg = f"Interface returned a JSON error: '{chunk}'. Error message: {e}."
                                self.logger.error(f"{e.__class__.__name__}: {msg}")

                                if chunk.startswith("data: "):
                                    chunk_cache += chunk[6:-2]
                                elif chunk.startswith(":"):  # skip sse comment line
                                    continue
                                else:
                                    chunk_cache += chunk
                                continue
                        else:
                            # print(chunk, end="", flush=True)
                            yield chunk
            except httpx.ConnectError as e:
                msg = f"Could not connect to the API server. Please make sure 'api.py' is running. ({e})"
                self.logger.error(msg)
                yield {"code": 500, "msg": msg}
            except httpx.ReadTimeout as e:
                msg = f"API communication timed out. Please make sure FastChat and the API service are started (see Wiki '5. Start the API Service or Web UI'). ({e})"
                self.logger.error(msg)
                yield {"code": 500, "msg": msg}
            except Exception as e:
                msg = f"Error during API communication: {e}"
                self.logger.error(f"{e.__class__.__name__}: {msg}")
                yield {"code": 500, "msg": msg}

        def ret_sync(response, as_json):
            try:
                with response as r:
                    chunk_cache = ""
                    for chunk in r.iter_text(None):
                        if not chunk:  # fastchat api yield empty bytes on start and end
                            continue
                        if as_json:
                            try:
                                if chunk.startswith("data: "):
                                    data = json.loads(chunk_cache + chunk[6:-2])
                                elif chunk.startswith(":"):  # skip sse comment line
                                    continue
                                else:
                                    data = json.loads(chunk_cache + chunk)

                                chunk_cache = ""
                                yield data
                            except Exception as e:
                                msg = f"Interface returned a JSON error: '{chunk}'. Error message: {e}."
                                self.logger.error(f"{e.__class__.__name__}: {msg}")

                                if chunk.startswith("data: "):
                                    chunk_cache += chunk[6:-2]
                                elif chunk.startswith(":"):  # skip sse comment line
                                    continue
                                else:
                                    chunk_cache += chunk
                                continue
                        else:
                            # print(chunk, end="", flush=True)
                            yield chunk
            except httpx.ConnectError as e:
                msg = f"Could not connect to the API server. Please make sure 'api.py' is running. ({e})"
                self.logger.error(msg)
                yield {"code": 500, "msg": msg}
            except httpx.ReadTimeout as e:
                msg = f"API communication timed out. Please make sure FastChat and the API service are started (see Wiki '5. Start the API Service or Web UI'). ({e})"
                self.logger.error(msg)
                yield {"code": 500, "msg": msg}
            except Exception as e:
                msg = f"Error during API communication: {e}"
                self.logger.error(f"{e.__class__.__name__}: {msg}")
                yield {"code": 500, "msg": msg}

        if self._use_async:
            return ret_async(response, as_json)
        else:
            return ret_sync(response, as_json)

    def _get_response_value(
            self,
            response: httpx.Response,
            as_json: bool = False,
            value_func: Callable = None,
    ):
        """
        Transform the response returned from a sync or async request
        `as_json`: return JSON
        `value_func`: user can customize the return value; this function accepts the response or JSON
        """

        def to_json(r):
            try:
                return r.json()
            except Exception as e:
                msg = "API did not return valid JSON." + str(e)
                self.logger.error(f"{e.__class__.__name__}: {msg}")
                return {"code": 500, "msg": msg, "data": None}

        if value_func is None:
            value_func = lambda r: r

        async def ret_async(response):
            if as_json:
                return value_func(to_json(await response))
            else:
                return value_func(await response)

        if self._use_async:
            return ret_async(response)
        else:
            if as_json:
                return value_func(to_json(response))
            else:
                return value_func(response)


def get_request_method(api_client_obj: ApiClient, method):
    if method is httpx.post:
        return getattr(api_client_obj, "_post")
    elif method is httpx.get:
        return getattr(api_client_obj, "_get")
    # elif method is httpx.put:
    #     return api_client_obj.put
    elif method is httpx.delete:
        return getattr(api_client_obj, "_delete")


def http_request(method):
    def decorator(url, base_url='', headers=None, body_model: Type[BaseModel] = None, **options):
        headers = headers or {}

        def wrapper(func):
            @wraps(func)
            def inner(*args, **kwargs):
                try:
                    default_param: dict = get_function_default_params(func)

                    api_client_obj: ApiClient = args[0] if len(args) > 0 and isinstance(args[0], ApiClient) else None
                    return_type = get_type_hints(func).get('return')
                    full_url = base_url + url
                    param = merge_dicts(kwargs, default_param)
                    if body_model is not None:
                        param = body_model(**kwargs).dict()
                    # Send the HTTP request
                    response = None
                    if api_client_obj is not None:
                        _method = get_request_method(api_client_obj, method)
                        response = _method(full_url, headers=headers, json=param)
                    else:
                        response = method(full_url, headers=headers, json=param)
                        response.raise_for_status()
                    return response.json()
                except requests.exceptions.HTTPError as http_err:
                    print(f"HTTP error occurred: {http_err}")
                except Exception as err:
                    print(f"An error occurred: {err}")

            return inner

        return wrapper

    return decorator


post = http_request(httpx.post)
get = http_request(httpx.get)
delete = http_request(httpx.delete)
put = http_request(httpx.put)

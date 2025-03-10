import asyncio
import re

from dataclasses import dataclass
from enum import Enum

from pytelnetdevice import TelnetDevice


@dataclass
class SingleLineResponse:
    prefix: str
    path: str


@dataclass
class PropertyResponse(SingleLineResponse):
    value: str

    def __str__(self):
        return self.value


@dataclass
class ErrorResponse(SingleLineResponse):
    code: int
    message: str

    def __str__(self):
        return self.message


@dataclass
class NodeResponse(SingleLineResponse):
    pass


@dataclass
class MethodResponse(SingleLineResponse):
    name: str

    def __str__(self):
        return self.name


type MultiLineResponse = list[SingleLineResponse]
type Response = SingleLineResponse | MultiLineResponse


class ResponseType(Enum):
    Node = 1
    Property = 2
    Error = 3
    Method = 4


def get_response_type(response: str) -> ResponseType:
    if response[1] == "E":
        return ResponseType.Error
    elif response[0] == "p":
        return ResponseType.Property
    elif response[0] == "n":
        return ResponseType.Node
    elif response[0] == "m":
        return ResponseType.Method

    raise ValueError(f"Unknown response type: {response}")


def parse_single_line_response(response: str) -> SingleLineResponse:
    match get_response_type(response):
        case ResponseType.Error:
            matches = re.search(r"^(.E) (.*) %(E[0-9]+):(.*)$", response)
            return ErrorResponse(matches.group(1), matches.group(2), matches.group(3), matches.group(4))
        case ResponseType.Property:
            matches = re.fullmatch(r"^p(.*) (.*)=(.*)$", response)
            return PropertyResponse(f"p{matches.group(1)}", matches.group(2), matches.group(3))
        case ResponseType.Node:
            matches = re.fullmatch(r"^n(.*) (.*)$", response)
            return NodeResponse(f"n{matches.group(1)}", matches.group(2))
        case ResponseType.Method:
            matches = re.fullmatch(r"^m(.*) (.*):(.*)$", response)
            return MethodResponse(f"m{matches.group(1)}", matches.group(2), matches.group(3))

    raise ValueError(f"Unable to parse response: {response}")


def parse_multiline_response(lines: list[str]) -> MultiLineResponse:
    return [parse_single_line_response(response) for response in lines]


def parse_response(response: str) -> Response:
    lines = response.split("\r\n")

    # Determine if we're dealing with a single line response or multiple
    if len(lines) == 3:
        return parse_single_line_response(lines[1])
    else:
        return parse_multiline_response(lines[1:-1])


def is_encoder_discovery_node(node: Response) -> bool:
    return isinstance(node, NodeResponse) and "TX" in node.path


def is_decoder_discovery_node(node: Response) -> bool:
    return isinstance(node, NodeResponse) and "RX" in node.path


class LW3(TelnetDevice):
    def __init__(self, host: str, port: int, timeout: int = 5):
        super().__init__(host, port, timeout)

    async def _read_and_parse_response(self) -> Response:
        # All commands are wrapped with a signature, so read until the end delimiter
        response = await self._read_until("}")

        if response is None:
            raise EOFError("Reached EOF while reading, connection probably lost")

        result = parse_response(response.strip())

        if isinstance(result, ErrorResponse):
            raise ValueError(result)

        return result

    async def _run_get(self, path: str) -> Response:
        async with self._semaphore:
            self._writer.write(f"0000#GET {path}\r\n".encode())
            await self._writer.drain()

            return await self._read_and_parse_response()

    async def _run_set(self, path: str, value: str) -> Response:
        async with self._semaphore:
            self._writer.write(f"0000#SET {path}={value}\r\n".encode())
            await self._writer.drain()

            return await self._read_and_parse_response()

    async def _run_get_all(self, path: str) -> Response:
        async with self._semaphore:
            self._writer.write(f"0000#GETALL {path}\r\n".encode())
            await self._writer.drain()

            return await self._read_and_parse_response()

    async def _run_call(self, path: str, method: str) -> Response:
        async with self._semaphore:
            self._writer.write(f"0000#CALL {path}:{method}\r\n".encode())
            await self._writer.drain()

            return await self._read_and_parse_response()

    async def get_property(self, path: str) -> PropertyResponse:
        response = await asyncio.wait_for(self._run_get(path), self._timeout)

        if not isinstance(response, PropertyResponse):
            raise ValueError(f"Requested path {path} does not return a property")

        return response

    async def set_property(self, path: str, value: str) -> PropertyResponse:
        response = await asyncio.wait_for(self._run_set(path, value), self._timeout)

        if not isinstance(response, PropertyResponse):
            raise ValueError(f"Requested path {path} does not return a property")

        return response

    async def get_all(self, path: str) -> Response:
        return await asyncio.wait_for(self._run_get_all(path), self._timeout)

    async def call(self, path: str, method: str) -> MethodResponse:
        response = await asyncio.wait_for(self._run_call(path, method), self._timeout)

        if not isinstance(response, MethodResponse):
            raise ValueError(f"Called method {path}:{method} does not return a method response")

        return response

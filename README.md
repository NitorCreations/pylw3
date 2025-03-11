# pylw3

[![Tests](https://github.com/NitorCreations/pylw3/actions/workflows/unittest.yaml/badge.svg)](https://github.com/NitorCreations/pylw3/actions/workflows/unittest.yaml)
[![Linting](https://github.com/NitorCreations/pylw3/actions/workflows/ruff.yaml/badge.svg)](https://github.com/NitorCreations/pylw3/actions/workflows/ruff.yaml)

Lightware LW3 protocol library for controlling Lightware encoders and decoders.

This library uses our [pytelnetdevice](https://github.com/NitorCreations/pytelnetdevice) library under the hood.

## Usage

This is just a basic example, explore the library to and the documentation for the LW3 protocol for your specific 
device to learn more.

```python
import asyncio

from pylw3 import LW3


async def main():
    # Connect to a VINX decoder and print the current input
    decoder_device = LW3("10.211.0.23", 6107)
    async with decoder_device.connection():
        video_channel_id = await decoder_device.get_property("/SYS/MB/PHY.VideoChannelId")
        print(video_channel_id)

    # Connect to a VINX encoder and print whether signal is present
    encoder_device = LW3("10.211.0.86", 6107)
    async with encoder_device.connection():
        signal_present = await encoder_device.get_property("/MEDIA/VIDEO/I1.SignalPresent")
        print(signal_present)


asyncio.run(main())
```

This will output something like:

```
9
0
```

## License

GNU GENERAL PUBLIC LICENSE version 3

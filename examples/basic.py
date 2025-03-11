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

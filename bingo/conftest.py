import pytest
from channels.layers import channel_layers


@pytest.fixture(autouse=True)
async def fresh_channel_layer():
    """Give each test its own channel layer and clear it afterwards.

    The layer caches connections per event loop and pytest-asyncio uses a new loop per test, so
    sharing one layer (and leftover groups in Redis) between tests makes runs order-dependent.
    """
    channel_layers.backends.clear()
    yield
    layer = channel_layers.backends.get("default")
    if layer is not None and hasattr(layer, "flush"):
        await layer.flush()
    channel_layers.backends.clear()

import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

subscribers: list[asyncio.Queue] = []


async def event_generator(queue: asyncio.Queue):
    try:
        while True:
            data = await queue.get()
            yield f"data: {data}\n\n"
    except asyncio.CancelledError:
        pass


@router.get("/stream")
async def orders_stream():
    queue: asyncio.Queue = asyncio.Queue()
    subscribers.append(queue)

    async def streamer():
        try:
            async for chunk in event_generator(queue):
                yield chunk
        finally:
            if queue in subscribers:
                subscribers.remove(queue)

    return StreamingResponse(streamer(), media_type="text/event-stream")


def broadcast_event(message: str):
    for queue in list(subscribers):
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            pass
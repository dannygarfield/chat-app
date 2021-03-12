from aiohttp import web
from string import Template

# curl -i http://0.0.0.0:8080/ --> send an empty GET request
# curl -i :8080 -d sender=jordan -d recipient=danny -d contents="hello, danny" --> adding -d makes it a POST request

messages = []
clients = set()

# an async function is a coroutine. You must 'await' the function.
async def showChats(request):
    print(request)
    print(request.headers)
    print(request.text)
    print(request.content)

    rows = "".join(
            f"<tr><td>{m['sender']}</td><td>{m['recipient']}</td><td>{m['contents']}</td></tr>" for m in messages
        )

    with open('index.template.html') as f:
        template = Template(f.read())

    html = template.substitute({'rows': rows})

    return web.Response(text=html, content_type="text/html")


async def addMessage(request):
    form = await request.post()
    print(form)
    messages.append(
        {
            "sender": form["sender"],
            "recipient": form["recipient"],
            "contents": form["contents"],
        }
    )
    for client in clients: # WHAT'S GOING ON HERE? How does sequencing work of adding/discarding ws from clients?

        await client.send_str("new chat") # What is the connection between this and ws in the client?
    return web.Response(
        status=303,
        headers={
            "Location": "/",
        },
    )

async def reloader(request):
    # coroutine: get GET from client, send 101 to client, including some info to establish the connection
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    await ws.send_str("hello from the server")

    clients.add(ws) # WHAT IS GOING ON HERE ?
    try:
        # this is weird, but we need to wait to kick off this message read loop
        # in order for this implementation of websockets to work.
        async for msg in ws:  # ws is iterable. this loop will continue forever until this iterator ends (when the websocket closes)
            pass
    finally:
        clients.discard(ws)

    return ws


app = web.Application()
app.add_routes(
    [
        # when we receive a GET request at the path "/", execute showChats
        web.get("/", showChats),
        web.post("/", addMessage),
        web.get("/reloader", reloader)
    ]
)
web.run_app(app)

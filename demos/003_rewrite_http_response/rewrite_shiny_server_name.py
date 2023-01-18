from mitmproxy import ctx, http

class RewriteShinyServerName:

    def __init__(self):
        pass

    def response(self, flow: http.HTTPFlow) -> None:
        if flow.request.path == "/" and flow.response and flow.response.content:
            flow.response.content = flow.response.content.replace(
                b"Shiny Server",
                b"dskard's Server"
            )

addons = [
    RewriteShinyServerName()
]

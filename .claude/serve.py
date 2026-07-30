"""Dev-only preview server. Nothing on the live site depends on this file.

`python -m http.server` would do, except for two things:

  * it ignores $PORT, which the preview harness uses to hand out a free port
    so two sessions can run at once;
  * binding is fiddly on Windows. `--bind 127.0.0.1` refuses
    http://localhost:PORT, because Windows resolves localhost to ::1 first.
    Binding AF_INET6 alone then breaks http://127.0.0.1:PORT instead. The fix
    is one socket with IPV6_V6ONLY cleared, which accepts both families.

Run it directly if you are not using the preview harness:

    python .claude/serve.py            # port 8000
    PORT=9000 python .claude/serve.py  # or pick one
"""

import http.server
import os
import socket


class DualStackServer(http.server.ThreadingHTTPServer):
    address_family = socket.AF_INET6
    allow_reuse_address = True

    def server_bind(self):
        # Accept IPv4 and IPv6 on the same socket, so localhost, 127.0.0.1 and
        # ::1 all reach the server whichever way the name resolves.
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        return super().server_bind()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    with DualStackServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
        print(f"Serving {os.getcwd()} on http://localhost:{port}/", flush=True)
        httpd.serve_forever()

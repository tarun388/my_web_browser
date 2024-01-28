import os.path
import socket
import ssl
import tkinter

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 10


def lex(body):
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return text


def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        # Line breaks
        if c == "\n":
            cursor_x = HSTEP
            # Increase y, i.e. move to next line
            cursor_y += 1.2 * VSTEP
        else:
            cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list


def load(url):
    if url.scheme in ["http", "https"]:
        body = url.request()
        # show(body)
    elif url.scheme == "file":
        body = url.read_dir_file()
        print(body)


class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file"]
        if '/' not in url:
            url = url + "/"

        if self.scheme in ["http", "https"]:
            if self.scheme == "http":
                self.port = 80
            elif self.scheme == "https":
                self.port = 443
            self.host, url = url.split("/", 1)
            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)
        self.path = "/" + url

    def request(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        s.connect((self.host, self.port))
        s.send(("GET {} HTTP/1.0\r\n".format(self.path) +
                "Host: {}\r\n".format(self.host) +
                "Connection: close\r\n" +
                "User-Agent: my_web_browser/1.0\r\n" +  # Dummy value fo now
                "\r\n")
               .encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        body = response.read()
        s.close()
        return body

    def read_dir_file(self):
        assert os.path.exists(self.path)
        body = ""
        if os.path.isdir(self.path):
            body = "\n".join(os.listdir(self.path))
        elif os.path.isfile(self.path):
            body = open(self.path).read()
        return body


class Browser:
    def __init__(self):
        self.display_list = None
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()
        self.scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.mouseWheel)

    def load(self, url):
        body = url.request()
        text = lex(body)
        self.display_list = layout(text)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT:
                continue
            if y + VSTEP < self.scroll:
                continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def scrollup(self, e):
        if self.scroll > 0:
            self.scroll -= SCROLL_STEP
            self.draw()

    def mouseWheel(self, e):
        if self.scroll > 0 or e.delta < 0:
            self.scroll -= e.delta * SCROLL_STEP
            self.draw()


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        # By default root dir
        Browser().load(URL("file://"))
    else:
        # load(URL(sys.argv[1]))
        Browser().load(URL(sys.argv[1]))
    tkinter.mainloop()

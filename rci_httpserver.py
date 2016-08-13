import BaseHTTPServer as basehttp
import cgi
import rci_nonblocking as rci

class RCIRequestHandler(basehttp.BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            ctype,params = cgi.parse_header(self.headers.getheader("content-type"))
        except:
            self.send_error(415)
            return
        if ctype != 'text/xml':
            self.send_error(415)
            return
        content_len = int(self.headers.getheader('content-length', 0))
        post_body = self.rfile.read(content_len)
        resp = rci.process_request('<rci_request>' + post_body + '</rci_request>')
        self.send_response(200)
        self.send_header("content-type","text/xml")
        self.end_headers()
        self.wfile.write(resp)

if __name__ == "__main__":
    addr = ("",8080)
    httpd = basehttp.HTTPServer(addr,RCIRequestHandler)
    httpd.serve_forever()


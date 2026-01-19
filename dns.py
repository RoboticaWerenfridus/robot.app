import socketserver
from dnslib import DNSRecord, QTYPE, RR, A, DNSHeader

DOMAIN = "robot.app."
IP = "127.0.0.1"
PORT = 53
LISTEN_ADDR = "0.0.0.0"

class DNSHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0]
        socket = self.request[1]
        request = DNSRecord.parse(data)
        reply = DNSRecord(DNSHeader(id=request.header.id, qr=1, aa=1, ra=0), q=request.q)

        qname = str(request.q.qname)
        qtype = QTYPE[request.q.qtype]

        if qname.lower() == DOMAIN.lower() and qtype in ("A", "ANY"):
            reply.add_answer(RR(rname=qname, rtype=QTYPE.A, rclass=1, ttl=60, rdata=A(IP)))
        else:
            print(f"wrong domain")

        socket.sendto(reply.pack(), self.client_address)

if __name__ == "__main__":
    print(f"Starting DNS server for {DOMAIN} to {IP} on {LISTEN_ADDR}:{PORT}")
    with socketserver.UDPServer((LISTEN_ADDR, PORT), DNSHandler) as server:
        server.serve_forever()

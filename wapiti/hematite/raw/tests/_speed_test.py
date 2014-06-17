
import StringIO

headers = '''Location: http://www.google.com/
Content-Type: text/html; charset=UTF-8
Date: Sat, 01 Mar 2014 23:10:17 GMT
Expires: Mon, 31 Mar 2014 23:10:17 GMT
Cache-Control: public, max-age=2592000
Server: gws
Content-Length: 219
X-XSS-Protection: 1; mode=block
X-Frame-Options: SAMEORIGIN
Alternate-Protocol: 80:quic
Connection: close
''' * 1024

resp = '''HTTP/1.1 301 Moved Permanently
%s
<HTML><HEAD><meta http-equiv="content-type" content="text/html;charset=utf-8">
<TITLE>301 Moved</TITLE></HEAD><BODY>
<H1>301 Moved</H1>
The document has moved
<A HREF="http://www.google.com/">here</A>.
</BODY></HTML>
''' % headers


fake = StringIO.StringIO(resp)
fake.recv = fake.read


def linear_setup():
    response._advance_until_lf = response.core._advance_until_lf
    response._advance_until_lflf = response.core._advance_until_lflf


def _test():
    fake.seek(0)
    return response.Response.parsefromsocket(fake)


if __name__ == '__main__':
    import argparse
    import timeit
    a = argparse.ArgumentParser()
    a.add_argument('-l', action='store_true',
                   help='linear time test')

    args = a.parse_args()
    setup_code = 'from __main__ import fake, linear_setup, test'
    if args.l:
        print 'linear test'
        setup_code += '; linear_setup()'

    print timeit.timeit('_test()', setup=setup_code, number=1)

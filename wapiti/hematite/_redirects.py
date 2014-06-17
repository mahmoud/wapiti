# -*- coding: utf-8 -*-

# Some pseudocode and sketches toward following redirects

FOLLOWABLE_REDIRECTS = [301, 302, 303, 307, 308]

"""
1. Check redirect limit, potentially raising exception
2. Flush socket
3. Resolve new URL (can be relative or missing scheme, resolve
   according to originating request/response)
4. Copy request, setting new URL
5. If 301, 302, 303, method is automatically switched to GET (or HEAD)
   (not for 307 or 308 though, those either return or raise)
6. Cookies will need to be re-evaluated for expiration + the new URL
7. Similarly, clear authorization headers if the authority changes
8. Submit new request

"""

import gevent
from gevent import monkey
monkey.patch_all()

from wapiti import WapitiClient

client = WapitiClient('you@example.com')

cats = ('Africa', 'FA-Class_articles', 'GA-Class_articles', 'Physics')
tasks = [gevent.spawn(client.get_category_recursive, x, 1000) for x in cats]
gevent.wait(tasks)

print tasks[0].value[0]

import pdb;pdb.set_trace()

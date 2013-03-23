from wapiti import WapitiClient

client = WapitiClient('you@example.com')

res = []
cats = ('Africa', 'FA-Class_articles', 'GA-Class_articles', 'Physics')
for cat in cats:
    res.append(client.get_category_recursive(cat, 1000))

print res[0][0]

import pdb;pdb.set_trace()

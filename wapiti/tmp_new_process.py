# -*- coding: utf-8 -*-
"""

Stuff is currently overly abstracted, need to be honest and
convert the library to be more obviously web request-oriented.

process:

* prepare parameters
* create API Request
* execute
* post-process results
* extract results
* store results
* loop

"""

from operations.rand import GetRandomArticles
from operations.links import GetLinks
from operations.revisions import (GetRevisionInfos,
                                  GetCurrentContent,
                                  GetPageRevisionInfos)

from hematite.async import join as hematite_join


def process(ops):
    i = 0
    to_proc = set(ops)
    while to_proc:
        i += 1
        resps = []
        for op in list(to_proc):
            resps.extend(op.incomplete_resps.values())
        print resps
        hematite_join(resps, timeout=5.0)
        for op in list(to_proc):
            op.process_responses()
            if not op.remaining:
                import pdb;pdb.set_trace()
                to_proc.remove(op)
        if i > 7:
            import pdb;pdb.set_trace()


def get_links():
    gl_physics = GetLinks('Physics')
    gl_africa = GetLinks('Africa')

    process([gl_physics, gl_africa])
    print len(gl_physics.results), gl_physics.results.keys()[-10:]
    import pdb;pdb.set_trace()


#rands = GetRandomArticles()
#process([rands])
#import pdb;pdb.set_trace()
gpri = GetPageRevisionInfos(u'Beyoncé', limit=500)
process([gpri])
gri = GetRevisionInfos(gpri.results.values())
process([gri])
import pdb;pdb.set_trace()
#gcc2 = GetCurrentContent(rands.results.values())
#process([gcc, gcc2])

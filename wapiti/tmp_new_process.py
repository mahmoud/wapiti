
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

from operations.category import GetCategoryList

from hematite.async import join as hematite_join


def process(ops):
    to_proc = set(ops)
    while to_proc:
        resps = []
        for op in list(to_proc):
            if not op.remaining:
                to_proc.remove(op)
            resps.extend(op.incomplete_resps.values())
        print resps
        hematite_join(resps, timeout=5.0)
        for op in to_proc:
            op.process_responses()


gcl_physics = GetCategoryList('Physics')
gcl_africa = GetCategoryList('Africa')
#task = gcl.current_task
#mw_resp = MWResponse(task.prepare_params(), client=task.client)
#mw_resp.execute()
#mw_resp.do_complete()

process([gcl_physics, gcl_africa])

import pdb;pdb.set_trace()

# -*- coding: utf-8 -*-

import time
import select


def join(reqs, timeout=5.0, raise_exc=True,
         follow_redirects=None, select_timeout=0.05):
    ret = list(reqs)
    cutoff_time = time.time() + timeout

    while True:
        readers = [r for r in reqs if r.want_read]
        writers = [r for r in reqs if r.want_write]

        # forced writers are e.g., resolving/connecting, don't have sockets yet
        forced_writers = [r for r in writers if r.fileno() is None]
        selectable_writers = [r for r in writers if r.fileno() is not None]

        if not (readers or writers):
            break
        if time.time() > cutoff_time:
            # TODO: is time.time monotonic? no, so... time.clock()?
            break

        if readers or selectable_writers:
            read_ready, write_ready, _ = select.select(readers,
                                                       selectable_writers,
                                                       [],
                                                       select_timeout)
            write_ready.extend(forced_writers)
        else:
            read_ready = []
            write_ready = forced_writers

        try:
            for wr in write_ready:
                _keep_writing = True
                while _keep_writing:
                    _keep_writing = wr.do_write()
            for rr in read_ready:
                _keep_reading = True
                while _keep_reading:
                    _keep_reading = rr.do_read()
        except Exception:
            if raise_exc:
                raise
    return ret

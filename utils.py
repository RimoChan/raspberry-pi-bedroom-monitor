import time
from typing import Callable, Union
from 打点 import save


def 冷却时间(t: Union[int, float], left: Union[int, float] = 0):
    def d(f: Callable):
        def 新f(*li, **d):
            now = time.time()
            if now - 新f.上次执行时间 > 新f.冷却时间:
                新f.上次执行时间 = now
                start = time.time()
                res = f(*li, **d)
                end = time.time()
                save('use_time', end-start, {'function_name': f.__name__})
                return res
        新f.冷却时间 = t
        新f.上次执行时间 = time.time() - t + left
        return 新f
    return d

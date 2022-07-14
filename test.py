from PIL import Image
from time import time


def timer_func(func):
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f'Function {func.__name__!r} executed in {(t2 - t1):.4f}s')
        return result
    return wrap_func

@timer_func
def usingPILandShrink(f, n):
    x = 1599 // 50
    y = 1200 // 50
    for _ in range(10):
        im = Image.open(f)
        im.draft('RGB', (x, y))
        for i in range(n):
            im.getpixel((i, i))

f = "C:\\Users\\victi\\Desktop\\test - Copie\\Caméra\\P_20190606_231050_vHDR_On.jpg"
usingPILandShrink(f, 8)

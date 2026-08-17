import time, random, io, contextlib
import importlib.util
def load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
opt=load("inventory_analysis_optimized.py","opt"); orig=load("inventory_analysis_original.py","orig")
def quiet(fn,*a):
    with contextlib.redirect_stdout(io.StringIO()):
        t0=time.time(); r=fn(*a); return r, time.time()-t0
for n in (250, 400):
    random.seed(7)
    d=[{'id':i,'name':f'P{i}','price':random.randint(5,500)} for i in range(n)]
    ro,to=quiet(orig.find_product_combinations,d,500,50)
    rp,tp=quiet(opt.find_product_combinations,d,500,50)
    print(f"[n={n}] original={to:.3f}s  optimized={tp:.4f}s  speedup={to/tp:.0f}x  pairs={len(ro)}", flush=True)

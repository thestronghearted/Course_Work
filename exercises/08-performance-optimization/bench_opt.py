import time, random, io, contextlib
import importlib.util
def load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
opt=load("inventory_analysis_optimized.py","opt")
orig=load("inventory_analysis_original.py","orig")
def pset(r): return {frozenset((x['product1']['id'],x['product2']['id'])) for x in r}
def quiet(fn,*a):
    with contextlib.redirect_stdout(io.StringIO()):
        t0=time.time(); r=fn(*a); return r, time.time()-t0
# correctness n=300
random.seed(42)
s=[{'id':i,'name':f'P{i}','price':random.randint(5,500)} for i in range(300)]
ro,_=quiet(orig.find_product_combinations,s,500,50); rp,_=quiet(opt.find_product_combinations,s,500,50)
print(f"[correctness n=300] orig={len(ro)} opt={len(rp)} identical={pset(ro)==pset(rp)}")
# optimized at 5000
random.seed(1)
big=[{'id':i,'name':f'P{i}','price':random.randint(5,500)} for i in range(5000)]
rp5,t5=quiet(opt.find_product_combinations,big,500,50)
print(f"[opt n=5000] {t5:.4f}s ({len(rp5)} pairs)")

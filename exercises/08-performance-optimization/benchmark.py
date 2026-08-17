import time, random, io, contextlib
import importlib.util

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

orig = load("inventory_analysis_original.py", "orig")
opt  = load("inventory_analysis_optimized.py", "opt")

def pair_set(results):
    return {frozenset((r['product1']['id'], r['product2']['id'])) for r in results}

def run_quiet(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()):
        t0 = time.time(); res = fn(*a); t1 = time.time()
    return res, t1 - t0

# Correctness on seeded n=400
random.seed(42)
small = [{'id': i, 'name': f'P{i}', 'price': random.randint(5, 500)} for i in range(400)]
ro, _ = run_quiet(orig.find_product_combinations, small, 500, 50)
rp, _ = run_quiet(opt.find_product_combinations, small, 500, 50)
print(f"[Correctness n=400] original={len(ro)} pairs, optimized={len(rp)} pairs, identical set={pair_set(ro)==pair_set(rp)}")

# Direct speedup at n=1500 (original can finish)
random.seed(7)
mid = [{'id': i, 'name': f'P{i}', 'price': random.randint(5, 500)} for i in range(1500)]
ro, to = run_quiet(orig.find_product_combinations, mid, 500, 50)
rp, tp = run_quiet(opt.find_product_combinations, mid, 500, 50)
print(f"[n=1500] original={to:.3f}s  optimized={tp:.4f}s  speedup={to/tp:.0f}x  identical set={pair_set(ro)==pair_set(rp)}")

# Optimized at full n=5000 (original omitted: impractically slow)
random.seed(1)
big = [{'id': i, 'name': f'P{i}', 'price': random.randint(5, 500)} for i in range(5000)]
rp5, tp5 = run_quiet(opt.find_product_combinations, big, 500, 50)
print(f"[n=5000] optimized={tp5:.4f}s  ({len(rp5)} pairs)")

"""T5 reproducible audit. Run from repository root: python t5/full.py --source path/to/app.py --out t5/results/local"""
import argparse, ast, collections, csv, datetime, html, importlib.util, json, os, pathlib, platform, subprocess, sys, time, traceback
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(args,out,timeout=240):
    try:
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=timeout)
        out.write_text(p.stdout,encoding="utf-8")
        return {"exit_code":p.returncode,"stderr":p.stderr[-4000:],"command":args}
    except Exception as e:
        out.write_text("",encoding="utf-8");return {"error":str(e),"command":args}
def load(p):
    try:return json.loads(p.read_text(encoding="utf-8"))
    except Exception:return None
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--source",default=None);ap.add_argument("--out",default="t5/results/local");ap.add_argument("--repeats",type=int,default=10);a=ap.parse_args()
    src=pathlib.Path(a.source) if a.source else next((p for p in [ROOT/"monitoreo_salud_publica/monitoreo_salud_publica/app.py",ROOT/"monitoreo_salud_publica/app.py"] if p.is_file()),None)
    if src is None:raise SystemExit("No se encontró app.py; especifique --source")
    src=src if src.is_absolute() else ROOT/src
    if not src.is_file():raise SystemExit("No existe: "+str(src))
    out=pathlib.Path(a.out);out=out if out.is_absolute() else ROOT/out;out.mkdir(parents=True,exist_ok=True)
    py=sys.executable;f=str(src);commands={
      "radon_cc":[py,"-m","radon","cc","-j","-s",f],
      "radon_mi":[py,"-m","radon","mi","-j",f],
      "radon_raw":[py,"-m","radon","raw","-j",f],
      "pylint":[py,"-m","pylint",f,"--output-format=json","--score=n"],
      "bandit":[py,"-m","bandit","-f","json","-q",f],
      "pymetrica":["pymetrica","run-all","-rt","JSON",str(src.parent)]
    }
    executions={k:run(v,out/(k+".json")) for k,v in commands.items()}
    for k in commands:
        if load(out/(k+".json")) is None: executions[k]["json_valid"]=False
        else:executions[k]["json_valid"]=True
    tree=ast.parse(src.read_text(encoding="utf-8"));parent={}
    for n in ast.walk(tree):
        for child in ast.iter_child_nodes(n):parent[child]=n
    def callname(n):
        try:return ast.unparse(n.func)
        except Exception:return ""
    candidates=[]
    def add(n,indicator,rule,detail):
        candidates.append({"indicator":indicator,"line":n.lineno,"rule":rule,"description":detail,"confirmed":False,"review":"pendiente"})
    for n in ast.walk(tree):
        if isinstance(n,(ast.For,ast.AsyncFor,ast.While)):
            calls=[x for x in ast.walk(n) if isinstance(x,ast.Call)]
            for c in calls:
                name=callname(c)
                if name.endswith((".iterrows",".itertuples")):add(c,"IND-EF-02","CWE-1050","Iteración de filas: "+name)
                elif name.endswith((".read_csv",".read_excel")):add(c,"IND-EF-02","CWE-1050","Lectura dentro de bucle: "+name)
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            dec=[ast.unparse(x) for x in n.decorator_list]
            is_route=any(".route(" in d for d in dec)
            reads=[x for x in ast.walk(n) if isinstance(x,ast.Call) and callname(x).endswith((".read_csv",".read_excel"))]
            if is_route:
                for x in reads:add(x,"IND-EF-01","CWE-1067","Lectura en endpoint; verificar repetición: "+n.name)
                scans=collections.Counter()
                for x in ast.walk(n):
                    if isinstance(x,ast.Subscript) and isinstance(x.value,ast.Name):scans[x.value.id]+=1
                for name,count in scans.items():
                    if count>1:add(n,"IND-EF-03","CWE-1067",f"Revisar {count} subíndices de {name}; NO prueba rescaneos")
        if isinstance(n,ast.Call) and callname(n)=="open":
            cur=parent.get(n);in_with=False
            while cur is not None and not isinstance(cur,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Module)):
                if isinstance(cur,ast.withitem):in_with=True;break
                cur=parent.get(cur)
            if not in_with:add(n,"REV-CWE-775","CWE-775","Revisar cierre de recurso abierto")
    (out/"eficiencia_candidatos.json").write_text(json.dumps(candidates,indent=2,ensure_ascii=False),encoding="utf-8")
    with (out/"eficiencia_candidatos.csv").open("w",newline="",encoding="utf-8") as fp:
        w=csv.DictWriter(fp,fieldnames=["indicator","line","rule","description","confirmed","review"]);w.writeheader();w.writerows(candidates)
    dynamic={"status":"not_run","reason":"","routes":[],"repeats":a.repeats,"note":"test_client en proceso, no latencia de red ni servidor real"}
    try:
        import pandas as pd
        old=pd.read_csv;counts=collections.Counter()
        def counted(*args,**kwargs):
            counts["read_csv"]+=1
            return old(*args,**kwargs)
        sys.path.insert(0, str(src.parent.parent))
        import importlib
        importlib.invalidate_caches()
        module=importlib.import_module(f"{src.parent.name}.{src.stem}")
        if not hasattr(module,"app"):raise RuntimeError("No existe objeto Flask app")
        legacy=module.legacy_ready() if hasattr(module,"legacy_ready") else None
        dynamic["legacy_ready"]=legacy
        routes=["/","/regional","/severidad","/ranking","/pronosticos"]
        client=module.app.test_client()
        pd.read_csv=counted
        try:
            for route in routes:
                lat=[];reads=[];codes=[];errors=[]
                for i in range(max(1,a.repeats)):
                    counts.clear();start=time.perf_counter()
                    try:
                        response=client.get(route);codes.append(response.status_code)
                    except Exception as exc:errors.append(repr(exc));codes.append(None)
                    lat.append((time.perf_counter()-start)*1000);reads.append(counts["read_csv"])
                dynamic["routes"].append({"route":route,"status_codes":dict(collections.Counter(str(x) for x in codes)),"mean_ms":round(sum(lat)/len(lat),3),"min_ms":round(min(lat),3),"max_ms":round(max(lat),3),"mean_csv_reads":round(sum(reads)/len(reads),3),"read_counts":reads,"errors":errors[:3]})
        finally:pd.read_csv=old
        dynamic["status"]="measured" if legacy else "incomplete_missing_legacy_data"
        dynamic["reason"]="" if legacy else "Datos legados no disponibles; respuestas fallback no permiten medir las rutas reales"
    except Exception as exc:
        dynamic["status"]="failed";dynamic["reason"]=repr(exc);dynamic["traceback"]=traceback.format_exc()[-3000:]
    (out/"dynamic.json").write_text(json.dumps(dynamic,indent=2,ensure_ascii=False),encoding="utf-8")
    raw=load(out/"radon_raw.json") or {};lloc=sum(x.get("lloc",0) for x in raw.values() if isinstance(x,dict))
    cc=load(out/"radon_cc.json") or {};cc_items=[x for v in cc.values() if isinstance(v,list) for x in v]
    mi=load(out/"radon_mi.json") or {};mi_vals=[v.get("mi") for v in mi.values() if isinstance(v,dict) and isinstance(v.get("mi"),(int,float))]
    pylint=load(out/"pylint.json");bandit=load(out/"bandit.json")
    from importlib.metadata import version,PackageNotFoundError
    versions={}
    for name in ["radon","pylint","bandit","pymetrica","flask","pandas"]:
        try:versions[name]=version(name)
        except PackageNotFoundError:versions[name]="not_installed"
    git=run(["git","rev-parse","HEAD"],out/"git_commit.txt")
    summary={"utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"system":platform.platform(),"python":sys.version.split()[0],"source":str(src),"git_commit":(out/"git_commit.txt").read_text().strip(),"versions":versions,"lloc":lloc,"kloc":lloc/1000,"cc_functions":len(cc_items),"cc_max":max([x.get("complexity",0) for x in cc_items],default=None),"mi":round(sum(mi_vals)/len(mi_vals),2) if mi_vals else None,"pylint_alerts":len(pylint) if isinstance(pylint,list) else None,"bandit_alerts":len(bandit.get("results",[])) if isinstance(bandit,dict) else None,"efficiency_candidates":len(candidates),"ind_ef_01":None,"ind_ef_02_confirmed":None,"ind_ef_03_confirmed":None,"ind_ef_04_def":None,"dynamic":dynamic,"executions":executions,"methodology":"EF01 dynamic read counts are measured only when legacy_ready; EF02/03 require review; EF04 requires confirmed distinct weaknesses / (LLOC/1000)."}
    if dynamic["status"]=="measured":
        summary["ind_ef_01"]={x["route"]:x["mean_csv_reads"] for x in dynamic["routes"]}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    with (out/"routes.csv").open("w",newline="",encoding="utf-8") as fp:
        w=csv.DictWriter(fp,fieldnames=["route","mean_ms","min_ms","max_ms","mean_csv_reads","status_codes"]);w.writeheader()
        for x in dynamic["routes"]:w.writerow({k:json.dumps(x[k],ensure_ascii=False) if k=="status_codes" else x[k] for k in w.fieldnames})
    items=[("Sistema",summary["system"]),("Commit",summary["git_commit"]),("LLOC",lloc),("Radon CC máxima",summary["cc_max"]),("Radon MI",summary["mi"]),("Alertas Pylint",summary["pylint_alerts"]),("Alertas Bandit",summary["bandit_alerts"]),("Candidatos EF (sin confirmar)",len(candidates)),("Dinámica",dynamic["status"]),("EF04 DEF","Pendiente de validación")]
    table="".join("<tr><th>"+html.escape(str(k))+"</th><td>"+html.escape(str(v))+"</td></tr>" for k,v in items)
    rt="".join("<tr>"+ "".join("<td>"+html.escape(str(x.get(k,"")))+"</td>" for k in ["route","mean_ms","mean_csv_reads","status_codes"])+"</tr>" for x in dynamic["routes"])
    page="<html lang='es'><meta charset='utf-8'><title>T5 resultados</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 18px;color:#243448}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bfcad4;padding:9px;text-align:left}th{background:#e4eff8}</style><h1>T5: auditoría reproducible</h1><p>Alertas no equivalen a defectos confirmados. EF04 requiere revisión humana.</p><table>"+table+"</table><h2>Rutas</h2><table><tr><th>Ruta</th><th>Media ms</th><th>Lecturas CSV</th><th>HTTP</th></tr>"+rt+"</table><p>Archivos: summary.json, dynamic.json, routes.csv, eficiencia_candidatos.csv, reportes JSON por herramienta.</p></html>"
    (out/"reporte.html").write_text(page,encoding="utf-8")
    print("Resultados:",out,"\nEstado dinámico:",dynamic["status"],"\nLLOC:",lloc)
    if any(not x.get("json_valid") for x in executions.values()):print("AVISO: herramienta(s) sin JSON válido. Revisar summary.json.")
if __name__=="__main__":main()

import json,pathlib,re,unicodedata,difflib,hashlib
import pymupdf
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=pathlib.Path(__file__).resolve().parent
BASE=ROOT/'pipeline/salida/gpt-6-luna__p5'
def norm(s):
 s=unicodedata.normalize('NFKD',s.lower());s=''.join(c for c in s if not unicodedata.combining(c));s=s.replace('-\n','');return re.findall(r'[a-z0-9]+',s)
def run():
 records=[]; entries=[];diffs=[]
 for f in sorted((BASE/'soluciones/gpt-6-luna__s1').glob('*/*.json')):
  d=json.loads(f.read_text());b=json.loads((BASE/f.name).read_text());pdf=pymupdf.open(ROOT/'data'/d['fuente']['archivo']);r=d.get('resultado',{});nodes={x['id']:x for x in b['resultado']['nodos']}
  rec={'documento':f.stem,'origen':f.parent.name,'asignatura':b['documento']['asignatura'],'anio':b['documento']['anio'],'convocatoria':b['documento']['convocatoria'],'estado_pipeline':d['estado'],'contiene_soluciones':r.get('contiene_soluciones'),'entradas':len(r.get('entradas',[])),'paginas_pdf':len(pdf),'desde':d['fuente']['desde'],'fuente':d['fuente'],'sha256_pdf':hashlib.sha256((ROOT/'data'/d['fuente']['archivo']).read_bytes()).hexdigest(),'incidencias':r.get('incidencias',[]),'sin_correspondencia':r.get('sin_correspondencia',[])}; records.append(rec)
  for e in r.get('entradas',[]):
   for t in e['respuesta']:
    n=nodes.get(e['nodo']);p=next((p['pagina'] for p in e['paginas'] if p['idioma']==t['idioma']),None)
    source='\n'.join(pdf[k].get_text(sort=True) for k in range((p or 1)-1,len(pdf))); a=norm(source); c=norm(t['markdown']);m=difflib.SequenceMatcher(None,a,c,autojunk=False);blocks=[z for z in m.get_matching_blocks() if z.size>=5]
    start=blocks[0].a if blocks else 0; end=blocks[-1].a+blocks[-1].size if blocks else len(a);span=a[start:end];mm=difflib.SequenceMatcher(None,span,c,autojunk=False)
    row={'documento':f.stem,'origen':f.parent.name,'nodo':e['nodo'],'idioma':t['idioma'],'pagina':p,'nodo_existe':n is not None,'pagina_valida':p is not None and 1<=p<=len(pdf),'tipo_nodo':n['tipo'] if n else None,'etiqueta':n['etiqueta'] if n else None,'enunciado':n['enunciado'] if n else None,'palabras_salida':len(c),'similitud_lexica_orientativa':round(mm.ratio(),4),'figura_marcador':'ver figura' in t['markdown'],'texto':t['markdown']};entries.append(row)
    if rec['asignatura']=='Historia de España':
     changes=[]
     for op,i,j,k,l in mm.get_opcodes():
      if op!='equal' and (j-i>=5 or l-k>=5):changes.append({'op':op,'fuente':' '.join(span[i:j]),'salida':' '.join(c[k:l])})
     diffs.append({'doc':f.stem,'nodo':e['nodo'],'pagina':p,'etiqueta':n['etiqueta'],'enunciado':n['enunciado'],'ratio':round(mm.ratio(),3),'inicio':t['markdown'][:150],'final':t['markdown'][-150:],'cambios':changes})
 (OUT/'registros.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
 (OUT/'entradas.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2))
 (OUT/'contraste-lexico-historia.json').write_text(json.dumps(diffs,ensure_ascii=False,indent=2))
 print(len(records),len(entries),'entradas; history',len(diffs));print('validity',[(r['documento'],r['nodo']) for r in entries if not r['nodo_existe'] or not r['pagina_valida']])
 for rec in records:
  es=[x for x in entries if x['documento']==rec['documento']];print(rec['documento'],len(es),sum(x['palabras_salida'] for x in es))
if __name__=='__main__':run()

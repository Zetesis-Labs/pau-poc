import pathlib,json,collections
P=pathlib.Path(__file__).resolve().parents[3];O=pathlib.Path(__file__).resolve().parent;B=P/'pipeline/salida/gpt-6-luna__p5'
entries=json.loads((O/'entradas.json').read_text());records=json.loads((O/'registros.json').read_text());pub=json.loads((P/'datos/preguntas.json').read_text());out=[]
def txt(a):
 d={}
 for x in a:d[x['idioma']]=d.get(x['idioma'],'')+ ('\n\n' if x['idioma'] in d else '')+x['markdown']
 return d
for rec in records:
 id=rec['documento'];ns=json.loads((B/(id+'.json')).read_text())['resultado']['nodos'];pubnodes={};amb=[]
 def walk(q,parent=None):
  if 'id' in q: nid=q['id'].split(':')[1]
  else:
   candidates=[n for n in ns if n['padre']==parent and txt(n['etiqueta'])==q['etiqueta'] and txt(n['enunciado'])==q['enunciado']];nid=candidates[0]['id'] if len(candidates)==1 else None
   if nid is None:amb.append(q['etiqueta'])
  if nid:pubnodes[nid]=q
  for a in q['apartados']:walk(a,nid)
 for q in pub['preguntas']:
  if q['examen']['id']==id:walk(q)
 rfile=B/'rubricas/gpt-6-luna__r2'/(id+'.json');r=json.loads(rfile.read_text()) if rfile.exists() else None;rs={e['nodo']:e for e in (r or {}).get('resultado',{}).get('entradas',[])}
 for e in entries:
  if e['documento']!=id:continue
  n=pubnodes.get(e['nodo']);sol=n.get('solucion') if n else None;r2=rs.get(e['nodo']);rt=txt(r2.get('respuesta',[])) if r2 else {};t=rt.get(e['idioma'])
  out.append({'documento':id,'origen':e['origen'],'nodo':e['nodo'],'idioma':e['idioma'],'publicacion_nodo_encontrado':n is not None,'publicacion_texto_identico':sol is not None and sol['texto'].get(e['idioma'])==e['texto'],'publicacion_pagina_identica':sol is not None and sol['paginas'].get(e['idioma'])==e['pagina'],'publicacion_origen_identico':sol is not None and sol['origen']==e['origen'],'publicacion_fuente_identica':sol is not None and sol['fuente']==rec['fuente']['anexo']['fuente'],'publicacion_pdf':sol.get('pdf') if sol else None,'publicacion_url':sol.get('url') if sol else None,'publicacion_incrustado':sol.get('incrustado') if sol else None,'r2_existe':r is not None,'r2_respuesta_presente':t is not None,'r2_texto_identico':t==e['texto'] if t else None,'r2_respuesta':t})
 print(id,'pub',len(pubnodes),'amb',amb,'r2',r is not None,'respuestas',sum(bool(x.get('respuesta')) for x in rs.values()))
(O/'publicacion-r2.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print('NO IDENTICOS PUB',[(x['documento'],x['nodo'],x['idioma']) for x in out if not x['publicacion_texto_identico']]);print('r2matches',sum(x['r2_respuesta_presente'] for x in out),'identical',sum(x['r2_texto_identico'] is True for x in out))

"""Build transparent Astrolytics client-side data from the original NASA PSI CSV archive.
Standard library only; all provenance retained. Run: python build_data.py INPUT_ZIP
"""
import csv, io, json, math, re, sys, zipfile, collections, pathlib
ROOT = pathlib.Path(__file__).resolve().parent
ZIP = pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'source'/'CSVs for the PSIs(1).zip'
OUT=ROOT/'data'; OUT.mkdir(exist_ok=True)
ATM_TO_PSI=14.6959488; MMHG_TO_PSI=ATM_TO_PSI/760; BAR_TO_PSI=14.5037738
NAMES=[
 ('26','BASS','Prevention','ISS','Solid materials; ventilation changes combustion',3,True,'Prevention & suppression'),
 ('25','BASS-II','Prevention','ISS','Flame spread over PMMA, rods and films',3,True,'Prevention'),
 ('98','Saffire-I','Prevention','Cygnus','Large-scale cotton-fiberglass sheet fire',3,True,'Prevention'),
 ('99','Saffire-II','Prevention','Cygnus','Nine material sample tests and Earth comparison',3,True,'Prevention'),
 ('100','Saffire-III','Prevention','Cygnus','Large sheet test under airflow',3,True,'Prevention'),
 ('20','ACME BRE','Prevention','ISS','Gas burner as surrogate for material flames',3,True,'Prevention'),
 ('102','SAME','Detection','ISS','Microgravity smoke from overheated materials',3,False,'Detection'),
 ('101','SAME-R','Detection','ISS','Smoke aging and detector-relevant properties',3,False,'Detection'),
 ('47','DAFT / DAFT-2','Detection','ISS','Dust and particle-counter hardware in orbit',2,False,'Detection'),
 ('69','FLEX','Suppression','ISS','Droplet flame extinction, disruption, completion',3,True,'Suppression'),
 ('68','FLEX-2','Flame science','ISS','Fuel plan, not experimental outcomes',2,False,'Supporting science'),
 ('39','CFI','Flame science','ISS','Cool-flame droplet tests; no outcomes in summary table',1,False,'Supporting science'),
 ('107','SPICE','Flame science','ISS','Soot and gas-jet flame tests with airflow',2,False,'Supporting science'),
 ('106','SLICE','Flame science','ISS','Lifted diffusion flames',1,False,'Supporting science'),
 ('159','ACME CFI-G','Flame science','ISS','Gas spherical flames; normal and inverse geometries',2,True,'Supporting science'),
 ('22','ACME E-FIELD','Flame science','ISS','Electric-field impact on flame emissions',2,False,'Supporting science'),
 ('23','ACME s-Flame','Flame science','ISS','Spherical flames in varied atmospheres',1,False,'Supporting science'),
 ('21','ACME CLD Flame','Flame science','ISS','Coflow flames at extreme fuel dilution',1,False,'Supporting science'),
 ('10','ACME Flame Design','Flame science','ISS','Normal and inverse flame conditions without outcomes',1,False,'Supporting science'),
 ('62','Flame-spread model','Ground studies','Ground / model','Simulation based on BASS and BASS-II imagery',2,False,'Prevention'),
 ('115','Smoke-growth simulation','Ground studies','Ground / model','Simulation based on SAME',2,False,'Detection'),
 ('142','Cool-flame counterflow','Ground studies','Ground / model','Ground-lab literature references and modeling',1,False,'Supporting science'),
 ('117','Cool-flame droplet CFD','Ground studies','Ground / model','CFD using FLEX flight data',1,False,'Supporting science'),
 ('60','Soot analysis','Ground studies','Ground / model','Modeled soot properties from SPICE images',1,False,'Supporting science')]
meta=[]
for psi,name,pillar,environment,desc,relevance,material,application in NAMES:
 meta.append({'id':'PSI-'+psi,'name':name,'pillar':pillar,'environment':environment,'description':desc,'relevance':relevance,'materialEvidence':material,'application':application,'url':'https://psi.nasa.gov/physci/repo/data/investigations/PSI-'+psi})
meta_by_id={e['id']:e for e in meta}

def num(v):
 try:
  s=str(v).strip(); x=float(s); return x if math.isfinite(x) else None
 except: return None

def col(r,k): return (r.get(k) or '').strip()
def pr(x,d=3):return round(x,d) if x is not None else None

def valid_oxygen(v):return v is not None and 0 <= v <= 100

def valid_pressure(v):return v is not None and v>0 and v<250

def to_oxygen_fraction(v):
 a=num(v);return pr(a*100,3) if a is not None and 0<=a<=1 else None

def read_archive():
 res=[]
 with zipfile.ZipFile(ZIP) as z:
  for name in z.namelist():
   if not name.lower().endswith('.csv') or name.startswith('__MACOSX/'):continue
   content=z.read(name).decode('utf-8-sig',errors='replace')
   rdr=csv.DictReader(io.StringIO(content))
   rows=list(rdr)
   # Preserve line number as based on actual CSV records; multiline rows make physical line number different.
   for i,r in enumerate(rows,start=2):r['_source_row']=i
   code=re.search(r'PSI-\d+',name)
   res.append((name.rsplit('/',1)[-1],code.group(0) if code else '',list(rdr.fieldnames or []),rows))
 return res

sources=read_archive(); data={'generatedFrom':'User-uploaded NASA PSI experimental tables (22 CSV files); not a live NASA API','metadata':meta,'sourceTables':[],'quality':[], 'flex':[],'cfigNormal':[],'cfigInverse':[],'flameNormal':[],'flameInverse':[],'spice':[],'bass2':[],'saffire':[],'sourceFiles':[]}
quality=[]
for filename,psi,headers,rows in sources:
 nonempty=[r for r in rows if any((str(r.get(h) or '')).strip() for h in headers)]
 t={'file':filename,'psi':psi,'rowsInFile':len(rows),'nonemptyRows':len(nonempty),'blankPadding':len(rows)-len(nonempty),'columns':len(headers),'headers':headers,'category':'Records with heterogeneous formats'}
 if psi=='PSI-69':t['category']='Experimental outcomes';
 if psi=='PSI-159':t['category']='Experimental outcomes';
 if psi=='PSI-10':t['category']='Experimental conditions only';
 # Flag exact duplicate records for reviewer inspection; do not discard possible repeated measurements.
 signatures=collections.Counter(tuple((r.get(h) or '').strip() for h in headers) for r in nonempty)
 exact_extra=sum(c-1 for c in signatures.values() if c>1)
 t['exactDuplicateExtraRows']=exact_extra
 if exact_extra:quality.append({'file':filename,'issue':'Exact duplicate-looking records detected; preserved pending human verification','rows':exact_extra})
 data['sourceTables'].append(t)
 data['sourceFiles'].append({'file':filename,'psi':psi})
 if psi=='PSI-69':
  for r in nonempty:
   pressure = pr(num(col(r,'Ambient pressure; mmHg'))*MMHG_TO_PSI,3) if num(col(r,'Ambient pressure; mmHg')) is not None else None
   oxygen=to_oxygen_fraction(col(r,'O initial ambient composition; mole fraction'))
   outcome=col(r,'Test end').title()
   if outcome not in ('Extinction','Disruption','Completion'):outcome='Not classified'
   record={'dataset':'FLEX','psi':psi,'id':col(r,'FLEX Test #'),'test':col(r,'FLEX Identifier'),'sourceRow':r['_source_row'],'oxygen':oxygen,'pressure':pressure,'oxygenContext':'Ambient','fuel':col(r,'Fuel').title(),'outcome':outcome,'time':num(col(r,'Burn time; s')),'diameter':num(col(r,'Droplet initial diameter; mm')),'date':col(r,'Test Date')}
   record['validMap']=valid_pressure(pressure) and valid_oxygen(oxygen)
   if not record['validMap']:quality.append({'file':filename,'row':r['_source_row'],'issue':'Excluded from oxygen-pressure map: invalid pressure or oxygen','rawPressure':col(r,'Ambient pressure; mmHg'),'rawOxygen':col(r,'O initial ambient composition; mole fraction')})
   data['flex'].append(record)
 elif psi=='PSI-159':
  inverse='Inverse' in filename
  for r in nonempty:
   oxygen=to_oxygen_fraction(col(r,'XO2') if inverse else col(r,' XO2 before test'))
   bar=num(col(r,'approx p (bar)'));p=pr(bar*BAR_TO_PSI,3) if bar is not None else None
   hot=col(r,'Hot ignition').lower(); ignition='Ignited' if hot=='yes' else ('No ignition' if hot=='no' else ('Flash / uncertain' if hot=='flash' else 'Unknown'))
   o={'dataset':'CFI-G inverse' if inverse else 'CFI-G normal','psi':psi,'id':col(r,'Test'),'sourceRow':r['_source_row'],'oxygen':oxygen,'pressure':p,'oxygenContext':'Burner stream (inverse flame)' if inverse else 'Test atmosphere (normal flame)','fuel':col(r,'Fuel'),'outcome':ignition,'ignition':hot,'terminal':col(r,'Self -ext or flow term') if inverse else col(r,'Self-ext or flow term'),'time':num(col(r,'burn time (sec)')),'day':col(r,'Day')}
   o['validMap']=bool(valid_pressure(p) and valid_oxygen(oxygen))
   if not o['validMap']:quality.append({'file':filename,'row':r['_source_row'],'issue':'Excluded: invalid oxygen/pressure'})
   data['cfigInverse' if inverse else 'cfigNormal'].append(o)
 elif psi=='PSI-10':
  inverse='Inverse' in filename
  for r in nonempty:
   oxy=to_oxygen_fraction(col(r,'XO2') if inverse else col(r,'XO2 (init)'))
   atm=num(col(r,'pmean (atm)')); pressure=pr(atm*ATM_TO_PSI,3) if atm is not None else None
   if oxy is None or pressure is None:continue
   data['flameInverse' if inverse else 'flameNormal'].append({'dataset':'Flame Design inverse' if inverse else 'Flame Design normal','psi':psi,'id':col(r,'Test'),'sourceRow':r['_source_row'],'oxygen':oxy,'pressure':pressure,'oxygenContext':'Burner stream (inverse flame)' if inverse else 'Normal flame atmosphere','fuel':col(r,'Fuel') if not inverse else 'Ethylene (inverse stream)','outcome':None})
 elif psi=='PSI-107':
  for r in nonempty:
   air=num(col(r,'Air Rate (cm/s)'))
   if air is not None and air>=0:
    data['spice'].append({'psi':psi,'sourceRow':r['_source_row'],'fuel':col(r,'Fuel'),'air':air,'fuelRate':num(col(r,'Fuel Rate (mg/s)')),'nozzle':num(col(r,'Nozzle (mm)'))})
   elif air is not None:
    quality.append({'file':filename,'row':r['_source_row'],'issue':'Invalid negative airflow excluded from airflow plot','value':air})
 elif psi=='PSI-25':
  for r in nonempty:
   o=num(col(r,'Calibrated  initial O2 % by vol '))
   data['bass2'].append({'psi':psi,'sourceRow':r['_source_row'],'test':col(r,'Test #'),'material':col(r,'Fuel Sample Material'),'oxygen':o if valid_oxygen(o) else None,'airflowText':col(r,'Air display')})
 elif psi in ('PSI-98','PSI-99','PSI-100'):
  for r in nonempty:
   sample=col(r,'Sample Number') or col(r,'Sample Number ')
   mat=col(r,'Material')
   rawflow=col(r,'Air Flow (cm/s)') or col(r,'Air Flow ') ;airtext=rawflow.strip().replace('cm/s','').strip();air=num(airtext)
   if psi=='PSI-98':
    rawO=col(r,'Percent O2');burn=col(r,'Burn Time (s)')
   elif psi=='PSI-99':
    rawO=col(r,'Percent O2 (Note 1)');burn=col(r,'Burn Time (s)')
   else:rawO='Not recorded';burn='Not recorded'
   if air is None:continue # pre-test camera-only rows are not burns
   data['saffire'].append({'psi':psi,'sample':sample,'material':mat,'air':air,'oxygenText':rawO,'burnTime':num(burn),'burnTimeText':burn,'sourceRow':r['_source_row']})

for r in data['sourceTables']:
 if r['blankPadding']:quality.append({'file':r['file'],'issue':'Blank padding excluded from all row counts','rows':r['blankPadding']})
 # types of placeholders, do not imply corrections
 t=next(x[3] for x in sources if x[0]==r['file']);
 errors=sum(1 for row in t for field in r['headers'] if str(row.get(field,'')).strip() in ('#VALUE!','#DIV/0!','#REF!'))
 if errors:quality.append({'file':r['file'],'issue':'Spreadsheet error tokens present; not silently converted to numeric zeros','cells':errors})

for entry in data['metadata']:
 tables=[t for t in data['sourceTables'] if t['psi']==entry['id']]
 entry['fileCount']=len(tables)
 entry['tableRows']=sum(t['nonemptyRows'] for t in tables)
 entry['hasCSV']=bool(tables)
 entry['score']=entry['relevance']*2+(2 if entry['materialEvidence'] else 0)+(2 if entry['id'] in ('PSI-69','PSI-159') else 0)
 entry['scoreReason']='2 × documented relevance (1–3) + 2 if material evidence + 2 if an outcome-ready oxygen/pressure table; heuristic, not a safety score.'

data['quality']=quality
stats={
 'csvFiles':len(sources), 'investigations':len(meta), 'withTables':sum(m['hasCSV'] for m in meta),
 'allNonemptyRows':sum(t['nonemptyRows'] for t in data['sourceTables']),
 'blankRowsExcluded':sum(t['blankPadding'] for t in data['sourceTables']),
 'flexTests':len(data['flex']), 'flexMapped':sum(r['validMap'] for r in data['flex']),
 'cfigNormal':len(data['cfigNormal']), 'cfigInverse':len(data['cfigInverse']),
 'cfigNormalMapped':sum(r['validMap'] for r in data['cfigNormal']),
 'spiceAirflow':len(data['spice']),
 'saffireBurns':len(data['saffire']),
 'flameDesignConditions':len(data['flameNormal'])+len(data['flameInverse']),
 'flexOutcome':dict(collections.Counter(r['outcome'] for r in data['flex'])),
 'cfigNormalOutcome':dict(collections.Counter(r['outcome'] for r in data['cfigNormal']))}
data['stats']=stats
data['notes']=[
 'FLEX and CFI-G normal flames contribute comparable ambient oxygen/pressure scatter data, but use different fuels, geometries, and endpoints.',
 'CFI-G inverse flame XO2 refers to the burner oxygen stream, not cabin air; inverse tests are excluded from ambient Fire Map.',
 'Flame Design tables contain conditions without a combustion outcome; never interpret them as successes or failures.',
 'FLEX atmospheric pressure was converted mmHg to psi; CFI-G bar to psi; Flame Design atm to psi.',
 'Saffire-I and Saffire-II contain camera-only pretests; only airflow-bearing sample rows are treated as burns.',
 'BASS-II Air display is nonstandard free text; it cannot be safely converted into air velocity without manual research.',
 'Some CFI-G FT (flow terminated) burn times are censored; do not present them as natural extinction times.',
 'SPICE airflow is experimental gas-flow metadata without a direct extinction outcome.',
 'Not every one of the 24 investigations has an experimental table in this archive.',
 'No direct lunar or Martian partial-gravity fire tests are present in these datasets.',
 'All scores are transparent navigation heuristics, not predictions of safety.',
 ]
jsonfile=OUT/'astrolytics.json';jsonfile.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(OUT/'astrolytics-data.js').write_text('window.ASTRO_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
(OUT/'quality-report.json').write_text(json.dumps({'stats':stats,'issues':quality,'assumptions':data['notes']},indent=2,ensure_ascii=False),encoding='utf-8')
# Clean exports, linking each record back to a test and source row
for key in ('flex','cfigNormal','cfigInverse','flameNormal','flameInverse','spice','saffire'):
 records=data[key]
 if not records:continue
 keys=list(dict.fromkeys(k for r in records for k in r.keys()))
 with (OUT/(key+'.csv')).open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(records)
print(json.dumps(stats,indent=2))
print('issues:',len(quality),'output:',jsonfile)

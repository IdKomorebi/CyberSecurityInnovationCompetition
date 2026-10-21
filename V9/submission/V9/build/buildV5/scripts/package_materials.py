"""Package only the prepared submission files; keep recording work and credentials out."""
from pathlib import Path
import zipfile,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
NAME='杜浩存-面向聚合推断威胁的数据定级与共享审查系统-'
OUT=ROOT/'deliverables';OUT.mkdir(exist_ok=True)
SKIP={'__pycache__','.git','.codex','logs','回收站'}
def archive(dest,files):
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for file,arc in files:
   assert not file.is_symlink(),file
   z.write(file,arc)
 with zipfile.ZipFile(dest) as z:assert z.testzip() is None
 return {'file':dest.name,'bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
def main():
 root=ROOT/'package';files=[]
 for p in sorted(root.rglob('*')):
  if not p.is_file() or set(p.relative_to(root).parts)&SKIP or p.suffix in {'.pyc','.log','.pid'}:continue
  assert p.name!='deepseek.env',p
  files.append((p,str(p.relative_to(root))))
 result=[archive(OUT/(NAME+'可执行程序.zip'),files)]
 if (ROOT/'video/演示视频.mp4').exists() and (ROOT/'video/制作说明.md').exists():
  result.append(archive(OUT/(NAME+'演示视频.zip'),[(ROOT/'video'/f,'演示视频/'+f) for f in ['演示视频.mp4','演示视频.srt','制作说明.md']]))
 (ROOT/'打包校验.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 for r in result:print(r['file'],round(r['bytes']/1e6,2),'MB')
if __name__=='__main__':main()

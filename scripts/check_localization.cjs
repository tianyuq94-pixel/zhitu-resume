// Audit literal UI translations using the TypeScript parser (no model/API requests).
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const ts=require('../frontend/node_modules/typescript');
const root=path.resolve(__dirname,'../frontend/src');
const messages=JSON.parse(fs.readFileSync(path.join(root,'locales/zh.json'),'utf8'));
const allowed=new Set(['Vue','JavaScript','↓ PDF','↓ Word','PDF','Word','DOCX','TypeScript','V1.0']);
const missing=new Set();
function scan(dir){
 for(const entry of fs.readdirSync(dir,{withFileTypes:true})){
   const file=path.join(dir,entry.name);
   if(entry.isDirectory()){scan(file);continue;}
   if(!/\.(vue|ts)$/.test(file))continue;
   const text=fs.readFileSync(file,'utf8');
   // Template expressions are valid TS fragments; walk them alongside the script.
   const snippets=file.endsWith('.vue')?[text.match(/<script[^>]*>([\s\S]*?)<\/script>/)?.[1]||'',...[...text.matchAll(/\{\{([\s\S]*?)\}\}/g)].map(m=>m[1]),...[...text.matchAll(/(?:[:@][\w.-]+)="([^"]+)"/g)].map(m=>m[1])]:[text];
   for(const snippet of snippets){
     const tree=ts.createSourceFile(file,snippet,ts.ScriptTarget.Latest,true);
     const check=node=>{
       if(ts.isCallExpression(node)&&node.expression.getText(tree)==='t'){
         const walk=value=>{
           if(ts.isStringLiteral(value)&&/[a-zA-Z]{3}/.test(value.text)&&!allowed.has(value.text)&&!Object.hasOwn(messages,value.text))missing.add(path.relative(root,file)+': '+value.text);
           else if(ts.isConditionalExpression(value)){walk(value.whenTrue);walk(value.whenFalse);}
         };
         if(node.arguments[0])walk(node.arguments[0]);
       }
       ts.forEachChild(node,check);
     };
     check(tree);
   }
 }
}
scan(root);
assert.deepEqual([...missing],[],'Untranslated UI copy');
console.log('Literal UI translation coverage passed.');

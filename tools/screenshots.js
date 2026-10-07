const { chromium } = require('playwright');
(async()=>{
 const b=await chromium.launch();const errs=[];
 for (const [w,h,scheme,hash,name] of [[1300,900,'dark','','home'],[1300,900,'dark','#a-sva.2','amb'],[1300,900,'dark','#p-'+process.argv[2],'proc'],[400,850,'light','#repaso','repaso'],[1300,900,'light','#vademecum','vadem'],[400,850,'dark','#quiz-claves','quiz']]){
  const p=await b.newPage({viewport:{width:w,height:h},colorScheme:scheme});
  p.on('console',m=>{if(m.type()==='error')errs.push(name+': '+m.text())});p.on('pageerror',e=>errs.push(name+': '+e.message));
  await p.goto('file://'+process.cwd()+'/samur-manual.html'+hash);await p.waitForTimeout(900);
  const ov=await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
  if(ov)errs.push(name+': horizontal overflow');
  await p.screenshot({path:'s_'+name+'.png',fullPage:false});await p.close();
 }
 console.log(errs.join('\n')||'no errors');await b.close();
})();

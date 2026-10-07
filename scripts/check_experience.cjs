// Browser checks with isolated, synthetic API fixtures. No real AI calls or user edits.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=process.env.TEST_BASE||'http://127.0.0.1:5173';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
 try{
  const context=await browser.newContext(),page=await context.newPage(),errors=[],unexpected=[],reports=[];
  const output=path.resolve(__dirname,'../tmp/experience-qa');fs.mkdirSync(output,{recursive:true});
  let guest=true;
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/api/v1/**',route=>{
   const request=route.request(),url=new URL(request.url()),endpoint=url.pathname.replace('/api/v1','');
   if(['/auth/me','/auth/guest'].includes(endpoint))return route.fulfill({json:{id:999,username:guest?'guest_fixture':'fixture_user',profile_completed:true,created_at:'2026-10-07T00:00:00'}});
   if(endpoint==='/profile')return route.fulfill({json:{real_name:null,school:null,major:null,degree:null,graduation_year:null,career_direction:null,desired_cities:[],job_type:null,profile_completed:false}});
   if(endpoint==='/profile/facts')return route.fulfill({json:{about:'',skills:'',experiences:'',revision:0}});
   if(['/agent','/custom-resumes'].includes(endpoint))return route.fulfill({json:[]});
   if(['/resumes/primary','/resumes/primary/diagnoses/latest','/job-matches/current','/interviews/current'].includes(endpoint))return route.fulfill({body:'null',contentType:'application/json'});
   if(endpoint==='/health/database')return route.fulfill({json:{status:'ok'}});
   if(endpoint==='/persona/profile'){
    const zh=request.headers()['accept-language']==='zh-CN';
    const profile=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../backend/app/persona_public'+(zh?'_zh':'')+'.json'),'utf8'));
    return route.fulfill({json:Object.fromEntries(['name','headline','welcome','links'].map(k=>[k,profile[k]]))});
   }
   unexpected.push(endpoint);return route.fulfill({status:500,json:{detail:'Unexpected fixture endpoint'}});
  });
  const routes=['/agent','/me','/app','/app/resume','/app/profile','/app/custom-resumes','/app/job-match','/app/interview','/app/resume/diagnosis'];
  for(const width of [1440,390])for(const language of ['en','zh'])for(const url of routes){
   await page.setViewportSize({width,height:width===390?844:1000});
   await page.goto(base+url,{waitUntil:'networkidle'});
   await page.getByRole('button',{name:language==='en'?'English':'中文',exact:true}).click();
   assert.equal(new URL(page.url()).pathname,url);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,url+' horizontal overflow');
   if(language==='zh')assert.doesNotMatch(await page.locator('body').innerText(),/YOUR NEXT CHAPTER|YOUR STORY|CAREER WORKSPACE|QUICK START|CAREER PROFILE|TAILORED RESUME|JOB MATCHING|AI INTERVIEW|PRIMARY RESUME/);
   if(url==='/app/profile')assert.equal(await page.locator('.password-card').count(),0,'Guest cannot use password changes');
   if(url==='/agent'){
    await page.locator('.agent-suggestions button').first().click();
    assert.equal(await page.locator('.agent-job-fields input').first().inputValue(),language==='zh'?'AI 应用开发工程师':'AI Application Engineer');
    await page.locator(width===390?'.agent-mobile-tabs button':'.agent-nav').filter({hasText:language==='zh'?'我的简历':'My CV'}).click();
    await page.getByRole('dialog').waitFor();assert.ok(await page.getByRole('dialog').isVisible());
    await page.getByRole('button',{name:language==='zh'?'关闭我的简历':'Close my CV',exact:true}).click();
   }
   if(url==='/me'){
    await page.locator('.chat-header>button').click();await page.locator('.chat-profile').waitFor();
    for(const href of await page.locator('.chat-profile a').evaluateAll(a=>a.map(e=>e.getAttribute('href'))))assert.ok(/^https:\/\//.test(href));
    await page.locator('.chat-header>button').click();
   }
   await page.evaluate(()=>window.scrollTo(0,0));
   await page.screenshot({path:path.join(output,url.replaceAll('/','-')+'-'+language+'-'+width+'.png'),fullPage:true});
   reports.push({url,width,language});
  }
  guest=false;await page.goto(base+'/app/profile',{waitUntil:'networkidle'});assert.ok(await page.locator('.password-card').isVisible(),'Registered users keep password management');
  assert.deepEqual(errors,[]);assert.deepEqual(unexpected,[]);
  // Translate the saved view without changing scores, tool trace, or edit decisions.
  const en=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../frontend/public/demo/recorded-run.json'),'utf8'));
  const zh=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../frontend/src/content/demo-zh.json'),'utf8'));
  assert.deepEqual(zh.sections.map(s=>s.items.map(i=>i.suggestion===null)),en.sections.map(s=>s.items.map(i=>i.suggestion===null)));
  assert.equal(zh.match.matched_items.length,en.match.matched_items.length);assert.equal(zh.match.missing_items.length,en.match.missing_items.length);assert.equal(zh.preparation.items.length,en.preparation.items.length);
  assert.ok(!Object.hasOwn(zh.match,'match_score'),'Score is always preserved from the original run');
  fs.writeFileSync(path.join(output,'report.json'),JSON.stringify({base,reports,errors,unexpected},null,2));
  console.log(JSON.stringify({checks:reports.length,errors,guestPasswordHidden:true,registeredPasswordKept:true,translatedSampleIntegrity:true}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});

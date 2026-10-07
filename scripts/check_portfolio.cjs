/* Read-only portfolio QA. Live toolkit guest creation is mocked for repeatability.
   Requires Playwright; optionally provide PLAYWRIGHT_MODULE and BROWSER_EXECUTABLE. */
const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),path=require('node:path');
const base=process.env.TEST_BASE||'http://127.0.0.1:5173';
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE?{executablePath:process.env.BROWSER_EXECUTABLE}:{})});
 const out=path.resolve(__dirname,'../tmp/portfolio-qa');fs.mkdirSync(out,{recursive:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 const page=await context.newPage(),errors=[],apiRequests=[],reports=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(r.url().includes('/api/v1/'))apiRequests.push(r.url())});
 const routes=['/','/projects/career-agent','/projects/ai-persona','/projects/zhitu-cv','/demo'];
 for(const width of [1440,768,390]) for(const language of ['en','zh']) for(const route of routes){
   await page.setViewportSize({width,height:width===390?844:1000});
   await page.goto(base+route,{waitUntil:'networkidle'});
   await page.getByRole('button',{name:language==='en'?'English':'中文',exact:true}).click();
   if(route==='/demo')await page.locator('.demo-tabs').waitFor();
   await page.locator('img').evaluateAll(images=>images.forEach(img=>{img.loading='eager'}));
   await page.waitForFunction(()=>[...document.images].every(img=>img.complete&&img.naturalWidth>0));
   const actual=await page.evaluate(()=>({lang:document.documentElement.lang,overflow:document.documentElement.scrollWidth>innerWidth+1,images:[...document.querySelectorAll('img')].map(i=>({src:i.src,ok:i.complete&&i.naturalWidth>0})),heading:document.querySelector('h1')?.textContent}));
   assert.equal(actual.lang,language==='en'?'en-GB':'zh-CN');assert.equal(actual.overflow,false,`${route}/${language}/${width} overflow`);assert.ok(actual.images.every(i=>i.ok),JSON.stringify(actual.images));assert.ok(actual.heading);
   assert.ok(await page.locator('img').evaluateAll(images=>images.every(i=>Math.abs(i.clientWidth/i.clientHeight-i.naturalWidth/i.naturalHeight)<0.03)),'Screenshot aspect ratio must be preserved');
   assert.equal(await page.locator('a[href^="mailto:"]').count(),0,'No non-functional email shortcuts');
   if(language==='zh'){
     assert.doesNotMatch(await page.locator('.portfolio-site').innerText(),/Career Agent|AI Persona|Tianyu Qi|Tool selection|Workflow tests|Reply pipeline|Public facts/,'English interface copy in Chinese view');
     assert.ok(await page.locator('img').evaluateAll(images=>images.every(i=>i.src.includes('-zh.png'))),'Chinese screenshots must follow the selected language');
   }
   if(route==='/'){
     assert.deepEqual(await page.locator('.card-links .portfolio-button').evaluateAll(links=>links.map(a=>a.getAttribute('href'))),['/me','/agent','/app']);
     if(width===1440)assert.ok(await page.locator('.card-links .portfolio-button').evaluateAll(links=>links.every(a=>a.getBoundingClientRect().bottom<innerHeight)),'Primary actions should be visible without scrolling on desktop');
     for(const button of await page.locator('.card-links .portfolio-button').all())await button.click({trial:true});
   }
   await page.evaluate(()=>window.scrollTo(0,0));
   const name=`${route.replaceAll('/','-')}-${language}-${width}`;await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});reports.push({route,language,width,...actual});
 }
 assert.equal(apiRequests.length,0,'Portfolio/demo should not create a session or call the model');
 await page.getByRole('button',{name:'English',exact:true}).click();
 await page.goto(base+'/demo',{waitUntil:'networkidle'});
 for(let i=0;i<4;i++){await page.getByRole('tab').nth(i).click();assert.equal(await page.getByRole('tab').nth(i).getAttribute('aria-selected'),'true');assert.ok(await page.getByRole('tabpanel').isVisible());}
 await page.getByRole('tab').nth(0).focus();await page.keyboard.press('End');assert.equal(await page.getByRole('tab').nth(3).getAttribute('aria-selected'),'true');await page.keyboard.press('Home');assert.equal(await page.getByRole('tab').nth(0).getAttribute('aria-selected'),'true');
 for(const file of ['/demo/sample-cv.pdf','/demo/sample-cv.docx','/portfolio/tianyu-qi-project-brief.pdf']) {const response=await context.request.get(base+file);assert.equal(response.status(),200,file);const data=await response.body();assert.ok(data.subarray(0,5).toString().startsWith(file.endsWith('.docx')?'PK':'%PDF'),file);}
 await page.getByRole('button',{name:'中文',exact:true}).click();await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('html').getAttribute('lang'),'zh-CN');
 for(let i=0;i<4;i++){
   await page.getByRole('tab').nth(i).click();
   const copy=await page.getByRole('tabpanel').innerText();
   assert.doesNotMatch(copy,/Education:|Developed a|The candidate|Your CV already|Example Company|AI Application Engineer/,'Recorded example needs translated body content');
   assert.match(copy,/[\u3400-\u9fff]/);
 }
 assert.equal(await page.locator('.demo-language-note').innerText(),'当前正文为同一次英文生成记录的中文译文，评分、缺口及是否修改均保持一致。下载文件保留原始英文，不是另一次生成结果。');
 await page.goto(base+'/projects/not-a-project',{waitUntil:'networkidle'});assert.match(await page.locator('h1').innerText(),/未找到项目/);
 await page.setViewportSize({width:1440,height:1000});await page.goto(base+'/',{waitUntil:'networkidle'});await page.locator('header a[href="/#projects"]').click();await page.waitForFunction(()=>document.querySelector('#projects').getBoundingClientRect().top<80);
 // Static example fetch failure is recoverable without involving authentication.
 await page.route('**/demo/recorded-run.json',r=>r.fulfill({status:503,body:'unavailable'}));await page.goto(base+'/demo',{waitUntil:'networkidle'});assert.ok(await page.getByRole('alert').isVisible());await page.unroute('**/demo/recorded-run.json');await page.getByRole('button',{name:'重试',exact:true}).click();await page.locator('.demo-tabs').waitFor();
 const guest=await browser.newContext();const g=await guest.newPage();let created=0,authed=false;
 await g.route('**/api/v1/**',async route=>{const url=new URL(route.request().url());if(url.pathname.endsWith('/auth/guest')){created++;authed=true;return route.fulfill({json:{id:999,username:'guest_synthetic',profile_completed:false,created_at:'2026-10-07T00:00:00'}})} if(url.pathname.endsWith('/auth/me'))return route.fulfill({status:authed?200:401,json:authed?{id:999,username:'guest_synthetic',profile_completed:false,created_at:'2026-10-07T00:00:00'}:{detail:'Unauthenticated'}}); if(url.pathname.endsWith('/resumes/primary'))return route.fulfill({json:null});return route.fulfill({json:{}})});
 await g.goto(base+'/app',{waitUntil:'networkidle'});await g.locator('.topbar h1').waitFor();assert.equal(new URL(g.url()).pathname,'/app');assert.equal(created,1);
 await g.goto(base+'/app/profile',{waitUntil:'networkidle'});assert.equal(created,1,'Existing sessions must not be replaced');
 // Backend unavailable: static demo must remain reachable from the login fallback.
 const down=await browser.newContext();const d=await down.newPage();await d.route('**/api/v1/**',r=>r.fulfill({status:503,json:{detail:'Service unavailable'}}));await d.goto(base+'/app',{waitUntil:'networkidle'});await d.waitForURL('**/login?redirect=/app');assert.ok(await d.locator('a[href="/demo"]').isVisible());await d.locator('a[href="/demo"]').click();await d.locator('.demo-tabs').waitFor();
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({base,reports,errors,staticApiRequests:apiRequests.length,downloads:true,keyboardTabs:true,persistence:true,guestEntry:true,fallback:true},null,2));
 await browser.close();console.log(JSON.stringify({responsiveChecks:reports.length,staticApiRequests:apiRequests.length,errors,downloads:true,keyboardTabs:true,persistence:true,guestEntry:true,fallback:true}));
})().catch(e=>{console.error(e);process.exit(1)});

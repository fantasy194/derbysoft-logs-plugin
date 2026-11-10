// Real Chromium + an isolated synthetic MCP Apps host; never connects to log services.
// PLAYWRIGHT_MODULE and CHROME_PATH may point to an existing local installation.
import assert from 'node:assert/strict'
import { readFile, mkdir } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const require = createRequire(import.meta.url)
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright')
const dir = path.dirname(fileURLToPath(import.meta.url))
const html = await readFile(path.join(dir, '../src/derbysoft_logs/assets/analysis.html'), 'utf8')
const fixture = JSON.parse(await readFile(path.join(dir, 'fixtures/analysis-report.json'), 'utf8'))
const hostHtml = `<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0"><iframe title="analysis" sandbox="allow-scripts" src="/app" style="border:0;width:100%;height:100vh"></iframe><script>
window.calls=[]; window.payload=${JSON.stringify(fixture)};
window.deliver=params=>document.querySelector('iframe').contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-result',params},'*');
window.context=params=>document.querySelector('iframe').contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/host-context-changed',params},'*');
window.addEventListener('message',event=>{if(event.source!==document.querySelector('iframe').contentWindow||!event.data||event.data.jsonrpc!=='2.0')return;
  const msg=event.data;window.calls.push(msg);if(msg.method==='ui/notifications/size-changed'&&msg.params?.height>0&&msg.params.height<20000)document.querySelector('iframe').style.height=msg.params.height+'px';if(msg.method==='ui/initialize'){
    const mode=new URL(location.href).searchParams.get('mode');
    if(mode==='early')window.deliver({content:[],structuredContent:{schema_version:1,report:window.payload}});
    event.source.postMessage({jsonrpc:'2.0',id:msg.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'fixture',version:'1'},hostCapabilities:{},hostContext:{theme:new URL(location.href).searchParams.get('theme')||'light',styles:{variables:{'--font-sans':'Arial, sans-serif'}}}}},'*');
    if(mode!=='early'&&mode!=='empty')setTimeout(()=>window.deliver({content:[],structuredContent:{schema_version:1,report:window.payload}}),40);
  }
});</script></body></html>`

const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||undefined})
try {
  const page=await browser.newPage({viewport:{width:900,height:900}})
  await page.route('http://fixture.test/**',route=>route.fulfill({status:200,contentType:'text/html',body:route.request().url().includes('/app')?html:hostHtml}))
  page.on('pageerror', error=>console.error('PAGE ERROR:',error.message))
  page.on('console', msg=>console.log('BROWSER:',msg.text()))
  const frame=page.frameLocator('iframe[title="analysis"]')
  const screenshots=process.env.UI_SCREENSHOT_DIR
  if(screenshots)await mkdir(screenshots,{recursive:true})
  async function load(width,theme,mode='early'){
    await page.setViewportSize({width,height:900});await page.goto(`http://fixture.test/?mode=${mode}&theme=${theme}`)
    if(mode!=='empty'){try{await frame.getByRole('heading',{name:fixture.title}).waitFor({timeout:5000})}catch(error){console.log('CALLS:',await page.evaluate(()=>window.calls));console.log('STATUS:',await frame.locator('#app').textContent());throw error}}
  }
  await load(900,'light')
  assert.equal(await frame.locator('html').getAttribute('data-theme'),'light')
  assert.equal(await frame.getByText('数据范围：console 不完整。请结合来源查看。').count(),1)
  assert.equal(await frame.locator('.event').count(),2)
  assert.deepEqual(await frame.locator('.event-time').allTextContents(),[fixture.events[0].timestamp,fixture.events[1].timestamp])
  assert.equal(await frame.locator('.metric .source-ref').count(),2)
  assert.equal(await frame.locator('.chart .source-ref').count(),2)
  assert.equal(await frame.locator('.event .source-ref').count(),2)
  const sourceButton=frame.locator('.event').last().getByRole('button',{name:'来源：console'})
  await sourceButton.focus()
  assert.equal(await sourceButton.evaluate(n=>document.activeElement===n),true)
  await sourceButton.press('Enter')
  assert.equal(await frame.locator('.sources').getAttribute('open'),'')
  assert.equal(await frame.getByText('只返回查询上限内的 console 记录，可能还有更多。').count(),1)
  await frame.getByRole('button',{name:'每分钟请求 数据'}).click()
  assert.equal(await frame.locator('table tbody tr').count(),4)
  assert.equal(await frame.locator('.chart').first().locator('.legend').isVisible(),false)
  assert.equal(await frame.locator('.chart').first().locator('.point-detail').isVisible(),false)
  await frame.getByRole('button',{name:'每分钟请求 图表'}).click()
  const selected=frame.locator('.chart').first().locator('circle').first()
  await selected.focus()
  assert.equal(await selected.evaluate(n=>document.activeElement===n),true)
  await selected.press('Enter')
  assert.match(await frame.locator('.chart').first().locator('.point-detail').textContent(),/2026-11-10T00:00:00Z.*18/)
  const prior=await frame.locator('.chart').first().locator('circle').count()
  await frame.locator('.chart').first().getByRole('button',{name:'异常',exact:true}).click()
  assert.ok(await frame.locator('.chart').first().locator('circle').count()<prior)
  await page.evaluate(()=>window.context({theme:'dark'}))
  await frame.locator('html[data-theme="dark"]').waitFor()
  assert.ok((await page.evaluate(()=>window.calls)).some(x=>x.method==='ui/notifications/size-changed'))
  if(screenshots)await page.screenshot({path:path.join(screenshots,'analysis-dark-900.png'),fullPage:true})

  // Time spacing uses exact nanoseconds, missing values break paths, negatives use a zero baseline.
  await page.evaluate(()=>{
    const r=structuredClone(window.payload)
    r.charts[0].series=[{name:'时间',points:[{x:'2026-11-10T00:00:00.000000001Z',y:1},{x:'2026-11-10T00:00:00.000000002Z',y:null},{x:'2026-11-10T00:00:00.000000004Z',y:4}]}]
    r.charts[1].series=[{name:'净变化',points:[{x:'减少',y:-5},{x:'增加',y:10},{x:'未知',y:null}]}]
    r.events.push({...r.events[0],timestamp:'2026-11-10T00:01:12.123456788Z',label:'更早一纳秒'})
    window.deliver({content:[],structuredContent:{schema_version:1,report:r}})
  })
  const line=frame.locator('.chart').first()
  assert.deepEqual(await frame.locator('.event-title').allTextContents(),['更早一纳秒','收到预订请求','上游返回异常'])
  assert.equal(await line.locator('circle').count(),2)
  assert.equal((await line.locator('path.line').getAttribute('d')).match(/M/g).length,2)
  assert.equal(await line.locator('circle').first().getAttribute('data-x'),'2026-11-10T00:00:00.000000001Z')
  assert.equal(await frame.locator('.bar-zero').first().evaluate(n=>Math.round(parseFloat(n.style.left))),33)
  assert.equal(await frame.getByText('缺失',{exact:true}).count(),1)

  // Untrusted markup stays text; a forged message from the child cannot replace host data.
  await page.evaluate(()=>{const r=structuredClone(window.payload);r.title='<img src=x onerror=alert(1)>';window.deliver({structuredContent:{schema_version:1,report:r}})})
  assert.equal(await frame.getByRole('heading',{name:'<img src=x onerror=alert(1)>'}).count(),1)
  assert.equal(await frame.locator('img').count(),0)
  await frame.locator('html').evaluate(()=>window.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:{isError:true}},'*'))
  assert.equal(await frame.getByRole('heading',{name:'<img src=x onerror=alert(1)>'}).count(),1)
  await page.waitForFunction(()=>document.querySelector('iframe').clientHeight>500)
  await page.evaluate(()=>window.deliver({structuredContent:{schema_version:1,report:{}}}))
  assert.equal(await frame.getByText('分析结果格式不完整，无法显示图表。').count(),1)
  assert.equal(await frame.locator('.chart').count(),0)
  await page.waitForFunction(()=>document.querySelector('iframe').clientHeight<200) // The result is allowed to shrink.
  await page.evaluate(()=>window.deliver({isError:true,content:[{type:'text',text:'fixture error'}]}))
  assert.equal(await frame.getByText('分析视图未能生成，请查看工具返回的信息。').count(),1)
  await page.evaluate(()=>{const r=structuredClone(window.payload);r.charts=[];r.metrics=[];r.events=[];window.deliver({structuredContent:{schema_version:1,report:r}})})
  assert.equal(await frame.getByText('没有可展示的数据。').count(),1)
  for(const [width,theme] of [[375,'light'],[410,'dark'],[900,'light']]){
    await load(width,theme,'normal')
    assert.equal(await frame.locator('html').getAttribute('data-theme'),theme)
    assert.equal(await frame.locator('body').evaluate(n=>n.scrollWidth<=n.clientWidth),true)
    if(screenshots){const height=await frame.locator('main').evaluate(n=>Math.ceil(n.getBoundingClientRect().height));await page.setViewportSize({width,height:height+20});await page.waitForTimeout(300);await page.screenshot({path:path.join(screenshots,`analysis-${theme}-${width}.png`),fullPage:true})}
  }
  await load(410,'light','normal')
  await frame.locator('.sources > summary').click()
  await frame.getByRole('button',{name:'每分钟请求 数据'}).click()
  if(screenshots){const height=await frame.locator('main').evaluate(n=>Math.ceil(n.getBoundingClientRect().height));await page.setViewportSize({width:410,height:height+20});await page.waitForTimeout(300);await page.screenshot({path:path.join(screenshots,'analysis-sources-table-410.png'),fullPage:true})}
  await load(410,'light','empty')
  assert.equal(await frame.getByText('正在准备分析视图…').count(),1)
  const standalone=await browser.newPage()
  await standalone.route('http://fixture.test/app',route=>route.fulfill({status:200,contentType:'text/html',body:html}))
  await standalone.goto('http://fixture.test/app')
  assert.equal(await standalone.getByText('请在支持 MCP App 的宿主中打开此分析视图。').count(),1)
  await standalone.close()
  console.log('MCP analysis UI passed: early result, themes, charts, missing/negative values, provenance, timeline, failures, responsive layouts')
} finally {await browser.close()}

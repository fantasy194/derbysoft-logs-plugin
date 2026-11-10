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
const chartFamilies = JSON.parse(await readFile(path.join(dir, 'fixtures/analysis-chart-families.json'), 'utf8')).reports
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
  const pageErrors=[]
  const externalRequests=[]
  page.on('pageerror', error=>{pageErrors.push(error.message);console.error('PAGE ERROR:',error.message)})
  page.on('request', request=>{if(!request.url().startsWith('http://fixture.test/') && !request.url().startsWith('data:'))externalRequests.push(request.url())})
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

  // Exercise the actual fallback renderer with synthetic, attributed data in
  // each chart family. Check individual rows, rather than only chart titles:
  // an attractive SVG alone must not hide missing or altered values.
  const expectedRows = {
    area: [['请求','2026-11-10T00:00:00Z','4'],['请求','2026-11-10T00:10:00Z','缺失'],['请求','2026-11-10T00:20:00Z','12']],
    stack: [['成功','渠道 A','20'],['失败','渠道 A','80'],['成功','渠道 B','10'],['失败','渠道 B','30']],
    share: [['成功','渠道 A','20'],['失败','渠道 A','80'],['成功','渠道 B','10'],['失败','渠道 B','30']],
    pie: [['成功','15'],['失败','5'],['取消','0']],
    donut: [['成功','15'],['失败','5']],
    histogram: [['0','10','10'],['10','30','10'],['40','50','2']],
    heat: [['A','S1','0'],['B','S1','缺失'],['A','S2','8'],['B','S2','12']],
    scatter: [['一','1','4.5'],['二','7','10'],['三','9','3'],['重合','9','3']],
    funnel: [['提交','100'],['处理','60'],['完成','30']],
    box: [['服务 A','1','3','5','8','13'],['服务 B','2','4','6','7','10']],
    sankey: [['请求','预订','12'],['预订','失败','5'],['预订','完成','6']]
  }
  for(const [width,theme] of [[900,'light'],[375,'light'],[375,'dark']]) {
    await load(width,theme,'empty')
    for(const report of chartFamilies) {
      await page.evaluate(r=>window.deliver({content:[],structuredContent:{schema_version:1,report:r}}),report)
      await frame.getByRole('heading',{name:report.title,exact:true}).waitFor({timeout:5000})
      assert.equal(await frame.locator('body').evaluate(n=>n.scrollWidth<=n.clientWidth),true,`${report.title}: horizontal overflow at ${width}px`)
      for(const chart of report.charts) {
        const card=frame.locator(`[data-chart-kind="${chart.kind}"]`).filter({has:frame.getByRole('heading',{name:chart.title})})
        assert.equal(await card.count(),1,`${chart.id}: one chart card`)
        assert.equal(await card.locator('.source-ref').count(),1,`${chart.id}: source must be available`)
        const marks=card.locator(`[data-geometry="${chart.kind}"]`)
        assert.ok(await marks.count()>0,`${chart.id}: chart geometry is rendered`)
        if(width===375 && ['boxplot','sankey'].includes(chart.kind)) {
          const fits=await card.locator('.svg-scroll').evaluate(node=>({viewport:node.clientWidth,content:node.scrollWidth}))
          assert.ok(fits.content<=fits.viewport,`${chart.id}: the entire graph must fit the 375px viewport without hidden end nodes (${JSON.stringify(fits)})`)
          const visible=await card.locator('.svg-scroll').boundingBox()
          const ends=chart.kind==='sankey' ? card.locator('rect[data-geometry="sankey"]') : card.locator('[data-geometry="boxplot"]')
          assert.ok(await ends.count()>0)
          for(const item of await ends.all()) {
            const box=await item.boundingBox()
            assert.ok(box && box.x>=visible.x-1 && box.x+box.width<=visible.x+visible.width+1,`${chart.id}: end geometry is within viewport`)
          }
        }
        if(chart.kind==='area') {
          assert.equal(await marks.count(),2,'a null observation separates filled area into distinct runs')
          assert.equal((await card.locator('path.line').getAttribute('d')).match(/M/g).length,2,'null observations break the line as well')
        }
        if(chart.kind==='histogram') {
          const bins=await marks.evaluateAll(nodes=>nodes.map(node=>Object.fromEntries(['x','width','height'].map(k=>[k,Number(node.getAttribute(k))]))))
          assert.equal(bins.length,3)
          assert.ok(Math.abs(bins[1].width/bins[0].width-2)<1e-8,'twice-wide bin has twice the width')
          assert.ok(Math.abs(bins[1].height/bins[0].height-.5)<1e-8,'equal counts over twice the interval have half the density')
          assert.ok(bins[2].x>bins[1].x+bins[1].width,'an unprovided interval is visibly empty')
          assert.match(await card.locator('.chart-note').textContent(),/密度.*面积|面积.*数量/,'density and area semantics are disclosed')
        }
        if(chart.kind==='scatter') {
          assert.equal(await marks.count(),4,'coincident scatter points each retain their own keyboard target')
          const firstOverlap=marks.nth(2), secondOverlap=marks.nth(3)
          assert.equal(await firstOverlap.getAttribute('cx'),await secondOverlap.getAttribute('cx'))
          assert.equal(await firstOverlap.getAttribute('cy'),await secondOverlap.getAttribute('cy'))
          await firstOverlap.focus(); await firstOverlap.press('Enter')
          assert.match(await card.locator('.point-detail').textContent(),/三/)
          await secondOverlap.focus(); await secondOverlap.press('Enter')
          assert.match(await card.locator('.point-detail').textContent(),/重合/)
          await secondOverlap.hover()
          const overlapDetail=await card.locator('.point-detail').textContent()
          assert.match(overlapDetail,/三/,'pointer hover reveals the hidden coincident observation')
          assert.match(overlapDetail,/重合/,'pointer hover reveals every coincident observation')
        }
        if(chart.kind==='sankey') assert.match(await card.locator('.chart-note').textContent(),/不平衡.*12.*11/,'an imbalance must be disclosed')
        // Geometry marks are keyboard operable and reveal the exact value.
        const focusable=chart.kind==='area' ? card.locator('circle.point[tabindex="0"]').first() : card.locator(`[data-geometry="${chart.kind}"][tabindex="0"],button[data-geometry="${chart.kind}"]`).first()
        assert.equal(await focusable.count(),1,`${chart.id}: a keyboard-accessible mark`)
        await focusable.focus()
        assert.equal(await focusable.evaluate(n=>document.activeElement===n),true)
        await focusable.press('Enter')
        const detail=await card.locator('.point-detail').textContent()
        assert.ok(detail?.trim() && !detail.includes('选择数据点查看精确值'),`${chart.id}: selection exposes data`)
        if(chart.id==='share') assert.match(detail,/20(?:\.0+)?\s*%/, 'percentage uses the full original category total')
        await card.getByRole('button',{name:`${chart.title} 数据`}).click()
        const rows=await card.locator('table tbody tr').evaluateAll(nodes=>nodes.map(node=>[...node.querySelectorAll('td')].map(cell=>cell.textContent.trim())))
        for(const parts of expectedRows[chart.id]) {
          assert.ok(rows.some(row=>parts.every(part=>row.includes(part))),`${chart.id}: missing exact row ${JSON.stringify(parts)} in ${JSON.stringify(rows)}`)
        }
        await card.getByRole('button',{name:`${chart.title} 图表`}).click()
      }
      if(screenshots){
        const height=await frame.locator('main').evaluate(n=>Math.ceil(n.getBoundingClientRect().height))
        await page.waitForFunction(h=>document.querySelector('iframe').clientHeight>=h-1,height)
        await page.screenshot({path:path.join(screenshots,`analysis-families-${report.title==='趋势与占比示例'?'composition':'distribution'}-${theme}-${width}.png`),fullPage:true})
      }
    }
  }
  // Exactly one non-zero slice still fills the circle, or the ring around its
  // hole. This catches SVG arcs whose identical start/end points render empty.
  const singleSlice=structuredClone(chartFamilies[0])
  singleSlice.title='单一扇区'
  singleSlice.charts=singleSlice.charts.filter(c=>c.kind==='pie'||c.kind==='donut')
  for(const chart of singleSlice.charts)chart.slices=[{label:'唯一',value:15},{label:'零',value:0}]
  await page.evaluate(r=>window.deliver({content:[],structuredContent:{schema_version:1,report:r}}),singleSlice)
  await frame.getByRole('heading',{name:singleSlice.title,exact:true}).waitFor({timeout:5000})
  for(const kind of ['pie','donut']) {
    const path=frame.locator(`[data-chart-kind="${kind}"] [data-geometry="${kind}"]`).first()
    const fill=await path.evaluate(node=>{const center=node.ownerSVGElement.createSVGPoint();center.x=120;center.y=120;const rim=node.ownerSVGElement.createSVGPoint();rim.x=120;rim.y=30;return {center:node.isPointInFill(center),rim:node.isPointInFill(rim)}})
    assert.equal(fill.rim,true,`${kind}: full slice renders on outer ring`)
    assert.equal(fill.center,kind==='pie',`${kind}: only donut has a center hole`)
  }
  // Subnormal positive flows must not overflow the layout scale to Infinity.
  const tinyFlows=structuredClone(chartFamilies[1])
  tinyFlows.title='极小流量'
  tinyFlows.charts=tinyFlows.charts.filter(c=>c.kind==='sankey')
  tinyFlows.charts[0].links[0].value=1e-323
  tinyFlows.charts[0].links[1].value=5e-324
  tinyFlows.charts[0].links[2].value=5e-324
  await page.evaluate(r=>window.deliver({content:[],structuredContent:{schema_version:1,report:r}}),tinyFlows)
  await frame.getByRole('heading',{name:tinyFlows.title,exact:true}).waitFor({timeout:5000})
  const malformedAttributes=await frame.locator('[data-chart-kind="sankey"] svg *').evaluateAll(nodes=>nodes.flatMap(node=>[...node.attributes].filter(a=>/NaN|Infinity/.test(a.value)).map(a=>`${a.name}=${a.value}`)))
  assert.deepEqual(malformedAttributes,[],'subnormal Sankey flows must not generate NaN or Infinity SVG geometry')
  // Larger flows may scroll horizontally, but the affordance and scroll region
  // must be discoverable and operable with a keyboard at narrow widths.
  const wideFlow=structuredClone(tinyFlows)
  wideFlow.title='较宽流向'
  wideFlow.charts[0].nodes=Array.from({length:13},(_,i)=>({id:`n${i}`,label:`节点 ${i}`}))
  wideFlow.charts[0].links=Array.from({length:12},(_,i)=>({source:`n${i}`,target:`n${i+1}`,value:1}))
  await page.evaluate(r=>window.deliver({content:[],structuredContent:{schema_version:1,report:r}}),wideFlow)
  await frame.getByRole('heading',{name:wideFlow.title,exact:true}).waitFor({timeout:5000})
  const wideCard=frame.locator('[data-chart-kind="sankey"]')
  assert.match(await wideCard.locator('.chart-note').textContent(),/左右滚动/)
  const scrollRegion=wideCard.getByRole('region',{name:/图形可左右滚动/})
  assert.equal(await scrollRegion.getAttribute('tabindex'),'0')
  assert.ok(await scrollRegion.evaluate(n=>n.scrollWidth>n.clientWidth))
  await scrollRegion.focus()
  for(let i=0;i<5;i++)await scrollRegion.press('ArrowRight')
  await page.waitForTimeout(300) // Chromium can animate keyboard scrolling.
  assert.ok(await scrollRegion.evaluate(n=>n.scrollLeft)>0,'keyboard scroll reveals wide Sankey nodes')
  // A compromised or buggy host must not cause the client to fabricate a
  // plausible-looking chart from malformed data, even though normally the MCP
  // server validates these inputs first.
  const forgedCases=[
    [0,'area',c=>{c.series[0].points[0].x='2026-11-10T00:00:00'}],
    [0,'stacked_bar',c=>{c.series[1].points.pop()}],
    [0,'pie',c=>{c.slices[0].value=-1}],
    [0,'donut',c=>{c.slices.forEach(x=>x.value=0)}],
    [0,'histogram',c=>{c.bins[0].upper=c.bins[0].lower}],
    [1,'heatmap',c=>{c.cells.push({...c.cells[0]})}],
    [1,'scatter',c=>{c.points[0].x=Infinity}],
    [1,'funnel',c=>{c.stages[0].value=-1}],
    [1,'boxplot',c=>{c.boxes[0].median=c.boxes[0].max+1}],
    [1,'sankey',c=>{c.links.push({source:'done',target:'request',value:1})}]
  ]
  for(const [reportIndex,kind,damage] of forgedCases) {
    const validReport=structuredClone(chartFamilies[reportIndex])
    validReport.charts=validReport.charts.filter(c=>c.kind===kind).slice(0,1)
    await page.evaluate(r=>window.deliver({content:[],structuredContent:{schema_version:1,report:r}}),validReport)
    await frame.getByRole('heading',{name:validReport.title,exact:true}).waitFor({timeout:5000})
    const bad=structuredClone(validReport)
    damage(bad.charts[0])
    await page.evaluate(r=>window.deliver({content:[],structuredContent:{schema_version:1,report:r}}),bad)
    await frame.getByText('分析结果格式不完整，无法显示图表。').waitFor({timeout:5000})
    assert.equal(await frame.locator('.chart').count(),0,`${kind}: malformed payload must not render`)
  }
  const standalone=await browser.newPage()
  await standalone.route('http://fixture.test/app',route=>route.fulfill({status:200,contentType:'text/html',body:html}))
  await standalone.goto('http://fixture.test/app')
  assert.equal(await standalone.getByText('请在支持 MCP App 的宿主中打开此分析视图。').count(),1)
  await standalone.close()
  assert.deepEqual(pageErrors,[], 'rendering all reports must not throw in the browser')
  assert.deepEqual(externalRequests,[], 'the fallback renderer must not fetch external resources')
  console.log('MCP analysis UI passed: all chart families, exact tables, keyboard, sources, missing/negative values, themes, failures, responsive layouts')
} finally {await browser.close()}

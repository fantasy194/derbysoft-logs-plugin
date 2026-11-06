// Browser smoke for the fallback MCP App. Uses a synthetic host and no credentials.
// Run with PLAYWRIGHT_MODULE pointing to a local Playwright installation when
// Playwright is not installed in this project. CHROME_PATH may select Chromium.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const require = createRequire(import.meta.url)
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright')
const dir = path.dirname(fileURLToPath(import.meta.url))
const appHtml = await readFile(path.join(dir, '../src/derbysoft_logs/assets/settings.html'), 'utf8')
const hostHtml = `<!doctype html><html><head><meta charset="utf-8"><title>Fixture host</title></head><body style="margin:0">
<iframe title="settings" sandbox="allow-scripts allow-forms" src="/app" style="border:0;width:100%;height:100vh"></iframe>
<script>
  const calls = window.calls = [];
  window.failNextUpdate = false;
  const values = {default_environment:'uat', uat_index:'derbysoft-exchange-*', new_environment_id:'', new_environment_label:'', new_environment_kind:'custom'};
  const props = {
    default_environment:{type:'string',title:'默认环境',enum:['','uat','prod']},
    uat_index:{type:'string',title:'UAT 默认索引',description:'业务日志索引'},
    new_environment_id:{type:'string',title:'新环境 ID'},
    new_environment_label:{type:'string',title:'新环境名称'},
    new_environment_kind:{type:'string',title:'环境类型',enum:['custom','uat','prod']}
  };
  let layout = [
    {kind:'group',title:'默认环境',items:[{kind:'property',property:'default_environment'},{kind:'tool',tool:'open_log_settings'}]},
    {kind:'group',title:'UAT 环境',items:[{kind:'property',property:'uat_index'},{kind:'tool',tool:'configure_credentials__uat',description:'凭证已配置'},{kind:'tool',tool:'test_connection__uat'}]},
    {kind:'group',title:'新增环境',items:[{kind:'property',property:'new_environment_id'},{kind:'property',property:'new_environment_label'},{kind:'property',property:'new_environment_kind'},{kind:'tool',tool:'create_environment'}]}
  ];
  const read = () => ({schema:{type:'object',properties:props}, values:{...values},layout});
  const reply = (event,id,result) => event.source.postMessage({jsonrpc:'2.0',id,result},'*');
  window.addEventListener('message', async event => {
    const frame = document.querySelector('iframe');
    if (event.source !== frame.contentWindow || !event.data || event.data.jsonrpc !== '2.0') return;
    const msg = event.data;
    if (msg.method === 'ui/initialize') { calls.push({method:msg.method}); reply(event,msg.id,{protocolVersion:'2026-01-26',hostInfo:{name:'test-host',version:'1'},hostCapabilities:{},hostContext:{theme:'light'}}); return; }
    if (msg.method !== 'tools/call') return;
    const name = msg.params.name, args = msg.params.arguments;
    calls.push({method:msg.method,name,args});
    let out;
    if (name === 'settings_read') out=read();
    else if (name === 'settings_update') {
      if (window.failNextUpdate) { window.failNextUpdate=false; reply(event,msg.id,{isError:true,content:[{type:'text',text:'fixture: 保存失败'}]}); return; }
      Object.assign(values,args.set); out={values:{...values}};
    } else if (name === 'create_environment') {
      const id=values.new_environment_id;
      if (!id) { reply(event,msg.id,{isError:true,content:[{type:'text',text:'请输入环境 ID'}]}); return; }
      props[id+'_index']={type:'string',title:id+' 默认索引'}; values[id+'_index']='';
      layout = [...layout,{kind:'group',title:id+' 环境',items:[{kind:'property',property:id+'_index'}]}];
      out={created:id};
    } else if (name === 'configure_credentials__uat') out={opened:true,environment:'uat'};
    else if (name === 'test_connection__uat') out={environment:'uat',opensearch:{configured:true}};
    else { reply(event,msg.id,{isError:true,content:[{type:'text',text:'unknown action'}]}); return; }
    reply(event,msg.id,{content:[],structuredContent:out});
  });
</script></body></html>`

const browser = await chromium.launch({ headless:true, executablePath:process.env.CHROME_PATH || undefined })
try {
  const page = await browser.newPage({viewport:{width:1080,height:800}})
  const browserErrors = []
  page.on('pageerror', error => browserErrors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') browserErrors.push(message.text()) })
  await page.route('http://fixture.test/**', async route => {
    const url = new URL(route.request().url())
    await route.fulfill({status:200,contentType:'text/html; charset=utf-8',body:url.pathname === '/app' ? appHtml : hostHtml})
  })
  await page.goto('http://fixture.test/')
  const frame = page.frameLocator('iframe')
  await frame.getByRole('heading',{name:'日志连接配置'}).waitFor()
  try { await frame.getByLabel('UAT 默认索引').waitFor({timeout:5000}) }
  catch (error) { console.error('HOST CALLS:', await page.evaluate(() => window.calls)); console.error('APP:', await frame.locator('body').innerText()); throw error }
  assert.equal(await frame.getByLabel('UAT 默认索引').inputValue(),'derbysoft-exchange-*')
  assert.equal(await frame.getByRole('button',{name:'保存更改'}).isDisabled(),true)
  assert.equal(await frame.getByRole('button',{name:'open_log_settings'}).count(),0)
  assert.ok(await frame.getByText('凭证已配置').isVisible())
  if (process.env.UI_SCREENSHOT_DIR) await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR, 'settings-light.png')})

  await frame.getByLabel('UAT 默认索引').fill('logs-uat-*')
  assert.equal(await frame.getByRole('button',{name:'保存更改'}).isEnabled(),true)
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('设置已保存。').waitFor()
  const update = (await page.evaluate(() => window.calls)).find(call => call.name === 'settings_update')
  assert.deepEqual(update.args, {set:{uat_index:'logs-uat-*'}})

  await page.evaluate(() => { window.failNextUpdate = true })
  await frame.getByLabel('UAT 默认索引').fill('not-yet-saved-*')
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('fixture: 保存失败',{exact:false}).first().waitFor()
  assert.equal(await frame.getByLabel('UAT 默认索引').inputValue(),'not-yet-saved-*')
  assert.equal(await frame.getByRole('button',{name:'保存更改'}).isEnabled(),true)
  await frame.getByRole('button',{name:'重新读取'}).click()
  await frame.getByText('请先保存或放弃未保存的修改，再重新读取。').waitFor()
  assert.equal(await frame.getByLabel('UAT 默认索引').inputValue(),'not-yet-saved-*')
  await frame.getByRole('button',{name:'放弃修改'}).click()
  assert.equal(await frame.getByLabel('UAT 默认索引').inputValue(),'logs-uat-*')

  await frame.getByLabel('新环境 ID').fill('prod2')
  await frame.getByLabel('新环境名称').fill('新生产环境')
  await frame.getByRole('button',{name:'新增环境'}).click()
  await frame.getByRole('heading',{name:'prod2 环境'}).waitFor()
  const calls = await page.evaluate(() => window.calls)
  const createPos = calls.findIndex(call => call.name === 'create_environment')
  assert.ok(createPos > 0)
  assert.deepEqual(calls[createPos-1],{method:'tools/call',name:'settings_update',args:{set:{new_environment_id:'prod2',new_environment_label:'新生产环境'}}})
  assert.deepEqual(calls[createPos].args,{})

  await frame.getByRole('button',{name:'配置凭证'}).click()
  await frame.getByText('已为 uat 打开凭证配置页面。请在该页面完成输入。').waitFor()
  const credentialCall = (await page.evaluate(() => window.calls)).find(call => call.name === 'configure_credentials__uat')
  assert.deepEqual(credentialCall.args,{})
  await frame.getByRole('button',{name:'测试连接'}).click()
  await frame.getByText('OpenSearch：已配置，尚未验证查询。',{exact:false}).waitFor()
  assert.ok(await frame.getByText('StreamLog：未配置',{exact:false}).isVisible())

  await page.setViewportSize({width:375,height:800})
  const dimensions = await page.locator('iframe').evaluate(el => ({client:el.clientWidth,scroll:el.contentDocument?.documentElement.scrollWidth ?? null}))
  // The sandbox is cross-origin to the fixture host; inspect through Playwright's frame.
  const frameWidth = await frame.locator('html').evaluate(el => ({client:el.clientWidth,scroll:el.scrollWidth}))
  assert.equal(dimensions.client,375)
  assert.ok(frameWidth.scroll <= frameWidth.client + 1, JSON.stringify(frameWidth))
  if (process.env.UI_SCREENSHOT_DIR) {
    await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR, 'settings-narrow.png')})
    await page.evaluate(() => document.querySelector('iframe').contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/host-context-changed',params:{theme:'dark'}},'*'))
    await frame.locator('html[data-theme="dark"]').waitFor()
    await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR, 'settings-dark.png')})
  }
  assert.ok((await page.evaluate(() => window.calls)).some(call => call.method === 'ui/initialize'))
  assert.deepEqual(browserErrors,[])
  console.log('MCP App UI smoke passed: sandbox handshake, save, failed-save retention, actions, environment binding, narrow layout')
} finally { await browser.close() }

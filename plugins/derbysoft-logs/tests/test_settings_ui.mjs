// Test the real MCP App in an isolated synthetic host; no credentials or network.
// PLAYWRIGHT_MODULE may point to a local Playwright installation; CHROME_PATH is optional.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const require = createRequire(import.meta.url)
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright')
const dir = path.dirname(fileURLToPath(import.meta.url))
const appHtml = await readFile(path.join(dir, '../src/derbysoft_logs/assets/settings.html'), 'utf8')
const credentialsHtml = await readFile(path.join(dir, '../src/derbysoft_logs/assets/secret-entry.html'), 'utf8')
const hostHtml = `<!doctype html><html><head><meta charset="utf-8"><title>Fixture host</title></head><body style="margin:0">
<iframe title="settings" sandbox="allow-scripts allow-forms" src="/app" style="border:0;width:100%;height:100vh"></iframe>
<script>
  const calls = window.calls = [];
  window.failNextUpdate = false;
  const values = {default_environment:'uat',new_environment_id:'',new_environment_label:'',new_environment_kind:'custom'};
  const props = {
    default_environment:{type:'string',title:'默认环境',enum:['不设置（查询时询问）','uat','prod']},
    new_environment_id:{type:'string',title:'新环境 ID'},
    new_environment_label:{type:'string',title:'显示名称'},
    new_environment_kind:{type:'string',title:'环境类型',enum:['dev','qa','uat','prod','custom']}
  };
  const layout = [
    {kind:'group',title:'环境选择',items:[{kind:'property',property:'default_environment'},{kind:'tool',tool:'open_log_settings'}]},
    {kind:'group',title:'新增或迁移环境',items:[{kind:'property',property:'new_environment_id'},{kind:'property',property:'new_environment_label'},{kind:'property',property:'new_environment_kind'},{kind:'tool',tool:'create_environment'}]}
  ];
  function addEnvironment(id,label) {
    const prefix='env__'+id+'__', items=[];
    const fields=[['label','显示名称',label],['kind','环境类型',id==='uat'?'uat':'prod'],
      ['opensearch__url','OpenSearch 地址','https://'+id+'.example.test'],
      ['opensearch__username','OpenSearch 用户名','reader'],
      ['opensearch__default_index','OpenSearch 默认业务索引','logs-'+id+'-*'],
      ['streamlog__url','StreamLog 地址','https://stream.example.test'],
      ['loki__url','Loki 地址','https://loki.example.test'],
      ['loki__username','Loki 用户名','reader'],['loki__auth_type','Loki 认证方式','basic'],
      ['loki__tenant_id','Loki 租户 ID',''],['loki__service_label','Loki 应用标签','app']];
    for(const [key,title,value] of fields){
      const name=prefix+key; props[name]={type:'string',title}; values[name]=value;
      if(key==='kind')props[name].enum=['dev','qa','uat','prod','custom'];
      if(key==='loki__auth_type')props[name].enum=['basic','bearer','none'];
      items.push({kind:'property',property:name});
    }
    items.push({kind:'tool',tool:'configure_credentials__'+id,description:'凭证状态：已保存'},
               {kind:'tool',tool:'test_connection__'+id});
    layout.push({kind:'group',title:label+'（'+id+'）',items});
  }
  addEnvironment('uat','测试环境');addEnvironment('prod','生产环境');
  const read = () => ({schema:{type:'object',properties:props},values:{...values},layout});
  const reply = (event,id,result) => event.source.postMessage({jsonrpc:'2.0',id,result},'*');
  window.addEventListener('message', async event => {
    if(event.source !== document.querySelector('iframe').contentWindow || !event.data || event.data.jsonrpc !== '2.0')return;
    const msg=event.data;
    if(msg.method==='ui/initialize'){calls.push({method:msg.method});reply(event,msg.id,{protocolVersion:'2026-01-26',hostInfo:{name:'test-host',version:'1'},hostCapabilities:{},hostContext:{theme:'light'}});return;}
    if(msg.method!=='tools/call')return;
    const name=msg.params.name,args=msg.params.arguments;calls.push({method:msg.method,name,args});let out;
    if(name==='settings_read')out=read();
    else if(name==='settings_update'){
      if(window.failNextUpdate){window.failNextUpdate=false;reply(event,msg.id,{isError:true,content:[{type:'text',text:'fixture: 保存失败'}]});return;}
      for(const [key,value] of Object.entries(args.set))values[key]=key.endsWith('__url')?value.replace(/\\/+$/,''):value;
      out={values:{...values}};
    } else if(name==='create_environment'){
      const id=values.new_environment_id;if(!id){reply(event,msg.id,{isError:true,content:[{type:'text',text:'请输入环境 ID'}]});return;}
      addEnvironment(id,values.new_environment_label||id);props.default_environment.enum.push(id);
      values.new_environment_id='';values.new_environment_label='';values.new_environment_kind='custom';out={environment:id,created:true,migrated:false};
    } else if(name.startsWith('configure_credentials__'))out={opened:true,environment:name.slice('configure_credentials__'.length)};
    else if(name.startsWith('test_connection__'))out={environment:name.slice('test_connection__'.length),opensearch:{configured:true}};
    else {reply(event,msg.id,{isError:true,content:[{type:'text',text:'unknown action'}]});return;}
    reply(event,msg.id,{content:[],structuredContent:out});
  });
</script></body></html>`

const browser = await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH || undefined})
try {
  const page = await browser.newPage({viewport:{width:410,height:780}})
  const browserErrors=[]
  page.on('pageerror',error=>browserErrors.push(error.message))
  page.on('console',message=>{if(message.type()==='error')browserErrors.push(message.text())})
  await page.route('http://fixture.test/**',async route=>{
    const url=new URL(route.request().url())
    await route.fulfill({status:200,contentType:'text/html; charset=utf-8',body:url.pathname==='/app'?appHtml:hostHtml})
  })
  await page.goto('http://fixture.test/')
  const frame=page.frameLocator('iframe')
  await frame.getByRole('heading',{name:'日志设置'}).waitFor()
  await frame.getByLabel('编辑环境').waitFor()
  assert.equal(await frame.getByLabel('编辑环境').inputValue(),'uat')
  assert.equal(await frame.getByLabel('默认环境').inputValue(),'uat')
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'logs-uat-*')
  assert.equal(await frame.getByRole('button',{name:'保存更改'}).isDisabled(),true)
  assert.equal(await frame.getByRole('button',{name:'open_log_settings'}).count(),0)
  assert.equal(await frame.getByText('管理环境、服务连接和默认索引',{exact:false}).count(),0)
  if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,'settings-410-light.png')})

  await frame.getByLabel('默认业务索引').fill('pending-uat-*')
  await frame.getByLabel('编辑环境').selectOption('prod')
  assert.equal(await frame.getByLabel('默认环境').inputValue(),'uat')
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'logs-prod-*')
  await frame.getByLabel('默认业务索引').fill('pending-prod-*')
  await frame.getByLabel('编辑环境').selectOption('uat')
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'pending-uat-*')
  assert.equal(await frame.getByLabel('默认环境').inputValue(),'uat')

  await page.evaluate(()=>{window.failNextUpdate=true})
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('fixture: 保存失败',{exact:false}).first().waitFor()
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'pending-uat-*')
  await frame.getByLabel('编辑环境').selectOption('prod')
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'pending-prod-*')
  assert.equal(await frame.getByRole('button',{name:'保存更改'}).isEnabled(),true)
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByRole('button',{name:'保存更改'}).waitFor({state:'visible'})
  await frame.getByText('已保存',{exact:true}).waitFor()
  const save=(await page.evaluate(()=>window.calls)).filter(call=>call.name==='settings_update').at(-1)
  assert.deepEqual(save.args,{set:{env__uat__opensearch__default_index:'pending-uat-*',env__prod__opensearch__default_index:'pending-prod-*'}})

  await frame.getByLabel('编辑环境').selectOption('uat')
  await frame.getByLabel('默认业务索引').fill('still-unsaved-uat-*')
  await frame.getByLabel('编辑环境').selectOption('prod')
  await frame.getByLabel('默认业务索引').fill('saved-for-prod-*')
  await frame.getByRole('button',{name:'配置凭证'}).click()
  await frame.getByText('已为 prod 打开凭证配置页面。请在该页面完成输入。').waitFor()
  const calls=await page.evaluate(()=>window.calls)
  const credentialPos=calls.findIndex(call=>call.name==='configure_credentials__prod')
  assert.deepEqual(calls[credentialPos-1].args,{set:{env__prod__opensearch__default_index:'saved-for-prod-*'}})
  assert.deepEqual(calls[credentialPos].args,{})
  await frame.getByLabel('编辑环境').selectOption('uat')
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'still-unsaved-uat-*')
  assert.equal(await frame.getByRole('button',{name:'保存更改'}).isEnabled(),true)

  await frame.getByRole('button',{name:'新增',exact:true}).click()
  await frame.getByLabel('新环境 ID').fill('qa')
  await frame.getByLabel('显示名称').fill('QA')
  await frame.getByRole('button',{name:'新增环境'}).click()
  await frame.getByText('已创建环境 qa。').waitFor()
  assert.equal(await frame.getByLabel('编辑环境').inputValue(),'qa')
  assert.equal(await frame.getByLabel('默认环境').inputValue(),'uat')
  await frame.getByLabel('编辑环境').selectOption('uat')
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'still-unsaved-uat-*')
  await frame.getByRole('button',{name:'放弃修改'}).click()
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'pending-uat-*')

  await frame.locator('#field-env__uat__opensearch__url').fill('https://uat.example.test/')
  await frame.getByText('更改地址会移除旧凭证；未同时修改的默认索引也会清除。').waitFor()
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('已保存',{exact:true}).waitFor()
  assert.equal(await frame.locator('#field-env__uat__opensearch__url').inputValue(),'https://uat.example.test')

  await page.setViewportSize({width:375,height:780})
  let dimensions=await frame.locator('html').evaluate(el=>({client:el.clientWidth,scroll:el.scrollWidth}))
  assert.ok(dimensions.scroll<=dimensions.client+1,JSON.stringify(dimensions))
  if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,'settings-375-light.png')})
  await page.evaluate(()=>document.querySelector('iframe').contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/host-context-changed',params:{theme:'dark'}},'*'))
  await frame.locator('html[data-theme="dark"]').waitFor()
  if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,'settings-375-dark.png')})
  await page.setViewportSize({width:410,height:780})
  if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,'settings-410-dark.png')})
  await page.setViewportSize({width:1080,height:800})
  dimensions=await frame.locator('html').evaluate(el=>({client:el.clientWidth,scroll:el.scrollWidth}))
  assert.ok(dimensions.scroll<=dimensions.client+1,JSON.stringify(dimensions))
  assert.deepEqual(browserErrors,[])
  const credentialPage=await browser.newPage({viewport:{width:410,height:780},colorScheme:'light'})
  const credentialRequests=[]
  const credentialErrors=[]
  credentialPage.on('pageerror',error=>credentialErrors.push(error.message))
  await credentialPage.route('http://credential.test/**',async route=>{
    const url=new URL(route.request().url())
    if(url.pathname==='/state'){
      credentialRequests.push({path:url.pathname,token:route.request().headers()['x-setup-token']})
      await route.fulfill({status:200,json:{environment:{id:'uat',label:'测试环境',services:{
        opensearch:{url:'https://uat.example.test',username:'reader',has_secret:true},
        streamlog:{url:'https://stream.example.test',has_secret:false},
        loki:{url:'https://loki.example.test',auth_type:'none',has_secret:false}
      }}}})
    }else if(url.pathname==='/credentials'){
      credentialRequests.push({path:url.pathname,token:route.request().headers()['x-setup-token'],body:route.request().postDataJSON()})
      await route.fulfill({status:200,json:{saved:true}})
    }else await route.fulfill({status:200,contentType:'text/html; charset=utf-8',body:credentialsHtml})
  })
  await credentialPage.goto('http://credential.test/#fixture-token')
  await credentialPage.getByText('测试环境（uat）').waitFor()
  assert.equal(new URL(credentialPage.url()).hash,'')
  assert.ok(await credentialPage.getByText('无需认证').isVisible())
  assert.equal(await credentialPage.locator('input[type=password]').count(),2)
  if(process.env.UI_SCREENSHOT_DIR)await credentialPage.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,'credentials-410-light.png')})
  const openSearch=credentialPage.locator('section').filter({has:credentialPage.getByRole('heading',{name:'OpenSearch'})})
  await openSearch.getByLabel('密码').fill('fixture-secret')
  await openSearch.getByRole('button',{name:'更新凭证'}).click()
  await openSearch.getByText('凭证已保存').waitFor({state:'attached'})
  assert.equal(await openSearch.getByLabel('密码').inputValue(),'')
  assert.deepEqual(credentialRequests.at(-1),{path:'/credentials',token:'fixture-token',body:{service:'opensearch',secret:'fixture-secret'}})
  await credentialPage.emulateMedia({colorScheme:'dark'})
  if(process.env.UI_SCREENSHOT_DIR)await credentialPage.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,'credentials-410-dark.png')})
  await credentialPage.setViewportSize({width:375,height:780})
  const credentialWidth=await credentialPage.locator('html').evaluate(el=>({client:el.clientWidth,scroll:el.scrollWidth}))
  assert.ok(credentialWidth.scroll<=credentialWidth.client+1,JSON.stringify(credentialWidth))
  assert.deepEqual(credentialErrors,[])
  await credentialPage.close()
  console.log('MCP App UI passed: multi-environment editing, default isolation, dirty retention, scoped action, creation, light/dark/narrow layout')
  console.log('Credential UI passed: environment identity, no-auth mode, secret save and clearing, URL fragment removal, light/dark/narrow layout')
}finally{await browser.close()}

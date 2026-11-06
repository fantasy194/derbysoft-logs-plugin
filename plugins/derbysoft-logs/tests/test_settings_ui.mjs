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
  window.failNextDelete = false;
  window.failNextRead = false;
  const values = {default_environment:'uat',new_environment_id:''};
  const props = {
    default_environment:{type:'string',title:'默认环境',enum:['不设置（查询时询问）','uat','prod']},
    new_environment_id:{type:'string',title:'环境名称'}
  };
  const layout = [
    {kind:'group',title:'环境选择',items:[{kind:'property',property:'default_environment'},{kind:'tool',tool:'open_log_settings'}]},
    {kind:'group',title:'新增环境',items:[{kind:'property',property:'new_environment_id'},{kind:'tool',tool:'create_environment'}]}
  ];
  function addEnvironment(id) {
    const prefix='env__'+id+'__', items=[];
    const fields=[['opensearch__url','OpenSearch 地址','https://'+id+'.example.test'],
      ['opensearch__username','OpenSearch 用户名','reader'],
      ['opensearch__default_index','OpenSearch 默认业务索引','logs-'+id+'-*'],
      ['streamlog__url','StreamLog 地址','https://stream.example.test'],
      ['loki__url','Loki 地址','https://loki.example.test'],
      ['loki__username','Loki 用户名','reader'],['loki__auth_type','Loki 认证方式','basic'],
      ['loki__tenant_id','Loki 租户 ID',''],['loki__service_label','Loki 应用标签','app']];
    for(const [key,title,value] of fields){
      const name=prefix+key; props[name]={type:'string',title}; values[name]=value;
      if(key==='loki__auth_type')props[name].enum=['basic','bearer','none'];
      items.push({kind:'property',property:name});
    }
    items.push({kind:'tool',tool:'configure_credentials__'+id,description:'凭证状态：已保存'},
               {kind:'tool',tool:'test_connection__'+id},{kind:'tool',tool:'request_delete__'+id});
    layout.push({kind:'group',title:id,items});
  }
  addEnvironment('uat');addEnvironment('prod');
  const read = () => ({schema:{type:'object',properties:props},values:{...values},layout});
  const reply = (event,id,result) => event.source.postMessage({jsonrpc:'2.0',id,result},'*');
  window.addEventListener('message', async event => {
    if(event.source !== document.querySelector('iframe').contentWindow || !event.data || event.data.jsonrpc !== '2.0')return;
    const msg=event.data;
    if(msg.method==='ui/initialize'){
      calls.push({method:msg.method});
      if(new URL(location.href).searchParams.has('early'))event.source.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:{content:[],structuredContent:{action:'confirm_delete',environment:'prod',default_environment:false}}},'*');
      reply(event,msg.id,{protocolVersion:'2026-01-26',hostInfo:{name:'test-host',version:'1'},hostCapabilities:{},hostContext:{theme:'light'}});return;
    }
    if(msg.method!=='tools/call')return;
    const name=msg.params.name,args=msg.params.arguments;calls.push({method:msg.method,name,args});let out;
    if(name==='settings_read'){
      if(window.failNextRead){window.failNextRead=false;reply(event,msg.id,{isError:true,content:[{type:'text',text:'fixture: 刷新失败'}]});return;}
      out=read();
    }
    else if(name==='settings_update'){
      if(window.failNextUpdate){window.failNextUpdate=false;reply(event,msg.id,{isError:true,content:[{type:'text',text:'fixture: 保存失败'}]});return;}
      for(const [key,value] of Object.entries(args.set))values[key]=key.endsWith('__url')?value.replace(/\\/+$/,''):value;
      out={values:{...values}};
    } else if(name==='create_environment'){
      const id=values.new_environment_id;if(!id){reply(event,msg.id,{isError:true,content:[{type:'text',text:'请输入环境 ID'}]});return;}
      addEnvironment(id);props.default_environment.enum.push(id);
      values.new_environment_id='';out={environment:id,created:true};
    } else if(name.startsWith('configure_credentials__'))out={opened:true,environment:name.slice('configure_credentials__'.length)};
    else if(name.startsWith('test_connection__'))out={environment:name.slice('test_connection__'.length),opensearch:{configured:true}};
    else if(name.startsWith('request_delete__')){
      const environment=name.slice('request_delete__'.length);
      out={action:'confirm_delete',environment,default_environment:values.default_environment===environment};
    }else if(name==='delete_environment'){
      if(window.failNextDelete){window.failNextDelete=false;reply(event,msg.id,{isError:true,content:[{type:'text',text:'fixture: 删除失败'}]});return;}
      if(args.confirmation!==args.environment){reply(event,msg.id,{isError:true,content:[{type:'text',text:'名称不匹配'}]});return;}
      const index=layout.findIndex(group=>(group.items||[]).some(item=>item.tool==='request_delete__'+args.environment));
      if(index<0){reply(event,msg.id,{isError:true,content:[{type:'text',text:'环境不存在'}]});return;}
      for(const item of layout[index].items)if(item.kind==='property'){delete props[item.property];delete values[item.property];}
      layout.splice(index,1);props.default_environment.enum=props.default_environment.enum.filter(x=>x!==args.environment);
      const defaultCleared=values.default_environment===args.environment;
      if(defaultCleared)values.default_environment='不设置（查询时询问）';
      out={environment:args.environment,deleted:true,default_cleared:defaultCleared};
    }
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
  assert.equal(await frame.getByRole('heading',{name:'新增环境',exact:true}).locator('..').locator('..').locator('input,select').count(),1)
  if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,'settings-create-410-light.png')})
  await frame.getByLabel('环境名称',{exact:true}).fill('qa')
  assert.equal(await frame.getByLabel('显示名称').count(),0)
  assert.equal(await frame.getByLabel('环境类型').count(),0)
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

  // Delete a default environment without committing its draft or another environment's draft.
  await frame.getByLabel('默认业务索引').fill('draft-uat-*')
  await frame.getByLabel('编辑环境').selectOption('prod')
  await frame.getByLabel('默认业务索引').fill('draft-prod-*')
  await frame.getByLabel('编辑环境').selectOption('uat')
  let beforeDelete=(await page.evaluate(()=>window.calls)).length
  await frame.getByRole('button',{name:'删除',exact:true}).click()
  const dialog=frame.getByRole('dialog',{name:'删除环境'})
  await dialog.waitFor()
  assert.ok(await dialog.getByText('这是默认环境，删除后会清空默认环境。').isVisible())
  assert.ok(await dialog.getByText('uat',{exact:true}).isVisible())
  assert.deepEqual((await page.evaluate(()=>window.calls)).slice(beforeDelete).map(call=>call.name),['request_delete__uat'])
  if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,'settings-delete-410-light.png')})
  await page.evaluate(()=>document.querySelector('iframe').contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/host-context-changed',params:{theme:'dark'}},'*'))
  await frame.locator('html[data-theme="dark"]').waitFor()
  if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,'settings-delete-410-dark.png')})
  await page.evaluate(()=>document.querySelector('iframe').contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/host-context-changed',params:{theme:'light'}},'*'))
  await dialog.getByRole('button',{name:'取消'}).click()
  assert.equal((await page.evaluate(()=>window.calls)).filter(call=>call.name==='delete_environment').length,0)
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'draft-uat-*')

  await frame.getByRole('button',{name:'删除',exact:true}).click()
  await dialog.getByLabel('输入环境名称确认').fill('UAT')
  assert.equal(await dialog.getByRole('button',{name:'删除环境'}).isDisabled(),true)
  assert.equal((await page.evaluate(()=>window.calls)).filter(call=>call.name==='delete_environment').length,0)
  await dialog.getByLabel('输入环境名称确认').fill('uat')
  await page.evaluate(()=>{window.failNextDelete=true})
  await dialog.getByRole('button',{name:'删除环境'}).click()
  await dialog.getByText('fixture: 删除失败',{exact:false}).waitFor()
  assert.equal(await dialog.getByLabel('输入环境名称确认').inputValue(),'uat')
  assert.equal(await dialog.getByRole('button',{name:'删除环境'}).isEnabled(),true)
  await dialog.getByRole('button',{name:'删除环境'}).click()
  await frame.getByText('已删除环境 uat。').waitFor()
  assert.equal(await frame.getByLabel('默认环境').inputValue(),'不设置（查询时询问）')
  assert.equal(await frame.getByLabel('编辑环境').inputValue(),'prod')
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'draft-prod-*')
  assert.equal(await frame.getByRole('button',{name:'保存更改'}).isEnabled(),true)
  assert.equal(await frame.getByLabel('编辑环境').locator('option[value="uat"]').count(),0)
  const deletedUat=(await page.evaluate(()=>window.calls)).filter(call=>call.name==='delete_environment').at(-1)
  assert.deepEqual(deletedUat.args,{environment:'uat',confirmation:'uat'})

  // A native action can target another environment; it must not save the visible draft.
  await frame.getByLabel('默认环境').selectOption('qa')
  beforeDelete=(await page.evaluate(()=>window.calls)).length
  await page.evaluate(()=>document.querySelector('iframe').contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:{content:[],structuredContent:{action:'confirm_delete',environment:'qa',default_environment:false}}},'*'))
  await dialog.waitFor()
  assert.ok(await dialog.getByText('qa',{exact:true}).isVisible())
  assert.equal(await dialog.getByText('这是默认环境，删除后会清空默认环境。').count(),0)
  assert.ok(await dialog.getByText('未保存的默认环境选择也会清除。').isVisible())
  await dialog.getByLabel('输入环境名称确认').fill('qa')
  await dialog.getByRole('button',{name:'删除环境'}).click()
  await frame.getByText('已删除环境 qa。').waitFor()
  assert.equal(await frame.getByLabel('编辑环境').inputValue(),'prod')
  assert.equal(await frame.getByLabel('默认环境').inputValue(),'不设置（查询时询问）')
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'draft-prod-*')
  const afterNative=(await page.evaluate(()=>window.calls)).slice(beforeDelete)
  assert.deepEqual(afterNative.map(call=>call.name),['delete_environment','settings_read'])
  assert.deepEqual(afterNative[0].args,{environment:'qa',confirmation:'qa'})
  assert.equal(await frame.getByLabel('编辑环境').locator('option[value="qa"]').count(),0)

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
  // Native host can notify the app before ui/initialize or settings_read completes.
  await page.goto('http://fixture.test/?early=1')
  const early=page.frameLocator('iframe').getByRole('dialog',{name:'删除环境'})
  await early.waitFor()
  assert.ok(await early.getByText('prod',{exact:true}).isVisible())
  await early.getByRole('button',{name:'取消'}).click()
  assert.equal((await page.evaluate(()=>window.calls)).filter(call=>call.name==='delete_environment').length,0)
  await page.frameLocator('iframe').locator('html').evaluate(()=>window.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:{structuredContent:{action:'confirm_delete',environment:'uat',default_environment:true}}},'*'))
  await page.waitForTimeout(100)
  assert.equal(await early.isVisible(),false)
  await page.evaluate(()=>document.querySelector('iframe').contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:{structuredContent:{action:'confirm_delete',environment:'../bad',default_environment:'true'}}},'*'))
  await page.waitForTimeout(100)
  assert.equal(await early.isVisible(),false)
  // If deletion succeeded but refresh failed, never resend deletion and retain other drafts.
  const earlyFrame=page.frameLocator('iframe')
  await earlyFrame.getByLabel('编辑环境').selectOption('prod')
  await earlyFrame.getByLabel('默认业务索引').fill('retained-after-refresh-*')
  await earlyFrame.getByLabel('编辑环境').selectOption('uat')
  await earlyFrame.getByRole('button',{name:'删除',exact:true}).click()
  await early.waitFor()
  await early.getByLabel('输入环境名称确认').fill('uat')
  await page.evaluate(()=>{window.failNextRead=true})
  await early.getByRole('button',{name:'删除环境'}).click()
  await earlyFrame.getByText('环境 uat 已删除，但刷新失败；请刷新设置。').waitFor()
  assert.equal(await earlyFrame.getByRole('button',{name:'保存更改'}).isDisabled(),true)
  await earlyFrame.getByRole('button',{name:'刷新'}).click()
  await earlyFrame.getByLabel('编辑环境').waitFor()
  assert.equal(await earlyFrame.getByLabel('编辑环境').inputValue(),'prod')
  assert.equal(await earlyFrame.getByLabel('默认业务索引').inputValue(),'retained-after-refresh-*')
  assert.equal((await page.evaluate(()=>window.calls)).filter(call=>call.name==='delete_environment').length,1)
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
  await credentialPage.getByText('uat',{exact:true}).waitFor()
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
  console.log('MCP App UI passed: multi-environment editing, native/early deletion, cancellation, exact confirmation, retry, default clearing, unrelated drafts, light/dark/narrow layout')
  console.log('Credential UI passed: environment identity, no-auth mode, secret save and clearing, URL fragment removal, light/dark/narrow layout')
}finally{await browser.close()}

// Test the real MCP App in an isolated synthetic host; no credentials or network.
// PLAYWRIGHT_MODULE may point to a local Playwright installation; CHROME_PATH is optional.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { constants, createDecipheriv, generateKeyPairSync, privateDecrypt } from 'node:crypto'

const require = createRequire(import.meta.url)
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright')
const dir = path.dirname(fileURLToPath(import.meta.url))
const appHtml = await readFile(path.join(dir, '../src/derbysoft_logs/assets/settings.html'), 'utf8')
const { publicKey, privateKey } = generateKeyPairSync('rsa',{modulusLength:2048})
const publicSpki = publicKey.export({type:'spki',format:'der'}).toString('base64')
const decryptedSubmissions = []
const hostHtml = `<!doctype html><html><head><meta charset="utf-8"><title>Fixture host</title></head><body style="margin:0">
<iframe title="settings" sandbox="allow-scripts allow-forms" src="/app" style="border:0;width:100%;height:100vh"></iframe>
<script>
  const calls = window.calls = [];
  window.failNextUpdate = false;
  window.failNextDelete = false;
  window.failNextRead = false;
  window.savedWithoutValues = false;
  window.loseNextResponse = false;
  const publicSpki=${JSON.stringify(publicSpki)}, sessions={};let sessionNumber=0, revisionNumber=0;
  const revision=()=>String(++revisionNumber).padStart(64,'0');
  const metadata={settings_revision:revision(),environments:{}};
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
    metadata.environments[id]={revision:revision(),storage:'file',opensearch:{has_secret:true},streamlog:{has_secret:false},loki:{has_secret:false}};
  }
  addEnvironment('uat');addEnvironment('prod');
  window.externalChange=id=>{metadata.environments[id].revision=revision();values['env__'+id+'__opensearch__url']='https://changed-'+id+'.example.test';};
  const read = () => ({schema:{type:'object',properties:props},values:{...values},layout,metadata});
  const reply = (event,id,result) => event.source.postMessage({jsonrpc:'2.0',id,result},'*');
  window.addEventListener('message', async event => {
    if(event.source !== document.querySelector('iframe').contentWindow || !event.data || event.data.jsonrpc !== '2.0')return;
    const msg=event.data;
    if(msg.method==='ui/initialize'){
      calls.push({method:msg.method});
      const early=new URL(location.href).searchParams.get('early');
      if(early){
        const action=early==='edit'?{action:'edit_environment',environment:'prod'}:early==='result'?{action:'connection_result',environment:'uat',opensearch:{configured:true,index_query_status:'ok',index:'logs-uat-*',http_status:403},streamlog:{configured:true},loki:{configured:true,labels_accessible:true}}:{action:'confirm_delete',environment:'prod',default_environment:false};
        event.source.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:{content:[],structuredContent:action}},'*');
      }
      reply(event,msg.id,{protocolVersion:'2026-01-26',hostInfo:{name:'test-host',version:'1'},hostCapabilities:{},hostContext:{theme:'light'}});return;
    }
    if(msg.method!=='tools/call')return;
    const name=msg.params.name,args=msg.params.arguments;calls.push({method:msg.method,name,args});let out;
    if(name==='settings_read'){
      if(window.failNextRead){window.failNextRead=false;reply(event,msg.id,{isError:true,content:[{type:'text',text:'fixture: 刷新失败'}]});return;}
      out=read();
    }
    else if(name==='settings_update'){reply(event,msg.id,{isError:true,content:[{type:'text',text:'UI 必须安全保存'}]});return;}
    else if(name==='begin_settings_save'){
      if(args.expected_settings_revision!==metadata.settings_revision||args.environments.some(id=>args.expected_revisions[id]!==metadata.environments[id]?.revision)){
        reply(event,msg.id,{isError:true,content:[{type:'text',text:'环境已改变，请刷新页面后重新输入凭证。'}]});return;
      }
      const id='session-'+(++sessionNumber);sessions[id]={environments:args.environments};out={session_id:id,public_key_spki:publicSpki,expires_in_seconds:600};
    }else if(name==='save_settings_secure'){
      if(window.failNextUpdate){window.failNextUpdate=false;reply(event,msg.id,{isError:true,content:[{type:'text',text:'fixture: 保存失败'}]});return;}
      if(!sessions[args.session_id]){reply(event,msg.id,{isError:true,content:[{type:'text',text:'会话无效'}]});return;}
      const decoded=await window.__decryptFixture(args);delete sessions[args.session_id];
      for(const [key,value] of Object.entries(decoded.set)){
        values[key]=key.endsWith('__url')?value.replace(/\\/+$/,''):value;
        const ids=Object.keys(metadata.environments).sort((a,b)=>b.length-a.length);
        const id=ids.find(name=>key.startsWith('env__'+name+'__'));
        if(id)metadata.environments[id].revision=revision();
        else if(key==='default_environment'||key==='new_environment_id')metadata.settings_revision=revision();
      }
      for(const [id,services] of Object.entries(decoded.savedServices)){
        for(const service of services)metadata.environments[id][service].has_secret=true;
        metadata.environments[id].revision=revision();
      }
      if(window.loseNextResponse){window.loseNextResponse=false;event.source.postMessage({jsonrpc:'2.0',id:msg.id,error:{code:-32603,message:'fixture: response lost'}},'*');return;}
      if(window.savedWithoutValues){window.savedWithoutValues=false;out={saved:true,refresh_required:true};}
      else out={saved:true,values:{...values}};
    } else if(name==='create_environment'){
      const id=values.new_environment_id;if(!id){reply(event,msg.id,{isError:true,content:[{type:'text',text:'请输入环境 ID'}]});return;}
      addEnvironment(id);props.default_environment.enum.push(id);
      values.new_environment_id='';metadata.settings_revision=revision();out={environment:id,created:true};
    } else if(name.startsWith('configure_credentials__'))out={action:'edit_environment',environment:name.slice('configure_credentials__'.length)};
    else if(name.startsWith('test_connection__'))out={action:'connection_result',environment:name.slice('test_connection__'.length),opensearch:{configured:true,index_query_status:'ok',index:'logs-prod-*',index_query_accessible:true},streamlog:{configured:true},loki:{configured:true,labels_accessible:true}};
    else if(name.startsWith('request_delete__')){
      const environment=name.slice('request_delete__'.length);
      out={action:'confirm_delete',environment,default_environment:values.default_environment===environment};
    }else if(name==='delete_environment'){
      if(window.failNextDelete){window.failNextDelete=false;reply(event,msg.id,{isError:true,content:[{type:'text',text:'fixture: 删除失败'}]});return;}
      if(args.confirmation!==args.environment){reply(event,msg.id,{isError:true,content:[{type:'text',text:'名称不匹配'}]});return;}
      const index=layout.findIndex(group=>(group.items||[]).some(item=>item.tool==='request_delete__'+args.environment));
      if(index<0){reply(event,msg.id,{isError:true,content:[{type:'text',text:'环境不存在'}]});return;}
      for(const item of layout[index].items)if(item.kind==='property'){delete props[item.property];delete values[item.property];}
      layout.splice(index,1);delete metadata.environments[args.environment];props.default_environment.enum=props.default_environment.enum.filter(x=>x!==args.environment);
      const defaultCleared=values.default_environment===args.environment;
      if(defaultCleared){values.default_environment='不设置（查询时询问）';metadata.settings_revision=revision();}
      out={environment:args.environment,deleted:true,default_cleared:defaultCleared};
    }
    else {reply(event,msg.id,{isError:true,content:[{type:'text',text:'unknown action'}]});return;}
    reply(event,msg.id,{content:[],structuredContent:out});
  });
</script></body></html>`

const browser = await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH || undefined})
try {
  const page = await browser.newPage({viewport:{width:410,height:780}})
  await page.exposeFunction('__decryptFixture', args => {
    const key=privateDecrypt({key:privateKey,padding:constants.RSA_PKCS1_OAEP_PADDING,oaepHash:'sha256'},Buffer.from(args.encrypted_key,'base64'))
    const ciphertext=Buffer.from(args.ciphertext,'base64')
    const decipher=createDecipheriv('aes-256-gcm',key,Buffer.from(args.iv,'base64'))
    decipher.setAAD(Buffer.from(args.session_id,'utf8')); decipher.setAuthTag(ciphertext.subarray(-16))
    const payload=JSON.parse(Buffer.concat([decipher.update(ciphertext.subarray(0,-16)),decipher.final()]).toString('utf8'))
    decryptedSubmissions.push(payload)
    return {set:payload.set,savedServices:Object.fromEntries(Object.entries(payload.secrets).map(([id,services])=>[id,Object.keys(services)]))}
  })
  const browserErrors=[]
  page.on('pageerror',error=>browserErrors.push(error.message))
  page.on('console',message=>{if(message.type()==='error')browserErrors.push(message.text())})
  await page.route('http://localhost/**',async route=>{
    const url=new URL(route.request().url())
    await route.fulfill({status:200,contentType:'text/html; charset=utf-8',body:url.pathname==='/app'?appHtml:hostHtml})
  })
  await page.goto('http://localhost/')
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
  const save=decryptedSubmissions.at(-1)
  assert.deepEqual(save,{set:{env__uat__opensearch__default_index:'pending-uat-*',env__prod__opensearch__default_index:'pending-prod-*'},secrets:{}})

  await frame.getByLabel('编辑环境').selectOption('uat')
  await frame.getByLabel('默认业务索引').fill('still-unsaved-uat-*')
  await frame.getByLabel('编辑环境').selectOption('prod')
  await frame.getByLabel('默认业务索引').fill('saved-for-prod-*')
  await frame.locator('#secret-prod-opensearch').fill('prod-密$secret')
  assert.equal(await frame.getByRole('button',{name:'配置凭证'}).count(),0)
  await frame.getByRole('button',{name:'保存并测试'}).click()
  const connectionDialog=frame.getByRole('dialog',{name:'连接结果'})
  await connectionDialog.getByText('默认索引查询通过').waitFor()
  assert.ok(await connectionDialog.getByText('已配置；查询权限尚未验证').isVisible())
  assert.ok(await connectionDialog.getByText('标签接口可访问').isVisible())
  if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,'settings-connection-410-light.png')})
  await page.evaluate(()=>document.querySelector('iframe').contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/host-context-changed',params:{theme:'dark'}},'*'))
  await frame.locator('html[data-theme="dark"]').waitFor()
  if(process.env.UI_SCREENSHOT_DIR)await page.screenshot({path:path.join(process.env.UI_SCREENSHOT_DIR,'settings-connection-410-dark.png')})
  await page.evaluate(()=>document.querySelector('iframe').contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/host-context-changed',params:{theme:'light'}},'*'))
  await connectionDialog.getByRole('button',{name:'关闭'}).click()
  const calls=await page.evaluate(()=>window.calls)
  const testPos=calls.findIndex(call=>call.name==='test_connection__prod')
  assert.ok(testPos>0)
  assert.deepEqual(decryptedSubmissions.at(-1),{set:{env__prod__opensearch__default_index:'saved-for-prod-*'},secrets:{prod:{opensearch:'prod-密$secret'}}})
  assert.equal(JSON.stringify(calls).includes('prod-密$secret'),false)
  assert.equal(await frame.locator('#secret-prod-opensearch').inputValue(),'')
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
  await frame.getByText('更改地址后需重新输入已保存的凭证；未同时修改的默认索引也会清除。').waitFor()
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
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('已保存',{exact:true}).waitFor()
  assert.equal(decryptedSubmissions.at(-1).set.env__prod__opensearch__default_index,'draft-prod-*')

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
  await page.goto('http://localhost/?early=1')
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
  await earlyFrame.getByLabel('编辑环境').locator('option[value="uat"]').waitFor({state:'detached'})
  assert.equal(await earlyFrame.getByLabel('编辑环境').inputValue(),'prod')
  assert.equal(await earlyFrame.getByLabel('默认业务索引').inputValue(),'retained-after-refresh-*')
  assert.equal((await page.evaluate(()=>window.calls)).filter(call=>call.name==='delete_environment').length,1)
  // Native settings actions can arrive before app initialization.
  await page.goto('http://localhost/?early=edit')
  await frame.getByLabel('编辑环境').waitFor()
  await frame.locator('#secret-prod-opensearch').waitFor({state:'visible'})
  assert.equal(await frame.getByLabel('编辑环境').inputValue(),'prod')
  assert.equal(await frame.locator('#secret-prod-opensearch').evaluate(el=>document.activeElement===el),true)
  await page.goto('http://localhost/?early=result')
  const nativeResult=frame.getByRole('dialog',{name:'连接结果'})
  await nativeResult.getByText('默认索引查询通过').waitFor()
  assert.ok(await nativeResult.getByText('标签接口可访问').isVisible())
  await nativeResult.getByRole('button',{name:'关闭'}).click()

  // A failed encrypted save leaves public and password drafts available for retry.
  await page.goto('http://localhost/')
  await frame.locator('#secret-uat-opensearch').fill('uat-失败$密码')
  await frame.getByLabel('默认业务索引').fill('uat-draft-*')
  await page.evaluate(()=>{window.failNextUpdate=true})
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('fixture: 保存失败',{exact:false}).waitFor()
  assert.equal(await frame.locator('#secret-uat-opensearch').inputValue(),'uat-失败$密码')
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'uat-draft-*')
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('已保存',{exact:true}).waitFor()
  assert.equal(await frame.locator('#secret-uat-opensearch').inputValue(),'')
  assert.equal(JSON.stringify(await page.evaluate(()=>window.calls)).includes('uat-失败$密码'),false)

  // Refresh after an external revision conflict clears only the conflicting environment.
  await page.goto('http://localhost/')
  await frame.locator('#secret-uat-opensearch').fill('stale-uat-secret')
  await frame.getByLabel('默认业务索引').fill('stale-uat-*')
  await frame.getByLabel('编辑环境').selectOption('prod')
  await frame.locator('#secret-prod-opensearch').fill('keep-prod-secret')
  await frame.getByLabel('默认业务索引').fill('keep-prod-*')
  await page.evaluate(()=>window.externalChange('uat'))
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('环境已改变，请刷新页面后重新输入凭证。').waitFor()
  assert.equal(await frame.getByRole('button',{name:'保存更改'}).isDisabled(),true)
  await frame.getByRole('button',{name:'刷新'}).click()
  await frame.getByText('配置已变化，uat 的未保存修改及凭证已清除，请检查后重新输入。').waitFor()
  assert.equal(await frame.locator('#secret-prod-opensearch').inputValue(),'keep-prod-secret')
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'keep-prod-*')
  await frame.getByLabel('编辑环境').selectOption('uat')
  assert.equal(await frame.locator('#secret-uat-opensearch').inputValue(),'')
  assert.equal(await frame.getByLabel('默认业务索引').inputValue(),'logs-uat-*')
  assert.equal(await frame.locator('#field-env__uat__opensearch__url').inputValue(),'https://changed-uat.example.test')
  await frame.getByLabel('编辑环境').selectOption('prod')
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('已保存',{exact:true}).waitFor()
  assert.equal(decryptedSubmissions.at(-1).secrets.prod.opensearch,'keep-prod-secret')

  // A confirmed durable save without values is never repeated; the password is cleared.
  await page.goto('http://localhost/')
  await frame.locator('#secret-uat-opensearch').fill('confirmed-secret')
  await page.evaluate(()=>{window.savedWithoutValues=true})
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('设置已保存，但需要刷新以确认结果。').waitFor()
  assert.equal(await frame.locator('#secret-uat-opensearch').inputValue(),'')
  assert.equal(await frame.getByRole('button',{name:'保存更改'}).isDisabled(),true)
  await frame.getByRole('button',{name:'刷新'}).click()
  await frame.getByText('设置已刷新，请检查后继续。').waitFor()
  assert.equal((await page.evaluate(()=>window.calls)).filter(call=>call.name==='save_settings_secure').length,1)

  // Lost response is ambiguous; refresh before any retry, then clear conflicting secret.
  await page.goto('http://localhost/')
  await frame.locator('#secret-uat-opensearch').fill('unknown-result-secret')
  await page.evaluate(()=>{window.loseNextResponse=true})
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('保存结果未知，请刷新后检查设置。').waitFor()
  assert.equal(await frame.locator('#secret-uat-opensearch').inputValue(),'unknown-result-secret')
  assert.equal(await frame.getByRole('button',{name:'保存更改'}).isDisabled(),true)
  await frame.getByRole('button',{name:'刷新'}).click()
  await frame.getByText('配置已变化，uat 的未保存修改及凭证已清除，请检查后重新输入。').waitFor()
  assert.equal(await frame.locator('#secret-uat-opensearch').inputValue(),'')
  assert.equal((await page.evaluate(()=>window.calls)).filter(call=>call.name==='save_settings_secure').length,1)
  assert.equal(JSON.stringify(await page.evaluate(()=>window.calls)).includes('unknown-result-secret'),false)
  // Each service has an in-page secret; Loki's no-auth mode cannot submit a token.
  await page.goto('http://localhost/')
  await frame.locator('summary').filter({hasText:'StreamLog'}).click()
  await frame.locator('#secret-uat-streamlog').fill('stream-token-$')
  await frame.locator('summary').filter({hasText:'Loki'}).click()
  await frame.locator('#secret-uat-loki').fill('loki-secret')
  await frame.locator('#field-env__uat__loki__auth_type').selectOption('none')
  assert.equal(await frame.locator('#secret-uat-loki').getAttribute('placeholder'),'无需认证，请留空')
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('uat 的 Loki 无需认证，请清空凭证后保存。').waitFor()
  assert.equal(await frame.locator('#secret-uat-loki').inputValue(),'loki-secret')
  await frame.locator('#field-env__uat__loki__auth_type').selectOption('basic')
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('已保存',{exact:true}).waitFor()
  assert.deepEqual(decryptedSubmissions.at(-1).secrets,{uat:{streamlog:'stream-token-$',loki:'loki-secret'}})
  assert.equal(JSON.stringify(await page.evaluate(()=>window.calls)).includes('stream-token-$'),false)
  assert.equal(JSON.stringify(await page.evaluate(()=>window.calls)).includes('loki-secret'),false)

  // An identity change cannot reuse a saved password without explicit re-entry.
  await page.goto('http://localhost/')
  await frame.locator('#field-env__uat__opensearch__url').fill('https://new-uat.example.test')
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('uat 的 opensearch 连接已更改，请重新输入凭证。').waitFor()
  assert.equal((await page.evaluate(()=>window.calls)).filter(call=>call.name==='begin_settings_save').length,0)
  await frame.locator('#secret-uat-opensearch').fill('new-password')
  await frame.getByRole('button',{name:'保存更改'}).click()
  await frame.getByText('已保存',{exact:true}).waitFor()
  assert.equal(decryptedSubmissions.at(-1).secrets.uat.opensearch,'new-password')
  assert.equal(JSON.stringify(await page.evaluate(()=>window.calls)).includes('new-password'),false)
  console.log('MCP App UI passed: secure save, multi-environment editing, deletion and responsive layouts')
}finally{await browser.close()}

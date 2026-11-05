const {readFileSync}=require('node:fs');
const {runInNewContext}=require('node:vm');
const assert=require('node:assert/strict');
const html=readFileSync('rageval/server/static/index.html','utf8');
const source=html.slice(html.indexOf('        async function accountAction(action) {'),html.indexOf('        // Supabase email links'));
async function check({email='test@example.com',password='test-password',fetch}) {
 const nodes=Object.fromEntries(['status','email','password','signup','login'].map(k=>['account-'+k,{value:k==='email'?email:k==='password'?password:'',disabled:false,checkValidity:()=>email.includes('@'),focus(){},scrollIntoView(){},setAttribute(){}}]));
 const context={document:{getElementById:id=>nodes[id]},fetch,AbortController,setTimeout,clearTimeout,TypeError};
 runInNewContext(source,context);
 await context.accountAction('signup');
 assert.equal(nodes['account-signup'].disabled,false);
 return nodes['account-status'].textContent;
}
(async()=>{
 assert.match(await check({email:'',fetch:()=>assert.fail('invalid input sent')}),/valid email/);
 assert.match(await check({password:'short',fetch:()=>assert.fail('short password sent')}),/8 characters/);
 assert.match(await check({fetch:async()=>{throw new TypeError('Failed to fetch')}}),/Registration is not confirmed/);
 assert.match(await check({fetch:async()=>({ok:false,status:503,json:async()=>({detail:'Email sender restricted'})})}),/Email sender restricted/);
 assert.match(await check({fetch:async()=>({ok:true,json:async()=>({message:'Check your email'})})}),/Check your email/);
 assert.match(await check({fetch:async()=>({ok:false,status:502,json:async()=>{throw new SyntaxError()}})}),/restarting/);
 console.log('6 account feedback scenarios passed');
})().catch(e=>{console.error(e);process.exitCode=1});

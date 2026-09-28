// Run against an empty EVIDENCE-mode server; this tests UI behavior, not AI quality.
const {chromium} = require('playwright');
const path = require('node:path');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({headless:true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? {executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE} : {}),
    args:['--disable-gpu','--disable-dev-shm-usage']});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors=[]; page.on('pageerror', e=>errors.push(String(e)));
    await page.goto('http://127.0.0.1:8000');
    await page.waitForFunction(()=>document.querySelector('#model').textContent.includes('EVIDENCE'));
    await page.locator('#question').fill('What is the battery endurance?');
    await page.locator('#send').click();
    await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Upload and select'));
    await page.setInputFiles('#file',path.join(__dirname,'../samples/uav_training_brief.txt'));
    await page.locator('#upload').click();
    await page.waitForFunction(()=>document.querySelectorAll('.document').length===1);
    await page.waitForFunction(()=>!document.querySelector('#send').disabled);
    await page.locator('#question').fill('What is the battery endurance?');
    await page.locator('#send').click();
    await page.waitForSelector('.citation');
    await page.locator('.citation').first().click();
    await page.waitForSelector('#source-dialog[open]');
    if(!await page.locator('#source-text mark').count())throw Error('Missing source highlight');
    fs.mkdirSync(path.join(__dirname,'../artifacts'),{recursive:true});
    await page.screenshot({path:path.join(__dirname,'../artifacts/citation.png'),fullPage:true});
    await page.locator('#close-source').click();
    await page.reload(); await page.waitForSelector('.answer');
    if(!(await page.locator('.answer').innerText()).includes('Evidence excerpts only'))throw Error('Evidence mode label missing');
    await page.locator('.document input').check();
    await page.locator('[data-mode="compare"]').click();
    await page.locator('#question').fill('Compare battery endurance');
    await page.locator('#send').click();
    await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('exactly two'));
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(__dirname,'../artifacts/mobile.png'),fullPage:true});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile horizontal overflow');
    if(errors.length)throw Error(errors.join('\n'));
    console.log('PASS: upload, errors, evidence Q&A, citations, persistence, comparison validation, mobile layout, JavaScript');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});

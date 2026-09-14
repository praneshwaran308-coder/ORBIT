const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({headless: true});
  const page = await browser.newPage();
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  try {
    await page.goto('http://localhost:5174/', {waitUntil: 'networkidle0', timeout: 30000});
    const hasComposer = await page.$('textarea') !== null;
    const hasRunButton = await page.$x("//button[contains(translate(., 'RUN TASK', 'run task'), 'run task')]").then(r=>r.length>0);
    const hasLiveExec = await page.$('main div.bg-surface-container-low') !== null;
    const hasAgents = await page.$('aside ul') !== null;
    console.log(JSON.stringify({consoleErrors,hasTaskComposer:hasComposer,hasRunButton,hasLiveExecutionArea:hasLiveExec,hasAgentsSection:!!hasAgents}));
  } catch(e){console.error('Error during QA check:',e);}
  finally {await browser.close();}
})();

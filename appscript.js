const AGENT_ENDPOINT = 'https://jayanths-macbook-pro-2.taila1d577.ts.net/agent-response';  // Change to Tailscale URL after setup https://jayanths-macbook-pro-2.taila1d577.ts.net/agent-response
//const AGENT_TOKEN = 'shared-secret';  // You can remove this since you don't have auth
const BOT_EMAIL = 'ccpaxbot@gmail.com';

function processQueue() {
  const label = GmailApp.getUserLabelByName('agent-queue');
  const doneLabel = GmailApp.getUserLabelByName('agent-done') || GmailApp.createLabel('agent-done');
  const threads = label.getThreads(0, 10);

  threads.forEach(t => {
    if (t.getLabels().some(l => l.getName() === 'agent-done')) return;
    const msg = t.getMessages().pop();
    const taskText = msg.getPlainBody();
    const subject = msg.getSubject();
    const from = msg.getFrom();

    // Changed to use 'query' instead of 'task'
    const payload = { 
      query: taskText  // CHANGED: Use 'query' to match FastAPI
    };
    
    try {
      const res = UrlFetchApp.fetch(AGENT_ENDPOINT, {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify(payload),
        muteHttpExceptions: true
      });

      const responseData = JSON.parse(res.getContentText());
      Logger.log('Response: ' + JSON.stringify(responseData));
      
      // Extract the actual response (we'll see the structure once it works)
      const agentOutput = responseData.response || responseData.output || responseData.result || JSON.stringify(responseData);
      
      const reply = agentOutput + '\n\n— Pax Assistant';
      
      t.replyAll(reply);
      t.addLabel(doneLabel);
      
      Logger.log(`Successfully processed email from ${from}`);
    } catch (error) {
      Logger.log(`Error: ${error}`);
    }
  });
}

function debugAgentResponse() {
  const testPayload = {
    query: "Find Italian restaurants in San Francisco"  // CHANGED: from 'task' to 'query'
  };
  
  try {
    const response = UrlFetchApp.fetch(AGENT_ENDPOINT, {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(testPayload),
      muteHttpExceptions: true
    });
    
    const rawResponse = response.getContentText();
    Logger.log('=== RAW RESPONSE ===');
    Logger.log(rawResponse);
    
    const parsed = JSON.parse(rawResponse);
    Logger.log('=== PARSED RESPONSE ===');
    Logger.log(JSON.stringify(parsed, null, 2));
    
    Logger.log('=== AVAILABLE FIELDS ===');
    Logger.log('Keys: ' + Object.keys(parsed).join(', '));
    
  } catch (error) {
    Logger.log('Error: ' + error);
  }
}
# config.json merge via API

Use this snippet from client-side JS to perform non-destructive updates to configuration via the Node.js API.

```js
fetch('/api/config', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ headerText: "Today's Specials", bgBrightness: 0.9 })
})
.then(r => r.json())
.then(res => {
  if (res.success) console.log('Config merged');
  else console.error('Merge failed', res);
})
.catch(console.error);
```

The server automatically merges partial updates with existing configuration and writes atomically.

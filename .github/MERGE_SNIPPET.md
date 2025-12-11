# config.json merge snippet

Use this snippet from client-side JS to perform non-destructive updates to `config.json` by POSTing partial changes to `scripts/merge-config.php`.

```js
fetch('scripts/merge-config.php', {
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

Place small partial updates in the body; the server will merge them with existing `config.json` and write atomically.

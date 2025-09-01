# Frontend Debug Commands

## Problem: Frontend still calling `/api/v1/chat/intelligent` instead of new endpoint

## Solution: Enable the new endpoint feature flag

### 1. Open Browser Console (F12)
Go to your WealthPath AI frontend in the browser and open Developer Tools (F12), then go to Console tab.

### 2. Check Current Feature Flag Status
```javascript
console.log('Current new chat flag:', localStorage.getItem('use_new_chat'));
```

### 3. Enable New Endpoint
```javascript
// Enable new endpoint
localStorage.setItem('use_new_chat', 'true');
console.log('New endpoint enabled. Refresh the page to apply.');
```

### 4. Refresh the Page
Press Ctrl+F5 or Cmd+Shift+R to hard refresh and load the new code.

### 5. Verify It's Working
After refresh, open console again and try a message. Look for these log messages:
```
🆕 Using new chat endpoint: true
🌐 Full Chat URL: http://localhost:3000/api/v1/chat-simple/message
```

### 6. Test a Message
Try sending "Hello" in the chat interface. You should see:
- New endpoint URL in console logs
- Different response format (may get LLM provider error but that's expected)

### 7. If Still Getting 404
If you still get 404 after following steps 1-6, disable and re-enable:

```javascript
// Disable
localStorage.setItem('use_new_chat', 'false');
// Refresh page
location.reload();

// Then re-enable
localStorage.setItem('use_new_chat', 'true');
location.reload();
```

### 8. Revert If Needed
```javascript
// Go back to old endpoint
localStorage.removeItem('use_new_chat');
location.reload();
```

## Expected Behavior
- **With flag enabled**: Should call `/api/v1/chat-simple/message`
- **With flag disabled**: Will call `/api/v1/chat/intelligent` (404)
- **Logs should show**: "🆕 Using new chat endpoint: true"
# Integration Test Instructions

## Testing the New Chat Endpoint

### 1. Enable the New Endpoint (Browser Console)
```javascript
// Enable new endpoint
localStorage.setItem('use_new_chat', 'true');

// Verify it's set
console.log('New chat enabled:', localStorage.getItem('use_new_chat'));

// Refresh page to apply changes
location.reload();
```

### 2. Test Messages
Try these test messages to verify the integration:

#### Basic Financial Question
```
"What is my net worth?"
```
Expected: Should return calculated net worth using IdentityMath

#### Tax Question
```
"How can I optimize my taxes?"
```
Expected: Should use tax prompts and provide tax advice

#### Risk Assessment
```
"What are the risks in my portfolio?"
```
Expected: Should analyze risk using the risk prompt

#### General Chat
```
"Hello, how are you?"
```
Expected: Should handle as general chat (non-financial)

### 3. Monitor Console Output
Look for these logs in browser console:
- `🆕 Using new chat endpoint: true`
- `🌐 Full Chat URL: .../api/v1/chat-simple/message`
- Response should include confidence, assumptions, warnings

### 4. Disable to Revert (If Issues)
```javascript
// Disable new endpoint
localStorage.setItem('use_new_chat', 'false');

// Or remove completely
localStorage.removeItem('use_new_chat');

// Refresh
location.reload();
```

### 5. Expected Changes in UI
When using new endpoint:
- Messages should still display normally
- Console should show new endpoint URL
- Response metadata includes confidence/warnings (in message object)
- No token counts or costs (shows 0)

### 6. Verify Backend Integration
Check that requests hit:
- **New**: `POST /api/v1/chat-simple/message`
- **Old**: `POST /api/v1/chat/intelligent` or `POST /api/v1/chat/message`

### 7. Test Error Handling
Try with invalid authentication:
```javascript
// Temporarily break auth
localStorage.removeItem('auth_tokens');

// Send message - should get proper error
// Then restore auth tokens
```

### 8. A/B Testing
Switch between endpoints during conversation:
```javascript
// Use new for a few messages
localStorage.setItem('use_new_chat', 'true');

// Switch to old endpoint
localStorage.setItem('use_new_chat', 'false');

// Compare response quality and speed
```

## Success Criteria
✅ Messages send successfully to new endpoint  
✅ Responses display correctly in chat UI  
✅ Console shows correct endpoint selection  
✅ Error handling works properly  
✅ Can switch between old/new endpoints  
✅ Authentication works with Bearer tokens  
✅ Session IDs maintained properly  

## Troubleshooting
- **Empty responses**: Check backend logs for IdentityMath errors
- **Auth errors**: Verify tokens in localStorage
- **Network errors**: Check API base URL configuration
- **UI issues**: Check for JavaScript console errors
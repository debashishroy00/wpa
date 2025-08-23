# WealthPath AI - MVP Deployment Guide

## 🎯 MVP Testing Strategy

**User Experience**: Seamless testing without API keys required from users
**Cost Structure**: You provide API keys, users get full functionality
**Target Audience**: Anyone can test immediately with `test@gmail.com`

---

## 🔑 API Key Setup (One-Time)

### Required API Keys (Your Account)
1. **Gemini API Key** (Primary - Most Cost Effective):
   - Go to [makersuite.google.com](https://makersuite.google.com)
   - Create API key (free tier: 60 requests/minute)
   - Cost: ~$0.50-2.00 per 1000 requests

2. **OpenAI API Key** (Optional Backup):  
   - Go to [platform.openai.com](https://platform.openai.com)
   - Create API key with billing setup
   - Cost: ~$2-4 per 1000 requests

### MVP Cost Estimate
- **Budget**: $20-50/month for MVP testing
- **Capacity**: 10,000+ financial advice requests  
- **Users**: Unlimited testers using your keys

---

## 🚀 Deployment Steps

### Step 1: Get Your API Keys
```bash
# Get Gemini API key (required)
https://makersuite.google.com → Create API Key

# Get OpenAI API key (optional)  
https://platform.openai.com → Create API Key
```

### Step 2: Setup Database (Supabase)
1. Go to [supabase.com](https://supabase.com)
2. Create project: `wealthpath-ai`
3. Copy DATABASE_URL from Settings > Database

### Step 3: Deploy Backend (Render)
1. Connect GitHub repo to [render.com](https://render.com)
2. Add Environment Variables:
```
DATABASE_URL = [supabase-connection-string]
GEMINI_API_KEY = [your-gemini-key]  
OPENAI_API_KEY = [your-openai-key]
JWT_SECRET_KEY = [generate-secure-string]
ENVIRONMENT = production
```

### Step 4: Deploy Frontend (Vercel)
1. Connect GitHub repo to [vercel.com](https://vercel.com)
2. Set VITE_API_BASE_URL to your Render backend URL

---

## 🎯 User Testing Experience

### For Any User
1. Visit: https://wealthpathai.vercel.app
2. Register OR login with: `test@gmail.com` / `password123`
3. Get instant AI financial advice (using your API keys)
4. Test all features immediately - no setup required

### For You (Admin)
1. Login with your credentials for admin dashboard access
2. Monitor usage and costs through hosting platform dashboards
3. All API costs charged to your accounts (controlled by you)

---

## 💰 Cost Management

### Monitor Usage
- **Gemini**: Check usage at makersuite.google.com
- **Render**: Monitor at dashboard for backend resource usage
- **Supabase**: Track database usage and connections

### Cost Controls
- Set spending limits on API key accounts
- Monitor daily/weekly to stay within budget
- Primary model (Gemini) is most cost-effective

---

## 🚨 Security Notes

- Your API keys are secure in Render environment variables
- Users never see or need API keys
- You control all costs and usage
- Demo credentials are safe for public use

---

**Result: Anyone can test WealthPath AI immediately with full AI functionality!**
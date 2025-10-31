# Hosting Recommendation

**I recommend Netlify** for your static site. Here's why:

## Why Netlify?

1. **Free Forever** - Generous free tier (100GB bandwidth/month)
2. **Auto-Deploy** - Connects to GitHub, builds on every push
3. **Easy Setup** - 5 minute setup, no configuration needed
4. **Custom Domain** - Free SSL certificates
5. **Fast CDN** - Global content delivery network
6. **Preview Deployments** - Preview changes before merging

## Quick Setup

1. **Create `netlify.toml`** in your repo:
```toml
[build]
  command = "python3 build.py"
  publish = "site"
```

2. **Go to [netlify.com](https://netlify.com)**
3. **Click "Add new site" → "Import from Git"**
4. **Connect GitHub** and select your repo
5. **Deploy!**

Done! Your site will auto-deploy on every push.

## Alternative: GitHub Pages

If you prefer GitHub Pages, use GitHub Actions for automatic builds. See `DEPLOYMENT.md` for setup instructions.

## Cost

- **Netlify:** Free ($0/month)
- **GitHub Pages:** Free ($0/month)
- **Vercel:** Free ($0/month)

All options are free for personal sites. Only cost is domain name (~$10-15/year) if you want a custom domain.


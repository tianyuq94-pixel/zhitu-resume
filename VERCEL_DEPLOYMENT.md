# 免费公开展示部署

本项目支持使用 GitHub、Vercel、TiDB Cloud Starter 和 Vercel Blob 公开展示。无需购买服务器或域名，Vercel 会提供 HTTPS 的 `*.vercel.app` 地址。

## 服务分工

- GitHub：保存代码，并在代码更新后触发重新发布。
- Vercel：运行 Vue 网站和 FastAPI 接口。
- TiDB Cloud Starter：长期保存账号、简历文字和 AI 结果。
- Vercel Blob（Private）：长期保存用户上传的原始简历和证件照。
- DeepSeek：提供 AI 分析。

## 推荐开通顺序

1. 用 GitHub 登录 TiDB Cloud，创建免费的 Starter 集群，并创建数据库 `ai_career`。
2. 复制 TiDB 提供的 MySQL 连接地址，转换为 `mysql+pymysql://...` 格式。
3. 用 GitHub 登录 Vercel，导入 `tianyuq94-pixel/zhitu-resume`。
4. 在首次部署前添加下面的环境变量。首次部署把 `AI_CAREER_STORAGE_BACKEND` 设为 `local`。
5. 部署成功后，在 Vercel 项目中创建并连接一个 Private Blob Store。
6. 把 `AI_CAREER_STORAGE_BACKEND` 改为 `vercel_blob`，重新部署。
7. 注册一个测试账号，上传小于 4 MB 的 PDF/DOCX，依次验证诊断、岗位匹配、定制简历和面试。

## Vercel 环境变量

参考 `backend/.env.vercel.example`，至少设置：

- `AI_CAREER_APP_ENV=production`
- `AI_CAREER_CORS_ORIGINS=["https://你的项目地址.vercel.app"]`
- `AI_CAREER_ALLOWED_HOSTS=["*.vercel.app"]`
- `AI_CAREER_DATABASE_URL=TiDB 的完整连接地址`
- `AI_CAREER_AUTO_CREATE_SCHEMA=true`
- `AI_CAREER_AUTH_SECRET=不少于 32 位的随机字符串`
- `AI_CAREER_SECURE_COOKIES=true`
- `AI_CAREER_STORAGE_BACKEND=local`（连接 Blob 后改为 `vercel_blob`）
- `AI_CAREER_RESUME_MAX_BYTES=4000000`
- `AI_CAREER_DEEPSEEK_API_KEY=你的私密 API Key`

Private Blob Store 连接项目后，Vercel 会自动提供 `BLOB_READ_WRITE_TOKEN`，不需要把它写进代码。

## 安全边界

- `.env`、数据库密码、登录签名密钥和 DeepSeek API Key 不进入 GitHub。
- Vercel Blob 必须选择 Private，原始文件只通过登录后的后端接口读取。
- 这个免费方案适合个人作品展示和非商业试用。正式商业收费前，需要重新确认部署套餐、支付资质、隐私政策和中国大陆相关合规要求。

# Render 免费部署

本项目使用一个 Render Web Service 同时运行前端和后端，继续连接 TiDB Cloud，并将用户上传的简历和证件照持久化到 TiDB。这样即使免费实例休眠、重启或重新部署，用户文件也不会丢失。

## 部署前准备

需要准备两项私密信息，只在 Render 的环境变量页面填写：

1. TiDB Cloud 连接地址，变量名为 `AI_CAREER_DATABASE_URL`
2. DeepSeek API Key，变量名为 `AI_CAREER_DEEPSEEK_API_KEY`

不要把真实连接地址、数据库密码或 API Key 写入代码、聊天消息或 GitHub。

TiDB 地址应包含数据库名和 TLS 参数，例如：

```text
mysql+pymysql://用户名:密码@主机:4000/test?ssl_verify_cert=true&ssl_verify_identity=true
```

## 创建服务

1. 登录 Render，并连接 GitHub。
2. 选择 **New + → Blueprint**。
3. 选择仓库 `tianyuq94-pixel/zhitu-resume`。
4. Render 会读取根目录的 `render.yaml`，创建名为 `zhitu-resume-tianyuq94` 的免费 Web Service。
5. 在要求填写的环境变量中粘贴 TiDB 连接地址和 DeepSeek API Key。
6. 开始部署，等待状态变为 **Live**。

首次构建会安装前端、后端和中文字体，通常需要几分钟。部署完成后的默认地址为 `https://zhitu-resume-tianyuq94.onrender.com`；如果 Render 因重名调整了服务地址，需要同步修改 `AI_CAREER_CORS_ORIGINS`。

## 部署后检查

依次确认：

- 首页可以打开；
- 可以注册、登录和退出；
- 上传 PDF 或 DOCX 后刷新页面，文件仍然存在；
- AI 简历诊断可以完成；
- 定制简历可以导出 PDF 和 Word；
- `https://你的地址/api/v1/health/database` 返回数据库已连接。

Render 免费 Web Service 闲置 15 分钟后会休眠，下一次访问会自动唤醒。后续可直接升级为付费实例消除冷启动，无需迁移代码和数据库。

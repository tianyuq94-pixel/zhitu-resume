# 职途简历上线准备清单

当前项目采用同域部署：浏览器访问一个 HTTPS 域名，静态网页由 Nginx 提供，`/api/` 转发给 FastAPI。这样不需要把后端服务直接暴露到公网。

## 上线前需要准备

- 一台可长期运行的服务器
- 一个已解析到服务器的域名和有效 HTTPS 证书
- MySQL 8 数据库
- Python 3.12、Node.js 24、pnpm 和 Nginx
- 中文字体包（推荐 Noto Sans CJK），用于 PDF 导出
- DeepSeek API Key
- 可持续备份的文件目录和数据库备份位置

## 1. 生产环境变量

复制 `backend/.env.production.example` 为 `backend/.env`，然后替换全部示例值：

- `AI_CAREER_CORS_ORIGINS` 必须是网站的完整 HTTPS 地址
- `AI_CAREER_ALLOWED_HOSTS` 必须是域名，不要保留 `*`
- `AI_CAREER_AUTH_SECRET` 使用至少 32 位的随机字符串
- `AI_CAREER_SECURE_COOKIES` 保持为 `true`
- 数据库密码和 DeepSeek API Key 只保存在服务器环境中
- `AI_CAREER_STORAGE_ROOT` 必须指向有写入权限、会被备份的持久目录

生产配置不符合上述安全要求时，后端会拒绝启动。

## 2. 构建前端

在 `frontend` 目录执行：

```powershell
pnpm install --frozen-lockfile
pnpm build
```

将生成的 `frontend/dist/` 内容部署到 Nginx 的网站根目录。`deploy/nginx.conf.example` 提供了同域转发、单页路由和安全响应头示例，替换域名与网站目录后使用。

## 3. 安装并启动后端

在 `backend` 目录创建独立 Python 环境并安装项目，然后先执行数据库迁移：

```bash
python3.12 -m venv .venv
./.venv/bin/python -m pip install .
./.venv/bin/python -m alembic upgrade head
./.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips 127.0.0.1
```

正式服务器应使用系统服务管理器守护后端进程，并设置开机自动启动。后端只监听 `127.0.0.1:8000`，公网访问统一经过 Nginx 与 HTTPS。

## 4. 数据备份

至少每天备份：

- MySQL 数据库 `ai_career`
- `AI_CAREER_STORAGE_ROOT` 指向的简历目录
- 与简历目录同级的 `custom-resume-photos` 目录

备份文件应加密并保存在另一台设备或对象存储中。恢复流程需要在正式开放前演练一次。

## 5. 上线验收

- `https://你的域名/api/v1/health` 返回 `status: ok`
- `/api/v1/health/database` 返回数据库已连接
- 生产环境无法访问 `/api/docs` 和 `/api/openapi.json`
- 注册、登录、退出和修改密码正常
- 未完善求职档案时，打开 AI 功能会进入资料页；保存后自动继续
- 上传 PDF/DOCX、文字确认和简历删除正常
- 四类 AI 流程均可完成，页面不显示模型供应商名称
- 岗位定制简历可以导出 PDF 与可编辑 Word
- 手机和电脑均可正常浏览，浏览器控制台无错误
- HTTPS、Secure Cookie、安全响应头和上传大小限制生效

## 尚未包含

- 支付、次数余额和邀请赠送
- 短信验证码登录
- 扫描件 OCR
- 多机部署所需的共享限流与对象存储

这些内容不影响当前 V1.0 单机版上线测试。

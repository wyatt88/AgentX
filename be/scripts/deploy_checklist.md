# AgentX 2.0 — 部署清单

> **最后更新**: 2026-03-04  
> **适用环境**: AWS (ECS + DynamoDB + ECR + S3/CloudFront)

---

## 前置条件

- [ ] AWS CLI 已配置，有足够 IAM 权限
- [ ] Docker 已安装并可运行
- [ ] Node.js 18+ (前端构建)
- [ ] Python 3.10+ (后端)

---

## 1. DynamoDB 表创建

```bash
# 从仓库根目录执行
python3 be/scripts/create_tables.py --region us-east-1
```

**验证**:
- [ ] `WorkflowTable` — ACTIVE
- [ ] `WorkflowExecutionTable` — ACTIVE，GSI `workflow_id-index` 存在
- [ ] `ModelProviderTable` — ACTIVE

---

## 2. Seed 数据 (可选)

```bash
python3 be/scripts/seed_data.py --region us-east-1
```

- [ ] Bedrock Provider (is_default=True) 已创建
- [ ] OpenAI Provider 已创建
- [ ] 示例工作流已创建

---

## 3. 后端 Docker 镜像构建 & 推送

```bash
# 登录 ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# 构建
cd be
docker build -t agentx-be:latest .

# 标记 & 推送
docker tag agentx-be:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/agentx-be:latest
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/agentx-be:latest
```

- [ ] ECR 仓库 `agentx-be` 存在
- [ ] 镜像推送成功

---

## 4. ECS 服务更新

```bash
# 更新 Task Definition (确认以下环境变量)
#   APP_ENV=production
#   AWS_REGION=us-east-1
#   CORS_ORIGINS=https://your-domain.com

# 强制新部署
aws ecs update-service \
  --cluster agentx-cluster \
  --service agentx-be-service \
  --force-new-deployment \
  --region us-east-1
```

- [ ] Task Definition 中 `APP_ENV=production`
- [ ] Task Definition 中 `CORS_ORIGINS` 设置为实际前端域名
- [ ] ECS 服务已滚动更新完成
- [ ] Health check `/health` 返回 200

---

## 5. 前端构建 & 部署

```bash
cd fe
npm install
npm run build
# 产物在 dist/ 目录

# 部署到 S3 + CloudFront (或 ECS)
aws s3 sync dist/ s3://agentx-frontend-bucket/ --delete
aws cloudfront create-invalidation \
  --distribution-id <DISTRIBUTION_ID> \
  --paths "/*"
```

- [ ] `npm run build` 无报错
- [ ] S3 上传成功
- [ ] CloudFront 缓存失效已触发

---

## 6. 端到端验证

| 检查项 | 命令/方法 | 预期结果 |
|--------|----------|---------|
| 后端健康检查 | `curl https://api.your-domain.com/health` | `{"status":"ok"}` |
| Swagger 文档 | 浏览器打开 `https://api.your-domain.com/docs` | 所有路由可见 |
| 前端首页 | 浏览器打开 `https://your-domain.com` | 正常加载 |
| Agent 列表 | 前端导航到 Agent 页面 | API 调用成功 |
| 工作流列表 | 前端导航到 Workflow 页面 | 显示 seed 工作流 |
| 模型提供商 | 前端导航到 Model 页面 | 显示 Bedrock + OpenAI |
| CORS | 前端发起 API 请求 | 无 CORS 报错 |

---

## 7. 回滚方案

```bash
# 回滚后端 — 指定旧 Task Definition revision
aws ecs update-service \
  --cluster agentx-cluster \
  --service agentx-be-service \
  --task-definition agentx-be:<PREVIOUS_REVISION>

# 回滚前端 — S3 版本管理或从旧构建重新部署
aws s3 sync s3://agentx-frontend-backup/ s3://agentx-frontend-bucket/ --delete
```

---

## 环境变量清单

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `APP_ENV` | 应用环境 | `production` |
| `AWS_REGION` | AWS 区域 | `us-east-1` |
| `CORS_ORIGINS` | 允许的前端域名(逗号分隔) | `https://agentx.example.com` |

---

## 注意事项

1. **CORS**: 生产环境务必将 `CORS_ORIGINS` 限制为实际前端域名，不要使用 `*`
2. **DynamoDB**: 使用 PAY_PER_REQUEST 计费模式，无需预设容量
3. **Strands SDK**: 确保 ECS Task Role 有 Bedrock 调用权限
4. **日志**: 后端日志输出到 stdout/stderr，由 ECS/CloudWatch 收集

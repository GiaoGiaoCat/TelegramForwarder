# Telegram Forwarder 部署指南

本文档提供 Telegram Forwarder 的部署流程。功能说明和使用指南请参考 [README.md](./README.md)。

## 📋 前置准备

### 系统要求

- Docker 20.10+
- Docker Compose 1.29+
- 至少 1GB 磁盘空间

### 配置凭据

按照 [README.md 快速开始](./README.md#-快速开始) 章节获取以下凭据：
- `API_ID` 和 `API_HASH`
- `BOT_TOKEN`
- `USER_ID`
- `PHONE_NUMBER`

### 配置 .env 文件

```bash
# 克隆仓库并配置
git clone git@github.com:GiaoGiaoCat/TelegramForwarder.git
cd TelegramForwarder
cp .env.example .env

# 编辑 .env 填写上述凭据
vim .env
```

---

## 部署方式

### 方式一：本地构建部署（推荐）

适合需要修改代码或使用最新代码的场景。

```bash
# 1. 构建镜像
docker build --no-cache -t telegram-forwarder:local .

# 2. 首次运行（登录验证）
docker compose run -it telegram-forwarder
# 按提示输入验证码和密码，完成后 Ctrl+C 退出

# 3. 修改 docker-compose.yml
# 将 stdin_open 和 tty 改为 false

# 4. 后台运行
docker compose up -d
```

### 方式二：使用 Docker Compose 自动构建

```bash
# 首次运行（自动构建+登录）
docker compose run -it telegram-forwarder
# 完成登录后 Ctrl+C 退出

# 修改 docker-compose.yml
# 将 stdin_open 和 tty 改为 false

# 后台启动
docker compose up -d
```

### 启用 RSS 功能（可选）

```bash
# 1. 编辑 .env
RSS_ENABLED=true

# 2. 修改 docker-compose.yml，取消端口映射注释
ports:
  - 9804:8000

# 3. 重启服务
docker compose restart

# 4. 访问 http://localhost:9804
```

---

## 更新和维护

### 更新代码

```bash
git pull origin main
docker compose down
docker build --no-cache -t telegram-forwarder:local .
docker compose up -d
```

### 常用命令

```bash
# 查看日志
docker compose logs -f
docker compose logs --tail=100

# 重启服务
docker compose restart

# 停止服务
docker compose down

# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz db/ sessions/ config/ .env
```

---

## 常见问题

### Session 过期需要重新登录

```bash
rm -rf ./sessions/*
docker compose run -it telegram-forwarder
```

### 容器启动失败

```bash
# 查看日志排查原因
docker compose logs telegram-forwarder

# 常见原因：.env 配置错误、Session 文件损坏
```

### 数据库锁定

```bash
docker compose down
docker compose up -d
```

### 端口冲突

修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - 9805:8000  # 改为其他端口
```

---

## 重要提示

### 数据保护

- `sessions/` 包含登录凭证，需妥善保管
- `db/` 包含所有规则，建议定期备份
- 不要将 `.env`、`sessions/`、`db/` 提交到 Git

### 安全建议

```bash
# 设置文件权限
chmod 600 .env
chmod 700 sessions/

# 启用 Telegram 两步验证
```

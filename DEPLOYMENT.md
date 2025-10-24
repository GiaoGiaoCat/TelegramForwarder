# Telegram Forwarder 部署指南

本文档提供了 Telegram Forwarder 的完整部署流程，包括本地构建和 Docker 部署。

## 📋 目录

- [环境准备](#环境准备)
- [获取配置凭据](#获取配置凭据)
- [配置环境变量](#配置环境变量)
- [部署方式](#部署方式)
  - [方式一：本地构建部署](#方式一本地构建部署)
  - [方式二：Docker Compose 部署](#方式二docker-compose-部署)
- [首次运行](#首次运行)
- [更新和维护](#更新和维护)
- [常见问题](#常见问题)

---

## 环境准备

### 系统要求

- Docker 20.10+ 或 Docker Desktop
- Docker Compose 1.29+ (通常随 Docker 一起安装)
- 至少 1GB 可用磁盘空间
- 稳定的网络连接

### 检查 Docker 环境

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本
docker compose version
```

---

## 获取配置凭据

在开始部署前，需要准备以下凭据：

### 1. Telegram API 凭据

访问 [https://my.telegram.org/apps](https://my.telegram.org/apps) 创建应用：

- 登录您的 Telegram 账号
- 填写应用信息（名称和平台）
- 获取 `API_ID` 和 `API_HASH`

### 2. Bot Token

与 [@BotFather](https://t.me/BotFather) 对话创建机器人：

```
/newbot
```

按照提示完成创建，获取 `BOT_TOKEN`

### 3. 用户 ID

与 [@userinfobot](https://t.me/userinfobot) 对话，发送任意消息获取您的 `USER_ID`

---

## 配置环境变量

### 1. 下载配置模板

```bash
# 如果还没有克隆仓库
git clone git@github.com:GiaoGiaoCat/TelegramForwarder.git
cd TelegramForwarder

# 复制环境变量模板
cp .env.example .env
```

### 2. 编辑 .env 文件

使用文本编辑器打开 `.env` 文件，填写必填项：

```ini
######### 必填项 #########
# Telegram API 配置
API_ID=你的API_ID
API_HASH=你的API_HASH

# 用户账号手机号 (格式: +8613812345678)
PHONE_NUMBER=+8613812345678

# Bot Token
BOT_TOKEN=你的BOT_TOKEN

# 用户ID
USER_ID=你的USER_ID
```

### 3. 可选配置

根据需要配置以下选项：

```ini
# RSS 功能（如需要 RSS 订阅功能）
RSS_ENABLED=true

# AI 功能（如需要 AI 处理）
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
# ... 其他 AI 配置

# 其他配置请参考 .env.example
```

---

## 部署方式

### 方式一：本地构建部署

适合需要自定义修改代码或使用最新代码的场景。

#### 1. 构建镜像

```bash
# 进入项目目录
cd TelegramForwarder

# 构建 Docker 镜像（不使用缓存，确保最新）
docker build --no-cache -t telegram-forwarder:local .
```

构建过程需要几分钟，请耐心等待。

#### 2. 首次运行（需要登录验证）

```bash
# 交互式启动，用于首次登录
docker compose run -it telegram-forwarder
```

按照提示：
1. 输入手机号接收的验证码
2. 如果启用了两步验证，输入密码
3. 登录成功后按 `Ctrl+C` 退出

#### 3. 修改 docker-compose.yml

登录成功后，编辑 `docker-compose.yml`：

```yaml
services:
  telegram-forwarder:
    # ... 其他配置
    stdin_open: false  # 改为 false
    tty: false         # 改为 false
```

#### 4. 后台运行

```bash
# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

---

### 方式二：Docker Compose 部署

使用 docker-compose.yml 中已配置的构建选项。

#### 1. 首次运行

```bash
# 进入项目目录
cd TelegramForwarder

# 交互式启动，用于首次登录
docker compose run -it telegram-forwarder
```

Docker Compose 会自动构建镜像并启动容器。

#### 2. 完成登录验证

按照提示输入验证码和密码，登录成功后按 `Ctrl+C` 退出。

#### 3. 修改配置并启动

编辑 `docker-compose.yml`，将 `stdin_open` 和 `tty` 改为 `false`，然后：

```bash
# 后台启动
docker compose up -d

# 查看日志
docker compose logs -f telegram-forwarder
```

---

## 首次运行

### 登录流程

1. **启动交互式容器**
   ```bash
   docker compose run -it telegram-forwarder
   ```

2. **输入验证码**
   - Telegram 会向您的手机号发送验证码
   - 在终端输入验证码

3. **输入两步验证密码**（如果启用）
   - 如果账号启用了两步验证
   - 输入您设置的密码

4. **登录成功**
   - 看到 "用户客户端已启动" 和 "机器人客户端已启动" 消息
   - Session 文件会保存在 `./sessions` 目录

5. **退出容器**
   - 按 `Ctrl+C` 退出

6. **修改配置并后台运行**
   ```bash
   # 修改 docker-compose.yml 中的 stdin_open 和 tty 为 false
   docker compose up -d
   ```

### 启用 RSS 功能（可选）

如果需要使用 RSS 功能：

1. 在 `.env` 中设置：
   ```ini
   RSS_ENABLED=true
   RSS_BASE_URL=http://your-domain.com  # 可选
   ```

2. 修改 `docker-compose.yml`，取消端口映射注释：
   ```yaml
   ports:
     - 9804:8000
   ```

3. 重启服务：
   ```bash
   docker compose down
   docker compose up -d
   ```

4. 访问 RSS 仪表盘：
   ```
   http://localhost:9804
   ```

---

## 更新和维护

### 更新代码

```bash
# 拉取最新代码
git pull origin main

# 停止运行中的容器
docker compose down

# 重新构建镜像
docker build --no-cache -t telegram-forwarder:local .

# 启动服务
docker compose up -d
```

### 查看日志

```bash
# 实时查看日志
docker compose logs -f

# 查看最近 100 行日志
docker compose logs --tail=100

# 查看特定服务日志
docker compose logs -f telegram-forwarder
```

### 重启服务

```bash
# 重启服务
docker compose restart

# 或者
docker compose down && docker compose up -d
```

### 清理数据

```bash
# 停止并删除容器
docker compose down

# 清理未使用的 Docker 资源
docker system prune -a

# ⚠️ 删除数据（谨慎操作）
rm -rf ./db ./sessions ./logs ./temp
```

---

## 常见问题

### 1. 构建失败：网络超时

**问题**：构建时无法下载依赖包

**解决方案**：Dockerfile 已配置清华大学镜像源，如仍失败可尝试：

```bash
# 使用代理构建
docker build --build-arg HTTP_PROXY=http://your-proxy:port \
             --build-arg HTTPS_PROXY=http://your-proxy:port \
             -t telegram-forwarder:local .
```

### 2. 登录时收不到验证码

**问题**：无法接收 Telegram 验证码

**解决方案**：
- 确认手机号格式正确（包含国家代码，如 +86）
- 检查 Telegram 是否在线
- 尝试请求语音验证码

### 3. Session 过期需要重新登录

**问题**：提示 "Session expired" 或 "Unauthorized"

**解决方案**：

```bash
# 删除旧的 session 文件
rm -rf ./sessions/*

# 重新登录
docker compose run -it telegram-forwarder
```

### 4. 容器启动后立即退出

**问题**：`docker compose up -d` 后容器立即停止

**解决方案**：

```bash
# 查看详细日志
docker compose logs telegram-forwarder

# 常见原因：
# - .env 文件配置错误
# - Session 文件问题
# - 数据库文件损坏
```

### 5. 端口被占用

**问题**：RSS 端口 9804 已被占用

**解决方案**：

修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - 9805:8000  # 改为其他端口
```

### 6. 数据库锁定错误

**问题**：提示 "database is locked"

**解决方案**：

```bash
# 停止所有容器
docker compose down

# 检查是否有进程占用数据库
lsof ./db/forward.db

# 重启服务
docker compose up -d
```

### 7. 内存不足

**问题**：容器因内存不足被 kill

**解决方案**：

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  telegram-forwarder:
    # ... 其他配置
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

---

## 目录结构说明

部署后会创建以下目录：

```
TelegramForwarder/
├── db/              # 数据库文件
├── logs/            # 日志文件
├── sessions/        # Telegram 会话文件
├── temp/            # 临时文件
├── config/          # 配置文件
├── rss/             # RSS 相关数据
│   ├── data/        # RSS 数据库
│   └── media/       # RSS 媒体文件
└── ufb/             # UFB 插件配置
    └── config/
```

**重要**：
- `sessions/` 目录包含登录凭证，请妥善保管
- `db/` 目录包含所有转发规则，定期备份
- `logs/` 目录会占用磁盘空间，可定期清理

---

## 备份和恢复

### 备份

```bash
# 停止服务
docker compose down

# 备份重要数据
tar -czf backup-$(date +%Y%m%d).tar.gz \
    db/ sessions/ config/ .env

# 恢复服务
docker compose up -d
```

### 恢复

```bash
# 停止服务
docker compose down

# 解压备份
tar -xzf backup-20250124.tar.gz

# 启动服务
docker compose up -d
```

---

## 安全建议

1. **保护敏感文件**
   ```bash
   chmod 600 .env
   chmod 700 sessions/
   ```

2. **不要提交敏感信息到 Git**
   - `.env` 文件已在 `.gitignore` 中
   - 不要提交 `sessions/` 和 `db/` 目录

3. **定期更新**
   ```bash
   git pull origin main
   docker build --no-cache -t telegram-forwarder:local .
   docker compose up -d
   ```

4. **使用强密码**
   - 为 Telegram 账号启用两步验证
   - RSS 功能的管理密码要足够复杂

---

## 技术支持

如遇到问题：

1. 查看日志：`docker compose logs -f`
2. 查看 [GitHub Issues](https://github.com/GiaoGiaoCat/TelegramForwarder/issues)
3. 参考 [README.md](./README.md) 中的使用说明
4. 查看 [CLAUDE.md](./CLAUDE.md) 了解架构细节

---

## 许可证

本项目采用 GPL-3.0 开源协议，详见 [LICENSE](./LICENSE) 文件。

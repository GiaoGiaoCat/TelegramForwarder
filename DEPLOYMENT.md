# Telegram Forwarder 部署指南

本文档提供 Telegram Forwarder 的部署流程。功能说明和使用指南请参考 [README.md](./README.md)。

## 📋 前置准备

### 系统要求

**最低要求**：
- 操作系统：Linux（推荐 Ubuntu 20.04+、CentOS 8+ 或 Fedora 35+）
- Docker：20.10+
- Docker Compose：1.29+（推荐使用 Docker Compose V2）
- 磁盘空间：至少 1GB
- 内存：建议 512MB 以上

### 安装依赖

根据你的操作系统选择对应的安装方式：

#### RHEL / CentOS / Fedora 系统

**1. 安装基础工具**

```bash
# 安装 git, vim 和常用解压工具
sudo dnf install -y git vim unzip tar
```

**2. 安装 Docker**

```bash
# 移除旧版本（如果存在）
sudo dnf remove -y docker \
  docker-client \
  docker-client-latest \
  docker-common \
  docker-latest \
  docker-latest-logrotate \
  docker-logrotate \
  docker-engine

# 安装依赖
sudo dnf install -y yum-utils

# 添加 Docker 官方仓库
sudo yum-config-manager --add-repo \
  https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker 和 Docker Compose 插件
sudo dnf install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

# 启动 Docker
sudo systemctl start docker

# 设置开机自启
sudo systemctl enable docker

# 验证安装
docker --version
```

**3. 配置 Docker（可选但推荐）**

```bash
# 将当前用户加入 docker 组，避免每次使用 sudo
sudo usermod -aG docker $USER

# 需要重新登录或执行以下命令使其生效
newgrp docker

# 测试（不需要 sudo）
docker ps
```

**4. 配置 Docker Compose 命令别名（可选）**

Docker Compose V2 使用 `docker compose`（空格），如果你习惯旧版的 `docker-compose`（连字符），可以创建别名：

```bash
echo 'alias docker-compose="docker compose"' >> ~/.bashrc
source ~/.bashrc
```

#### Ubuntu / Debian 系统

**1. 安装基础工具**

```bash
# 更新软件包索引
sudo apt update

# 安装 git, vim 和常用工具
sudo apt install -y git vim unzip tar curl
```

**2. 安装 Docker**

```bash
# 移除旧版本
sudo apt remove -y docker docker-engine docker.io containerd runc

# 安装必要依赖
sudo apt install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

# 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置 Docker 仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker 和 Docker Compose 插件
sudo apt update
sudo apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
```

**3. 配置 Docker（可选但推荐）**

```bash
# 将当前用户加入 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行
newgrp docker

# 测试
docker ps
```

#### 其他 Linux 发行版

请参考 [Docker 官方文档](https://docs.docker.com/engine/install/) 进行安装。

### 验证安装

完成上述步骤后，运行以下命令验证所有组件：

```bash
git --version          # 应显示 git 版本
vim --version          # 应显示 vim 版本
docker --version       # 应显示 Docker 版本（20.10+）
docker compose version # 应显示 Docker Compose 版本（1.29+）
```

**预期输出示例**：
```
git version 2.34.1
VIM - Vi IMproved 8.2
Docker version 24.0.6, build ed223bc
Docker Compose version v2.21.0
```



### 获取 Telegram 凭据

在部署前，你需要准备以下 Telegram 凭据。详细步骤请参考 [README.md 快速开始](./README.md#-快速开始) 章节。

| 凭据 | 获取方式 | 说明 |
|------|---------|------|
| `API_ID` | https://my.telegram.org/apps | Telegram API 应用 ID |
| `API_HASH` | https://my.telegram.org/apps | Telegram API 应用密钥 |
| `BOT_TOKEN` | @BotFather | 机器人 Token |
| `USER_ID` | @userinfobot | 你的 Telegram 用户 ID |
| `PHONE_NUMBER` | - | 你的手机号（国际格式，如 +8613812345678） |

### 下载项目并配置环境

```bash
# 方式 1: 使用 Git 克隆（推荐）
git clone https://github.com/Heavrnl/TelegramForwarder.git
cd TelegramForwarder

# 方式 2: 下载压缩包
wget https://github.com/Heavrnl/TelegramForwarder/archive/refs/heads/main.zip
unzip main.zip
cd TelegramForwarder-main

# 创建 .env 配置文件
cp .env.example .env

# 编辑配置文件，填写上述凭据
vim .env
# 或使用其他编辑器：nano .env
```

**必填项示例**：
```ini
API_ID=12345678
API_HASH=abcdef1234567890abcdef1234567890
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
USER_ID=123456789
PHONE_NUMBER=+8613812345678
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

## 🔄 更新和维护

### 更新到最新版本

**使用 Git 更新**（推荐）：

```bash
# 1. 停止服务
docker compose down

# 2. 备份重要数据（可选但推荐）
tar -czf backup-$(date +%Y%m%d).tar.gz db/ sessions/ config/ .env

# 3. 拉取最新代码
git pull origin main

# 4. 重新构建镜像
docker build --no-cache -t telegram-forwarder:local .

# 5. 启动服务
docker compose up -d

# 6. 查看日志确认运行正常
docker compose logs -f
```

**手动下载更新**：

```bash
# 1. 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz db/ sessions/ config/ .env

# 2. 下载最新代码
wget https://github.com/Heavrnl/TelegramForwarder/archive/refs/heads/main.zip
unzip main.zip

# 3. 复制配置和数据到新目录
cp backup-*.tar.gz TelegramForwarder-main/
cd TelegramForwarder-main
tar -xzf backup-*.tar.gz

# 4. 构建并启动
docker build --no-cache -t telegram-forwarder:local .
docker compose up -d
```

### 常用管理命令

**日志查看**：
```bash
# 实时查看日志
docker compose logs -f

# 查看最近 100 条日志
docker compose logs --tail=100

# 查看特定服务的日志
docker compose logs -f telegram-forwarder

# 保存日志到文件
docker compose logs > logs_$(date +%Y%m%d).txt
```

**服务控制**：
```bash
# 重启服务
docker compose restart

# 停止服务
docker compose down

# 停止并删除容器、网络（保留数据）
docker compose down

# 停止并删除所有内容（包括数据卷）
docker compose down -v
```

**数据备份**：
```bash
# 完整备份（包含配置和数据）
tar -czf backup-full-$(date +%Y%m%d).tar.gz \
  db/ sessions/ config/ .env

# 仅备份数据库
tar -czf backup-db-$(date +%Y%m%d).tar.gz db/

# 仅备份会话文件
tar -czf backup-sessions-$(date +%Y%m%d).tar.gz sessions/
```

**磁盘空间管理**：
```bash
# 查看临时文件占用
du -sh temp/

# 手动清理临时文件（系统会自动清理）
rm -rf temp/*

# 查看 Docker 镜像占用
docker system df

# 清理未使用的 Docker 资源
docker system prune -a
```

---

## ❓ 常见问题

### Session 过期需要重新登录

**问题现象**：
- 提示 "Unauthorized" 或 "Session expired"
- 无法正常收发消息

**解决方法**：
```bash
# 1. 删除旧的会话文件
rm -rf ./sessions/*

# 2. 重新登录
docker compose run -it telegram-forwarder
# 按提示输入验证码

# 3. 修改 docker-compose.yml，将 stdin_open 和 tty 改为 false

# 4. 后台运行
docker compose up -d
```

### 容器启动失败

**排查步骤**：

```bash
# 1. 查看完整日志
docker compose logs telegram-forwarder

# 2. 检查配置文件
cat .env  # 确认必填项都已填写

# 3. 检查端口占用
netstat -tlnp | grep 9804

# 4. 重新构建镜像
docker compose down
docker build --no-cache -t telegram-forwarder:local .
docker compose up -d
```

**常见原因**：
- ❌ `.env` 配置错误或缺少必填项
- ❌ Session 文件损坏
- ❌ 端口被占用
- ❌ Docker 资源不足

### 数据库锁定

**问题现象**：
- 日志显示 "database is locked"
- 操作无响应

**解决方法**：
```bash
# 重启服务通常可以解决
docker compose down
docker compose up -d

# 如果仍然锁定，检查是否有多个进程访问数据库
ps aux | grep telegram-forwarder
```

### 端口冲突

**问题现象**：
- 提示 "port is already allocated"

**解决方法**：

修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - 9805:8000  # 改为其他可用端口
```

然后重启服务：
```bash
docker compose down
docker compose up -d
```

### 临时文件占用过多磁盘空间

**问题现象**：
- `temp/` 目录占用大量空间
- 磁盘空间不足警告

**解决方法**：
```bash
# 1. 检查临时文件大小
du -sh temp/

# 2. 手动清理（系统会自动定期清理）
rm -rf temp/*

# 3. 调整清理策略（可选）
# 编辑 .env 文件：
CLEANUP_INTERVAL_SECONDS=1800    # 30分钟清理一次
CLEANUP_FILE_AGE_SECONDS=1800    # 清理超过30分钟的文件
```

详见 [临时文件自动清理](./README.md#-临时文件自动清理) 文档。

### 内存不足

**问题现象**：
- 容器频繁重启
- 系统变慢

**解决方法**：
```bash
# 1. 检查内存使用
docker stats telegram-forwarder

# 2. 限制容器内存（修改 docker-compose.yml）
services:
  telegram-forwarder:
    deploy:
      resources:
        limits:
          memory: 512M

# 3. 重启服务
docker compose down
docker compose up -d
```

---

## ⚠️ 重要提示

### 数据保护

**需要保护的文件**：
- 📁 `sessions/` - 包含登录凭证，**非常重要**
- 📁 `db/` - 包含所有规则和配置
- 📄 `.env` - 包含敏感凭据
- 📁 `config/` - 自定义配置（如果有）

**备份建议**：
```bash
# 每周备份一次
tar -czf backup-weekly-$(date +%Y%m%d).tar.gz \
  db/ sessions/ config/ .env

# 重要操作前备份
tar -czf backup-before-update-$(date +%Y%m%d-%H%M).tar.gz \
  db/ sessions/ config/ .env
```

**不要提交到 Git**：
- ✅ 已在 `.gitignore` 中排除
- ❌ 永远不要将敏感文件提交到公共仓库

### 安全建议

**1. 文件权限设置**：
```bash
# 限制敏感文件的访问权限
chmod 600 .env
chmod 700 sessions/
chmod 700 db/
```

**2. Telegram 账号安全**：
- ✅ 启用 Telegram 两步验证
- ✅ 定期检查活跃会话（Telegram 设置 → 隐私与安全 → 活跃会话）
- ✅ 不要在公共网络登录

**3. 服务器安全**：
```bash
# 使用防火墙限制访问
sudo ufw allow 9804/tcp  # 仅允许 RSS 端口（如需要）

# 如果不需要外部访问 RSS，修改 docker-compose.yml：
ports:
  - 127.0.0.1:9804:8000  # 仅本地访问
```

**4. 定期更新**：
- 定期更新到最新版本以获取安全修复
- 关注项目的更新日志

### 监控建议

**定期检查日志**：
```bash
# 每天检查是否有异常
docker compose logs --tail=500 | grep -i error

# 检查清理日志
docker compose logs | grep "清理"
```

**监控资源使用**：
```bash
# 监控容器资源使用
watch -n 5 docker stats telegram-forwarder

# 监控磁盘空间
df -h
du -sh temp/ db/ sessions/
```

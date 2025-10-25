# 临时文件清理问题分析报告

## 🔍 问题现象
用户反映 `temp/` 目录中的视频文件未被完全清理，占用大量硬盘空间。

## 📋 临时文件生命周期

### 1. 文件下载位置
**MediaFilter** (`filters/media_filter.py:244`)
```python
file_path = await event.message.download_media(TEMP_DIR)
```

**SenderFilter** (`filters/sender_filter.py:142`)
```python
file_path = await message.download_media(TEMP_DIR)  # 媒体组消息
```

**PushFilter** (`filters/push_filter.py:149, 166, 312`)
```python
file_path = await message.download_media(TEMP_DIR)  # 仅在 enable_only_push 时
```

### 2. 文件清理逻辑

#### SenderFilter 清理策略 (`sender_filter.py:260-275, 357-371`)
```python
if not rule.enable_push:
    os.remove(file_path)  # 删除文件
else:
    logger.info(f'推送功能已启用，保留临时文件')  # 不删除！
```

**关键点**: 如果启用推送功能 (`rule.enable_push = True`)，文件**不会**被删除，留给 PushFilter 处理。

#### PushFilter 清理策略 (`push_filter.py:87-104`)
```python
finally:
    if processed_files:
        for file_path in processed_files:
            os.remove(path_str)  # 删除文件
```

**关键点**: 只清理 `processed_files` 列表中的文件。

## ⚠️ 发现的问题

### 问题 1: 推送失败时文件不清理

**场景**:
1. 规则启用了推送 (`rule.enable_push = True`)
2. SenderFilter 下载文件后跳过清理（line 260-275）
3. PushFilter 在处理时抛出异常（网络错误、配置错误等）
4. `processed_files` 为空或不完整
5. 文件永久滞留在 `temp/` 目录

**受影响代码**:
- `sender_filter.py:260` - 单条媒体
- `sender_filter.py:357` - 媒体组

**触发条件**:
```python
rule.enable_push = True  # 启用推送
# 且推送过程中发生任何异常
```

### 问题 2: 媒体组部分失败时的清理不完整

**场景**:
1. 媒体组有 10 个文件
2. SenderFilter 下载并上传了 8 个
3. 第 9 个文件上传失败（FloodWaitError、网络超时等）
4. `finally` 块只清理了部分文件
5. 剩余文件未被清理

**受影响代码**:
- `sender_filter.py:258-276` - 媒体组清理逻辑

### 问题 3: PushFilter 异常时的清理不确定性

**场景**:
1. PushFilter 自己下载文件 (`need_cleanup = True`)
2. 在 `_push_media_group` 内部的 finally 块清理（line 247-257）
3. 但如果在清理之前就发生异常，可能跳过清理

**受影响代码**:
- `push_filter.py:247-257` - 媒体组清理
- `push_filter.py:366-384` - 单条媒体清理

### 问题 4: 缩略图文件清理遗漏

**场景**:
1. 视频文件下载时会生成缩略图 (`.jpg.thumb`)
2. 如果主文件清理失败，缩略图也不会被清理
3. 缩略图路径存储在 `context.media_metadata` 中

**受影响代码**:
- 所有清理缩略图的代码都依赖主文件清理成功

## 🐛 最严重的问题：视频文件

**为什么视频文件占用特别大？**

1. **文件体积大**: 视频文件通常比图片大 10-100 倍
2. **处理时间长**: 上传视频更容易超时或触发限流
3. **缩略图额外空间**: 每个视频都有缩略图文件
4. **失败率高**: 视频上传失败率比其他媒体类型高

## 📊 风险评估

### 高风险场景
1. ✅ **启用推送 + 推送服务不稳定** - 最常见
2. ✅ **大量视频转发 + 网络不稳定** - 文件积累快
3. ✅ **频繁的 FloodWaitError** - 部分文件上传失败

### 中风险场景
1. ⚠️ **媒体组消息转发** - 部分失败时清理不完整
2. ⚠️ **只转发到推送配置** (`enable_only_push = True`) - 依赖 PushFilter

### 低风险场景
1. ⏸️ **仅文本消息** - 无临时文件
2. ⏸️ **未启用推送** - SenderFilter 直接清理

## 💡 建议的修复方案

### 方案 1: 添加全局清理机制（推荐）
在每个 filter 处理完成后，无论成功失败，都强制清理 `context.media_files` 中的文件。

```python
# 在 FilterChain 的 finally 块中
for file_path in context.media_files:
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f'强制清理文件失败: {e}')
```

### 方案 2: 改进 PushFilter 的清理逻辑
确保 PushFilter 无论成功失败都清理 `context.media_files`。

```python
finally:
    # 清理所有 context.media_files 中的文件
    if rule.enable_push and context.media_files:
        for file_path in context.media_files:
            try:
                if os.path.exists(str(file_path)):
                    os.remove(file_path)
            except Exception as e:
                logger.error(f'清理文件失败: {e}')
```

### 方案 3: 定时清理脚本
添加一个后台任务，定期清理超过 1 小时的临时文件。

```python
async def cleanup_old_temp_files():
    """清理超过1小时的临时文件"""
    import time
    current_time = time.time()
    for file in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, file)
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > 3600:  # 1小时
                os.remove(file_path)
```

### 方案 4: 使用上下文管理器
创建一个文件管理器，自动跟踪和清理下载的文件。

```python
class TempFileManager:
    def __init__(self):
        self.files = []

    def add(self, file_path):
        self.files.append(file_path)

    def cleanup(self):
        for f in self.files:
            if os.path.exists(f):
                os.remove(f)
```

## 🔧 临时解决方案

**手动清理命令**:
```bash
# 查看 temp 目录大小
du -sh temp/

# 清理所有临时文件
rm -rf temp/*

# 或者只清理视频文件
find temp/ -type f \( -name "*.mp4" -o -name "*.mkv" -o -name "*.avi" \) -delete

# 清理超过1小时的文件
find temp/ -type f -mmin +60 -delete
```

## 📝 结论

主要问题在于 **SenderFilter 和 PushFilter 之间的清理责任不明确**：

1. SenderFilter 期望 PushFilter 会清理文件
2. PushFilter 只清理自己下载的文件或处理成功的文件
3. 异常情况下，文件"无人认领"，永久滞留

**最优解决方案**: 实施方案 1（全局清理机制）+ 方案 3（定时清理），确保文件一定会被清理。

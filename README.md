# 免费 AI API 羊毛雷达

零成本（$0）分布式系统，自动扫描 Reddit 上的免费 AI API 羊毛信息，通过 Gemini AI 智能过滤，最终通过 Telegram 机器人推送给用户。

## 架构总览

```
cron-job.org（外部定时触发）
       │
       ▼
GitHub Actions（爬取 + 过滤）
       │
       ├─► Reddit 爬虫 → 关键词前置过滤（干掉 90% 噪音）
       ├─► Gemini 3.1 Flash Lite AI 二次过滤（每天 500 次免费额度）
       └─► 写入结果 → Hugging Face Dataset（CSV 文件）

Telegram 用户 → /search
       │
       ▼
HF Space（FastAPI，端口 7860）
       ├─► deque 去重（防止 Telegram 冷启动重试轰炸）
       ├─► BackgroundTasks（秒回 200 OK）
       └─► 读取 CSV → 回复用户
```

---

## 零、你需要注册哪些账号（全部免费）

在开始之前，你需要准备好以下 5 个账号。如果你已经有某个账号，跳过即可。

| 序号 | 平台 | 注册地址 | 用途 |
|---|---|---|---|
| 1 | GitHub | https://github.com/signup | 存放代码 + 跑定时任务 |
| 2 | Google（Gmail） | https://accounts.google.com/signup | 获取 Gemini API Key |
| 3 | Hugging Face | https://huggingface.co/join | 存储数据 + 托管 Telegram 机器人 |
| 4 | Telegram | 手机应用商店下载 | 接收羊毛通知的聊天软件 |
| 5 | cron-job.org | https://cron-job.org/en/signup/ | 外部定时触发（可选） |

---

## 一、获取 Google Gemini API Key（免费）

这个 Key 用来让 AI 帮你判断 Reddit 帖子是不是真正的羊毛。

1. 用浏览器打开 https://aistudio.google.com/apikey
2. 用你的 Google 账号登录
3. 点击页面上的 **Create API Key** 按钮
4. 在弹出的对话框中，选择一个 Google Cloud 项目（如果没有会自动创建），点击 **Create API key in existing project**
5. 页面上会出现一串以 `AIzaSy` 开头的长字符串，这就是你的 API Key
6. ⚠️ **立刻复制保存到记事本！** 这个 Key 离开页面后可能无法再次查看

> 💡 免费额度：Gemini 3.1 Flash Lite 每天可以调用 500 次，完全够用。

---

## 二、获取 Hugging Face Token（免费）

这个 Token 用来让程序自动往你的 HF Dataset 写入数据。

1. 用浏览器打开 https://huggingface.co/settings/tokens
2. 用你的 Hugging Face 账号登录
3. 点击 **Create new token** 按钮
4. Name 随便填，比如 `freeworld-scanner`
5. Role 选 **Write**（必须选 Write，否则无法写入数据）
6. 点击 **Create token**
7. ⚠️ **立刻复制保存到记事本！** 这个 Token 只显示一次

---

## 三、创建 Telegram 机器人（免费）

1. 打开 Telegram 应用（手机或电脑版都行）
2. 在搜索框中搜索 `@BotFather`，点击进入与它的对话
3. 发送 `/newbot`
4. BotFather 会问你机器人的名字（显示名），比如输入：`免费AI羊毛雷达`
5. 然后问你机器人的用户名（必须以 `bot` 结尾），比如输入：`free_ai_deals_xxx_bot`（xxx 换成你自己的，因为用户名不能重复）
6. BotFather 会回复一段信息，其中有一行类似：
   ```
   Use this token to access the HTTP API:
   7123456789:AAHx1234567890abcdefghijklmnopqrst
   ```
7. ⚠️ **把这串 Token 复制保存到记事本！** 这就是你的 `TG_BOT_TOKEN`

---

## 四、创建 GitHub 仓库并上传代码

### 4.1 创建仓库

1. 打开 https://github.com/new
2. Repository name 填：`freeworld`
3. ⚠️ **Visibility 必须选 Public（公共）！** 因为只有公共仓库才能免费使用 GitHub Actions
4. 其他选项都不用勾选，直接点 **Create repository**

### 4.2 上传代码

**方法一：用 Git 命令行（推荐）**

如果你电脑上装了 Git，打开终端（Windows 用 PowerShell），进入项目目录：

```bash
cd d:\Projects\freeworld
git init
git add .
git commit -m "init:  AI sheephair雷达"
git branch -M main
git remote add origin https://github.com/teddyezz/freeSheepHair.git
git push -u origin main
```

> 💡 如果提示输入用户名密码，去 GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token，勾选 `repo` 权限，用生成的 Token 当密码。

**方法二：用浏览器直接上传（适合不会 Git 的小白）**

1. 进入你刚创建的仓库页面 `https://github.com/你的用户名/freeworld`
2. 点击 **creating a new file** 或 **uploading an existing file**
3. 按照项目目录结构，逐个创建文件夹和文件：
   - 先点 **creating a new file**，在文件名框输入 `.github/workflows/scan.yml`（这样会自动创建文件夹），然后把 [scan.yml](.github/workflows/scan.yml) 的内容粘贴进去，点 **Commit changes**
   - 同理创建 `.github/workflows/keepalive.yml`，粘贴 [keepalive.yml](.github/workflows/keepalive.yml) 的内容
   - 创建 `scraper/crawler.py`，粘贴 [crawler.py](scraper/crawler.py) 的内容
   - 创建 `scraper/ai_filter.py`，粘贴 [ai_filter.py](scraper/ai_filter.py) 的内容
   - 创建 `scraper/storage.py`，粘贴 [storage.py](scraper/storage.py) 的内容
   - 创建 `scraper/requirements.txt`，粘贴 [requirements.txt](scraper/requirements.txt) 的内容
   - 创建 `.gitignore`，粘贴 [.gitignore](.gitignore) 的内容

> ⚠️ 注意：`hf_space/` 目录下的文件是给 Hugging Face Space 用的，不需要上传到 GitHub。

---

## 五、配置 GitHub Secrets

Secrets 是加密存储的敏感信息，你的 API Key 和 Token 都放在这里。

1. 进入你的仓库页面 `https://github.com/你的用户名/freeworld`
2. 点击顶部的 **Settings** 标签
3. 在左侧菜单找到 **Secrets and variables** → 点击 **Actions**
4. 点击 **New repository secret** 按钮，逐个添加以下 4 个 Secret：

### Secret 1：Gemini API Key

- Name 填：`GEMINI_API_KEY`
- Value 填：你在第一步获取的那串 `AIzaSy...` 开头的 Key
- 点击 **Add secret**

### Secret 2：Hugging Face Token

- Name 填：`HF_TOKEN`
- Value 填：你在第二步获取的 `hf_` 开头的 Token
- 点击 **Add secret**

### Secret 3：HF Dataset 仓库 ID

- Name 填：`HF_DATASET_REPO`
- Value 填：`你的HF用户名/free-ai-api-deals`（比如你的 HF 用户名是 `zhangsan`，就填 `zhangsan/free-ai-api-deals`）
- 点击 **Add secret**

> 💡 你的 HF 用户名可以在 https://huggingface.co/settings/profile 页面看到。

### Secret 4：Reddit 板块列表

- Name 填：`REDDIT_SUBREDDITS`
- Value 填：`LocalLLaMA,MachineLearning,artificial,OpenAI,ChatGPT`
- 点击 **Add secret**

> 💡 这些是 AI 相关的 Reddit 板块，用英文逗号分隔。你可以根据需要增减。

---

## 六、创建 Hugging Face Dataset

这个 Dataset 就是一个在线的 CSV 文件，用来存储扫描到的羊毛信息。

1. 打开 https://huggingface.co/new-dataset
2. Owner 选择你自己的账号
3. Dataset name 填：`free-ai-api-deals`
4. License 随便选一个，比如 `mit`
5. ⚠️ **Visibility 必须选 Public！** 否则 Space 无法读取数据
6. 点击 **Create dataset**
7. 创建完成后，不需要手动上传任何文件。首次运行扫描器时会自动创建 `deals.csv`

> 💡 验证：你的 Dataset 地址应该是 `https://huggingface.co/datasets/你的HF用户名/free-ai-api-deals`

---

## 七、部署 Hugging Face Space（Telegram 机器人）

这是最关键的一步——把 Telegram 机器人部署到 HF 的免费服务器上。

### 7.1 创建 Space

1. 打开 https://huggingface.co/new-space
2. Space name 填：`free-ai-deals-bot`
3. License 随便选
4. SDK 选 **Docker**
5. Hardware 选 **CPU Basic - FREE**（就是免费那个）
6. ⚠️ **Visibility 选 Public！** 否则 Telegram 无法发送 Webhook
7. 点击 **Create Space**

### 7.2 上传文件

创建完成后，Space 页面会显示一个空仓库。你需要上传 `hf_space/` 目录下的 4 个文件：

1. 在 Space 页面点击 **Files and versions** 标签
2. 点击 **Add file** → **Upload files**
3. 把以下 4 个文件拖进去：
   - `app.py`（Telegram 机器人主程序）
   - `Dockerfile`（容器配置）
   - `requirements.txt`（Python 依赖）
   - `README.md`（Space 元数据）
4. 点击 **Commit changes to main**

> ⚠️ 这 4 个文件在你本地的 `d:\Projects\freeworld\hf_space\` 目录下。

### 7.3 配置环境变量

1. 在 Space 页面点击 **Settings** 标签
2. 往下滚动找到 **Variables and secrets** 区域
3. 点击 **New secret**，添加以下 2 个 Secret：

| 类型 | 名称 | 值 |
|---|---|---|
| Secret | `TG_BOT_TOKEN` | 你在第三步获取的 Telegram Bot Token（`7123456789:AAHx...` 那串） |
| Secret | `HF_TOKEN` | 你在第二步获取的 Hugging Face Token（`hf_...` 那串） |

4. 点击 **New variable**，添加 1 个 Variable：

| 类型 | 名称 | 值 |
|---|---|---|
| Variable | `HF_DATASET_REPO` | `你的HF用户名/free-ai-api-deals` |

> 💡 Secret 和 Variable 的区别：Secret 是加密的，填完后无法再查看；Variable 是明文的，可以随时修改。

### 7.4 等待构建完成

1. 回到 Space 页面，你会看到状态显示 **Building**（正在构建）
2. 大约需要 2~5 分钟
3. 当状态变成 **Running** 时，说明部署成功了！
4. 你可以点击 Space 页面上的 URL 链接，如果看到 `{"status":"alive","deals_repo":"..."}` 就说明一切正常

---

## 八、设置 Telegram Webhook

这一步把 Telegram 和你的 HF Space 连接起来。

### 8.1 获取你的 Space URL

你的 Space URL 格式是：
```
https://你的HF用户名-free-ai-deals-bot.hf.space
```

比如你的 HF 用户名是 `zhangsan`，那 URL 就是：
```
https://zhangsan-free-ai-deals-bot.hf.space
```

> 💡 注意：HF 的 URL 规则是把用户名中的特殊字符去掉，用连字符连接。你可以在 Space 页面的嵌入链接中确认实际 URL。

### 8.2 设置 Webhook

打开浏览器，在地址栏输入以下 URL 并回车（把对应的值替换成你自己的）：

```
https://api.telegram.org/bot你的TG_BOT_TOKEN/setWebhook?url=https://你的HF用户名-free-ai-deals-bot.hf.space/webhook
```

举例，如果你的：
- TG_BOT_TOKEN = `7123456789:AAHx1234567890abcdefghijklmnopqrst`
- HF 用户名 = `zhangsan`

那完整 URL 就是：
```
https://api.telegram.org/bot7123456789:AAHx1234567890abcdefghijklmnopqrst/setWebhook?url=https://zhangsan-free-ai-deals-bot.hf.space/webhook
```

如果页面显示：
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

恭喜！Webhook 设置成功了！

> ⚠️ 如果显示错误，检查：1) Token 是否正确 2) Space 是否在 Running 状态 3) URL 中是否有多余的空格

---

## 九、测试 Telegram 机器人

1. 在 Telegram 中搜索你创建的机器人用户名（比如 `@free_ai_deals_xxx_bot`）
2. 点击进入对话
3. 发送 `/start`
4. 如果机器人回复了欢迎消息，说明一切正常！

然后试试：
- `/search` - 查看所有羊毛（目前可能还没有数据，因为爬虫还没跑过）
- `/latest` - 查看最近 5 条

---

## 十、手动触发一次扫描（验证爬虫是否工作）

不用等 2 小时，我们可以手动触发一次扫描来验证。

1. 进入你的 GitHub 仓库页面
2. 点击顶部的 **Actions** 标签
3. 左侧找到 **Scan Free AI Deals**，点击它
4. 右侧点击 **Run workflow** 按钮
5. 在弹出的确认框中再点 **Run workflow**
6. 等待几十秒到几分钟，刷新页面，你会看到一个新的运行记录
7. 点击进去可以查看详细日志

如果运行成功（绿色 ✓），回到 Telegram 发 `/search`，应该就能看到扫描到的羊毛了！

---

## 十一、配置 cron-job.org 外部定时触发（可选但推荐）

GitHub 自带的定时任务经常迟到甚至跳过。用 cron-job.org 外部触发更准时。

### 11.1 创建细粒度 PAT

先创建一个专用的 GitHub Token，只给最小权限。

1. 打开 https://github.com/settings/personal-access-tokens/new
2. Token name 填：`cronjob-trigger`
3. Expiration 选：**1 year**（一年后过期，到时候再续）
4. Repository access 选：**Only select repositories** → 下拉选择你的 `freeworld` 仓库
5. Permissions 展开 **Repository permissions**：
   - 找到 **Actions** → 设为 **Read and write**
   - ⚠️ **其他所有权限保持 No access 不要动！** 尤其是 Contents 绝对不要给！
6. 点击 **Generate token**
7. ⚠️ **立刻复制保存到记事本！** 这串 Token 以 `github_pat_` 开头

### 11.2 注册 cron-job.org

1. 打开 https://cron-job.org/en/signup/
2. 填写邮箱和密码，注册账号
3. 登录后点击 **Create new job**

### 11.3 创建定时任务

在创建任务页面，按以下填写：

| 字段 | 填写内容 |
|---|---|
| Title | `触发羊毛扫描` |
| URL | `https://api.github.com/repos/你的GitHub用户名/freeworld/dispatches` |
| Request method | **POST** |
| Schedule | 选 **Every 2 hours**（每 2 小时） |

然后展开 **Advanced configuration**：

**Request headers**（点击 Add header，添加 3 个）：

| Header 名称 | Header 值 |
|---|---|
| `Accept` | `application/vnd.github.v3+json` |
| `Authorization` | `Bearer github_pat_你的细粒度PAT` |
| `Content-Type` | `application/json` |

**Request body**：

```json
{"event_type": "scan-news"}
```

点击 **Create job** 保存。

> 💡 验证：你可以点击任务旁边的 **Execute now** 按钮手动测试一次。如果成功，你的 GitHub Actions 页面会出现一个新的运行记录。

---

## 十二、常见问题排查

### Q：手动触发 Actions 后报错，日志显示 `GEMINI_API_KEY not set`

A：说明 GitHub Secrets 没配置好。回到第五步，检查 Secret 的名称是否完全一致（区分大小写），值是否有多余的空格。

### Q：Telegram 机器人不回复

A：按以下顺序排查：
1. HF Space 是否在 Running 状态？去 Space 页面确认
2. Webhook 是否设置成功？在浏览器访问 `https://api.telegram.org/bot你的TOKEN/getWebhookInfo`，查看 `url` 字段是否正确，`last_error_message` 是否有报错
3. HF Space 的环境变量是否配置了？去 Settings → Variables and secrets 确认

### Q：扫描运行成功但 Telegram 里 /search 没有数据

A：可能原因：
1. HF_DATASET_REPO 在 GitHub Secrets 和 HF Space Variable 中的值不一致
2. HF Token 没有 write 权限——重新创建一个 Write 权限的 Token
3. 确实没有扫描到羊毛——查看 Actions 运行日志中的 `After keyword filter` 数量

### Q：GitHub Actions 的定时任务没有自动运行

A：这是 GitHub 的已知问题，Schedule 在高负载时会延迟。解决方案：
1. 配置 cron-job.org 外部触发（第十一步）
2. 或者手动去 Actions 页面点 Run workflow

### Q：Space 休眠后机器人响应很慢

A：这是正常的。HF 免费 Space 会在无人访问时休眠，首次唤醒需要 10~30 秒。用户发消息后等一会儿就会收到回复。

---

## 费用

**$0** — 所有组件均使用免费额度：

| 组件 | 免费额度 |
|---|---|
| GitHub Actions | 公共仓库无限免费 |
| Gemini 3.1 Flash Lite | 每天 500 次请求 |
| Hugging Face Space (CPU Basic) | 2 vCPU + 16GB RAM，永久免费 |
| Hugging Face Dataset | 免费存储 |
| cron-job.org | 免费 |
| Telegram Bot API | 免费 |

---

## 工作原理详解

1. **定时触发**：GitHub Actions 每 2 小时自动运行（也可通过 cron-job.org 外部触发，更准时）
2. **关键词初筛**：爬虫从 Reddit 抓取帖子，用硬编码关键词过滤掉 90% 无关内容
3. **AI 精筛**：剩余帖子发送给 Gemini 3.1 Flash Lite，AI 判断是否为真正的免费 AI API 羊毛
4. **数据存储**：确认的羊毛信息写入 HF Dataset 的 CSV 文件
5. **用户查询**：用户在 Telegram 发 /search，HF Space 读取 CSV 返回结果
6. **去重防护**：deque 内存去重防止 Telegram 冷启动重试导致重复消息
7. **保活机制**：每月自动 commit 防止 GitHub 60 天不活跃禁用定时任务

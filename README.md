# Kessler Research English

为丁涛准备牛津访学交流而制作的科研英语 PWA。软件从可明确归属于 Oxford researcher **Benedikt M. Kessler**（ORCID `0000-0002-8160-2446`）的公开论文题目和摘要，以及丁涛的英文课题进展 PPT 中提取学习内容。

## 当前版本

- 经核验并纳入语料：373 篇期刊论文；
- 会议必备层：370 项；
- 组成：270 个单词（含 70 个 PPT 词汇）、60 个专业短语、40 个科研交流句型；
- 每日计划：50 个单词、3 个短语、2 个句型、约 30 项复习；
- 功能：英式语音优先、慢速/正常/循环、录音回听、听力题、四档间隔复习、词库检索、学习统计、错误标记、进度导入导出、离线使用；
- 英语模拟面试：可选 1.0×、0.75× 或 0.50× 语速，使用随网站发布的固定英国男声 Ryan（不依赖设备系统声音）并支持试听；每次只问一题，支持隐藏/显示原文、麦克风英语转写、基于回答的澄清追问，以及结束后的听力与表达复盘。
- 自我介绍跟读页：固定英国男声 Ryan，全文 332 个词逐词显示英式 IPA，支持 1.0×、0.75×、0.50×、逐段播放、点击单词跳转及 MP3 下载。

模拟面试完全在浏览器中运行，不需要 API 密钥，也不会把录音或转写上传到项目服务器。Chrome、Edge 和 Android 浏览器可优先尝试内置语音转写；不支持时可使用手机键盘自带的英语语音输入。

## 本机打开

网页需要通过 HTTP 打开，不能直接双击 `index.html`。在本目录运行：

```powershell
python -m http.server 8000 --directory app
```

然后在浏览器打开 `http://127.0.0.1:8000/`。

## Android 安装

1. 使用 Chrome 打开 GitHub Pages 网址。
2. 点击 Chrome 菜单中的“添加到主屏幕”或“安装应用”。
3. 首次完整打开后，应用主体和学习数据会写入离线缓存。
4. 学习进度只保存在当前浏览器；建议每周在“设置”中导出备份。

## GitHub Pages 发布

仓库已经包含官方 GitHub Pages Actions 工作流。用户自行登录 GitHub 后：

1. 创建公开仓库 `kessler-vocab`；
2. 将本目录提交并推送到 `main` 分支；
3. 在仓库 `Settings → Pages` 中选择 `GitHub Actions`；
4. 工作流会将 `app/` 目录发布为网站。

不要在聊天、源代码或提交记录中保存 GitHub 密码或访问令牌。

## 重建数据

按以下顺序执行：

```powershell
python scripts/build_corpus.py
python scripts/analyze_candidates.py
python scripts/fetch_uk_ipa.py
python scripts/build_learning_content.py
python scripts/generate_icons.py
python scripts/build_self_introduction_player.py
python scripts/verify_release.py
```

`data/raw/` 和 `data/publications.json` 含有抓取的摘要，仅用于本地分析，已通过 `.gitignore` 排除，不应提交到公开仓库。

## 内容与来源

- 作者身份：ORCID、Europe PMC 作者标识和 DOI/PMID；
- 论文元数据：ORCID、Europe PMC、Crossref；
- 音标：English Wiktionary（CC BY-SA 4.0）及人工校正；
- 学习例句：根据论文语境重新编写，不是摘要原句；
- 代码：MIT License；学习内容仅用于个人教育和会议准备。

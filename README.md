# 会议记录提取工具

这个工具用于从飞书会议纪要中提取说话人、时间和对话内容，支持从URL或本地HTML文件中提取。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 重要说明：关于飞书会议纪要访问限制

⚠️ **注意**：飞书会议纪要通常需要登录才能访问。直接使用URL提取内容可能会失败，因为需要飞书账号的登录凭证。

**推荐使用方法**：
1. 使用浏览器登录飞书账号
2. 打开会议纪要页面
3. 右键选择"另存为"保存为HTML文件
4. 使用本工具处理保存的HTML文件

### 从URL提取会议记录（需要公开访问权限）

只有当会议纪要设置为公开访问时，才能直接从URL提取：

```bash
python transcript_parser.py https://example.feishu.cn/minutes/meeting-url
```

或者指定输出文件:

```bash
python transcript_parser.py https://example.feishu.cn/minutes/meeting-url output.json
```

### 从本地HTML文件提取会议记录（推荐方法）

1. 在浏览器中登录飞书并打开会议纪要
2. 右键选择"另存为"，保存为HTML文件
3. 运行以下命令处理保存的HTML文件:

```bash
python transcript_parser.py 保存的文件.html output.json
```

例如:

```bash
python transcript_parser.py meeting_saved.html output.json
```

### 转换为CSV格式

可以将提取的会议记录转换为CSV格式：

```bash
python csv_converter.py output.json output.csv
```

或者直接从保存的HTML文件转换为CSV：

```bash
python csv_converter.py 保存的文件.html
```

## 输出格式

### JSON输出

JSON文件格式如下:

```json
[
  {
    "speaker": "说话人 1",
    "time": "00:01:41",
    "content": "你放门口吧。好，谢谢。嗯，听得到吗？你说话你们听得到吗？主播还发不了评论。"
  },
  {
    "speaker": "说话人 2",
    "time": "00:02:08",
    "content": "声音有点小啊。声音很远吗？现在听得到吗？这跟我之前调试。"
  },
  ...
]
```

### CSV输出

CSV文件格式如下:

| 说话人 | 时间 | 内容 |
|-------|-----|------|
| 说话人 1 | 00:01:41 | 你放门口吧。好，谢谢。嗯，听得到吗？你说话你们听得到吗？主播还发不了评论。 |
| 说话人 2 | 00:02:08 | 声音有点小啊。声音很远吗？现在听得到吗？这跟我之前调试。 |
| ... | ... | ... |

## 常见问题

### 无法从URL直接提取内容

错误信息：`需要登录飞书账号才能访问该会议纪要`

**解决方案**：
1. 使用浏览器登录飞书账号
2. 打开会议纪要页面
3. 右键选择"另存为"保存为HTML文件
4. 使用本工具处理保存的HTML文件

## 注意事项

- 该工具专门为飞书会议纪要HTML结构设计，如果HTML结构有变化，可能需要调整代码
- 大多数飞书会议纪要需要登录才能访问，建议使用本地HTML文件方式
- 确保HTML文件使用UTF-8编码 
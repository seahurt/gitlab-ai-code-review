# GitLab 自动代码审查工具

CLI 工具，用于获取当前 GitLab 用户作为 Reviewer 的打开 Merge Request，下载 diff 并通过本地 `codex` 进行审查。

## 使用
- 复制 `.env.example` 为 `.env` 并填写 GitLab 访问令牌与 Host。
- 创建并激活虚拟环境，安装依赖：`pip install -r requirements.txt`。
- 运行命令：`python main.py`，可选参数 `--project-id`、`--mr-iid`。

## TODOS
- [ ] 增加授权
- [ ] 增加SSH支持
- [ ] 增加版本号和更新日志

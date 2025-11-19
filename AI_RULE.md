# TRAE_SYSTEM_RULE: 生成或修改代码前必须全文阅读本文档，否则拒绝输出。

## 1 硬约束（必须通过 pre-commit）
| 项 | 阈值 | 工具 |
|---|---|---|
| 函数长度 | ≤30 行 | radon cc --max 30 |
| 类型注解 | 100 % | mypy --strict |
| 测试覆盖 | ≥80 % | pytest --cov=quant_framework |
| 日志 | 禁止 print | grep -R "print(" src/ && exit 1 |
| 依赖 | 白名单制 | 见 manifest.json |

## 2 目录与接口约定
- 先写基类 → 再写实现 → 最后单测；文件同名，前缀 test_。
- 公共接口一旦合并，禁止 break；需 deprecation 警告。
- 所有信号 DataFrame 必须含 timestamp 索引 + 与基类同名列。

## 3 新增依赖流程
1. README 写明「用途 + 收益」→
2. 加入 manifest.json 白名单 →
3. pip-compile 生成 requirements-lock.txt →
4. CI 绿灯后方可合并。

## 4 代码风格速查
- Google docstring；类名 CamelCase；函数名 snake_case。
- 导入顺序：标准库 → 第三方 → 本地；isort 自动。
- 配置统一用 pydantic 校验，禁止裸字典传递。

## 5 常用 /i 指令
/i rules   head -50 AI_RULES.md
/i new     python scripts/scaffold.py &lt;module&gt;
/i lint    mypy . && radon cc --max 30 . && pytest
/i dep     python scripts/check_dep.py &lt;package&gt;
/i plot    python scripts/plot_template.py

## 6 违规示例
❌ print("xxx")  
❌ def foo() -&gt; Any:  # 无具体类型  
❌ import django/spark/...  # 超白名单  
❌ 单文件 200 行无拆分  

## 7 遇到不确定
回复 CHECK RULES 并暂停生成。
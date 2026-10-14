# pbtots — PowerBuilder → TypeScript 转换工具

把 PBL（含源码）/ PBD（编译产物）中的 PowerScript 转成 TypeScript。
当前阶段（M1）：**签名级翻译**——类型化的函数/事件骨架 + 以注释保留的 PB 函数体（`TODO`），
`npx tsc --noEmit` 保证产物可编译；语义级翻译（M2，函数体逐句转译）开发中。

## 目录

- `converter/`
  - `pbltext.py`       文本层：二进制中的可打印 run 抽取、GBK 解码、`DAT*` 断行重连
  - `extract_pbl.py`   PBL 块扫描器：对象/成员/函数/事件/变量/原型声明（含截断保护）
  - `convert.py`       抽取 JSON → TS 类（重载保留、全局函数模块化、外部库声明）
  - `convert_pbd.py`   PBD 无源码路径：对象清单 + 空壳类 + 恢复的 SQL
  - `pbdview.py`       PBD/PBL 目录项枚举与 SQL 字符串恢复
  - `batch.py`         批量 CLI：抽取 + 转换 + tsc + 报告
  - `pslexer.py` / `psparser.py` / `tsbuilder.py`  （M2）语义翻译层，开发中
- `tools/`             调试脚本（recon/hexdump/strings/dump_text）、`diag_blocks.py` 块诊断、`coverage_report.py` 报告
- `tests/`             pytest 单测 + `tests/golden/` 回归快照

## 用法

```bash
# 全量批转（跳过路径含"作废""副本"的库）
python converter/batch.py --input D:\ynsoft --out out --report notes/convert-report.md

# 单个 PBL
python converter/extract_pbl.py foo.pbl decompiled/foo
python converter/convert.py decompiled/foo/foo.json ts/foo

# 测试（PBTOTS_CORPUS 默认 D:\ynsoft，缺失时 golden 自动跳过）
python -m pytest tests/
UPDATE_GOLDEN=1 python -m pytest tests/test_golden.py   # 重建回归快照
```

输出布局：`<out>/decompiled/<库>__<对象>/`（.ps.txt + .json）、`<out>/ts/<库>__<对象>/`（TS）。

## 转换规则（M1）

- 一个 PB 对象 → 一个 TS 类；祖先映射 `window/application` → `Window/Application`，其余 → `NonVisualObject`。
- 函数/子例程 → 类型化方法（`ref` 参数标记保留、`dec{2}` 精度、数组参数、默认值剥离）；
  同名重载全部保留为 TS overload 声明。
- 事件 → `on_<控件>_<事件>` / `on_<事件>` 方法（含 `on X.create/destroy`）。
- 全局函数（`<global>` 块与 `function_object` 对象）→ `global-functions.ts` 模块级导出，不再串入各类。
- `Function ... Library "dll"` 外部声明 → 标注 TODO 的桩。
- 函数体：原 PB 源码以注释保留（最多 60 行），返回类型给默认值；受损块（抽取截断）显式标注。
- `pb-runtime.ts`：PB 内建函数类型桩（M2 扩充为真实实现）。

## 测试与质量

- `tests/test_pbltext.py` 断行重连与 run 抽取；`tests/test_extract.py` 块扫描（含历史 bug 回归：`on X.create`
  必须止于 `end on`）；`tests/test_parse_sig.py` 真实签名样本；`tests/test_golden.py` 端到端 golden。
- golden 覆盖：`hiscom_public`（结构体）、`rf`（application）、`mz_ghcl`（小库）全量文件对比；
  `gy_pyybjk`/`sb_ywcl`（大库）锁定统计计数。
- 报告：`tools/coverage_report.py` 输出对象/函数/事件/TODO 桩/未解析/截断统计与 tsc 错误数。

## 已知限制

- PBL 抽取是启发式（文本 run + 语法头识别），约 1% 的块因源文本受损被截断并在报告中列出；
  二进制垃圾撕裂签名时回退为 `(..._args: any[])` 桩。
- 函数体尚未翻译（M2 目标）；`goto`、NULL 三值逻辑按计划降级处理（标注回退/风险清单）。
- PBD 路径只产空壳与 SQL 存档；p-code 反编译在路线图中。

## 路线图

1. **M2 语义翻译核心**（进行中）：`pslexer`/`psparser`（PowerScript AST）→ `tsbuilder`（TS 生成）：
   控制流结构化、1-based 下标换算、`ref` 参数包装、条件 `=` → `PB.eq`（NULL 安全）、事件/继承/对象依赖。
2. `pb-runtime.ts` 扩充：MessageBox、SQLCA/commit/rollback、日期/字符串等高频内置的真实实现。
3. DataWindow（`.dwo/.srd`）列解析 → interface；SQL 剥离与参数化。
4. PBD：目录表正规解析（替代文本启发式）、p-code 反编译调研。
5. UI 框架映射（React/Vue 选型后）。

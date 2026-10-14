# PB→TS 转换补全实施计划（M1+M2）

## 目标定位（按推荐方案，用户未另行指定）
- **语义翻译优先**：函数体逐句译成可执行 TS（控制流、ref、1-based、事件/继承/依赖）；NULL 语义简化为"保留显式 IsNull + 比较用 PB.eq 家族"，并输出 null 风险清单；译不了的（goto 等）回退 TODO 标注。
- **开发地**：`E:\ChatGPT\PyPbdViewer`；`E:\chatgpt\pbtots` 整体只读，作为回归对照基准。
- 本轮范围 M1+M2；DataWindow 列解析、PBD p-code 反编译、UI 映射列入路线图但不实现。

## 调研结论（计划依据）
- 语料：`D:\ynsoft` 137 个 PBL、5908 个 PBD（无 SR* 源码导出）；`E:\chatgpt\pbtots\decompiled` 2950 对 `.json/.ps.txt`、`tsout` 14.2 万个 .ts 可作抽样对照。
- 实锤 bug：`private function` 在语料出现 125 处，但抽取结果 `function` block **为 0**（`RE_FUNC` 只认 `public`）。
- 语料结构特征（两大样本）：`choose case`、`try/catch`、`ref`、`goto`（单样本 752 处）、`create`、`messagebox`、`commit/rollback` 高频；embedded SQL（`declare/fetch` 2-4 处、`execute` 0）**低频**，SQL 剥离降级为后续项。
- 巨型 block（最大 2.6 万行）是抽取越界产物（`end function` 未匹配就吞到文件尾）。
- 环境：Python 3.12.7 + pytest 9.1.1、node v24 + npx 在 PATH。

## M1 — 抽取正确性 + 工程基础

### 1. 修 extract_pbl.py（抽取层）
- `RE_FUNC` 扩展：`public|private|protected|global` 均可、返回类型可缺省、签名跨行（括号未闭合则续行）；`function`/`subroutine` kind 正确归类。
- block 扫描截断规则：`end function|subroutine|event` 未匹配时，遇到下一个对象头（`type X from`、`on X.`、`forward`、`end type`、新签名行）即截断；单 block 行数上限保护（5000），越界 block 进报告。
- 事件覆盖：`on obj.evt` 与裸 `event ue_x(...)` 声明都归入 event block 并解析参数。

### 2. 修 convert.py（三个已知 bug + 清理）
- 全局块不再串入每个类：单独生成 `global-functions.ts` 模块级导出。
- 重载保留：同名多签名生成 TS overload 声明 + 单 impl，不再 `seen` 去重丢弃。
- `parse_signature` 补：默认参数 `= x`、`dec{2}` 精度、`any`、数组参数 `[]`、`ref/readonly` 保留为 byref 标志。
- 删除死代码 `transliterate_body`/`has_junk`（由 M2 真翻译器接管）。

### 3. 公共化与 CLI
- 新建 `converter/pbltext.py`：合并 pbdview/extract_pbl 重复的 `extract_runs/decode/clean_line`。
- `batch.py` 改 argparse：`--input`（pbl/pbd 或目录）、`--out`、`--report`、`--update-golden`；删除 `D:\ynsoft`、`E:\chatgpt\pbtots`、Doubao node 路径硬编码。
- README 重写与实际文件对齐（现引用的 recon.py 等在旧工程 converter/ 下，搬入本仓库 `tools/`）。

### 4. 测试基准 + 覆盖率报告
- 从 `D:\ynsoft` 取 4 个代表性 PBL 作 golden fixtures：`gy_pyybjk.pbl`（新代码含 try/catch）、`sb_ywcl.pbl`（老代码）、一个小 PBL、一个含菜单/结构对象的 PBL。
- `tests/`：`test_extract.py`、`test_parse_sig.py`、`test_golden.py`（golden 对比，`--update-golden` 再生成）。
- `tools/coverage_report.py` → `notes/convert-report.md`：对象/函数数、已译/TODO 体数、未解析语句类型 top-N、null 风险条目。

### M1 验收标准
- 重抽取后 function+subroutine block 数与 grep 文本计数吻合（误差 <5%）；无 block 超 5000 行。
- 全局函数仅在 `global-functions.ts`；重载签名保留。
- pytest 全绿；golden 产物 `npx tsc --noEmit` 0 错误。

## M2 — PowerScript→TS 语义翻译核心

### 1. `converter/pslexer.py`（词法）
关键字、标识符（含中文）、数字（含 `dec{2}`）、字符串（`'…'`/`"…"`、`~r~n`/`~~` 转义）、`//` 与 `/* */` 注释、`:hostvar`、`;`/换行语释、`DAT*` 乱码清洗沿用 `clean_line`。容错设计：词法错误不抛异常，产出 `Junk` token 供上层回退。

### 2. `converter/psparser.py`（递归下降 → AST，dataclasses，可 dump JSON）
- 声明：函数/子例程（访问级、ref/readonly、默认值、数组参数、forward 原型）、实例/共享/全局变量、`constant`、`type X from <ancestor>`。
- 语句：赋值、IF/ELSEIF/ELSE、CHOOSE CASE（含 TO 区间与 CASE ELSE）、FOR..NEXT [STEP]、DO WHILE/UNTIL..LOOP、LOOP WHILE/UNTIL、TRY/CATCH/THROW、RETURN、EXIT/CONTINUE、CREATE/DESTROY、CALL/TriggerEvent/Post、嵌入 SQL 块（低频：整体捕获为 SqlBlock 节点）、GOTO/LABEL（捕获但不译）、表达式语句、HALT。
- 表达式：完整优先级、AND/OR/NOT、索引 `[]`、成员 `.`、调用（含实参处 `ref`）、字面量、THIS/PARENT/SUPER。

### 3. `converter/tsbuilder.py`（AST → TS，接入 convert.py 管线）
关键翻译规则：
| PB | TS |
|---|---|
| `IF a = b`（条件比较） | `if (PB.eq(a, b))`（NULL 安全；`<>`→`PB.ne`，其余比较同理） |
| 赋值 `a = expr` | `a = expr;`（赋值不走 PB.eq） |
| `AND/OR/NOT` | `&&`/`\|\|`/`!`（NOT 统一加括号） |
| `arr[i]` / `s[i]` | `arr[(i) - 1]`（1-based→0-based 只在下标处转换；循环变量保持 PB 值域） |
| `ref T x` 参数 | `x: PB.Ref<T>`，体内读写 `x.v` |
| 调用点 `f(ref x)` | 语句级：`{ const _r = PB.ref(x); f(_r); x = _r.v; }`；表达式内出现 ref 调用则整函数回退 TODO |
| CHOOSE CASE | if/else-if 链（PB.eq 判等、TO→区间比较） |
| `FOR i=a TO b [STEP s]` | `for (let i=a; s>0 ? i<=b : i>=b; i+=s)` |
| DO/LOOP 各变体 | while / do-while（UNTIL 取反） |
| TRY/CATCH | `try/catch(e)`，PB 异常类 → `PB.exc` 映射 |
| `CREATE x` / `DESTROY` | `new Cls()` / 置 null（GC 语义，风险入报告） |
| `COMMIT/ROLLBACK [USING x]` | `PB.commit(SQLCA)` / `PB.rollback(SQLCA)` |
| `MessageBox(...)` | `PB.MessageBox(...)` |
| GOTO/LABEL | 不译：整函数回退 TODO 并标注（计入覆盖率报告） |
| 事件块 | `onXxx(...)` 方法 + 基类 `TriggerEvent` 分发；`on x.create/destroy` → constructor/destructor |
| 祖先 `from n_xxx` | `extends N_xxx` + 对象间 `import`（生成类互引） |
| 全局函数 | `global-functions.ts` 导出 |

NULL 简化策略（本轮选定）：条件比较走 `PB.eq/ne/lt/le/gt/ge`；算术保持原生运算符；显式 `IsNull/SetNull` 原样保留；"DB/GetItem 取值直接参与运算"的表达式列入 null 风险清单，不自动改写。

### 4. `pb-runtime.ts` 扩充（按语料频率，真实实现）
`MessageBox`、`SQLCA` + `commit/rollback`、`TriggerEvent` 分发语义、`Open/Close/OpenSheet/Timer`、字符串（`Fill/Replace/LastPos`…）、日期（`DaysAfter/Year/Month/Day`…）、数值（`Abs/Mod`…）、`UpperBound/LowerBound`、`FileRead/Seek` 等。未覆盖函数由报告列出，不静默缺漏。

### M2 验收标准（golden 语料上）
- 函数体按语句计的非回退翻译率 ≥70%；goto 函数 100% 被识别并回退标注（不产生错误代码）。
- 全部 golden 产物 `npx tsc --noEmit` 0 错误。
- `notes/convert-report.md` 含翻译率、未解析语句 top-N、null 风险清单。

## 批次安排（执行顺序）
1. **批次1**：M1.1+M1.2 抽取/转换 bug 修 + `pbltext.py` 公共化（含巨型 block 成因诊断脚本）。
2. **批次2**：CLI + golden fixtures + pytest + 覆盖率报告 → 建立回归防线。
3. **批次3**：`pslexer.py` + `psparser.py`（AST dump + 单测）。
4. **批次4**：`tsbuilder.py` 翻译规则接入管线 + golden 冻结。
5. **批次5**：`pb-runtime.ts` 扩充 + 全量语料试跑出报告。

## 明确不做（本轮）
- PBD p-code 反编译（列入路线图，先做目录表正规解析的调研结论）。
- DataWindow `.dwo/.srd` 列解析、UI 框架映射。
- GOTO 自动结构化、NULL 三值逻辑全保真（可选后续项）。
- 嵌入 SQL 参数化改写（语料低频，仅 SqlBlock 保留原文）。

## 交付物
- `converter/`：修复后的 extract_pbl/convert/batch + 新增 `pbltext.py`、`pslexer.py`、`psparser.py`、`tsbuilder.py`。
- `tests/`（pytest + golden fixtures）、`tools/coverage_report.py`、`tools/`（pbtots 调试脚本搬入）。
- `notes/convert-report.md`、更新的 README（含路线图：DataWindow/SQL/UI/PBD）。

## 风险与对策
- 巨型 block 成因未完全定性 → 批次1 先跑诊断脚本核实（可能是多函数连排被吞），再定截断规则。
- `goto` 高频（gy_pyybjk 752 处）→ 翻译率指标按回退容忍，报告单独列 goto 函数清单供人工迁移。
- pbtots 旧产物是旧规则生成的，与新输出必有 diff → golden 以新规则重生成后冻结为准，pbtots 仅抽样对照。
# PyPbdViewer — PowerBuilder PBD/PBL 反编译器

将 C# WPF 版 PbdViewer 移植到 Python，支持 PB9 PBD 文件反编译为可读的伪 PB 代码。



***

## 致谢

本项目的二进制格式分析和 P-Code 反编译逻辑参考了以下开源项目和工具，感谢各位作者的工作：



| 项目                         | 语言          | 作者 / 来源                                | 贡献                                                                                                                   |
| -------------------------- | ----------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **PbdViewer**              | C# WPF      | 原始项目（本项目移植自它）                          | 核心反编译逻辑、PCODE\_LEN\_ARRAY 547 字节表                                                                                    |
| **PblDump**                | C++         | Anatoly Moskovsky \<avm@sqlbatch.com\> | PBL B+ 树遍历、ENT\* 提取、二进制结构参考（pbldump-1.3.1）                                                                       |
| **PBL Analyzer**           | 文档          | 匿名（pblanalyzer-master）              | PBL\_File\_Format.txt 完整格式文档（2003-2012）、FRE\*/NOD\*/ENT\*/DAT\* 块结构                                                   |
| **PBL Exporter**           | C#          | 匿名（PblExporter-master）               | ORCA API 调用方式、对象导出参考                                                                                                 |
| **PBSCAnalyzer**           | C#          | 匿名（PBSCAnalyzer-master）              | ORCA session 封装、IDE 风格分析                                                                                             |
| **PowerBuilder-decompile** | Python      | 匿名（GitHub: PowerBuilder-decompile）   | 完整 SM\_ opcode 名字表（500+ 条）、arg\_num 参数个数、栈操作语义参考；直接修正了 opcode 0x125 (SM\_POP) 和 0x1BC (SM\_PUSH\_FUNC\_CLASS plen=2) |
| **pb-libpbc**              | C++         | 匿名（pb-libpbc-master）               | pbl\_format.h 头文件、ORCA SDK 底层封装                                                                                      |
| **pb-pbldump**             | C++         | 匿名（pb-pbldump-master）              | PBLMI 格式补充                                                                                                           |
| **powerbuilder-pbl-dump**  | Python/C++  | Arnd Schmidt（PB 规范）                    | PBL 提取工具、pbl-spec.txt 规范文档                                                                                           |
| **PblViewer**              | C++         | 匿名（pblviewer_1_1）                   | PowerBuilder Library Viewer                                                                                          |
| **PBKiller**               | Delphi/汇编  | Kivens.Jiang（商业软件 v2.5.18）          | 反编译输出参考（.srw/.sru/.srm 标准 PB 源码格式）、VMProtect 加壳分析                                                                 |



***

## 二进制格式参考来源



* `pblanalyzer-master/PBL_File_Format.txt` — 完整 PBL 块结构文档

* `powerbuilder-pbl-dump-master/pbl-spec.txt` — B+ 树遍历规范

* `pb-libpbc-master/pblmi/pbl_format.h` — C++ 结构定义

* `PowerBuilder-decompile-main/pbd/pcode.py` — SM\_ opcode 名字表（500+ 条）

* `PowerBuilder-decompile-main/pbd/definitions.py` — 类型 / 枚举定义



***

## 用法



```
\# 反编译单个 PBD

python py/decompile.py \<input.pbd> \<output\_dir>

\# 批量反编译目录

python py/batch.py \<input\_dir> \<output\_dir>
```



***

## 支持版本



| PB 版本  | Pdb Version | 状态                  |
| ------ | ----------- | ------------------- |
| PB 7   | 114         | 部分支持                |
| PB 8   | 166         | 已支持              |
| PB 9   | 193         | 主要支持目标              |
| PB 10+ | 193+        | 已转换 opcode 表（未测试验证） |

约 42 处失败（0.34%），主要是栈不平衡连锁反应和少数 SQL 操作栈模型问题，不影响结构识别。
#define FAKECSHARP
using System;
using System.Collections.Generic;
using System.Linq;
using HISWebInterface;
using PbdViewer.Uitils.PbClass;
using PbdViewer.Uitils.PCode;

namespace PbdViewer.Uitils
{
    // Token: 0x0200000A RID: 10
    public static class PCodeHelper
    {

        //记录所有的跳转点
        public static Dictionary<ushort, bool> JumpPCodes = new Dictionary<ushort, bool>();


        // Token: 0x0600001B RID: 27 RVA: 0x000025B4 File Offset: 0x000007B4
        public static IEnumerable<string> ParsePCode(PbFunction pbFunction, bool depth)
        {
            if (pbFunction.Project.IsDebug && !depth)
            {
                return PCodeHelper.PrivaeParsePCode(pbFunction, false);
            }
            List<string> list = new List<string>();
            foreach (string text in PCodeHelper.PrivaeParsePCode(pbFunction, depth))
            {
                string[] array = text.Split(new char[]
                {
                    '\r',
                    '\n'
                }, StringSplitOptions.RemoveEmptyEntries);
                int i = 0;
                while (i < array.Length)
                {
                    string text2 = array[i];
                    string text3 = text2;
                    if (pbFunction.Project.IsDebug)
                    {
                        goto IL_78;
                    }
                    text3 = text2.Substring(48);
                    if (!string.IsNullOrWhiteSpace(text3))
                    {
                        goto IL_78;
                    }
                IL_80:
                    i++;
                    continue;
                IL_78:
                    list.Add(text3);
                    goto IL_80;
                }
            }
            return list;
        }

        // Token: 0x0600001C RID: 28 RVA: 0x00002670 File Offset: 0x00000870
        private static IEnumerable<string> PrivaeParsePCode(PbFunction pbFunction, bool depth)
        {
            ushort version = pbFunction.Project.Version;
            PCodeHelper.Init(version);
            Dictionary<ushort, CodeLine> dictionary = new Dictionary<ushort, CodeLine>();
            if (pbFunction.PCodeBytes.Length == 0)
            {
                return from o in dictionary
                       select o.ToString();
            }
            PCodeParserBase pcodeParse = PCodeHelper.GetPCodeParse(pbFunction, pbFunction.Project.Version);
            //var tmp = pcodeParse.GetArray(pbFunction.Project.FilePath);
            //Console.WriteLine(tmp);
            if (pcodeParse == null)
            {
                return from o in dictionary
                       select o.ToString();
            }
            Dictionary<ushort, ushort> dictionary2 = new Dictionary<ushort, ushort>();
            for (int i = 0; i < pbFunction.DebugBytes.Length / 4; i++)
            {
                byte[] buffer = BufferHelper.GetBuffer(pbFunction.DebugBytes, (long)(i * 4), 4);
                dictionary2[BufferHelper.GetUShort(buffer, 2L)] = BufferHelper.GetUShort(buffer, 0L);
            }
            bool flag = false;
            ushort num = 0;
            CodeLine codeLine = null;
            while ((int)num < pbFunction.PCodeBytes.Length)
            {
                ushort @ushort = BufferHelper.GetUShort(pbFunction.PCodeBytes, (long)((ulong)num));
                byte pcodeLen = pcodeParse.GetPCodeLen(@ushort);
                if (pcodeLen == 255)
                {
                    flag = true;
                    break;
                }

                //获取代码
                CodeLine codeLine2 = new CodeLine
                {
                    PCodePositon = num,
                    DebugLine = (dictionary2.ContainsKey(num) ? new ushort?(dictionary2[num]) : null),
                    PCodeOp = @ushort,
                    PCodeParam = BufferHelper.GetBuffer(pbFunction.PCodeBytes, (long)(num + 2), (int)(pcodeLen * 2))
                };
                //代码链
                if (codeLine != null)
                {
                    codeLine.NextCodeLine = codeLine2;
                    codeLine2.PreCodeLine = codeLine;
                }
                codeLine = codeLine2;
                if (depth)
                {
                    try
                    {
                        if (!flag)
                        {
                            pcodeParse.ParsePCode(codeLine2);
                            if (codeLine2.SCode.StartsWith("--") && !PCodeHelper.UnParsedPCodeList[version].Contains(codeLine2.PCodeOp))
                            {
                                PCodeHelper.UnParsedPCodeList[version].Add(codeLine2.PCodeOp);
                            }
                        }
                    }
                    catch (Exception)
                    {
                        flag = true;
                    }
                }
                PCodeHelper.UsedPCodeList[version].Add(codeLine2.PCodeOp);
                dictionary.Add(codeLine2.PCodePositon, codeLine2);
                num += (ushort)(2 + pcodeLen * 2);
                //if(!string.IsNullOrEmpty(codeLine2.SCode))
                //    Log.Info(codeLine2.SCode);
            }
            if (depth)
            {
                try
                {
                    PCodeHelper.ParseJmp(pbFunction, dictionary);
                }
                catch (Exception ex)
                {
                    Console.Write("ExceptionException"+ex.Message);
                    flag = true;
                }
            }
            ushort key;
            int num2;
            if (!flag)
            {
                Dictionary<ushort, int> goodcount = PCodeHelper.Goodcount;
                key = version;
                num2 = goodcount[key];
                goodcount[key] = num2 + 1;
            }
            Dictionary<ushort, int> count = PCodeHelper.Count;
            key = version;
            num2 = count[key];
            count[key] = num2 + 1;
            return from o in dictionary.Values
                   select o.ToString();
        }

        // Token: 0x0600001D RID: 29 RVA: 0x00002904 File Offset: 0x00000B04
        private static void ParseJmp(PbFunction pbFunction, Dictionary<ushort, CodeLine> list)
        {
            PCodeHelper.JumpPCodes = new Dictionary<ushort, bool>();
            PCodeHelper.ParseReverseJmp(list);
            List<CodeArea> areas = new List<CodeArea>();
            if (pbFunction.Project.Version >= 283)
            {
                PCodeHelper.ParseReturn(list);
            }
            //不能调整这里的顺序
            PCodeHelper.ParseTryCatchFinally(list, areas);
            PCodeHelper.ParseChoose(list, areas);
            PCodeHelper.ParseForNext(list, areas);
            PCodeHelper.ParseDoLoop(list, areas);
            PCodeHelper.ParseExitContinue(list, areas);
            PCodeHelper.ParseIfElse(list);
            PCodeHelper.ParseGoto(list);
            PCodeHelper.ParseEventReturn(list);
            PCodeHelper.ParseIndent(pbFunction, list);
        }

        // Token: 0x0600001E RID: 30 RVA: 0x0000296C File Offset: 0x00000B6C
        private static void ParseReturn(Dictionary<ushort, CodeLine> list)
        {
            foreach (CodeLine codeLine in list.Values)
            {
                if (codeLine.SCode.StartsWith("return ") && codeLine.NextCodeLine.JmpType == JmpType.Jmp && list[codeLine.NextCodeLine.JmpPositon].SCode == "return")
                {
                    codeLine.NextCodeLine.SCode = "";
                    codeLine.NextCodeLine.JmpType = JmpType.None;
                }
            }
        }

        // Token: 0x0600001F RID: 31 RVA: 0x00002A18 File Offset: 0x00000C18
        private static void ParseTryCatchFinally(Dictionary<ushort, CodeLine> list, List<CodeArea> areas)
        {
            foreach (CodeLine codeLine in list.Values)
            {
                if (!string.IsNullOrEmpty(codeLine.SCode))
                {
                    if (codeLine.JmpType == JmpType.JmpIfFalse && codeLine.Condition.StartsWith("catch ("))
                    {
                        codeLine.SCode = codeLine.Condition;
                        codeLine.JmpType = JmpType.None;
                        if (list[codeLine.JmpPositon].SCode != null && !list[codeLine.JmpPositon].SCode.StartsWith("end try ") && !list[codeLine.JmpPositon].SCode.StartsWith("enter finally ") && list[codeLine.JmpPositon].PreCodeLine.JmpType == JmpType.Jmp && (list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].SCode.StartsWith("end try ") || list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].SCode.StartsWith("enter finally ")))
                        {
                            list[codeLine.JmpPositon].PreCodeLine.SCode = "";
                            list[codeLine.JmpPositon].PreCodeLine.JmpType = JmpType.None;
                        }
                    }
                    if (list[codeLine.JmpPositon].SCode != null && (codeLine.JmpType == JmpType.Jmp && (list[codeLine.JmpPositon].SCode.StartsWith("end try ") || list[codeLine.JmpPositon].SCode.StartsWith("enter finally "))))
                    {
                        codeLine.SCode = "";
                        codeLine.JmpType = JmpType.None;
                    }
                    if (codeLine.SCode == "enter finally ")
                    {
                        codeLine.SCode = "";
                        list[codeLine.JmpPositon].LabelSCode.Add("finally ");
                    }
                }
            }
        }

        // Token: 0x06000020 RID: 32 RVA: 0x00002C30 File Offset: 0x00000E30
        private static void ParseChoose(Dictionary<ushort, CodeLine> list, List<CodeArea> areas)
        {



            Dictionary<string, CodeArea> dictionary = new Dictionary<string, CodeArea>();
            foreach (CodeLine codeLine in list.Values)
            {
                if (!string.IsNullOrEmpty(codeLine.SCode))
                {
                    if (codeLine.SCode.StartsWith("\u0001case"))
                    {
                        string text = codeLine.SCode.Substring(0, codeLine.SCode.IndexOf('=')).Trim();
                        string tmp = codeLine.SCode.Substring(codeLine.SCode.IndexOf('=') + 1).Trim();
                        codeLine.SCode = codeLine.SCode.Replace(text + " = ", "choose case ");
                        codeLine.CSharpCode = "switch(" + tmp + "){";
                        dictionary[text] = new CodeArea
                        {
                            Type = "choose",
                            Start = codeLine.PCodePositon
                        };
                        if (!PCodeHelper.JumpPCodes.ContainsKey(codeLine.PCodePositon))
                            PCodeHelper.JumpPCodes.Add(codeLine.PCodePositon, true);
                    }
                    if (codeLine.JmpType == JmpType.JmpIfFalse && codeLine.JmpPositon > codeLine.PCodePositon && codeLine.Condition.Contains("\u0001"))
                    {
                        string text2 = "";
                        foreach (KeyValuePair<string, CodeArea> keyValuePair in dictionary)
                        {
                            if (codeLine.Condition.EndsWith(keyValuePair.Key) || codeLine.Condition.Contains(keyValuePair.Key + " "))
                            {
                                text2 = keyValuePair.Key;
                                break;
                            }
                        }

                        if (!PCodeHelper.JumpPCodes.ContainsKey(codeLine.PCodePositon))
                            PCodeHelper.JumpPCodes.Add(codeLine.PCodePositon, true);
                        if (!string.IsNullOrEmpty(text2))
                        {
                            if (codeLine.Condition.Contains(string.Format(" <= {0} and ", text2)))
                            {
                                codeLine.SCode = "case " + codeLine.Condition.Replace(string.Format(" <= {0} and ", text2), " to ").Replace(string.Format(" >= {0}", text2), "");
                            }
                            else if (codeLine.Condition.EndsWith(string.Format(" = {0}", text2)))
                            {
                                codeLine.SCode = "case " + codeLine.Condition.Replace(string.Format(" = {0}", text2), "");
                            }
                            else if (codeLine.Condition.Contains(string.Format(" <= {0}", text2)))
                            {
                                codeLine.SCode = "case is >= " + codeLine.Condition.Replace(string.Format(" <= {0}", text2), "");
                            }
                            else if (codeLine.Condition.Contains(string.Format(" >= {0}", text2)))
                            {
                                codeLine.SCode = "case is <= " + codeLine.Condition.Replace(string.Format(" >= {0}", text2), "");
                            }
                            else if (codeLine.Condition.Contains(string.Format(" < {0}", text2)))
                            {
                                codeLine.SCode = "case is > " + codeLine.Condition.Replace(string.Format(" < {0}", text2), "");
                            }
                            else if (codeLine.Condition.Contains(string.Format(" > {0}", text2)))
                            {
                                codeLine.SCode = "case is < " + codeLine.Condition.Replace(string.Format(" > {0}", text2), "");
                            }

                            codeLine.CSharpCode = codeLine.SCode + ":{" + String.Format("///{0:X4}->{1:X4}", codeLine.PCodePositon, codeLine.JmpPositon);

                            if (!PCodeHelper.JumpPCodes.ContainsKey(list[codeLine.JmpPositon].PCodePositon))
                                PCodeHelper.JumpPCodes.Add(list[codeLine.JmpPositon].PCodePositon, true);

                            if (list[codeLine.JmpPositon].LabelSCode.IndexOf("end case") == -1)
                            {
                                list[codeLine.JmpPositon].LabelSCode.Insert(0, "end case");
                            }

                            codeLine.JmpType = JmpType.None;
                            CodeLine preCodeLine = codeLine.PreCodeLine;
                            while (string.IsNullOrEmpty(preCodeLine.SCode))
                            {
                                preCodeLine = preCodeLine.PreCodeLine;
                            }

                            if (preCodeLine.SCode.StartsWith("case else "))
                            {
                                preCodeLine.SCode = "";
                                preCodeLine.CSharpCode = "";
                            }

                          

                            if (list[codeLine.JmpPositon].PreCodeLine.JmpType == JmpType.Jmp)
                            {

                                if (!PCodeHelper.JumpPCodes.ContainsKey(codeLine.JmpPositon))
                                    PCodeHelper.JumpPCodes.Add(codeLine.JmpPositon, true);
                                if (!PCodeHelper.JumpPCodes.ContainsKey(list[codeLine.JmpPositon].PreCodeLine.JmpPositon))
                                    PCodeHelper.JumpPCodes.Add(list[codeLine.JmpPositon].PreCodeLine.JmpPositon, true);
                                if (!PCodeHelper.JumpPCodes.ContainsKey(list[codeLine.JmpPositon].PreCodeLine.PCodePositon))
                                    PCodeHelper.JumpPCodes.Add(list[codeLine.JmpPositon].PreCodeLine.PCodePositon, true);

                                if(list[codeLine.JmpPositon].LabelSCode.IndexOf("end case")>=0)
                                {
                                    //已经是最后一个case,case else 必须放再 end case后面


                                    list[codeLine.JmpPositon].LabelSCode.Add("case else " + String.Format("///{0:X4}->{1:X4}", codeLine.JmpPositon, list[codeLine.JmpPositon].PreCodeLine.JmpPositon));
                                    if(list[codeLine.JmpPositon].PreCodeLine.SCode.StartsWith("goto"))
                                    {
                                        list[codeLine.JmpPositon].PreCodeLine.SCode = "";
                                    }
                                }
                                else
                                {
                                    list[codeLine.JmpPositon].PreCodeLine.SCode = "case else " + String.Format("///{0:X4}->{1:X4}", codeLine.JmpPositon, list[codeLine.JmpPositon].PreCodeLine.JmpPositon);
                                   
                                }
                                if (list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].LabelSCode.IndexOf("end case") == -1)
                                {
                                    //最后只要保留一个end case就可以
                                    list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].LabelSCode.Insert(0, "end case");
                                }

                                //list[codeLine.JmpPositon].PreCodeLine.CSharpCode = "default: {" + String.Format("///{0:X4}", codeLine.JmpPositon);
                                list[codeLine.JmpPositon].PreCodeLine.JmpType = JmpType.None;
                                if (dictionary[text2].End == 0)
                                {


                                    list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].LabelSCode.Add("end choose " + String.Format("///{0:X4}->{1:X4}", codeLine.JmpPositon, list[codeLine.JmpPositon].PreCodeLine.JmpPositon));
                                    //list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].LabelCSharpCode.Insert(0, "} ");
                                    dictionary[text2].End = list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].PreCodeLine.PCodePositon;
                                }
                            }
                            else if (dictionary[text2].End == 0)
                            {
                                if (!PCodeHelper.JumpPCodes.ContainsKey(codeLine.JmpPositon))
                                    PCodeHelper.JumpPCodes.Add(codeLine.JmpPositon, true);
                                list[codeLine.JmpPositon].LabelSCode.Add("end choose " + String.Format("///{0:X4}", codeLine.JmpPositon));
                                //list[codeLine.JmpPositon].LabelCSharpCode.Insert(0, "} //end switch ");
                                dictionary[text2].End = list[codeLine.JmpPositon].PreCodeLine.PCodePositon;
                            }
                        }
                    }
                }
            }
            areas.AddRange(dictionary.Values);
        }

        // Token: 0x06000021 RID: 33 RVA: 0x0000310C File Offset: 0x0000130C
        private static void ParseForNext(Dictionary<ushort, CodeLine> list, List<CodeArea> areas)
        {
            foreach (CodeLine codeLine in list.Values)
            {
                if (!string.IsNullOrEmpty(codeLine.SCode) && codeLine.JmpType == JmpType.JmpIfFalse && codeLine.JmpPositon > codeLine.PCodePositon && list[codeLine.JmpPositon].PreCodeLine.JmpType == JmpType.Jmp && list[codeLine.JmpPositon].PreCodeLine.JmpPositon < list[codeLine.JmpPositon].PreCodeLine.PCodePositon && list[codeLine.JmpPositon].PreCodeLine.JmpPositon < codeLine.PCodePositon)
                {
                    CodeLine preCodeLine = list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].PreCodeLine;
                    if (preCodeLine != null && preCodeLine.JmpType == JmpType.Jmp)
                    {
                        string[] array = codeLine.Condition.Split(new char[]
                        {
                            '>',
                            '<',
                            '=',
                            ' '
                        }, StringSplitOptions.RemoveEmptyEntries);
                        if (array.Length > 1)
                        {
                            CodeLine preCodeLine2 = codeLine.PreCodeLine;
                            while (string.IsNullOrEmpty(preCodeLine2.SCode))
                            {
                                preCodeLine2 = preCodeLine2.PreCodeLine;
                            }
                            string arg = "";
                            if (preCodeLine2.SCode.StartsWith(string.Format("{0} += ", array[1])))
                            {
                                arg = "step " + preCodeLine2.SCode.Substring(string.Format("{0} += ", array[1]).Length);
                            }



                            codeLine.CSharpCode = string.Format("for({0};{1};{2}){{", list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].PreCodeLine.PreCodeLine.SCode, codeLine.Condition, preCodeLine2.SCode.Replace(" ", ""));
                            preCodeLine2.SCode = "";
                            codeLine.SCode = string.Format("for {0} to {1} {2}", list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].PreCodeLine.PreCodeLine.SCode, array[0], arg);
                            codeLine.SCode += string.Format("/*{0:X4}*/  ", codeLine.PCodePositon);
                            codeLine.JmpType = JmpType.None;
                            list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].PreCodeLine.PreCodeLine.SCode = "";
                            list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].PreCodeLine.SCode = "";
                            list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].PreCodeLine.JmpType = JmpType.None;
                            list[codeLine.JmpPositon].PreCodeLine.SCode = "next //" + string.Format("/*{0:X4}*/  ", codeLine.PCodePositon);
                            list[codeLine.JmpPositon].PreCodeLine.CSharpCode = "}" + string.Format("/*{0:X4}*/  ", codeLine.PCodePositon);
                            list[codeLine.JmpPositon].PreCodeLine.JmpType = JmpType.None;
                            areas.Add(new CodeArea
                            {
                                Type = "for",
                                Start = codeLine.PCodePositon,
                                End = list[codeLine.JmpPositon].PreCodeLine.PCodePositon
                            });
                        }
                    }
                }
            }
        }

        // Token: 0x06000022 RID: 34 RVA: 0x0000340C File Offset: 0x0000160C
        private static void ParseDoLoop(Dictionary<ushort, CodeLine> list, List<CodeArea> areas)
        {
            foreach (CodeLine codeLine in list.Values)
            {
                if (!string.IsNullOrEmpty(codeLine.SCode))
                {
                    if (codeLine.JmpType == JmpType.JmpIfFalse)
                    {
                        if (codeLine.JmpPositon > codeLine.PCodePositon)
                        {
                            if (list[codeLine.JmpPositon].PreCodeLine.JmpType == JmpType.Jmp && list[codeLine.JmpPositon].PreCodeLine.JmpPositon < list[codeLine.JmpPositon].PreCodeLine.PCodePositon && list[codeLine.JmpPositon].PreCodeLine.JmpPositon < codeLine.PCodePositon)
                            {
                                codeLine.SCode = string.Format("do while {0}", codeLine.Condition);
                                codeLine.CSharpCode = string.Format("while( {0}){{", codeLine.Condition);
                                codeLine.JmpType = JmpType.None;
                                list[codeLine.JmpPositon].PreCodeLine.SCode = "loop ";
                                list[codeLine.JmpPositon].PreCodeLine.CSharpCode = "}";
                                list[codeLine.JmpPositon].PreCodeLine.JmpType = JmpType.None;
                                areas.Add(new CodeArea
                                {
                                    Type = "do",
                                    Start = codeLine.PCodePositon,
                                    End = list[codeLine.JmpPositon].PreCodeLine.PCodePositon
                                });
                            }
                        }
                        else
                        {
                            list[codeLine.JmpPositon].LabelSCode.Add("do ");
                            list[codeLine.JmpPositon].LabelCSharpCode.Add("do{");
                            codeLine.SCode = string.Format("loop until {0}", codeLine.Condition);
                            codeLine.CSharpCode = string.Format("}}while(!({0}));", codeLine.Condition);
                            codeLine.JmpType = JmpType.None;
                            areas.Add(new CodeArea
                            {
                                Type = "do",
                                Start = list[codeLine.JmpPositon].PCodePositon,
                                End = codeLine.PCodePositon
                            });
                        }
                    }
                    else if (codeLine.JmpType == JmpType.JmpIfTrue)
                    {
                        if (codeLine.JmpPositon > codeLine.PCodePositon)
                        {
                            if (list[codeLine.JmpPositon].PreCodeLine.JmpType == JmpType.Jmp && list[codeLine.JmpPositon].PreCodeLine.JmpPositon < list[codeLine.JmpPositon].PreCodeLine.PCodePositon && list[codeLine.JmpPositon].PreCodeLine.JmpPositon < codeLine.PCodePositon)
                            {
                                codeLine.SCode = string.Format("do until {0}", codeLine.Condition);
                                codeLine.CSharpCode = string.Format("while( !({0})){{", codeLine.Condition);
                                codeLine.JmpType = JmpType.None;
                                list[codeLine.JmpPositon].PreCodeLine.SCode = "loop ";
                                list[codeLine.JmpPositon].PreCodeLine.CSharpCode = "}";
                                list[codeLine.JmpPositon].PreCodeLine.JmpType = JmpType.None;
                                areas.Add(new CodeArea
                                {
                                    Type = "do",
                                    Start = codeLine.PCodePositon,
                                    End = list[codeLine.JmpPositon].PreCodeLine.PCodePositon
                                });
                            }
                        }
                        else
                        {
                            list[codeLine.JmpPositon].LabelSCode.Add("do ");
                            list[codeLine.JmpPositon].LabelCSharpCode.Add("do{");
                            codeLine.SCode = string.Format("loop while {0}", codeLine.Condition);
                            codeLine.CSharpCode = string.Format("}}while({0});", codeLine.Condition);
                            codeLine.JmpType = JmpType.None;
                            areas.Add(new CodeArea
                            {
                                Type = "do",
                                Start = list[codeLine.JmpPositon].PCodePositon,
                                End = codeLine.PCodePositon
                            });
                        }
                    }
#if FAKECSHARP
                    list[codeLine.JmpPositon].LabelSCode.Clear();
#else
                  
                    list[codeLine.JmpPositon].LabelCSharpCode.Clear();
#endif

                }
            }
        }

        // Token: 0x06000023 RID: 35 RVA: 0x00003798 File Offset: 0x00001998
        private static void ParseExitContinue(Dictionary<ushort, CodeLine> list, List<CodeArea> areas)
        {
            if (areas.Count == 0)
            {
                return;
            }
            using (Dictionary<ushort, CodeLine>.ValueCollection.Enumerator enumerator = list.Values.GetEnumerator())
            {
                while (enumerator.MoveNext())
                {
                    CodeLine codeLine = enumerator.Current;
                    if (!string.IsNullOrEmpty(codeLine.SCode) && codeLine.JmpType == JmpType.Jmp && codeLine.JmpPositon > codeLine.PCodePositon)
                    {
                        CodeArea codeArea = (from o in areas
                                             orderby Math.Abs((int)(codeLine.PCodePositon - o.Start)) + Math.Abs((int)(o.End - codeLine.PCodePositon))
                                             select o).First<CodeArea>();
                        if (codeLine.PCodePositon >= codeArea.Start && codeLine.PCodePositon <= codeArea.End)
                        {
                            if (list[codeLine.JmpPositon].PreCodeLine.PCodePositon == codeArea.End)
                            {
                                codeLine.SCode = "exit";
                                codeLine.CSharpCode = "break ";
                                codeLine.JmpType = JmpType.None;
                            }
                            else if (list[codeLine.JmpPositon].PCodePositon == codeArea.End)
                            {
                                codeLine.SCode = "continue";
                                codeLine.CSharpCode = "continue; ";
                                codeLine.JmpType = JmpType.None;
                            }
                        }
                    }
                }
            }
        }

        private static void ParseReverseJmp(Dictionary<ushort, CodeLine> list)
        {
            foreach (CodeLine codeLine in list.Values)
            {
                if (codeLine.JmpPositon > 0)
                {
                    list[codeLine.JmpPositon].PreCodeLine.ReverseJmpPositon = codeLine.PCodePositon;

                }
            }

        }


        // Token: 0x06000024 RID: 36 RVA: 0x00003908 File Offset: 0x00001B08
        private static void ParseIfElse(Dictionary<ushort, CodeLine> list)
        {
            try
            {

           
            Dictionary<ushort, ushort> ifArea = new Dictionary<ushort, ushort>();

            foreach (CodeLine codeLine in list.Values)
            {
                //false跳转，直接跳转到else的下面一句语句
                if (!string.IsNullOrEmpty(codeLine.SCode) && codeLine.JmpType == JmpType.JmpIfFalse && codeLine.JmpPositon > codeLine.PCodePositon)
                {
                    //加入jmp点标签
                    if (!PCodeHelper.JumpPCodes.ContainsKey(codeLine.JmpPositon))
                        PCodeHelper.JumpPCodes.Add(codeLine.JmpPositon, true);
                    if (!PCodeHelper.JumpPCodes.ContainsKey(codeLine.PCodePositon))
                        PCodeHelper.JumpPCodes.Add(codeLine.PCodePositon, true);
                    if (!PCodeHelper.JumpPCodes.ContainsKey(list[codeLine.JmpPositon].PreCodeLine.JmpPositon))
                        PCodeHelper.JumpPCodes.Add(list[codeLine.JmpPositon].PreCodeLine.JmpPositon, true);

                    string jmpstr = string.Format("///pos:{0:x4}->jmp:{1:x4}", codeLine.PCodePositon, codeLine.JmpPositon);
                    ifArea.Add(codeLine.PCodePositon, codeLine.JmpPositon);

                    //JmpPositon跳转位置的上一句是一个跳转语句
                    if (list[codeLine.JmpPositon].PreCodeLine.JmpType == JmpType.Jmp && list[codeLine.JmpPositon].PreCodeLine.JmpPositon > list[codeLine.JmpPositon].PreCodeLine.PCodePositon)
                    {
#if FAKECSHARP
						codeLine.SCode = string.Format("if {0} then ", codeLine.Condition) + jmpstr;
#else
                        codeLine.SCode = string.Format("if {0} then ", codeLine.Condition) + jmpstr;
#endif
                        codeLine.JmpType = JmpType.None;


                        //JmpPositon跳转位置的上一句是一个跳转语句是exit或者continue
                        if (list[codeLine.JmpPositon].PreCodeLine.SCode == "exit" || list[codeLine.JmpPositon].PreCodeLine.SCode == "continue")
                        {
                            list[codeLine.JmpPositon].PreCodeLine.JmpType = JmpType.None;
                            list[codeLine.JmpPositon].LabelSCode.Insert(0, "end if " + jmpstr);
                        }
                        else
                        {
                            //这里存在两种情况，else跳转和goto跳转，单语句无法区分
                            if (list[codeLine.JmpPositon].NextCodeLine != null
                                && list[codeLine.JmpPositon].PreCodeLine.SCode.Trim().StartsWith("goto"))
                            {
                                //list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].LabelSCode.Insert(0, "///" + list[codeLine.JmpPositon].PreCodeLine.SCode + ":");

                                //CodeLine revserse = list[codeLine.JmpPositon].PreCodeLine;
                                //while (revserse!=null)
                                //                        {
                                //	if(revserse.SCode.Trim().StartsWith("if"))
                                //                            {


                                //		break;

                                //	}
                                //                        }

                                if (list[codeLine.JmpPositon].PreCodeLine.ReverseJmpPositon > 0)
                                {
                                    jmpstr = string.Format("///pos:{0:x4}->jmp:{1:x4}->next_jmp:{2:x4}", codeLine.PCodePositon, codeLine.JmpPositon, list[codeLine.JmpPositon].PreCodeLine.JmpPositon);

                                    list[codeLine.JmpPositon].PreCodeLine.SCode = " else //" + list[codeLine.JmpPositon].PreCodeLine.SCode + jmpstr;
                                }


                            }
                            else
                            {
                                list[codeLine.JmpPositon].PreCodeLine.SCode = "else " + jmpstr;
                            }

                            //start line: codeLine.PCodePositon
                            //end line :list[codeLine.JmpPositon].PreCodeLine.JmpPositon

                            jmpstr = string.Format("///pos:{0:x4}->jmp:{1:x4}->next_jmp:{2:x4}", codeLine.PCodePositon, codeLine.JmpPositon, list[codeLine.JmpPositon].PreCodeLine.JmpPositon);

                            list[codeLine.JmpPositon].PreCodeLine.JmpType = JmpType.None;
                            list[list[codeLine.JmpPositon].PreCodeLine.JmpPositon].LabelSCode.Insert(0, "end if //" + jmpstr);


                        }

                    }
                    else
                    {
                        jmpstr = string.Format("///pos:{0:x4}->jmp:{1:x4}->jmp:{2:x4}", codeLine.PCodePositon, codeLine.JmpPositon, list[codeLine.JmpPositon].PreCodeLine.JmpPositon);
                        //start line: codeLine.PCodePositon
                        //end line :codeLine.JmpPositon
                        codeLine.SCode = string.Format("if {0} then " + jmpstr, codeLine.Condition);
                        codeLine.JmpType = JmpType.None;
                        list[codeLine.JmpPositon].LabelSCode.Insert(0, "end if //" + jmpstr);
                    }

                }
            }
            int num = 0;
            HashSet<int> hashSet = new HashSet<int>();
            foreach (CodeLine codeLine2 in list.Values)
            {
                if (codeLine2.SCode != null)
                {
                    if (codeLine2.SCode.Trim().StartsWith("if "))
                    {
                        num++;
                        CodeLine firstVailiablePreCodeLine = PCodeHelper.GetFirstVailiablePreCodeLine(codeLine2.PreCodeLine);
                        if (((firstVailiablePreCodeLine != null) ? firstVailiablePreCodeLine.SCode : null) == "else ")
                        {
                            //删除无用的else，这里会和单纯的goto语句混淆在一起
                            //需要判断goto的地址是否在if .... end if 范围之内
                            CodeLine codeLine3 = firstVailiablePreCodeLine;
                            codeLine3.SCode += codeLine2.SCode;
                            codeLine2.SCode = "///--DEL--" + codeLine2.SCode;
                            hashSet.Add(num);
                        }
                    }
                    for (int i = 0; i < codeLine2.LabelSCode.Count; i++)
                    {
                        if (codeLine2.LabelSCode[i].Trim().StartsWith("end if"))
                        {
                            if (hashSet.Contains(num))
                            {
                                codeLine2.LabelSCode[i] = "///--DEL--" + codeLine2.LabelSCode[i];
                                hashSet.Remove(num);
                            }
                            num--;
                        }
                    }
                    if (codeLine2.SCode.Trim().StartsWith("end if"))
                    {
                        if (hashSet.Contains(num))
                        {
                            codeLine2.SCode = "///--DEL--" + codeLine2.SCode;
                            hashSet.Remove(num);
                        }
                        num--;
                    }
                }
            }
            }
            catch(Exception ex)
            {
                throw ex;
            }
        }

        // Token: 0x06000025 RID: 37 RVA: 0x00003C80 File Offset: 0x00001E80
        private static void ParseGoto(Dictionary<ushort, CodeLine> list)
        {
            foreach (CodeLine codeLine in list.Values)
            {
                if (!string.IsNullOrEmpty(codeLine.SCode) && codeLine.SCode.Trim().StartsWith("goto"))
                {

                    Console.WriteLine(codeLine.SCode);
                    if (!PCodeHelper.JumpPCodes.ContainsKey(codeLine.JmpPositon))
                        PCodeHelper.JumpPCodes.Add(codeLine.JmpPositon, true);
                    //string label = "label" + codeLine.SCode.Trim().Split(' ')[1] + ":";
                    string label = codeLine.SCode.Trim().Split(' ')[1] + ":";
                    JmpType jmpType = codeLine.JmpType;
                    bool found = false;
                    foreach (string item in list[codeLine.JmpPositon].LabelSCode)
                    {
                        if (item == label)
                        {
                            found = true;
                            break;
                        }
                    }
                    if (!found)
                    {
                        list[codeLine.JmpPositon].LabelSCode.Insert(0, label);
                    }

                }
            }
        }

        // Token: 0x06000026 RID: 38 RVA: 0x00003CE4 File Offset: 0x00001EE4
        private static void ParseEventReturn(Dictionary<ushort, CodeLine> list)
        {
            foreach (CodeLine codeLine in list.Values)
            {
                if (codeLine.SCode != null && codeLine.SCode.Trim().StartsWith("if isvalid(::message) then goto "))
                {
                    CodeLine firstVailiableNextCodeLine = PCodeHelper.GetFirstVailiableNextCodeLine(codeLine);
                    if (firstVailiableNextCodeLine != null && firstVailiableNextCodeLine.SCode.Trim().Equals("return 0"))
                    {
                        CodeLine firstVailiableNextCodeLine2 = PCodeHelper.GetFirstVailiableNextCodeLine(firstVailiableNextCodeLine);
                        if (firstVailiableNextCodeLine2 != null && firstVailiableNextCodeLine2.SCode.Trim().StartsWith("goto "))
                        {
                            CodeLine firstVailiableNextCodeLine3 = PCodeHelper.GetFirstVailiableNextCodeLine(firstVailiableNextCodeLine2);
                            if (firstVailiableNextCodeLine3 != null && firstVailiableNextCodeLine3.SCode.Trim().Equals("return ::message.returnvalue"))
                            {
                                codeLine.SCode = "return";
                                firstVailiableNextCodeLine.SCode = "";
                                firstVailiableNextCodeLine2.SCode = "";
                                firstVailiableNextCodeLine3.SCode = "";
                            }
                        }
                    }
                }
                else
                {
                    //Log.Object(codeLine);
                }
            }
        }

        // Token: 0x06000027 RID: 39 RVA: 0x00003DE8 File Offset: 0x00001FE8
        private static void ParseIndent(PbFunction pbFunction, Dictionary<ushort, CodeLine> list)
        {
            int num = 0;
            foreach (CodeLine codeLine in list.Values)
            {
                try
                {
                    for (int i = 0; i < codeLine.LabelSCode.Count; i++)
                    {
                        codeLine.LabelSCode[i] = PCodeHelper.ParseIndent(codeLine.LabelSCode[i], ref num);
                    }
                    if (!string.IsNullOrEmpty(codeLine.SCode))
                    {
                        codeLine.SCode = PCodeHelper.ParseIndent(codeLine.SCode, ref num);
                    }
                }
                catch (Exception)
                {
                    break;
                }
            }
        }

        // Token: 0x06000028 RID: 40 RVA: 0x00003EA0 File Offset: 0x000020A0
        private static string ParseIndent(string scode, ref int indent)
        {
            if (scode.StartsWith("try "))
            {
                scode = "".PadRight(indent * 4) + scode;
                indent++;
            }
            else if (scode.StartsWith("catch "))
            {
                indent--;
                scode = "".PadRight(indent * 4) + scode;
                indent++;
            }
            else if (scode.StartsWith("finally "))
            {
                indent--;
                scode = "".PadRight(indent * 4) + scode;
                indent++;
            }
            else if (scode.StartsWith("end try "))
            {
                indent--;
                scode = "".PadRight(indent * 4) + scode;
            }
            else if (scode.StartsWith("if "))
            {
                scode = "".PadRight(indent * 4) + scode;
                indent++;
            }
            else if (scode.StartsWith("else "))
            {
                indent--;
                scode = "".PadRight(indent * 4) + scode;
                indent++;
            }
            else if (scode.StartsWith("end if "))
            {
                indent--;
                scode = "".PadRight(indent * 4) + scode;
            }
            else if (scode.StartsWith("for "))
            {
                scode = "".PadRight(indent * 4) + scode;
                indent++;
            }
            else if (scode.StartsWith("next "))
            {
                indent--;
                scode = "".PadRight(indent * 4) + scode;
            }
            else if (scode.StartsWith("choose case "))
            {
                scode = "".PadRight(indent * 4) + scode;
                indent++;
                indent++;
            }
            else if (scode.StartsWith("case "))
            {
                indent--;
                scode = "".PadRight(indent * 4) + scode;
                indent++;
            }
            else if (scode.StartsWith("end choose "))
            {
                indent--;
                indent--;
                scode = "".PadRight(indent * 4) + scode;
            }
            else if (scode.StartsWith("do "))
            {
                scode = "".PadRight(indent * 4) + scode;
                indent++;
            }
            else if (scode.StartsWith("loop "))
            {
                indent--;
                scode = "".PadRight(indent * 4) + scode;
            }
            else if (!string.IsNullOrEmpty(scode))
            {
                scode = "".PadRight(indent * 4) + scode;
            }
            return scode;
        }

        // Token: 0x06000029 RID: 41 RVA: 0x0000416C File Offset: 0x0000236C
        private static void Init(ushort version)
        {
            if (PCodeHelper.Count.ContainsKey(version))
            {
                return;
            }
            PCodeHelper.Count[version] = 0;
            PCodeHelper.Goodcount[version] = 0;
            PCodeHelper.UsedPCodeList[version] = new HashSet<ushort>();
            PCodeHelper.UnParsedPCodeList[version] = new HashSet<ushort>();
        }

        // Token: 0x0600002A RID: 42 RVA: 0x000041C0 File Offset: 0x000023C0
        private static PCodeParserBase GetPCodeParse(PbFunction pbFunction, ushort version)
        {
            PCodeParserBase result = null;
            if (version <= 196)
            {
                if (version <= 146)
                {
                    if (version != 79 && version != 114 && version != 146)
                    {
                        return result;
                    }
                }
                else if (version != 166 && version != 193 && version != 196)
                {
                    return result;
                }
                result = new PCodeParser90(pbFunction);
            }
            else
            {
                if (version <= 322)
                {
                    if (version == 238)
                    {
                        return new PCodeParser100(pbFunction);
                    }
                    if (version == 283)
                    {
                        return new PCodeParser105(pbFunction);
                    }
                    switch (version)
                    {
                        case 316:
                        case 319:
                        case 321:
                        case 322:
                            break;
                        case 317:
                        case 318:
                        case 320:
                            return result;
                        default:
                            return result;
                    }
                }
                else if (version != 325 && version != 333 && version != 334)
                {
                    return result;
                }
                result = new PCodeParser110(pbFunction);
            }
            return result;
        }

        // Token: 0x0600002B RID: 43 RVA: 0x00004298 File Offset: 0x00002498
        private static CodeLine GetFirstVailiablePreCodeLine(CodeLine codeLine)
        {
            CodeLine preCodeLine = codeLine.PreCodeLine;
            while (preCodeLine != null && string.IsNullOrEmpty(preCodeLine.SCode))
            {
                preCodeLine = preCodeLine.PreCodeLine;
            }
            return preCodeLine;
        }

        // Token: 0x0600002C RID: 44 RVA: 0x000042C8 File Offset: 0x000024C8
        private static CodeLine GetFirstVailiableNextCodeLine(CodeLine codeLine)
        {
            CodeLine nextCodeLine = codeLine.NextCodeLine;
            while (nextCodeLine != null && string.IsNullOrEmpty(nextCodeLine.SCode))
            {
                nextCodeLine = nextCodeLine.NextCodeLine;
            }
            return nextCodeLine;
        }

        // Token: 0x0400001D RID: 29
        public static readonly Dictionary<ushort, int> Count = new Dictionary<ushort, int>();

        // Token: 0x0400001E RID: 30
        public static readonly Dictionary<ushort, int> Goodcount = new Dictionary<ushort, int>();

        // Token: 0x0400001F RID: 31
        public static readonly Dictionary<ushort, HashSet<ushort>> UsedPCodeList = new Dictionary<ushort, HashSet<ushort>>();

        // Token: 0x04000020 RID: 32
        public static readonly Dictionary<ushort, HashSet<ushort>> UnParsedPCodeList = new Dictionary<ushort, HashSet<ushort>>();
    }
}

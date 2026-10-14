#define FAKECSHARP
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using PbdViewer.Uitils.PbClass;

namespace PbdViewer.Uitils.PCode
{
    // Token: 0x02000010 RID: 16
    internal abstract class PCodeParserBase
    {
        // Token: 0x1700000A RID: 10
        // (get) Token: 0x06000067 RID: 103
        protected abstract byte[] PCodeLenArray { get; }

        // Token: 0x06000068 RID: 104 RVA: 0x00007870 File Offset: 0x00005A70
        public void ParsePCode(CodeLine codeLine)
        {
            this._codeLine = codeLine;
            this._codeLine.SCode = "";
            if (!this.OnParsePcode((int)codeLine.PCodeOp, codeLine))
            {
                codeLine.SCode = string.Format("//无法解析的pcode-------{0:X4}", codeLine.PCodeOp);
            }
        }

        // Token: 0x06000069 RID: 105 RVA: 0x000078BE File Offset: 0x00005ABE
        public byte GetPCodeLen(ushort pcode)
        {
            return this.OnGetPCodeLen(pcode);
        }

        // Token: 0x0600006A RID: 106 RVA: 0x000078C7 File Offset: 0x00005AC7
        protected PCodeParserBase(PbFunction pbFunction)
        {
            this.PbFunction = pbFunction;
        }

        // Token: 0x0600006B RID: 107 RVA: 0x000078E1 File Offset: 0x00005AE1
        protected virtual byte OnGetPCodeLen(ushort pcode)
        {
            if ((int)pcode < this.PCodeLenArray.Length)
            {
                return this.PCodeLenArray[(int)pcode];
            }
            return byte.MaxValue;
        }

        // Token: 0x0600006C RID: 108
        protected abstract bool OnParsePcode(int pCodeOp, CodeLine codeLine);

        // Token: 0x0600006D RID: 109 RVA: 0x000078FC File Offset: 0x00005AFC
        protected void BeginAssignLocalVariable(ushort index)
        {
            this.PushVariable(this.PbFunction.Variables[(int)index]);
        }

        // Token: 0x0600006E RID: 110 RVA: 0x00007911 File Offset: 0x00005B11
        protected void BeginAssignSharedVariable(ushort index)
        {
            this.PushVariable(this.PbFunction.Entry.Variables[(int)index]);
        }

        // Token: 0x0600006F RID: 111 RVA: 0x0000792C File Offset: 0x00005B2C
        protected void BeginAssignGlobalVariable(ushort index)
        {
            this.PushVariable(this.PbFunction.Variables.First((PbVariable o) => o.GlobalIndex == index));
        }

        // Token: 0x06000070 RID: 112 RVA: 0x00007968 File Offset: 0x00005B68
        protected void BeginAssignInstanceVariable()
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject stackObject2 = this._stackObjects.Pop();
            if (stackObject2.Str == "entryobject")
            {
                this._stackObjects.Push(new PCodeParserBase.StackObject(string.Format("{0}", stackObject.Str), stackObject.Type));
                return;
            }
            this._stackObjects.Push(new PCodeParserBase.StackObject(string.Format("{0}.{1}", stackObject2.Str, stackObject.Str), stackObject.Type));
        }

        // Token: 0x06000071 RID: 113 RVA: 0x000079F4 File Offset: 0x00005BF4
        protected void EndAssign(bool isArray = false)
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject stackObject2 = this._stackObjects.Pop();

#if FAKECSHARP
            if (isArray)
            {
                this._codeLine.SCode = string.Format("{0} = {1}", stackObject2.Str, stackObject.Str);
                return;
            }
#else



            if (isArray)
            {
                this._codeLine.SCode = string.Format("{0}[] = {1}", stackObject2.Str, stackObject.Str);
                return;
            }

#endif

            this._codeLine.SCode = string.Format("{0} = {1}", stackObject2.Str, stackObject.Str);
        }

        // Token: 0x06000072 RID: 114 RVA: 0x00007A60 File Offset: 0x00005C60
        protected void EndAssign(string operater)
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject stackObject2 = this._stackObjects.Pop();
            this._codeLine.SCode = string.Format("{0} {1}= {2}", stackObject2.Str, operater, stackObject.Str);
        }

        // Token: 0x06000073 RID: 115 RVA: 0x00007AA8 File Offset: 0x00005CA8
        protected void EndAssign2(string operater)
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            this._codeLine.SCode = string.Format("{0} {1}", stackObject.Str, operater);
        }

        // Token: 0x06000074 RID: 116 RVA: 0x00007AE0 File Offset: 0x00005CE0
        protected void ResetAssign(ushort count)
        {
            PCodeParserBase.StackObject item = this._stackObjects.Pop();
            PCodeParserBase.StackObject item2 = this._stackObjects.Peek();
            this._stackObjects.Push(item2);
            this._stackObjects.Push(item);
        }

        // Token: 0x06000075 RID: 117 RVA: 0x000078FC File Offset: 0x00005AFC
        protected void PushLocalVariable(ushort index)
        {
            this.PushVariable(this.PbFunction.Variables[(int)index]);
        }

        // Token: 0x06000076 RID: 118 RVA: 0x00007911 File Offset: 0x00005B11
        protected void PushSharedVariable(ushort index)
        {
            this.PushVariable(this.PbFunction.Entry.Variables[(int)index]);
        }

        // Token: 0x06000077 RID: 119 RVA: 0x00007B20 File Offset: 0x00005D20
        protected void PushGlobalSharedVariable(ushort index)
        {
            this.PushVariable(this.PbFunction.Entry.Variables.FirstOrDefault((PbVariable o) => o.GlobalIndex == index));
        }

        // Token: 0x06000078 RID: 120 RVA: 0x00007B64 File Offset: 0x00005D64
        protected void PushGlobalVariable(ushort index)
        {
            this.PushVariable(this.PbFunction.Variables.First((PbVariable o) => o.GlobalIndex == index));
        }

        // Token: 0x06000079 RID: 121 RVA: 0x00007BA0 File Offset: 0x00005DA0
        protected void PushInstanceVariable(ushort unkown = 0)
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject stackObject2 = this._stackObjects.Pop();
            if (stackObject2.Str == "entryobject")
            {
                this._stackObjects.Push(new PCodeParserBase.StackObject(string.Format("{0}", stackObject.Str), stackObject.Type));
                return;
            }
            this._stackObjects.Push(new PCodeParserBase.StackObject(string.Format("{0}.{1}", stackObject2.Str, stackObject.Str), stackObject.Type));
        }

        // Token: 0x0600007A RID: 122 RVA: 0x00007C2C File Offset: 0x00005E2C
        protected void PushInstanceVariableName(uint offset)
        {
            if (offset >= 1U && offset <= 7U)
            {
                this._stackObjects.Push(new PCodeParserBase.StackObject("entryobject", this.PbFunction.Entry.EntryObject.Type));
                return;
            }
            uint @uint = BufferHelper.GetUInt(this.PbFunction.Buffer, (long)((ulong)offset));
            PbType type = this._stackObjects.Peek().Type;
            PbVariable pbVariable;
            if (type == null)
            {
                pbVariable = null;
            }
            else
            {
                PbObject @object = type.GetObject(this.PbFunction.Entry);
                pbVariable = ((@object != null) ? @object.AllVariables[(int)BufferHelper.GetUShort(this.PbFunction.Buffer, (long)((ulong)(offset + 4U)))] : null);
            }
            PbVariable pbVariable2 = pbVariable;
            string text;
            if (pbVariable2 == null)
            {
                if ((@uint & 65535U) != 65535U)
                {
                    text = BufferHelper.GetString(this.PbFunction.Project.IsUnicode, this.PbFunction.Buffer, (long)((ulong)@uint));
                }
                else
                {
                    text = string.Format("{0:X4}", BufferHelper.GetUShort(this.PbFunction.Buffer, (long)((ulong)(offset + 4U))));
                }
            }
            else if ((@uint & 65535U) != 65535U)
            {
                text = BufferHelper.GetString(this.PbFunction.Project.IsUnicode, this.PbFunction.Buffer, (long)((ulong)@uint));
                if (!string.Equals(pbVariable2.Name, text, StringComparison.CurrentCultureIgnoreCase))
                {
                    throw new Exception(string.Format("PushInstanceVariableName \"{0}\" != \"{1}\"", pbVariable2.Name, text));
                }
            }
            else
            {
                text = pbVariable2.Name;
            }
            this._stackObjects.Push(new PCodeParserBase.StackObject(text, (pbVariable2 != null) ? pbVariable2.Type : null));
        }

        // Token: 0x0600007B RID: 123 RVA: 0x00007DA2 File Offset: 0x00005FA2
        protected void PushConstant(string constant)
        {
            this._stackObjects.Push(new PCodeParserBase.StackObject(constant, null));
        }

        // Token: 0x0600007C RID: 124 RVA: 0x00007DB6 File Offset: 0x00005FB6
        protected void PushThis()
        {
            this._stackObjects.Push(new PCodeParserBase.StackObject("this", this.PbFunction.Object.Type));
        }

        // Token: 0x0600007D RID: 125 RVA: 0x00007DDD File Offset: 0x00005FDD
        protected void PushParent()
        {
            Stack<PCodeParserBase.StackObject> stackObjects = this._stackObjects;
            string str = "parent";
            PbObject parentObject = this.PbFunction.Object.ParentObject;
            stackObjects.Push(new PCodeParserBase.StackObject(str, (parentObject != null) ? parentObject.Type : null));
        }

        // Token: 0x0600007E RID: 126 RVA: 0x00007E10 File Offset: 0x00006010
        protected void PushEnum(ushort enumIndex, ushort itemIndex)
        {
            this._stackObjects.Push(new PCodeParserBase.StackObject(this.PbFunction.Project.Enums[enumIndex].Items[itemIndex], PbType.GetPbType(this.PbFunction.Entry, enumIndex)));
        }

        // Token: 0x0600007F RID: 127 RVA: 0x00007E60 File Offset: 0x00006060
        protected void OperateStack(string op)
        {
            int operatorLevel = PCodeParserBase.GetOperatorLevel(op);
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            int operatorLevel2 = PCodeParserBase.GetOperatorLevel(stackObject.Opreator);
            if (operatorLevel2 > operatorLevel || operatorLevel2 == operatorLevel)
            {
                stackObject.Str = string.Format("({0})", stackObject.Str);
            }
            PCodeParserBase.StackObject stackObject2 = this._stackObjects.Pop();
            if (PCodeParserBase.GetOperatorLevel(stackObject2.Opreator) > operatorLevel)
            {
                stackObject2.Str = string.Format("({0})", stackObject2.Str);
            }
            string str = string.Concat(new string[]
            {
                stackObject2.Str,
                " ",
                op,
                " ",
                stackObject.Str
            });
            this._stackObjects.Push(new PCodeParserBase.StackObject(str, null)
            {
                Opreator = op
            });
        }

        // Token: 0x06000080 RID: 128 RVA: 0x00007F28 File Offset: 0x00006128
        protected void OperateStackSingle(string op)
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            if (PCodeParserBase.GetOperatorLevel(stackObject.Opreator) > 0)
            {
                stackObject.Str = string.Format("({0})", stackObject.Str);
            }
            string str = op + " " + stackObject.Str;
            this._stackObjects.Push(new PCodeParserBase.StackObject(str, null)
            {
                Opreator = "$" + op
            });
        }

        // Token: 0x06000081 RID: 129 RVA: 0x00007F9C File Offset: 0x0000619C
        protected void Return(ushort p1 = 0)
        {
            string scode = (p1 == 1) ? string.Format("return {0}", this._stackObjects.Pop().Str) : "return";
            this._codeLine.SCode = scode;
        }

        // Token: 0x06000082 RID: 130 RVA: 0x00007FDC File Offset: 0x000061DC
        protected void Halt(ushort force)
        {
            string text = "halt";
            if (force == 0)
            {
                text += " close";
            }
            this._codeLine.SCode = text;
        }

        // Token: 0x06000083 RID: 131 RVA: 0x0000800C File Offset: 0x0000620C
        /// <summary>
        /// Jmp指令预处理
        /// </summary>
        /// <param name="pos"></param>
        /// <param name="jmpType"></param>
        protected void Jump(ushort pos, JmpType jmpType)
        {
            this._codeLine.JmpType = jmpType;
            this._codeLine.JmpPositon = pos;
            if (jmpType == JmpType.Jmp)
            {
                this._codeLine.SCode = string.Format("goto {0:X4}", pos);
                return;
            }
            if (jmpType == JmpType.JmpIfTrue)
            {
                this._codeLine.Condition = this._stackObjects.Pop().Str;
                this._codeLine.SCode = string.Format("if {0} then goto {1:X4}", this._codeLine.Condition, pos);
                return;
            }
            if (jmpType == JmpType.JmpIfFalse)
            {
                this._codeLine.Condition = this._stackObjects.Pop().Str;
                this._codeLine.SCode = string.Format("if {0} then not goto {1:X4}", this._codeLine.Condition, pos);
            }
        }

        // Token: 0x06000084 RID: 132 RVA: 0x000080DC File Offset: 0x000062DC
        protected void Try(ushort catchpos, ushort endpos)
        {
            this._codeLine.SCode = "try ";
        }

        // Token: 0x06000085 RID: 133 RVA: 0x000080EE File Offset: 0x000062EE
        protected void EndTry()
        {
            this._codeLine.SCode = "end try ";
        }

        // Token: 0x06000086 RID: 134 RVA: 0x00008100 File Offset: 0x00006300
        protected void Catch()
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            this._stackObjects.Push(new PCodeParserBase.StackObject(string.Format("catch ({0} {1})", stackObject.Type.Name, stackObject.Str), null));
        }

        // Token: 0x06000087 RID: 135 RVA: 0x00008148 File Offset: 0x00006348
        protected void Throw()
        {
            PCodeParserBase.StackObject arg = this._stackObjects.Pop();
            this._codeLine.SCode = string.Format("throw {0}", arg);
        }

        // Token: 0x06000088 RID: 136 RVA: 0x00008177 File Offset: 0x00006377
        protected void EnterFinally(ushort finallypos)
        {
            this._codeLine.SCode = "enter finally ";
            this._codeLine.JmpPositon = finallypos;
        }

        // Token: 0x06000089 RID: 137 RVA: 0x000020C6 File Offset: 0x000002C6
        protected void LeaveFinally()
        {
        }

        // Token: 0x0600008A RID: 138 RVA: 0x00008198 File Offset: 0x00006398
        protected void CreateObject(uint offset)
        {
            PbType typeName = this.GetTypeName(offset);
            this._stackObjects.Push(new PCodeParserBase.StackObject(string.Format("create {0}", typeName.Name), typeName));
        }

        // Token: 0x0600008B RID: 139 RVA: 0x000081CE File Offset: 0x000063CE
        protected void CreateObjectUsingName(uint index)
        {
            this._stackObjects.Push(new PCodeParserBase.StackObject(string.Format("create using {0}", this._stackObjects.Pop()), PbType.GetPbType(this.PbFunction.Entry, 8)));
        }

        // Token: 0x0600008C RID: 140 RVA: 0x00008208 File Offset: 0x00006408
        protected void DestroyObject()
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            this._codeLine.SCode = string.Format("destroy({0})", stackObject.Str);
        }

        // Token: 0x0600008D RID: 141 RVA: 0x0000823C File Offset: 0x0000643C
        protected void PopFunction()
        {
            this._codeLine.SCode = string.Format("{0}", this._stackObjects.Pop().Str);
        }

        // Token: 0x0600008E RID: 142 RVA: 0x00008264 File Offset: 0x00006464
        protected void PushGlobalFunctionName(ushort objIndex, ushort functionIndex)
        {
            string str = null;
            if ((objIndex & 32768) == 32768)
            {
                str = this.PbFunction.Object.ReferencedFunctions[(int)functionIndex].Name;
            }
            else if ((objIndex & 16384) == 16384)
            {
                PbEntry systemEntry = this.PbFunction.Project.SystemEntry;
                PbFunctionDefinition pbFunctionDefinition;
                if (systemEntry == null)
                {
                    pbFunctionDefinition = null;
                }
                else
                {
                    PbObject pbObject = systemEntry.Objects[objIndex];
                    pbFunctionDefinition = ((pbObject != null) ? pbObject.FunctionDefinitions[(int)functionIndex] : null);
                }
                PbFunctionDefinition pbFunctionDefinition2 = pbFunctionDefinition;
                if (pbFunctionDefinition2 != null)
                {
                    str = pbFunctionDefinition2.Name;
                }
                else
                {
                    str = string.Format("({0:X4}{1:X4})", objIndex, functionIndex);
                }
            }
            this._stackObjects.Push(new PCodeParserBase.StackObject(str, null));
        }

        // Token: 0x0600008F RID: 143 RVA: 0x00008310 File Offset: 0x00006510
        protected void CallGlobalFunction(uint count, uint type)
        {
            string text = this._stackObjects.Pop().Str;
            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)((ulong)count));
            if ((type & 1U) == 1U)
            {
                text = "post " + text;
            }
            if ((type & 2U) == 2U)
            {
                text = "dynamic " + text;
            }
            if ((type & 4U) == 4U)
            {
                text = "event " + text;
            }
#if FAKECSHARP
            Console.WriteLine("CallGlobalFunction=" + text);
            switch (text)
            {
                case "string":
                    text = "ConvertToString";
                    break;
                case "long":
                    text = "ConvertToLong";
                    break;
                default:
                    break;
            }
#else

#endif

            string str = string.Format("{0}({1})", text, string.Join(",", from o in source
                                                                          select o.Str));
          



            this._stackObjects.Push(new PCodeParserBase.StackObject(str, null));
        }

        // Token: 0x06000090 RID: 144 RVA: 0x000083BC File Offset: 0x000065BC
        protected void CallSuper(uint functionIndex, ushort paramcount, ushort objType, uint nameoffset)
        {
            object[] array = new object[(int)paramcount];
            for (int i = 0; i < (int)paramcount; i++)
            {
                array[i] = this._stackObjects.Pop();
            }
            string str = "call super::" + BufferHelper.GetString(this.PbFunction.Project.IsUnicode, this.PbFunction.Buffer, (long)((ulong)nameoffset));
            this._stackObjects.Push(new PCodeParserBase.StackObject(str, null));
        }

        // Token: 0x06000091 RID: 145 RVA: 0x0000842C File Offset: 0x0000662C
        protected void CallFunction(uint offset, uint count, uint type)
        {
            ushort @ushort = BufferHelper.GetUShort(this.PbFunction.Buffer, (long)((ulong)offset));
            PbType pbType = PbType.GetPbType(this.PbFunction.Entry, BufferHelper.GetUShort(this.PbFunction.Buffer, (long)((ulong)(offset + 2U))));
            uint @uint = BufferHelper.GetUInt(this.PbFunction.Buffer, (long)((ulong)(offset + 4U)));
            if ((@uint & 65535U) == 65535U)
            {
                throw new Exception("CallFunction funnameoffset==0xFFFF");
            }
            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)((ulong)count));
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();

            string text = stackObject.Str;



            string text2 = BufferHelper.GetString(this.PbFunction.Project.IsUnicode, this.PbFunction.Buffer, (long)((ulong)@uint));
            PbFunctionDefinition pbFunctionDefinition = null;
            if (@ushort != 65535 && stackObject.Type != null && stackObject.Type.Name != "any")
            {
                PbObject @object = stackObject.Type.GetObject(this.PbFunction.Entry);
                pbFunctionDefinition = ((@object != null) ? @object.AllFunctionDefinitions[(int)@ushort] : null);
                if (pbFunctionDefinition != null)
                {
                    string a;
                    if (pbFunctionDefinition == null)
                    {
                        a = null;
                    }
                    else
                    {
                        string name = pbFunctionDefinition.Name;
                        a = ((name != null) ? name.ToLower() : null);
                    }
                    if (a != ((text2 != null) ? text2.ToLower() : null))
                    {
                        pbFunctionDefinition = null;
                    }
                }
            }



            if ((type & 1U) == 1U)
            {
                text2 = "post " + text2;
            }
            if ((type & 2U) == 2U)
            {
                text2 = "dynamic " + text2;
            }
            if ((type & 4U) == 4U)
            {
                text2 = "event " + text2;
            }
            if (stackObject.Str == "this" && !string.IsNullOrEmpty(pbType.Name))
            {
                text = "super::";
            }
            else
            {
                text += ".";
            }
            string text3 = string.Format("{0}{1}({2})", text, text2, string.Join(",", from o in source
                                                                                      select o.Str));
            Stack<PCodeParserBase.StackObject> stackObjects = this._stackObjects;
            string str = text3;
            PbType type2 = stackObject.Type;
            stackObjects.Push(new PCodeParserBase.StackObject(str, (((type2 != null) ? type2.Name : null) == "any") ? stackObject.Type : ((pbFunctionDefinition != null) ? pbFunctionDefinition.ReturnType : null)));
        }

        // Token: 0x06000092 RID: 146 RVA: 0x00008668 File Offset: 0x00006868
        protected void CallBuiltinFunction(string function, int paramcount = 1)
        {


            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)paramcount);
            string str = string.Format("{0}({1})", function, string.Join(",", from o in source
                                                                              select o.Str));
            this._stackObjects.Push(new PCodeParserBase.StackObject(str, null));
        }

        // Token: 0x06000093 RID: 147 RVA: 0x000086CC File Offset: 0x000068CC
        protected void CreateArray(uint arraylen)
        {
            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)((ulong)arraylen));

#if FAKECSHARP
            string str = string.Format("new [] {{{0}}}", string.Join(",", from o in source
                                                                          select o.Str));
#else
            string str = string.Format("{{{0}}}", string.Join(",", from o in source
                                                                   select o.Str));
#endif
            this._stackObjects.Push(new PCodeParserBase.StackObject(str, null));
        }

        // Token: 0x06000094 RID: 148 RVA: 0x00008730 File Offset: 0x00006930
        protected void Index()
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject stackObject2 = this._stackObjects.Pop();
            string str = string.Format("{0}[{1}]", stackObject2.Str, stackObject.Str);
            this._stackObjects.Push(new PCodeParserBase.StackObject(str, stackObject2.Type));
        }

        // Token: 0x06000095 RID: 149 RVA: 0x00008784 File Offset: 0x00006984
        protected void Index2(ushort p1, ushort p2)
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject stackObject2 = this._stackObjects.Pop();
            string str = string.Format("{0}[{1}]", stackObject2.Str, stackObject.Str);
            this._stackObjects.Push(new PCodeParserBase.StackObject(str, stackObject2.Type));
        }

        // Token: 0x06000096 RID: 150 RVA: 0x000087D8 File Offset: 0x000069D8
        protected void Index3(ushort p1, ushort p2, ushort p3)
        {
            this.PopStack(2L);
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject stackObject2 = this._stackObjects.Pop();
            string str = string.Format("{0}[{1}]", stackObject2.Str, stackObject.Str);
            this._stackObjects.Push(new PCodeParserBase.StackObject(str, stackObject2.Type));
        }

        // Token: 0x06000097 RID: 151 RVA: 0x000020C6 File Offset: 0x000002C6
        protected void Cast(ushort pos = 0)
        {
        }

        // Token: 0x06000098 RID: 152 RVA: 0x00008834 File Offset: 0x00006A34
        protected void SqlOperateTransaction(string function)
        {
            PCodeParserBase.StackObject arg = this._stackObjects.Pop();
            this._codeLine.SCode = string.Format("{0} using {1};", function, arg);
        }

        // Token: 0x06000099 RID: 153 RVA: 0x00008864 File Offset: 0x00006A64
        protected void SqlOpen(ushort paramCount)
        {
            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)((ulong)paramCount));
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject cusor = this._stackObjects.Pop();
            PbVariable pbVariable = this.PbFunction.Variables.FirstOrDefault((PbVariable o) => o.Name == cusor.Str);
            if (pbVariable != null)
            {
                pbVariable.SetCursorParams(from o in source
                                           select o.Str, stackObject.Str);
            }
            this._codeLine.SCode = string.Format("open {0};", cusor);
        }

        // Token: 0x0600009A RID: 154 RVA: 0x0000890C File Offset: 0x00006B0C
        protected void SqlOpenDynamic(uint cursorOffset, ushort paramCount)
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject cusor = this._stackObjects.Pop();
            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)((ulong)paramCount));
            PbVariable pbVariable = this.PbFunction.Variables.FirstOrDefault((PbVariable o) => o.Name == cusor.Str);
            if (pbVariable != null)
            {
                pbVariable.SetDynamicCursorParams(stackObject.Str);
            }
            string text;
            if (paramCount <= 0)
            {
                text = "";
            }
            else
            {
                text = string.Format("using {0}", string.Join(",", from o in source
                                                                   select string.Format(":{0}", o)));
            }
            string arg = text;
            this._codeLine.SCode = string.Format("open dynamic {0} {1};", cusor, arg);
        }

        // Token: 0x0600009B RID: 155 RVA: 0x000089D4 File Offset: 0x00006BD4
        protected void SqlExecute(ushort paramcount)
        {
            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)((ulong)paramcount));
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject procedure = this._stackObjects.Pop();
            PbVariable pbVariable = this.PbFunction.Variables.FirstOrDefault((PbVariable o) => o.Name == procedure.Str);
            if (pbVariable != null)
            {
                pbVariable.SetProcdureParams(from o in source
                                             select o.Str, stackObject.Str);
            }
            this._codeLine.SCode = string.Format("execute {0};", procedure);
        }

        // Token: 0x0600009C RID: 156 RVA: 0x00008A7C File Offset: 0x00006C7C
        protected void SqlExecuteDynamic(uint procedureOffset, ushort paramCount)
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject cusor = this._stackObjects.Pop();
            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)((ulong)paramCount));
            PbVariable pbVariable = this.PbFunction.Variables.FirstOrDefault((PbVariable o) => o.Name == cusor.Str);
            if (pbVariable != null)
            {
                pbVariable.SetDynamictProcdureParams(stackObject.Str);
            }
            string text;
            if (paramCount <= 0)
            {
                text = "";
            }
            else
            {
                text = string.Format("using {0}", string.Join(",", from o in source
                                                                   select string.Format(":{0}", o)));
            }
            string arg = text;
            this._codeLine.SCode = string.Format("execute dynamic {0} {1};", cusor, arg);
        }

        // Token: 0x0600009D RID: 157 RVA: 0x00008B44 File Offset: 0x00006D44
        protected void SqlFetch(ushort paramcount)
        {
            this._stackObjects.Pop();
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)((ulong)paramcount));
            this._codeLine.SCode = string.Format("fetch {0} into {1};", stackObject.Str, string.Join(",", from o in source
                                                                                                          select string.Format(":{0}", o.Str)));
        }

        // Token: 0x0600009E RID: 158 RVA: 0x00008BBC File Offset: 0x00006DBC
        protected void SqlClose()
        {
            this._stackObjects.Pop();
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            this._codeLine.SCode = string.Format("close {0};", stackObject.Str);
        }

        // Token: 0x0600009F RID: 159 RVA: 0x00008BFC File Offset: 0x00006DFC
        protected void SqlPrepareSqlsa()
        {
            PCodeParserBase.StackObject arg = this._stackObjects.Pop();
            string text = this._stackObjects.Pop().Str;
            if (!text.StartsWith("\""))
            {
                text = ":" + text;
            }
            PCodeParserBase.StackObject arg2 = this._stackObjects.Pop();
            this._codeLine.SCode = string.Format("prepare {0} from {1} using {2};", arg2, text, arg);
        }

        // Token: 0x060000A0 RID: 160 RVA: 0x00008C64 File Offset: 0x00006E64
        protected void SqlExecuteSqlsa(ushort paramcount)
        {
            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)((ulong)paramcount));
            PCodeParserBase.StackObject arg = this._stackObjects.Pop();
            this._codeLine.SCode = string.Format("execute {0} using {1};", arg, string.Join(",", from o in source
                                                                                                 select string.Format(":{0}", o)));
        }

        // Token: 0x060000A1 RID: 161 RVA: 0x00008CCC File Offset: 0x00006ECC
        protected void SqlExecuteImmediate()
        {
            PCodeParserBase.StackObject arg = this._stackObjects.Pop();
            string text = this._stackObjects.Pop().Str;
            if (!text.StartsWith("\""))
            {
                text = ":" + text;
            }
            this._codeLine.SCode = string.Format("execute immediate {0} using {1};", text, arg);
        }

        // Token: 0x060000A2 RID: 162 RVA: 0x00008D28 File Offset: 0x00006F28
        protected void SqlDescribe()
        {
            PCodeParserBase.StackObject arg = this._stackObjects.Pop();
            PCodeParserBase.StackObject arg2 = this._stackObjects.Pop();
            this._codeLine.SCode = string.Format("describe {0} into {1};", arg2, arg);
        }

        // Token: 0x060000A3 RID: 163 RVA: 0x00008D64 File Offset: 0x00006F64
        protected void SqlOpenDynamicDescriptor(uint cursorOffset)
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject cusor = this._stackObjects.Pop();
            PCodeParserBase.StackObject arg = this._stackObjects.Pop();
            PbVariable pbVariable = this.PbFunction.Variables.FirstOrDefault((PbVariable o) => o.Name == cusor.Str);
            if (pbVariable != null)
            {
                pbVariable.SetDynamicCursorParams(stackObject.Str);
            }
            this._codeLine.SCode = string.Format("open dynamic {0} using descriptor {1};", cusor, arg);
        }

        // Token: 0x060000A4 RID: 164 RVA: 0x00008DEC File Offset: 0x00006FEC
        protected void SqlExecuteDynamicDescriptor(uint procedureOffset)
        {
            PCodeParserBase.StackObject stackObject = this._stackObjects.Pop();
            PCodeParserBase.StackObject cusor = this._stackObjects.Pop();
            PCodeParserBase.StackObject arg = this._stackObjects.Pop();
            PbVariable pbVariable = this.PbFunction.Variables.FirstOrDefault((PbVariable o) => o.Name == cusor.Str);
            if (pbVariable != null)
            {
                pbVariable.SetDynamicCursorParams(stackObject.Str);
            }
            this._codeLine.SCode = string.Format("execute dynamic {0} using descriptor {1};", cusor, arg);
        }

        // Token: 0x060000A5 RID: 165 RVA: 0x00008E74 File Offset: 0x00007074
        protected void SqlFetchDynamicDescriptor()
        {
            this._stackObjects.Pop();
            PCodeParserBase.StackObject arg = this._stackObjects.Pop();
            PCodeParserBase.StackObject arg2 = this._stackObjects.Pop();
            this._codeLine.SCode = string.Format("fetch {0} using descriptor {1};", arg, arg2);
        }

        // Token: 0x060000A6 RID: 166 RVA: 0x00008EBC File Offset: 0x000070BC
        protected void SqlDirectInsertUpdateDelete(uint cursorOffset, ushort paramcount)
        {
            PCodeParserBase.StackObject arg = this._stackObjects.Pop();
            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)((ulong)paramcount));
            string cursor = BufferHelper.GetCursor(this.PbFunction.Project.IsUnicode, this.PbFunction.Entry.VariableBuffer, cursorOffset, from o in source
                                                                                                                                          select o.Str);

#if FAKECSHARP
            var tmp = string.Join(",", from o in source
                                       select string.Format("{{\"{0}\",{0} }}", o));
            tmp = string.Format("new Dictionary<string, dynamic> {{ {0} }}", tmp);
            Console.WriteLine(tmp);
            this._codeLine.SCode = string.Format(" RunSQL(@\"{0}\" ,{1},out {2});", cursor.Replace("\"", ""), tmp, arg);
            Console.WriteLine(this._codeLine.SCode);
#else
		this._codeLine.SCode = string.Format("{0} using {1};", cursor, arg);
#endif
        }

        // Token: 0x060000A7 RID: 167 RVA: 0x00008F44 File Offset: 0x00007144
        protected void SqlDirectSelect(uint cursorOffset, ushort paramcount1, ushort paramcount2)
        {
            PCodeParserBase.StackObject arg = this._stackObjects.Pop();
            IEnumerable<PCodeParserBase.StackObject> source = this.PopStack((long)((ulong)paramcount1));
            IEnumerable<PCodeParserBase.StackObject> source2 = this.PopStack((long)((ulong)paramcount2));
            string text = BufferHelper.GetCursor(this.PbFunction.Project.IsUnicode, this.PbFunction.Entry.VariableBuffer, cursorOffset, from o in source
                                                                                                                                        select o.Str);
            Console.WriteLine(text);
            text = new Regex(" from ", RegexOptions.IgnoreCase).Replace(text, string.Format(" into {0} from ", string.Join(",", from o in source2
                                                                                                                                select string.Format(":{0}", o))), 1);


#if FAKECSHARP
            var tmp = string.Join(",", from o in source
                                       select string.Format("{{\"{0}\",{0} }}", o));
            tmp = string.Format("new Dictionary<string, dynamic> {{ {0} }}", tmp);
            Console.WriteLine(tmp);

            this._codeLine.SCode = string.Format("var obj = RunSQL(@\"{0}\" ,{1},out {2});", text.Replace("\"", ""), tmp, arg);
            Console.WriteLine(this._codeLine.SCode);
#else
			this._codeLine.SCode = string.Format("{0} using {1};", text, arg);
			Console.WriteLine(this._codeLine.SCode);
#endif
        }

        // Token: 0x060000A8 RID: 168 RVA: 0x00009020 File Offset: 0x00007220
        private PbType GetTypeName(uint offset)
        {
            uint @uint = BufferHelper.GetUInt(this.PbFunction.Buffer, (long)((ulong)offset));
            ushort @ushort = BufferHelper.GetUShort(this.PbFunction.Buffer, (long)((ulong)(offset + 4U)));
            ushort ushort2 = BufferHelper.GetUShort(this.PbFunction.Buffer, (long)((ulong)(offset + 6U)));
            if (ushort2 != 65535)
            {
            }
            PbType pbType = PbType.GetPbType(this.PbFunction.Entry, @ushort);
            string @string = BufferHelper.GetString(this.PbFunction.Project.IsUnicode, this.PbFunction.Buffer, (long)((ulong)@uint));
            if (pbType.Name != @string)
            {
                throw new Exception(string.Format("GetTypeName \"{0}\" != \"{1}\"", pbType.Name, @string));
            }
            return pbType;
        }

        // Token: 0x060000A9 RID: 169 RVA: 0x000090D4 File Offset: 0x000072D4
        private static int GetOperatorLevel(string @operator)
        {
            uint num = PrivateImplementationDetails.ComputeStringHash(@operator);
            if (num <= 789356349U)
            {
                if (num > 616290874U)
                {
                    if (num <= 705468254U)
                    {
                        if (num != 671913016U)
                        {
                            if (num != 705468254U)
                            {
                                return 0;
                            }
                            if (!(@operator == "/"))
                            {
                                return 0;
                            }
                            return 4;
                        }
                        else if (!(@operator == "-"))
                        {
                            return 0;
                        }
                    }
                    else if (num != 772578730U)
                    {
                        if (num != 789356349U)
                        {
                            return 0;
                        }
                        if (!(@operator == "*"))
                        {
                            return 0;
                        }
                        return 4;
                    }
                    else if (!(@operator == "+"))
                    {
                        return 0;
                    }
                    return 5;
                }
                if (num != 254395046U)
                {
                    if (num != 284975636U)
                    {
                        if (num != 616290874U)
                        {
                            return 0;
                        }
                        if (!(@operator == "$-"))
                        {
                            return 0;
                        }
                        return 6;
                    }
                    else
                    {
                        if (!(@operator == ">="))
                        {
                            return 0;
                        }
                        return 1;
                    }
                }
                else if (!(@operator == "and"))
                {
                    return 0;
                }
            }
            else if (num <= 1563699588U)
            {
                if (num <= 957132539U)
                {
                    if (num != 940354920U)
                    {
                        if (num != 957132539U)
                        {
                            return 0;
                        }
                        if (!(@operator == "<"))
                        {
                            return 0;
                        }
                        return 1;
                    }
                    else
                    {
                        if (!(@operator == "="))
                        {
                            return 0;
                        }
                        return 1;
                    }
                }
                else if (num != 990687777U)
                {
                    if (num != 1563699588U)
                    {
                        return 0;
                    }
                    if (!(@operator == "or"))
                    {
                        return 0;
                    }
                }
                else
                {
                    if (!(@operator == ">"))
                    {
                        return 0;
                    }
                    return 1;
                }
            }
            else if (num <= 2499223986U)
            {
                if (num != 2482446367U)
                {
                    if (num != 2499223986U)
                    {
                        return 0;
                    }
                    if (!(@operator == "<="))
                    {
                        return 0;
                    }
                    return 1;
                }
                else
                {
                    if (!(@operator == "<>"))
                    {
                        return 0;
                    }
                    return 1;
                }
            }
            else if (num != 2606455940U)
            {
                if (num != 3675003649U)
                {
                    return 0;
                }
                if (!(@operator == "^"))
                {
                    return 0;
                }
                return 3;
            }
            else
            {
                if (!(@operator == "$not"))
                {
                    return 0;
                }
                return 6;
            }
            return 2;
        }

        // Token: 0x060000AA RID: 170 RVA: 0x000092F5 File Offset: 0x000074F5
        private void PushVariable(PbVariable variable)
        {
            this._stackObjects.Push(new PCodeParserBase.StackObject(variable.Name, variable.Type));
        }

        // Token: 0x060000AB RID: 171 RVA: 0x00009314 File Offset: 0x00007514
        private void Check()
        {
            byte[] pcodeLenArray = new PCodeParser105(this.PbFunction).PCodeLenArray;
            byte[] pcodeLenArray2 = new PCodeParser110(this.PbFunction).PCodeLenArray;
            int num = Math.Min(pcodeLenArray.Length, pcodeLenArray2.Length);
            int num2 = 0;
            while (num2 < num && pcodeLenArray[num2] == pcodeLenArray2[num2])
            {
                num2++;
            }
            int num3 = 0;
            while (num3 < num && pcodeLenArray[pcodeLenArray.Length - 1 - num3] == pcodeLenArray2[pcodeLenArray2.Length - 1 - num3])
            {
                num3++;
            }
        }

        // Token: 0x060000AC RID: 172 RVA: 0x0000938C File Offset: 0x0000758C
        public string GetArray(string filename)
        {
            byte[] array = new byte[4096];
            List<byte> list = new List<byte>();
            FileStream fileStream = File.Open(filename, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
            int num = 0;
            bool flag = false;
            int i = fileStream.Read(array, num, 4096);
            byte[] array2 = new byte[]
            {
                193,
                224,
                2,
                139,
                byte.MaxValue,
                byte.MaxValue,
                byte.MaxValue,
                byte.MaxValue,
                byte.MaxValue,
                141,
                84,
                byte.MaxValue,
                2
            };
            while (i >= array2.Length)
            {
                for (int j = 0; j < i - array2.Length; j++)
                {
                    bool flag2 = true;
                    for (int k = 0; k < array2.Length; k++)
                    {
                        if (array2[k] != 255 && array[j + k] != array2[k])
                        {
                            flag2 = false;
                            break;
                        }
                    }
                    if (flag2)
                    {
                        flag = true;
                        num += j + 5;
                        break;
                    }
                }
                if (flag)
                {
                    break;
                }
                int num2 = 1 - array2.Length;
                num += i + num2;
                fileStream.Seek((long)num2, SeekOrigin.Current);
                i = fileStream.Read(array, 0, 4096);
            }
            if (!flag)
            {
                return "";
            }
            fileStream.Seek((long)num, SeekOrigin.Begin);
            fileStream.Read(array, 0, 4);
            uint num3 = BufferHelper.GetUInt(array, 0L);
            num3 = new PEHelper(fileStream).GetOffset(num3) - 4U;
            fileStream.Seek((long)((ulong)num3), SeekOrigin.Begin);
            for (; ; )
            {
                fileStream.Read(array, 0, 12);
                if (BufferHelper.GetUInt(array, 4L) > 255U)
                {
                    break;
                }
                list.Add(array[4]);
            }
            fileStream.Close();
            string text = string.Empty;
            int num4 = list.Count / 16;
            for (int l = 0; l < num4; l++)
            {
                for (int m = 0; m < 16; m++)
                {
                    text = text + list[l * 16 + m] + ",";
                }
                if (l % 8 == 0)
                {
                    text += string.Format("\t\t//0x{0:X2}", l);
                }
                text += "\r\n";
            }
            for (int n = 0; n < list.Count - num4 * 16; n++)
            {
                text = text + list[num4 * 16 + n] + ",";
            }
            return text;
        }

        // Token: 0x060000AD RID: 173 RVA: 0x000095A8 File Offset: 0x000077A8
        private IEnumerable<PCodeParserBase.StackObject> PopStack(long count)
        {
            PCodeParserBase.StackObject[] array = new PCodeParserBase.StackObject[count];
            int num = 0;
            while ((long)num < count)
            {
                array[(int)(checked((IntPtr)(unchecked(count - 1L - (long)num))))] = this._stackObjects.Pop();
                num++;
            }
            return array;
        }

        // Token: 0x04000030 RID: 48
        private readonly Stack<PCodeParserBase.StackObject> _stackObjects = new Stack<PCodeParserBase.StackObject>();

        // Token: 0x04000031 RID: 49
        private CodeLine _codeLine;

        // Token: 0x04000032 RID: 50
        protected readonly PbFunction PbFunction;

        // Token: 0x02000038 RID: 56
        private class StackObject
        {
            // Token: 0x17000079 RID: 121
            // (get) Token: 0x060001D8 RID: 472 RVA: 0x000108EE File Offset: 0x0000EAEE
            // (set) Token: 0x060001D9 RID: 473 RVA: 0x000108F6 File Offset: 0x0000EAF6
            public PbType Type { get; set; }

            // Token: 0x1700007A RID: 122
            // (get) Token: 0x060001DA RID: 474 RVA: 0x000108FF File Offset: 0x0000EAFF
            // (set) Token: 0x060001DB RID: 475 RVA: 0x00010907 File Offset: 0x0000EB07
            public string Str { get; set; }

            // Token: 0x1700007B RID: 123
            // (get) Token: 0x060001DC RID: 476 RVA: 0x00010910 File Offset: 0x0000EB10
            // (set) Token: 0x060001DD RID: 477 RVA: 0x00010918 File Offset: 0x0000EB18
            public string Opreator { get; set; }

            // Token: 0x060001DE RID: 478 RVA: 0x00010921 File Offset: 0x0000EB21
            public StackObject(string str, PbType type = null)
            {
                this.Type = type;
                this.Str = str;
            }

            // Token: 0x060001DF RID: 479 RVA: 0x00010937 File Offset: 0x0000EB37
            public override string ToString()
            {
                return this.Str;
            }
        }
    }
}

#define FAKE
using System;
using System.Collections.Generic;
using System.Linq;
using HISWebInterface;

namespace PbdViewer.Uitils
{
    // Token: 0x02000008 RID: 8
    public class CodeLine
    {
        // Token: 0x06000018 RID: 24 RVA: 0x000024E8 File Offset: 0x000006E8
        public override string ToString()
        {
            if (this.LabelSCode.Count > 1)
            {
                this.LabelSCode.Insert(0, "/*START*/");
                this.LabelSCode.Add("/*END*/");
            }
            string str = string.Join("", from o in this.LabelSCode
                                         select string.Format("{0} {1}\r\n", "".PadRight(47), o));
            string sharpstr = string.Join("", from o in this.LabelCSharpCode
                                              select string.Format("{0} {1}\r\n", "".PadRight(47), o));

            this.CSharpCode += sharpstr.Trim();


            string text = string.Format("{0:X4}", this.DebugLine);

            text = string.Format("{0} {1:X4}:  ", text.PadRight(47), this.PCodePositon) + string.Format("{0:X4}  {1}", this.PCodeOp, BufferHelper.GetHexString(this.PCodeParam));


            text = "";
#if FAKE
            if (!string.IsNullOrEmpty(this.CSharpCode))
            {
                this.SCode = this.CSharpCode + "///" + this.SCode;
            }

#endif

            text = string.Format("{0} {1}", text.PadRight(47), this.SCode);


            //长度48开始，其他代码会按这个位置读取
            string ret = "";




            if (PCodeHelper.JumpPCodes.ContainsKey(this.PCodePositon))
            {
                ret = str + text + string.Format(" /*{0:X4}*/  ", this.PCodePositon);
            }
            else
            {
                ret = str + text;
            }

            if (this.SCode != null && ret.Contains("do{"))
            {
                Console.WriteLine("Debug");
            }
#if FAKE

            ret = ReplaceKeyWord(ret);
            //if (!string.IsNullOrEmpty(this.CSharpCode))
            //{
            //    ret = string.Format("{0} {1}", string.Empty.PadRight(47), this.CSharpCode) + "//" + ret.Substring(48);
            //}



#endif
            return ret;


        }

        private string ReplaceKeyWord(string ret)
        {
            string text3 = ret.Substring(48);
            if (!string.IsNullOrEmpty(text3))
            {
                var words = text3.Split(' ', '.', '(',')');



                ret = ret.Replace("end if", "}");

                

                ret = ret.Replace("case else", "default:{ /*case else*/");

                if (words.Contains("if") || words.Contains("while"))
                {
                    ret = ret.Replace("if", "if(");
                    ret = ret.Replace("=", "==");
                    ret = ret.Replace(">==", ">=");
                    ret = ret.Replace("<==", "<=");
                    ret = ret.Replace("==<", "=<");
                    if (words.Contains("and"))
                        ret = ret.Replace("and", "&& /*and*/");

                    if (words.Contains("or"))
                        ret = ret.Replace("or", "||/*or*/");
                    if (words.Contains("not"))
                        ret = ret.Replace("not", "!/*not*/");
                    ret = ret.Replace("<>", "!=");
                }
                if (words.Contains("then"))
                    ret = ret.Replace("then", "){");
                if (words.Contains("else"))
                    ret = ret.Replace("else", "}else{");

                //if (words.Contains("integer"))
                //    ret = ret.Replace("integer", "int");
                //if (words.Contains("date"))
                //    ret = ret.Replace("date", "DateOnly");
                //if (words.Contains("time"))
                //    ret = ret.Replace("time", "timeOnly");
                //if (words.Contains("datetime"))
                //    ret = ret.Replace("datetime", "DateTime");
                //if (words.Contains("boolean"))
                //    ret = ret.Replace("boolean", "bool");

                if (words.Contains("object"))
                    ret = ret.Replace(".object.", ".");
                if (words.Contains("break"))
                    ret = ret.Replace("break", "break;");
                if (words.Contains("create"))
                {
                    ret = ret.Replace("create", "new");
                    ret += "();";
                }

                //ret = ret.Replace("case }else{", "case else");
                //ret = ret.Replace(",string(", " ,/*string*/ConvertToString(");
                //ret = ret.Replace(" string(", "  /*string*/ConvertToString(");
                //ret = ret.Replace(",long(", ",/*long*/ConvertToLong(");
                //ret = ret.Replace(" long(", " /*long*/ConvertToLong(");
                ret = ret.Replace("end choose", " }/*end choose*/");

                ret = ret.Replace("end case", " break;}/*end case*/");
                if (ret.Contains("call super::"))
                {
                    ret = ret.Replace("call super::", " base./*call super::*/");
                    ret += "()";
                }
                


                int count1 = ret.Count(f => f == '}');
                int count2 = ret.Count(f => f == '{');
                if (count1 == count2 && count1 != 0)
                {
                    Console.WriteLine(ret);
                }
                if ((count1 == count2 && count1 != 0) && ret.IndexOf("}") != ret.Length - 1 && ret.IndexOf(";")==-1)  //或者最后一个字符不是}
                {
                    ret = AddToken();
                }

                if (text3.Trim().IndexOf("/*") == 0 || ret.IndexOf(";") > 0
                || count1>=1 || count2>=1  //同一个代码行里面 {}字符数量相同

            )
                {
                    //不用加上分号
                }
                else
                {
                    ret = AddToken();
                }
            }

            return ret;

            string AddToken()
            {
                var index = ret.IndexOf("///");
                if (index == -1)
                {
                    ret = ret + ";";
                }
                else
                {
                    ret = ret.Substring(0, index) + ";" + ret.Substring(index).Trim();
                }

                return ret;
            }
        }

        // Token: 0x0400000F RID: 15
        public ushort PCodePositon;

        // Token: 0x04000010 RID: 16
        public ushort? DebugLine;

        // Token: 0x04000011 RID: 17
        public ushort PCodeOp;

        // Token: 0x04000012 RID: 18
        public byte[] PCodeParam;

        private string _scode;
        // Token: 0x04000013 RID: 19
        public string SCode
        {
            get => _scode;
            set  {
                //if(_scode!=null && _scode.Contains("isvalid(::message)"))
                //    Log.Info(_scode + "->" + value);
                _scode = value;
            }
           
        }

        // Token: 0x04000014 RID: 20
        public ushort JmpPositon;

        // Token: 0x04000015 RID: 21
        public JmpType JmpType;

        // Token: 0x04000016 RID: 22
        public string Condition;

        // Token: 0x04000017 RID: 23
        public CodeLine PreCodeLine;

        // Token: 0x04000018 RID: 24
        public CodeLine NextCodeLine;

        // Token: 0x04000019 RID: 25
        public readonly List<string> LabelSCode = new List<string>();
        public readonly List<string> LabelCSharpCode = new List<string>();

        //反向跳转
        public ushort ReverseJmpPositon;

        public string CSharpCode = string.Empty;
    }
}

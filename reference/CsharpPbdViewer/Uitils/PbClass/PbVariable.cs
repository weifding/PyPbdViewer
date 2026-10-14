#define FAKESHARP
using System;
using System.Collections.Generic;
using System.Linq;

namespace PbdViewer.Uitils.PbClass
{
    // Token: 0x02000018 RID: 24
    public class PbVariable
    {
        // Token: 0x17000043 RID: 67
        // (get) Token: 0x0600012A RID: 298 RVA: 0x0000BCD6 File Offset: 0x00009ED6
        // (set) Token: 0x0600012B RID: 299 RVA: 0x0000BCDE File Offset: 0x00009EDE
        public ushort Index { get; set; }

        // Token: 0x17000044 RID: 68
        // (get) Token: 0x0600012C RID: 300 RVA: 0x0000BCE7 File Offset: 0x00009EE7
        public ushort GlobalIndex
        {
            get
            {
                if (!this.IsShared)
                {
                    return ushort.MaxValue;
                }
                return BufferHelper.GetUShort(this.Buffer, 12L);
            }
        }

        // Token: 0x17000045 RID: 69
        // (get) Token: 0x0600012D RID: 301 RVA: 0x0000BD05 File Offset: 0x00009F05
        // (set) Token: 0x0600012E RID: 302 RVA: 0x0000BD0D File Offset: 0x00009F0D
        public PbType Type { get; set; }

        // Token: 0x17000046 RID: 70
        // (get) Token: 0x0600012F RID: 303 RVA: 0x0000BD16 File Offset: 0x00009F16
        // (set) Token: 0x06000130 RID: 304 RVA: 0x0000BD1E File Offset: 0x00009F1E
        public PbVariableFlag Flag { get; set; }

        // Token: 0x17000047 RID: 71
        // (get) Token: 0x06000131 RID: 305 RVA: 0x0000BD27 File Offset: 0x00009F27
        // (set) Token: 0x06000132 RID: 306 RVA: 0x0000BD2F File Offset: 0x00009F2F
        public string PrecisionOrSize { get; set; }

        // Token: 0x17000048 RID: 72
        // (get) Token: 0x06000133 RID: 307 RVA: 0x0000BD38 File Offset: 0x00009F38
        // (set) Token: 0x06000134 RID: 308 RVA: 0x0000BD40 File Offset: 0x00009F40
        public string Name { get; set; }

        // Token: 0x17000049 RID: 73
        // (get) Token: 0x06000135 RID: 309 RVA: 0x0000BD49 File Offset: 0x00009F49
        // (set) Token: 0x06000136 RID: 310 RVA: 0x0000BD51 File Offset: 0x00009F51
        public string ArrayString { get; set; }

        // Token: 0x1700004A RID: 74
        // (get) Token: 0x06000137 RID: 311 RVA: 0x0000BD5A File Offset: 0x00009F5A
        // (set) Token: 0x06000138 RID: 312 RVA: 0x0000BD62 File Offset: 0x00009F62
        public string AccessString { get; set; }

        // Token: 0x1700004B RID: 75
        // (get) Token: 0x06000139 RID: 313 RVA: 0x0000BD6B File Offset: 0x00009F6B
        // (set) Token: 0x0600013A RID: 314 RVA: 0x0000BD73 File Offset: 0x00009F73
        public bool IsReferencedGlobal { get; set; }

        // Token: 0x1700004C RID: 76
        // (get) Token: 0x0600013B RID: 315 RVA: 0x0000BD7C File Offset: 0x00009F7C
        // (set) Token: 0x0600013C RID: 316 RVA: 0x0000BD84 File Offset: 0x00009F84
        public bool IsShared { get; set; }

        // Token: 0x1700004D RID: 77
        // (get) Token: 0x0600013D RID: 317 RVA: 0x0000BD8D File Offset: 0x00009F8D
        // (set) Token: 0x0600013E RID: 318 RVA: 0x0000BD95 File Offset: 0x00009F95
        public bool IsInstance { get; set; }

        // Token: 0x1700004E RID: 78
        // (get) Token: 0x0600013F RID: 319 RVA: 0x0000BD9E File Offset: 0x00009F9E
        // (set) Token: 0x06000140 RID: 320 RVA: 0x0000BDA6 File Offset: 0x00009FA6
        public bool IsIndirect { get; set; }

        // Token: 0x1700004F RID: 79
        // (get) Token: 0x06000141 RID: 321 RVA: 0x0000BDAF File Offset: 0x00009FAF
        // (set) Token: 0x06000142 RID: 322 RVA: 0x0000BDB7 File Offset: 0x00009FB7
        public bool IsConstant { get; set; }

        // Token: 0x17000050 RID: 80
        // (get) Token: 0x06000143 RID: 323 RVA: 0x0000BDC0 File Offset: 0x00009FC0
        // (set) Token: 0x06000144 RID: 324 RVA: 0x0000BDC8 File Offset: 0x00009FC8
        public PbEntry Entry { get; set; }

        // Token: 0x17000051 RID: 81
        // (get) Token: 0x06000145 RID: 325 RVA: 0x0000BDD1 File Offset: 0x00009FD1
        // (set) Token: 0x06000146 RID: 326 RVA: 0x0000BDD9 File Offset: 0x00009FD9
        public PbObject Object { get; set; }

        // Token: 0x17000052 RID: 82
        // (get) Token: 0x06000147 RID: 327 RVA: 0x0000BDE2 File Offset: 0x00009FE2
        public byte[] Buffer { get; }

        // Token: 0x06000148 RID: 328 RVA: 0x0000BDEC File Offset: 0x00009FEC
        public PbVariable(PbEntry pbEntry, ushort index, byte[] buffer, byte[] structBuffer, bool delayParseType)
        {
            this.Entry = pbEntry;
            this.Buffer = buffer;
            this.Index = index;
            this.Flag = (PbVariableFlag)this.Buffer[17];
            this.AccessString = (this.Flag.HasFlag(PbVariableFlag.IsPrivate) ? "private " : (this.Flag.HasFlag(PbVariableFlag.IsProtected) ? "protected " : ""));
            this.IsShared = this.Flag.HasFlag(PbVariableFlag.IsShared);
            this.IsReferencedGlobal = ((buffer[16] & 64) == 64);
            this.IsInstance = ((buffer[0] & 15) <= 1);
            this.IsIndirect = ((buffer[0] & 2) == 2);
            this.IsConstant = ((buffer[0] & 4) == 4);
            if (!delayParseType)
            {
                this.ParseType();
            }
            this.Name = BufferHelper.GetString(pbEntry.Project.IsUnicode, structBuffer, (long)BufferHelper.GetUInt(buffer, 8L));
            this.ArrayString = PbVariable.GetArrayString(BufferHelper.GetUInt(buffer, 4L), structBuffer);
        }

        // Token: 0x06000149 RID: 329 RVA: 0x0000BF0C File Offset: 0x0000A10C
        public PbVariable Inherit(PbObject control)
        {
            PbVariable pbVariable = (PbVariable)base.MemberwiseClone();
            pbVariable.Type = control.Type;
            pbVariable.Entry = control.Entry;
            pbVariable.Object = control;
            return pbVariable;
        }

        // Token: 0x0600014A RID: 330 RVA: 0x0000BF38 File Offset: 0x0000A138
        public void ParseType()
        {
            this.Type = PbType.GetPbType(this.Entry, BufferHelper.GetUShort(this.Buffer, 18L));
            if (this.Type.IsValueType)
            {
                if (this.Type.Name == "blob")
                {
                    ushort @ushort = BufferHelper.GetUShort(this.Buffer, 12L);
                    this.PrecisionOrSize = ((@ushort == 0) ? "" : string.Format("{{{0}}}", BufferHelper.GetUShort(this.Buffer, 12L)));
                    return;
                }
                if (this.Type.Name == "decimal")
                {
                    int num = (int)(this.Buffer[16] & 63);
                    this.PrecisionOrSize = ((num == 62) ? "" : string.Format("{{{0}}}", (int)(this.Buffer[16] / 2)));
                }
            }
        }

        // Token: 0x0600014B RID: 331 RVA: 0x0000C018 File Offset: 0x0000A218
        public static string GetArrayString(uint offset, byte[] buffer)
        {
            string text = string.Empty;
            if (offset != 65535U)
            {
                text += "[";
                byte b = buffer[(int)offset];
                for (int i = 0; i < (int)b; i++)
                {
                    if (i != 0)
                    {
                        text += ",";
                    }
                    uint @uint = BufferHelper.GetUInt(buffer, (long)((ulong)(offset + 4U) + (ulong)((long)(i * 8))));
                    uint uint2 = BufferHelper.GetUInt(buffer, (long)((ulong)(offset + 8U) + (ulong)((long)(i * 8))));
                    if (@uint == 1U)
                    {
                        text += uint2;
                    }
                    else if (@uint != uint2 || uint2 != 0U)
                    {
                        text = string.Concat(new object[]
                        {
                            text,
                            @uint,
                            " to ",
                            uint2
                        });
                    }
                }
                text += "]";
            }
            return text;
        }

        // Token: 0x0600014C RID: 332 RVA: 0x0000C0D8 File Offset: 0x0000A2D8
        public string GetValue(byte[] valueBuffer)
        {
            if (!this.Flag.HasFlag(PbVariableFlag.IsCustom))
            {
                return null;
            }
            if (!this.Type.IsValueType && this.Type.Enum == null)
            {
                return null;
            }
            if (this.IsIndirect || this.IsReferencedGlobal)
            {
                return null;
            }
            if (!this.Flag.HasFlag(PbVariableFlag.IsArray))
            {
                return this.GetValue(BufferHelper.GetUInt(this.Buffer, 12L), valueBuffer, true);
            }
            if (this.Flag.HasFlag(PbVariableFlag.Invalid))
            {
                return null;
            }
            List<uint> list = this.GetList(valueBuffer);
            List<string> list2 = (from o in list
                                  select this.GetValue(o, valueBuffer, true)).ToList<string>();
            while (list2.Count > 0 && list2.Last<string>() == null)
            {
                list2.RemoveAt(list2.Count - 1);
            }
            for (int i = 0; i < list2.Count; i++)
            {
                if (list2[i] == null)
                {
                    list2[i] = this.GetValue(list[i], valueBuffer, false);
                }
            }
#if FAKESHARP
            return string.Format("new [] {{{0}}}", string.Join(",", list2));
#else
			return string.Format("{{{0}}}", string.Join(",", list2));
#endif
        }

        // Token: 0x0600014D RID: 333 RVA: 0x0000C224 File Offset: 0x0000A424
        private string GetValue(uint code, byte[] valueBuffer, bool checkisdefault)
        {
            if (this.Type.Enum == null)
            {
                string name = this.Type.Name;
                uint num = PrivateImplementationDetails.ComputeStringHash(name);
                if (num <= 2699759368U)
                {
                    if (num <= 1564253156U)
                    {
                        if (num != 398550328U)
                        {
                            if (num != 520654156U)
                            {
                                if (num == 1564253156U)
                                {
                                    if (name == "time")
                                    {
                                        if (!checkisdefault || (!this.Flag.HasFlag(PbVariableFlag.Invalid) && !(BufferHelper.GetTime(valueBuffer, (long)((ulong)code)) == "00:00:00")))
                                        {
                                            return string.Format("{0}", BufferHelper.GetTime(valueBuffer, (long)((ulong)code)));
                                        }
                                        return null;
                                    }
                                }
                            }
                            else if (name == "decimal")
                            {
                                if (!checkisdefault || (!this.Flag.HasFlag(PbVariableFlag.Invalid) && !(BufferHelper.GetDecimal(valueBuffer, (long)((ulong)code)) == "0.0")))
                                {
                                    return string.Format("{0}", BufferHelper.GetDecimal(valueBuffer, (long)((ulong)code)));
                                }
                                return null;
                            }
                        }
                        else if (name == "string")
                        {
                            if (!checkisdefault || (!this.Flag.HasFlag(PbVariableFlag.Invalid) && !(BufferHelper.GetString(this.Entry.Project.IsUnicode, valueBuffer, (long)((ulong)code)) == "")))
                            {
                                return string.Format("{0}", BufferHelper.GetEscapeString(this.Entry.Project.IsUnicode, valueBuffer, (long)((ulong)code)));
                            }
                            return null;
                        }
                    }
                    else if (num <= 1710517951U)
                    {
                        if (num != 1683620383U)
                        {
                            if (num == 1710517951U)
                            {
                                if (name == "boolean")
                                {
                                    if (!checkisdefault || (byte)code != 0)
                                    {
                                        return string.Format("{0}", (byte)code > 0).ToLower();
                                    }
                                    return null;
                                }
                            }
                        }
                        else if (name == "byte")
                        {
                            if (!checkisdefault || (ushort)code != 0)
                            {
                                return string.Format("{0}", (byte)code);
                            }
                            return null;
                        }
                    }
                    else if (num != 2667225454U)
                    {
                        if (num == 2699759368U)
                        {
                            if (name == "double")
                            {
                                if (!checkisdefault || (!this.Flag.HasFlag(PbVariableFlag.Invalid) && !(BufferHelper.GetDouble(valueBuffer, (long)((ulong)code)) == "0")))
                                {
                                    return BufferHelper.GetDouble(valueBuffer, (long)((ulong)code));
                                }
                                return null;
                            }
                        }
                    }
                    else if (name == "ulong")
                    {
                        if (!checkisdefault || code != 0U)
                        {
                            return string.Format("{0}", code);
                        }
                        return null;
                    }
                }
                else if (num <= 3415750305U)
                {
                    if (num <= 3218261061U)
                    {
                        if (num != 2823553821U)
                        {
                            if (num == 3218261061U)
                            {
                                if (name == "integer")
                                {
                                    if (!checkisdefault || (short)code != 0)
                                    {
                                        return string.Format("{0}", (short)code);
                                    }
                                    return null;
                                }
                            }
                        }
                        else if (name == "char")
                        {
                            if (!checkisdefault || (ushort)code != 0)
                            {
                                return string.Format("'{0}'", (char)code);
                            }
                            return null;
                        }
                    }
                    else if (num != 3270303571U)
                    {
                        if (num == 3415750305U)
                        {
                            if (name == "uint")
                            {
                                if (!checkisdefault || (ushort)code != 0)
                                {
                                    return string.Format("{0}", (ushort)code);
                                }
                                return null;
                            }
                        }
                    }
                    else if (name == "long")
                    {
                        if (!checkisdefault || code != 0U)
                        {
                            return string.Format("{0}", (int)code);
                        }
                        return null;
                    }
                }
                else if (num <= 3564297305U)
                {
                    if (num != 3437915536U)
                    {
                        if (num == 3564297305U)
                        {
                            if (name == "date")
                            {
                                if (!checkisdefault || (!this.Flag.HasFlag(PbVariableFlag.Invalid) && !(BufferHelper.GetDate(valueBuffer, (long)((ulong)code)) == "1900-01-01")))
                                {
                                    return string.Format("{0}", BufferHelper.GetDate(valueBuffer, (long)((ulong)code)));
                                }
                                return null;
                            }
                        }
                    }
                    else if (name == "datetime")
                    {
                        if (!checkisdefault || (!this.Flag.HasFlag(PbVariableFlag.Invalid) && !(BufferHelper.GetDateTime(valueBuffer, (long)((ulong)code)) == "datetime(1900-01-01,00:00:00)")))
                        {
                            return string.Format("{0}", BufferHelper.GetDateTime(valueBuffer, (long)((ulong)code)));
                        }
                        return null;
                    }
                }
                else if (num != 3604983901U)
                {
                    if (num == 3867392237U)
                    {
                        if (name == "longlong")
                        {
                            if (!checkisdefault || (!this.Flag.HasFlag(PbVariableFlag.Invalid) && !(BufferHelper.GetLongLong(valueBuffer, (long)((ulong)code)) == "0")))
                            {
                                return BufferHelper.GetLongLong(valueBuffer, (long)((ulong)code));
                            }
                            return null;
                        }
                    }
                }
                else if (name == "real")
                {
                    if (!checkisdefault || code != 0U)
                    {
                        return BufferHelper.GetReal(code);
                    }
                    return null;
                }
                return null;
            }
            if (!checkisdefault || (ushort)code != 0)
            {
                return this.Type.Enum.Items[(ushort)code];
            }
            return null;
        }

        // Token: 0x0600014E RID: 334 RVA: 0x0000C75C File Offset: 0x0000A95C
        private List<uint> GetList(byte[] valuebuffer)
        {
            List<uint> list = new List<uint>();
            ushort @ushort = BufferHelper.GetUShort(this.Buffer, 12L);
            ushort ushort2 = BufferHelper.GetUShort(valuebuffer, (long)(@ushort + 14));
            int num = (int)(@ushort + 28 + ushort2 * 8);
            uint @uint = BufferHelper.GetUInt(valuebuffer, (long)num);
            int num2 = 0;
            while ((long)num2 < (long)((ulong)@uint))
            {
                list.Add(BufferHelper.GetUInt(valuebuffer, (long)(num + 4 + 8 * num2)));
                num2++;
            }
            return list;
        }

        // Token: 0x0600014F RID: 335 RVA: 0x0000C7C8 File Offset: 0x0000A9C8
        public void SetCursorParams(IEnumerable<string> paramList, string sqlcaStr)
        {
            if (this._sqlDeclear == null)
            {
                this._sqlDeclear = BufferHelper.GetCursor(this.Entry.Project.IsUnicode, this.Entry.VariableBuffer, BufferHelper.GetUInt(this.Buffer, 12L), paramList);
                this._sqlDeclear = string.Format("declare {0} cursor for {1} using {2} ;", this.Name, this._sqlDeclear, sqlcaStr);
            }
        }

        // Token: 0x06000150 RID: 336 RVA: 0x0000C830 File Offset: 0x0000AA30
        public void SetDynamicCursorParams(string sqlsaStr)
        {
            if (this._sqlDeclear == null)
            {
                this._sqlDeclear = BufferHelper.GetCursor(this.Entry.Project.IsUnicode, this.Entry.VariableBuffer, BufferHelper.GetUInt(this.Buffer, 12L), null);
                this._sqlDeclear = string.Format("declare {0} dynamic cursor {1} for {2} ;", this.Name, this._sqlDeclear, sqlsaStr);
            }
        }

        // Token: 0x06000151 RID: 337 RVA: 0x0000C898 File Offset: 0x0000AA98
        public void SetProcdureParams(IEnumerable<string> paramList, string sqlcaStr)
        {
            if (this._sqlDeclear == null)
            {
                this._sqlDeclear = BufferHelper.GetCursor(this.Entry.Project.IsUnicode, this.Entry.VariableBuffer, BufferHelper.GetUInt(this.Buffer, 12L), paramList).Replace("execute ", "");
                this._sqlDeclear = string.Format("declare {0} procedure for {1} using {2} ;", this.Name, this._sqlDeclear, sqlcaStr);
            }
        }

        // Token: 0x06000152 RID: 338 RVA: 0x0000C910 File Offset: 0x0000AB10
        public void SetDynamictProcdureParams(string sqlsaStr)
        {
            if (this._sqlDeclear == null)
            {
                this._sqlDeclear = BufferHelper.GetCursor(this.Entry.Project.IsUnicode, this.Entry.VariableBuffer, BufferHelper.GetUInt(this.Buffer, 12L), null);
                this._sqlDeclear = string.Format("declare {0} dynamic procedure {1} for {2} ;", this.Name, this._sqlDeclear, sqlsaStr);
            }
        }

        // Token: 0x06000153 RID: 339 RVA: 0x0000C978 File Offset: 0x0000AB78
        public string ToString(byte[] valueBuffer, bool debug = false)
        {
#if FAKESHARP
            string text = "";
            string GetFakeType(string type, string size)
            {
                if (type == "decimal" && size == "{0}")
                {
                    return "Decimal0";

                }
                if (type == "decimal" && size == "{1}")
                {
                    return "Decimal1";

                }
                if (type == "decimal" && size == "{2}")
                {
                    return "Decimal2";

                }
                if (type == "decimal" && size == "{3}")
                {
                    return "Decimal3";

                }
                if (type == "decimal" && size == "{4}")
                {
                    return "Decimal4";

                }


                return type + size;
            }
            if (string.IsNullOrEmpty(this.ArrayString))
            {
                
                //非数组
                text = string.Format("{0}{1} {2}", new object[]
                {
                this.AccessString,
                GetFakeType(this.Type.Name, this.PrecisionOrSize),
                this.Name

                });
            }
            else
            {
                //数组
                text = string.Format("{0}PBArray<{1}> {2}", new object[]
                {
                this.AccessString,
                GetFakeType(this.Type.Name, this.PrecisionOrSize),
                this.Name

                });
            }
#else
		string text = string.Format("{0}{1}{2} {3}{4}", new object[]
		{
				this.AccessString,
				this.Type.Name,
				this.PrecisionOrSize,
				this.Name,
				this.ArrayString
		});
#endif

            if (this._sqlDeclear != null)
            {
                text = this._sqlDeclear;
            }
            if (this.IsConstant)
            {
                text = "constant " + text;
            }
            if (debug)
            {
                if (this.IsReferencedGlobal)
                {
                    text = "global " + text;
                }
                else if (this.IsShared)
                {
                    text = "shared " + text;
                }
                text = BufferHelper.GetHexString(this.Buffer) + "  " + text;
            }
            if (valueBuffer != null)
            {
                string text2 = null;
                if (!this.IsReferencedGlobal)
                {
                    text2 = this.GetValue(valueBuffer);
                }
                if (text2 != null)
                {
                    text += string.Format(" = {0}", text2);
                }
            }
            return text;
        }

        // Token: 0x0400007C RID: 124
        private string _sqlDeclear;
    }
}

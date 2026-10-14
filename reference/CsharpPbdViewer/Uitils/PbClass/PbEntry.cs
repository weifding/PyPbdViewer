using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Windows.Media.Imaging;

namespace PbdViewer.Uitils.PbClass
{
	// Token: 0x02000019 RID: 25
	public class PbEntry
	{
		// Token: 0x17000053 RID: 83
		// (get) Token: 0x06000154 RID: 340 RVA: 0x0000CA5A File Offset: 0x0000AC5A
		// (set) Token: 0x06000155 RID: 341 RVA: 0x0000CA62 File Offset: 0x0000AC62
		public byte[] VariableBuffer { get; set; }

		// Token: 0x17000054 RID: 84
		// (get) Token: 0x06000156 RID: 342 RVA: 0x0000CA6B File Offset: 0x0000AC6B
		// (set) Token: 0x06000157 RID: 343 RVA: 0x0000CA73 File Offset: 0x0000AC73
		private byte[] FunctionBuffer { get; set; }

		// Token: 0x17000055 RID: 85
		// (get) Token: 0x06000158 RID: 344 RVA: 0x0000CA7C File Offset: 0x0000AC7C
		// (set) Token: 0x06000159 RID: 345 RVA: 0x0000CA84 File Offset: 0x0000AC84
		private byte[] ParamBuffer { get; set; }

		// Token: 0x17000056 RID: 86
		// (get) Token: 0x0600015A RID: 346 RVA: 0x0000CA8D File Offset: 0x0000AC8D
		public Dictionary<ushort, PbType> Types { get; } = new Dictionary<ushort, PbType>();

		// Token: 0x17000057 RID: 87
		// (get) Token: 0x0600015B RID: 347 RVA: 0x0000CA95 File Offset: 0x0000AC95
		// (set) Token: 0x0600015C RID: 348 RVA: 0x0000CA9D File Offset: 0x0000AC9D
		public PbVariable[] Variables { get; private set; }

		// Token: 0x17000058 RID: 88
		// (get) Token: 0x0600015D RID: 349 RVA: 0x0000CAA6 File Offset: 0x0000ACA6
		public Dictionary<ushort, PbObject> Objects { get; } = new Dictionary<ushort, PbObject>();

		// Token: 0x17000059 RID: 89
		// (get) Token: 0x0600015E RID: 350 RVA: 0x0000CAAE File Offset: 0x0000ACAE
		public PbProject Project { get; }

		// Token: 0x1700005A RID: 90
		// (get) Token: 0x0600015F RID: 351 RVA: 0x0000CAB6 File Offset: 0x0000ACB6
		public PbFile File { get; }

		// Token: 0x1700005B RID: 91
		// (get) Token: 0x06000160 RID: 352 RVA: 0x0000CABE File Offset: 0x0000ACBE
		// (set) Token: 0x06000161 RID: 353 RVA: 0x0000CAC6 File Offset: 0x0000ACC6
		public PbObject EntryObject { get; private set; }

		// Token: 0x1700005C RID: 92
		// (get) Token: 0x06000162 RID: 354 RVA: 0x0000CACF File Offset: 0x0000ACCF
		public string EntryName { get; }

		// Token: 0x1700005D RID: 93
		// (get) Token: 0x06000163 RID: 355 RVA: 0x0000CAD7 File Offset: 0x0000ACD7
		// (set) Token: 0x06000164 RID: 356 RVA: 0x0000CADF File Offset: 0x0000ACDF
		public string Source { get; private set; }

		// Token: 0x1700005E RID: 94
		// (get) Token: 0x06000165 RID: 357 RVA: 0x0000CAE8 File Offset: 0x0000ACE8
		// (set) Token: 0x06000166 RID: 358 RVA: 0x0000CAF0 File Offset: 0x0000ACF0
		public BitmapImage Bitmap { get; private set; }

		// Token: 0x1700005F RID: 95
		// (get) Token: 0x06000167 RID: 359 RVA: 0x0000CAF9 File Offset: 0x0000ACF9
		public string Name { get; }

		// Token: 0x17000060 RID: 96
		// (get) Token: 0x06000168 RID: 360 RVA: 0x0000CB01 File Offset: 0x0000AD01
		public string Suffix { get; }

		// Token: 0x17000061 RID: 97
		// (get) Token: 0x06000169 RID: 361 RVA: 0x0000CB09 File Offset: 0x0000AD09
		// (set) Token: 0x0600016A RID: 362 RVA: 0x0000CB11 File Offset: 0x0000AD11
		public DateTime ModifiedTime { get; set; }

		// Token: 0x17000062 RID: 98
		// (get) Token: 0x0600016B RID: 363 RVA: 0x0000CB1A File Offset: 0x0000AD1A
		// (set) Token: 0x0600016C RID: 364 RVA: 0x0000CB22 File Offset: 0x0000AD22
		public DateTime CompliedTime { get; set; }

		// Token: 0x0600016D RID: 365 RVA: 0x0000CB2C File Offset: 0x0000AD2C
		private void PrintString(string str)
		{
			for (int i = 0; i < this._indent; i++)
			{
				this._sb.Append("\t");
			}
			this._sb.Append(str);
			this._sb.Append("\r\n");
		}

		// Token: 0x0600016E RID: 366 RVA: 0x0000CB7C File Offset: 0x0000AD7C
		private void PrintBuffer(byte[] buff, int step)
		{
			int num = buff.Length / step;
			for (int i = 0; i < num; i++)
			{
				this.PrintString(string.Format("{0:X04}:{1:X04}   ", i, i * step) + BufferHelper.GetHexString(buff, (long)(i * step), step));
			}
			int num2 = buff.Length - num * step;
			if (num2 > 0)
			{
				this.PrintString(string.Format("{0:X04}:{1:X04}   ", num, num * step) + BufferHelper.GetHexString(buff, (long)(num * step), num2));
			}
		}

		// Token: 0x0600016F RID: 367 RVA: 0x0000CC04 File Offset: 0x0000AE04
		private static DateTime GetTime(uint timeStamp)
		{
			DateTime dateTime = TimeZone.CurrentTimeZone.ToLocalTime(new DateTime(1970, 1, 1));
			TimeSpan value = new TimeSpan((long)((ulong)timeStamp * 10000000UL));
			return dateTime.Add(value);
		}

		// Token: 0x06000170 RID: 368 RVA: 0x0000CC40 File Offset: 0x0000AE40
		public PbEntry(PbFile file, string entryName, byte[] entryData)
		{
			this._entryData = entryData;
			this.File = file;
			this.EntryName = entryName;
			this.Project = this.File.Project;
			this.Name = this.EntryName.Substring(0, this.EntryName.LastIndexOfAny(new char[]
			{
				'.'
			}));
			this.Suffix = this.EntryName.Substring(this.EntryName.LastIndexOfAny(new char[]
			{
				'.'
			}) + 1);
			string suffix = this.Suffix;
			uint num = PrivateImplementationDetails.ComputeStringHash(suffix);
			if (num <= 1824651960U)
			{
				if (num <= 1371315337U)
				{
					if (num != 200788825U)
					{
						if (num != 862626472U)
						{
							if (num != 1371315337U)
							{
								goto IL_353;
							}
							if (!(suffix == "udo"))
							{
								goto IL_353;
							}
							goto IL_326;
						}
						else
						{
							if (!(suffix == "apl"))
							{
								goto IL_353;
							}
							goto IL_326;
						}
					}
					else
					{
						if (!(suffix == "win"))
						{
							goto IL_353;
						}
						goto IL_326;
					}
				}
				else if (num <= 1738962391U)
				{
					if (num != 1446480772U)
					{
						if (num != 1738962391U)
						{
							goto IL_353;
						}
						if (!(suffix == "exe"))
						{
							goto IL_353;
						}
						this.ParseExe();
						this._isParsed = true;
						return;
					}
					else
					{
						if (!(suffix == "grp"))
						{
							goto IL_353;
						}
						this.Project.OnSystemEntry(this);
						this.ParseObject(true);
						this._isParsed = true;
						return;
					}
				}
				else if (num != 1748353692U)
				{
					if (num != 1824651960U)
					{
						goto IL_353;
					}
					if (!(suffix == "bmp"))
					{
						goto IL_353;
					}
				}
				else if (!(suffix == "png"))
				{
					goto IL_353;
				}
			}
			else if (num <= 3259748752U)
			{
				if (num != 2095122494U)
				{
					if (num != 2832955486U)
					{
						if (num != 3259748752U)
						{
							goto IL_353;
						}
						if (!(suffix == "str"))
						{
							goto IL_353;
						}
						goto IL_326;
					}
					else
					{
						if (!(suffix == "fun"))
						{
							goto IL_353;
						}
						goto IL_326;
					}
				}
				else if (!(suffix == "ico"))
				{
					goto IL_353;
				}
			}
			else if (num <= 3459018009U)
			{
				if (num != 3383581291U)
				{
					if (num != 3459018009U)
					{
						goto IL_353;
					}
					if (!(suffix == "dwo"))
					{
						goto IL_353;
					}
					this.Source = "DataWindow可以通过PB接口函数导出";
					this._isParsed = true;
					return;
				}
				else
				{
					if (!(suffix == "men"))
					{
						goto IL_353;
					}
					goto IL_326;
				}
			}
			else if (num != 3661425870U)
			{
				if (num != 3670499120U)
				{
					goto IL_353;
				}
				if (!(suffix == "jpg"))
				{
					goto IL_353;
				}
			}
			else
			{
				if (!(suffix == "srj"))
				{
					goto IL_353;
				}
				this.ParseSrj();
				this._isParsed = true;
				return;
			}
			this.Bitmap = new BitmapImage();
			this.Bitmap.BeginInit();
			this.Bitmap.StreamSource = new MemoryStream(this._entryData);
			this.Bitmap.EndInit();
			this._isParsed = true;
			return;
			IL_326:
			this.Project.OnSystemLibrary(BufferHelper.GetUShort(this._entryData, 0L));
			return;
			IL_353:
			this.Source = this.Project.GetString(this._entryData);
			this._isParsed = true;
		}

		// Token: 0x06000171 RID: 369 RVA: 0x0000CFC0 File Offset: 0x0000B1C0
		public void ParseObject(bool isSystem = false)
		{
			if (this._isParsed)
			{
				return;
			}
			this._sb.Clear();
			this._dataBuffer = this._entryData;
			this._position = 0L;
			this.PrintString(string.Format("Pdb Version: {0:X}", this.ReadUShort()));
			this._flag = this.ReadUShort();
			this.PrintString(string.Format("Flag: {0:X}", this._flag));
			uint num = this.ReadUInt();
			this.PrintString(string.Format("EntryType: {0:X}", num));
			uint num2 = this.ReadUInt();
			this.PrintString(string.Format("Unkown: {0:X}", num2));
			this.ModifiedTime = PbEntry.GetTime(this.ReadUInt());
			if (this.Project.Version >= 334)
			{
				this.ReadUInt();
			}
			this.PrintString(string.Format("Last Modify Time: {0}", this.ModifiedTime));
			this.CompliedTime = PbEntry.GetTime(this.ReadUInt());
			if (this.Project.Version >= 334)
			{
				this.ReadUInt();
			}
			this.PrintString(string.Format("Last Complied Time: {0}", this.CompliedTime));
			uint num3 = this.ReadUInt();
			this.PrintString(string.Format("Unkown: {0:X}", num3));
			ushort num4 = this.ReadUShort();
			byte[][] array = new byte[(int)num4][];
			for (int i = 0; i < (int)num4; i++)
			{
				array[i] = this.ReadBuffer(12);
			}
			this.VariableBuffer = this.ReadStructBuffer();
			this.Variables = this.ReadVariables(true);
			//对象数
			ushort totalObjNum = this.ReadUShort();
			ushort num6 = this.ReadUShort();
			this.FunctionBuffer = this.ReadStructBuffer();
			this.ParamBuffer = this.ReadStructBuffer();
			using (new PbEntry.IndentBlock(this, "Types"))
			{
				this.ReadTypes(isSystem);
			}
			PbVariable[] variables = this.Variables;
			for (int j = 0; j < variables.Length; j++)
			{
				variables[j].ParseType();
			}
			using (new PbEntry.IndentBlock(this, "Globel and Shared Variables"))
			{
				for (int k = 0; k < this.Variables.Length; k++)
				{
					this.PrintString(string.Format("{0:X2}:  ", k) + this.Variables[k].ToString(this.VariableBuffer, this._isDebug));
				}
			}
			PbVariable[] array2 = this.ReadVariables(false);
			using (new PbEntry.IndentBlock(this, "Enums"))
			{
				for (int l = 0; l < array2.Length; l++)
				{
					this.PrintString(string.Format("{0:X2}:  ", l) + array2[l].ToString(null, this._isDebug));
					this.Project.OnNewEnumItem(array2[l].Type, BufferHelper.GetUShort(array2[l].Buffer, 12L), array2[l].Name);
				}
			}
			//对象的原始数据
			int size = this.Project.IsPb5 ? 8 : 16;
			byte[][] objrawdata = new byte[(int)totalObjNum][];
			for (int m = 0; m < (int)totalObjNum; m++)
			{
				objrawdata[m] = this.ReadBuffer(size);
			}

			byte[][] array4 = new byte[(int)num6][];
			for (int n = 0; n < (int)num6; n++)
			{
				array4[n] = this.ReadBuffer(32);
			}
			int num7 = 0;
			//分析对象数据
			using (new PbEntry.IndentBlock(this, string.Format("Objects: {0}", totalObjNum)))
			{
				ushort index = 0;
				while (index < totalObjNum)
				{
					//对象原始数据分析
					byte[] raw = objrawdata[(int)index];
					//获取类型
					PbType pbType = PbType.GetPbType(this, BufferHelper.GetUShort(raw, 2L));
					PbObject pbObject = new PbObject(this, index, pbType);
					int num9 = raw[0] >> 1 & 7;
					if (num9 == 0)
					{
						byte[] array6 = array4[num7++];
						pbObject.InheritType = PbType.GetPbType(this, BufferHelper.GetUShort(array6, 0L));
						pbObject.ParentType = PbType.GetPbType(this, BufferHelper.GetUShort(array6, 2L));
						this.Objects[pbObject.Type.Index] = pbObject;
						if (isSystem)
						{
							this.Project.OnNewObject(pbObject, null);
						}
						else if (pbObject.Type.Name == this.Name)
						{
							this.EntryObject = pbObject;
							this.Project.OnNewObject(pbObject, null);
						}
						else if (!pbObject.Type.Name.Contains('`'))
						{
							this.Project.OnNewObject(pbObject, this.Name + "`" + pbObject.Type.Name);
						}
						using (new PbEntry.IndentBlock(this, string.Format("Object[{0}] {1}:{2}", index, pbType.Name, pbObject.InheritType.Name)))
						{
							this.PrintBuffer(raw, 16);
							this.PrintBuffer(array6, array6.Length);
							//获取对象中的附属信息，函数，属性，控件，事件和内部对象
							this.ReadObject(pbObject, array6);
							goto IL_56D;
						}

						goto IL_4E9;
					}
					goto IL_4E9;
					IL_56D:
					index += 1;
					continue;

					
					IL_4E9:
					//这部分代码无法被访问到
					using (new PbEntry.IndentBlock(this, string.Format("Object[{0}] {1}", index, pbType.Name)))
					{
						this.PrintBuffer(raw, 16);
						if (num9 == 1)
						{
							ushort @ushort = BufferHelper.GetUShort(raw, 4L);
							byte[][] array7 = new byte[(int)@ushort][];
							for (int num10 = 0; num10 < (int)@ushort; num10++)
							{
								array7[num10] = this.ReadBuffer(8);
								this.PrintBuffer(array7[num10], 16);
							}
						}
						else if (num9 == 6)
						{
							break;
						}
					}
					goto IL_56D;
				}
			}
			if (this.Project.IsDebug)
			{
				this.Source = this._sb.ToString();
			}
			this.Source = this._sb.ToString();
			this._sb.Clear();
			if (this._position != (long)this._dataBuffer.Length)
			{
				throw new Exception("读取错误");
			}
			this._isParsed = true;
		}

		// Token: 0x06000172 RID: 370 RVA: 0x0000D63C File Offset: 0x0000B83C
		private void ReadObject(PbObject pbObject, byte[] buffer)
		{
			ushort num = this.ReadUShort();
			pbObject.Functions = new PbFunction[(int)num];
			using (new PbEntry.IndentBlock(this, string.Format("Functions: {0}", num)))
			{
				byte[][] array = new byte[(int)num][];
				for (int i = 0; i < (int)num; i++)
				{
					array[i] = this.ReadBuffer(4);
				}
				for (int j = 0; j < (int)num; j++)
				{
					pbObject.Functions[j] = new PbFunction(pbObject);
					this.ReadFunction(pbObject.Functions[j], array[j]);
				}
			}
			num = BufferHelper.GetUShort(buffer, 24L);
			this.ReadBuffer((int)(6 * num));
			num = BufferHelper.GetUShort(buffer, 22L);
			this.ReadBuffer((int)(4 * num));
			pbObject.ReferencedFunctions = this.ReadReferencedFunctions();
			using (new PbEntry.IndentBlock(this, string.Format("Referenced Functions And Events: {0}", pbObject.ReferencedFunctions.Length)))
			{
				for (int k = 0; k < pbObject.ReferencedFunctions.Length; k++)
				{
					this.PrintString(string.Format("{0:X2}:  ", k) + pbObject.ReferencedFunctions[k].ToString(this._isDebug));
				}
			}
			pbObject.Variables = this.ReadVariables(false);
			using (new PbEntry.IndentBlock(this, string.Format("Properties Or Controls: {0}", pbObject.Variables.Length)))
			{
				for (int l = 0; l < pbObject.Variables.Length; l++)
				{
					pbObject.Variables[l].Object = pbObject;
					this.PrintString(string.Format("{0:X2}:  ", l) + pbObject.Variables[l].ToString(this.VariableBuffer, this._isDebug));
				}
			}
			ushort @ushort = BufferHelper.GetUShort(buffer, 28L);
			this.ReadBuffer((int)(8 * @ushort));
			pbObject.AllVariables = new PbVariable[(int)@ushort];
			int num2 = this.Project.IsPb5 ? 12 : 16;
			num = BufferHelper.GetUShort(buffer, 26L);
			byte[] buff = this.ReadBuffer(num2 * (int)num);
			this.PrintBuffer(buff, num2);
			num = BufferHelper.GetUShort(buffer, 4L);
			int num3 = (this.Project.Version > 146) ? 48 : (this.Project.IsPb5 ? 32 : 44);
			pbObject.FunctionDefinitions = new PbFunctionDefinition[(int)num];
			pbObject.AllFunctionDefinitions = new PbFunctionDefinition[(int)BufferHelper.GetUShort(buffer, 16L)];
			using (new PbEntry.IndentBlock(this, "Events And Functions"))
			{
				for (ushort num4 = 0; num4 < num; num4 += 1)
				{
					byte[] array2 = this.ReadBuffer(num3);
					this.PrintBuffer(array2, num3);
					PbFunctionDefinition pbFunctionDefinition = new PbFunctionDefinition();
					pbObject.FunctionDefinitions[(int)num4] = pbFunctionDefinition;
					pbFunctionDefinition.Object = pbObject;
					pbFunctionDefinition.Index = num4;
					pbFunctionDefinition.Flag = (PbFunctionFlag)array2[this.Project.IsPb5 ? 27 : 31];
					pbFunctionDefinition.ReturnType = PbType.GetPbType(this, BufferHelper.GetUShort(array2, this.Project.IsPb5 ? 24L : 28L));
					pbFunctionDefinition.Name = BufferHelper.GetString(this.Project.IsUnicode, this.FunctionBuffer, (long)((ulong)BufferHelper.GetUInt(array2, 0L)));
					if (pbFunctionDefinition.Name.StartsWith("+"))
					{
						pbFunctionDefinition.Name = pbFunctionDefinition.Name.Substring(1);
					}
					pbFunctionDefinition.GlobalIndex = BufferHelper.GetUShort(array2, this.Project.IsPb5 ? 16L : 20L);
					pbFunctionDefinition.RefIndex = BufferHelper.GetUShort(array2, this.Project.IsPb5 ? 18L : 22L);
					pbFunctionDefinition.EventCode = BufferHelper.GetUShort(array2, this.Project.IsPb5 ? 28L : 32L);
					pbFunctionDefinition.Params = new PbFunctionParam[0];
					uint @uint = BufferHelper.GetUInt(array2, this.Project.IsPb5 ? 4L : 8L);
					if (@uint != 65535U)
					{
						byte b = array2[this.Project.IsPb5 ? 26 : 30];
						pbFunctionDefinition.Params = new PbFunctionParam[(int)b];
						for (int m = 0; m < (int)b; m++)
						{
							PbFunctionParam pbFunctionParam = new PbFunctionParam();
							pbFunctionDefinition.Params[m] = pbFunctionParam;
							byte[] buffer2 = BufferHelper.GetBuffer(this.ParamBuffer, (long)(@uint + (uint)(m * 12)), 12);
							if ((buffer2[10] & 4) == 4)
							{
								pbFunctionParam.IsReadOnly = true;
							}
							else if ((buffer2[10] & 2) == 2)
							{
								pbFunctionParam.IsReference = true;
							}
							pbFunctionParam.Type = PbType.GetPbType(this, BufferHelper.GetUShort(buffer2, 8L));
							pbFunctionParam.Name = BufferHelper.GetString(this.Project.IsUnicode, this.FunctionBuffer, (long)BufferHelper.GetUInt(buffer2, 0L));
							pbFunctionParam.ArrayString = PbVariable.GetArrayString(BufferHelper.GetUInt(buffer2, 4L), this.FunctionBuffer);
						}
					}
					uint uint2 = BufferHelper.GetUInt(array2, this.Project.IsPb5 ? 8L : 12L);
					if (uint2 != 65535U)
					{
						uint uint3 = BufferHelper.GetUInt(array2, this.Project.IsPb5 ? 12L : 16L);
						pbFunctionDefinition.Library = BufferHelper.GetString(this.Project.IsUnicode, this.FunctionBuffer, (long)uint3);
						pbFunctionDefinition.Alias = BufferHelper.GetString(this.Project.IsUnicode, this.FunctionBuffer, (long)uint2);
					}
					if (this.Project.Version > 146)
					{
						ushort ushort2 = BufferHelper.GetUShort(array2, 44L);
						if (ushort2 != 65535)
						{
							pbFunctionDefinition.ThrowsType = PbType.GetPbType(this, BufferHelper.GetUShort(this.FunctionBuffer, (long)((ulong)ushort2)));
						}
					}
					this.PrintString(pbFunctionDefinition.ToString());
				}
			}
		}

		// Token: 0x06000173 RID: 371 RVA: 0x0000DC6C File Offset: 0x0000BE6C
		private void ReadFunction(PbFunction pbFunction, byte[] index)
		{
			using (new PbEntry.IndentBlock(this, string.Format("Function :{0}", string.Join(" ", from o in index
			select string.Format("{0:X4}", o)))))
			{
				pbFunction.Index = BufferHelper.GetUShort(index, 2L);
				ushort num = this.ReadUShort();
				ushort num2 = this.ReadUShort();
				this.PrintString(string.Format("{0:X4} {1:X4} {2:X4}", num, num2, this.ReadUShort()));
				pbFunction.PCodeBytes = this.ReadBuffer((int)num);
				pbFunction.DebugBytes = this.ReadBuffer((int)(num2 * 4));
				using (new PbEntry.IndentBlock(this, "PCodes"))
				{
					foreach (string str in PCodeHelper.ParsePCode(pbFunction, false))
					{
						this.PrintString(str);
					}
				}
				pbFunction.Variables = this.ReadVariables(false);
				pbFunction.Buffer = this.ReadStructBuffer();
				using (new PbEntry.IndentBlock(this, "Stack"))
				{
					this.PrintBuffer(pbFunction.Buffer, 16);
				}
				using (new PbEntry.IndentBlock(this, string.Format("Variable {0}", pbFunction.Variables.Length)))
				{
					for (int i = 0; i < pbFunction.Variables.Length; i++)
					{
						pbFunction.Variables[i].Object = pbFunction.Object;
						this.PrintString(string.Format("{0:X4}: {1}", i, pbFunction.Variables[i].ToString(pbFunction.Buffer, this._isDebug)));
					}
				}
			}
		}

		// Token: 0x06000174 RID: 372 RVA: 0x0000DEB4 File Offset: 0x0000C0B4
		/// <summary>
		/// 读取原始文件内容，并移动游标位置2L
		/// </summary>
		/// <returns></returns>
		private ushort ReadUShort()
		{
			this._position += 2L;
			return BufferHelper.GetUShort(this._dataBuffer, this._position - 2L);
		}

		// Token: 0x06000175 RID: 373 RVA: 0x0000DED9 File Offset: 0x0000C0D9
		/// <summary>
		/// 读取原始文件内容，并移动游标位置4L
		/// </summary>
		/// <returns></returns>
		private uint ReadUInt()
		{
			this._position += 4L;
			return BufferHelper.GetUInt(this._dataBuffer, this._position - 4L);
		}

		// Token: 0x06000176 RID: 374 RVA: 0x0000DEFE File Offset: 0x0000C0FE
		/// <summary>
		/// 读取原始文件内容，并移动游标位置
		/// </summary>
		/// <param name="size"></param>
		/// <returns></returns>
		private byte[] ReadBuffer(int size)
		{
			this._position += (long)size;
			return BufferHelper.GetBuffer(this._dataBuffer, this._position - (long)size, size);
		}

		// Token: 0x06000177 RID: 375 RVA: 0x0000DF24 File Offset: 0x0000C124
		private byte[] ReadStructBuffer()
		{
			uint size = this.ReadUInt();
			uint size2 = this.ReadUInt();
			byte[] result = this.ReadBuffer((int)size);
			this.ReadBuffer((int)size2);
			return result;
		}

		// Token: 0x06000178 RID: 376 RVA: 0x0000DF50 File Offset: 0x0000C150
		private PbType[] ReadTypes(bool isSystemEntry)
		{
			this.ReadBuffer(6);
			byte[] buffer = this.ReadStructBuffer();
			int num = (int)(this.ReadUShort() / 20);
			PbType[] array = new PbType[num];
			ushort num2 = 0;
			while ((int)num2 < num)
			{
				byte[] array2 = this.ReadBuffer(20);
				array[(int)num2] = new PbType(this, num2, BufferHelper.GetString(this.Project.IsUnicode, buffer, (long)((ulong)BufferHelper.GetUInt(array2, 8L))), array2[16] == 64, isSystemEntry);
				this.PrintString(string.Format("{0:X4} {1} {2}", num2, BufferHelper.GetHexString(array2), array[(int)num2].Name));
				num2 += 1;
			}
			return array;
		}

		// Token: 0x06000179 RID: 377 RVA: 0x0000DFEC File Offset: 0x0000C1EC
		private PbVariable[] ReadVariables(bool delayParseType = false)
		{
			this.ReadBuffer(6);
			byte[] structBuffer = this.ReadStructBuffer();
			int num = (int)(this.ReadUShort() / 20);
			PbVariable[] array = new PbVariable[num];
			ushort num2 = 0;
			while ((int)num2 < num)
			{
				byte[] buffer = this.ReadBuffer(20);
				array[(int)num2] = new PbVariable(this, num2, buffer, structBuffer, delayParseType);
				num2 += 1;
			}
			return array;
		}

		// Token: 0x0600017A RID: 378 RVA: 0x0000E040 File Offset: 0x0000C240
		private PbReferencedFunction[] ReadReferencedFunctions()
		{
			this.ReadBuffer(6);
			byte[] buffer = this.ReadStructBuffer();
			int num = (int)(this.ReadUShort() / 20);
			PbReferencedFunction[] array = new PbReferencedFunction[num];
			ushort num2 = 0;
			while ((int)num2 < num)
			{
				byte[] array2 = this.ReadBuffer(20);
				PbReferencedFunction pbReferencedFunction = new PbReferencedFunction(num2, array2)
				{
					Name = BufferHelper.GetString(this.Project.IsUnicode, buffer, (long)((ulong)BufferHelper.GetUInt(array2, 8L))),
					GlobalIndex = BufferHelper.GetUShort(array2, 12L),
					IsGlobalFunction = (array2[16] == 2)
				};
				array[(int)num2] = pbReferencedFunction;
				num2 += 1;
			}
			return array;
		}

		// Token: 0x0600017B RID: 379 RVA: 0x0000E0D3 File Offset: 0x0000C2D3
		public override string ToString()
		{
			return this.File.FileName + "/" + this.EntryName;
		}

		// Token: 0x0600017C RID: 380 RVA: 0x0000E0F0 File Offset: 0x0000C2F0
		private void ParseSrj()
		{
			this.Source = this.Project.GetString(this._entryData);
			foreach (string text in this.Source.Split(new char[]
			{
				'\r',
				'\n'
			}, StringSplitOptions.RemoveEmptyEntries))
			{
				if (text.StartsWith("PBD:"))
				{
					this.Project.OnNewLibrary(text.Substring(4).Split(new char[]
					{
						','
					})[0], true);
				}
			}
		}

		// Token: 0x0600017D RID: 381 RVA: 0x0000E178 File Offset: 0x0000C378
		private void ParseExe()
		{
			List<string> list = new List<string>();
			List<string> list2 = new List<string>();
			if (this.Project.IsUnicode)
			{
				int num = 0;
				int k = ((int)this._entryData[num + 1] << 8) + (int)this._entryData[num];
				num += 2;
				while (k > 0)
				{
					while (this._entryData[num] != 0 || this._entryData[num + 1] != 0)
					{
						num += 2;
					}
					num += 2;
					k--;
				}
				k = ((int)this._entryData[num + 1] << 8) + (int)this._entryData[num];
				num += 2;
				int num2 = num;
				while (k > 0)
				{
					while (this._entryData[num] != 0 || this._entryData[num + 1] != 0)
					{
						num += 2;
					}
					list.Add(Encoding.Unicode.GetString(this._entryData, num2, num - num2));
					num += 2;
					num2 = num;
					k--;
				}
				k = ((int)this._entryData[num + 1] << 8) + (int)this._entryData[num];
				num += 2;
				num2 = num;
				while (k > 0)
				{
					while (this._entryData[num] != 0 || this._entryData[num + 1] != 0)
					{
						num += 2;
					}
					list2.Add(Encoding.Unicode.GetString(this._entryData, num2, num - num2));
					num += 2;
					num2 = num;
					k--;
				}
			}
			else
			{
				int num3;
				int j;
				if (this.Project.IsPb5)
				{
					num3 = 0;
					j = 1;
				}
				else
				{
					num3 = 1;
					j = (int)this._entryData[0];
				}
				while (j > 0)
				{
					while (this._entryData[num3] != 0)
					{
						num3++;
					}
					num3++;
					j--;
				}
				j = ((int)this._entryData[num3 + 1] << 8) + (int)this._entryData[num3];
				num3 += 2;
				int num4 = num3;
				while (j > 0)
				{
					while (this._entryData[num3] != 0)
					{
						num3++;
					}
					list.Add(Encoding.Default.GetString(this._entryData, num4, num3 - num4));
					num3++;
					num4 = num3;
					j--;
				}
				j = ((int)this._entryData[num3 + 1] << 8) + (int)this._entryData[num3];
				num3 += 2;
				num4 = num3;
				while (j > 0)
				{
					while (this._entryData[num3] != 0)
					{
						num3++;
					}
					list2.Add(Encoding.Default.GetString(this._entryData, num4, num3 - num4));
					num3++;
					num4 = num3;
					j--;
				}
			}
			foreach (string libpath in list)
			{
				this.Project.OnNewLibrary(libpath, false);
			}
			this.Source = string.Format("Libraries {0:X4}:\r\n\t", list.Count) + string.Join("\r\n\t", list.Select((string o, int i) => string.Format("{0:X4}:\t{1}", i, o))) + string.Format("\r\nEntries {0:X4}:\r\n\t", list2.Count) + string.Join("\r\n\t", list2.Select((string o, int i) => string.Format("{0:X4}:\t{1}", i, o)));
		}

		// Token: 0x0600017E RID: 382 RVA: 0x0000E4A8 File Offset: 0x0000C6A8
		public void OnNewType(PbType pbType)
		{
			this.Types[pbType.Index] = pbType;
		}

		// Token: 0x0600017F RID: 383 RVA: 0x0000E4BC File Offset: 0x0000C6BC
		public void ParseInherit()
		{
			foreach (PbObject pbObject in this.Objects.Values)
			{
				pbObject.ParseInherit();
			}
		}

		// Token: 0x0400007D RID: 125
		private readonly byte[] _entryData;

		// Token: 0x0400007E RID: 126
		private bool _isParsed;

		// Token: 0x0400007F RID: 127
		private ushort _flag;

		// Token: 0x04000080 RID: 128
		private int _indent;

		// Token: 0x04000081 RID: 129
		private byte[] _dataBuffer;

		// Token: 0x04000082 RID: 130
		private long _position;

		// Token: 0x04000083 RID: 131
		private readonly StringBuilder _sb = new StringBuilder();

		// Token: 0x04000084 RID: 132
		private bool _isDebug = true;

		// Token: 0x02000047 RID: 71
		private class IndentBlock : IDisposable
		{
			// Token: 0x0600020B RID: 523 RVA: 0x00010AAB File Offset: 0x0000ECAB
			public IndentBlock(PbEntry pbEntry, string blockName)
			{
				this._pbEntry = pbEntry;
				this._pbEntry.PrintString(blockName + ": {");
				this._pbEntry._indent++;
			}

			// Token: 0x0600020C RID: 524 RVA: 0x00010AE3 File Offset: 0x0000ECE3
			public void Dispose()
			{
				this._pbEntry._indent--;
				this._pbEntry.PrintString("}");
			}

			// Token: 0x04000161 RID: 353
			private readonly PbEntry _pbEntry;
		}
		public void ShowSource()
        {
			//Console.WriteLine(this._sb.ToString());
			//Console.WriteLine(this.Source);
        }
	}
}

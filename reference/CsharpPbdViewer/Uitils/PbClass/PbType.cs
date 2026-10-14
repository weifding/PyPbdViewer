#define FAKESHARP
using System;
using System.Collections.Generic;
using System.Linq;

namespace PbdViewer.Uitils.PbClass
{
	// Token: 0x02000017 RID: 23
	public class PbType
	{
		// Token: 0x1700003B RID: 59
		// (get) Token: 0x06000113 RID: 275 RVA: 0x0000B902 File Offset: 0x00009B02
		// (set) Token: 0x06000114 RID: 276 RVA: 0x0000B90A File Offset: 0x00009B0A
		public ushort Index { get; set; }

		// Token: 0x1700003C RID: 60
		// (get) Token: 0x06000115 RID: 277 RVA: 0x0000B913 File Offset: 0x00009B13
		// (set) Token: 0x06000116 RID: 278 RVA: 0x0000B91B File Offset: 0x00009B1B
		public string Name { get; set; }

		// Token: 0x1700003D RID: 61
		// (get) Token: 0x06000117 RID: 279 RVA: 0x0000B924 File Offset: 0x00009B24
		// (set) Token: 0x06000118 RID: 280 RVA: 0x0000B92C File Offset: 0x00009B2C
		public bool IsValueType { get; set; }

		// Token: 0x1700003E RID: 62
		// (get) Token: 0x06000119 RID: 281 RVA: 0x0000B935 File Offset: 0x00009B35
		// (set) Token: 0x0600011A RID: 282 RVA: 0x0000B93D File Offset: 0x00009B3D
		public bool IsSystemType { get; set; }

		// Token: 0x1700003F RID: 63
		// (get) Token: 0x0600011B RID: 283 RVA: 0x0000B946 File Offset: 0x00009B46
		// (set) Token: 0x0600011C RID: 284 RVA: 0x0000B94E File Offset: 0x00009B4E
		public bool IsReferencedObject { get; set; }

		// Token: 0x17000040 RID: 64
		// (get) Token: 0x0600011D RID: 285 RVA: 0x0000B957 File Offset: 0x00009B57
		// (set) Token: 0x0600011E RID: 286 RVA: 0x0000B95F File Offset: 0x00009B5F
		public PbEnum Enum { get; set; }

		// Token: 0x17000041 RID: 65
		// (get) Token: 0x0600011F RID: 287 RVA: 0x0000B968 File Offset: 0x00009B68
		// (set) Token: 0x06000120 RID: 288 RVA: 0x0000B970 File Offset: 0x00009B70
		public PbEntry Entry { get; set; }

		// Token: 0x17000042 RID: 66
		// (get) Token: 0x06000121 RID: 289 RVA: 0x0000B979 File Offset: 0x00009B79
		// (set) Token: 0x06000122 RID: 290 RVA: 0x0000B981 File Offset: 0x00009B81
		public PbObject Object { get; set; }

		// Token: 0x06000123 RID: 291 RVA: 0x0000B98C File Offset: 0x00009B8C
		public PbType(PbEntry entry, ushort index, string name, bool isReferencedObject, bool isSystemEntry)
		{
			this.Name = name;
			this.Entry = entry;
			this.IsReferencedObject = isReferencedObject;
			if (!isSystemEntry)
			{
				if (this.IsReferencedObject)
				{
					this.Enum = entry.Project.Enums.Values.FirstOrDefault((PbEnum o) => o.Name == this.Name);
				}
				this.Index =(ushort) (32768 | index);
				entry.OnNewType(this);
				return;
			}
			if (this.IsReferencedObject)
			{
				throw new Exception("system entry can't reference other object");
			}
			this.IsSystemType = true;
			this.Index = (ushort)(16384 | index);
			entry.Project.OnNewSystemType(this);
		}

		// Token: 0x06000124 RID: 292 RVA: 0x0000BA32 File Offset: 0x00009C32
		private PbType(ushort index)
		{
			this.Index = index;
			this.Name = this.GetValueTypeName((int)index);
			this.IsValueType = true;
		}

		// Token: 0x06000125 RID: 293 RVA: 0x0000BA58 File Offset: 0x00009C58
		public static PbType GetPbType(PbEntry pbEntry, ushort index)
		{
			int num = index >> 12;
			if (num <= 4)
			{
				if (num == 0)
				{
					if (!PbType.ValueTypes.ContainsKey(index))
					{
						PbType.ValueTypes[index] = new PbType(index);
					}
					return PbType.ValueTypes[index];
				}
				if (num == 4)
				{
					return pbEntry.Project.SystemTypes[index];
				}
			}
			else
			{
				if (num == 8)
				{
					return pbEntry.Types[index];
				}
				if (num == 12)
				{
					return new PbType(0);
				}
			}
			throw new Exception(string.Format("Unkown Type {0:X4}", index));
		}

		// Token: 0x06000126 RID: 294 RVA: 0x0000BAE8 File Offset: 0x00009CE8
		private string GetValueTypeName(int low)
		{
#if FAKESHARP
			switch (low)
			{
				case 0:
					return "";
				case 1:
					return "int";
				case 2:
					return "long";
				case 3:
					return "float";
				case 4:
					return "double";
				case 5:
					return "decimal";
				case 6:
					return "string";
				case 7:
					return "bool";
				case 8: 
					return "dynamic";
				case 9:
					return "uint";
				case 10:
					return "ulong";
				case 11:
					return "blob";
				case 12:
					return "DateOnly";
				case 13:
					return "TimeOnly";
				case 14:
					return "DateTime";
				case 15:
					return "cursor";
				case 16:
					return "procedure";
				case 18:
					return "char";
				case 19:
					return "objhandle";
				case 20:
					return "longlong";
				case 21:
					return "byte";
			}

#else
			switch (low)
			{
			case 0:
				return "";
			case 1:
				return "integer";
			case 2:
				return "long";
			case 3:
				return "real";
			case 4:
				return "double";
			case 5:
				return "decimal";
			case 6:
				return "string";
			case 7:
				return "boolean";
			case 8:
				return "any";
			case 9:
				return "uint";
			case 10:
				return "ulong";
			case 11:
				return "blob";
			case 12:
				return "date";
			case 13:
				return "time";
			case 14:
				return "datetime";
			case 15:
				return "cursor";
			case 16:
				return "procedure";
			case 18:
				return "char";
			case 19:
				return "objhandle";
			case 20:
				return "longlong";
			case 21:
				return "byte";
			}
#endif
			return string.Format("{0:X4}", low);
		}

		// Token: 0x06000127 RID: 295 RVA: 0x0000BBE4 File Offset: 0x00009DE4
		public PbObject GetObject(PbEntry pbEntry)
		{
			if (this.Object != null)
			{
				return this.Object;
			}
			if (this.IsValueType)
			{
				return this.Object;
			}
			if (this._isFinded)
			{
				return this.Object;
			}
			if (this.Name.Contains('`') || this.IsSystemType || this.IsReferencedObject)
			{
				if (pbEntry.Project.Objects.ContainsKey(this.Name))
				{
					this.Object = pbEntry.Project.Objects[this.Name];
				}
			}
			else
			{
				pbEntry = (this.Entry ?? pbEntry);
				if (pbEntry.Objects.ContainsKey(this.Index))
				{
					this.Object = pbEntry.Objects[this.Index];
				}
			}
			this._isFinded = true;
			return this.Object;
		}

		// Token: 0x04000063 RID: 99
		private static readonly Dictionary<ushort, PbType> ValueTypes = new Dictionary<ushort, PbType>();

		// Token: 0x04000064 RID: 100
		private bool _isFinded;
	}
}

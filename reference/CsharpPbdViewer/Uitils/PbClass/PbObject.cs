using System;
using System.Collections.Generic;
using System.Linq;

namespace PbdViewer.Uitils.PbClass
{
	// Token: 0x02000015 RID: 21
	public class PbObject
	{
		// Token: 0x17000028 RID: 40
		// (get) Token: 0x060000EB RID: 235 RVA: 0x0000B510 File Offset: 0x00009710
		public PbEntry Entry { get; }

		// Token: 0x17000029 RID: 41
		// (get) Token: 0x060000EC RID: 236 RVA: 0x0000B518 File Offset: 0x00009718
		public PbProject Project { get; }

		// Token: 0x1700002A RID: 42
		// (get) Token: 0x060000ED RID: 237 RVA: 0x0000B520 File Offset: 0x00009720
		public ushort Index { get; }

		// Token: 0x1700002B RID: 43
		// (get) Token: 0x060000EE RID: 238 RVA: 0x0000B528 File Offset: 0x00009728
		public PbType Type { get; }

		// Token: 0x1700002C RID: 44
		// (get) Token: 0x060000EF RID: 239 RVA: 0x0000B530 File Offset: 0x00009730
		// (set) Token: 0x060000F0 RID: 240 RVA: 0x0000B538 File Offset: 0x00009738
		public PbType InheritType { get; set; }

		// Token: 0x1700002D RID: 45
		// (get) Token: 0x060000F1 RID: 241 RVA: 0x0000B541 File Offset: 0x00009741
		// (set) Token: 0x060000F2 RID: 242 RVA: 0x0000B549 File Offset: 0x00009749
		public PbObject InheritObject { get; set; }

		// Token: 0x1700002E RID: 46
		// (get) Token: 0x060000F3 RID: 243 RVA: 0x0000B552 File Offset: 0x00009752
		// (set) Token: 0x060000F4 RID: 244 RVA: 0x0000B55A File Offset: 0x0000975A
		public PbType ParentType { get; set; }

		// Token: 0x1700002F RID: 47
		// (get) Token: 0x060000F5 RID: 245 RVA: 0x0000B563 File Offset: 0x00009763
		// (set) Token: 0x060000F6 RID: 246 RVA: 0x0000B56B File Offset: 0x0000976B
		public PbObject ParentObject { get; set; }

		// Token: 0x17000030 RID: 48
		// (get) Token: 0x060000F7 RID: 247 RVA: 0x0000B574 File Offset: 0x00009774
		// (set) Token: 0x060000F8 RID: 248 RVA: 0x0000B57C File Offset: 0x0000977C
		public PbFunction[] Functions { get; set; }

		// Token: 0x17000031 RID: 49
		// (get) Token: 0x060000F9 RID: 249 RVA: 0x0000B585 File Offset: 0x00009785
		// (set) Token: 0x060000FA RID: 250 RVA: 0x0000B58D File Offset: 0x0000978D
		public PbVariable[] Variables { get; set; }

		// Token: 0x17000032 RID: 50
		// (get) Token: 0x060000FB RID: 251 RVA: 0x0000B596 File Offset: 0x00009796
		// (set) Token: 0x060000FC RID: 252 RVA: 0x0000B59E File Offset: 0x0000979E
		public PbReferencedFunction[] ReferencedFunctions { get; set; }

		// Token: 0x17000033 RID: 51
		// (get) Token: 0x060000FD RID: 253 RVA: 0x0000B5A7 File Offset: 0x000097A7
		// (set) Token: 0x060000FE RID: 254 RVA: 0x0000B5AF File Offset: 0x000097AF
		public PbFunctionDefinition[] FunctionDefinitions { get; set; }

		// Token: 0x17000034 RID: 52
		// (get) Token: 0x060000FF RID: 255 RVA: 0x0000B5B8 File Offset: 0x000097B8
		// (set) Token: 0x06000100 RID: 256 RVA: 0x0000B5C0 File Offset: 0x000097C0
		public PbVariable[] AllVariables { get; set; }

		// Token: 0x17000035 RID: 53
		// (get) Token: 0x06000101 RID: 257 RVA: 0x0000B5C9 File Offset: 0x000097C9
		// (set) Token: 0x06000102 RID: 258 RVA: 0x0000B5D1 File Offset: 0x000097D1
		public PbFunctionDefinition[] AllFunctionDefinitions { get; set; }

		// Token: 0x17000036 RID: 54
		// (get) Token: 0x06000103 RID: 259 RVA: 0x0000B5DA File Offset: 0x000097DA
		// (set) Token: 0x06000104 RID: 260 RVA: 0x0000B5E2 File Offset: 0x000097E2
		public PbObject[] Controls { get; set; }

		// Token: 0x06000105 RID: 261 RVA: 0x0000B5EB File Offset: 0x000097EB
		public PbObject(PbEntry entry, ushort index, PbType type)
		{
			this.Entry = entry;
			this.Index = index;
			this.Type = type;
			this.Project = this.Entry.Project;
		}

		// Token: 0x06000106 RID: 262 RVA: 0x0000B61C File Offset: 0x0000981C
		public void ParseInherit()
		{
			if (this._parsedInherit)
			{
				return;
			}
			PbType inheritType = this.InheritType;
			this.InheritObject = ((inheritType != null) ? inheritType.GetObject(this.Entry) : null);
			PbType parentType = this.ParentType;
			this.ParentObject = ((parentType != null) ? parentType.GetObject(this.Entry) : null);
			if (this.InheritObject != null)
			{
				this.InheritObject.ParseInherit();
				int num = Math.Min(this.InheritObject.AllVariables.Length, this.AllVariables.Length);
				for (int i = 0; i < num; i++)
				{
					this.AllVariables[i] = this.InheritObject.AllVariables[i];
				}
				foreach (PbFunctionDefinition pbFunctionDefinition in this.InheritObject.AllFunctionDefinitions)
				{
					if (pbFunctionDefinition != null)
					{
						this.AllFunctionDefinitions[(int)pbFunctionDefinition.GlobalIndex] = pbFunctionDefinition;
					}
				}
			}
			List<PbVariable> list = (from o in this.Variables
			where o.IsInstance
			select o).Reverse<PbVariable>().ToList<PbVariable>();
			for (int k = 0; k < list.Count; k++)
			{
				this.AllVariables[this.AllVariables.Length - 1 - k] = list[k];
			}
			foreach (PbFunctionDefinition pbFunctionDefinition2 in this.FunctionDefinitions)
			{
				this.AllFunctionDefinitions[(int)pbFunctionDefinition2.GlobalIndex] = pbFunctionDefinition2;
			}
			this.Controls = (from o in this.Entry.Objects.Values
			where o.ParentType == this.Type
			select o).ToArray<PbObject>();
			for (int l = 0; l < this.AllVariables.Length; l++)
			{
				PbVariable variable = this.AllVariables[l];
				if (variable != null)
				{
					PbObject pbObject = this.Controls.FirstOrDefault((PbObject o) => o.Type.Name == variable.Name);
					if (pbObject != null && pbObject.Type != variable.Type)
					{
						this.AllVariables[l] = variable.Inherit(pbObject);
					}
				}
			}
			this._parsedInherit = true;
		}

		// Token: 0x06000107 RID: 263 RVA: 0x0000B83E File Offset: 0x00009A3E
		public override string ToString()
		{
			return this.Entry + "/" + this.Type.Name;
		}

		public string GetNameWithParent()
        {
			return this.Type.Name + "->" + (this.ParentObject != null ? this.ParentObject.Type.Name : "");

		}

		// Token: 0x0400004E RID: 78
		private bool _parsedInherit;
	}
}

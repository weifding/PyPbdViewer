using System;

namespace PbdViewer.Uitils.PbClass
{
	// Token: 0x02000012 RID: 18
	public class PbFunction
	{
		// Token: 0x1700000C RID: 12
		// (get) Token: 0x060000B2 RID: 178 RVA: 0x0000B114 File Offset: 0x00009314
		public PbProject Project { get; }

		// Token: 0x1700000D RID: 13
		// (get) Token: 0x060000B3 RID: 179 RVA: 0x0000B11C File Offset: 0x0000931C
		public PbEntry Entry { get; }

		// Token: 0x1700000E RID: 14
		// (get) Token: 0x060000B4 RID: 180 RVA: 0x0000B124 File Offset: 0x00009324
		public PbObject Object { get; }

		// Token: 0x060000B5 RID: 181 RVA: 0x0000B12C File Offset: 0x0000932C
		public PbFunction(PbObject @object)
		{
			this.Object = @object;
			this.Entry = this.Object.Entry;
			this.Project = this.Entry.Project;
		}

		// Token: 0x1700000F RID: 15
		// (get) Token: 0x060000B6 RID: 182 RVA: 0x0000B15D File Offset: 0x0000935D
		// (set) Token: 0x060000B7 RID: 183 RVA: 0x0000B165 File Offset: 0x00009365
		public ushort Index { get; set; }

		// Token: 0x17000010 RID: 16
		// (get) Token: 0x060000B8 RID: 184 RVA: 0x0000B16E File Offset: 0x0000936E
		// (set) Token: 0x060000B9 RID: 185 RVA: 0x0000B176 File Offset: 0x00009376
		public PbFunctionDefinition Definition { get; set; }

		// Token: 0x17000011 RID: 17
		// (get) Token: 0x060000BA RID: 186 RVA: 0x0000B17F File Offset: 0x0000937F
		// (set) Token: 0x060000BB RID: 187 RVA: 0x0000B187 File Offset: 0x00009387
		public byte[] PCodeBytes { get; set; }

		// Token: 0x17000012 RID: 18
		// (get) Token: 0x060000BC RID: 188 RVA: 0x0000B190 File Offset: 0x00009390
		// (set) Token: 0x060000BD RID: 189 RVA: 0x0000B198 File Offset: 0x00009398
		public byte[] DebugBytes { get; set; }

		// Token: 0x17000013 RID: 19
		// (get) Token: 0x060000BE RID: 190 RVA: 0x0000B1A1 File Offset: 0x000093A1
		// (set) Token: 0x060000BF RID: 191 RVA: 0x0000B1A9 File Offset: 0x000093A9
		public byte[] Buffer { get; set; }

		// Token: 0x17000014 RID: 20
		// (get) Token: 0x060000C0 RID: 192 RVA: 0x0000B1B2 File Offset: 0x000093B2
		// (set) Token: 0x060000C1 RID: 193 RVA: 0x0000B1BA File Offset: 0x000093BA
		public PbVariable[] Variables { get; set; }

		// Token: 0x060000C2 RID: 194 RVA: 0x0000B1C3 File Offset: 0x000093C3
		public override string ToString()
		{
			object @object = this.Object;
			object arg = "/";
			PbFunctionDefinition definition = this.Definition;
			return @object.ToString() + arg + (((definition != null) ? definition.Name : null) ?? string.Format("#{0:X4}", this.Index));
		}
	}
}

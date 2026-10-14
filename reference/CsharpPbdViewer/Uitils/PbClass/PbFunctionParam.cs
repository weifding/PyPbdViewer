#define FAKESHARP
using System;

namespace PbdViewer.Uitils.PbClass
{
	// Token: 0x02000014 RID: 20
	public class PbFunctionParam
	{
		// Token: 0x17000023 RID: 35
		// (get) Token: 0x060000DF RID: 223 RVA: 0x0000B455 File Offset: 0x00009655
		// (set) Token: 0x060000E0 RID: 224 RVA: 0x0000B45D File Offset: 0x0000965D
		public bool IsReadOnly { get; set; }

		// Token: 0x17000024 RID: 36
		// (get) Token: 0x060000E1 RID: 225 RVA: 0x0000B466 File Offset: 0x00009666
		// (set) Token: 0x060000E2 RID: 226 RVA: 0x0000B46E File Offset: 0x0000966E
		public bool IsReference { get; set; }

		// Token: 0x17000025 RID: 37
		// (get) Token: 0x060000E3 RID: 227 RVA: 0x0000B477 File Offset: 0x00009677
		// (set) Token: 0x060000E4 RID: 228 RVA: 0x0000B47F File Offset: 0x0000967F
		public PbType Type { get; set; }

		// Token: 0x17000026 RID: 38
		// (get) Token: 0x060000E5 RID: 229 RVA: 0x0000B488 File Offset: 0x00009688
		// (set) Token: 0x060000E6 RID: 230 RVA: 0x0000B490 File Offset: 0x00009690
		public string Name { get; set; }

		// Token: 0x17000027 RID: 39
		// (get) Token: 0x060000E7 RID: 231 RVA: 0x0000B499 File Offset: 0x00009699
		// (set) Token: 0x060000E8 RID: 232 RVA: 0x0000B4A1 File Offset: 0x000096A1
		public string ArrayString { get; set; }

		// Token: 0x060000E9 RID: 233 RVA: 0x0000B4AC File Offset: 0x000096AC
		public override string ToString()
		{
			string str = string.Empty;
			if (this.IsReference)
			{
				str += "ref ";
			}
			if (this.IsReadOnly)
			{
				str += "readonly ";
			}
#if FAKESHARP
			if (string.IsNullOrEmpty(this.ArrayString))
            {
				return str + string.Format("{0} {1}{2}", this.Type.Name, this.Name, this.ArrayString);
			}
			else
            {
				return str + string.Format("PBArray<{0}> {1}", this.Type.Name, this.Name);
			}

#else
			return str + string.Format("{0} {1}{2}", this.Type.Name, this.Name, this.ArrayString);
#endif
		}
	}
}

using System;

namespace PbdViewer.Uitils.PbClass
{
	// Token: 0x0200001E RID: 30
	public enum PbVariableFlag
	{
		// Token: 0x040000AD RID: 173
		IsCustom = 1,
		// Token: 0x040000AE RID: 174
		IsShared,
		// Token: 0x040000AF RID: 175
		UShort = 4,
		// Token: 0x040000B0 RID: 176
		ULong = 8,
		// Token: 0x040000B1 RID: 177
		Invalid = 12,
		// Token: 0x040000B2 RID: 178
		IsBuffer = 16,
		// Token: 0x040000B3 RID: 179
		IsArray = 32,
		// Token: 0x040000B4 RID: 180
		IsPrivate = 64,
		// Token: 0x040000B5 RID: 181
		IsProtected = 128
	}
}

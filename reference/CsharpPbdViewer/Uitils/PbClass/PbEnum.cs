using System;
using System.Collections.Generic;

namespace PbdViewer.Uitils.PbClass
{
	// Token: 0x0200001A RID: 26
	public class PbEnum
	{
		// Token: 0x17000063 RID: 99
		// (get) Token: 0x06000180 RID: 384 RVA: 0x0000E514 File Offset: 0x0000C714
		// (set) Token: 0x06000181 RID: 385 RVA: 0x0000E51C File Offset: 0x0000C71C
		public ushort Index { get; set; }

		// Token: 0x17000064 RID: 100
		// (get) Token: 0x06000182 RID: 386 RVA: 0x0000E525 File Offset: 0x0000C725
		// (set) Token: 0x06000183 RID: 387 RVA: 0x0000E52D File Offset: 0x0000C72D
		public string Name { get; set; }

		// Token: 0x17000065 RID: 101
		// (get) Token: 0x06000184 RID: 388 RVA: 0x0000E536 File Offset: 0x0000C736
		public Dictionary<ushort, string> Items { get; } = new Dictionary<ushort, string>();
	}
}

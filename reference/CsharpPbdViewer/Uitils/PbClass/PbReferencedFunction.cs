using System;

namespace PbdViewer.Uitils.PbClass
{
	// Token: 0x02000016 RID: 22
	public class PbReferencedFunction
	{
		// Token: 0x06000109 RID: 265 RVA: 0x0000B86B File Offset: 0x00009A6B
		public PbReferencedFunction(ushort index, byte[] buffer)
		{
			this.Index = index;
			this._buffer = buffer;
		}

		// Token: 0x17000037 RID: 55
		// (get) Token: 0x0600010A RID: 266 RVA: 0x0000B881 File Offset: 0x00009A81
		// (set) Token: 0x0600010B RID: 267 RVA: 0x0000B889 File Offset: 0x00009A89
		public string Name { get; set; }

		// Token: 0x17000038 RID: 56
		// (get) Token: 0x0600010C RID: 268 RVA: 0x0000B892 File Offset: 0x00009A92
		// (set) Token: 0x0600010D RID: 269 RVA: 0x0000B89A File Offset: 0x00009A9A
		public ushort Index { get; set; }

		// Token: 0x17000039 RID: 57
		// (get) Token: 0x0600010E RID: 270 RVA: 0x0000B8A3 File Offset: 0x00009AA3
		// (set) Token: 0x0600010F RID: 271 RVA: 0x0000B8AB File Offset: 0x00009AAB
		public ushort GlobalIndex { get; set; }

		// Token: 0x1700003A RID: 58
		// (get) Token: 0x06000110 RID: 272 RVA: 0x0000B8B4 File Offset: 0x00009AB4
		// (set) Token: 0x06000111 RID: 273 RVA: 0x0000B8BC File Offset: 0x00009ABC
		public bool IsGlobalFunction { get; set; }

		// Token: 0x06000112 RID: 274 RVA: 0x0000B8C8 File Offset: 0x00009AC8
		public string ToString(bool isDebug)
		{
			string text = this.Name;
			if (isDebug)
			{
				text = string.Format("{0}\t{1:X4}: {2}", BufferHelper.GetHexString(this._buffer), this.GlobalIndex, text);
			}
			return text;
		}

		// Token: 0x0400005E RID: 94
		private readonly byte[] _buffer;
	}
}

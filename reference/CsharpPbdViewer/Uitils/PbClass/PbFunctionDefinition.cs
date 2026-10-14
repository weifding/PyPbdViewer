
#define FAKESHARP
using System;
using System.Linq;

namespace PbdViewer.Uitils.PbClass
{
	// Token: 0x02000013 RID: 19
	public class PbFunctionDefinition
	{
		// Token: 0x17000015 RID: 21
		// (get) Token: 0x060000C3 RID: 195 RVA: 0x0000B200 File Offset: 0x00009400
		// (set) Token: 0x060000C4 RID: 196 RVA: 0x0000B208 File Offset: 0x00009408
		public PbObject Object { get; set; }

		// Token: 0x17000016 RID: 22
		// (get) Token: 0x060000C5 RID: 197 RVA: 0x0000B211 File Offset: 0x00009411
		// (set) Token: 0x060000C6 RID: 198 RVA: 0x0000B219 File Offset: 0x00009419
		public ushort Index { get; set; }

		// Token: 0x17000017 RID: 23
		// (get) Token: 0x060000C7 RID: 199 RVA: 0x0000B222 File Offset: 0x00009422
		// (set) Token: 0x060000C8 RID: 200 RVA: 0x0000B22A File Offset: 0x0000942A
		public ushort GlobalIndex { get; set; }

		// Token: 0x17000018 RID: 24
		// (get) Token: 0x060000C9 RID: 201 RVA: 0x0000B233 File Offset: 0x00009433
		// (set) Token: 0x060000CA RID: 202 RVA: 0x0000B23B File Offset: 0x0000943B
		public ushort RefIndex { get; set; }

		// Token: 0x17000019 RID: 25
		// (get) Token: 0x060000CB RID: 203 RVA: 0x0000B244 File Offset: 0x00009444
		// (set) Token: 0x060000CC RID: 204 RVA: 0x0000B24C File Offset: 0x0000944C
		public ushort EventCode { get; set; }

		// Token: 0x1700001A RID: 26
		// (get) Token: 0x060000CD RID: 205 RVA: 0x0000B255 File Offset: 0x00009455
		public bool IsEvent
		{
			get
			{
				return this.Flag.HasFlag(PbFunctionFlag.IsEvent);
			}
		}

		// Token: 0x1700001B RID: 27
		// (get) Token: 0x060000CE RID: 206 RVA: 0x0000B26D File Offset: 0x0000946D
		public bool IsExternal
		{
			get
			{
				return this.Flag.HasFlag(PbFunctionFlag.IsExternal);
			}
		}

		// Token: 0x1700001C RID: 28
		// (get) Token: 0x060000CF RID: 207 RVA: 0x0000B285 File Offset: 0x00009485
		// (set) Token: 0x060000D0 RID: 208 RVA: 0x0000B28D File Offset: 0x0000948D
		public PbFunctionFlag Flag { get; set; }

		// Token: 0x1700001D RID: 29
		// (get) Token: 0x060000D1 RID: 209 RVA: 0x0000B296 File Offset: 0x00009496
		// (set) Token: 0x060000D2 RID: 210 RVA: 0x0000B29E File Offset: 0x0000949E
		public PbType ReturnType { get; set; }

		// Token: 0x1700001E RID: 30
		// (get) Token: 0x060000D3 RID: 211 RVA: 0x0000B2A7 File Offset: 0x000094A7
		// (set) Token: 0x060000D4 RID: 212 RVA: 0x0000B2AF File Offset: 0x000094AF
		public string Name { get; set; }

		// Token: 0x1700001F RID: 31
		// (get) Token: 0x060000D5 RID: 213 RVA: 0x0000B2B8 File Offset: 0x000094B8
		// (set) Token: 0x060000D6 RID: 214 RVA: 0x0000B2C0 File Offset: 0x000094C0
		public PbFunctionParam[] Params { get; set; }

		// Token: 0x17000020 RID: 32
		// (get) Token: 0x060000D7 RID: 215 RVA: 0x0000B2C9 File Offset: 0x000094C9
		// (set) Token: 0x060000D8 RID: 216 RVA: 0x0000B2D1 File Offset: 0x000094D1
		public string Library { get; set; }

		// Token: 0x17000021 RID: 33
		// (get) Token: 0x060000D9 RID: 217 RVA: 0x0000B2DA File Offset: 0x000094DA
		// (set) Token: 0x060000DA RID: 218 RVA: 0x0000B2E2 File Offset: 0x000094E2
		public string Alias { get; set; }

		// Token: 0x17000022 RID: 34
		// (get) Token: 0x060000DB RID: 219 RVA: 0x0000B2EB File Offset: 0x000094EB
		// (set) Token: 0x060000DC RID: 220 RVA: 0x0000B2F3 File Offset: 0x000094F3
		public PbType ThrowsType { get; set; }

		// Token: 0x060000DD RID: 221 RVA: 0x0000B2FC File Offset: 0x000094FC
		public override string ToString()
		{
			string text = string.Empty;

#if FAKESHARP
			if (this.IsEvent)
			{
				text += "private ";
			}
			else
			{
				if (this.Flag.HasFlag(PbFunctionFlag.IsPrivate))
				{
					text += "private ";
				}
				else if (this.Flag.HasFlag(PbFunctionFlag.IsProtected))
				{
					text += "protected ";
				}
				else
				{
					text += "public ";
				}
				if (this.ReturnType.Index == 0)
				{
					text += " ";
				}
				else
				{
					text += " ";
				}
			}
			if (string.IsNullOrEmpty(this.ReturnType.Name))
			{
				text = text + "void ";
			}
			

			text = text + this.ReturnType.Name + " ";
			text += string.Format("{0}({1})", this.Name, string.Join(",", from o in this.Params
			select o.ToString()));
			if (this.ThrowsType != null)
			{
				text += string.Format(" throws {0}", this.ThrowsType.Name);
			}
			if (this.Library != null)
			{
				text += string.Format(" library \"{0}\" alias for \"{1}\"", this.Library, this.Alias);
			}

#else

			if (this.IsEvent)
			{
				text += "event ";
			}
			else
			{
				if (this.Flag.HasFlag(PbFunctionFlag.IsPrivate))
				{
					text += "private ";
				}
				else if (this.Flag.HasFlag(PbFunctionFlag.IsProtected))
				{
					text += "protected ";
				}
				else
				{
					text += "public ";
				}
				if (this.ReturnType.Index == 0)
				{
					text += "subroutine ";
				}
				else
				{
					text += "function ";
				}
			}
			text = text + this.ReturnType.Name + " ";
			text += string.Format("{0}({1})", this.Name, string.Join(",", from o in this.Params
			select o.ToString()));
			if (this.ThrowsType != null)
			{
				text += string.Format(" throws {0}", this.ThrowsType.Name);
			}
			if (this.Library != null)
			{
				text += string.Format(" library \"{0}\" alias for \"{1}\"", this.Library, this.Alias);
			}
#endif
			return text;

		}
	}
}

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace PbdViewer.Uitils.PbClass
{
	// Token: 0x0200001D RID: 29
	public class PbProject
	{
		// Token: 0x1700006A RID: 106
		// (get) Token: 0x0600018E RID: 398 RVA: 0x0000EB20 File Offset: 0x0000CD20
		public List<PbFile> Files { get; } = new List<PbFile>();

		// Token: 0x1700006B RID: 107
		// (get) Token: 0x0600018F RID: 399 RVA: 0x0000EB28 File Offset: 0x0000CD28
		public Dictionary<string, PbObject> Objects { get; } = new Dictionary<string, PbObject>();

		// Token: 0x1700006C RID: 108
		// (get) Token: 0x06000190 RID: 400 RVA: 0x0000EB30 File Offset: 0x0000CD30
		public Dictionary<ushort, PbType> SystemTypes { get; } = new Dictionary<ushort, PbType>();

		// Token: 0x1700006D RID: 109
		// (get) Token: 0x06000191 RID: 401 RVA: 0x0000EB38 File Offset: 0x0000CD38
		public Dictionary<ushort, PbEnum> Enums { get; } = new Dictionary<ushort, PbEnum>();

		// Token: 0x1700006E RID: 110
		// (get) Token: 0x06000192 RID: 402 RVA: 0x0000EB40 File Offset: 0x0000CD40
		// (set) Token: 0x06000193 RID: 403 RVA: 0x0000EB48 File Offset: 0x0000CD48
		public PbEntry SystemEntry { get; set; }

		// Token: 0x1700006F RID: 111
		// (get) Token: 0x06000194 RID: 404 RVA: 0x0000EB51 File Offset: 0x0000CD51
		// (set) Token: 0x06000195 RID: 405 RVA: 0x0000EB59 File Offset: 0x0000CD59
		public bool IsUnicode { get; set; }

		// Token: 0x17000070 RID: 112
		// (get) Token: 0x06000196 RID: 406 RVA: 0x0000EB62 File Offset: 0x0000CD62
		// (set) Token: 0x06000197 RID: 407 RVA: 0x0000EB6A File Offset: 0x0000CD6A
		public bool IsPb5 { get; set; }

		// Token: 0x17000071 RID: 113
		// (get) Token: 0x06000198 RID: 408 RVA: 0x0000EB73 File Offset: 0x0000CD73
		// (set) Token: 0x06000199 RID: 409 RVA: 0x0000EB7B File Offset: 0x0000CD7B
		public ushort Version { get; set; }

		// Token: 0x0600019A RID: 410 RVA: 0x0000EB84 File Offset: 0x0000CD84
		public PbProject(string filePath)
		{
			this._filePath = filePath;
			this._dir = Path.GetDirectoryName(filePath);
			PbFile item = new PbFile(this, filePath);
			this.Files.Insert(0, item);
			foreach (PbFile pbFile in this.Files)
			{
				foreach (PbEntry pbEntry in pbFile.Entries)
				{
					pbEntry.ParseObject(false);
				}
			}
			PbEntry systemEntry = this.SystemEntry;
			if (systemEntry != null)
			{
				systemEntry.ParseInherit();
			}
			foreach (PbFile pbFile2 in this.Files)
			{
				foreach (PbEntry pbEntry2 in pbFile2.Entries)
				{
					pbEntry2.ParseInherit();
				}
			}
		}

		// Token: 0x0600019B RID: 411 RVA: 0x0000ECF4 File Offset: 0x0000CEF4
		public string GetString(byte[] buffer, int offset, int size)
		{
			if (!this.IsUnicode)
			{
				return Encoding.Default.GetString(buffer, offset, size);
			}
			return Encoding.Unicode.GetString(buffer, offset, size);
		}

		// Token: 0x0600019C RID: 412 RVA: 0x0000ED19 File Offset: 0x0000CF19
		public string GetString(byte[] buffer)
		{
			if (!this.IsUnicode)
			{
				return Encoding.Default.GetString(buffer);
			}
			return Encoding.Unicode.GetString(buffer);
		}

		// Token: 0x0600019D RID: 413 RVA: 0x0000ED3A File Offset: 0x0000CF3A
		public void OnNewLibrary(string libpath, bool isFullPath)
		{
			if (!isFullPath)
			{
				libpath = Path.Combine(this._dir, libpath);
			}
			if (!string.Equals(this._filePath, libpath, StringComparison.OrdinalIgnoreCase) && File.Exists(libpath))
			{
				this.Files.Add(new PbFile(this, libpath));
			}
		}

		// Token: 0x0600019E RID: 414 RVA: 0x0000ED76 File Offset: 0x0000CF76
		public PbFile OnSystemLibrary(ushort version)
		{
			if (this.Version == 0)
			{
				this.Version = version;
				return new PbFile(this, this.Version);
			}
			if (this.Version != version)
			{
				throw new Exception("two version library in one project??");
			}
			return null;
		}

		// Token: 0x0600019F RID: 415 RVA: 0x0000EDA9 File Offset: 0x0000CFA9
		public void OnSystemEntry(PbEntry pbEntry)
		{
			this.SystemEntry = pbEntry;
		}

		// Token: 0x060001A0 RID: 416 RVA: 0x0000EDB2 File Offset: 0x0000CFB2
		public void OnNewSystemType(PbType pbType)
		{
			this.SystemTypes[pbType.Index] = pbType;
		}

		// Token: 0x060001A1 RID: 417 RVA: 0x0000EDC6 File Offset: 0x0000CFC6
		public void OnNewObject(PbObject pbObject, string name = null)
		{
			this.Objects[name ?? pbObject.Type.Name] = pbObject;
		}

		// Token: 0x060001A2 RID: 418 RVA: 0x0000EDE4 File Offset: 0x0000CFE4
		public void OnNewEnumItem(PbType type, ushort index, string itemName)
		{
			if (!this.Enums.ContainsKey(type.Index))
			{
				this.Enums[type.Index] = new PbEnum
				{
					Index = type.Index,
					Name = type.Name
				};
			}
			this.Enums[type.Index].Items[index] = itemName + "!";
		}

		// Token: 0x040000A1 RID: 161
		private readonly string _filePath;

		// Token: 0x040000A2 RID: 162
		private readonly string _dir;

		// Token: 0x040000A3 RID: 163
		public bool IsDebug;

		public string FilePath { get { return this._filePath; } }
	}
}

using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Resources;
using System.Text;

namespace PbdViewer.Uitils.PbClass
{
	// Token: 0x0200001B RID: 27
	public class PbFile
	{
		// Token: 0x17000066 RID: 102
		// (get) Token: 0x06000186 RID: 390 RVA: 0x0000E551 File Offset: 0x0000C751
		public PbProject Project { get; }

		// Token: 0x17000067 RID: 103
		// (get) Token: 0x06000187 RID: 391 RVA: 0x0000E559 File Offset: 0x0000C759
		public string FilePath { get; }

		// Token: 0x17000068 RID: 104
		// (get) Token: 0x06000188 RID: 392 RVA: 0x0000E561 File Offset: 0x0000C761
		public string FileName { get; }

		// Token: 0x17000069 RID: 105
		// (get) Token: 0x06000189 RID: 393 RVA: 0x0000E569 File Offset: 0x0000C769
		public List<PbEntry> Entries { get; } = new List<PbEntry>();

		// Token: 0x0600018A RID: 394 RVA: 0x0000E574 File Offset: 0x0000C774
		public PbFile(PbProject project, string filePath)
		{
			this.Project = project;
			this.FilePath = filePath;
			this.FileName = Path.GetFileName(this.FilePath);
			FileStream fileStream = new FileStream(this.FilePath, FileMode.Open, FileAccess.Read);
			//PEHelper pEHelper = new PEHelper(fileStream);


			foreach (long offset in this.GetNodeList(fileStream))
			{
				long pos = offset;
				byte[] buffer = new byte[32];
				fileStream.Seek(pos, SeekOrigin.Begin);
				fileStream.Read(buffer, 0, 32);
				pos = fileStream.Position;
				ushort @ushort = BufferHelper.GetUShort(buffer, 20L);
				int num = this.Project.IsUnicode ? 2 : 1;
				int num2 = 4 + num * 4;
				int num3 = num2 + 16;
				byte[] array = new byte[num3];
				for (int i = 0; i < (int)@ushort; i++)
				{
					fileStream.Seek(pos, SeekOrigin.Begin);
					fileStream.Read(array, 0, num3);
					if (!Encoding.ASCII.GetString(array, 0, 4).Equals("ENT*") || (!this.Project.GetString(array, 4, num * 4).Equals("0600") && !this.Project.GetString(array, 4, num * 4).Equals("0500")))
					{
						throw new Exception("格式错误");
					}
					uint @uint = BufferHelper.GetUInt(array, (long)num2);
					uint uint2 = BufferHelper.GetUInt(array, (long)(num2 + 4));
					ushort ushort2 = BufferHelper.GetUShort(array, (long)(num2 + 14));
					byte[] buffer2 = new byte[(int)ushort2];
					fileStream.Read(buffer2, 0, (int)ushort2);
					pos = fileStream.Position;
					string entryName = this.Project.GetString(buffer2, 0, (int)ushort2 - num);
					this.Entries.Add(new PbEntry(this, entryName, PbFile.ReadData(fileStream, (long)((ulong)@uint), (long)((ulong)uint2))));
				}
			}
			fileStream.Close();
		}

		// Token: 0x0600018B RID: 395 RVA: 0x0000E770 File Offset: 0x0000C970
		public PbFile(PbProject project, ushort version)
		{
			this.Project = project;
			this.FileName = "system";
			UnmanagedMemoryStream stream = new ResourceManager("PbdViewer.g", base.GetType().Assembly).GetStream(string.Format("Resoures/{0:X4}.bin", version).ToLower());
			if (stream != null)
			{
				byte[] array = new byte[4096];
				GZipStream gzipStream = new GZipStream(stream, CompressionMode.Decompress, true);
				MemoryStream memoryStream = new MemoryStream();
				int num;
				do
				{
					num = gzipStream.Read(array, 0, array.Length);
					memoryStream.Write(array, 0, num);
				}
				while (num > 0);
				gzipStream.Close();
				stream.Close();
				byte[] entryData = memoryStream.ToArray();
				memoryStream.Close();
				this.Entries.Add(new PbEntry(this, "_typedef.grp", entryData));
			}
		}

		// Token: 0x0600018C RID: 396 RVA: 0x0000E83C File Offset: 0x0000CA3C
		private static byte[] ReadData(Stream stream, long start, long size)
		{
			byte[] array = new byte[size];
			int num = 0;
			long offset = start;
			byte[] array2 = new byte[10];
			while ((long)num < size)
			{
				stream.Seek(offset, SeekOrigin.Begin);
				stream.Read(array2, 0, 10);
				if (!Encoding.ASCII.GetString(array2, 0, 4).Equals("DAT*"))
				{
					break;
				}
				ushort @ushort = BufferHelper.GetUShort(array2, 8L);
				stream.Read(array, num, (int)@ushort);
				num += (int)@ushort;
				offset = (long)((ulong)BufferHelper.GetUInt(array2, 4L));
			}
			return array;
		}

		// Token: 0x0600018D RID: 397 RVA: 0x0000E8B8 File Offset: 0x0000CAB8
		private IEnumerable<long> GetNodeList(Stream stream)
		{
			List<long> list = new List<long>();
			byte[] array = new byte[512];
			long num = 0L;
			bool flag = false;
			stream.Seek(0L, SeekOrigin.Begin);
			for (int i = stream.Read(array, 0, 512); i > 0; i = stream.Read(array, 0, 512))
			{
				if (Encoding.ASCII.GetString(array, 0, 4).Equals("HDR*"))
				{
					if (Encoding.ASCII.GetString(array, 4, 12).Equals("PowerBuilder"))
					{
						if (Encoding.ASCII.GetString(array, 18, 4).Equals("0500"))
						{
							this.Project.IsPb5 = true;
							flag = true;
							break;
						}
						if (Encoding.ASCII.GetString(array, 18, 4).Equals("0600"))
						{
							flag = true;
							break;
						}
					}
					if (Encoding.Unicode.GetString(array, 4, 24).Equals("PowerBuilder") && Encoding.Unicode.GetString(array, 32, 8).Equals("0600"))
					{
						flag = true;
						this.Project.IsUnicode = true;
						break;
					}
				}
				num += (long)i;
			}
			if (flag)
			{
				num += (this.Project.IsUnicode ? 1536L : 1024L);
				stream.Seek(num, SeekOrigin.Begin);
				int i = stream.Read(array, 0, 512);
				if (i != 512 || !Encoding.ASCII.GetString(array, 0, 4).Equals("NOD*"))
				{
					throw new Exception("格式错误");
				}
				list.Add(num);
				uint @uint = BufferHelper.GetUInt(array, 4L);
				uint uint2 = BufferHelper.GetUInt(array, 12L);
				while (@uint > 0U)
				{
					stream.Seek((long)((ulong)@uint), SeekOrigin.Begin);
					i = stream.Read(array, 0, 512);
					if (i != 512 || !Encoding.ASCII.GetString(array, 0, 4).Equals("NOD*"))
					{
						throw new Exception("格式错误");
					}
					list.Add((long)((ulong)@uint));
					@uint = BufferHelper.GetUInt(array, 4L);
				}
				while (uint2 > 0U)
				{
					stream.Seek((long)((ulong)uint2), SeekOrigin.Begin);
					i = stream.Read(array, 0, 512);
					if (i != 512 || !Encoding.ASCII.GetString(array, 0, 4).Equals("NOD*"))
					{
						throw new Exception("格式错误");
					}
					list.Add((long)((ulong)uint2));
					uint2 = BufferHelper.GetUInt(array, 12L);
				}
			}
			return list;
		}
	}
}

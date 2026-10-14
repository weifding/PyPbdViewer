using System;
using System.Collections;
using System.Data;
using System.IO;
using System.Text;

namespace PbdViewer.Uitils
{
	// Token: 0x0200000C RID: 12
	public class PEHelper
	{
		// Token: 0x17000006 RID: 6
		// (get) Token: 0x0600003D RID: 61 RVA: 0x00004840 File Offset: 0x00002A40
		public bool OpenFile
		{
			get
			{
				return this._OpenFile;
			}
		}

		// Token: 0x0600003E RID: 62 RVA: 0x00004848 File Offset: 0x00002A48
		public PEHelper(Stream stream)
		{
			this._OpenFile = false;
			this.PEFileByte = new byte[stream.Length];
			long position = stream.Position;
			stream.Seek(0L, SeekOrigin.Begin);
			stream.Read(this.PEFileByte, 0, this.PEFileByte.Length);
			stream.Seek(position, SeekOrigin.Begin);
			this.LoadFile();
			this._OpenFile = true;
		}

		// Token: 0x0600003F RID: 63 RVA: 0x000048B4 File Offset: 0x00002AB4
		public PEHelper(string FileName)
		{
			this._OpenFile = false;
			FileStream fileStream = new FileStream(FileName, FileMode.Open);
			this.PEFileByte = new byte[fileStream.Length];
			fileStream.Read(this.PEFileByte, 0, this.PEFileByte.Length);
			fileStream.Close();
			this.LoadFile();
			this._OpenFile = true;
		}

		// Token: 0x06000040 RID: 64 RVA: 0x00004914 File Offset: 0x00002B14
		public uint GetOffset(uint offset)
		{
			foreach (object obj in this._SectionTable.Section)
			{
				PEHelper.SectionTable.SectionData sectionData = (PEHelper.SectionTable.SectionData)obj;
				uint @uint = BufferHelper.GetUInt(sectionData.VirtualAddress, 0L);
				uint num = BufferHelper.GetUInt(sectionData.SizeOfRawDataRVA, 0L) + BufferHelper.GetUInt(this._OptionalHeader.ImageFileCode, 0L);
				if (offset >= num && offset <= num + @uint)
				{
					return BufferHelper.GetUInt(sectionData.PointerToRawData, 0L) + (offset - num);
				}
			}
			return uint.MaxValue;
		}

		// Token: 0x06000041 RID: 65 RVA: 0x000049C0 File Offset: 0x00002BC0
		private void LoadFile()
		{
			this.LoadDosHeader();
			this.LoadDosStub();
			this.LoadPEHeader();
			this.LoadOptionalHeader();
			this.LoadOptionalDirAttrib();
			this.LoadSectionTable();
			this.LoadExportDirectory();
			this.LoadImportDirectory();
			this.LoadResourceDirectory();
		}

		// Token: 0x06000042 RID: 66 RVA: 0x000049F8 File Offset: 0x00002BF8
		private void LoadDosHeader()
		{
			this._DosHeader = new PEHelper.DosHeader();
			this._DosHeader.FileStarIndex = this.PEFileIndex;
			this.Loadbyte(ref this._DosHeader.e_magic);
			this.Loadbyte(ref this._DosHeader.e_cblp);
			this.Loadbyte(ref this._DosHeader.e_cp);
			this.Loadbyte(ref this._DosHeader.e_crlc);
			this.Loadbyte(ref this._DosHeader.e_cparhdr);
			this.Loadbyte(ref this._DosHeader.e_minalloc);
			this.Loadbyte(ref this._DosHeader.e_maxalloc);
			this.Loadbyte(ref this._DosHeader.e_ss);
			this.Loadbyte(ref this._DosHeader.e_sp);
			this.Loadbyte(ref this._DosHeader.e_csum);
			this.Loadbyte(ref this._DosHeader.e_ip);
			this.Loadbyte(ref this._DosHeader.e_cs);
			this.Loadbyte(ref this._DosHeader.e_rva);
			this.Loadbyte(ref this._DosHeader.e_fg);
			this.Loadbyte(ref this._DosHeader.e_bl1);
			this.Loadbyte(ref this._DosHeader.e_oemid);
			this.Loadbyte(ref this._DosHeader.e_oeminfo);
			this.Loadbyte(ref this._DosHeader.e_bl2);
			this.Loadbyte(ref this._DosHeader.e_PESTAR);
			this._DosHeader.FileEndIndex = this.PEFileIndex;
		}

		// Token: 0x06000043 RID: 67 RVA: 0x00004B78 File Offset: 0x00002D78
		private void LoadDosStub()
		{
			long size = this.GetLong(this._DosHeader.e_PESTAR) - this.PEFileIndex;
			this._DosStub = new PEHelper.DosStub(size);
			this._DosStub.FileStarIndex = this.PEFileIndex;
			this.Loadbyte(ref this._DosStub.DosStubData);
			this._DosStub.FileEndIndex = this.PEFileIndex;
		}

		// Token: 0x06000044 RID: 68 RVA: 0x00004BE0 File Offset: 0x00002DE0
		private void LoadPEHeader()
		{
			this._PEHeader = new PEHelper.PEHeader();
			this._PEHeader.FileStarIndex = this.PEFileIndex;
			this.Loadbyte(ref this._PEHeader.Header);
			this.Loadbyte(ref this._PEHeader.Machine);
			this.Loadbyte(ref this._PEHeader.NumberOfSections);
			this.Loadbyte(ref this._PEHeader.TimeDateStamp);
			this.Loadbyte(ref this._PEHeader.PointerToSymbolTable);
			this.Loadbyte(ref this._PEHeader.NumberOfSymbols);
			this.Loadbyte(ref this._PEHeader.SizeOfOptionalHeader);
			this.Loadbyte(ref this._PEHeader.Characteristics);
			this._PEHeader.FileEndIndex = this.PEFileIndex;
		}

		// Token: 0x06000045 RID: 69 RVA: 0x00004CA4 File Offset: 0x00002EA4
		private void LoadOptionalHeader()
		{
			this._OptionalHeader = new PEHelper.OptionalHeader();
			this._OptionalHeader.FileStarIndex = this.PEFileIndex;
			this.Loadbyte(ref this._OptionalHeader.Magic);
			this.Loadbyte(ref this._OptionalHeader.MajorLinkerVersion);
			this.Loadbyte(ref this._OptionalHeader.MinorLinkerVersion);
			this.Loadbyte(ref this._OptionalHeader.SizeOfCode);
			this.Loadbyte(ref this._OptionalHeader.SizeOfInitializedData);
			this.Loadbyte(ref this._OptionalHeader.SizeOfUninitializedData);
			this.Loadbyte(ref this._OptionalHeader.AddressOfEntryPoint);
			this.Loadbyte(ref this._OptionalHeader.BaseOfCode);
			this.Loadbyte(ref this._OptionalHeader.ImageBase);
			this.Loadbyte(ref this._OptionalHeader.ImageFileCode);
			this.Loadbyte(ref this._OptionalHeader.SectionAlign);
			this.Loadbyte(ref this._OptionalHeader.FileAlign);
			this.Loadbyte(ref this._OptionalHeader.MajorOSV);
			this.Loadbyte(ref this._OptionalHeader.MinorOSV);
			this.Loadbyte(ref this._OptionalHeader.MajorImageVer);
			this.Loadbyte(ref this._OptionalHeader.MinorImageVer);
			this.Loadbyte(ref this._OptionalHeader.MajorSV);
			this.Loadbyte(ref this._OptionalHeader.MinorSV);
			this.Loadbyte(ref this._OptionalHeader.UNKNOW);
			this.Loadbyte(ref this._OptionalHeader.SizeOfImage);
			this.Loadbyte(ref this._OptionalHeader.SizeOfHeards);
			this.Loadbyte(ref this._OptionalHeader.CheckSum);
			this.Loadbyte(ref this._OptionalHeader.Subsystem);
			this.Loadbyte(ref this._OptionalHeader.DLL_Characteristics);
			this.Loadbyte(ref this._OptionalHeader.Bsize);
			this.Loadbyte(ref this._OptionalHeader.TimeBsize);
			this.Loadbyte(ref this._OptionalHeader.AucBsize);
			this.Loadbyte(ref this._OptionalHeader.SizeOfBsize);
			this.Loadbyte(ref this._OptionalHeader.FuckBsize);
			this.Loadbyte(ref this._OptionalHeader.DirectCount);
			this._OptionalHeader.FileEndIndex = this.PEFileIndex;
		}

		// Token: 0x06000046 RID: 70 RVA: 0x00004EDC File Offset: 0x000030DC
		private void LoadOptionalDirAttrib()
		{
			this._OptionalDirAttrib = new PEHelper.OptionalDirAttrib();
			this._OptionalDirAttrib.FileStarIndex = this.PEFileIndex;
			long @long = this.GetLong(this._OptionalHeader.DirectCount);
			int num = 0;
			while ((long)num != @long)
			{
				PEHelper.OptionalDirAttrib.DirAttrib dirAttrib = new PEHelper.OptionalDirAttrib.DirAttrib();
				this.Loadbyte(ref dirAttrib.DirRva);
				this.Loadbyte(ref dirAttrib.DirSize);
				this._OptionalDirAttrib.DirByte.Add(dirAttrib);
				num++;
			}
			this._OptionalDirAttrib.FileEndIndex = this.PEFileIndex;
		}

		// Token: 0x06000047 RID: 71 RVA: 0x00004F68 File Offset: 0x00003168
		private void LoadSectionTable()
		{
			this._SectionTable = new PEHelper.SectionTable();
			long @long = this.GetLong(this._PEHeader.NumberOfSections);
			this._SectionTable.FileStarIndex = this.PEFileIndex;
			for (long num = 0L; num != @long; num += 1L)
			{
				PEHelper.SectionTable.SectionData sectionData = new PEHelper.SectionTable.SectionData();
				this.Loadbyte(ref sectionData.SectName);
				this.Loadbyte(ref sectionData.VirtualAddress);
				this.Loadbyte(ref sectionData.SizeOfRawDataRVA);
				this.Loadbyte(ref sectionData.SizeOfRawDataSize);
				this.Loadbyte(ref sectionData.PointerToRawData);
				this.Loadbyte(ref sectionData.PointerToRelocations);
				this.Loadbyte(ref sectionData.PointerToLinenumbers);
				this.Loadbyte(ref sectionData.NumberOfRelocations);
				this.Loadbyte(ref sectionData.NumberOfLinenumbers);
				this.Loadbyte(ref sectionData.Characteristics);
				this._SectionTable.Section.Add(sectionData);
			}
			this._SectionTable.FileEndIndex = this.PEFileIndex;
		}

		// Token: 0x06000048 RID: 72 RVA: 0x00005058 File Offset: 0x00003258
		private void LoadExportDirectory()
		{
			if (this._OptionalDirAttrib.DirByte.Count == 0)
			{
				return;
			}
			PEHelper.OptionalDirAttrib.DirAttrib dirAttrib = (PEHelper.OptionalDirAttrib.DirAttrib)this._OptionalDirAttrib.DirByte[0];
			if (this.GetLong(dirAttrib.DirRva) == 0L)
			{
				return;
			}
			long @long = this.GetLong(dirAttrib.DirRva);
			this._ExportDirectory = new PEHelper.ExportDirectory();
			int num = 0;
			while (num != this._SectionTable.Section.Count)
			{
				PEHelper.SectionTable.SectionData sectionData = (PEHelper.SectionTable.SectionData)this._SectionTable.Section[num];
				long long2 = this.GetLong(sectionData.SizeOfRawDataRVA);
				long long3 = this.GetLong(sectionData.SizeOfRawDataSize);
				if (@long >= long2 && @long < long2 + long3)
				{
					this.PEFileIndex = @long - this.GetLong(sectionData.SizeOfRawDataRVA) + this.GetLong(sectionData.PointerToRawData);
					this._ExportDirectory.FileStarIndex = this.PEFileIndex;
					this._ExportDirectory.FileEndIndex = this.PEFileIndex + this.GetLong(dirAttrib.DirSize);
					this.Loadbyte(ref this._ExportDirectory.Characteristics);
					this.Loadbyte(ref this._ExportDirectory.TimeDateStamp);
					this.Loadbyte(ref this._ExportDirectory.MajorVersion);
					this.Loadbyte(ref this._ExportDirectory.MinorVersion);
					this.Loadbyte(ref this._ExportDirectory.Name);
					this.Loadbyte(ref this._ExportDirectory.Base);
					this.Loadbyte(ref this._ExportDirectory.NumberOfFunctions);
					this.Loadbyte(ref this._ExportDirectory.NumberOfNames);
					this.Loadbyte(ref this._ExportDirectory.AddressOfFunctions);
					this.Loadbyte(ref this._ExportDirectory.AddressOfNames);
					this.Loadbyte(ref this._ExportDirectory.AddressOfNameOrdinals);
					this.PEFileIndex = this.GetLong(this._ExportDirectory.AddressOfFunctions) - this.GetLong(sectionData.SizeOfRawDataRVA) + this.GetLong(sectionData.PointerToRawData);
					long num2 = this.GetLong(this._ExportDirectory.AddressOfNames) - this.GetLong(sectionData.SizeOfRawDataRVA) + this.GetLong(sectionData.PointerToRawData);
					long num3 = (num2 - this.PEFileIndex) / 4L;
					for (long num4 = 0L; num4 != num3; num4 += 1L)
					{
						byte[] value = new byte[4];
						this.Loadbyte(ref value);
						this._ExportDirectory.AddressOfFunctionsList.Add(value);
					}
					this.PEFileIndex = num2;
					num2 = this.GetLong(this._ExportDirectory.AddressOfNameOrdinals) - this.GetLong(sectionData.SizeOfRawDataRVA) + this.GetLong(sectionData.PointerToRawData);
					num3 = (num2 - this.PEFileIndex) / 4L;
					for (long num5 = 0L; num5 != num3; num5 += 1L)
					{
						byte[] value2 = new byte[4];
						this.Loadbyte(ref value2);
						this._ExportDirectory.AddressOfNamesList.Add(value2);
					}
					this.PEFileIndex = num2;
					num2 = this.GetLong(this._ExportDirectory.Name) - this.GetLong(sectionData.SizeOfRawDataRVA) + this.GetLong(sectionData.PointerToRawData);
					num3 = (num2 - this.PEFileIndex) / 2L;
					for (long num6 = 0L; num6 != num3; num6 += 1L)
					{
						byte[] value3 = new byte[2];
						this.Loadbyte(ref value3);
						this._ExportDirectory.AddressOfNameOrdinalsList.Add(value3);
					}
					this.PEFileIndex = num2;
					long num7 = 0L;
					for (;;)
					{
						if (this.PEFileByte[(int)(checked((IntPtr)(unchecked(this.PEFileIndex + num7))))] == 0)
						{
							if (this.PEFileByte[(int)(checked((IntPtr)(unchecked(this.PEFileIndex + num7 + 1L))))] == 0)
							{
								return;
							}
							byte[] value4 = new byte[num7];
							this.Loadbyte(ref value4);
							this._ExportDirectory.NameList.Add(value4);
							this.PEFileIndex += 1L;
							num7 = 0L;
						}
						num7 += 1L;
					}
				}
				else
				{
					num++;
				}
			}
		}

		// Token: 0x06000049 RID: 73 RVA: 0x0000543C File Offset: 0x0000363C
		private void LoadImportDirectory()
		{
			if (this._OptionalDirAttrib.DirByte.Count < 1)
			{
				return;
			}
			PEHelper.OptionalDirAttrib.DirAttrib dirAttrib = (PEHelper.OptionalDirAttrib.DirAttrib)this._OptionalDirAttrib.DirByte[1];
			long @long = this.GetLong(dirAttrib.DirRva);
			if (@long == 0L)
			{
				return;
			}
			long long2 = this.GetLong(dirAttrib.DirSize);
			this._ImportDirectory = new PEHelper.ImportDirectory();
			long num = 0L;
			long num2 = 0L;
			long num3 = 0L;
			long num4 = 0L;
			for (int num5 = 0; num5 != this._SectionTable.Section.Count; num5++)
			{
				PEHelper.SectionTable.SectionData sectionData = (PEHelper.SectionTable.SectionData)this._SectionTable.Section[num5];
				num3 = this.GetLong(sectionData.SizeOfRawDataRVA);
				num4 = this.GetLong(sectionData.SizeOfRawDataSize);
				if (@long >= num3 && @long < num3 + num4)
				{
					num = this.GetLong(sectionData.SizeOfRawDataRVA);
					num2 = this.GetLong(sectionData.PointerToRawData);
					this.PEFileIndex = @long - num + num2;
					this._ImportDirectory.FileStarIndex = this.PEFileIndex;
					this._ImportDirectory.FileEndIndex = this.PEFileIndex + long2;
					break;
				}
			}
			if (num == 0L && num2 == 0L)
			{
				return;
			}
			for (;;)
			{
				PEHelper.ImportDirectory.ImportDate importDate = new PEHelper.ImportDirectory.ImportDate();
				this.Loadbyte(ref importDate.OriginalFirstThunk);
				this.Loadbyte(ref importDate.TimeDateStamp);
				this.Loadbyte(ref importDate.ForwarderChain);
				this.Loadbyte(ref importDate.Name);
				this.Loadbyte(ref importDate.FirstThunk);
				if (this.GetLong(importDate.Name) == 0L)
				{
					break;
				}
				this._ImportDirectory.ImportList.Add(importDate);
			}
			for (int num6 = 0; num6 != this._ImportDirectory.ImportList.Count; num6++)
			{
				PEHelper.ImportDirectory.ImportDate importDate2 = (PEHelper.ImportDirectory.ImportDate)this._ImportDirectory.ImportList[num6];
				long pefileIndex = this.GetLong(importDate2.Name) - num + num2;
				this.PEFileIndex = pefileIndex;
				long num7 = 0L;
				while (this.PEFileByte[(int)(checked((IntPtr)(unchecked(this.PEFileIndex + num7))))] != 0)
				{
					num7 += 1L;
				}
				importDate2.DLLName = new byte[num7];
				this.Loadbyte(ref importDate2.DLLName);
			}
			for (int num8 = 0; num8 != this._ImportDirectory.ImportList.Count; num8++)
			{
				PEHelper.ImportDirectory.ImportDate importDate3 = (PEHelper.ImportDirectory.ImportDate)this._ImportDirectory.ImportList[num8];
				long pefileIndex2 = this.GetLong(importDate3.OriginalFirstThunk) - num + num2;
				this.PEFileIndex = pefileIndex2;
				for (;;)
				{
					PEHelper.ImportDirectory.ImportDate.FunctionList functionList = new PEHelper.ImportDirectory.ImportDate.FunctionList();
					this.Loadbyte(ref functionList.OriginalFirst);
					long long3 = this.GetLong(functionList.OriginalFirst);
					if (long3 == 0L)
					{
						break;
					}
					long pefileIndex3 = this.PEFileIndex;
					this.PEFileIndex = long3 - num + num2;
					if (long3 >= num3 && long3 < num3 + num4)
					{
						int num9 = 0;
						for (;;)
						{
							if (num9 == 0)
							{
								this.Loadbyte(ref functionList.FunctionHead);
							}
							if (this.PEFileByte[(int)(checked((IntPtr)(unchecked(this.PEFileIndex + (long)num9))))] == 0)
							{
								break;
							}
							num9++;
						}
						byte[] functionName = new byte[num9];
						this.Loadbyte(ref functionName);
						functionList.FunctionName = functionName;
					}
					else
					{
						functionList.FunctionName = new byte[1];
					}
					this.PEFileIndex = pefileIndex3;
					importDate3.DllFunctionList.Add(functionList);
				}
			}
		}

		// Token: 0x0600004A RID: 74 RVA: 0x0000578C File Offset: 0x0000398C
		private void LoadResourceDirectory()
		{
			if (this._OptionalDirAttrib.DirByte.Count < 3)
			{
				return;
			}
			PEHelper.OptionalDirAttrib.DirAttrib dirAttrib = (PEHelper.OptionalDirAttrib.DirAttrib)this._OptionalDirAttrib.DirByte[2];
			long @long = this.GetLong(dirAttrib.DirRva);
			if (@long == 0L)
			{
				return;
			}
			long long2 = this.GetLong(dirAttrib.DirSize);
			this._ResourceDirectory = new PEHelper.ResourceDirectory();
			long num = 0L;
			long num2 = 0L;
			long num3 = 0L;
			long peindex = 0L;
			for (int num4 = 0; num4 != this._SectionTable.Section.Count; num4++)
			{
				PEHelper.SectionTable.SectionData sectionData = (PEHelper.SectionTable.SectionData)this._SectionTable.Section[num4];
				num3 = this.GetLong(sectionData.SizeOfRawDataRVA);
				long long3 = this.GetLong(sectionData.SizeOfRawDataSize);
				if (@long >= num3 && @long < num3 + long3)
				{
					num = this.GetLong(sectionData.SizeOfRawDataRVA);
					num2 = this.GetLong(sectionData.PointerToRawData);
					this.PEFileIndex = @long - num + num2;
					peindex = this.PEFileIndex;
					this._ResourceDirectory.FileStarIndex = this.PEFileIndex;
					this._ResourceDirectory.FileEndIndex = this.PEFileIndex + long2;
					break;
				}
			}
			if (num == 0L && num2 == 0L)
			{
				return;
			}
			this.AddResourceNode(this._ResourceDirectory, peindex, 0L, num3);
		}

		// Token: 0x0600004B RID: 75 RVA: 0x000058DC File Offset: 0x00003ADC
		private void AddResourceNode(PEHelper.ResourceDirectory Node, long PEIndex, long RVA, long ResourSectRva)
		{
			this.PEFileIndex = PEIndex + RVA;
			this.Loadbyte(ref Node.Characteristics);
			this.Loadbyte(ref Node.TimeDateStamp);
			this.Loadbyte(ref Node.MajorVersion);
			this.Loadbyte(ref Node.MinorVersion);
			this.Loadbyte(ref Node.NumberOfNamedEntries);
			this.Loadbyte(ref Node.NumberOfIdEntries);
			long @long = this.GetLong(Node.NumberOfNamedEntries);
			int num = 0;
			while ((long)num != @long)
			{
				PEHelper.ResourceDirectory.DirectoryEntry directoryEntry = new PEHelper.ResourceDirectory.DirectoryEntry();
				this.Loadbyte(ref directoryEntry.Name);
				this.Loadbyte(ref directoryEntry.Id);
				byte[] array = new byte[]
				{
					directoryEntry.Name[0],
					directoryEntry.Name[1]
				};
				long num2 = this.GetLong(array) + PEIndex;
				long long2;
				checked
				{
					array[0] = this.PEFileByte[(int)((IntPtr)num2)];
					array[1] = this.PEFileByte[(int)((IntPtr)(unchecked(num2 + 1L)))];
					long2 = this.GetLong(array);
				}
				Node.Name = new byte[long2 * 2L];
				for (int num3 = 0; num3 != Node.Name.Length; num3++)
				{
					Node.Name[num3] = this.PEFileByte[(int)(checked((IntPtr)(unchecked(num2 + 2L + (long)num3))))];
				}
				array[0] = directoryEntry.Id[2];
				array[1] = directoryEntry.Id[3];
				long pefileIndex = this.PEFileIndex;
				if (this.GetLong(array) == 0L)
				{
					array[0] = directoryEntry.Id[0];
					array[1] = directoryEntry.Id[1];
					this.PEFileIndex = this.GetLong(array) + PEIndex;
					PEHelper.ResourceDirectory.DirectoryEntry.DataEntry dataEntry = new PEHelper.ResourceDirectory.DirectoryEntry.DataEntry();
					this.Loadbyte(ref dataEntry.ResourRVA);
					this.Loadbyte(ref dataEntry.ResourSize);
					this.Loadbyte(ref dataEntry.ResourTest);
					this.Loadbyte(ref dataEntry.ResourWen);
					this.PEFileIndex = pefileIndex;
					directoryEntry.DataEntryList.Add(dataEntry);
				}
				else
				{
					array[0] = directoryEntry.Id[0];
					array[1] = directoryEntry.Id[1];
					PEHelper.ResourceDirectory resourceDirectory = new PEHelper.ResourceDirectory();
					directoryEntry.NodeDirectoryList.Add(resourceDirectory);
					this.AddResourceNode(resourceDirectory, PEIndex, this.GetLong(array), ResourSectRva);
				}
				this.PEFileIndex = pefileIndex;
				Node.EntryList.Add(directoryEntry);
				num++;
			}
			long long3 = this.GetLong(Node.NumberOfIdEntries);
			int num4 = 0;
			while ((long)num4 != long3)
			{
				PEHelper.ResourceDirectory.DirectoryEntry directoryEntry2 = new PEHelper.ResourceDirectory.DirectoryEntry();
				this.Loadbyte(ref directoryEntry2.Name);
				this.Loadbyte(ref directoryEntry2.Id);
				byte[] array2 = new byte[]
				{
					directoryEntry2.Id[2],
					directoryEntry2.Id[3]
				};
				long pefileIndex2 = this.PEFileIndex;
				if (this.GetLong(array2) == 0L)
				{
					array2[0] = directoryEntry2.Id[0];
					array2[1] = directoryEntry2.Id[1];
					this.PEFileIndex = this.GetLong(array2) + PEIndex;
					PEHelper.ResourceDirectory.DirectoryEntry.DataEntry dataEntry2 = new PEHelper.ResourceDirectory.DirectoryEntry.DataEntry();
					this.Loadbyte(ref dataEntry2.ResourRVA);
					this.Loadbyte(ref dataEntry2.ResourSize);
					this.Loadbyte(ref dataEntry2.ResourTest);
					this.Loadbyte(ref dataEntry2.ResourWen);
					long num5 = this.GetLong(dataEntry2.ResourRVA) - ResourSectRva + PEIndex;
					dataEntry2.FileStarIndex = num5;
					dataEntry2.FileEndIndex = num5 + this.GetLong(dataEntry2.ResourSize);
					this.PEFileIndex = pefileIndex2;
					directoryEntry2.DataEntryList.Add(dataEntry2);
				}
				else
				{
					array2[0] = directoryEntry2.Id[0];
					array2[1] = directoryEntry2.Id[1];
					PEHelper.ResourceDirectory resourceDirectory2 = new PEHelper.ResourceDirectory();
					directoryEntry2.NodeDirectoryList.Add(resourceDirectory2);
					this.AddResourceNode(resourceDirectory2, PEIndex, this.GetLong(array2), ResourSectRva);
				}
				this.PEFileIndex = pefileIndex2;
				Node.EntryList.Add(directoryEntry2);
				num4++;
			}
		}

		// Token: 0x0600004C RID: 76 RVA: 0x00005C90 File Offset: 0x00003E90
		private void Loadbyte(ref byte[] Data)
		{
			for (int num = 0; num != Data.Length; num++)
			{
				Data[num] = this.PEFileByte[(int)(checked((IntPtr)this.PEFileIndex))];
				this.PEFileIndex += 1L;
			}
		}

		// Token: 0x0600004D RID: 77 RVA: 0x00005CD0 File Offset: 0x00003ED0
		private string GetString(byte[] Data)
		{
			string str = "";
			for (int num = 0; num != Data.Length - 1; num++)
			{
				str = str + Data[num].ToString("X02") + " ";
			}
			return str + Data[Data.Length - 1].ToString("X02");
		}

		// Token: 0x0600004E RID: 78 RVA: 0x00005D30 File Offset: 0x00003F30
		private string GetString(byte[] Data, string Type)
		{
			if (Type.Trim().ToUpper() == "ASCII")
			{
				return Encoding.ASCII.GetString(Data);
			}
			if (Type.Trim().ToUpper() == "DEFAULT")
			{
				return Encoding.Default.GetString(Data);
			}
			if (Type.Trim().ToUpper() == "UNICODE")
			{
				return Encoding.Unicode.GetString(Data);
			}
			if (Type.Trim().ToUpper() == "BYTE")
			{
				string str = "";
				for (int num = Data.Length - 1; num != 0; num--)
				{
					str = str + Data[num].ToString("X02") + " ";
				}
				return str + Data[0].ToString("X02");
			}
			return this.GetInt(Data);
		}

		// Token: 0x0600004F RID: 79 RVA: 0x00005E10 File Offset: 0x00004010
		private string GetInt(byte[] Data)
		{
			string str = "";
			for (int num = 0; num != Data.Length - 1; num++)
			{
				int num2 = (int)Data[num];
				str = str + num2.ToString() + " ";
			}
			int num3 = (int)Data[Data.Length - 1];
			return str + num3.ToString();
		}

		// Token: 0x06000050 RID: 80 RVA: 0x00005E64 File Offset: 0x00004064
		private long GetLong(byte[] Data)
		{
			string text = "";
			if (Data.Length <= 4)
			{
				for (int num = Data.Length - 1; num != -1; num--)
				{
					text += Data[num].ToString("X02");
				}
				return Convert.ToInt64(text, 16);
			}
			return 0L;
		}

		// Token: 0x06000051 RID: 81 RVA: 0x00005EB4 File Offset: 0x000040B4
		private void AddTableRow(DataTable RefTable, byte[] Data, string Name, string Describe)
		{
			RefTable.Rows.Add(new string[]
			{
				Name,
				Data.Length.ToString(),
				this.GetString(Data),
				this.GetLong(Data).ToString(),
				this.GetString(Data, "ASCII"),
				Describe
			});
		}

		// Token: 0x06000052 RID: 82 RVA: 0x00005F18 File Offset: 0x00004118
		public DataSet GetPETable()
		{
			if (!this._OpenFile)
			{
				return null;
			}
			DataSet dataSet = new DataSet("PEFile");
			if (this._DosHeader != null)
			{
				dataSet.Tables.Add(this.TableDosHeader());
			}
			if (this._PEHeader != null)
			{
				dataSet.Tables.Add(this.TablePEHeader());
			}
			if (this._OptionalHeader != null)
			{
				dataSet.Tables.Add(this.TableOptionalHeader());
			}
			if (this._OptionalDirAttrib != null)
			{
				dataSet.Tables.Add(this.TableOptionalDirAttrib());
			}
			if (this._SectionTable != null)
			{
				dataSet.Tables.Add(this.TableSectionData());
			}
			if (this._ExportDirectory != null)
			{
				dataSet.Tables.Add(this.TableExportDirectory());
				dataSet.Tables.Add(this.TableExportFunction());
			}
			if (this._ImportDirectory != null)
			{
				dataSet.Tables.Add(this.TableImportDirectory());
				dataSet.Tables.Add(this.TableImportFunction());
			}
			if (this._ResourceDirectory != null)
			{
				dataSet.Tables.Add(this.TableResourceDirectory());
			}
			return dataSet;
		}

		// Token: 0x06000053 RID: 83 RVA: 0x00006028 File Offset: 0x00004228
		private DataTable TableDosHeader()
		{
			DataTable dataTable = new DataTable(string.Concat(new string[]
			{
				"DosHeader FileStar{",
				this._DosHeader.FileStarIndex.ToString(),
				"}FileEnd{",
				this._DosHeader.FileEndIndex.ToString(),
				"}"
			}));
			dataTable.Columns.Add("Name");
			dataTable.Columns.Add("Size");
			dataTable.Columns.Add("Value16");
			dataTable.Columns.Add("Value10");
			dataTable.Columns.Add("ASCII");
			dataTable.Columns.Add("Describe");
			this.AddTableRow(dataTable, this._DosHeader.e_magic, "e_magic", "魔术数字");
			this.AddTableRow(dataTable, this._DosHeader.e_cblp, "e_cblp", "文件最后页的字节数");
			this.AddTableRow(dataTable, this._DosHeader.e_cp, "e_cp", "文件页数");
			this.AddTableRow(dataTable, this._DosHeader.e_crlc, "e_crlc", "重定义元素个数");
			this.AddTableRow(dataTable, this._DosHeader.e_cparhdr, "e_cparhdr", "头部尺寸，以段落为单位");
			this.AddTableRow(dataTable, this._DosHeader.e_minalloc, "e_minalloc", "所需的最小附加段");
			this.AddTableRow(dataTable, this._DosHeader.e_maxalloc, "e_maxalloc", "所需的最大附加段");
			this.AddTableRow(dataTable, this._DosHeader.e_ss, "e_ss", "初始的SS值（相对偏移量）");
			this.AddTableRow(dataTable, this._DosHeader.e_sp, "e_sp", "初始的SP值");
			this.AddTableRow(dataTable, this._DosHeader.e_csum, "e_csum", "校验和");
			this.AddTableRow(dataTable, this._DosHeader.e_ip, "e_ip", "初始的IP值");
			this.AddTableRow(dataTable, this._DosHeader.e_cs, "e_cs", "初始的CS值（相对偏移量）");
			this.AddTableRow(dataTable, this._DosHeader.e_rva, "e_rva", "");
			this.AddTableRow(dataTable, this._DosHeader.e_fg, "e_fg", "");
			this.AddTableRow(dataTable, this._DosHeader.e_bl1, "e_bl1", "");
			this.AddTableRow(dataTable, this._DosHeader.e_oemid, "e_oemid", "");
			this.AddTableRow(dataTable, this._DosHeader.e_oeminfo, "e_oeminfo", "");
			this.AddTableRow(dataTable, this._DosHeader.e_bl2, "e_bl2", "");
			this.AddTableRow(dataTable, this._DosHeader.e_PESTAR, "e_PESTAR", "PE开始 +本结构的位置");
			return dataTable;
		}

		// Token: 0x06000054 RID: 84 RVA: 0x00006300 File Offset: 0x00004500
		private DataTable TablePEHeader()
		{
			DataTable dataTable = new DataTable(string.Concat(new string[]
			{
				"PeHeader FileStar{",
				this._PEHeader.FileStarIndex.ToString(),
				"}FileEnd{",
				this._PEHeader.FileEndIndex.ToString(),
				"}"
			}));
			dataTable.Columns.Add("Name");
			dataTable.Columns.Add("Size");
			dataTable.Columns.Add("Value16");
			dataTable.Columns.Add("Value10");
			dataTable.Columns.Add("ASCII");
			dataTable.Columns.Add("Describe");
			this.AddTableRow(dataTable, this._PEHeader.Header, "Header", "PE文件标记");
			this.AddTableRow(dataTable, this._PEHeader.Machine, "Machine", "该文件运行所要求的CPU。对于Intel平台，该值是IMAGE_FILE_MACHINE_I386 (14Ch)。我们尝试了LUEVELSMEYER的pe.txt声明的14Dh和14Eh，但Windows不能正确执行。 ");
			this.AddTableRow(dataTable, this._PEHeader.NumberOfSections, "NumberOfSections", "文件的节数目。如果我们要在文件中增加或删除一个节，就需要修改这个值。");
			this.AddTableRow(dataTable, this._PEHeader.TimeDateStamp, "TimeDateStamp", "文件创建日期和时间。 ");
			this.AddTableRow(dataTable, this._PEHeader.PointerToSymbolTable, "PointerToSymbolTable", "用于调试。 ");
			this.AddTableRow(dataTable, this._PEHeader.NumberOfSymbols, "NumberOfSymbols", "用于调试。 ");
			this.AddTableRow(dataTable, this._PEHeader.SizeOfOptionalHeader, "SizeOfOptionalHeader", "指示紧随本结构之后的 OptionalHeader 结构大小，必须为有效值。");
			this.AddTableRow(dataTable, this._PEHeader.Characteristics, "Characteristics", "关于文件信息的标记，比如文件是exe还是dll。");
			return dataTable;
		}

		// Token: 0x06000055 RID: 85 RVA: 0x000064A4 File Offset: 0x000046A4
		private DataTable TableOptionalHeader()
		{
			DataTable dataTable = new DataTable(string.Concat(new string[]
			{
				"OptionalHeader FileStar{",
				this._OptionalHeader.FileStarIndex.ToString(),
				"}FileEnd{",
				this._OptionalHeader.FileEndIndex.ToString(),
				"}"
			}));
			dataTable.Columns.Add("Name");
			dataTable.Columns.Add("Size");
			dataTable.Columns.Add("Value16");
			dataTable.Columns.Add("Value10");
			dataTable.Columns.Add("ASCII");
			dataTable.Columns.Add("Describe");
			this.AddTableRow(dataTable, this._OptionalHeader.Magic, "Magic", "Magic 010B=普通可以执行，0107=ROM映像");
			this.AddTableRow(dataTable, this._OptionalHeader.MajorLinkerVersion, "MajorLinkerVersion", "主版本号");
			this.AddTableRow(dataTable, this._OptionalHeader.MinorLinkerVersion, "MinorLinkerVersion", "副版本号");
			this.AddTableRow(dataTable, this._OptionalHeader.SizeOfCode, "SizeOfCode", "代码段大小");
			this.AddTableRow(dataTable, this._OptionalHeader.SizeOfInitializedData, "SizeOfInitializedData", "已初始化数据大小");
			this.AddTableRow(dataTable, this._OptionalHeader.SizeOfUninitializedData, "SizeOfUninitializedData", "未初始化数据大小");
			this.AddTableRow(dataTable, this._OptionalHeader.AddressOfEntryPoint, "AddressOfEntryPoint", "执行将从这里开始（RVA）");
			this.AddTableRow(dataTable, this._OptionalHeader.BaseOfCode, "BaseOfCode", "代码基址（RVA）");
			this.AddTableRow(dataTable, this._OptionalHeader.ImageBase, "ImageBase", "数据基址（RVA）");
			this.AddTableRow(dataTable, this._OptionalHeader.ImageFileCode, "ImageFileCode", "映象文件基址");
			this.AddTableRow(dataTable, this._OptionalHeader.SectionAlign, "SectionAlign", "区段列队");
			this.AddTableRow(dataTable, this._OptionalHeader.MajorOSV, "MajorOSV", "文件列队");
			this.AddTableRow(dataTable, this._OptionalHeader.MinorOSV, "MinorOSV", "操作系统主版本号");
			this.AddTableRow(dataTable, this._OptionalHeader.MajorImageVer, "MajorImageVer", "映象文件主版本号");
			this.AddTableRow(dataTable, this._OptionalHeader.MinorImageVer, "MinorImageVer", "映象文件副版本号");
			this.AddTableRow(dataTable, this._OptionalHeader.MajorSV, "MajorSV", "子操作系统主版本号");
			this.AddTableRow(dataTable, this._OptionalHeader.MinorSV, "MinorSV", "子操作系统副版本号");
			this.AddTableRow(dataTable, this._OptionalHeader.UNKNOW, "UNKNOW", "Win32版本值");
			this.AddTableRow(dataTable, this._OptionalHeader.SizeOfImage, "SizeOfImage", "映象文件大小");
			this.AddTableRow(dataTable, this._OptionalHeader.SizeOfHeards, "SizeOfHeards", "标志头大小");
			this.AddTableRow(dataTable, this._OptionalHeader.CheckSum, "CheckSum", "文件效验");
			this.AddTableRow(dataTable, this._OptionalHeader.Subsystem, "Subsystem", "子系统（映象文件）1本地 2WINDOWS-GUI 3WINDOWS-CUI 4 POSIX-CUI");
			this.AddTableRow(dataTable, this._OptionalHeader.DLL_Characteristics, "DLL_Characteristics", "DLL标记");
			this.AddTableRow(dataTable, this._OptionalHeader.Bsize, "Bsize", "保留栈的大小");
			this.AddTableRow(dataTable, this._OptionalHeader.TimeBsize, "TimeBsize", "初始时指定栈大小");
			this.AddTableRow(dataTable, this._OptionalHeader.AucBsize, "AucBsize", "保留堆的大小");
			this.AddTableRow(dataTable, this._OptionalHeader.SizeOfBsize, "SizeOfBsize", "初始时指定堆大小");
			this.AddTableRow(dataTable, this._OptionalHeader.FuckBsize, "FuckBsize", "加载器标志");
			this.AddTableRow(dataTable, this._OptionalHeader.DirectCount, "DirectCount", "数据目录数");
			return dataTable;
		}

		// Token: 0x06000056 RID: 86 RVA: 0x00006894 File Offset: 0x00004A94
		private DataTable TableOptionalDirAttrib()
		{
			DataTable dataTable = new DataTable(string.Concat(new string[]
			{
				"OptionalDirAttrib  FileStar{",
				this._OptionalDirAttrib.FileStarIndex.ToString(),
				"}FileEnd{",
				this._OptionalDirAttrib.FileEndIndex.ToString(),
				"}"
			}));
			dataTable.Columns.Add("Name");
			dataTable.Columns.Add("Size");
			dataTable.Columns.Add("Value16");
			dataTable.Columns.Add("Value10");
			dataTable.Columns.Add("ASCII");
			dataTable.Columns.Add("Describe");
			Hashtable hashtable = new Hashtable();
			hashtable.Add("0", "输出表");
			hashtable.Add("1", "输入表");
			hashtable.Add("2", "资源表");
			hashtable.Add("3", "异常表");
			hashtable.Add("4", "安全表");
			hashtable.Add("5", "基部重定位表");
			hashtable.Add("6", "调试数据");
			hashtable.Add("7", "版权数据");
			hashtable.Add("8", "全局PTR");
			hashtable.Add("9", "TLS表");
			hashtable.Add("10", "装入配置表");
			hashtable.Add("11", "其他表1");
			hashtable.Add("12", "其他表2");
			hashtable.Add("13", "其他表3");
			hashtable.Add("14", "其他表4");
			hashtable.Add("15", "其他表5");
			for (int num = 0; num != this._OptionalDirAttrib.DirByte.Count; num++)
			{
				PEHelper.OptionalDirAttrib.DirAttrib dirAttrib = (PEHelper.OptionalDirAttrib.DirAttrib)this._OptionalDirAttrib.DirByte[num];
				string name = "未知表";
				if (hashtable[num.ToString()] != null)
				{
					name = hashtable[num.ToString()].ToString();
				}
				this.AddTableRow(dataTable, dirAttrib.DirRva, name, "地址");
				this.AddTableRow(dataTable, dirAttrib.DirSize, "", "大小");
			}
			return dataTable;
		}

		// Token: 0x06000057 RID: 87 RVA: 0x00006AE8 File Offset: 0x00004CE8
		private DataTable TableSectionData()
		{
			DataTable dataTable = new DataTable(string.Concat(new string[]
			{
				"SectionData FileStar{",
				this._SectionTable.FileStarIndex.ToString(),
				"}FileEnd{",
				this._SectionTable.FileEndIndex.ToString(),
				"}"
			}));
			dataTable.Columns.Add("Name");
			dataTable.Columns.Add("Size");
			dataTable.Columns.Add("Value16");
			dataTable.Columns.Add("Value10");
			dataTable.Columns.Add("ASCII");
			dataTable.Columns.Add("Describe");
			for (int num = 0; num != this._SectionTable.Section.Count; num++)
			{
				PEHelper.SectionTable.SectionData sectionData = (PEHelper.SectionTable.SectionData)this._SectionTable.Section[num];
				this.AddTableRow(dataTable, sectionData.SectName, "SectName", "名字");
				this.AddTableRow(dataTable, sectionData.VirtualAddress, "VirtualAddress", "虚拟内存地址");
				this.AddTableRow(dataTable, sectionData.SizeOfRawDataRVA, "SizeOfRawDataRVA", "RVA偏移");
				this.AddTableRow(dataTable, sectionData.SizeOfRawDataSize, "SizeOfRawDataSize", "RVA大小");
				this.AddTableRow(dataTable, sectionData.PointerToRawData, "PointerToRawData", "指向RAW数据");
				this.AddTableRow(dataTable, sectionData.PointerToRelocations, "PointerToRelocations", "指向定位号");
				this.AddTableRow(dataTable, sectionData.PointerToLinenumbers, "PointerToLinenumbers", "指向行数");
				this.AddTableRow(dataTable, sectionData.NumberOfRelocations, "NumberOfRelocations", "定位号");
				this.AddTableRow(dataTable, sectionData.NumberOfLinenumbers, "NumberOfLinenumbers", "行数号");
				this.AddTableRow(dataTable, sectionData.Characteristics, "Characteristics", "区段标记");
			}
			return dataTable;
		}

		// Token: 0x06000058 RID: 88 RVA: 0x00006CCC File Offset: 0x00004ECC
		private DataTable TableExportDirectory()
		{
			DataTable dataTable = new DataTable(string.Concat(new string[]
			{
				"ExportDirectory FileStar{",
				this._ExportDirectory.FileStarIndex.ToString(),
				"}FileEnd{",
				this._ExportDirectory.FileEndIndex.ToString(),
				"}"
			}));
			dataTable.Columns.Add("Name");
			dataTable.Columns.Add("Size");
			dataTable.Columns.Add("Value16");
			dataTable.Columns.Add("Value10");
			dataTable.Columns.Add("ASCII");
			dataTable.Columns.Add("Describe");
			this.AddTableRow(dataTable, this._ExportDirectory.Characteristics, "Characteristics", "一个保留字段，目前为止值为0。");
			this.AddTableRow(dataTable, this._ExportDirectory.TimeDateStamp, "TimeDateStamp", "产生的时间。");
			this.AddTableRow(dataTable, this._ExportDirectory.MajorVersion, "MajorVersion", "主版本号");
			this.AddTableRow(dataTable, this._ExportDirectory.MinorVersion, "MinorVersion", "副版本号");
			this.AddTableRow(dataTable, this._ExportDirectory.Name, "Name", "一个RVA，指向一个dll的名称的ascii字符串。");
			this.AddTableRow(dataTable, this._ExportDirectory.Base, "Base", "输出函数的起始序号。一般为1。");
			this.AddTableRow(dataTable, this._ExportDirectory.NumberOfFunctions, "NumberOfFunctions", "输出函数入口地址的数组 中的元素个数。");
			this.AddTableRow(dataTable, this._ExportDirectory.NumberOfNames, "NumberOfNames", "输出函数名的指针的数组 中的元素个数，也是输出函数名对应的序号的数组 中的元素个数。");
			this.AddTableRow(dataTable, this._ExportDirectory.AddressOfFunctions, "AddressOfFunctions", "一个RVA，指向输出函数入口地址的数组。");
			this.AddTableRow(dataTable, this._ExportDirectory.AddressOfNames, "AddressOfNames", "一个RVA，指向输出函数名的指针的数组。");
			this.AddTableRow(dataTable, this._ExportDirectory.AddressOfNameOrdinals, "AddressOfNameOrdinals", "一个RVA，指向输出函数名对应的序号的数组。");
			return dataTable;
		}

		// Token: 0x06000059 RID: 89 RVA: 0x00006EC4 File Offset: 0x000050C4
		private DataTable TableExportFunction()
		{
			DataTable dataTable = new DataTable("ExportFunctionList");
			dataTable.Columns.Add("Name");
			dataTable.Columns.Add("Size");
			dataTable.Columns.Add("Value16");
			dataTable.Columns.Add("Value10");
			dataTable.Columns.Add("ASCII");
			dataTable.Columns.Add("Describe");
			for (int num = 0; num != this._ExportDirectory.NameList.Count; num++)
			{
				this.AddTableRow(dataTable, (byte[])this._ExportDirectory.NameList[num], "Name", "_ExportDirectory.Name-Sect.SizeOfRawDataRVA+Sect.PointerToRawData");
			}
			for (int num2 = 0; num2 != this._ExportDirectory.AddressOfNamesList.Count; num2++)
			{
				this.AddTableRow(dataTable, (byte[])this._ExportDirectory.AddressOfNamesList[num2], "NamesList", "");
			}
			for (int num3 = 0; num3 != this._ExportDirectory.AddressOfFunctionsList.Count; num3++)
			{
				this.AddTableRow(dataTable, (byte[])this._ExportDirectory.AddressOfFunctionsList[num3], "Functions", "");
			}
			for (int num4 = 0; num4 != this._ExportDirectory.AddressOfNameOrdinalsList.Count; num4++)
			{
				this.AddTableRow(dataTable, (byte[])this._ExportDirectory.AddressOfNameOrdinalsList[num4], "NameOrdinals", "");
			}
			return dataTable;
		}

		// Token: 0x0600005A RID: 90 RVA: 0x00007050 File Offset: 0x00005250
		private DataTable TableImportDirectory()
		{
			DataTable dataTable = new DataTable(string.Concat(new string[]
			{
				"ImportDirectory FileStar{",
				this._ImportDirectory.FileStarIndex.ToString(),
				"}FileEnd{",
				this._ImportDirectory.FileEndIndex.ToString(),
				"}"
			}));
			dataTable.Columns.Add("Name");
			dataTable.Columns.Add("Size");
			dataTable.Columns.Add("Value16");
			dataTable.Columns.Add("Value10");
			dataTable.Columns.Add("ASCII");
			dataTable.Columns.Add("Describe");
			for (int num = 0; num != this._ImportDirectory.ImportList.Count; num++)
			{
				PEHelper.ImportDirectory.ImportDate importDate = (PEHelper.ImportDirectory.ImportDate)this._ImportDirectory.ImportList[num];
				this.AddTableRow(dataTable, importDate.DLLName, "输入DLL名称", "**********");
				this.AddTableRow(dataTable, importDate.OriginalFirstThunk, "OriginalFirstThunk", "这里实际上保存着一个RVA，这个RVA指向一个DWORD数组，这个数组可以叫做输入查询表。每个数组元素，或者叫一个表项，保存着一个指向函数名的RVA或者保存着一个函数的序号。");
				this.AddTableRow(dataTable, importDate.TimeDateStamp, "TimeDateStamp", "当这个值为0的时候，表明还没有bind。不为0的话，表示已经bind过了。有关bind的内容后面介绍。");
				this.AddTableRow(dataTable, importDate.ForwarderChain, "ForwarderChain", "");
				this.AddTableRow(dataTable, importDate.Name, "Name", "一个RVA，这个RVA指向一个ascii以空字符结束的字符串，这个字符串就是本结构对应的dll文件的名字。");
				this.AddTableRow(dataTable, importDate.FirstThunk, "FirstThunk", "一个RVA,这个RVA指向一个DWORD数组，这个数组可以叫输入地址表。如果bind了的话，这个数组的每个元素，就是一个输入函数的入口地址。");
			}
			return dataTable;
		}

		// Token: 0x0600005B RID: 91 RVA: 0x000071D8 File Offset: 0x000053D8
		private DataTable TableImportFunction()
		{
			DataTable dataTable = new DataTable("ImportFunctionList");
			dataTable.Columns.Add("Name");
			dataTable.Columns.Add("Size");
			dataTable.Columns.Add("Value16");
			dataTable.Columns.Add("Value10");
			dataTable.Columns.Add("ASCII");
			dataTable.Columns.Add("Describe");
			for (int num = 0; num != this._ImportDirectory.ImportList.Count; num++)
			{
				PEHelper.ImportDirectory.ImportDate importDate = (PEHelper.ImportDirectory.ImportDate)this._ImportDirectory.ImportList[num];
				this.AddTableRow(dataTable, importDate.DLLName, "DLL-Name", "**********");
				for (int num2 = 0; num2 != importDate.DllFunctionList.Count; num2++)
				{
					PEHelper.ImportDirectory.ImportDate.FunctionList functionList = (PEHelper.ImportDirectory.ImportDate.FunctionList)importDate.DllFunctionList[num2];
					this.AddTableRow(dataTable, functionList.FunctionName, "FunctionName", "");
					this.AddTableRow(dataTable, functionList.FunctionHead, "FunctionHead", "");
					this.AddTableRow(dataTable, functionList.OriginalFirst, "OriginalFirstThunk", "");
				}
			}
			return dataTable;
		}

		// Token: 0x0600005C RID: 92 RVA: 0x00007318 File Offset: 0x00005518
		private DataTable TableResourceDirectory()
		{
			DataTable dataTable = new DataTable(string.Concat(new string[]
			{
				"ResourceDirectory FileStar{",
				this._ResourceDirectory.FileStarIndex.ToString(),
				"}FileEnd{",
				this._ResourceDirectory.FileEndIndex.ToString(),
				"}"
			}));
			dataTable.Columns.Add("GUID");
			dataTable.Columns.Add("Text");
			dataTable.Columns.Add("ParentID");
			this.AddResourceDirectoryRow(dataTable, this._ResourceDirectory, "");
			return dataTable;
		}

		// Token: 0x0600005D RID: 93 RVA: 0x000073BC File Offset: 0x000055BC
		private void AddResourceDirectoryRow(DataTable MyTable, PEHelper.ResourceDirectory Node, string ParentID)
		{
			string text = "";
			if (Node.Name != null)
			{
				text = this.GetString(Node.Name, "UNICODE");
			}
			for (int num = 0; num != Node.EntryList.Count; num++)
			{
				PEHelper.ResourceDirectory.DirectoryEntry directoryEntry = (PEHelper.ResourceDirectory.DirectoryEntry)Node.EntryList[num];
				long @long = this.GetLong(directoryEntry.Name);
				string text2 = Guid.NewGuid().ToString();
				string text3 = "ID{" + @long + "}";
				if (text.Length != 0)
				{
					text3 = text3 + "Name{" + text + "}";
				}
				if (ParentID.Length == 0)
				{
					long num2 = @long - 1L;
					if (num2 <= 15L)
					{
						switch ((uint)num2)
						{
						case 0U:
							text3 += "Type{Cursor}";
							goto IL_21B;
						case 1U:
							text3 += "Type{Bitmap}";
							goto IL_21B;
						case 2U:
							text3 += "Type{Icon}";
							goto IL_21B;
						case 3U:
							text3 += "Type{Cursor}";
							goto IL_21B;
						case 4U:
							text3 += "Type{Menu}";
							goto IL_21B;
						case 5U:
							text3 += "Type{Dialog}";
							goto IL_21B;
						case 6U:
							text3 += "Type{String Table}";
							goto IL_21B;
						case 7U:
							text3 += "Type{Font Directory}";
							goto IL_21B;
						case 8U:
							text3 += "Type{Font}";
							goto IL_21B;
						case 9U:
							text3 += "Type{Accelerators}";
							goto IL_21B;
						case 10U:
							text3 += "Type{Unformatted}";
							goto IL_21B;
						case 11U:
							text3 += "Type{Message Table}";
							goto IL_21B;
						case 12U:
							text3 += "Type{Group Cursor}";
							goto IL_21B;
						case 13U:
							text3 += "Type{Group Icon}";
							goto IL_21B;
						case 14U:
							text3 += "Type{Information}";
							goto IL_21B;
						case 15U:
							text3 += "Type{Version}";
							goto IL_21B;
						}
					}
					text3 += "Type{未定义}";
				}
				IL_21B:
				MyTable.Rows.Add(new string[]
				{
					text2,
					text3,
					ParentID
				});
				for (int num3 = 0; num3 != directoryEntry.DataEntryList.Count; num3++)
				{
					PEHelper.ResourceDirectory.DirectoryEntry.DataEntry dataEntry = (PEHelper.ResourceDirectory.DirectoryEntry.DataEntry)directoryEntry.DataEntryList[num3];
					string text4 = string.Concat(new string[]
					{
						"Address{",
						this.GetString(dataEntry.ResourRVA),
						"} Size{",
						this.GetString(dataEntry.ResourSize),
						"} FileBegin{",
						dataEntry.FileStarIndex.ToString(),
						"-",
						dataEntry.FileEndIndex.ToString(),
						"}"
					});
					MyTable.Rows.Add(new string[]
					{
						Guid.NewGuid().ToString(),
						text4,
						text2
					});
				}
				for (int num4 = 0; num4 != directoryEntry.NodeDirectoryList.Count; num4++)
				{
					this.AddResourceDirectoryRow(MyTable, (PEHelper.ResourceDirectory)directoryEntry.NodeDirectoryList[num4], text2);
				}
			}
		}

		// Token: 0x04000021 RID: 33
		private byte[] PEFileByte;

		// Token: 0x04000022 RID: 34
		private bool _OpenFile;

		// Token: 0x04000023 RID: 35
		private long PEFileIndex;

		// Token: 0x04000024 RID: 36
		private PEHelper.DosHeader _DosHeader;

		// Token: 0x04000025 RID: 37
		private PEHelper.DosStub _DosStub;

		// Token: 0x04000026 RID: 38
		private PEHelper.PEHeader _PEHeader;

		// Token: 0x04000027 RID: 39
		private PEHelper.OptionalHeader _OptionalHeader;

		// Token: 0x04000028 RID: 40
		private PEHelper.OptionalDirAttrib _OptionalDirAttrib;

		// Token: 0x04000029 RID: 41
		private PEHelper.SectionTable _SectionTable;

		// Token: 0x0400002A RID: 42
		private PEHelper.ExportDirectory _ExportDirectory;

		// Token: 0x0400002B RID: 43
		private PEHelper.ImportDirectory _ImportDirectory;

		// Token: 0x0400002C RID: 44
		private PEHelper.ResourceDirectory _ResourceDirectory;

		// Token: 0x0200002F RID: 47
		private class DosHeader
		{
			// Token: 0x040000DA RID: 218
			public byte[] e_magic = new byte[2];

			// Token: 0x040000DB RID: 219
			public byte[] e_cblp = new byte[2];

			// Token: 0x040000DC RID: 220
			public byte[] e_cp = new byte[2];

			// Token: 0x040000DD RID: 221
			public byte[] e_crlc = new byte[2];

			// Token: 0x040000DE RID: 222
			public byte[] e_cparhdr = new byte[2];

			// Token: 0x040000DF RID: 223
			public byte[] e_minalloc = new byte[2];

			// Token: 0x040000E0 RID: 224
			public byte[] e_maxalloc = new byte[2];

			// Token: 0x040000E1 RID: 225
			public byte[] e_ss = new byte[2];

			// Token: 0x040000E2 RID: 226
			public byte[] e_sp = new byte[2];

			// Token: 0x040000E3 RID: 227
			public byte[] e_csum = new byte[2];

			// Token: 0x040000E4 RID: 228
			public byte[] e_ip = new byte[2];

			// Token: 0x040000E5 RID: 229
			public byte[] e_cs = new byte[2];

			// Token: 0x040000E6 RID: 230
			public byte[] e_rva = new byte[2];

			// Token: 0x040000E7 RID: 231
			public byte[] e_fg = new byte[2];

			// Token: 0x040000E8 RID: 232
			public byte[] e_bl1 = new byte[8];

			// Token: 0x040000E9 RID: 233
			public byte[] e_oemid = new byte[2];

			// Token: 0x040000EA RID: 234
			public byte[] e_oeminfo = new byte[2];

			// Token: 0x040000EB RID: 235
			public byte[] e_bl2 = new byte[20];

			// Token: 0x040000EC RID: 236
			public byte[] e_PESTAR = new byte[2];

			// Token: 0x040000ED RID: 237
			public long FileStarIndex;

			// Token: 0x040000EE RID: 238
			public long FileEndIndex;
		}

		// Token: 0x02000030 RID: 48
		private class DosStub
		{
			// Token: 0x060001D0 RID: 464 RVA: 0x00010580 File Offset: 0x0000E780
			public DosStub(long Size)
			{
				this.DosStubData = new byte[Size];
			}

			// Token: 0x040000EF RID: 239
			public byte[] DosStubData;

			// Token: 0x040000F0 RID: 240
			public long FileStarIndex;

			// Token: 0x040000F1 RID: 241
			public long FileEndIndex;
		}

		// Token: 0x02000031 RID: 49
		private class PEHeader
		{
			// Token: 0x040000F2 RID: 242
			public byte[] Header = new byte[4];

			// Token: 0x040000F3 RID: 243
			public byte[] Machine = new byte[2];

			// Token: 0x040000F4 RID: 244
			public byte[] NumberOfSections = new byte[2];

			// Token: 0x040000F5 RID: 245
			public byte[] TimeDateStamp = new byte[4];

			// Token: 0x040000F6 RID: 246
			public byte[] PointerToSymbolTable = new byte[4];

			// Token: 0x040000F7 RID: 247
			public byte[] NumberOfSymbols = new byte[4];

			// Token: 0x040000F8 RID: 248
			public byte[] SizeOfOptionalHeader = new byte[2];

			// Token: 0x040000F9 RID: 249
			public byte[] Characteristics = new byte[2];

			// Token: 0x040000FA RID: 250
			public long FileStarIndex;

			// Token: 0x040000FB RID: 251
			public long FileEndIndex;
		}

		// Token: 0x02000032 RID: 50
		private class OptionalHeader
		{
			// Token: 0x040000FC RID: 252
			public byte[] Magic = new byte[2];

			// Token: 0x040000FD RID: 253
			public byte[] MajorLinkerVersion = new byte[1];

			// Token: 0x040000FE RID: 254
			public byte[] MinorLinkerVersion = new byte[1];

			// Token: 0x040000FF RID: 255
			public byte[] SizeOfCode = new byte[4];

			// Token: 0x04000100 RID: 256
			public byte[] SizeOfInitializedData = new byte[4];

			// Token: 0x04000101 RID: 257
			public byte[] SizeOfUninitializedData = new byte[4];

			// Token: 0x04000102 RID: 258
			public byte[] AddressOfEntryPoint = new byte[4];

			// Token: 0x04000103 RID: 259
			public byte[] BaseOfCode = new byte[4];

			// Token: 0x04000104 RID: 260
			public byte[] ImageBase = new byte[4];

			// Token: 0x04000105 RID: 261
			public byte[] ImageFileCode = new byte[4];

			// Token: 0x04000106 RID: 262
			public byte[] SectionAlign = new byte[4];

			// Token: 0x04000107 RID: 263
			public byte[] FileAlign = new byte[4];

			// Token: 0x04000108 RID: 264
			public byte[] MajorOSV = new byte[2];

			// Token: 0x04000109 RID: 265
			public byte[] MinorOSV = new byte[2];

			// Token: 0x0400010A RID: 266
			public byte[] MajorImageVer = new byte[2];

			// Token: 0x0400010B RID: 267
			public byte[] MinorImageVer = new byte[2];

			// Token: 0x0400010C RID: 268
			public byte[] MajorSV = new byte[2];

			// Token: 0x0400010D RID: 269
			public byte[] MinorSV = new byte[2];

			// Token: 0x0400010E RID: 270
			public byte[] UNKNOW = new byte[4];

			// Token: 0x0400010F RID: 271
			public byte[] SizeOfImage = new byte[4];

			// Token: 0x04000110 RID: 272
			public byte[] SizeOfHeards = new byte[4];

			// Token: 0x04000111 RID: 273
			public byte[] CheckSum = new byte[4];

			// Token: 0x04000112 RID: 274
			public byte[] Subsystem = new byte[2];

			// Token: 0x04000113 RID: 275
			public byte[] DLL_Characteristics = new byte[2];

			// Token: 0x04000114 RID: 276
			public byte[] Bsize = new byte[4];

			// Token: 0x04000115 RID: 277
			public byte[] TimeBsize = new byte[4];

			// Token: 0x04000116 RID: 278
			public byte[] AucBsize = new byte[4];

			// Token: 0x04000117 RID: 279
			public byte[] SizeOfBsize = new byte[4];

			// Token: 0x04000118 RID: 280
			public byte[] FuckBsize = new byte[4];

			// Token: 0x04000119 RID: 281
			public byte[] DirectCount = new byte[4];

			// Token: 0x0400011A RID: 282
			public long FileStarIndex;

			// Token: 0x0400011B RID: 283
			public long FileEndIndex;
		}

		// Token: 0x02000033 RID: 51
		private class OptionalDirAttrib
		{
			// Token: 0x0400011C RID: 284
			public ArrayList DirByte = new ArrayList();

			// Token: 0x0400011D RID: 285
			public long FileStarIndex;

			// Token: 0x0400011E RID: 286
			public long FileEndIndex;

			// Token: 0x0200005B RID: 91
			public class DirAttrib
			{
				// Token: 0x0400018E RID: 398
				public byte[] DirRva = new byte[4];

				// Token: 0x0400018F RID: 399
				public byte[] DirSize = new byte[4];
			}
		}

		// Token: 0x02000034 RID: 52
		private class SectionTable
		{
			// Token: 0x0400011F RID: 287
			public ArrayList Section = new ArrayList();

			// Token: 0x04000120 RID: 288
			public long FileStarIndex;

			// Token: 0x04000121 RID: 289
			public long FileEndIndex;

			// Token: 0x0200005C RID: 92
			public class SectionData
			{
				// Token: 0x04000190 RID: 400
				public byte[] SectName = new byte[8];

				// Token: 0x04000191 RID: 401
				public byte[] VirtualAddress = new byte[4];

				// Token: 0x04000192 RID: 402
				public byte[] SizeOfRawDataRVA = new byte[4];

				// Token: 0x04000193 RID: 403
				public byte[] SizeOfRawDataSize = new byte[4];

				// Token: 0x04000194 RID: 404
				public byte[] PointerToRawData = new byte[4];

				// Token: 0x04000195 RID: 405
				public byte[] PointerToRelocations = new byte[4];

				// Token: 0x04000196 RID: 406
				public byte[] PointerToLinenumbers = new byte[4];

				// Token: 0x04000197 RID: 407
				public byte[] NumberOfRelocations = new byte[2];

				// Token: 0x04000198 RID: 408
				public byte[] NumberOfLinenumbers = new byte[2];

				// Token: 0x04000199 RID: 409
				public byte[] Characteristics = new byte[4];
			}
		}

		// Token: 0x02000035 RID: 53
		private class ExportDirectory
		{
			// Token: 0x04000122 RID: 290
			public byte[] Characteristics = new byte[4];

			// Token: 0x04000123 RID: 291
			public byte[] TimeDateStamp = new byte[4];

			// Token: 0x04000124 RID: 292
			public byte[] MajorVersion = new byte[2];

			// Token: 0x04000125 RID: 293
			public byte[] MinorVersion = new byte[2];

			// Token: 0x04000126 RID: 294
			public byte[] Name = new byte[4];

			// Token: 0x04000127 RID: 295
			public byte[] Base = new byte[4];

			// Token: 0x04000128 RID: 296
			public byte[] NumberOfFunctions = new byte[4];

			// Token: 0x04000129 RID: 297
			public byte[] NumberOfNames = new byte[4];

			// Token: 0x0400012A RID: 298
			public byte[] AddressOfFunctions = new byte[4];

			// Token: 0x0400012B RID: 299
			public byte[] AddressOfNames = new byte[4];

			// Token: 0x0400012C RID: 300
			public byte[] AddressOfNameOrdinals = new byte[4];

			// Token: 0x0400012D RID: 301
			public ArrayList AddressOfFunctionsList = new ArrayList();

			// Token: 0x0400012E RID: 302
			public ArrayList AddressOfNamesList = new ArrayList();

			// Token: 0x0400012F RID: 303
			public ArrayList AddressOfNameOrdinalsList = new ArrayList();

			// Token: 0x04000130 RID: 304
			public ArrayList NameList = new ArrayList();

			// Token: 0x04000131 RID: 305
			public long FileStarIndex;

			// Token: 0x04000132 RID: 306
			public long FileEndIndex;
		}

		// Token: 0x02000036 RID: 54
		private class ImportDirectory
		{
			// Token: 0x04000133 RID: 307
			public ArrayList ImportList = new ArrayList();

			// Token: 0x04000134 RID: 308
			public long FileStarIndex;

			// Token: 0x04000135 RID: 309
			public long FileEndIndex;

			// Token: 0x0200005D RID: 93
			public class ImportDate
			{
				// Token: 0x0400019A RID: 410
				public byte[] OriginalFirstThunk = new byte[4];

				// Token: 0x0400019B RID: 411
				public byte[] TimeDateStamp = new byte[4];

				// Token: 0x0400019C RID: 412
				public byte[] ForwarderChain = new byte[4];

				// Token: 0x0400019D RID: 413
				public byte[] Name = new byte[4];

				// Token: 0x0400019E RID: 414
				public byte[] FirstThunk = new byte[4];

				// Token: 0x0400019F RID: 415
				public byte[] DLLName;

				// Token: 0x040001A0 RID: 416
				public ArrayList DllFunctionList = new ArrayList();

				// Token: 0x0200005F RID: 95
				public class FunctionList
				{
					// Token: 0x040001A5 RID: 421
					public byte[] OriginalFirst = new byte[4];

					// Token: 0x040001A6 RID: 422
					public byte[] FunctionName;

					// Token: 0x040001A7 RID: 423
					public byte[] FunctionHead = new byte[2];
				}
			}
		}

		// Token: 0x02000037 RID: 55
		private class ResourceDirectory
		{
			// Token: 0x04000136 RID: 310
			public byte[] Characteristics = new byte[4];

			// Token: 0x04000137 RID: 311
			public byte[] TimeDateStamp = new byte[4];

			// Token: 0x04000138 RID: 312
			public byte[] MajorVersion = new byte[2];

			// Token: 0x04000139 RID: 313
			public byte[] MinorVersion = new byte[2];

			// Token: 0x0400013A RID: 314
			public byte[] NumberOfNamedEntries = new byte[2];

			// Token: 0x0400013B RID: 315
			public byte[] NumberOfIdEntries = new byte[2];

			// Token: 0x0400013C RID: 316
			public byte[] Name;

			// Token: 0x0400013D RID: 317
			public ArrayList EntryList = new ArrayList();

			// Token: 0x0400013E RID: 318
			public long FileStarIndex;

			// Token: 0x0400013F RID: 319
			public long FileEndIndex;

			// Token: 0x0200005E RID: 94
			public class DirectoryEntry
			{
				// Token: 0x040001A1 RID: 417
				public byte[] Name = new byte[4];

				// Token: 0x040001A2 RID: 418
				public byte[] Id = new byte[4];

				// Token: 0x040001A3 RID: 419
				public ArrayList DataEntryList = new ArrayList();

				// Token: 0x040001A4 RID: 420
				public ArrayList NodeDirectoryList = new ArrayList();

				// Token: 0x02000060 RID: 96
				public class DataEntry
				{
					// Token: 0x040001A8 RID: 424
					public byte[] ResourRVA = new byte[4];

					// Token: 0x040001A9 RID: 425
					public byte[] ResourSize = new byte[4];

					// Token: 0x040001AA RID: 426
					public byte[] ResourTest = new byte[4];

					// Token: 0x040001AB RID: 427
					public byte[] ResourWen = new byte[4];

					// Token: 0x040001AC RID: 428
					public long FileStarIndex;

					// Token: 0x040001AD RID: 429
					public long FileEndIndex;
				}
			}
		}
	}
}

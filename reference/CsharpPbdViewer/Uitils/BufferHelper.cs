using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using System.Text;

namespace PbdViewer.Uitils
{
	// Token: 0x0200000B RID: 11
	public static class BufferHelper
	{
		// Token: 0x0600002E RID: 46 RVA: 0x00004320 File Offset: 0x00002520
		public static byte[] GetBuffer(byte[] buffer, long offset, int size)
		{
			offset &= 2147483647L;
			size = Math.Min(size, buffer.Length - (int)offset);
			byte[] array = new byte[size];
			Buffer.BlockCopy(buffer, (int)offset, array, 0, size);
			return array;
		}

		// Token: 0x0600002F RID: 47 RVA: 0x00004358 File Offset: 0x00002558
		public static string GetHexString(byte[] buffer)
		{
			return string.Join(" ", from o in buffer
			select string.Format("{0:X2}", o));
		}

		// Token: 0x06000030 RID: 48 RVA: 0x00004389 File Offset: 0x00002589
		public static string GetHexString(byte[] buffer, long offset, int size)
		{
			return BufferHelper.GetHexString(BufferHelper.GetBuffer(buffer, offset, size));
		}

		// Token: 0x06000031 RID: 49 RVA: 0x00004398 File Offset: 0x00002598
		public static ushort GetUShort(byte[] buffer, long offset)
		{
			offset &= 2147483647L;
			return (ushort)(((int)buffer[(int)(checked((IntPtr)(unchecked(offset + 1L))))] << 8) + (int)buffer[(int)(checked((IntPtr)offset))]);
		}

		// Token: 0x06000032 RID: 50 RVA: 0x000043B3 File Offset: 0x000025B3
		public static uint GetUInt(byte[] buffer, long offset)
		{
			offset &= 2147483647L;
			return (uint)(((int)buffer[(int)(checked((IntPtr)(unchecked(offset + 3L))))] << 24) + ((int)buffer[(int)(checked((IntPtr)(unchecked(offset + 2L))))] << 16) + ((int)buffer[(int)(checked((IntPtr)(unchecked(offset + 1L))))] << 8) + (int)buffer[(int)(checked((IntPtr)offset))]);
		}

		// Token: 0x06000033 RID: 51 RVA: 0x000043E4 File Offset: 0x000025E4
		public static string GetDate(byte[] buffer, long offset)
		{
			offset &= 2147483647L;
			ushort @ushort = BufferHelper.GetUShort(buffer, offset + 4L);
			return string.Format("{0}-{1:D2}-{2:D2}", (int)(@ushort + 1900), (int)(buffer[(int)(checked((IntPtr)(unchecked(offset + 6L))))] + 1), buffer[(int)(checked((IntPtr)(unchecked(offset + 7L))))]);
		}

		// Token: 0x06000034 RID: 52 RVA: 0x00004436 File Offset: 0x00002636
		public static string GetDateTime(byte[] buffer, long offset)
		{
			offset &= 2147483647L;
			return string.Format("datetime({0},{1})", BufferHelper.GetDate(buffer, offset), BufferHelper.GetTime(buffer, offset));
		}

		// Token: 0x06000035 RID: 53 RVA: 0x0000445C File Offset: 0x0000265C
		public static string GetTime(byte[] buffer, long offset)
		{
			offset &= 2147483647L;
			string text = checked(string.Format("{0:D2}:{1:D2}:{2:D2}", buffer[(int)((IntPtr)(unchecked(offset + 8L)))], buffer[(int)((IntPtr)(unchecked(offset + 9L)))], buffer[(int)((IntPtr)(unchecked(offset + 10L)))]));
			uint num = BufferHelper.GetUInt(buffer, offset) / 1000U;
			if (num != 0U)
			{
				text += string.Format(".{0:D3}", num);
			}
			return text;
		}

		// Token: 0x06000036 RID: 54 RVA: 0x000044D0 File Offset: 0x000026D0
		public static string GetEscapeString(bool isUnicode, byte[] buffer, long offset)
		{
			string arg = BufferHelper.GetString(isUnicode, buffer, offset).Replace("~", "~~").Replace("\r", "~r").Replace("\n", "~n").Replace("\t", "~t").Replace("\"", "~\"");
			return string.Format("\"{0}\"", arg);
		}

		// Token: 0x06000037 RID: 55 RVA: 0x0000453C File Offset: 0x0000273C
		public static string GetString(bool isUnicode, byte[] buffer, long offset)
		{
			offset &= 2147483647L;
			long num = offset;
			if (isUnicode)
			{
				while (num < (long)buffer.Length)
				{
					if (checked(buffer[(int)((IntPtr)num)] == 0 && buffer[(int)((IntPtr)(unchecked(num + 1L)))] == 0))
					{
						break;
					}
					num += 2L;
				}
			}
			else
			{
				while (num < (long)buffer.Length && buffer[(int)(checked((IntPtr)num))] != 0)
				{
					num += 1L;
				}
			}
			if (num - offset == 0L)
			{
				return string.Empty;
			}
			if (!isUnicode)
			{
				return Encoding.Default.GetString(buffer, (int)offset, (int)(num - offset));
			}
			return Encoding.Unicode.GetString(buffer, (int)offset, (int)(num - offset));
		}

		// Token: 0x06000038 RID: 56 RVA: 0x000045BC File Offset: 0x000027BC
		public static string GetDecimal(byte[] buffer, long offset)
		{
			offset &= 2147483647L;
			ushort @ushort = BufferHelper.GetUShort(buffer, offset);
			byte b = buffer[(int)(checked((IntPtr)(unchecked(offset + 2L))))];
			string text = (new BigInteger(BufferHelper.GetUInt(buffer, offset + 4L)) + (new BigInteger(BufferHelper.GetUInt(buffer, offset + 8L)) << 32) + (new BigInteger((int)BufferHelper.GetUShort(buffer, offset + 12L)) << 64)).ToString();
			if (b > 0)
			{
				if (text.Length <= (int)b)
				{
					text = text.PadLeft((int)(b + 1), '0');
				}
				text = text.Insert(text.Length - (int)b, ".").TrimEnd(new char[]
				{
					'0'
				});
				if (text.EndsWith("."))
				{
					text += "0";
				}
			}
			if (@ushort > 0)
			{
				text = "-" + text;
			}
			return text;
		}

		// Token: 0x06000039 RID: 57 RVA: 0x000046A0 File Offset: 0x000028A0
		public static string GetReal(uint code)
		{
			return string.Format("{0}", BitConverter.ToSingle(new byte[]
			{
				(byte)(code & 255U),
				(byte)(code >> 8 & 255U),
				(byte)(code >> 16 & 255U),
				(byte)(code >> 24 & 255U)
			}, 0));
		}

		// Token: 0x0600003A RID: 58 RVA: 0x000046FE File Offset: 0x000028FE
		public static string GetDouble(byte[] buffer, long offset)
		{
			offset &= 2147483647L;
			return string.Format("{0}", BitConverter.ToDouble(buffer, (int)offset));
		}

		// Token: 0x0600003B RID: 59 RVA: 0x00004721 File Offset: 0x00002921
		public static string GetLongLong(byte[] buffer, long offset)
		{
			offset &= 2147483647L;
			return string.Format("{0}", BitConverter.ToInt64(buffer, (int)offset));
		}

		// Token: 0x0600003C RID: 60 RVA: 0x00004744 File Offset: 0x00002944
		public static string GetCursor(bool isUnicode, byte[] bytes, uint offset, IEnumerable<string> paramList)
		{
			uint num = offset & 2147483647U;
			if (BufferHelper.GetUInt(bytes, (long)((ulong)(num + 8U))) != 65535U)
			{
				return BufferHelper.GetCursor(isUnicode, bytes, BufferHelper.GetUInt(bytes, (long)((ulong)(num + 8U))), paramList);
			}
			string @string = BufferHelper.GetString(isUnicode, bytes, (long)((ulong)BufferHelper.GetUInt(bytes, (long)((ulong)(num + 24U)))));
			string text = "";
			if (paramList != null)
			{
				uint num2 = BufferHelper.GetUInt(bytes, (long)((ulong)(num + 16U)));
				int num3 = 0;
				foreach (string arg in paramList)
				{
					ushort @ushort = BufferHelper.GetUShort(bytes, (long)((ulong)num2));
					ushort ushort2 = BufferHelper.GetUShort(bytes, (long)((ulong)(num2 + 2U)));
					num2 += 4U;
					if (@ushort == 0 && ushort2 == 0)
					{
						break;
					}
					var tmp = @string.Substring(num3, (int)@ushort - num3) + string.Format(":{0}", arg);
					//Console.WriteLine("GetCursor:\t"+tmp);	
					text = text + tmp;
					num3 = (int)ushort2;
				}
				text += @string.Substring(num3);
			}
			return text;
		}
	}
}

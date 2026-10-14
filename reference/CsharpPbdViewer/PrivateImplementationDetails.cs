using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

// Token: 0x02000029 RID: 41
[CompilerGenerated]
internal sealed class PrivateImplementationDetails
{
	// Token: 0x060001C0 RID: 448 RVA: 0x0001039C File Offset: 0x0000E59C
internal static uint ComputeStringHash(string s)
{
	uint num=0;
	if (s != null)
	{
		num = 2166136261U;
		for (int i = 0; i < s.Length; i++)
		{
			num = ((uint)s[i] ^ num) * 16777619U;
		}
	}
	return num;
}


}

#define FAKESHARP
using System;
using System.Collections.Generic;
using System.Linq;
using PbdViewer.Uitils;
using PbdViewer.Uitils.PbClass;

namespace PbdViewer.DataModel
{
	// Token: 0x02000023 RID: 35
	public class FunctionNode : TreeNode
	{
		// Token: 0x060001AD RID: 429 RVA: 0x0000FEA0 File Offset: 0x0000E0A0
		public FunctionNode(PbFunction pbFunction)
		{
			base.NodeType = NodeType.Function;
			base.Name = pbFunction.Definition.Name;
#if FAKESHARP
			base.Text = "//" + pbFunction.Object.GetNameWithParent()+"\r\n";
			base.Text = string.Concat(new object[]
			{
				base.Text,
				"",
				pbFunction.Definition,
				"{\r\n\r\n"
			});
#else
			base.Text = string.Concat(new object[]
			{
				base.Text,
				"//",
				pbFunction.Definition,
				"\r\n\r\n"
			});
#endif
			IEnumerable<string> values = PCodeHelper.ParsePCode(pbFunction, true);
			for (int i = 0; i < pbFunction.Variables.Length; i++)
			{
				PbVariable variable = pbFunction.Variables[i];
				if (pbFunction.Project.IsDebug)
				{
					base.Text += string.Format("{0:X4}:  {1}\r\n", i, variable.ToString(pbFunction.Buffer, true));
				}
				else if (pbFunction.Definition.Params.FirstOrDefault((PbFunctionParam b) => b.Name == variable.Name) == null && !variable.IsReferencedGlobal && !variable.Name.StartsWith("\u0001"))
				{
#if FAKESHARP
					var tmp = variable.ToString(pbFunction.Buffer, false);
					tmp = tmp.Replace("integer", "int");
					tmp = tmp.Replace("date", "DateOnly");
					tmp = tmp.Replace("time", "timeOnly");
					tmp = tmp.Replace("datetime", "DateTime");
					tmp = tmp.Replace("boolean", "bool");

					base.Text += string.Format("{0};\r\n", tmp);
#else
					base.Text += string.Format("{0}\r\n", variable.ToString(pbFunction.Buffer, false));
#endif
				}
			}
			if (pbFunction.Project.IsDebug)
			{
				base.Text += "\r\n\r\n";
				for (int j = 0; j < (pbFunction.Buffer.Length + 15) / 16; j++)
				{
					base.Text += string.Format("{0:X4}:  {1}\r\n", j, BufferHelper.GetHexString(pbFunction.Buffer, (long)(j * 16), 16));
				}
			}
			base.Text += "\r\n\r\n";
#if FAKESHARP

			
            foreach (var item in values)
            {
				if (item == values.Last() && item.Contains("return"))
				{
					base.Text += "}\r\n";
				}
				else
                {
					base.Text += item + "\r\n";
				}
            }
#else
			base.Text += string.Join("\r\n", values);
#endif
		}
	}
}

using System;
using System.Collections;
using System.Linq;
using PbdViewer.Uitils.PbClass;

namespace PbdViewer.DataModel
{
	// Token: 0x02000024 RID: 36
	internal class VariablesNode : TreeNode
	{
		// Token: 0x060001AE RID: 430 RVA: 0x00010088 File Offset: 0x0000E288
		public VariablesNode(string name, PbVariable[] variables, byte[] valueBuffer, bool isAll = false)
		{
			VariablesNode mythis = this;
			base.Name = name;
			base.NodeType = NodeType.Variables;
			if (variables != null)
			{
				base.Text += string.Join("\r\n", from o in variables
				select mythis.ShowVariable(o, valueBuffer, isAll));
			}
		}

		// Token: 0x060001AF RID: 431 RVA: 0x000100EC File Offset: 0x0000E2EC
		private string ShowVariable(PbVariable variable, byte[] valueBuffer, bool isAll)
		{
			if (variable == null)
			{
				return null;
			}
			string text = variable.ToString(valueBuffer, false);
			if (isAll && variable.Object != null)
			{
				ArrayList array = new ArrayList();
				//array.Add(variable.Object.Type.Name);
				PbObject obj = variable.Object.ParentObject;
				while(obj!=null)
                {
					array.Insert(0,obj.Type.Name);
					obj = obj.ParentObject;
				}



				text = string.Format("{0}// {1} -> {2} -> {3}", new object[]
				{
							text.PadRight(40),
							variable.Object.Type.Name,
							string.Join(".",array.ToArray()),
							variable.Object.Entry.File.FileName
				}); 

			
			}
			return text;
		}
	}
}

using System;
using System.Linq;
using PbdViewer.Uitils.PbClass;

namespace PbdViewer.DataModel
{
	// Token: 0x02000022 RID: 34
	internal class ExternalFunctionsNode : TreeNode
	{
		// Token: 0x060001AB RID: 427 RVA: 0x0000FDD0 File Offset: 0x0000DFD0
		public ExternalFunctionsNode(string name, PbFunctionDefinition[] pbFunctionDefinitions, bool isAll = false)
		{
			ExternalFunctionsNode node= this;
			base.Name = name;
			base.NodeType = NodeType.ExternalFunctions;
			base.Text = string.Join("\r\n", from o in pbFunctionDefinitions
			select node.ShowVariable(o, isAll));
		}

		// Token: 0x060001AC RID: 428 RVA: 0x0000FE28 File Offset: 0x0000E028
		private string ShowVariable(PbFunctionDefinition definition, bool isAll)
		{
			if (definition == null)
			{
				return null;
			}
			string text = definition.ToString();
			if (isAll && definition.Object != null)
			{
				text = string.Format("{0}  // {1} -> {2} -> {3}", new object[]
				{
					text,
					definition.Object.Type.Name,
					definition.Object.Entry.EntryName,
					definition.Object.Entry.File.FileName
				});
			}
			return text;
		}
	}
}

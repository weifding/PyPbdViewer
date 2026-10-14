using System;
using System.Linq;
using PbdViewer.Uitils.PbClass;

namespace PbdViewer.DataModel
{
	// Token: 0x02000025 RID: 37
	internal class StructureNode : TreeNode
	{
		// Token: 0x060001B0 RID: 432 RVA: 0x00010170 File Offset: 0x0000E370
		public StructureNode(PbObject oldPbObject)
		{
			base.Name = oldPbObject.Type.Name;
			base.NodeType = NodeType.Structure;
			if (oldPbObject.Variables != null)
			{
				base.Text = string.Join("\r\n", from o in oldPbObject.Variables
				select o.ToString(null, false));
			}
		}
	}
}

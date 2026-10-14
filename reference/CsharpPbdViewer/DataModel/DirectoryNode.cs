using System;

namespace PbdViewer.DataModel
{
	// Token: 0x0200001F RID: 31
	internal class DirectoryNode : TreeNode
	{
		// Token: 0x060001A3 RID: 419 RVA: 0x0000EE59 File Offset: 0x0000D059
		public DirectoryNode(string name)
		{
			base.Name = name;
			base.NodeType = NodeType.Directory;
		}
	}
}

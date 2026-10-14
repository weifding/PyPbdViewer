using System;
using System.Collections.ObjectModel;
using PbdViewer.DataModel;

namespace PbdViewer.ViewModel
{
	// Token: 0x02000006 RID: 6
	internal class WindowViewModel
	{
		// Token: 0x17000004 RID: 4
		// (get) Token: 0x06000014 RID: 20 RVA: 0x000024BA File Offset: 0x000006BA
		public ObservableCollection<TreeNode> Nodes { get; } = new ObservableCollection<TreeNode>();

		// Token: 0x17000005 RID: 5
		// (get) Token: 0x06000015 RID: 21 RVA: 0x000024C2 File Offset: 0x000006C2
		// (set) Token: 0x06000016 RID: 22 RVA: 0x000024CA File Offset: 0x000006CA
		public TreeNode SelectedNode { get; set; }
	}
}

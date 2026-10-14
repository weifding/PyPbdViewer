using System;
using System.Collections;
using System.Collections.ObjectModel;
using System.Windows.Media.Imaging;

namespace PbdViewer.DataModel
{
	// Token: 0x02000028 RID: 40
	public class TreeNode
	{


		public string Suffix { get; set; }
		// Token: 0x17000072 RID: 114
		// (get) Token: 0x060001B2 RID: 434 RVA: 0x00010318 File Offset: 0x0000E518
		// (set) Token: 0x060001B3 RID: 435 RVA: 0x00010320 File Offset: 0x0000E520
		public NodeType NodeType { get; set; }

		// Token: 0x17000073 RID: 115
		// (get) Token: 0x060001B4 RID: 436 RVA: 0x00010329 File Offset: 0x0000E529
		// (set) Token: 0x060001B5 RID: 437 RVA: 0x00010331 File Offset: 0x0000E531
		public bool IsExpanded { get; set; }

		// Token: 0x17000074 RID: 116
		// (get) Token: 0x060001B6 RID: 438 RVA: 0x0001033A File Offset: 0x0000E53A
		// (set) Token: 0x060001B7 RID: 439 RVA: 0x00010342 File Offset: 0x0000E542
		public bool IsSelected { get; set; }

		// Token: 0x17000075 RID: 117
		// (get) Token: 0x060001B8 RID: 440 RVA: 0x0001034B File Offset: 0x0000E54B
		// (set) Token: 0x060001B9 RID: 441 RVA: 0x00010353 File Offset: 0x0000E553
		public string Name { get; protected set; }

		// Token: 0x17000076 RID: 118
		// (get) Token: 0x060001BA RID: 442 RVA: 0x0001035C File Offset: 0x0000E55C
		// (set) Token: 0x060001BB RID: 443 RVA: 0x00010364 File Offset: 0x0000E564
		public string Text { get; protected set; }

		// Token: 0x17000077 RID: 119
		// (get) Token: 0x060001BC RID: 444 RVA: 0x0001036D File Offset: 0x0000E56D
		// (set) Token: 0x060001BD RID: 445 RVA: 0x00010375 File Offset: 0x0000E575
		public BitmapImage Bitmap { get; protected set; }


		public TreeNode parentNode { get; protected set; }

		// Token: 0x17000078 RID: 120
		// (get) Token: 0x060001BE RID: 446 RVA: 0x0001037E File Offset: 0x0000E57E
		public ObservableCollection<TreeNode> Children { get; } = new ObservableCollection<TreeNode>();

		public TreeNode()
        {
            this.Children.CollectionChanged += Children_CollectionChanged;
        }

        private void Children_CollectionChanged(object sender, System.Collections.Specialized.NotifyCollectionChangedEventArgs e)
        {
            foreach (var item in Children)
            {
				item.parentNode = this;

			}
        }

		public string GetRawParentNodeName()
        {
			ArrayList filters = new ArrayList(new[] { "win" , "controls", "men" });
			ArrayList name = new ArrayList();
			//name.Insert(0, this.Name);
			var node = this.parentNode;
			while(node!=null)
            {
				if (!filters.Contains(node.Name))
                {
					var tmp = node.Name;
					if (tmp.IndexOf(".")>0)
                    {
						tmp = tmp.Split('.')[0];

					}
					name.Insert(0, tmp);
				}
					
				node = node.parentNode;

			}
			
			return string.Join(".",name.ToArray());


		}
    }
}

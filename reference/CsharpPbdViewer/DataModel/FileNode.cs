using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using HISWebInterface;
using PbdViewer.Uitils;
using PbdViewer.Uitils.PbClass;

namespace PbdViewer.DataModel
{
	// Token: 0x02000027 RID: 39
	public class FileNode : TreeNode
	{
		// Token: 0x060001B1 RID: 433 RVA: 0x000101E0 File Offset: 0x0000E3E0
		public FileNode(PbFile pbFile)
		{
			base.IsExpanded = true;
			base.Name = pbFile.FileName;
			base.NodeType = NodeType.File;
			ushort version = pbFile.Project.Version;
			int num = PCodeHelper.Count[version];
			int num2 = PCodeHelper.Goodcount[version];

            //         foreach (var item in pbFile.Entries)
            //         {
            //	//item.ShowSource();
            //	base.Children.Add(new EntryNode(item));

            //}


            foreach (IGrouping<string, PbEntry> grouping in from o in pbFile.Entries
                                                            group o by o.Suffix)
            {
                DirectoryNode directoryNode = new DirectoryNode(grouping.Key)
                {
                    IsExpanded = true
                };
                foreach (PbEntry pbEntry in grouping.OrderBy((PbEntry o) => o.Name))
                {
                    //					pbEntry.ShowSource();
                    var tmp = new EntryNode(pbEntry);

                    Log.Info(pbEntry.Suffix);
                    Log.Info(pbEntry.Name);
                    Log.Info(tmp.Text);

                    directoryNode.Children.Add(tmp);
                }
              
                base.Children.Add(directoryNode);
            }
        }


		



	}
}

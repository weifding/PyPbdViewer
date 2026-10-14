using PbdViewer.Uitils.PbClass;
using System.Linq;

namespace PbdViewer.DataModel
{
    // Token: 0x02000024 RID: 36
    internal class ObjectNode : TreeNode
	{
		// Token: 0x060001AE RID: 430 RVA: 0x00010088 File Offset: 0x0000E288
		public ObjectNode(string name, PbObject[] objs, byte[] valueBuffe)
		{
			ObjectNode mythis = this;
			base.Name = name;
			base.NodeType = NodeType.Objects;
			if (objs != null)
			{
				base.Text = string.Join("\r\n", from o in objs
												select mythis.ShowObjects(o, valueBuffe));
			}
		}

		// Token: 0x060001AF RID: 431 RVA: 0x000100EC File Offset: 0x0000E2EC
		private string ShowObjects(PbObject obj, byte[] valueBuffer)
		{
			if (obj == null)
			{
				return null;
			}
			string text = obj.Type.Name;
			text = string.Format("{0}:{1} -> {2}", new object[]
			{
				text,
				obj.InheritType.Name,
				(obj.ParentType.Name.Length>0 ? obj.ParentType.Name:"NULL")
			});
			text += "\r\n\tSTART";

			foreach (var item in obj.Variables)
            {
                try
                {
					text += "\r\n\t" + item.ToString(valueBuffer, false);
				}
                catch (System.Exception ex)
                {

					text += "\r\n\t" + item.Name + " !Parse Error!";

				}
				
				//var tmp = new VariablesNode("variables", array2, this._pbEntry.VariableBuffer, false)

			}
			text += "\r\n\tEND";




			return text;
		}



	}
}

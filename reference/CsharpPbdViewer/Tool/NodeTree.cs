using System.Collections.Generic;

namespace PbdViewer.Tool
{
    public class NodeTree
    {
        public List<ObjectNode> objects = new List<ObjectNode>();

        public void Add(ObjectNode node)
        {
            if (node == null)
            {
                int l = 0;
            }
            foreach (var item in this.objects)
            {
                if (item.InheritType == item.objectName)
                {
                    node.InheritObject = item;

                }
            }

            objects.Add(node);
        }

        public ObjectNode GetObject(string objectname, string parenttype)
        {
            foreach (var item in this.objects)
            {
                if (item != null && item.objectName == objectname && item.ParentType == parenttype)
                {
                    return item;
                }
            }

            return null;

        }
    }
}

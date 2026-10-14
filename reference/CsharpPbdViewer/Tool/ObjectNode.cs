using System.Collections.Generic;

namespace PbdViewer.Tool
{
    public class ObjectNode
    {

        public string objectName;
        public string InheritType;
        public string ParentType;
        public string TopParentName;

        /// <summary>
        /// 从什么类继承过来
        /// </summary>
        public ObjectNode InheritObject;
        /// <summary>
        /// 被使用什么类之中，PB中类和对象是同义的
        /// </summary>
        public ObjectNode ParentObject = null;

        public DefineNode defineNode = new DefineNode();
        public List<FunctionNode> functions = new List<FunctionNode>();

        public void AddDefine(DefineNode node)
        {
            this.defineNode = node;
            this.defineNode.parent = this;
        }

        public void AddFunction(FunctionNode node)
        {
            node.parent = this;
            functions.Add(node);
        }

        public string GetNameSpace()
        {
            ObjectNode obj = this.ParentObject;
            string tmp = "";
            while (obj != null)

            {
                tmp += $".{obj.ParentType}";
                obj = obj.ParentObject;
            }
            return tmp;

        }

        public string ShowObjects()
        {
            string text = string.Format("{0}:{1} -> {2} from {3}", new object[]
                        {

                                objectName,
                                InheritType,
                                ParentType,
                                TopParentName

                        });
            return text;
        }

    }
}

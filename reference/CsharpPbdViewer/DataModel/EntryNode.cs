using System;
using System.Linq;
using PbdViewer.Uitils.PbClass;

namespace PbdViewer.DataModel
{
    // Token: 0x02000020 RID: 32
    public class EntryNode : TreeNode
    {
        // Token: 0x060001A4 RID: 420 RVA: 0x0000EE70 File Offset: 0x0000D070
        public EntryNode(PbEntry pbEntry)
        {
            this._pbEntry = pbEntry;
            base.NodeType = NodeType.Node;
            base.Name = pbEntry.EntryName;
            base.Text = pbEntry.Source;
            base.Bitmap = pbEntry.Bitmap;
            base.Suffix = pbEntry.Suffix;
            string suffix = pbEntry.Suffix;
            uint num = PrivateImplementationDetails.ComputeStringHash(suffix);
            if (num <= 1371315337U)
            {
                if (num != 200788825U)
                {
                    if (num != 862626472U)
                    {
                        if (num != 1371315337U)
                        {
                            return;
                        }
                        if (!(suffix == "udo"))
                        {
                            return;
                        }
                        base.NodeType = NodeType.UserObject;
                        this.ParseControl();
                        return;
                    }
                    else
                    {
                        if (!(suffix == "apl"))
                        {
                            return;
                        }
                        base.NodeType = NodeType.Application;
                        this.ParseApplication();
                        return;
                    }
                }
                else
                {
                    if (!(suffix == "win"))
                    {
                        return;
                    }
                    base.NodeType = NodeType.Window;
                    this.ParseControl();
                    return;
                }
            }
            else if (num <= 3259748752U)
            {
                if (num != 2832955486U)
                {
                    if (num != 3259748752U)
                    {
                        return;
                    }
                    if (!(suffix == "str"))
                    {
                        return;
                    }
                    base.NodeType = NodeType.Structure;
                    this.ParseStructure();
                    return;
                }
                else
                {
                    if (!(suffix == "fun"))
                    {
                        return;
                    }
                    base.NodeType = NodeType.Function;
                    this.ParseFunction();
                    return;
                }
            }
            else if (num != 3383581291U)
            {
                if (num != 3459018009U)
                {
                    return;
                }
                if (!(suffix == "dwo"))
                {
                    return;
                }
                base.NodeType = NodeType.DataWindow;
                return;
            }
            else
            {
                if (!(suffix == "men"))
                {
                    return;
                }
                base.NodeType = NodeType.Menu;
                this.ParseControl();
                return;
            }
        }

        // Token: 0x060001A5 RID: 421 RVA: 0x0000EFCC File Offset: 0x0000D1CC
        private void ParseStructure()
        {
            base.Children.Add(new VariablesNode("properties", this._pbEntry.EntryObject.Variables, null, true));
            base.Children.Add(new VariablesNode("all variables", this._pbEntry.EntryObject.Variables, null, true));
        }

        // Token: 0x060001A6 RID: 422 RVA: 0x0000EFF8 File Offset: 0x0000D1F8
        private void ParseFunction()
        {
            if (this._pbEntry.EntryObject.Functions.Length != 0)
            {
                DirectoryNode directoryNode = new DirectoryNode("functions");
                foreach (PbFunction pbFunction in this._pbEntry.EntryObject.Functions)
                {
                    pbFunction.Definition = this._pbEntry.EntryObject.FunctionDefinitions[(int)pbFunction.Index];
                }
                foreach (PbFunction pbFunction2 in from o in this._pbEntry.EntryObject.Functions
                                                   orderby o.Definition.Name
                                                   select o)
                {
                    directoryNode.Children.Add(new FunctionNode(pbFunction2));
                }
                base.Children.Add(directoryNode);
            }
            PbObject[] array = this._pbEntry.Objects.Values.Where(delegate (PbObject o)
            {
                PbType inheritType = o.InheritType;
                return ((inheritType != null) ? inheritType.Name : null) == "structure";
            }).ToArray<PbObject>();
            if (array.Length != 0)
            {
                DirectoryNode directoryNode2 = new DirectoryNode("structures");
                foreach (PbObject oldPbObject in from o in array
                                                 orderby o.Type.Name
                                                 select o)
                {
                    directoryNode2.Children.Add(new StructureNode(oldPbObject));
                }
                base.Children.Add(directoryNode2);
            }
        }

        // Token: 0x060001A7 RID: 423 RVA: 0x0000F1B8 File Offset: 0x0000D3B8
        private void ParseApplication()
        {
            string name = base.Name.Substring(0, base.Name.IndexOf(".", StringComparison.Ordinal));
            PbVariable[] array = (from o in this._pbEntry.Variables
                                  where !o.IsShared && o.Type.Name != name && o.Flag.HasFlag(PbVariableFlag.IsCustom)
                                  select o).ToArray<PbVariable>();
            if (array.Length != 0)
            {
                base.Children.Add(new VariablesNode("global variables", array, this._pbEntry.VariableBuffer, false));
            }
            PbFunctionDefinition[] array2 = (from o in this._pbEntry.EntryObject.FunctionDefinitions
                                             where o.IsExternal
                                             select o).ToArray<PbFunctionDefinition>();
            if (array2.Length != 0)
            {
                base.Children.Add(new ExternalFunctionsNode("global external functions", array2, false));
            }
            PbVariable[] array3 = (from o in this._pbEntry.Variables
                                   where o.IsShared
                                   select o).ToArray<PbVariable>();
            if (array3.Length != 0)
            {
                base.Children.Add(new VariablesNode("shared variables", array3, this._pbEntry.VariableBuffer, false));
            }
            PbVariable[] array4 = (from o in this._pbEntry.EntryObject.Variables
                                   where o.IsInstance && o.IsShared
                                   select o).ToArray<PbVariable>();
            if (array4.Length != 0)
            {
                base.Children.Add(new VariablesNode("instance variables", array4, this._pbEntry.VariableBuffer, false));
            }
            PbVariable[] array5 = (from o in this._pbEntry.EntryObject.Variables
                                   where !o.IsInstance
                                   select o).ToArray<PbVariable>();
            if (array5.Length != 0)
            {
                base.Children.Add(new VariablesNode("properties", array5, this._pbEntry.VariableBuffer, true));
            }
            PbVariable[] allVariables = this._pbEntry.EntryObject.AllVariables;
            if (allVariables.Length != 0)
            {
                base.Children.Add(new VariablesNode("all instance variables", allVariables, null, true));
            }
            PbFunctionDefinition[] allFunctionDefinitions = this._pbEntry.EntryObject.AllFunctionDefinitions;
            if (allFunctionDefinitions.Length != 0)
            {
                base.Children.Add(new ExternalFunctionsNode("all functions and events", allFunctionDefinitions, true));
            }
            PbObject[] array6 = this._pbEntry.Objects.Values.Where(delegate (PbObject o)
            {
                PbType inheritType = o.InheritType;
                return ((inheritType != null) ? inheritType.Name : null) == "structure";
            }).ToArray<PbObject>();
            if (array6.Length != 0)
            {
                DirectoryNode directoryNode = new DirectoryNode("structures");
                foreach (PbObject oldPbObject in array6)
                {
                    directoryNode.Children.Add(new StructureNode(oldPbObject));
                }
                base.Children.Add(directoryNode);
            }
            foreach (PbFunction pbFunction in this._pbEntry.EntryObject.Functions)
            {
                pbFunction.Definition = this._pbEntry.EntryObject.FunctionDefinitions[(int)pbFunction.Index];
            }
            PbFunction[] array9 = (from o in this._pbEntry.EntryObject.Functions
                                   where o.Definition.IsEvent
                                   select o).ToArray<PbFunction>();
            if (array9.Length != 0)
            {
                DirectoryNode directoryNode2 = new DirectoryNode("events");
                foreach (PbFunction pbFunction2 in array9)
                {
                    directoryNode2.Children.Add(new FunctionNode(pbFunction2));
                }
                base.Children.Add(directoryNode2);
            }
            PbFunction[] array10 = (from o in this._pbEntry.EntryObject.Functions
                                    where !o.Definition.IsEvent && !o.Definition.IsExternal
                                    select o).ToArray<PbFunction>();
            if (array10.Length != 0)
            {
                DirectoryNode directoryNode3 = new DirectoryNode("functions");
                foreach (PbFunction pbFunction3 in from o in array10
                                                   orderby o.Definition.Name
                                                   select o)
                {
                    directoryNode3.Children.Add(new FunctionNode(pbFunction3));
                }
                base.Children.Add(directoryNode3);
            }
        }

        // Token: 0x060001A8 RID: 424 RVA: 0x0000F638 File Offset: 0x0000D838
        private void ParseControl()
        {

            //获取全部的对象属性值
            PbObject[] objarray = this._pbEntry.Objects.Values.ToArray();
            if (objarray.Length != 0)
            {
                base.Children.Add(new ObjectNode("objects properties", objarray, this._pbEntry.VariableBuffer));

            }



            if (this._pbEntry.EntryObject.Variables.Length != 0)
            {
                base.Children.Add(new VariablesNode("all variables", this._pbEntry.EntryObject.Variables, this._pbEntry.VariableBuffer, true));
            }



            PbObject[] array = this._pbEntry.Objects.Values.Where(delegate (PbObject o)
            {
                PbType inheritType = o.InheritType;
                return ((inheritType != null) ? inheritType.Name : null) == "structure";
            }).ToArray<PbObject>();
            PbObject[] controls = (from o in this._pbEntry.Objects.Values
                                   where o.ParentObject == this._pbEntry.EntryObject
                                   select o).ToArray<PbObject>();
            PbVariable[] array2 = (from o in this._pbEntry.Variables
                                   where o.IsShared
                                   select o).ToArray<PbVariable>();
            if (array2.Length != 0)
            {
                base.Children.Add(new VariablesNode("shared variables", array2, this._pbEntry.VariableBuffer, false));
            }
            PbVariable[] array3 = (from o in this._pbEntry.EntryObject.Variables
                                   where o.IsInstance && o.IsShared
                                   select o).ToArray<PbVariable>();
            if (array3.Length != 0)
            {
                base.Children.Add(new VariablesNode("instance variables", array3, this._pbEntry.VariableBuffer, false));
            }
            PbVariable[] array4 = (from o in this._pbEntry.EntryObject.Variables
                                   where !o.IsInstance && controls.FirstOrDefault((PbObject b) => b.Type.Name == o.Type.Name) == null
                                   select o).ToArray<PbVariable>();
            if (array4.Length != 0)
            {
                base.Children.Add(new VariablesNode("properties", array4, this._pbEntry.VariableBuffer, true));
            }
            PbVariable[] allVariables = this._pbEntry.EntryObject.AllVariables;
            if (allVariables.Length != 0)
            {
                base.Children.Add(new VariablesNode("all instance variables", allVariables, null, true));
            }
            PbFunctionDefinition[] allFunctionDefinitions = this._pbEntry.EntryObject.AllFunctionDefinitions;
            if (allFunctionDefinitions.Length != 0)
            {
                base.Children.Add(new ExternalFunctionsNode("all functions and events", allFunctionDefinitions, true));
            }
            PbFunctionDefinition[] array5 = (from o in this._pbEntry.EntryObject.FunctionDefinitions
                                             where o.IsExternal
                                             select o).ToArray<PbFunctionDefinition>();
            if (array5.Length != 0)
            {
                base.Children.Add(new ExternalFunctionsNode("external functions", array5, false));
            }
            if (array.Length != 0)
            {
                DirectoryNode directoryNode = new DirectoryNode("structures");
                foreach (PbObject oldPbObject in from o in array
                                                 orderby o.Type.Name
                                                 select o)
                {
                    directoryNode.Children.Add(new StructureNode(oldPbObject));
                }
                base.Children.Add(directoryNode);
            }
            DirectoryNode directoryNode2 = new DirectoryNode("controls");
            foreach (PbObject pbObject in from o in controls
                                          orderby o.Type.Name
                                          select o)
            {
                directoryNode2.Children.Add(new ControlNode(pbObject.Type.Name, pbObject));
            }
            if (directoryNode2.Children.Count > 0)
            {
                base.Children.Add(directoryNode2);
            }
            foreach (PbFunction pbFunction in this._pbEntry.EntryObject.Functions)
            {
                pbFunction.Definition = this._pbEntry.EntryObject.FunctionDefinitions[(int)pbFunction.Index];
            }
            PbFunction[] array7 = (from o in this._pbEntry.EntryObject.Functions
                                   where o.Definition.IsEvent
                                   select o).ToArray<PbFunction>();
            if (array7.Length != 0)
            {
                DirectoryNode directoryNode3 = new DirectoryNode("events");
                foreach (PbFunction pbFunction2 in array7)
                {
                    directoryNode3.Children.Add(new FunctionNode(pbFunction2));
                }
                base.Children.Add(directoryNode3);
            }
            PbFunction[] array8 = (from o in this._pbEntry.EntryObject.Functions
                                   where !o.Definition.IsEvent && !o.Definition.IsExternal
                                   select o).ToArray<PbFunction>();
            if (array8.Length != 0)
            {
                DirectoryNode directoryNode4 = new DirectoryNode("functions");
                foreach (PbFunction pbFunction3 in from o in array8
                                                   orderby o.Definition.Name
                                                   select o)
                {
                    directoryNode4.Children.Add(new FunctionNode(pbFunction3));
                }
                base.Children.Add(directoryNode4);
            }
        }

        // Token: 0x040000B6 RID: 182
        private readonly PbEntry _pbEntry;
    }
}

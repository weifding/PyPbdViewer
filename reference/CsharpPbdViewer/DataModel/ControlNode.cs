using System;
using System.Linq;
using PbdViewer.Uitils.PbClass;

namespace PbdViewer.DataModel
{
	// Token: 0x02000021 RID: 33
	internal class ControlNode : TreeNode
	{
		// Token: 0x060001AA RID: 426 RVA: 0x0000FB5C File Offset: 0x0000DD5C
		public ControlNode(string name, PbObject @object)
		{
			base.Name = ((name == @object.Type.Name) ? name : string.Format("{0}({1})", name, @object.Type.Name));

			PbObject[] controls = (from o in @object.Entry.Objects.Values
			where o.ParentObject == @object
			select o).ToArray<PbObject>();


			if (@object.Variables.Length != 0)
			{
				base.Children.Add(new VariablesNode("all variables", @object.Variables, @object.Entry.VariableBuffer, true));
			}



			PbVariable[] array = (from o in @object.Variables
			where !o.IsInstance && controls.FirstOrDefault((PbObject b) => b.Type.Name == o.Type.Name) == null
			select o).ToArray<PbVariable>();
			if (array.Length != 0)
			{
				base.Children.Add(new VariablesNode("properties", array, @object.Entry.VariableBuffer, true));
			}
			PbVariable[] allVariables = @object.AllVariables;
			if (allVariables.Length != 0)
			{
				base.Children.Add(new VariablesNode("all instance variables", allVariables, null, true));
			}
			PbFunctionDefinition[] allFunctionDefinitions = @object.AllFunctionDefinitions;
			if (allFunctionDefinitions.Length != 0)
			{
				base.Children.Add(new ExternalFunctionsNode("all functions and events", allFunctionDefinitions, true));
			}
			DirectoryNode directoryNode = new DirectoryNode("controls");
			foreach (PbObject pbObject in controls)
			{
				directoryNode.Children.Add(new ControlNode(pbObject.Type.Name, pbObject));
			}
			if (directoryNode.Children.Count > 0)
			{
				base.Children.Add(directoryNode);
			}
			if (@object.Functions != null)
			{
				foreach (PbFunction pbFunction in @object.Functions)
				{
					pbFunction.Definition = @object.FunctionDefinitions[(int)pbFunction.Index];
				}
				PbFunction[] array3 = (from o in @object.Functions
				where o.Definition.IsEvent
				select o).ToArray<PbFunction>();
				if (array3.Length != 0)
				{
					DirectoryNode directoryNode2 = new DirectoryNode("events");
					foreach (PbFunction pbFunction2 in array3)
					{
						directoryNode2.Children.Add(new FunctionNode(pbFunction2));
					}
					base.Children.Add(directoryNode2);
				}
			}
		}
	}
}

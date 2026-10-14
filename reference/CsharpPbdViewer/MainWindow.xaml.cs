using System;
using System.CodeDom.Compiler;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Markup;
using HISWebInterface;
using PbdViewer.DataModel;
using PbdViewer.Tool;
using PbdViewer.Uitils.PbClass;
using PbdViewer.ViewModel;

//do while的解析是有问题的，uf_get_jzje的66行应该是do while才对
namespace PbdViewer
{
	// Token: 0x02000003 RID: 3
	public partial class MainWindow : Window
	{
		// Token: 0x06000004 RID: 4 RVA: 0x00002080 File Offset: 0x00000280
		public MainWindow()
		{
			this.InitializeComponent();
			base.DataContext = (this._model = new WindowViewModel());
			base.WindowStartupLocation = WindowStartupLocation.CenterScreen;
			base.Loaded += this.MainWindow_Loaded;
			Log.InitLogDirectory();
			SourceFile source = new SourceFile();
			//source.ParsePath(@"D:\下载\20220101\20211229\mzsf");
			source.ParsePath(@"D:\Working\PowerHIS\PBCode\pbd");
		}

		// Token: 0x06000005 RID: 5 RVA: 0x000020C6 File Offset: 0x000002C6
		private void MainWindow_Loaded(object sender, RoutedEventArgs e)
		{
		}

		// Token: 0x06000006 RID: 6 RVA: 0x000020C8 File Offset: 0x000002C8
		private void MainWindow_OnPreviewDragOver(object sender, DragEventArgs e)
		{
			e.Effects = DragDropEffects.None;
			if (!e.Data.GetDataPresent(DataFormats.FileDrop))
			{
				return;
			}
			Array array = (Array)e.Data.GetData(DataFormats.FileDrop);
			string text = (array != null) ? array.GetValue(0).ToString() : null;
			if (string.IsNullOrEmpty(text))
			{
				return;
			}
			string a = Path.GetExtension(text).ToLower();
			if (a == ".exe" || a == ".dll" || a == ".pbd" || a == ".pbl")
			{
				e.Effects = DragDropEffects.Move;
			}
			e.Handled = true;
		}

		// Token: 0x06000007 RID: 7 RVA: 0x00002170 File Offset: 0x00000370
		private void MainWindow_OnPreviewDrop(object sender, DragEventArgs e)
		{
			e.Handled = true;
			if (!e.Data.GetDataPresent(DataFormats.FileDrop))
			{
				return;
			}
			Array array = (Array)e.Data.GetData(DataFormats.FileDrop);
			string text = (array != null) ? array.GetValue(0).ToString() : null;
			if (string.IsNullOrEmpty(text))
			{
				return;
			}
			this.AddFile(text);
		}

		// Token: 0x06000008 RID: 8 RVA: 0x000021D0 File Offset: 0x000003D0
		private void AddFile(string filename)
		{
			//try
			{
				using (List<PbFile>.Enumerator enumerator = new PbProject(filename).Files.GetEnumerator())
				{
					while (enumerator.MoveNext())
					{
						PbFile pbFile = enumerator.Current;
						TreeNode treeNode = this._model.Nodes.FirstOrDefault((TreeNode o) => string.Compare(o.Name, pbFile.FilePath, StringComparison.OrdinalIgnoreCase) == 0);
						if (treeNode != null)
						{
							this._model.Nodes.Remove(treeNode);
						}
						this._model.Nodes.Add(new FileNode(pbFile));
					}
				}
			}
			//catch (Exception ex)
			//{
			//	MessageBox.Show(ex.Message);
			//}
		}

		// Token: 0x06000009 RID: 9 RVA: 0x00002294 File Offset: 0x00000494
		private void TreeView_OnSelectedItemChanged(object sender, RoutedPropertyChangedEventArgs<object> e)
		{
			TreeNode treeNode = e.NewValue as TreeNode;
			this.Image.Visibility = Visibility.Collapsed;
			this.RichTextBox.Visibility = Visibility.Collapsed;
			if (treeNode != null)
			{
				if (treeNode.Bitmap != null)
				{
					this.Image.Source = treeNode.Bitmap;
					this.Image.Visibility = Visibility.Visible;
					return;
				}
				this.RichTextBox.Document.Blocks.Clear();
				this.RichTextBox.Document.Blocks.Add(new Paragraph(new Run(treeNode.Text)));
				this.RichTextBox.Visibility = Visibility.Visible;
			}
		}

		// Token: 0x0600000A RID: 10 RVA: 0x00002334 File Offset: 0x00000534
		private void UIElement_OnKeyDown(object sender, KeyEventArgs e)
		{
			TreeView treeView = (TreeView)sender;
			if (e.Key == Key.Delete)
			{
				TreeNode treeNode = treeView.SelectedItem as TreeNode;
				if (treeNode != null && treeNode.NodeType == NodeType.File)
				{
					this._model.Nodes.Remove(treeNode);
				}
			}
		}

		// Token: 0x04000001 RID: 1
		private readonly WindowViewModel _model;
	}
}

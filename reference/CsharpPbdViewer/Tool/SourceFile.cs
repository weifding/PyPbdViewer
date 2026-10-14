using HISWebInterface;
using PbdViewer.DataModel;
using PbdViewer.Uitils;
using PbdViewer.Uitils.PbClass;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace PbdViewer.Tool
{
    class SourceFile
    {

        NodeTree pbObjectTree = new NodeTree();
        List<String> list = new List<string>();

        public static string topName = "";

        public List<string> FindFile(string sSourcePath)
        {

            //在指定目录及子目录下查找文件,在list中列出子目录及文件

            DirectoryInfo Dir = new DirectoryInfo(sSourcePath);
            DirectoryInfo[] DirSub = Dir.GetDirectories();

            if (DirSub.Length <= 0)
            {
                foreach (FileInfo f in Dir.GetFiles("*.*", SearchOption.TopDirectoryOnly)) //查找文件
                {
                    list.Add(Dir + @"\" + f.ToString());
                }
            }


            int t = 1;

            foreach (DirectoryInfo d in DirSub)//查找子目录 
            {

                CreateDir("output\\" + d.FullName.Replace(":", ""));
                FindFile(Dir + @"\" + d.ToString());
                list.Add(Dir + @"\" + d.ToString());

                if (t == 1)
                {
                    foreach (FileInfo f in Dir.GetFiles("*.*", SearchOption.TopDirectoryOnly)) //查找文件
                    {
                        list.Add(Dir + @"\" + f.ToString());
                    }
                    t = t + 1;
                }
            }
            return list;
        }

        public void ParsePath(string path)
        {

            FindFile(path);
            foreach (var filename in this.list)
            {

                string a = Path.GetExtension(filename).ToLower();
                SourceFile.topName = Path.GetFileNameWithoutExtension(filename);
                this.pbObjectTree.objects.Clear();

                if (a == ".exe" || a == ".pbd" || a == ".pbl")
                {
                    try
                    {
                        using (List<PbFile>.Enumerator enumerator = new PbProject(filename).Files.GetEnumerator())
                        {
                            while (enumerator.MoveNext())
                            {

                                PbFile pbFile = enumerator.Current;
                                //Save(pbFile);
                                TryParseToCSharp(pbFile);
                                SaveCSharpFile();



                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Log.Info(ex.Message);
                    }
                }
            }


        }

        public void CalcSuperClass()
        {
            foreach (var item in this.pbObjectTree.objects)
            {
                if (item.InheritType.IndexOf(".") > 0)
                {
                    var tmp = item.InheritType.Split('.');


                }
                Console.WriteLine(item.objectName + ":" + item.InheritType);
            }
        }

        public void SaveCSharpFile()
        {
            string root = System.IO.Directory.GetCurrentDirectory() + "/CSharp";
            if (!CreateDir(root))
            {
                return;
            }
            foreach (var item in this.pbObjectTree.objects)
            {

                string @namespace = SourceFile.topName + "." + item.GetNameSpace();
                string filepath = root + "/" + @namespace.Replace(".", "/");
                if (!File.Exists(filepath))
                {
                    CreateDir(filepath);
                }

                string filename = "";
                string code = "";



                if (item.defineNode != null)
                {
                    if (!string.IsNullOrEmpty(item.defineNode.body))
                    {
                        code = replacedefine(item.defineNode.body);
                        filename = filepath + "/" + item.objectName + ".cs";
                        Console.WriteLine(filename);
                        code = CreateSourceCode(item, code, @namespace);
                        SaveDateToFile(filename, code);
                    }

                }

                Dictionary<string, int> filecount = new Dictionary<string, int>();
                foreach (var fun in item.functions)
                {
                    filename = "";
                    if (filecount.ContainsKey(fun.name))
                    {
                        filecount[fun.name] += 1;
                        filename = filepath + "/" + fun.name + filecount[fun.name].ToString() + ".cs";
                    }
                    else
                    {
                        filecount.Add(fun.name, 1);
                        filename = filepath + "/" + fun.name + ".cs";
                    }
                    Console.WriteLine(filename);
                    code = replacefunction(fun.body, fun.isstatic);
                    code = CreateSourceCode(item, code, @namespace);
                    SaveDateToFile(filename, code);
                }


            }

        }

        private string replacefunction(string code, bool isstatic)
        {
            return code;
        }
        private string replacedefine(string code)
        {
            if (string.IsNullOrEmpty(code))
            {
                return string.Empty;
            }
            var items = code.Split(new string[] { "\r\n" }, StringSplitOptions.None);
            string result = "";
            foreach (var item in items)
            {
                var tmp = item;
                tmp = tmp.Replace("integer", "int");
                tmp = tmp.Replace("date", "DateOnly");
                tmp = tmp.Replace("time", "timeOnly");
                tmp = tmp.Replace("datetime", "DateTime");
                tmp = tmp.Replace("boolean", "bool");
                tmp = tmp.Replace("\r\n", ";\r\n");

                if (tmp.IndexOf("protected") == -1)
                {
                    tmp = "public " + tmp;
                }
                result += tmp + ";\r\n";

            }


            return result;
        }


        private string CreateSourceCode(ObjectNode item, string code, string @namespace)
        {
            string class_template = "";
            if (!string.IsNullOrEmpty(item.InheritType))
            {
                class_template = $"namespace {@namespace}\r\n" +
                    "{\r\n" +
                       $"\tpublic partial class {item.objectName}:{item.InheritType}\r\n" +
                    "\t{\r\n" +
                    $"{ code }\r\n" +

                    "\t}\r\n" +
                    "}\r\n";
            }
            else
            {
                class_template = $"namespace {@namespace}\r\n" +
                    "{\r\n" +
                       $"\tpublic partial class {item.objectName}\r\n" +
                    "\t{\r\n" +
                     $"{ code }\r\n" +

                    "\t}\r\n" +
                    "}\r\n";
            }
            return class_template;
        }

        private void SaveDateToFile(string file, string info)
        {
            try
            {
                StreamWriter sw;
                sw = File.CreateText(file);
                sw.WriteLine(info);
                sw.Close();
                Log.Info("save to:" + file);
            }
            catch (Exception ex)
            {

            }
        }

        public void SaveDateToFile(string filename, ushort data)
        {
            string info = data.ToString();
            SaveDateToFile(filename, info);
        }

        public void Save(PbFile pbFile)
        {
            string root = System.IO.Directory.GetCurrentDirectory() + "/output";
            string root_folder = root + "/" + pbFile.FilePath.Replace(":", "");
            if (!CreateDir(root_folder))
            {
                return;
            }

            ushort version = pbFile.Project.Version;
            SaveDateToFile(root_folder + "/version.md", version);
            if (version == 0)
            {
                return;
            }


            int num = PCodeHelper.Count[version];
            int num2 = PCodeHelper.Goodcount[version];
            foreach (IGrouping<string, PbEntry> grouping in from o in pbFile.Entries
                                                            group o by o.Suffix)
            {
                string keyfolder = root_folder + "/" + grouping.Key;
                CreateDir(keyfolder);
                foreach (PbEntry pbEntry in grouping.OrderBy((PbEntry o) => o.Name))
                {
                    var tmp = new EntryNode(pbEntry);
                    ParseTreeNode(tmp, keyfolder);
                }

            }
        }


        public void TryParseToCSharp(PbFile pbFile)
        {

            foreach (IGrouping<string, PbEntry> grouping in from o in pbFile.Entries
                                                            group o by o.Suffix)
            {

                bool isstatic = false;
                if (grouping.Key == "fun") //pbd或者pbl的全局函数
                {
                    isstatic = true;
                }

                foreach (PbEntry pbEntry in grouping.OrderBy((PbEntry o) => o.Name))
                {
                    var tmp = new EntryNode(pbEntry);
                    ParseObjectNodeForCSharp(tmp);
                }

                foreach (var item in this.pbObjectTree.objects)
                {
                    Console.WriteLine(item.ShowObjects());
                }



                foreach (PbEntry pbEntry in grouping.OrderBy((PbEntry o) => o.Name))
                {
                    var tmp = new EntryNode(pbEntry);
                    ParseTreeNodeForCSharp(tmp, isstatic);
                }

            }
        }

        public bool CreateDir(string url)
        {
            //Console.WriteLine(url);
            try
            {
                if (!Directory.Exists(url))
                {
                    Directory.CreateDirectory(url);
                }
                return true;
            }
            catch (Exception ex)
            {
                Log.Info(ex.Message);
                return false;
            }
        }

        private void ParseObjectNodeForCSharp(TreeNode treeNode)
        {

            foreach (var item in treeNode.Children)
            {

                //Console.WriteLine(item.Name);
                if (item.Children.Count > 0)
                {

                    ParseObjectNodeForCSharp(item);
                }
                else
                {
                    string parentobjectname = SourceFile.topName+"."+item.GetRawParentNodeName();

                   

                    if (item.Name == "objects properties")
                    {

                        //对象列表
                        var obj = item.Text.Split(new string[] { "\r\n" }, StringSplitOptions.None);
                        foreach (var line in obj)
                        {
                            if (line.Contains(":") && !line.Contains("="))
                            {

                                var ar = line.Split(':');
                                ObjectNode pbobject = new ObjectNode();
                                pbobject.objectName = ar[0].Trim();
                                pbobject.TopParentName = parentobjectname;


                                var tmp = ar[1];

                                int pos = tmp.IndexOf("->");
                                if (pos != -1)
                                {
                                    tmp = tmp.Substring(0, pos).Trim();
                                    pbobject.ParentType = ar[1].Substring(pos + 2).Trim();

                                }
                                if (tmp.Contains('`'))  //指向另外一个namespace的的class对象
                                {
                                    pbobject.InheritType = tmp.Replace('`', '.').Trim();
                                }
                                else
                                {
                                    pbobject.InheritType = tmp.Trim();

                                }

                                this.pbObjectTree.Add(pbobject);

                            }
                        }
                    }
                }
            }
        }

        private void ParseTreeNodeForCSharp(TreeNode treeNode, bool isstatic = false)
        {

            foreach (var item in treeNode.Children)
            {

                //Console.WriteLine(item.Name);
                if (item.Children.Count > 0)
                {

                    ParseTreeNodeForCSharp(item);
                }
                else
                {


                    switch (item.Name)
                    {
                        case "global variables":
                            {
                                //全局变量
                                break;
                            }
                        case "all variables":
                            {
                                DefineNode node = new DefineNode();
                                //对象中的全部对象和属性
                            
                                var vals = item.Text.Split(new string[] { "\r\n" }, StringSplitOptions.None);
                                if (vals.Length > 0)
                                {
                                   var ss =  vals[0].Split(new string[] { "//" }, StringSplitOptions.None);
                                    if (ss.Length>0)
                                    {
                                        var words = ss[1].Split(new string[] { "->" }, StringSplitOptions.None);


                                        node.objectName = words[0].Trim();

                                        string parentname = words[1].Trim();
                                        if(string.IsNullOrEmpty(parentname))
                                        {
                                            parentname = null;
                                        }
                                        node.body = item.Text;
                                        ObjectNode obj = this.pbObjectTree.GetObject(node.objectName, parentname);
                                        if (obj == null)
                                        {
                                            obj = new ObjectNode();
                                            obj.objectName = words[0].Trim();
                                            obj.ParentType = null;

                                            this.pbObjectTree.Add(obj);

                                        }
                                        obj.AddDefine(node);

                                    }

                                
                                }
                            }
                            break;


                    }

                    


                    if (item.NodeType == NodeType.Function)
                    {
                        string parentobjectname = item.GetRawParentNodeName();

                        //if (treeNode.Name == "events" || treeNode.Name == "functions")
                        {
                            FunctionNode functionNode = new FunctionNode();
                            functionNode.name = item.Name;
                            functionNode.body = item.Text;
                            functionNode.objectName = parentobjectname;

                            functionNode.type = treeNode.Name;
                            functionNode.isstatic = isstatic;

                            ObjectNode @class = this.pbObjectTree.GetObject(parentobjectname, "");
                            if (@class == null)
                            {
                                @class = new ObjectNode();
                                @class.objectName = parentobjectname;

                                this.pbObjectTree.Add(@class);

                            }
                            @class.AddFunction(functionNode);


                        }
                        Console.WriteLine(item.Name);
                    }




                    //string filename = "";
                    //if (filecount.ContainsKey(item.Name))
                    //{
                    //	filecount[item.Name] += 1;
                    //	filename = parent_folder + "/" + item.Name + filecount[item.Name].ToString() + ".pb";
                    //}
                    //else
                    //{
                    //	filecount.Add(item.Name, 1);
                    //	filename = parent_folder + "/" + item.Name + ".pb";
                    //}

                    ////string filename = parent_folder+"/"+item.Name + ".pb";
                    //SaveDateToFile(filename, item.Text);
                }
            }
        }

        private void ParseTreeNode(TreeNode treeNode, String parent_folder)
        {
            Dictionary<string, int> filecount = new Dictionary<string, int>();
            parent_folder = parent_folder + "/" + treeNode.Name;
            CreateDir(parent_folder);
            foreach (var item in treeNode.Children)
            {
                //Console.WriteLine(item.Name);
                if (item.Children.Count > 0)
                {
                    ParseTreeNode(item, parent_folder);

                }
                else
                {
                    string filename = "";
                    if (filecount.ContainsKey(item.Name))
                    {
                        filecount[item.Name] += 1;
                        filename = parent_folder + "/" + item.Name + filecount[item.Name].ToString() + ".pb";
                    }
                    else
                    {
                        filecount.Add(item.Name, 1);
                        filename = parent_folder + "/" + item.Name + ".pb";
                    }

                    //string filename = parent_folder+"/"+item.Name + ".pb";
                    SaveDateToFile(filename, item.Text);
                }
            }
        }
    }
}

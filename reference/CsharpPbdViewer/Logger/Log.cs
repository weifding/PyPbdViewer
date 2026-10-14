using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Web;
using System.Runtime.CompilerServices;
using System.Diagnostics;
using System.Web.Script.Serialization;

namespace HISWebInterface
{

    public class LogInstance
    {

        private LogInstance() { }

        public static readonly LogInstance instance = new LogInstance();

        public int DEBUG_LV = 1;

       

        public string CLIENT_IP
        {
            get
            {
                try
                {
                    return "255.255.255.255";
                }
                catch (Exception ex)
                {
                    return "255.255.255.255";
                }
            }

        }



        public int Time = 0;


        public string LastErrorString;



        public string LastErrorCode;
      
        public string Ext_Error_Info;
      

        private void AppendFile(string file, string info)
        {
            try
            {
                StreamWriter sw;
                if (!File.Exists(file))
                {
                    sw = File.CreateText(file);
                }
                else
                {
                    sw = File.AppendText(file);
                }
                sw.WriteLine(info);
                sw.Close();
            }
            catch (Exception ex)
            {

            }
        }
  
        public void SendMQ(string info_tag, string info)
        {
             //SendMQP(info_tag, info);
        }

        private IDictionary SessionObj;

        public IDictionary Session
        {
            get { return SessionObj; }
            set { SessionObj = value; }
        }

        public string ROOT_PATH = "./";

        private const string LOGPATH = "LOGPATH";



        public string PATH;
   

        public string ERROR_PATH = "./Error";


        public void InitLogDirectory()
        {
            string month = DateTime.Now.ToString("yyyyMM");
            string day = DateTime.Now.ToString("yyyyMMdd");
            string month_path = "./Log/" + month;
   
            this.ROOT_PATH = System.IO.Directory.GetCurrentDirectory() + month_path + "/" + day;
            this.PATH = this.ROOT_PATH;
            this.ERROR_PATH = this.ROOT_PATH + "/Error";

            if (!Directory.Exists(PATH))
            {
                Directory.CreateDirectory(PATH);
            }
            if (!Directory.Exists(ERROR_PATH))
            {
                Directory.CreateDirectory(ERROR_PATH);
            }


        }


        public string GetLogFileName()
        {
            return this.CLIENT_IP + ".log";
        }

        public string GetLogFile()
        {
            return PATH + "/" + GetLogFileName();
        }

        public string GetSQLFile()
        {
            return ERROR_PATH + "/SQL.log";
        }

        public string GetErrorFile()
        {
            return ERROR_PATH + "/Debug.log";

        }

        public string GetWarnFile()
        {
            return ERROR_PATH + "/Warn.log";

        }
        public string GetXMLLog()
        {
            return ROOT_PATH + "/XML.txt";
        }

        public string GetExFile()
        {
            return PATH + "/ex_" + GetLogFileName();
        }

        public string GetOracleTestFile()
        {
            return ERROR_PATH + "/OracleTest_" + GetLogFileName();
        }


        public bool isLocalDebug()
        {
            if ((string.IsNullOrEmpty(CLIENT_IP) || CLIENT_IP == "127.0.0.1" || CLIENT_IP == "255.255.255.255" || CLIENT_IP == "172.16.118.86" || CLIENT_IP.IndexOf("172.18.170.") >= 0))
            {
                return true;
            }
            return false;
        }

        private string SetMoreInfo(string info, string memberName, string sourceFilePath, int sourceLineNumber)
        {
            string time = DateTime.Now.ToString("HH:mm:ss.fff");
            int t = System.Environment.TickCount;
            info = time + " " + (t - Time).ToString() + "ms\t" + Assembly.GetExecutingAssembly().GetName().Version.ToString() + "\t" + GetCallerInfo(memberName, sourceFilePath, sourceLineNumber) + info;
            Time = t;
            return info;
        }

        public string Object(object obj, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            JavaScriptSerializer js = new JavaScriptSerializer();
            string info = js.Serialize(obj);
            info = SetMoreInfo(info, memberName, sourceFilePath, sourceLineNumber);
            SendMQ("Log", info);
            return info;
        }

        /// <summary>
        /// 单纯记录日志
        /// </summary>
        /// <param name="info"></param>
        /// <param name="memberName"></param>
        /// <param name="sourceFilePath"></param>
        /// <param name="sourceLineNumber"></param>
        /// <returns></returns>
        public string Info(string info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            info = SetMoreInfo(info, memberName, sourceFilePath, sourceLineNumber);
            SendMQ("Log", info);
            AppendFile(GetLogFile(), info);
            return info;
        }




        /// <summary>
        /// 记录出错信息，调试模式下，最后一次Info信息会返回给调用者
        /// </summary>
        /// <param name="info"></param>
        /// <param name="memberName"></param>
        /// <param name="sourceFilePath"></param>
        /// <param name="sourceLineNumber"></param>
        public void Debug(string info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            info = "程序错误!" +  ":" + info;
            info = SetMoreInfo(info, memberName, sourceFilePath, sourceLineNumber);
            SendMQ("Log", info);
            SendMQ("Debug", info);

            AppendFile(GetLogFile(), info);
            AppendFile(GetErrorFile(), info);

        }

        public void Warn(string info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            info = "警告!" + ":" + info;
            info = SetMoreInfo(info, memberName, sourceFilePath, sourceLineNumber);
            SendMQ("Log", info);
            SendMQ("Warn", info);

            AppendFile(GetLogFile(), info);
            AppendFile(GetWarnFile(), info);
        }

        public void SQL(string info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            info =  info + "\n";
            info = SetMoreInfo(info, memberName, sourceFilePath, sourceLineNumber);
            SendMQ("SQL", info);
            AppendFile(GetSQLFile(), info);
        }



        public string SystemInfo(string info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            info = SetMoreInfo(info, memberName, sourceFilePath, sourceLineNumber);
            SendMQ("System", info);
            return info;
        }


        public void WriteXMLLog(string xml, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            return;
            xml = SetMoreInfo(xml, memberName, sourceFilePath, sourceLineNumber);
            SendMQ("XML", xml);
            AppendFile(GetXMLLog(), xml);
        }


        public string GetCallerInfo(string memberName = "", string sourceFilePath = "", int sourceLineNumber = 0)
        {
            string[] paths = sourceFilePath.Split('\\');

            string file = "";
            if (paths.Length > 0)
            {
                file = paths[paths.Length - 1];
            }
            if (file != "Log.cs")
            {
                return file + ":" + sourceLineNumber.ToString() + ":" + memberName + "\t";
            }
            else
            {

                return "";
            }

        }



    }

    public class Log
    {

        public static void InitLogDirectory()
        {
            LogInstance.instance.InitLogDirectory();
        }

        public static string Ext_Error_Info
        {
            get { return LogInstance.instance.Ext_Error_Info; }
            set { LogInstance.instance.Ext_Error_Info = value; }
        }



        public static string LastErrorString
        {
            get { return LogInstance.instance.LastErrorString; }
            set { LogInstance.instance.LastErrorString = value; }
        }


        public static string LastErrorCode
        {
            get { return LogInstance.instance.LastErrorCode; }
            set { LogInstance.instance.LastErrorCode = value; }
        }




        public static bool isLocalDebug()
        {
            return LogInstance.instance.isLocalDebug();
        }

        public static void Object(object info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            LogInstance.instance.Object(info, memberName, sourceFilePath, sourceLineNumber);

        }

        public static void Assert(bool test, string info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            if (!test)
                LogInstance.instance.Info(info, memberName, sourceFilePath, sourceLineNumber);
        }


        /// <summary>
        /// 单纯记录日志
        /// </summary>
        /// <param name="info"></param>
        /// <param name="memberName"></param>
        /// <param name="sourceFilePath"></param>
        /// <param name="sourceLineNumber"></param>
        /// <returns></returns>
        public static void Info(string info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            LogInstance.instance.Info(info, memberName, sourceFilePath, sourceLineNumber);
        }
        /// <summary>
        /// 记录出错信息，最后一次Info信息会返回给调用者
        /// </summary>
        /// <param name="info"></param>
        /// <param name="memberName"></param>
        /// <param name="sourceFilePath"></param>
        /// <param name="sourceLineNumber"></param>
        public static void Debug(string info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            LogInstance.instance.Debug(info, memberName, sourceFilePath, sourceLineNumber);
        }

        public static void Warn(string info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            LogInstance.instance.Warn(info, memberName, sourceFilePath, sourceLineNumber);
        }
        public static void SQL(string info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            LogInstance.instance.SQL(info, memberName, sourceFilePath, sourceLineNumber);
        }



        public static void SystemInfo(string info, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            LogInstance.instance.SystemInfo(info, memberName, sourceFilePath, sourceLineNumber);

        }


        public static void WriteXMLLog(string xml, [CallerMemberName] string memberName = "", [CallerFilePath] string sourceFilePath = "", [CallerLineNumber] int sourceLineNumber = 0)
        {
            LogInstance.instance.WriteXMLLog(xml, memberName, sourceFilePath, sourceLineNumber);

        }


        public static void ClearErrorCode()
        {
            LastErrorString = "成功";
            LastErrorCode = "1";
        }




        public static void WriteEventLog(string sEvent)
        {
            LogInstance.instance.SendMQ("Warn", sEvent);
        }
    }
}

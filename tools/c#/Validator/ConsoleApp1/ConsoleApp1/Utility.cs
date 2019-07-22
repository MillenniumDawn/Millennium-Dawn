using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Collections.Concurrent;

namespace Validator
{
    class Utility
    {
        public static String ReturnMatch(string text, string expr)
        {
            Regex regex = new Regex(@expr);
            Match match = regex.Match(text);

            if (match.Success)
            {
                // Finally, we get the Group value and display it.
                return match.Value;
            }
            else
            {
                return null;
            }
        }

        public static void PullDataNew(string dir, string regex, List<string> variable, int braceCheck)
        {
            foreach (string file in Directory.GetFiles(dir))
            {
                int brace = 0;

                using (FileStream fs = File.Open(file, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (BufferedStream bs = new BufferedStream(fs))
                using (StreamReader sr = new StreamReader(bs))
                {
                    string line;
                    while ((line = sr.ReadLine()) != null)
                    {
                        if (line.StartsWith("#") == false)
                        {
                            if (line.Contains("{") | line.Contains("}"))
                            {
                                if (brace == braceCheck)
                                {

                                    var match = Regex.Match(line, regex);
                                    if (match.Success)
                                        variable.Add(match.Groups[1].Value);


                                }
                                if (line.Contains("#"))
                                {
                                    if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                    {
                                        brace += line.Count(f => f == '{');
                                        brace -= line.Count(f => f == '}');
                                    }
                                }
                                else
                                {
                                    brace += line.Count(f => f == '{');
                                    brace -= line.Count(f => f == '}');
                                }

                            }
                        }
                    }
                }
            }
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }
        public static void PullData(string dir, string regex, List<string> variable, int braceCheck)
        {
            foreach (string file in Directory.GetFiles(dir))
            {
                int brace = 0;
                string[] lines = File.ReadAllLines(file);
                foreach (string line in lines)
                {
                    if (line.StartsWith("#") == false)
                    {
                        if (line.Contains("{") | line.Contains("}"))
                        {
                            if (brace == braceCheck)
                            {

                                var match = Regex.Match(line, regex);
                                if (match.Success)
                                    variable.Add(match.Groups[1].Value);


                            }
                            if (line.Contains("#"))
                            {
                                if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                {
                                    brace += line.Count(f => f == '{');
                                    brace -= line.Count(f => f == '}');
                                }
                            }
                            else
                            {
                                brace += line.Count(f => f == '{');
                                brace -= line.Count(f => f == '}');
                            }

                        }
                    }
                }

            }
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }

        public static void PullDatap(string dir, string regex, BlockingCollection<string> variable, int braceCheck)
        {
            string[] file = Directory.GetFiles(dir);
            Parallel.For(0, file.Count(), i =>
            {
                int brace = 0;
                string[] lines = File.ReadAllLines(file[i]);

                foreach (string line in lines)
                {
                    if (line.StartsWith("#") == false)
                    {
                        if (line.Contains("{") | line.Contains("}"))
                        {
                            if (brace == braceCheck)
                            {

                                var match = Regex.Match(line, regex);
                                if (match.Success)
                                    variable.Add(match.Groups[1].Value);


                            }
                            if (line.Contains("#"))
                            {
                                if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                {
                                    brace += line.Count(f => f == '{');
                                    brace -= line.Count(f => f == '}');
                                }
                            }
                            else
                            {
                                brace += line.Count(f => f == '{');
                                brace -= line.Count(f => f == '}');
                            }

                        }
                    }
                }

            });
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }
        public static void PullDatapNew(string dir, string regex, BlockingCollection<string> variable, int braceCheck)
        {
            string[] file = Directory.GetFiles(dir);
            Parallel.For(0, file.Count(), i =>
            {
                int brace = 0;
                using (FileStream fs = File.Open(file[i], FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (BufferedStream bs = new BufferedStream(fs))
                using (StreamReader sr = new StreamReader(bs))
                {
                    string line;
                    while ((line = sr.ReadLine()) != null)
                    {
                        if (line.StartsWith("#") == false)
                        {
                            if (line.Contains("{") | line.Contains("}"))
                            {
                                if (brace == braceCheck)
                                {

                                    var match = Regex.Match(line, regex);
                                    if (match.Success)
                                        variable.Add(match.Groups[1].Value);


                                }
                                if (line.Contains("#"))
                                {
                                    if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                    {
                                        brace += line.Count(f => f == '{');
                                        brace -= line.Count(f => f == '}');
                                    }
                                }
                                else
                                {
                                    brace += line.Count(f => f == '{');
                                    brace -= line.Count(f => f == '}');
                                }

                            }
                        }
                    }
                }
            });
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }


        public static void PullData2(string dir, string regex, List<string> variable, int braceCheck)
        {
            foreach (string file in Directory.GetFiles(dir))
            {
                int brace = 0;
                string[] lines = File.ReadAllLines(file);
                foreach (string line in lines)
                {
                    if (line.StartsWith("#") == false)
                    {


                        if (brace == braceCheck)
                        {

                            var match = Regex.Match(line, regex);
                            if (match.Success)
                                variable.Add(match.Groups[1].Value);


                        }
                        if (line.Contains("{") | line.Contains("}"))
                        {
                            if (line.Contains("#"))
                            {
                                if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                {
                                    brace += line.Count(f => f == '{');
                                    brace -= line.Count(f => f == '}');
                                }
                            }
                            else
                            {
                                brace += line.Count(f => f == '{');
                                brace -= line.Count(f => f == '}');
                            }

                        }
                    }
                }

            }
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }
        public static void PullData2New(string dir, string regex, List<string> variable, int braceCheck)
        {
            foreach (string file in Directory.GetFiles(dir))
            {
                int brace = 0;
                using (FileStream fs = File.Open(file, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (BufferedStream bs = new BufferedStream(fs))
                using (StreamReader sr = new StreamReader(bs))
                {
                    string line;
                    while ((line = sr.ReadLine()) != null)
                    {
                        if (line.StartsWith("#") == false)
                        {


                            if (brace == braceCheck)
                            {

                                var match = Regex.Match(line, regex);
                                if (match.Success)
                                    variable.Add(match.Groups[1].Value);


                            }
                            if (line.Contains("{") | line.Contains("}"))
                            {
                                if (line.Contains("#"))
                                {
                                    if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                    {
                                        brace += line.Count(f => f == '{');
                                        brace -= line.Count(f => f == '}');
                                    }
                                }
                                else
                                {
                                    brace += line.Count(f => f == '{');
                                    brace -= line.Count(f => f == '}');
                                }

                            }
                        }
                    }
                }
                
            }
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }
        
        public static void PullData2p(string dir, string regex, BlockingCollection<string> variable, int braceCheck)
        {
            string[] file = Directory.GetFiles(dir);
            Parallel.For(0, file.Count(), i =>
            {
                int brace = 0;
                string[] lines = File.ReadAllLines(file[i]);
                foreach (string line in lines)
                {
                    if (line.StartsWith("#") == false)
                    {


                        if (brace == braceCheck)
                        {

                            var match = Regex.Match(line, regex);
                            if (match.Success)
                                variable.Add(match.Groups[1].Value);


                        }
                        if (line.Contains("{") | line.Contains("}"))
                        {
                            if (line.Contains("#"))
                            {
                                if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                {
                                    brace += line.Count(f => f == '{');
                                    brace -= line.Count(f => f == '}');
                                }
                            }
                            else
                            {
                                brace += line.Count(f => f == '{');
                                brace -= line.Count(f => f == '}');
                            }

                        }
                    }
                }

            });
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }
        public static void PullData2pNew(string dir, string regex, BlockingCollection<string> variable, int braceCheck)
        {
            string[] file = Directory.GetFiles(dir);
            Parallel.For(0, file.Count(), i =>
            {
                int brace = 0;
                using (FileStream fs = File.Open(file[i], FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (BufferedStream bs = new BufferedStream(fs))
                using (StreamReader sr = new StreamReader(bs))
                {
                    string line;
                    while ((line = sr.ReadLine()) != null)
                    {
                        if (line.StartsWith("#") == false)
                        {


                            if (brace == braceCheck)
                            {

                                var match = Regex.Match(line, regex);
                                if (match.Success)
                                    variable.Add(match.Groups[1].Value);


                            }
                            if (line.Contains("{") | line.Contains("}"))
                            {
                                if (line.Contains("#"))
                                {
                                    if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                    {
                                        brace += line.Count(f => f == '{');
                                        brace -= line.Count(f => f == '}');
                                    }
                                }
                                else
                                {
                                    brace += line.Count(f => f == '{');
                                    brace -= line.Count(f => f == '}');
                                }

                            }
                        }
                    }
                }
                
            });
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }
        

        public static void PullData2(string dir, string regex, List<string> variable, int braceCheck, string keyWord)
        {
            foreach (string file in Directory.GetFiles(dir))
            {
                int brace = 0;
                string[] lines = File.ReadAllLines(file);
                foreach (string line in lines)
                {
                    if (line.StartsWith("#") == false)
                    {

                        
                        if (brace == braceCheck)
                        {
                            if (line.Contains(keyWord))
                            {
                                var match = Regex.Match(line, regex);
                                if (match.Success)
                                    variable.Add(match.Groups[1].Value);


                            }
                            
                            if (line.Contains("{") | line.Contains("}"))
                            {
                                if (line.Contains("#"))
                                {
                                    if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                    {
                                        brace += line.Count(f => f == '{');
                                        brace -= line.Count(f => f == '}');
                                    }
                                }
                                else
                                {
                                    brace += line.Count(f => f == '{');
                                    brace -= line.Count(f => f == '}');
                                }

                            }
                        }
                    }
                }

            }
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }
        public static void PullData2New(string dir, string regex, List<string> variable, int braceCheck, string keyWord)
        {

            foreach (string file in Directory.GetFiles(dir))
            {
                int brace = 0;
                using (FileStream fs = File.Open(file, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (BufferedStream bs = new BufferedStream(fs))
                using (StreamReader sr = new StreamReader(bs))
                {
                    string line;
                    while ((line = sr.ReadLine()) != null)
                    {
                        if (line.StartsWith("#") == false)
                        {


                            if (brace == braceCheck)
                            {
                                if (line.Contains(keyWord))
                                {
                                    var match = Regex.Match(line, regex);
                                    if (match.Success)
                                        variable.Add(match.Groups[1].Value);


                                }

                                if (line.Contains("{") | line.Contains("}"))
                                {
                                    if (line.Contains("#"))
                                    {
                                        if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                        {
                                            brace += line.Count(f => f == '{');
                                            brace -= line.Count(f => f == '}');
                                        }
                                    }
                                    else
                                    {
                                        brace += line.Count(f => f == '{');
                                        brace -= line.Count(f => f == '}');
                                    }

                                }
                            }
                        }
                    }
                }
            }
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }

        public static void PullData2p(string dir, string regex, BlockingCollection<string> variable, int braceCheck, string keyWord)
        {
            string[] file = Directory.GetFiles(dir);
            Parallel.For(0, file.Count(), i =>
            {
                int brace = 0;
                string[] lines = File.ReadAllLines(file[i]);
                
                foreach (string line in lines)
                {
                    if (line.StartsWith("#") == false)
                    {

                        
                        if (brace == braceCheck)
                        {
                            if (line.Contains(keyWord))
                            {
                                var match = Regex.Match(line, regex);
                                if (match.Success)
                                    variable.Add(match.Groups[1].Value);


                            }
                            
                            if (line.Contains("{") | line.Contains("}"))
                            {
                                if (line.Contains("#"))
                                {
                                    if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                    {
                                        brace += line.Count(f => f == '{');
                                        brace -= line.Count(f => f == '}');
                                    }
                                }
                                else
                                {
                                    brace += line.Count(f => f == '{');
                                    brace -= line.Count(f => f == '}');
                                }

                            }
                        }
                    }
                }

            });
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }
        public static void PullData2pNew(string dir, string regex, BlockingCollection<string> variable, int braceCheck, string keyWord)
        {
            string[] file = Directory.GetFiles(dir);
            Parallel.For(0, file.Count(), i =>
            {
                int brace = 0;
                using (FileStream fs = File.Open(file[i], FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                using (BufferedStream bs = new BufferedStream(fs))
                using (StreamReader sr = new StreamReader(bs))
                {
                    string line;
                    while ((line = sr.ReadLine()) != null)
                    {
                        if (line.StartsWith("#") == false)
                        {


                            if (brace == braceCheck)
                            {
                                if (line.Contains(keyWord))
                                {
                                    var match = Regex.Match(line, regex);
                                    if (match.Success)
                                        variable.Add(match.Groups[1].Value);


                                }

                                if (line.Contains("{") | line.Contains("}"))
                                {
                                    if (line.Contains("#"))
                                    {
                                        if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                        {
                                            brace += line.Count(f => f == '{');
                                            brace -= line.Count(f => f == '}');
                                        }
                                    }
                                    else
                                    {
                                        brace += line.Count(f => f == '{');
                                        brace -= line.Count(f => f == '}');
                                    }

                                }
                            }
                        }
                    }
                }
            });
            //foreach (string line in variable)
            //{
            //    Console.WriteLine(line);
            //}
            //Console.ReadKey();
        }
        

    }

}

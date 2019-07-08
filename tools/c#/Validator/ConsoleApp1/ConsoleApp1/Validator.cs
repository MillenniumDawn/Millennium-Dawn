using System;
using System.IO;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using System.Linq;

namespace Validator
{
    public class Mod
    {
        protected String rootdir;
        protected List<String> allTags = new List<String>();
        protected List<String> errors = new List<String>();
        protected List<String> minorErrors = new List<String>();
        protected List<String> ideologies = new List<String>();

        
        public Mod(String _rootDir)
        {
            rootdir = _rootDir;
        }

        #region return functions
        public String GetRootDir()
        {
            return rootdir;
        }
        public List<String> GetAllTags()
        {
            return allTags;
        }
        public List<String> GetErrors()
        {
            return errors;
        }
        public List<String> GetMinorErrors()
        {
            return minorErrors;
        }
        #endregion

        public void PopulateTags()
        {
            var file = rootdir + "\\common\\country_tags\\00_countries.txt";
            // Read a text file line by line.  
            string[] lines = File.ReadAllLines(file);

            foreach (string line in lines)
                if (returnMatch(line, "^[A-Z]{3}") != null)
                    allTags.Add(returnMatch(line, "^[A-Z]{3}"));
            ValidateTags();
        }
        private void ValidateTags()
        {

            var dir = rootdir + "\\history\\countries\\";
            List<String> tempTags = new List<String>();
            tempTags = allTags;
            string temp = "";

            foreach (string file in Directory.GetFiles(dir))
            {
                temp = returnMatch(Path.GetFileName(file), "^[A-Z]{3}");
                if (temp != null | temp != "")
                {
                    if (tempTags.Contains(temp))
                    {
                        tempTags.Remove(temp);
                        if (tempTags.Contains(temp))
                        {
                            Console.WriteLine(temp);
                            errors.Add($"Duplicate tag: {temp} found in \\common\\country_tags\\00_countries.txt");
                            Console.ReadKey();
                        }
                    }
                    else
                    {

                        minorErrors.Add($"Tag: {temp} has a \\history\\countries\\ file but no entry in \\common\\country_tags\\00_countries.txt");
                    }
                }
            }
            foreach (string tag in tempTags)
            {
                minorErrors.Add($"Tag: {tag} has a entry in \\common\\country_tags\\00_countries.txt but no \\history\\countries\\ file");
            }
        }

        public void PopulateIdeologies()
        {
            var file = rootdir + "\\common\\ideologies\\00_ideologies.txt";
            int brace = 0;
            string[] lines = File.ReadAllLines(file);

            foreach (string line in lines)
            {
                if (line.StartsWith("#") == false)
                {
                    if (line.Contains("{") | line.Contains("}"))
                    {
                        if (brace == 1)
                        {
                            var match = Regex.Match(line, @"^\s?([\w]+)\s?=");
                            if (match.Success)
                                ideologies.Add(match.Groups[1].Value);

                        }
                        if (returnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                        {
                            brace += line.Count(f => f == '{');
                            brace -= line.Count(f => f == '}');
                        }

                        
                    }
                }
            }
        }

        public void CheckIfFlagExists()
        {

        }

        private String returnMatch(string text, string expr)
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



    }
    

    class Program
    {
        static void Main(string[] args)
        {

            var watch = new System.Diagnostics.Stopwatch();
            watch.Start();
            var path = Directory.GetCurrentDirectory();
            for (int i = 0; i < 4; i++)
            {
                path = Path.GetDirectoryName(Path.GetDirectoryName(path));
            }
            Mod mod = new Mod(path);

            mod.PopulateTags();
            mod.PopulateIdeologies();

            foreach (string error in mod.GetMinorErrors())
            {
                Console.WriteLine(error);
            }
            foreach (string error in mod.GetErrors())
            {
                Console.WriteLine(error);
            }
            watch.Stop();

            Console.WriteLine($"Execution Time: {watch.ElapsedMilliseconds} ms");

        }
    }
}

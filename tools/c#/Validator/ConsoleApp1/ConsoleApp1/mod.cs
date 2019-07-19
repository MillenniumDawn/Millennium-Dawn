using System;
using System.IO;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using System.Linq;
using Validator.Structs;
using System.Threading.Tasks;
using System.Collections.Concurrent;

namespace Validator
{
    public class Mod : ICloneable
    {
        protected String rootdir;
        protected List<String> allTags = new List<String>();
        protected List<String> errors = new List<String>();
        protected List<String> minorErrors = new List<String>();
        protected List<Ideology> ideologies = new List<Ideology>();
        protected List<String> ideas = new List<String>();
        protected List<String> technologies = new List<String>();
        protected List<String> techSharingGroups = new List<String>();
        protected List<String> opinionModifiers = new List<String>();
        protected List<String> traits = new List<String>();
        protected List<String> scriptedEffects = new List<String>();
        protected List<String> scripteTriggers = new List<String>();
        protected List<String> nationalFocus = new List<String>();
        protected List<State> states = new List<State>();


        protected BlockingCollection<String> allTags2 = new BlockingCollection<String>();
        protected BlockingCollection<String> errors2 = new BlockingCollection<String>();
        protected BlockingCollection<String> minorErrors2 = new BlockingCollection<String>();
        protected BlockingCollection<Ideology> ideologies2 = new BlockingCollection<Ideology>();
        protected BlockingCollection<String> ideas2 = new BlockingCollection<String>();
        protected BlockingCollection<String> technologies2 = new BlockingCollection<String>();
        protected BlockingCollection<String> techSharingGroups2 = new BlockingCollection<String>();
        protected BlockingCollection<String> opinionModifiers2 = new BlockingCollection<String>();
        protected BlockingCollection<String> traits2 = new BlockingCollection<String>();
        protected BlockingCollection<String> scriptedEffects2 = new BlockingCollection<String>();
        protected BlockingCollection<String> scripteTriggers2 = new BlockingCollection<String>();
        protected BlockingCollection<String> nationalFocus2 = new BlockingCollection<String>();
        protected BlockingCollection<State> states2 = new BlockingCollection<State>();

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

        #region Pupulate functions
        public void PopulateTags()
        {
            var file = rootdir + "\\common\\country_tags\\00_countries.txt";
            // Read a text file line by line.  
            string[] lines = File.ReadAllLines(file);

            foreach (string line in lines)
                if (Utility.ReturnMatch(line, "^[A-Z]{3}") != null)
                    allTags.Add(Utility.ReturnMatch(line, "^[A-Z]{3}"));

            ValidateTags();
        }

        public void PopulateIdeologies()
        {
            var dir = rootdir + "\\common\\ideologies\\";
            foreach (string file in Directory.GetFiles(dir))
            {
                int brace = 0;
                bool isSubideology = false;

                string[] lines = File.ReadAllLines(file);

                foreach (string line in lines)
                {
                    if (line.StartsWith("#") == false)
                    {
                        if (line.Contains("{") | line.Contains("}"))
                        {
                            if (brace == 1)
                            {
                                var match = Regex.Match(line, @"^\s?([\w-]+)\s?=");
                                if (match.Success)
                                {
                                    ideologies.Add(new Ideology(match.Groups[1].Value));
                                }

                            }

                            if (isSubideology)
                            {
                                var match2 = Regex.Match(line, @"\s?([\w-]+)\s?=");
                                if (match2.Success)
                                {
                                    ideologies[ideologies.Count - 1].subIdeologies.Add(match2.Groups[1].Value);
                                }

                            }
                            if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                            {
                                brace += line.Count(f => f == '{');
                                brace -= line.Count(f => f == '}');
                                if (brace == 3 && line.Contains("types"))
                                    isSubideology = true;
                                if (brace == 2)
                                    isSubideology = false;
                            }


                        }
                    }
                }
            }
        }

        public void PopulateIdeas()
        {
            string dir = rootdir + "\\common\\ideas\\";
            Utility.PullData(dir, @"\s?([\w-_]+)\s?=", ideas, 2);


        }
        public void PopulateIdeas2()
        {
            string dir = rootdir + "\\common\\ideas\\";
            Utility.PullDatap(dir, @"\s?([\w-_]+)\s?=", ideas2, 2);


        }
        public void PopulateTechnologies()
        {
            string dir = rootdir + "\\common\\technologies\\";
            Utility.PullData(dir, @"\s?([\w-_]+)\s?=", technologies, 1);

        }
        public void PopulateTechnologies2()
        {
            string dir = rootdir + "\\common\\technologies\\";
            Utility.PullDatap(dir, @"\s?([\w-_]+)\s?=", technologies2, 1);

        }

        public void PopulateTechSharingGroups()
        {
            var dir = rootdir + "\\common\\technology_sharing\\";
            foreach (string file in Directory.GetFiles(dir))
            {
                int brace = 0;
                string[] lines = File.ReadAllLines(file);
                foreach (string line in lines)
                {
                    if (line.StartsWith("#") == false)
                    {
                        if (brace == 1) //slightly different as ID = name not ID = name  = {
                        {
                            var match = Regex.Match(line, @"^\s?id\s?=\s?([\w_]+)");
                            if (match.Success)
                                techSharingGroups.Add(match.Groups[1].Value);

                        }
                        if (line.Contains("{") | line.Contains("}"))
                        {
                            
                            if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                            {
                                brace += line.Count(f => f == '{');
                                brace -= line.Count(f => f == '}');
                            }

                        }
                    }
                }

            }
        }

        public void PopulateOppinionModifier()
        {
            string dir = rootdir + "\\common\\opinion_modifiers\\";
            Utility.PullData(dir, @"\s?([\w-_]+)\s?=", opinionModifiers, 1);
            
        }
        public void PopulateOppinionModifier2()
        {
            string dir = rootdir + "\\common\\opinion_modifiers\\";
            Utility.PullDatap(dir, @"\s?([\w-_]+)\s?=", opinionModifiers2, 1);
            
        }

        public void PopulateScriptedEffects()
        {
            string dir = rootdir + "\\common\\scripted_effects\\";
            Utility.PullData(dir, @"^\s?([\w-_]+)\s?=", scriptedEffects, 0);
        }
        public void PopulateScriptedEffects2()
        {
            string dir = rootdir + "\\common\\scripted_effects\\";
            Utility.PullDatap(dir, @"^\s?([\w-_]+)\s?=", scriptedEffects2, 0);
        }

        public void PopulateScriptedTriggers()
        {
            string dir = rootdir + "\\common\\scripted_triggers\\";
            Utility.PullData(dir, @"^\s?([\w-_]+)\s?=", scripteTriggers, 0);
        }
        public void PopulateScriptedTriggers2()
        {
            string dir = rootdir + "\\common\\scripted_triggers\\";
            Utility.PullDatap(dir, @"^\s?([\w-_]+)\s?=", scripteTriggers2, 0);
        }
        public void PopulateTraits()
        {
            string dir = rootdir + "\\common\\unit_leader\\";
            Utility.PullData(dir, @"^\s?([\w-_]+)\s?=", traits, 1);
            
            traits = traits.Where(w => !w.All(char.IsDigit))
               .ToList();

        }
        public void PopulateNationalFocus()
        {
            string dir = rootdir + "\\common\\national_focus\\";
            Utility.PullData2(dir, @"\s?\bid\b\s?=\s?([\w_]+)", nationalFocus, 2, "id");
        }

        public void clearAll()
        {

            allTags.Clear();
            ideologies.Clear();
            technologies.Clear();
            techSharingGroups.Clear();
            opinionModifiers.Clear();
            scriptedEffects.Clear();
            scripteTriggers.Clear();
            nationalFocus.Clear();
            states.Clear();
            errors.Clear();
            minorErrors.Clear();

            while (allTags2.TryTake(out _)) { }
            while (ideologies2.TryTake(out _)) { }
            while (technologies2.TryTake(out _)) { }
            while (techSharingGroups2.TryTake(out _)) { }
            while (opinionModifiers2.TryTake(out _)) { }
            while (scriptedEffects2.TryTake(out _)) { }
            while (scripteTriggers2.TryTake(out _)) { }
            while (nationalFocus2.TryTake(out _)) { }
            while (states2.TryTake(out _)) { }
            while (errors2.TryTake(out _)) { }
            while (minorErrors2.TryTake(out _)) { }
        }

        public void PopulateStates()
        {
            string dir = rootdir + "\\history\\states";


            foreach (string file in Directory.GetFiles(dir))
            {
                int brace = 0;
                bool isProvince = false;
                string[] lines = File.ReadAllLines(file);

                foreach (string line in lines)
                {
                    if (line.StartsWith("#") == false)
                    {
                        if (brace == 1)
                        {
                            if (line.Contains("id"))
                            {
                                var match = Regex.Match(line, @"\s?id\s?=\s?([0-9]+)+");
                                if (match.Success)
                                {
                                    states.Add(new State(match.Groups[1].Value));
                                }
                            }

                        }
                        if (line.Contains("{"))
                        {
                            if (line.Contains("#"))
                            {
                                if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                    brace += line.Count(f => f == '{');
                            }
                            else
                            {
                                brace += line.Count(f => f == '{');
                            }
                            if (brace == 2 && line.Contains("provinces"))
                                isProvince = true;
                        }

                        if (brace == 2 && isProvince)
                        {
                            Regex regex = new Regex(@"([0-9]+)");

                            foreach (Match match in regex.Matches(line))
                            {
                                states[states.Count - 1].provinces.Add(match.Value);
                            }
                        }

                        if (line.Contains("}"))
                        {
                            if (line.Contains("#"))
                            {
                                if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                    brace -= line.Count(f => f == '}');
                            }
                            else
                            {
                                brace -= line.Count(f => f == '}');
                            }
                            if (brace == 1)
                                isProvince = false;
                        }
                    }
                }
            }
            //for (int i = 0; i < states.Count; i++)
            //{
            //    Console.WriteLine($"~~~State: {states[i].ID} ~~~");
            //   for (int x = 0; x < states[i].provinces.Count; x++)
            //    {
            //        Console.WriteLine(states[i].provinces[x]);
            //    }
            //    Console.ReadKey();
            //}
            //Console.WriteLine(states.Count());

        }

        public void PopulateStates2()
        {
            string dir = rootdir + "\\history\\states";
            string[] file = Directory.GetFiles(dir);
            Parallel.For(0, Directory.GetFiles(dir).Count(), i =>
            {
                int brace = 0;
                bool isProvince = false;
                string[] lines = File.ReadAllLines(file[i]);
                State _state = new State("");
                foreach (string line in lines)
                {
                    if (line.StartsWith("#") == false)
                    {

                        if (brace == 1)
                        {
                            if (line.Contains("id"))
                            {
                                var match = Regex.Match(line, @"\s?id\s?=\s?([0-9]+)+");
                                if (match.Success)
                                {
                                    _state.ID = match.Groups[1].Value;
                                    //states.Add(new State(match.Groups[1].Value));
                                }
                            }
                            
                        }
                        if (line.Contains("{"))
                        {
                            if (line.Contains("#"))
                            {
                                if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                    brace += line.Count(f => f == '{');
                            }
                            else
                            {
                                brace += line.Count(f => f == '{');
                            }
                            if ( brace == 2 && line.Contains("provinces"))
                                isProvince = true;
                        }

                        if (brace == 2 && isProvince)
                        {
                            Regex regex = new Regex(@"([0-9]+)");

                            foreach (Match match in regex.Matches(line))
                            {
                                _state.provinces.Add(match.Value);
                                //states[states.Count - 1].provinces.Add(match.Value);
                            }
                        }

                        if (line.Contains("}"))
                        {
                            if (line.Contains("#"))
                            {
                                if (Utility.ReturnMatch(line, "#.*[{}]+") == null) //if the line doesn't have a comment before the open brace
                                    brace -= line.Count(f => f == '}');
                            }
                            else
                            {
                                brace -= line.Count(f => f == '}');
                            }
                            if (brace == 1)
                                isProvince = false;
                        }
                    }
                }
                if(_state.ID != "")
                    states2.Add(_state);
            });
            //Console.WriteLine(states2.Count());
            //for (int i = 0; i < states.Count; i++)
            //{
            //    Console.WriteLine($"~~~State: {states[i].ID} ~~~");
            //   for (int x = 0; x < states[i].provinces.Count; x++)
            //    {
            //        Console.WriteLine(states[i].provinces[x]);
            //    }
            //    Console.ReadKey();
            //}

        }
        #endregion


        private void ValidateTags()
        {

            var dir = rootdir + "\\history\\countries\\";
            List<String> tempTags = new List<String>();
            tempTags = Extensions.Clone(allTags);
            string temp = "";

            foreach (string file in Directory.GetFiles(dir))
            {
                temp = Utility.ReturnMatch(Path.GetFileName(file), "^[A-Z]{3}");
                if (temp != null | temp != "")
                {
                    if (tempTags.Contains(temp))
                    {
                        tempTags.Remove(temp);
                        if (tempTags.Contains(temp))
                        {
                            minorErrors.Add($"Duplicate tag: {temp} found in \\common\\country_tags\\00_countries.txt");
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

        public void CheckIfFlagExists()
        {
            string dir = "";

            
            Parallel.For(0, allTags.Count, j =>
            {
                String tag = allTags[j];
                for (int i = 0; i < ideologies.Count; i++)
                {
                    var ideology = ideologies[i].name;

                    dir = rootdir + "\\gfx\\flags\\" + tag + "_" + ideology + ".tga";
                    if (File.Exists(dir) == false)
                    {
                        minorErrors.Add($"{tag} is missing flag {dir}");
                    }
                    dir = rootdir + "\\gfx\\flags\\medium\\" + tag + "_" + ideology + ".tga";
                    if (File.Exists(dir) == false)
                    {
                        minorErrors.Add($"{tag} is missing flag {dir}");
                    }
                    dir = rootdir + "\\gfx\\flags\\small\\" + tag + "_" + ideology + ".tga";
                    if (File.Exists(dir) == false)
                    {
                        minorErrors.Add($"{tag} is missing flag {dir}");
                    }
                }

            });
        }

        public object Clone()
        {
            throw new NotImplementedException();
        }
    }
}

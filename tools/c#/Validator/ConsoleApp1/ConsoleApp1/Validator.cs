using System;
using System.IO;


namespace Validator
{
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

            mod.PopulateStates();

            mod.PopulateTraits();
            mod.PopulateNationalFocus();
            mod.PopulateIdeologies();
            mod.PopulateScriptedTriggers();
            mod.PopulateScriptedEffects();
            mod.PopulateOppinionModifier();
            mod.PopulateTechSharingGroups();
            mod.PopulateIdeas();
            mod.PopulateTechnologies();
            mod.PopulateTags();
            
            mod.CheckIfFlagExists();

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
            Console.ReadKey();

        }
    }
}

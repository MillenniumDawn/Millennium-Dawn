using System;
using System.IO;


namespace Validator
{
    class Program
    {
        static void Main(string[] args)
        {

            var watch = new System.Diagnostics.Stopwatch();
            
            var path = Directory.GetCurrentDirectory();
            for (int i = 0; i < 4; i++)
            {
                path = Path.GetDirectoryName(Path.GetDirectoryName(path));
            }
            Mod mod = new Mod(path);

            //warm up
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

            //single thread
            mod.clearAll();
            watch.Reset();
            watch.Start();
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

            watch.Stop();

            Console.WriteLine($"Single thread execution Time: {watch.ElapsedMilliseconds} ms");

            //multi thread
            mod.clearAll();
            watch.Reset();
            watch.Start();
            mod.PopulateStates2();
            mod.PopulateTraits();
            mod.PopulateNationalFocus();
            mod.PopulateIdeologies();
            mod.PopulateScriptedTriggers2();
            mod.PopulateScriptedEffects2();
            mod.PopulateOppinionModifier2();
            mod.PopulateTechSharingGroups();
            mod.PopulateIdeas2();
            mod.PopulateTechnologies2();
            mod.PopulateTags();
            mod.CheckIfFlagExists();
            watch.Stop();

            Console.WriteLine($"Multi thread execution Time: {watch.ElapsedMilliseconds} ms");




            Console.ReadKey();

            foreach (string error in mod.GetMinorErrors())
            {
                Console.WriteLine(error);
            }
            foreach (string error in mod.GetErrors())
            {
                Console.WriteLine(error);
            }
            

        }
    }
}

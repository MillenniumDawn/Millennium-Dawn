using System;
using System.IO;
using System.Threading;

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
            mod.clearAll();

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
            mod.clearAll();

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
            mod.clearAll();


            

            //single thread
            mod.clearAll();
            watch.Reset();
            watch.Start();
            mod.PopulateStates(); //slower than MT
            mod.PopulateTraits(); //faster than mt
            mod.PopulateNationalFocus(); //faster than mt
            mod.PopulateIdeologies(); //faster than mt
            mod.PopulateScriptedTriggers(); //same as MT
            mod.PopulateScriptedEffects(); //slower than MT
            mod.PopulateOppinionModifier(); //slower than MT
            mod.PopulateTechSharingGroups(); //faster than MT
            mod.PopulateIdeas(); //slower than MT
            mod.PopulateTechnologies(); //slower than MT
            mod.PopulateTags();
            mod.CheckIfFlagExists();

            watch.Stop();

            Console.WriteLine($"Single thread execution Time: {watch.ElapsedMilliseconds} ms");


            //ST threaded
            mod.clearAll();
            watch.Reset();
            watch.Start();
            Thread[] threadSingle = new Thread[11];
            threadSingle[0] = new Thread(new ThreadStart(mod.PopulateStates));
            threadSingle[1] = new Thread(new ThreadStart(mod.PopulateTraits));
            threadSingle[2] = new Thread(new ThreadStart(mod.PopulateNationalFocus));
            threadSingle[3] = new Thread(new ThreadStart(mod.PopulateIdeologies));
            threadSingle[4] = new Thread(new ThreadStart(mod.PopulateScriptedTriggers));
            threadSingle[5] = new Thread(new ThreadStart(mod.PopulateScriptedEffects));
            threadSingle[6] = new Thread(new ThreadStart(mod.PopulateOppinionModifier));
            threadSingle[7] = new Thread(new ThreadStart(mod.PopulateIdeas));
            threadSingle[8] = new Thread(new ThreadStart(mod.PopulateTechnologies));
            threadSingle[9] = new Thread(new ThreadStart(mod.PopulateTags));
            threadSingle[10] = new Thread(new ThreadStart(mod.PopulateIdeas));

            for (int i = 0; i < threadSingle.Length; i++)
            {
                threadSingle[i].Start();
            }
            for (int i = 0; i < threadSingle.Length; i++)
            {
                threadSingle[i].Join();
            }
            mod.CheckIfFlagExists();

            watch.Stop();

            Console.WriteLine($"ST threaded execution Time: {watch.ElapsedMilliseconds} ms");

            //multi thread
            mod.clearAll();
            watch.Reset();
            watch.Start();
            mod.PopulateStates2();
            mod.PopulateTraits2();
            mod.PopulateNationalFocus2();
            mod.PopulateIdeologies2();
            mod.PopulateScriptedTriggers2();
            mod.PopulateScriptedEffects2();
            mod.PopulateOppinionModifier2();
            mod.PopulateTechSharingGroups2();
            mod.PopulateIdeas2();
            mod.PopulateTechnologies2();
            mod.PopulateTags();
            mod.CheckIfFlagExists();
            watch.Stop();

            Console.WriteLine($"Multi thread execution Time: {watch.ElapsedMilliseconds} ms");

            //MT threaded
            mod.clearAll();
            watch.Reset();
            watch.Start();
            Thread[] threadMulti = new Thread[11];
            threadMulti[0] = new Thread(new ThreadStart(mod.PopulateStates2));
            threadMulti[1] = new Thread(new ThreadStart(mod.PopulateTraits2));
            threadMulti[2] = new Thread(new ThreadStart(mod.PopulateNationalFocus2));
            threadMulti[3] = new Thread(new ThreadStart(mod.PopulateIdeologies2));
            threadMulti[4] = new Thread(new ThreadStart(mod.PopulateScriptedTriggers2));
            threadMulti[5] = new Thread(new ThreadStart(mod.PopulateScriptedEffects2));
            threadMulti[6] = new Thread(new ThreadStart(mod.PopulateOppinionModifier2));
            threadMulti[7] = new Thread(new ThreadStart(mod.PopulateIdeas2));
            threadMulti[8] = new Thread(new ThreadStart(mod.PopulateTechnologies2));
            threadMulti[9] = new Thread(new ThreadStart(mod.PopulateTags));
            threadMulti[10] = new Thread(new ThreadStart(mod.PopulateIdeas2));

            for (int i = 0; i < threadMulti.Length; i++)
            {
                threadMulti[i].Start();
            }

            for (int i = 0; i < threadMulti.Length; i++)
            {
                threadMulti[i].Join();
            }
            mod.CheckIfFlagExists();

            watch.Stop();

            Console.WriteLine($"MT threaded execution Time: {watch.ElapsedMilliseconds} ms");


            //mixed
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

            Console.WriteLine($"mixed thread execution Time: {watch.ElapsedMilliseconds} ms");


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

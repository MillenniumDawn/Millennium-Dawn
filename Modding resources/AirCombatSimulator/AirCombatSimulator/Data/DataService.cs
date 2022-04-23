using AirCombatSimulator.Configuration;

namespace AirCombatSimulator.Data
{
    public class DataService
    {
        private const string DefinesFilename = "defines.txt";

        private readonly string appPath;

        public DataService()
        {
            appPath = AppDomain.CurrentDomain.BaseDirectory;
        }

        public Defines GetDefines()
        {
            var path = Path.Combine(appPath, DefinesFilename);
            if (ReaderWriter.Exists(path))
            {
                var data = ReaderWriter.Read(path);
                return JsonConverter.Deserialize<Defines>(data);
            }
            else
            {
                // default defines
                var defines = new Defines
                {
                    AirWingMaxSpeed = 1500,
                    BiggestAgilityFactorDiff = 2.5,
                    AirWingMaxStatsAgility = 100,
                    DefaultCarrierFactor = 0.1,
                    CombatDamageStatMultiplier = 0.3,
                    BaseDamageMultuplier = 0.01,
                    DetectChanceFromOccupation = 0.1,
                    DetectChanceFromRadars = 0.5,
                    DetectChanceFromAircrafts = 0.8,
                    DetectChanceFromAircraftsEffectiveCount = 3000
                };

                var serialized = JsonConverter.Serialize(defines);
                ReaderWriter.Write(path, serialized);

                return defines;
            }
        }
    }
}

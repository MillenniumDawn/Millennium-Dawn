using AirCombatSimulator.Configuration;
using AirCombatSimulator.Models;

namespace AirCombatSimulator.Data
{
    public class DataService
    {
        private const string DefinesFilename = "defines.txt";
        private const string PlanesFile = "planes.txt";

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
                    AirWingMaxSpeed = 4000,
                    BiggestAgilityFactorDiff = 5,
                    AirWingMaxStatsAgility = 999,
                    DefaultCarrierFactor = 0.1,
                    CombatDamageStatMultiplier = 0.2,
                    AgilityDamageReduction = 0.8,
                    BetterSpeedDamageIncrease = 0.6,
                    BaseDamageMultuplier = 0.01,
                    DetectChanceFromOccupation = 0.05,
                    DetectChanceFromRadars = 0.85,
                    DetectChanceFromAircrafts = 0.975,
                    DetectChanceFromAircraftsEffectiveCount = 3000,
                    SpeedFactorDiff = 2.5,
                    SpeedDamageBonusFactor = 0.025
                };

                var serialized = JsonConverter.Serialize(defines);
                ReaderWriter.Write(path, serialized);

                return defines;
            }
        }

        public List<Plane> GetPlanes()
        {
            var path = Path.Combine(appPath, PlanesFile);
            if (ReaderWriter.Exists(path))
            {
                var data = ReaderWriter.Read(path);
                return JsonConverter.Deserialize<List<Plane>>(data);
            }

            return new List<Plane>();
        }

        public void SavePlanes(List<Plane> planes)
        {
            var path = Path.Combine(appPath, PlanesFile);
            var data = JsonConverter.Serialize(planes);
            ReaderWriter.Write(path, data);
        }
    }
}

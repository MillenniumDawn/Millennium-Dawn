namespace AirCombatSimulator.Models
{
    public class CombatConfiguration
    {
        public CombatConfiguration()
        {
        }

        public CombatConfiguration(double detectChanceFromLandA, double radarCoverageA, double detectChanceFromLandB, double radarCoverageB)
        {
            DetectChanceFromLandA = detectChanceFromLandA;
            RadarCoverageA = radarCoverageA;
            DetectChanceFromLandB = detectChanceFromLandB;
            RadarCoverageB = radarCoverageB;
        }

        public double DetectChanceFromLandA { get; set; }
        public double RadarCoverageA { get; set; }
        public double DetectChanceFromLandB { get; set; }
        public double RadarCoverageB { get; set; }
    }
}

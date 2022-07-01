using AirCombatSimulator.Configuration;
using AirCombatSimulator.Models;

namespace AirCombatSimulator.Services
{
    public class CombatService
    {
        private const double AgilityStep = 0.675 / 1.5;

        private readonly Defines defines;

        public CombatService(Defines defines)
        {
            this.defines = defines;
        }

        public List<CombatResult> Simulate(AirWing a, AirWing b, CombatConfiguration configuration, int sorties = 100)
        {
            var result = new List<CombatResult>();

            for (int i = 0; i < sorties; i++)
            {
                double detectionA = CalculateDetection(a, configuration, true);
                double detectionB = CalculateDetection(b, configuration, false);

                int numberOfAttackersA = Convert.ToInt32(Math.Round(detectionA * b.Count));
                int numberOfAttackersB = Convert.ToInt32(Math.Round(detectionB * a.Count));

                numberOfAttackersA = Math.Clamp(numberOfAttackersA, 0, numberOfAttackersA * 3);
                numberOfAttackersB = Math.Clamp(numberOfAttackersB, 0, numberOfAttackersB * 3);

                double damageByA = defines.BaseDamageMultuplier * numberOfAttackersA * a.Plane.Attack / b.Plane.Defense
                    * (1 + CalulateStatsMultiplier(a, b)) * defines.DefaultCarrierFactor * (1 + CalculateAgilityDisadvantage(a, b));

                double damageByB = defines.BaseDamageMultuplier * numberOfAttackersB * b.Plane.Attack / a.Plane.Defense
                    * (1 + CalulateStatsMultiplier(b, a)) * defines.DefaultCarrierFactor * (1 + CalculateAgilityDisadvantage(b, a));

                var item = new CombatResult(damageByB, damageByA);
                result.Add(item);
            }

            return result;
        }

        private static double CalculateAgilityDisadvantage(AirWing a, AirWing b)
        {
            var modifier = Math.Clamp(b.Plane.Agility / a.Plane.Agility, 1, 2.5);
            return -(modifier - 1) * AgilityStep;
        }

        private double CalulateStatsMultiplier(AirWing a, AirWing b)
        {
            var diff = (a.Plane.Speed - b.Plane.Speed) / defines.AirWingMaxSpeed;
            diff += (a.Plane.Agility - b.Plane.Agility) / defines.AirWingMaxStatsAgility;
            diff = Math.Clamp(diff, -1, 1);
            return diff * defines.CombatDamageStatMultiplier;
        }

        private double CalculateDetection(AirWing a, CombatConfiguration combatConfiguration, bool useA)
        {
            var step = defines.DetectChanceFromAircrafts / defines.DetectChanceFromAircraftsEffectiveCount;
            var planeDetection = a.Count * step;

            if (useA)
            {
                planeDetection += combatConfiguration.DetectChanceFromLandA * defines.DetectChanceFromOccupation;
                planeDetection += combatConfiguration.RadarCoverageA * defines.DetectChanceFromRadars;
            }
            else
            {
                planeDetection += combatConfiguration.DetectChanceFromLandB * defines.DetectChanceFromOccupation;
                planeDetection += combatConfiguration.RadarCoverageB * defines.DetectChanceFromRadars;
            }

            return Math.Clamp(planeDetection, 0, 1);
        }
    }
}

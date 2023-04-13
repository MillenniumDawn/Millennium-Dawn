using AirCombatSimulator.Configuration;
using AirCombatSimulator.Models;

namespace AirCombatSimulator.Services
{
    public class CombatService
    {
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

                numberOfAttackersA = Math.Clamp(a.Count, 0, numberOfAttackersA * 3);
                numberOfAttackersB = Math.Clamp(b.Count, 0, numberOfAttackersB * 3);

                var damageByA = CalculateDamageForWing(a, b, numberOfAttackersA);
                var damageByB = CalculateDamageForWing(b, a, numberOfAttackersB);

                var item = new CombatResult(damageByB, damageByA);
                result.Add(item);
            }

            return result;
        }

        private double CalculateDamageForWing(AirWing a, AirWing b, int numberOfAttackersA)
        {
            double newDamageByA = CalculateBaseDamage(a, numberOfAttackersA);
            double agilityPenaltyForA = 0;
            if (a.Plane.Agility < b.Plane.Agility)
            {
                agilityPenaltyForA = CalculateAgilityDisadvantageNew(a, b, newDamageByA);
            }

            double speedBonus = 0;
            if (a.Plane.Speed > b.Plane.Speed)
            {
                speedBonus = CalculateRelativeSpeedBonus(a, b, newDamageByA);
                speedBonus += CalculateAbsoluteSpeedBonus(a, newDamageByA);
            }

            return defines.BaseDamageMultuplier * (newDamageByA - agilityPenaltyForA + speedBonus) / b.Plane.Defense;
        }

        private double CalculateAbsoluteSpeedBonus(AirWing a, double newDamageByA)
        {
            return newDamageByA * defines.SpeedDamageBonusFactor * a.Plane.Speed / defines.AirWingMaxSpeed;
        }

        private double CalculateRelativeSpeedBonus(AirWing a, AirWing b, double newDamageByA)
        {
            return newDamageByA * defines.BetterSpeedDamageIncrease * Math.Min((a.Plane.Speed - b.Plane.Speed) / b.Plane.Speed, defines.SpeedFactorDiff - 1);
        }

        private double CalculateAgilityDisadvantageNew(AirWing a, AirWing b, double newDamageByA)
        {
            return newDamageByA * defines.AgilityDamageReduction * Math.Min((b.Plane.Agility - a.Plane.Agility) / a.Plane.Agility, defines.BiggestAgilityFactorDiff - 1);
        }

        private double CalculateBaseDamage(AirWing attacker, int numberOfPlanes)
        {
            return numberOfPlanes * attacker.Plane.Attack * defines.CombatDamageStatMultiplier;
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

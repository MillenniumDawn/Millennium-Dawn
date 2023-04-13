namespace AirCombatSimulator.Configuration
{
    public class Defines
    {
        public double AirWingMaxSpeed { get; set; }
        public double AirWingMaxStatsAgility { get; set; }
        public double CombatDamageStatMultiplier { get; set; }
        public double DefaultCarrierFactor { get; set; }
        public double BiggestAgilityFactorDiff { get; set; }
        public double BaseDamageMultuplier { get; set; }

        public double DetectChanceFromOccupation { get; set; }
        public double DetectChanceFromRadars { get; set; }
        public double DetectChanceFromAircrafts { get; set; }
        public int DetectChanceFromAircraftsEffectiveCount { get; set; }
        public double AgilityDamageReduction { get; set; }
        public double BetterSpeedDamageIncrease { get; set; }
        public double SpeedFactorDiff { get; set; }
        public double SpeedDamageBonusFactor { get; set; }
    }
}

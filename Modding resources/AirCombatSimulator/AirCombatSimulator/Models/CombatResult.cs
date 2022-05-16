namespace AirCombatSimulator.Models
{
    public class CombatResult
    {
        public CombatResult()
        {
        }

        public CombatResult(double damageToA, double damageToB)
        {
            DamageToA = damageToA;
            DamageToB = damageToB;
        }

        public double DamageToA { get; set; }
        public double DamageToB { get; set; }
    }
}

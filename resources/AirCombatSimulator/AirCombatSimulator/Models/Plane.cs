namespace AirCombatSimulator.Models
{
    public class Plane
    {
        public Plane()
        {
        }

        public Plane(string name, double attack, double defense, double agility, double speed)
        {
            Name = name;
            Attack = attack;
            Defense = defense;
            Agility = agility;
            Speed = speed;
        }

        public string Name { get; set; }
        public double Attack { get; set; }
        public double Defense { get; set; }
        public double Agility { get; set; }
        public double Speed { get; set; }
    }
}

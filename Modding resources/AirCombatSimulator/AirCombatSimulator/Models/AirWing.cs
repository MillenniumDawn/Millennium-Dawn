namespace AirCombatSimulator.Models
{
    public class AirWing
    {
        public AirWing()
        {
        }

        public AirWing(Plane plane, int count)
        {
            Plane = plane;
            Count = count;
        }

        public Plane Plane { get; set; }
        public int Count { get; set; }
    }
}

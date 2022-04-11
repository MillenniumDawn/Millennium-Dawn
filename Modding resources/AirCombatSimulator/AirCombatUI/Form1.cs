using AirCombatSimulator.Data;
using AirCombatSimulator.Models;
using AirCombatSimulator.Services;
using System.Diagnostics;

namespace AirCombatUI
{
    public partial class MainUIForm : Form
    {
        private readonly CombatService combatService;

        public MainUIForm()
        {
            InitializeComponent();

            var dataService = new DataService();
            var defines = dataService.GetDefines();

            combatService = new CombatService(defines);
        }

        private void SimulateButton_Click(object sender, EventArgs e)
        {
            var watch = new Stopwatch();

            try
            {
                var planeA = ValidateAndCreatePlaneA();
                var wingA = ValidateAndCreateWingA(planeA);

                var planeB = ValidateAndCreatePlaneB();
                var wingB = ValidateAndCreateWingB(planeB);

                var config = ValidateAndCreateBattleConfig();

                var sorties = Validator.ValidateInt(SortiesNumber.Text, "Sortie count");
                Validator.ValidateRange(sorties, 1, int.MaxValue, "Sortie count");

                watch.Start();

                var result = combatService.Simulate(wingA, wingB, config, sorties);

                watch.Stop();

                double damageToA = result.Sum(x => x.DamageToA);
                double damageToB = result.Sum(x => x.DamageToB);

                ResultsLabel.Text = $"Damage to A planes: {damageToA}\nDamage to B planes: {damageToB}\nElapsed time: {watch.ElapsedMilliseconds} ms";
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                if (watch.IsRunning)
                {
                    watch.Stop();
                }

                watch.Reset();
            }
        }

        #region Private Methods

        private AirWing ValidateAndCreateWingB(Plane planeB)
        {
            var planeBCount = Validator.ValidateInt(PlaneCountBTextBox.Text, "Plane B count");
            Validator.ValidateRange(planeBCount, 1, int.MaxValue, "Plane B count");
            return new AirWing(planeB, planeBCount);
        }

        private AirWing ValidateAndCreateWingA(Plane planeA)
        {
            var planeACount = Validator.ValidateInt(PlaneCountATextBox.Text, "Plane A count");
            Validator.ValidateRange(planeACount, 1, int.MaxValue, "Plane A count");
            return new AirWing(planeA, planeACount);
        }

        private Plane ValidateAndCreatePlaneB()
        {
            var planeBAttack = Validator.ValidateDouble(PlaneBAttack.Text, "Plane B attack");
            var planeBDefense = Validator.ValidateDouble(PlaneBDefense.Text, "Plane B defense");
            var planeBSpeed = Validator.ValidateDouble(PlaneBSpeed.Text, "Plane B speed");
            var planeBAgility = Validator.ValidateDouble(PlaneBAgility.Text, "Plane B agility");

            var planeB = new Plane("plane B", planeBAttack, planeBDefense, planeBAgility, planeBSpeed);
            return planeB;
        }

        private CombatConfiguration ValidateAndCreateBattleConfig()
        {
            var wingBOccupation = Validator.ValidateDouble(OccupationBTextBox.Text, "Wing B occupation");
            Validator.ValidateRange(wingBOccupation, 0, 1, "Wing B occupation");
            var wingBRadar = Validator.ValidateDouble(RadarBTextBox.Text, "Wing B radar");
            Validator.ValidateRange(wingBRadar, 0, 1, "Wing B radar");
            var wingAOccupation = Validator.ValidateDouble(OccupationATextBox.Text, "Wing A occupation");
            Validator.ValidateRange(wingAOccupation, 0, 1, "Wing A occupation");
            var wingARadar = Validator.ValidateDouble(RadarATextBox.Text, "Wing A radar");
            Validator.ValidateRange(wingARadar, 0, 1, "Wing A radar");

            return new CombatConfiguration(wingAOccupation, wingARadar, wingBOccupation, wingBRadar);
        }

        private Plane ValidateAndCreatePlaneA()
        {
            var planeAAttack = Validator.ValidateDouble(PlaneAAttack.Text, "Plane A attack");
            var planeADefense = Validator.ValidateDouble(PlaneADefense.Text, "Plane A defense");
            var planeASpeed = Validator.ValidateDouble(PlaneASpeed.Text, "Plane A speed");
            var planeAAgility = Validator.ValidateDouble(PlaneAAgility.Text, "Plane A agility");

            var planeA = new Plane("plane A", planeAAttack, planeADefense, planeAAgility, planeASpeed);
            return planeA;
        }

        #endregion

        private void aboutToolStripMenuItem_Click(object sender, EventArgs e)
        {
            MessageBox.Show($"Hoi4 air combat simulator\nVersion {Program.Version}\nMade by crocomoth, 2022", "About",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
    }
}
using AirCombatSimulator.Data;
using AirCombatSimulator.Models;
using AirCombatSimulator.Services;
using System.Diagnostics;

namespace AirCombatUI
{
    public partial class MainUIForm : Form
    {
        private readonly CombatService combatService;
        private readonly DataService dataService;
        private readonly List<Plane> planes;

        public MainUIForm()
        {
            InitializeComponent();

            dataService = new DataService();
            planes = dataService.GetPlanes();

            foreach (var plane in planes)
            {
                PlaneAComboBox.Items.Add(plane.Name);
                PlaneBComboBox.Items.Add(plane.Name);
            }

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

            var planeB = new Plane(PlaneBNameTextBox.Text , planeBAttack, planeBDefense, planeBAgility, planeBSpeed);
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

            var planeA = new Plane(PlaneANameTextBox.Text, planeAAttack, planeADefense, planeAAgility, planeASpeed);
            return planeA;
        }

        #endregion

        private void aboutToolStripMenuItem_Click(object sender, EventArgs e)
        {
            MessageBox.Show($"Hoi4 air combat simulator\nVersion {Program.Version}\nMade by crocomoth, 2023", "About",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void label17_Click(object sender, EventArgs e)
        {
        }

        private void PlaneAComboBox_SelectedIndexChanged(object sender, EventArgs e)
        {
            var plane = planes.FirstOrDefault(x => x.Name.Equals(PlaneAComboBox.Text));
            if (plane is not null)
            {
                PlaneANameTextBox.Text = plane.Name;
                PlaneAAttack.Text = plane.Attack.ToString();
                PlaneADefense.Text = plane.Defense.ToString();
                PlaneASpeed.Text = plane.Speed.ToString();
                PlaneAAgility.Text = plane.Agility.ToString();
            }
        }

        private void PlaneBComboBox_SelectedIndexChanged(object sender, EventArgs e)
        {
            var plane = planes.FirstOrDefault(x => x.Name.Equals(PlaneBComboBox.Text));
            if (plane is not null)
            {
                PlaneBNameTextBox.Text = plane.Name;
                PlaneBAttack.Text = plane.Attack.ToString();
                PlaneBDefense.Text = plane.Defense.ToString();
                PlaneBSpeed.Text = plane.Speed.ToString();
                PlaneBAgility.Text = plane.Agility.ToString();
            }
        }

        private void SaveButton_Click(object sender, EventArgs e)
        {
            if (!string.IsNullOrWhiteSpace(PlaneANameTextBox.Text))
            {
                var existing = planes.FirstOrDefault(x => x.Name.Equals(PlaneANameTextBox.Text));
                var plane = ValidateAndCreatePlaneA();
                if (existing is not null)
                {
                    existing.Attack = plane.Attack;
                    existing.Defense = plane.Defense;
                    existing.Speed = plane.Speed;
                    existing.Agility = plane.Agility;
                }
                else
                {
                    planes.Add(plane);
                    PlaneAComboBox.Items.Add(plane.Name);
                    PlaneBComboBox.Items.Add(plane.Name);
                }
            }

            if (!string.IsNullOrWhiteSpace(PlaneBNameTextBox.Text))
            {
                var existing = planes.FirstOrDefault(x => x.Name.Equals(PlaneBNameTextBox.Text));
                var plane = ValidateAndCreatePlaneB();
                if (existing is not null)
                {
                    existing.Attack = plane.Attack;
                    existing.Defense = plane.Defense;
                    existing.Speed = plane.Speed;
                    existing.Agility = plane.Agility;
                }
                else
                {
                    planes.Add(plane);
                    PlaneAComboBox.Items.Add(plane.Name);
                    PlaneBComboBox.Items.Add(plane.Name);
                }
            }

            dataService.SavePlanes(planes);
        }

        private void DeleteButton_Click(object sender, EventArgs e)
        {
            if (!string.IsNullOrWhiteSpace(PlaneANameTextBox.Text))
            {
                var existing = planes.FirstOrDefault(x => x.Name.Equals(PlaneANameTextBox.Text));
                if (existing is not null)
                {
                    planes.Remove(existing);
                    PlaneAComboBox.Items.Remove(existing.Name);
                    PlaneBComboBox.Items.Remove(existing.Name);
                    PlaneANameTextBox.Text = string.Empty;
                    PlaneAAttack.Text = string.Empty;
                    PlaneADefense.Text = string.Empty;
                    PlaneASpeed.Text = string.Empty;
                    PlaneAAgility.Text = string.Empty;
                }
            }

            if (!string.IsNullOrWhiteSpace(PlaneBNameTextBox.Text))
            {
                var existing = planes.FirstOrDefault(x => x.Name.Equals(PlaneBNameTextBox.Text));
                if (existing is not null)
                {
                    planes.Remove(existing);
                    PlaneAComboBox.Items.Remove(existing.Name);
                    PlaneBComboBox.Items.Remove(existing.Name);
                    PlaneBNameTextBox.Text = string.Empty;
                    PlaneBAttack.Text = string.Empty;
                    PlaneBDefense.Text = string.Empty;
                    PlaneBSpeed.Text = string.Empty;
                    PlaneBAgility.Text = string.Empty;
                }
            }
        }
    }
}

namespace AirCombatUI
{
    partial class MainUIForm
    {
        /// <summary>
        ///  Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        ///  Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        ///  Required method for Designer support - do not modify
        ///  the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.PlaneAAttack = new System.Windows.Forms.TextBox();
            this.PlaneADefense = new System.Windows.Forms.TextBox();
            this.PlaneASpeed = new System.Windows.Forms.TextBox();
            this.PlaneAAgility = new System.Windows.Forms.TextBox();
            this.PlaneBAttack = new System.Windows.Forms.TextBox();
            this.PlaneBDefense = new System.Windows.Forms.TextBox();
            this.PlaneBSpeed = new System.Windows.Forms.TextBox();
            this.PlaneBAgility = new System.Windows.Forms.TextBox();
            this.SortiesNumber = new System.Windows.Forms.TextBox();
            this.SimulateButton = new System.Windows.Forms.Button();
            this.ResultsLabel = new System.Windows.Forms.Label();
            this.OccupationATextBox = new System.Windows.Forms.TextBox();
            this.RadarATextBox = new System.Windows.Forms.TextBox();
            this.OccupationBTextBox = new System.Windows.Forms.TextBox();
            this.RadarBTextBox = new System.Windows.Forms.TextBox();
            this.label1 = new System.Windows.Forms.Label();
            this.label2 = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.label4 = new System.Windows.Forms.Label();
            this.PlaneCountATextBox = new System.Windows.Forms.TextBox();
            this.PlaneCountBTextBox = new System.Windows.Forms.TextBox();
            this.label5 = new System.Windows.Forms.Label();
            this.label6 = new System.Windows.Forms.Label();
            this.label7 = new System.Windows.Forms.Label();
            this.label8 = new System.Windows.Forms.Label();
            this.label9 = new System.Windows.Forms.Label();
            this.label10 = new System.Windows.Forms.Label();
            this.label11 = new System.Windows.Forms.Label();
            this.label12 = new System.Windows.Forms.Label();
            this.label13 = new System.Windows.Forms.Label();
            this.label14 = new System.Windows.Forms.Label();
            this.label15 = new System.Windows.Forms.Label();
            this.menuStrip1 = new System.Windows.Forms.MenuStrip();
            this.menuToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.aboutToolStripMenuItem = new System.Windows.Forms.ToolStripMenuItem();
            this.PlaneANameTextBox = new System.Windows.Forms.TextBox();
            this.label16 = new System.Windows.Forms.Label();
            this.PlaneBNameTextBox = new System.Windows.Forms.TextBox();
            this.label17 = new System.Windows.Forms.Label();
            this.PlaneAComboBox = new System.Windows.Forms.ComboBox();
            this.PlaneBComboBox = new System.Windows.Forms.ComboBox();
            this.SaveButton = new System.Windows.Forms.Button();
            this.DeleteButton = new System.Windows.Forms.Button();
            this.menuStrip1.SuspendLayout();
            this.SuspendLayout();
            //
            // PlaneAAttack
            //
            this.PlaneAAttack.Location = new System.Drawing.Point(65, 189);
            this.PlaneAAttack.Name = "PlaneAAttack";
            this.PlaneAAttack.Size = new System.Drawing.Size(125, 27);
            this.PlaneAAttack.TabIndex = 0;
            //
            // PlaneADefense
            //
            this.PlaneADefense.Location = new System.Drawing.Point(65, 245);
            this.PlaneADefense.Name = "PlaneADefense";
            this.PlaneADefense.Size = new System.Drawing.Size(125, 27);
            this.PlaneADefense.TabIndex = 1;
            //
            // PlaneASpeed
            //
            this.PlaneASpeed.Location = new System.Drawing.Point(65, 298);
            this.PlaneASpeed.Name = "PlaneASpeed";
            this.PlaneASpeed.Size = new System.Drawing.Size(125, 27);
            this.PlaneASpeed.TabIndex = 2;
            //
            // PlaneAAgility
            //
            this.PlaneAAgility.Location = new System.Drawing.Point(66, 351);
            this.PlaneAAgility.Name = "PlaneAAgility";
            this.PlaneAAgility.Size = new System.Drawing.Size(125, 27);
            this.PlaneAAgility.TabIndex = 3;
            //
            // PlaneBAttack
            //
            this.PlaneBAttack.Location = new System.Drawing.Point(547, 189);
            this.PlaneBAttack.Name = "PlaneBAttack";
            this.PlaneBAttack.Size = new System.Drawing.Size(125, 27);
            this.PlaneBAttack.TabIndex = 7;
            //
            // PlaneBDefense
            //
            this.PlaneBDefense.Location = new System.Drawing.Point(547, 245);
            this.PlaneBDefense.Name = "PlaneBDefense";
            this.PlaneBDefense.Size = new System.Drawing.Size(125, 27);
            this.PlaneBDefense.TabIndex = 8;
            //
            // PlaneBSpeed
            //
            this.PlaneBSpeed.Location = new System.Drawing.Point(547, 298);
            this.PlaneBSpeed.Name = "PlaneBSpeed";
            this.PlaneBSpeed.Size = new System.Drawing.Size(125, 27);
            this.PlaneBSpeed.TabIndex = 9;
            //
            // PlaneBAgility
            //
            this.PlaneBAgility.Location = new System.Drawing.Point(547, 351);
            this.PlaneBAgility.Name = "PlaneBAgility";
            this.PlaneBAgility.Size = new System.Drawing.Size(125, 27);
            this.PlaneBAgility.TabIndex = 10;
            //
            // SortiesNumber
            //
            this.SortiesNumber.Location = new System.Drawing.Point(405, 351);
            this.SortiesNumber.Name = "SortiesNumber";
            this.SortiesNumber.Size = new System.Drawing.Size(125, 27);
            this.SortiesNumber.TabIndex = 14;
            //
            // SimulateButton
            //
            this.SimulateButton.Location = new System.Drawing.Point(416, 395);
            this.SimulateButton.Name = "SimulateButton";
            this.SimulateButton.Size = new System.Drawing.Size(94, 29);
            this.SimulateButton.TabIndex = 15;
            this.SimulateButton.Text = "Start";
            this.SimulateButton.UseVisualStyleBackColor = true;
            this.SimulateButton.Click += new System.EventHandler(this.SimulateButton_Click);
            //
            // ResultsLabel
            //
            this.ResultsLabel.AutoSize = true;
            this.ResultsLabel.Location = new System.Drawing.Point(432, 437);
            this.ResultsLabel.Name = "ResultsLabel";
            this.ResultsLabel.Size = new System.Drawing.Size(58, 20);
            this.ResultsLabel.TabIndex = 16;
            this.ResultsLabel.Text = "Results:";
            //
            // OccupationATextBox
            //
            this.OccupationATextBox.Location = new System.Drawing.Point(234, 245);
            this.OccupationATextBox.Name = "OccupationATextBox";
            this.OccupationATextBox.Size = new System.Drawing.Size(125, 27);
            this.OccupationATextBox.TabIndex = 5;
            //
            // RadarATextBox
            //
            this.RadarATextBox.Location = new System.Drawing.Point(234, 298);
            this.RadarATextBox.Name = "RadarATextBox";
            this.RadarATextBox.Size = new System.Drawing.Size(125, 27);
            this.RadarATextBox.TabIndex = 6;
            //
            // OccupationBTextBox
            //
            this.OccupationBTextBox.Location = new System.Drawing.Point(725, 245);
            this.OccupationBTextBox.Name = "OccupationBTextBox";
            this.OccupationBTextBox.Size = new System.Drawing.Size(125, 27);
            this.OccupationBTextBox.TabIndex = 12;
            //
            // RadarBTextBox
            //
            this.RadarBTextBox.Location = new System.Drawing.Point(725, 298);
            this.RadarBTextBox.Name = "RadarBTextBox";
            this.RadarBTextBox.Size = new System.Drawing.Size(125, 27);
            this.RadarBTextBox.TabIndex = 13;
            //
            // label1
            //
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(65, 162);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(51, 20);
            this.label1.TabIndex = 15;
            this.label1.Text = "Attack";
            //
            // label2
            //
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(65, 219);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(63, 20);
            this.label2.TabIndex = 16;
            this.label2.Text = "Defense";
            //
            // label3
            //
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(65, 275);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(51, 20);
            this.label3.TabIndex = 17;
            this.label3.Text = "Speed";
            //
            // label4
            //
            this.label4.AutoSize = true;
            this.label4.Location = new System.Drawing.Point(66, 328);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(52, 20);
            this.label4.TabIndex = 18;
            this.label4.Text = "Agility";
            //
            // PlaneCountATextBox
            //
            this.PlaneCountATextBox.Location = new System.Drawing.Point(234, 189);
            this.PlaneCountATextBox.Name = "PlaneCountATextBox";
            this.PlaneCountATextBox.Size = new System.Drawing.Size(125, 27);
            this.PlaneCountATextBox.TabIndex = 4;
            //
            // PlaneCountBTextBox
            //
            this.PlaneCountBTextBox.Location = new System.Drawing.Point(725, 189);
            this.PlaneCountBTextBox.Name = "PlaneCountBTextBox";
            this.PlaneCountBTextBox.Size = new System.Drawing.Size(125, 27);
            this.PlaneCountBTextBox.TabIndex = 11;
            //
            // label5
            //
            this.label5.AutoSize = true;
            this.label5.Location = new System.Drawing.Point(233, 162);
            this.label5.Name = "label5";
            this.label5.Size = new System.Drawing.Size(92, 20);
            this.label5.TabIndex = 21;
            this.label5.Text = "Planes count";
            //
            // label6
            //
            this.label6.AutoSize = true;
            this.label6.Location = new System.Drawing.Point(234, 219);
            this.label6.Name = "label6";
            this.label6.Size = new System.Drawing.Size(128, 20);
            this.label6.TabIndex = 22;
            this.label6.Text = "Occupation factor";
            //
            // label7
            //
            this.label7.AutoSize = true;
            this.label7.Location = new System.Drawing.Point(234, 275);
            this.label7.Name = "label7";
            this.label7.Size = new System.Drawing.Size(91, 20);
            this.label7.TabIndex = 23;
            this.label7.Text = "Radar factor";
            //
            // label8
            //
            this.label8.AutoSize = true;
            this.label8.Location = new System.Drawing.Point(548, 162);
            this.label8.Name = "label8";
            this.label8.Size = new System.Drawing.Size(51, 20);
            this.label8.TabIndex = 24;
            this.label8.Text = "Attack";
            //
            // label9
            //
            this.label9.AutoSize = true;
            this.label9.Location = new System.Drawing.Point(547, 219);
            this.label9.Name = "label9";
            this.label9.Size = new System.Drawing.Size(63, 20);
            this.label9.TabIndex = 25;
            this.label9.Text = "Defense";
            //
            // label10
            //
            this.label10.AutoSize = true;
            this.label10.Location = new System.Drawing.Point(547, 275);
            this.label10.Name = "label10";
            this.label10.Size = new System.Drawing.Size(51, 20);
            this.label10.TabIndex = 26;
            this.label10.Text = "Speed";
            //
            // label11
            //
            this.label11.AutoSize = true;
            this.label11.Location = new System.Drawing.Point(547, 328);
            this.label11.Name = "label11";
            this.label11.Size = new System.Drawing.Size(52, 20);
            this.label11.TabIndex = 27;
            this.label11.Text = "Agility";
            //
            // label12
            //
            this.label12.AutoSize = true;
            this.label12.Location = new System.Drawing.Point(725, 162);
            this.label12.Name = "label12";
            this.label12.Size = new System.Drawing.Size(92, 20);
            this.label12.TabIndex = 28;
            this.label12.Text = "Planes count";
            //
            // label13
            //
            this.label13.AutoSize = true;
            this.label13.Location = new System.Drawing.Point(725, 219);
            this.label13.Name = "label13";
            this.label13.Size = new System.Drawing.Size(128, 20);
            this.label13.TabIndex = 29;
            this.label13.Text = "Occupation factor";
            this.label13.Click += new System.EventHandler(this.label13_Click);
            //
            // label14
            //
            this.label14.AutoSize = true;
            this.label14.Location = new System.Drawing.Point(725, 275);
            this.label14.Name = "label14";
            this.label14.Size = new System.Drawing.Size(91, 20);
            this.label14.TabIndex = 30;
            this.label14.Text = "Radar factor";
            //
            // label15
            //
            this.label15.AutoSize = true;
            this.label15.Location = new System.Drawing.Point(415, 316);
            this.label15.Name = "label15";
            this.label15.Size = new System.Drawing.Size(95, 20);
            this.label15.TabIndex = 31;
            this.label15.Text = "Sorties count";
            //
            // menuStrip1
            //
            this.menuStrip1.ImageScalingSize = new System.Drawing.Size(20, 20);
            this.menuStrip1.Items.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.menuToolStripMenuItem});
            this.menuStrip1.Location = new System.Drawing.Point(0, 0);
            this.menuStrip1.Name = "menuStrip1";
            this.menuStrip1.Size = new System.Drawing.Size(1044, 28);
            this.menuStrip1.TabIndex = 32;
            this.menuStrip1.Text = "menuStrip1";
            //
            // menuToolStripMenuItem
            //
            this.menuToolStripMenuItem.DropDownItems.AddRange(new System.Windows.Forms.ToolStripItem[] {
            this.aboutToolStripMenuItem});
            this.menuToolStripMenuItem.Name = "menuToolStripMenuItem";
            this.menuToolStripMenuItem.Size = new System.Drawing.Size(60, 24);
            this.menuToolStripMenuItem.Text = "Menu";
            //
            // aboutToolStripMenuItem
            //
            this.aboutToolStripMenuItem.Name = "aboutToolStripMenuItem";
            this.aboutToolStripMenuItem.Size = new System.Drawing.Size(133, 26);
            this.aboutToolStripMenuItem.Text = "About";
            this.aboutToolStripMenuItem.Click += new System.EventHandler(this.aboutToolStripMenuItem_Click);
            //
            // PlaneANameTextBox
            //
            this.PlaneANameTextBox.Location = new System.Drawing.Point(65, 132);
            this.PlaneANameTextBox.Name = "PlaneANameTextBox";
            this.PlaneANameTextBox.Size = new System.Drawing.Size(125, 27);
            this.PlaneANameTextBox.TabIndex = 33;
            this.PlaneANameTextBox.TextChanged += new System.EventHandler(this.textBox1_TextChanged);
            //
            // label16
            //
            this.label16.AutoSize = true;
            this.label16.Location = new System.Drawing.Point(65, 100);
            this.label16.Name = "label16";
            this.label16.Size = new System.Drawing.Size(49, 20);
            this.label16.TabIndex = 34;
            this.label16.Text = "Name";
            //
            // PlaneBNameTextBox
            //
            this.PlaneBNameTextBox.Location = new System.Drawing.Point(548, 132);
            this.PlaneBNameTextBox.Name = "PlaneBNameTextBox";
            this.PlaneBNameTextBox.Size = new System.Drawing.Size(125, 27);
            this.PlaneBNameTextBox.TabIndex = 35;
            //
            // label17
            //
            this.label17.AutoSize = true;
            this.label17.Location = new System.Drawing.Point(551, 98);
            this.label17.Name = "label17";
            this.label17.Size = new System.Drawing.Size(49, 20);
            this.label17.TabIndex = 36;
            this.label17.Text = "Name";
            //
            // PlaneAComboBox
            //
            this.PlaneAComboBox.FormattingEnabled = true;
            this.PlaneAComboBox.Location = new System.Drawing.Point(65, 56);
            this.PlaneAComboBox.Name = "PlaneAComboBox";
            this.PlaneAComboBox.Size = new System.Drawing.Size(151, 28);
            this.PlaneAComboBox.TabIndex = 37;
            this.PlaneAComboBox.SelectedIndexChanged += new System.EventHandler(this.PlaneAComboBox_SelectedIndexChanged);
            //
            // PlaneBComboBox
            //
            this.PlaneBComboBox.FormattingEnabled = true;
            this.PlaneBComboBox.Location = new System.Drawing.Point(551, 56);
            this.PlaneBComboBox.Name = "PlaneBComboBox";
            this.PlaneBComboBox.Size = new System.Drawing.Size(151, 28);
            this.PlaneBComboBox.TabIndex = 38;
            this.PlaneBComboBox.SelectedIndexChanged += new System.EventHandler(this.PlaneBComboBox_SelectedIndexChanged);
            //
            // SaveButton
            //
            this.SaveButton.Location = new System.Drawing.Point(917, 55);
            this.SaveButton.Name = "SaveButton";
            this.SaveButton.Size = new System.Drawing.Size(94, 29);
            this.SaveButton.TabIndex = 39;
            this.SaveButton.Text = "Save";
            this.SaveButton.UseVisualStyleBackColor = true;
            this.SaveButton.Click += new System.EventHandler(this.SaveButton_Click);
            //
            // DeleteButton
            //
            this.DeleteButton.Location = new System.Drawing.Point(790, 56);
            this.DeleteButton.Name = "DeleteButton";
            this.DeleteButton.Size = new System.Drawing.Size(94, 29);
            this.DeleteButton.TabIndex = 40;
            this.DeleteButton.Text = "Delete";
            this.DeleteButton.UseVisualStyleBackColor = true;
            this.DeleteButton.Click += new System.EventHandler(this.DeleteButton_Click);
            //
            // MainUIForm
            //
            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 20F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1044, 541);
            this.Controls.Add(this.DeleteButton);
            this.Controls.Add(this.SaveButton);
            this.Controls.Add(this.PlaneBComboBox);
            this.Controls.Add(this.PlaneAComboBox);
            this.Controls.Add(this.label17);
            this.Controls.Add(this.PlaneBNameTextBox);
            this.Controls.Add(this.label16);
            this.Controls.Add(this.PlaneANameTextBox);
            this.Controls.Add(this.label15);
            this.Controls.Add(this.label14);
            this.Controls.Add(this.label13);
            this.Controls.Add(this.label12);
            this.Controls.Add(this.label11);
            this.Controls.Add(this.label10);
            this.Controls.Add(this.label9);
            this.Controls.Add(this.label8);
            this.Controls.Add(this.label7);
            this.Controls.Add(this.label6);
            this.Controls.Add(this.label5);
            this.Controls.Add(this.PlaneCountBTextBox);
            this.Controls.Add(this.PlaneCountATextBox);
            this.Controls.Add(this.label4);
            this.Controls.Add(this.label3);
            this.Controls.Add(this.label2);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.RadarBTextBox);
            this.Controls.Add(this.OccupationBTextBox);
            this.Controls.Add(this.RadarATextBox);
            this.Controls.Add(this.OccupationATextBox);
            this.Controls.Add(this.ResultsLabel);
            this.Controls.Add(this.SimulateButton);
            this.Controls.Add(this.SortiesNumber);
            this.Controls.Add(this.PlaneBAgility);
            this.Controls.Add(this.PlaneBSpeed);
            this.Controls.Add(this.PlaneBDefense);
            this.Controls.Add(this.PlaneBAttack);
            this.Controls.Add(this.PlaneAAgility);
            this.Controls.Add(this.PlaneASpeed);
            this.Controls.Add(this.PlaneADefense);
            this.Controls.Add(this.PlaneAAttack);
            this.Controls.Add(this.menuStrip1);
            this.MainMenuStrip = this.menuStrip1;
            this.Name = "MainUIForm";
            this.Text = "Air Combat Simulator";
            this.menuStrip1.ResumeLayout(false);
            this.menuStrip1.PerformLayout();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        private void textBox1_TextChanged(object sender, EventArgs e)
        {
        }

        private void label13_Click(object sender, EventArgs e)
        {
        }

        #endregion

        private TextBox PlaneAAttack;
        private TextBox PlaneADefense;
        private TextBox PlaneASpeed;
        private TextBox PlaneAAgility;
        private TextBox PlaneBAttack;
        private TextBox PlaneBDefense;
        private TextBox PlaneBSpeed;
        private TextBox PlaneBAgility;
        private TextBox SortiesNumber;
        private Button SimulateButton;
        private Label ResultsLabel;
        private TextBox OccupationATextBox;
        private TextBox RadarATextBox;
        private TextBox OccupationBTextBox;
        private TextBox RadarBTextBox;
        private Label label1;
        private Label label2;
        private Label label3;
        private Label label4;
        private TextBox PlaneCountATextBox;
        private TextBox PlaneCountBTextBox;
        private Label label5;
        private Label label6;
        private Label label7;
        private Label label8;
        private Label label9;
        private Label label10;
        private Label label11;
        private Label label12;
        private Label label13;
        private Label label14;
        private Label label15;
        private MenuStrip menuStrip1;
        private ToolStripMenuItem menuToolStripMenuItem;
        private ToolStripMenuItem aboutToolStripMenuItem;
        private TextBox PlaneANameTextBox;
        private Label label16;
        private TextBox PlaneBNameTextBox;
        private Label label17;
        private ComboBox PlaneAComboBox;
        private ComboBox PlaneBComboBox;
        private Button SaveButton;
        private Button DeleteButton;
    }
}

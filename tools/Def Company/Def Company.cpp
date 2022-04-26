// Def Company.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"
#include <dirent.h>
#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <regex>
#include <stdlib.h>

using namespace std;
string Mod_Directory;
vector <string> List_Tags;
vector <string> All_Data_In_CSV;

//Reads the files in directory & returns a vector with file names
vector <string> Read_File_Names(string directory) {

	DIR *Local_Mod_DIR;
	struct dirent *ent;
	vector <string> File_lines;

	//If the directory is not null continue
	if ((Local_Mod_DIR = opendir(directory.c_str())) != NULL) {
		
		//For every file in this directory copy name to vector (basically an array)
		while ((ent = readdir(Local_Mod_DIR)) != NULL) {
			if (ent->d_type != DT_DIR) {
				File_lines.push_back(ent->d_name);
			}
		}
		closedir(Local_Mod_DIR);

	}
	else {
		/* could not open directory */
		//cout << endl << "error" << endl;
		//return EXIT_FAILURE;
	}

	for (int i = 0; i < File_lines.size(); i++) {
		//cout << File_lines[i] << endl;

	}
	
	return File_lines;

}

//Filters File names to get country name & tag - returns a vector with country name and its tag
vector <string> Filter_File_Name(vector <string> File_Names) {

	vector <string> Parsed_Content;

	for (int i = 0; i < File_Names.size(); i++) {

		//Parses the file name for the countries name "tag - COUNTRY.txt"
		std::regex Find_Name(+"[a-z-A-Z]{3} - ([a-zA-Z ]+).txt");
		std::smatch r;
		std::regex_match(File_Names[i], r, Find_Name);

		//If this line contains a country name save in vector
		if (r[1] != "") {
			Parsed_Content.push_back(r[1]);
			//cout << endl << "Country: " << r[1];


		}

		//Parses the file name for the tag "TAG - country.txt"
		std::regex Find_Tag(+"([a-z-A-Z]{3}) - [a-zA-z ]+.txt");
		std::smatch q;
		std::regex_match(File_Names[i], q, Find_Tag);

		//If this line contains a tag save in vector
		if (q[1] != "") {
			Parsed_Content.push_back(q[1]);
			//cout << endl << "tag: " << q[1];
			

		}

	}
	//cin.ignore();
	return Parsed_Content;
}

//Provide a country name, this searches the vector and returns the correct tag as a string
string Find_tag(vector <string> List_Tags, string Country) {

	string tag = "ERROR";
	cout << endl;
	for (int i = 0; i < List_Tags.size(); i++) {
		
		if (Country == List_Tags[i]) {
			tag = List_Tags[(i + 1)];

			//cout << endl << Country << " tag is: " << List_Tags[(i + 1)] << endl;
			i = List_Tags.size() + 100;
		}
		
	}
	if (tag == "ERROR") {

		cout << endl << "ERROR" << " - " << Country << endl;
		cin.ignore();

	}
	return tag;
}

void Write_Localisation(vector <string> data) {
	string file_name = ("MD4_Def_companies_l_english.yml");
	ofstream outfile(file_name);

	//cout << endl << file_name << " created";
	outfile << "l_english:" << endl;

	//0)country 1)tag 2)comp name 3)skill 4)cat1 5)subcat1 6)localisation 6)localisation
	for (int j = 0; j < data.size(); j = j +7) {
		
		outfile << " " << data[j + 1] << "_" << data[j + 2] << "_" << data[j + 4] << ":0 \"" << data[j + 6] << "\"" << endl;
		cout << endl << data[j + 6] << endl;
	}
	outfile.close();
}

void Write_Def_Comp(vector <string> data) {
	
	//string Generate_Directory = Mod_Directory + "//tool//generated//Def_Comp";
	//string file_name = (Generate_Directory + "//" + Country_Tag + "_DefComp.txt");
	string file_name = (data[1] + "_DefComp.txt");
	
	//CreateDirectoryA(Generate_Directory.c_str(), NULL);
	ofstream outfile(file_name);
	//outfile.open(file_name, std::ios::app);

	//for (int j = 0; j < data.size(); j++) {
	//	cout << data[j] << " - J = " << j << endl;
	//}

	//cin.ignore();

	cout << endl << file_name << " created";
	

	outfile << "ideas = {" << endl;
	outfile << endl;
	
	//outfile << Company_Name << endl << CompanyTag << endl;
	
	//0)country 1)tag 2)comp name 3)skill 4)cat1 5)subcat1 6)localisation
	for (int j = 0; j < data.size(); j = j +7) {
			
			//cat = j+5
			//comp name = J+3
			// tag = J+2
			//Category1 = {
			outfile << "\t" << data[j+4] <<" = {" << endl;
			outfile << "\t" << endl;
			//designer = yes
			outfile << "\t\tdesigner = yes" << endl;
			outfile << "\t\t" << endl;
			//Company_Name = {
			outfile << "\t\t" << data[j + 1] << "_" << data[j+2] << "_" << data[j+4] << " = {" << endl;
			outfile << "\t\t" << endl;
			//picture = company
			outfile << "\t\t\tpicture = " << data[j+2] << "_" << data[j + 1]  << endl;
			outfile << "\t\t\t" << endl;
			//allowed = {
			outfile << "\t\t\tallowed = {" << endl;
			//tag = TAG
			outfile << "\t\t\t\ttag = " << data[j + 1] << endl;
			outfile << "\t\t\t}" << endl;
			//cost = 150
			outfile << "\t\t\tcost = 150" << endl;
			outfile << "\t\t\t" << endl;
			//removal_cost = 10
			outfile << "\t\t\tremoval_cost = 10" << endl;
			outfile << "\t\t\t" << endl;
			outfile << "\t\t\tresearch_bonus = {" << endl;
			//0)country 1)tag 2)comp name 3)skill 4)cat1 5)subcat1 6)localisation
			if (data[j + 4] == "Ship_Company") {
				if (data[j + 5] == "Cat_NAVAL_EQP") {
					outfile << "\t\t\t\tCat_NAVAL_EQP" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_SURFACE_SHIP") {
					outfile << "\t\t\t\tCat_SURFACE_SHIP" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_CARRIER") {
					outfile << "\t\t\t\tCat_CARRIER" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_TRANS_SHIP") {
					outfile << "\t\t\t\tCat_TRANS_SHIP" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}

			}
			if (data[j + 4] == "Submarine_Company") {
				if (data[j + 5] == "Cat_SUB") {
					outfile << "\t\t\t\tCat_SUB" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_NUKE_SUB") {
					outfile << "\t\t\t\tCat_NUKE_SUB" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_D_SUB") {
					outfile << "\t\t\t\tCat_D_SUB" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
			}
			if (data[j + 4] == "Vehicle_Company") {
				if (data[j + 5] == "Cat_ARMOR") {
					outfile << "\t\t\t\tCat_ARMOR" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_AFV") {
					outfile << "\t\t\t\tCat_AFV" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "CAT_TANKS") {
					outfile << "\t\t\t\tCAT_TANKS" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_ARTILLERY") {
					outfile << "\t\t\t\tCat_ARTILLERY" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
			}
			if (data[j + 4] == "Infantry_Weapon_Company") {
				if (data[j + 5] == "Cat_INF") {
					outfile << "\t\t\t\tCat_INF" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_AA") {
					outfile << "\t\t\t\tCat_AA" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_AT") {
					outfile << "\t\t\t\tCat_AT" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_INF_WEP") {
					outfile << "\t\t\t\tCat_INF_WEP" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_L_DRONE") {
					outfile << "\t\t\t\tCat_L_DRONE" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
			}
			if (data[j + 4] == "Helicopter_Company") {
				if (data[j + 5] == "Cat_HELI") {
					outfile << "\t\t\t\tCat_HELI" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
			}
			if (data[j + 4] == "Aircraft_Company") {
				if (data[j + 5] == "CAT_FIXED_WING") {
					outfile << "\t\t\t\tCAT_FIXED_WING" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_H_AIR") {
					outfile << "\t\t\t\tCat_H_AIR" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_FIGHTER") {
					outfile << "\t\t\t\tCat_FIGHTER" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
				if (data[j + 5] == "Cat_L_Fighter") {
					outfile << "\t\t\t\tCat_L_Fighter" << " = " << (0.015 * stof(data[j + 3])) << endl;
				}
			}
			outfile << "\t\t\t}" << endl;
			outfile << "\t\t\t" << endl;
			outfile << "\t\t\ttraits = {" << endl;
			//0)country 1)tag 2)comp name 3)skill 4)cat1 5)subcat1 6)localisation
			if (data[j + 4] == "Ship_Company") {
				if (data[j + 5] == "Cat_NAVAL_EQP") {
					outfile << "\t\t\t\tCat_NAVAL_EQP" <<"_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_SURFACE_SHIP") {
					outfile << "\t\t\t\tCat_NAVAL_EQP" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_CARRIER") {
					outfile << "\t\t\t\tCat_CARRIER" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_TRANS_SHIP") {
					outfile << "\t\t\t\tCat_TRANS_SHIP" << "_" << data[j + 3] << endl;
				}
				
			}
			if (data[j + 4] == "Submarine_Company") {
				if (data[j + 5] == "Cat_SUB") {
					outfile << "\t\t\t\tCat_SUB" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_NUKE_SUB") {
					outfile << "\t\t\t\tCat_NUKE_SUB" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_D_SUB") {
					outfile << "\t\t\t\tCat_D_SUB" << "_" << data[j + 3] << endl;
				}
			}
			if (data[j + 4] == "Vehicle_Company") {
				if (data[j + 5] == "Cat_ARMOR") {
					outfile << "\t\t\t\tCat_ARMOR" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_AFV") {
					outfile << "\t\t\t\tCat_AFV" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "CAT_TANKS") {
					outfile << "\t\t\t\tCAT_TANKS" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_ARTILLERY") {
					outfile << "\t\t\t\tCat_ARTILLERY" << "_" << data[j + 3] << endl;
				}
			}
			if (data[j + 4] == "Infantry_Weapon_Company") {
				if (data[j + 5] == "Cat_INF") {
					outfile << "\t\t\t\tCat_INF" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_AA") {
					outfile << "\t\t\t\tCat_AA" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_AT") {
					outfile << "\t\t\t\tCat_AT" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_INF_WEP") {
					outfile << "\t\t\t\tCat_INF_WEP" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_L_DRONE") {
					outfile << "\t\t\t\tCat_L_DRONE" << "_" << data[j + 3] << endl;
				}
			}
			if (data[j + 4] == "Helicopter_Company") {
				if (data[j + 5] == "Cat_HELI") {
					outfile << "\t\t\t\tCat_HELI" << "_" << data[j + 3] << endl;
				}
			}
			if (data[j + 4] == "Aircraft_Company") {
				if (data[j + 5] == "CAT_FIXED_WING") {
					outfile << "\t\t\t\tCAT_FIXED_WING" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_H_AIR") {
					outfile << "\t\t\t\tCat_H_AIR" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_FIGHTER") {
					outfile << "\t\t\t\tCat_FIGHTER" << "_" << data[j + 3] << endl;
				}
				if (data[j + 5] == "Cat_L_Fighter") {
					outfile << "\t\t\t\tCat_L_Fighter" << "_" << data[j + 3] << endl;
				}
			}
			outfile << "\t\t\t" << endl;
			outfile << "\t\t\t}" << endl;
			if (data[j + 4] == "Ship_Company") {
				outfile << "\t\t\tai_will_do = {" << endl;
				outfile << "\t\t\t\tfactor = " << (stof(data[j + 3])/10) << endl;
				outfile << "\t\t\t\t" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\thas_navy_size = { size > 25 } #has a large navy" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tnum_of_naval_factories > 3 #has the industry to take advantage of the company" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tis_major = yes #Majors project power" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tNOT = { #need to have ports" << endl;
				outfile << "\t\t\t\t\t\tany_owned_state = {" << endl;
				outfile << "\t\t\t\t\t\t\tis_coastal = yes" << endl;
				outfile << "\t\t\t\t\t\t}" << endl;
				outfile << "\t\t\t\t\t}" << endl;
				outfile << "\t\t\t\t\tfactor = -10" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t}" << endl;
			}
			if (data[j + 4] == "Submarine_Company") {
				outfile << "\t\t\tai_will_do = {" << endl;
				outfile << "\t\t\t\tfactor = " << (stof(data[j + 3])/10) << endl;
				outfile << "\t\t\t\t" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\thas_navy_size = { size > 25 } #has a large navy" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tnum_of_naval_factories > 3 #has the industry to take advantage of the company" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tis_major = yes #Majors project power" << endl;
				outfile << "\t\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tNOT = { #need to have ports" << endl;
				outfile << "\t\t\t\t\t\tany_owned_state = {" << endl;
				outfile << "\t\t\t\t\t\tis_coastal = yes" << endl;
				outfile << "\t\t\t\t\t\t}" << endl;
				outfile << "\t\t\t\t\t}" << endl;
				outfile << "\t\t\t\t\tfactor = -10" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t}" << endl;
			}
			if (data[j + 4] == "Vehicle_Company") {
				outfile << "\t\t\tai_will_do = {" << endl;
				outfile << "\t\t\t\tfactor = " << (stof(data[j + 3]) / 10) << " #All countries need a land army, vehicles are part of modern warfare" << endl;
				outfile << "\t\t\t\t" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tnum_of_military_factories > 10 #has the industry to take advantage of the company" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tis_major = yes #Majors project power" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t}" << endl;
			}
			if (data[j + 4] == "Infantry_Weapon_Company") {
				outfile << "\t\t\tai_will_do = {" << endl;
				outfile << "\t\t\t\tfactor = " << (stof(data[j + 3]) / 10) << " #All countries need a land army, vehicles are part of modern warfare" << endl;
				outfile << "\t\t\t\t" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tnum_of_military_factories > 5 #has the industry to take advantage of the company" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tis_major = yes #Majors project power" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t}" << endl;
			}
			if (data[j + 4] == "Helicopter_Company") {
				outfile << "\t\t\tai_will_do = {" << endl;
				outfile << "\t\t\t\tfactor = " << (stof(data[j + 3]) / 10) << " #Most countries don't have decent airforces" << endl;
				outfile << "\t\t\t\t" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\thas_tech = attack_helicopter2 #has semi-modern tech, most countries dont have it" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\thas_tech = transport_helicopter2 #has semi-modern tech, most countries dont have it" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tis_major = yes #Majors project power" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t}" << endl;
			}
			if (data[j + 4] == "Aircraft_Company") {
				outfile << "\t\t\tai_will_do = {" << endl;
				outfile << "\t\t\t\tfactor = " << (stof(data[j + 3]) / 10) << " #Most countries don't have decent airforces" << endl;
				outfile << "\t\t\t\t" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tor = {" << endl;
				outfile << "\t\t\t\t\t\thas_tech = AS_Fighter2 #has semi-modern tech" << endl;
				outfile << "\t\t\t\t\t\thas_tech = MR_Fighter2" << endl;
				outfile << "\t\t\t\t\t\thas_tech = Strike_fighter2" << endl;
				outfile << "\t\t\t\t\t\thas_tech = L_Strike_fighter2" << endl;
				outfile << "\t\t\t\t\t\thas_tech = Air_UAV1" << endl;
				outfile << "\t\t\t\t\t}" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tor = {" << endl;
				outfile << "\t\t\t\t\t\thas_tech = strategic_bomber3 #has semi-modern tech, most countries dont have it" << endl;
				outfile << "\t\t\t\t\t\thas_tech = transport_plane2" << endl;
				outfile << "\t\t\t\t\t\thas_tech = naval_plane3" << endl;
				outfile << "\t\t\t\t\t\thas_tech = cas2" << endl;
				outfile << "\t\t\t\t\t}" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t\tmodifier = {" << endl;
				outfile << "\t\t\t\t\tis_major = yes #Majors project power" << endl;
				outfile << "\t\t\t\t\tfactor = 1" << endl;
				outfile << "\t\t\t\t}" << endl;
				outfile << "\t\t\t}" << endl;
			}
			
			outfile << "\t\t\t" << endl;
			outfile << "\t\t}" << endl;
			outfile << "\t}" << endl;
			outfile << "\t" << endl;
	}
	outfile << "}" << endl;
	outfile.close();
}



void Parse_CSV_File (string Mod_Directory) {
	ifstream file;
	string local_directory = Mod_Directory +"//test.csv";;
	string content;
	string country_name;
	string country_tag;
	vector <string> Content_of_CSV;
	int TotalCompanies = 0;
	bool write = false;
	std::vector<int>::iterator it;
	cout << endl;
	file.open(local_directory);

	while (getline(file, content)) {

		//Adds Country name & Country Tag to vector
		std::regex country("([a-zA-z ]+),,,,,,,,");
		std::smatch n;
		std::regex_match(content, n, country);

		if (n[1] != "") {

			if (write == true ) {
				//cout << endl << "tehe2" << endl;
				Write_Def_Comp(Content_of_CSV); //DONT FORGET YOU COMMENTED THIS OUT
				country_name = "";
				country_tag = "";
				All_Data_In_CSV.reserve(All_Data_In_CSV.size() + Content_of_CSV.size());
				All_Data_In_CSV.insert(All_Data_In_CSV.end(), Content_of_CSV.begin(), Content_of_CSV.end());
				Content_of_CSV.clear();
				write = false;
				
			}

			country_name = n[1]; //adds country to vector
			country_tag = Find_tag(List_Tags, n[1]); //adds tag to vector
			//cout << endl << country_name << " tag is " << country_tag;
			//cin.ignore();
			write = true;
			//cout << endl << "tehe" << endl;
		}
		
		
		//cout << content;

		//						 #Con/comp     #skill    #cat 1        #scat1       #cat 2		  #scat 2      #cat 3		  #scat 3		#Localisation
		std::regex company_name("([a-zA-z_]+),([0-9]+),(|[a-zA-z_]+),(|[a-zA-z_]+),(|[a-zA-z_]+),(|[a-zA-z_]+),(|[a-zA-z_]+),(|[a-zA-z_]+),(|.*)");
		std::smatch o;
		std::regex_match(content, o, company_name);

		
		//Adds company Category 1 to vector
		if (o[3] != "") {
			Content_of_CSV.push_back(country_name); //adds country to vector
			Content_of_CSV.push_back(country_tag); //adds tag to vector
			Content_of_CSV.push_back(o[1]); //Adds company name to vector
			Content_of_CSV.push_back(o[2]); //Adds company skill to vector
			Content_of_CSV.push_back(o[3]); //adds company category
			Content_of_CSV.push_back(o[4]); //adds company sub-category
			Content_of_CSV.push_back(o[9]); //adds localisation
			//cout << o[3] << endl;
			TotalCompanies++;
		}

		//Adds company Category 2 to vector
		if (o[5] != "") {
			Content_of_CSV.push_back(country_name); //adds country to vector
			Content_of_CSV.push_back(country_tag); //adds tag to vector
			Content_of_CSV.push_back(o[1]); //Adds company name to vector
			Content_of_CSV.push_back(o[2]); //Adds company skill to vector
			Content_of_CSV.push_back(o[5]); //adds company category
			Content_of_CSV.push_back(o[6]); //adds company sub-category
			Content_of_CSV.push_back(o[9]); //adds localisation
			//cout << o[4] << endl;
			TotalCompanies++;
		}

		//Adds company Category 3 to vector
		if (o[7] != "") {
			Content_of_CSV.push_back(Content_of_CSV[0]); //adds country to vector
			Content_of_CSV.push_back(Content_of_CSV[1]); //adds tag to vector
			Content_of_CSV.push_back(o[1]); //Adds company name to vector
			Content_of_CSV.push_back(o[2]); //Adds company skill to vector
			Content_of_CSV.push_back(o[7]); //adds company category
			Content_of_CSV.push_back(o[8]); //adds company sub-category
			Content_of_CSV.push_back(o[9]); //adds localisation
			//cout << o[5] << endl;
			TotalCompanies++;
		}

		//for (int i = 0; i < Content_of_CSV.size(); i++) {
		//	cout << Content_of_CSV[i];
		//	cin.ignore();
		//}
		
	}
	cout << endl << "There are a total of: " << TotalCompanies++ << endl;
	cin.ignore();
	Write_Localisation(All_Data_In_CSV);
}

int main()
{

	//Retrieve Mod directory
	cout << " Please enter the mod directory: ";
	getline(cin, Mod_Directory);
	if (Mod_Directory == "gearz") {
		Mod_Directory = "C://Users//smithmicsup//Desktop";
		cout << endl << endl;
		List_Tags = Filter_File_Name(Read_File_Names(Mod_Directory));
	}
	if (Mod_Directory == "gearz2") {
		Mod_Directory = "C://Users//Michael Smith//Documents//Paradox Interactive//Hearts of Iron IV//mod//Modern_Day_4_HOI";
		cout << endl << endl;
		List_Tags = Filter_File_Name(Read_File_Names((Mod_Directory + "//history//countries")));
	}

	
	
	//Fills a vector with all country names & tags.
	

	//Main Program



	string test;

	//test = Find_tag(List_Tags, "Australia");
	Parse_CSV_File(Mod_Directory);
	cout << endl << "done" << endl;
	cin.ignore();
	//return 0;
}


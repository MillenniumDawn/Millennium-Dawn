// HOI4 Tech Generator.cpp : Defines the entry point for the console application.
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
bool continue_program = true;
bool Repeat_ques_progr = true;
float file_counter = 0;
vector <string> filename;
string the_directory;
float tech_cost;

vector <string> tech_read_config(vector <string> file_directory) {

	ifstream file;
	string content;
	float locl_line = 0;
	string directory;
	vector<string> local_content;
	vector<string> parsed_content;
	int tc1 = 1;

	//Initial parse, finds tech and etc
	for (float i = 0; i < file_directory.size(); ++i) {
		directory = file_directory[i];
		file.open(directory);
		while (getline(file, content)) {

			std::regex tech_name(+"^[\t]([a-zA-Z0-9_]*)\\s?=\\s?\\{");
			std::smatch a;
			std::regex_match(content, a, tech_name);

			if (a[1] != "") {
				local_content.push_back("Found tech");
				local_content.push_back(a[1]);
				//cout << a[1] << endl;
				//cin.ignore();
			}

			std::regex research_cost(+"^[\t]+(research_cost\\s?=\\s?[0-9.]+)");
			std::smatch b;
			std::regex_match(content, b, research_cost);

			if (b[1] != "") {
				local_content.push_back(b[1]);
				//cout << b[1] << endl;
			}

			std::regex start_year(+"^[\t]+(start_year\\s?=\\s?[0-9]+)");
			std::smatch c;
			std::regex_match(content, c, start_year);

			if (c[1] != "") {
				local_content.push_back(c[1]);
				//cout << c[1] << endl;

			}


		}

		//displays file name that is being read
		std::regex file_name(+".*[\\\/]+([a-z 0-9_]+\.txt)");
		std::smatch f_name;
		std::regex_match(directory, f_name, file_name);
		string temp_file_name = "";

		if (f_name[1] != "") {
			temp_file_name = f_name[1];
		}
		
		cout << "Reading " << temp_file_name << endl;

		
		file.close();
	}

	bool continue_parse = false;

	//Cleans up parsed text & formats it
	for (int j = 0; j < local_content.size(); j++) {
		content = local_content[j];
		continue_parse = false;

		std::regex found_tech(+"(Found tech)");
		std::smatch a;
		std::regex_match(content, a, found_tech);

		if (a[1] != "") {
			//parsed_content.push_back(a[1];
			//cout << a[1] << endl;
			continue_parse = true;
		}

		if (continue_parse) {

			content = local_content[j + 1];
			std::regex tech_name(+"([a-zA-Z0-9_]*)");
			std::smatch b;
			std::regex_match(content, b, tech_name);

			if (b[1] != "") {
				parsed_content.push_back(b[1]);
				//cout << b[1] << endl;


			}
			if (b[1] == "") {
				parsed_content.push_back("ErrorInName");
				//cout << b[1] << endl;


			}

			content = local_content[j + 2];
			std::regex research_cost(+"research_cost\\s?=\\s?([0-9.]+)");
			std::smatch c;
			std::regex_match(content, c, research_cost);

			if (c[1] != "") {
				parsed_content.push_back(c[1]);
				//cout << c[1] << endl;

			}
			if (c[1] == "") {
				parsed_content.push_back("0");
				//cout << "0" << endl;


			}


			content = local_content[j + 3];
			std::regex start_year(+"start_year\\s?=\\s?([0-9]+)");
			std::smatch d;
			std::regex_match(content, d, start_year);

			if (d[1] != "") {
				parsed_content.push_back(d[1]);
				//cout << d[1] << endl;

			}
			else {
				parsed_content.push_back("0");
				//cout << "0" << endl;
			}

		}
		//cin.ignore();
	}

	//for (int j = 0; j < parsed_content.size(); j++) {
		//cout << parsed_content[j] << endl;
	//}

	//cin.ignore();
	return parsed_content;

}

vector <string> tech_scan_config_dir(string directory) {



	string local_directory = directory;
	DIR *local_dir = opendir(local_directory.c_str());
	struct dirent *file_listing;

	vector<string> file_directory;

	while (file_listing = readdir(local_dir)) {

		if (file_listing == NULL)
		{
			cout << "\nERROR! pdir could not be initialised correctly";
			exit(7);
		}

		else if (file_listing->d_type == DT_DIR) { // if Directory run this function again
			string test2 = file_listing->d_name;
			if (!(test2 == "." || test2 == "..")) {
				string test2 = directory + file_listing->d_name;
				vector<string> temp;

				temp = tech_scan_config_dir(test2);
				file_directory.insert(file_directory.end(), temp.begin(), temp.end());

				file_counter++;
			}
		}

		else if (file_listing->d_type != DT_DIR) {
			file_directory.push_back(directory + "//" + file_listing->d_name);

			file_counter++;
		}
	}

	return file_directory;

}

vector <string> tech_calculate_time(vector <string> tech_list) {

	vector<string> local_tech_list = tech_list;
	vector<string> parsed_tech;
	string content;
	bool continue_calc = false;
	float research_time = 0;

	for (float i = 0; i < local_tech_list.size(); ++i) {
		content = local_tech_list[i];
		continue_calc = false;

		std::regex tech_name(+"([a-zA-Z0-9_]*)");
		std::smatch a;
		std::regex_match(content, a, tech_name);

		if (a[1] != "") {	
			continue_calc = true;
		}

		if (continue_calc) {


			//Research Cost
			content = local_tech_list[1];
			research_time += atof(content.c_str());
			//research_time *= tech_cost;
			cout << research_time << endl;
			//Research Year
		}
	}

	return parsed_tech;
}

float read_defines(string file_directory) {

	ifstream file;
	string content;
	string directory;
	vector<string> local_content;
	float test = 0;

	//Initial parse, finds tech and etc
	
	directory = file_directory;
	file.open(directory);
	while (getline(file, content)) {
		//cout << content << endl;
		std::regex tech_name(+"(tech)");
		std::smatch a;
		std::regex_match(content, a, tech_name);
		//cout << a[1] <<endl;
		if (a[1] != "") {

			cout << a[1] << endl;
			//cin.ignore();
		}
	}
	//cout << directory << endl;
	//cout << "here" << endl;
	//cin.ignore();
	
	file.close();
	return test;
}


int main()
{
	//Main Variables
	string program_number;
	string str_continue_prog;
	
	string who;
	string temp;

	//Resource Calculator vars
	vector <string> file_location_vector;
	vector <string> content_of_file_vector;
	vector <string> calculations;

	//Tech Calculator
	bool stop = true;
	string tech_level;


	//Start of program
	cout << "Welcome to Gearz's HOI4 Tech Tool!" << endl << endl;
	cout << endl << "Please enter your mod's directory in the following fomat. Example  'C://Program Files (x86)//Steam//SteamApps//common//Hearts of Iron 3//tfh//mod//My Mod//' " << endl;
	cout << endl << "Directory: ";
	getline(cin, the_directory);

	if (the_directory == "gearz") {
		the_directory = "C://Users//Michael Smith//Documents//Paradox Interactive//Hearts of Iron IV//mod//Modern_Day_4_HOI//";
	}

	cout << endl << "Please enter the base tech cost: ";
	getline(cin, temp);
	tech_cost = stof(temp);
	system("cls");



	while (continue_program) {

		cout << endl << "Loading..." << endl;
		the_directory = the_directory;

		//tech_cost = read_defines(the_directory + "common//defines//00_defines.lua");

		file_location_vector = tech_scan_config_dir(the_directory+ "common//technologies");
		cout << endl << "Reading " << file_location_vector.size() << " files" << endl << endl;
		
		content_of_file_vector = tech_read_config(file_location_vector);

		calculations = tech_calculate_time(content_of_file_vector);
		cin.ignore();
		 
	}
    return 0;
}


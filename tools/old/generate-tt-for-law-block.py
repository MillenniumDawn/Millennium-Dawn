#!/usr/bin/python

list = [
    "bureau_01",
    "bureau_02",
    "bureau_03",
    "bureau_04",
    "bureau_05",
    "defence_00",
    "defence_01",
    "defence_02",
    "defence_03",
    "defence_04",
    "defence_05",
    "defence_06",
    "defence_07",
    "defence_08",
    "defence_09",
    "edu_01",
    "edu_02",
    "edu_03",
    "edu_04",
    "edu_05",
    "health_01",
    "health_02",
    "health_03",
    "health_04",
    "health_05",
    "health_06",
    "social_01",
    "social_02",
    "social_03",
    "social_04",
    "social_05",
    "social_06",
    "police_01",
    "police_02",
    "police_03",
    "police_04",
    "police_05",
]
header_list = [
    "bureaucracy",
    "Military_Spending",
    "education_budget",
    "health_budget",
    "social_budget",
    "crime_fighting",
]

with open("temp.txt", "w") as ffile:
    for a in header_list:
        for b in list:
            if a == "bureaucracy" and "bureau" in b:
                ffile.write(
                    f'cannot_go_lower_than_{b}_tt: "Cannot Lower §Y${a}$§! than §Y${b}$§!"\n'
                )
                ffile.write(
                    f'cannot_go_higher_than_{b}_tt: "Cannot Raise §Y${a}$§! Higher than §Y${b}$§!"\n'
                )
            if a == "Military_Spending" and "defence" in b:
                ffile.write(
                    f'cannot_go_lower_than_{b}_tt: "Cannot Lower §Y${a}$§! than §Y${b}$§!"\n'
                )
                ffile.write(
                    f'cannot_go_higher_than_{b}_tt: "Cannot Raise §Y${a}$§! Higher than §Y${b}$§!"\n'
                )

            if a == "education_budget" and "edu" in b:
                ffile.write(
                    f'cannot_go_lower_than_{b}_tt: "Cannot Lower §Y${a}$§! than §Y${b}$§!"\n'
                )
                ffile.write(
                    f'cannot_go_higher_than_{b}_tt: "Cannot Raise §Y${a}$§! Higher than §Y${b}$§!"\n'
                )

            if a == "health_budget" and "health" in b:
                ffile.write(
                    f'cannot_go_lower_than_{b}_tt: "Cannot Lower §Y${a}$§! than §Y${b}$§!"\n'
                )
                ffile.write(
                    f'cannot_go_higher_than_{b}_tt: "Cannot Raise §Y${a}$§! Higher than §Y${b}$§!"\n'
                )

            if a == "social_budget" and "social" in b:
                ffile.write(
                    f'cannot_go_lower_than_{b}_tt: "Cannot Lower §Y${a}$§! than §Y${b}$§!"\n'
                )
                ffile.write(
                    f'cannot_go_higher_than_{b}_tt: "Cannot Raise §Y${a}$§! Higher than §Y${b}$§!"\n'
                )

            if a == "crime_fighting" and "police" in b:
                ffile.write(
                    f'cannot_go_lower_than_{b}_tt: "Cannot Lower §Y${a}$§! than §Y${b}$§!"\n'
                )
                ffile.write(
                    f'cannot_go_higher_than_{b}_tt: "Cannot Raise §Y${a}$§! Higher than §Y${b}$§!"\n'
                )

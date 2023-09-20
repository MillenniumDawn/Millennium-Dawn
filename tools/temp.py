
i = 0

with open("tooltip.txt", "w") as ffile:
	while i < 204:
		x = float(i) / 100.00

		ffile.write(f'gdp_debt_ratio_lower_{i}_tt: "[THIS.GetName] §YDebt-to-GDP§! Lower than §Y{i}%§! (Current:[?THIS.debt_ratio|-1&])"\n')
		ffile.write(f'gdp_debt_ratio_higher_{i}_tt: "[THIS.GetName] §YDebt-to-GDP§! Higher than §Y{i}%§! (Current:[?THIS.debt_ratio|-1&])"\n')

		i = i + 5

i = 0

with open("triggers.txt", "w") as ffile:
	while i < 204:
		x = float(i) / 100.00
		x = round(x, 3)
		i = round(i)

		ffile.write('gdp_debt_ratio_lower_' + str(i) + ' = {\n\tcustom_trigger_tooltip = {\n\t\ttooltip = gdp_debt_ratio_lower_' + str(i) + '_tt\n\t\tcheck_variable = { THIS.debt_ratio < ' + str(x) + ' }\n\t}\n}')
		ffile.write('gdp_debt_ratio_higher_' + str(i) + ' = {\n\tcustom_trigger_tooltip = {\n\t\ttooltip = gdp_debt_ratio_higher_' + str(i) + '_tt\n\t\tcheck_variable = { THIS.debt_ratio > ' + str(x) + ' }\n\t}\n}')
		i = i + 5